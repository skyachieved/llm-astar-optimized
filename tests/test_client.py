"""Step 2.0: the chat client and the user-facing LLMAStar(llm='gpt') interface. No network: a fake API object
stands in for the OpenAI client."""
import pytest

from llmastar.model import ChatGPT
from llmastar.model.chatgpt import resolve_api_key
from llmastar.pather import LLMAStar


@pytest.fixture
def no_keys(monkeypatch):
    import openai
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setattr(openai, "api_key", None, raising=False)
    return openai


def test_key_order_argument_then_module_then_env(no_keys, monkeypatch):
    assert resolve_api_key() is None
    monkeypatch.setenv("OPENAI_API_KEY", "from-env")
    assert resolve_api_key() == "from-env"
    monkeypatch.setattr(no_keys, "api_key", "from-module")
    assert resolve_api_key() == "from-module"
    assert resolve_api_key("from-arg") == "from-arg"


def test_key_is_not_part_of_the_request_or_cache_key(no_keys):
    client = ChatGPT(api_key="sk-secret", cache_dir=None)
    assert "sk-secret" not in repr(client.sampling)
    assert not hasattr(client, "api_key")  # stored privately, never in a record


def test_llm_gpt_is_gpt4o_mini_with_the_paper_gpt_prompts():
    search = LLMAStar(llm="gpt", prompt="cot")
    assert search.llm.model == "gpt-4o-mini"
    assert search.generator.prompt == "cot" and search.generator.prompt_set == "gpt"
    messages = search.generator.messages({"start": [1, 2], "goal": [3, 4], "horizontal_barriers": [[10, 0, 25]],
                                          "vertical_barriers": [[25, 10, 22]]})
    assert len(messages) == 1 and messages[0]["role"] == "user"
    assert "Start Point: [1, 2]" in messages[0]["content"]


# ---- 2.0b: timeout / retry / parameter-drop policy, with a fake API object -------------------------------------

class FakeError(Exception):
    def __init__(self, status_code=None, message="", param=None):
        super().__init__(message)
        self.status_code, self.message, self.param = status_code, message, param


class FakeAPI:
    """Stands in for openai.OpenAI(): `script` lists, per call, an exception to raise or a reply text."""

    def __init__(self, script):
        self.script, self.calls = list(script), []
        self.chat = self
        self.completions = self

    def create(self, model, messages, **params):
        self.calls.append(params)
        step = self.script.pop(0)
        if isinstance(step, Exception):
            raise step
        from types import SimpleNamespace as NS
        return NS(choices=[NS(message=NS(content=step), finish_reason="stop")], usage=None)


def make_client(script, tmp_path, **kwargs):
    client = ChatGPT(cache_dir=str(tmp_path), api_key="dummy", **kwargs)
    client._client = FakeAPI(script)
    client._sleep = lambda seconds: None
    return client


MESSAGES = [{"role": "user", "content": "hi"}]


def test_transient_errors_are_retried_then_cached(tmp_path):
    client = make_client([FakeError(429, "rate limited"), TimeoutError("slow"), FakeError(503), "ok"], tmp_path)
    content, info = client.chat_with_info(MESSAGES)
    assert content == "ok" and info["attempts"] == 4 and "error" not in info
    assert client.chat_with_info(MESSAGES)[1]["cached"]  # second call served from the cache


def test_retries_stop_after_three_and_errors_are_returned_not_cached(tmp_path):
    client = make_client([FakeError(500)] * 4 + ["late"], tmp_path)
    content, info = client.chat_with_info(MESSAGES)
    assert content == "" and info["attempts"] == 4 and "500" in info["error"]
    content, info = client.chat_with_info(MESSAGES)  # not cached: the next call tries again
    assert content == "late" and not info["cached"]


@pytest.mark.parametrize("status", [400, 401, 403, 404])
def test_other_client_errors_are_not_retried(tmp_path, status):
    client = make_client([FakeError(status, "nope"), "never"], tmp_path)
    content, info = client.chat_with_info(MESSAGES)
    assert content == "" and info["attempts"] == 1 and str(status) in info["error"]


@pytest.mark.parametrize("error", [FakeError(400, "bad", param="temperature"),
                                   FakeError(400, "Unsupported parameter: 'temperature' is not supported")])
def test_a_rejected_parameter_is_dropped_once(tmp_path, error):
    client = make_client([error, "ok"], tmp_path)
    content, info = client.chat_with_info(MESSAGES)
    assert content == "ok" and info["dropped_params"] == ["temperature"]
    assert "temperature" in client._client.calls[0] and "temperature" not in client._client.calls[1]


def test_only_one_parameter_is_dropped(tmp_path):
    client = make_client([FakeError(400, "x", param="temperature"), FakeError(400, "y", param="top_p"), "ok"],
                         tmp_path)
    content, info = client.chat_with_info(MESSAGES)
    assert content == "" and info["attempts"] == 2


def test_missing_key_is_an_error_not_a_crash(tmp_path, no_keys):
    client = ChatGPT(cache_dir=str(tmp_path))
    content, info = client.chat_with_info(MESSAGES)
    assert content == "" and "No API key" in info["error"]


def test_stop_enters_the_request_only_when_set(tmp_path):
    default = make_client(["a"], tmp_path)
    assert set(default.sampling) == {"temperature", "max_tokens", "top_p", "seed"}  # same cache keys as before
    original = make_client(["a"], tmp_path, stop=["\n"], max_tokens=100)
    original.chat_with_info(MESSAGES)
    assert original._client.calls[0]["stop"] == ["\n"] and original._client.calls[0]["max_tokens"] == 100


def test_run_flags_name_the_original_setup():
    from llmastar.run import llm_variant, parse_args
    assert llm_variant(parse_args(["--method", "llmastar"])) is None
    assert llm_variant(parse_args(["--method", "llmastar", "--stop-newline", "--max-tokens", "100"])) == "stopnl-max100"


def test_model_sampling_sends_only_max_tokens(tmp_path):
    # Claude Opus 5.5 on Anthropic's OpenAI-compatible endpoint rejects temperature, top_p and json_object.
    client = make_client(["a", "b"], tmp_path, model_sampling=True, max_tokens=16000)
    key = client.chat_with_info(MESSAGES, json_mode=True)[1]["cache_key"]
    assert client._client.calls[0] == {"max_tokens": 16000}
    default = make_client(["c"], tmp_path, max_tokens=16000)
    assert default.chat_with_info(MESSAGES)[1]["cache_key"] != key  # never served a fixed-sampling answer


def test_run_flags_for_thinking_models_keep_run_names():
    from llmastar.run import build_generator, llm_variant, parse_args
    args = parse_args(["--method", "llmastar", "--model-sampling", "--max-tokens", "16000", "--timeout", "300"])
    assert llm_variant(args) is None  # a higher limit only leaves room; the folder tells the runs apart
    args.generator, args.prompt_set = "prompt", "gpt"
    client = build_generator(args).client
    assert client.model_sampling and client.timeout == 300 and client.sampling["max_tokens"] == 16000
