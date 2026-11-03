"""Step 2a: the no-op `_after_pop` hook and QuorumAStar's stall fallback (METHOD.md 4.7, 7)."""
import copy

import pytest

from llmastar.benchmark import load_queries
from llmastar.pather import AStar, LLMAStar, QuorumAStar

FIXED = {(1, 0), (1, 3), (7, 2), (23, 8), (42, 5), (77, 1)}
METRICS = ("operation", "storage", "length", "path", "llm_output")


@pytest.fixture(scope="module")
def queries():
    return load_queries(select=FIXED)


def _metrics(result):
    return tuple(result[k] for k in METRICS)


def test_hook_is_a_no_op_in_llmastar():
    assert LLMAStar._after_pop(LLMAStar(), (0, 0)) is None


def test_astar_still_matches_paper(queries):
    (query,) = [q for q in queries if (q["map_id"], q["sg_idx"]) == (1, 0)]
    result = AStar().searching(query)
    assert (result["operation"], result["storage"]) == (859, 802)
    assert result["length"] == pytest.approx(53.46, abs=0.01)


@pytest.mark.parametrize("waypoints", [[], [(24, 16)], [(44, 24), (24, 16), (5, 6)], [(10, 10), (30, 20)]])
def test_stall_k_zero_is_llmastar(queries, waypoints):
    for query in queries:
        base = LLMAStar().searching(query, waypoints=waypoints)
        ours = QuorumAStar(stall_k=0).searching(query, waypoints=waypoints)
        assert _metrics(ours) == _metrics(base)
        assert ours["fallback"] is None


def test_search_does_not_mutate_query(queries):
    before = copy.deepcopy(queries)
    for query in queries:
        QuorumAStar().searching(query, waypoints=[(10, 10)])
    assert queries == before


def test_fallback_fires_on_an_unreachable_target(queries):
    """A waypoint hidden in a spot the search cannot reach soon stalls the search, so the fallback must fire."""
    (query,) = [q for q in queries if (q["map_id"], q["sg_idx"]) == (1, 0)]
    # A tiny budget makes any non-goal target stall after a few pops.
    search = QuorumAStar(stall_k=0.01, stall_min=1)
    result = search.searching(query, waypoints=[(24, 16), (5, 6)])
    assert result["valid"]
    assert result["fallback"] is not None
    assert result["fallback"]["target"] == (24, 16)
    assert result["fallback"]["dropped"] == [(5, 6)] or result["fallback"]["dropped"] == [(24, 16), (5, 6)]
    assert result["llm_output"][-1] == tuple(query["goal"])
    assert len(result["llm_output"]) <= 3  # the dropped waypoint is no longer a target


def test_after_fallback_search_is_weighted_astar(queries):
    """Once the fallback fires at the very first pop, the rest of the search equals LLM-A* with no waypoints."""
    (query,) = [q for q in queries if (q["map_id"], q["sg_idx"]) == (1, 0)]
    none = LLMAStar().searching(query, waypoints=[])
    ours = QuorumAStar(stall_k=1e-9, stall_min=0).searching(query, waypoints=[(24, 16)])
    assert ours["fallback"]["pop"] == 1
    assert (ours["storage"], ours["length"], ours["path"]) == (none["storage"], none["length"], none["path"])


def test_fallback_fires_at_most_once(queries):
    (query,) = [q for q in queries if (q["map_id"], q["sg_idx"]) == (1, 0)]
    search = QuorumAStar(stall_k=0.01, stall_min=1)
    result = search.searching(query, waypoints=[(44, 24), (24, 16), (5, 6)])
    assert result["fallback"]["pop"] == search.fallback["pop"]
    assert result["llm_output"][-1] == tuple(query["goal"])


def test_budget_scales_with_k(queries):
    """Finding (2026-11-03): on the Fig. 1 query with the paper's waypoints, k = 2 fires at pop 80 (budget 56 for
    the (24, 15) -> (5, 6) leg, 57 pops used) one pop before the target would have been reached; k = 3 never fires.
    The result is unchanged either way (the dropped target was one cell from the goal). The default k is NOT chosen
    here (map 1 is an evaluation map): the pilot on self-generated maps decides it. This test only pins the mechanics.
    """
    (query,) = [q for q in queries if (q["map_id"], q["sg_idx"]) == (1, 0)]
    paper = [(44, 24), (24, 16), (5, 6)]
    at_k2 = QuorumAStar(stall_k=2).searching(query, waypoints=paper)
    at_k3 = QuorumAStar(stall_k=3).searching(query, waypoints=paper)
    assert at_k2["fallback"] is not None and at_k2["fallback"]["target"] == (5, 6)
    assert at_k3["fallback"] is None
    for result in (at_k2, at_k3):
        assert result["length"] == pytest.approx(53.46, abs=0.01)
