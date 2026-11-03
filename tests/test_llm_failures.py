"""Step 2.0c: an LLM failure never stops a search or a run; it becomes "no waypoints" plus an llm_error."""
import csv

import pytest

from llmastar.benchmark import load_queries
from llmastar.pather import LLMAStar
from llmastar.waypoints import REGISTRY, PromptWaypointGenerator


class DownClient:
    """A chat client whose every call fails, as ChatGPT reports it."""

    def chat_with_info(self, messages):
        return "", {"error": "APIConnectionError: Connection error.", "cached": False}


class RaisingClient:
    """A client without the error contract (e.g. the local Llama3 pipeline) that raises."""

    def chat(self, messages):
        raise RuntimeError("CUDA out of memory")


class TextClient:
    """A text-only mock model that answers with fixed waypoints."""

    def chat_with_info(self, messages):
        return "Generated Path: [[45, 25], [24, 16], [5, 5]]", {"cached": False}


@pytest.fixture(scope="module")
def query():
    (q,) = load_queries(select={(1, 0)})
    return q


@pytest.mark.parametrize("client", [DownClient(), RaisingClient()])
def test_generator_never_raises(query, client):
    result = PromptWaypointGenerator(client).generate(query)
    assert result.waypoints == [] and not result.parse_ok and result.raw["llm_error"]


def test_search_with_a_failing_llm_is_llmastar_without_waypoints(query):
    with pytest.warns(UserWarning, match="searching without waypoints"):
        failed = LLMAStar(llm=DownClient()).searching(query)
    none = LLMAStar().searching(query, waypoints=[])
    assert failed["valid"] and (failed["operation"], failed["storage"]) == (none["operation"], none["storage"])


def test_mock_text_model_drives_the_search(query):
    result = LLMAStar(llm=TextClient()).searching(query)
    assert result["valid"] and (24, 16) in result["llm_output"]


def test_llm_gpt_without_key_still_searches(query, monkeypatch):
    import openai
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setattr(openai, "api_key", None, raising=False)
    with pytest.warns(UserWarning, match="No API key"):
        result = LLMAStar(llm="gpt").searching(query)  # no network: the missing key fails before any request
    assert result["valid"] and result["llm_output"] == [tuple(query["start"]), tuple(query["goal"])]


def test_run_records_llm_errors_and_finishes(tmp_path, capsys, monkeypatch):
    from llmastar import run
    monkeypatch.setitem(REGISTRY, "down", lambda client, args: PromptWaypointGenerator(DownClient()))
    run.main(["--method", "llmastar", "--generator", "down", "--limit", "3", "--jobs", "1", "--trace",
              "--out", str(tmp_path), "--cache-dir", str(tmp_path / "cache")])
    out = capsys.readouterr().out
    assert "3/3 LLM calls failed" in out and "llm_errors=3" in out
    with open(tmp_path / "llama-3-8b-instruct" / "llmastar_down.csv", newline="") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 3 and all(r["llm_error"] and r["valid"] == "1" and r["n_targets"] == "2" for r in rows)
