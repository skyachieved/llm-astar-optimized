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
