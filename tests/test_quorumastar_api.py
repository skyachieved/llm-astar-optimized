"""The submission interface: QuorumAStar(llm=...).searching(query=..., filepath=...), as LLMAStar in the baseline
repository, so hidden maps run without edits. No network."""
import json

import pytest

from llmastar.benchmark import load_queries
from llmastar.model import ChatGPT
from llmastar.pather import LLMAStar, QuorumAStar
from llmastar.quorumastar import QuorumAStarGenerator, QuorumConfig
from tests.test_quorumastar_generator import EXAMPLE, ScriptedModel, _ids


@pytest.fixture
def no_keys(monkeypatch):
    import openai
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setattr(openai, "api_key", None, raising=False)


def test_llm_gpt_builds_quorumastar_on_gpt4o_mini():
    search = QuorumAStar(llm="gpt")
    assert isinstance(search.generator, QuorumAStarGenerator)
    assert isinstance(search.generator.client, ChatGPT) and search.generator.client.model == "gpt-4o-mini"
    assert search.config == QuorumConfig(prompt_set="gpt") and (search.stall_k, search.stall_min) == (2.0, 20)


def test_same_result_keys_as_llmastar_plus_fallback(no_keys):
    (query,) = load_queries(select={(1, 0)})
    with pytest.warns(UserWarning, match="searching without waypoints"):
        ours = QuorumAStar(llm="gpt").searching(query=query)  # no key: every view fails, the search still runs
    base = LLMAStar().searching(query, waypoints=[])
    assert set(ours) == set(base) | {"fallback"}
    assert ours["valid"] and ours["llm_output"] == base["llm_output"]


def test_end_to_end_with_a_chat_client(tmp_path):
    corner = (14, 15)
    model = ScriptedModel(text=json.dumps({"waypoints": [corner]}), corners=_ids([corner], EXAMPLE),
                          image=json.dumps({"waypoints": [corner]}), judge='{"remove": []}')
    result = QuorumAStar(llm=model).searching(query=EXAMPLE, filepath=str(tmp_path / "plot.png"))
    assert result["valid"] and corner in result["llm_output"] and (tmp_path / "plot.png").exists()


def test_stall_arguments_override_the_config():
    search = QuorumAStar(stall_k=0, config=QuorumConfig(stall_k=3, stall_min=5))
    assert (search.stall_k, search.stall_min) == (0, 5)


def test_bad_llm_name():
    with pytest.raises(ValueError):
        QuorumAStar(llm="claude")
