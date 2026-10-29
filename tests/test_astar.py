import copy

import pytest

from llmastar.benchmark import evaluate_llm_path, load_queries
from llmastar.model.cache import DiskCache, cache_key
from llmastar.pather import AStar, DWAStar, LLMAStar
from llmastar.pather.llm_a_star.prompt import llama_prompt, llama_template_to_messages
from llmastar.waypoints import parse_waypoints


@pytest.fixture(scope="module")
def fig1_query():
    """Map id 1, start_goal[0]: the query of the paper's Figure 1."""
    (query,) = load_queries(select={(1, 0)})
    return query


def test_astar_matches_paper_figure1(fig1_query):
    result = AStar().searching(fig1_query)
    assert result["valid"]
    assert result["operation"] == 859
    assert result["storage"] == 802
    assert result["length"] == pytest.approx(53.46, abs=0.01)
    assert result["path"][0] == tuple(fig1_query["start"]) and result["path"][-1] == tuple(fig1_query["goal"])


def test_search_does_not_mutate_query(fig1_query):
    before = copy.deepcopy(fig1_query)
    AStar().searching(fig1_query)
    LLMAStar().searching(fig1_query, waypoints=[])
    assert fig1_query == before


@pytest.mark.parametrize("rekey", [False, True])
def test_dwastar_with_unit_weight_is_astar(fig1_query, rekey):
    astar = AStar().searching(fig1_query)
    dwa = DWAStar(w0=1.0, rekey=rekey).searching(fig1_query)
    assert (dwa["operation"], dwa["storage"]) == (astar["operation"], astar["storage"])


@pytest.mark.parametrize("options", [{}, {"rekey": False}, {"schedule": "depth"},
                                     {"min_weight": 0.0}, {"rekey": False, "min_weight": 0.0}])
def test_dwastar_runs(fig1_query, options):
    result = DWAStar(**options).searching(fig1_query)
    assert result["valid"] and result["length"] >= 53.46 - 0.01


def test_llmastar_without_waypoints_finds_valid_path(fig1_query):
    result = LLMAStar().searching(fig1_query, waypoints=[])
    assert result["valid"]
    assert result["llm_output"] == [tuple(fig1_query["start"]), tuple(fig1_query["goal"])]


def test_llm_only_straight_line_is_invalid(fig1_query):
    # Every dataset query's straight start-goal segment crosses an obstacle.
    result = evaluate_llm_path(fig1_query, [fig1_query["start"], fig1_query["goal"]])
    assert not result["valid"] and result["length"] is None


def test_parse_waypoints():
    assert parse_waypoints("Thought: ...\nGenerated Path: [[5, 5], [26, 9], [20, 20]]") == \
        ([(5, 5), (26, 9), (20, 20)], True)
    assert parse_waypoints("no list here") == ([], False)
    assert parse_waypoints("Generated Path: [[5, 5], [26, 9]") == ([], False)


@pytest.mark.parametrize("prompt,turns", [("standard", 5), ("cot", 3), ("repe", 3)])
def test_llama_template_to_messages(prompt, turns):
    messages = llama_template_to_messages(llama_prompt[prompt], start=[1, 2], goal=[3, 4],
                                          horizontal_barriers=[[10, 0, 25]], vertical_barriers=[[25, 10, 22]])
    assert [m["role"] for m in messages] == ["system"] + ["user", "assistant"] * turns + ["user"]
    assert all(m["content"] and "<|" not in m["content"] for m in messages)
    assert messages[-1]["content"].startswith("Start Point: [1, 2]\nGoal Point: [3, 4]")


def test_disk_cache_roundtrip(tmp_path):
    cache = DiskCache(tmp_path)
    key = cache_key({"model": "m", "messages": [{"role": "user", "content": "hi"}]})
    assert cache.get(key) is None
    cache.put(key, {"response": {"content": "hello"}})
    assert cache.get(key) == {"response": {"content": "hello"}}
    assert key == cache_key({"messages": [{"role": "user", "content": "hi"}], "model": "m"})
