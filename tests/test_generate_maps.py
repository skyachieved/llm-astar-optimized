"""Harder generated maps (agent.md step 6): deterministic, in the benchmark format, solvable, straight line blocked."""
import json

import pytest

from llmastar.benchmark import load_queries, segment_collides
from llmastar.generate_maps import make_maps


@pytest.mark.parametrize("kind,size", [("dense", 3), ("large", 2), ("zigzag", 3)])
def test_maps_are_deterministic_loadable_and_blocked(kind, size, tmp_path):
    maps = make_maps(kind, size, seed=1)
    assert maps == make_maps(kind, size, seed=1) and maps != make_maps(kind, size, seed=2)
    path = tmp_path / f"{kind}.json"
    path.write_text(json.dumps(maps))
    queries = load_queries(str(path))
    assert len(queries) == size
    for q in queries:
        assert segment_collides(q["start"], q["goal"], q)
    if kind == "large":
        assert queries[0]["range_x"] == [0, 101] and queries[0]["range_y"] == [0, 61]


def test_zigzag_gaps_alternate_top_and_bottom():
    for m in make_maps("zigzag", 3, seed=1):
        walls = sorted(m["vertical_barriers"])
        assert 3 <= len(walls) <= 5 and not m["horizontal_barriers"]
        for i, (x, y1, y2) in enumerate(walls):
            assert (y1 == 0) if i % 2 == 0 else (y2 == 30)  # gap at the top, then at the bottom, ...
        start, goal = m["start_goal"][0]
        assert start[0] < walls[0][0] and goal[0] > walls[-1][0]


def test_committed_datasets_match_the_generator():
    for kind in ("dense", "zigzag"):
        with open(f"dataset/generated/{kind}.json") as f:
            assert json.load(f)[:3] == make_maps(kind, 3, seed=1)
