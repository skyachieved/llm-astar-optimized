"""Pilot tooling (METHOD.md 11): self-generated maps, the bad-waypoint ground truth, the offline vote simulation."""
import json

import pytest

from llmastar.benchmark import load_queries
from llmastar.quorumastar import pilot
from llmastar.quorumastar.fewshot import pool
from llmastar.quorumastar.voting import majority_add

EXAMPLE = {"start": [5, 10], "goal": [45, 12], "range_x": [0, 51], "range_y": [0, 31],
           "horizontal_barriers": [[16, 15, 40]], "vertical_barriers": []}


@pytest.fixture(scope="module")
def maps():
    return pilot.make_maps(size=6, seed=1)


def test_maps_are_deterministic_loadable_and_disjoint_from_the_pool(maps, tmp_path):
    assert maps == pilot.make_maps(size=6, seed=1)
    assert maps != pilot.make_maps(size=6, seed=2)
    examples = {json.dumps([e["horizontal_barriers"], e["vertical_barriers"]]) for e in pool(0, 12)}
    assert not any(json.dumps([m["horizontal_barriers"], m["vertical_barriers"]]) in examples for m in maps)
    path = tmp_path / "pilot.json"
    path.write_text(json.dumps(maps))
    queries = load_queries(str(path))
    assert [(q["map_id"], q["sg_idx"]) for q in queries] == [(i, 0) for i in range(6)]


def test_bad_waypoint_ground_truth():
    assert pilot.is_bad((16, 16), EXAMPLE)  # on the wall
    assert pilot.is_bad((1, 1), EXAMPLE)  # outside the filter's margin
    # the straight start-goal segment (y 10..12) passes under the wall, so a point on it is good and a detour is bad
    assert not pilot.is_bad((25, 11), EXAMPLE)
    assert pilot.is_bad((14, 15), EXAMPLE)  # the wall's corner: 5 cells up and back, > 5% longer
    assert pilot.is_bad((25, 28), EXAMPLE)  # above the wall: a long detour
    blocked = dict(EXAMPLE, goal=[25, 25])  # now the wall is in the way: its left-end corner is on a shortest path
    assert not pilot.is_bad((14, 17), blocked)


def test_simulated_vote_radius_zero_keeps_what_majority_add_keeps():
    lists = [[(24, 9), (30, 12)], [(26, 9), (30, 12)], [(24, 9), (5, 5)]]
    assert set(pilot.simulate_vote(lists, 0)) == set(majority_add(lists, 2).waypoints) == {(24, 9), (30, 12)}


def test_simulated_vote_radius_merges_the_two_sides_of_one_wall_end():
    lists = [[(24, 9)], [(26, 9)], [(10, 20)]]
    assert pilot.simulate_vote(lists, 0) == []
    assert pilot.simulate_vote(lists, 2) == [(24, 9)]  # a tie goes to the earliest view
    assert pilot.simulate_vote([[(24, 9)], [(26, 9)], [(26, 9)]], 2) == [(26, 9)]  # most views wins
    assert pilot.simulate_vote([[(24, 9), (26, 9)], [(30, 30)]], 2) == []  # one view alone is no quorum


def test_report_runs_on_a_raw_log(maps, tmp_path):
    directory = tmp_path / "gpt-4o-mini"
    (directory / "raw").mkdir(parents=True)
    dataset = tmp_path / "pilot.json"
    dataset.write_text(json.dumps(maps))
    queries = load_queries(str(dataset))
    with open(directory / "raw" / "quorumastar.jsonl", "w") as f:
        for q in queries:
            s, g = q["start"], q["goal"]
            views = [{"view": "text", "abstained": False, "error": "", "cells": [s]},
                     {"view": "corners", "abstained": False, "error": "", "cells": [s, g]},
                     {"view": "image", "abstained": True, "error": "", "response": "?"}]
            f.write(json.dumps({"map_id": q["map_id"], "sg_idx": q["sg_idx"], "views": views,
                                "votes": [{"cell": s, "support": 2}],
                                "judge": {"abstained": False, "remove": [1]}, "waypoints": [],
                                "calls": 3, "prompt_tokens": 100, "completion_tokens": 10}) + "\n")
    text = pilot.report(directory, "quorumastar", str(dataset))
    assert "| image | 6/6 |" in text
    assert "As run: 6/6" in text
    assert (directory / "pilot_quorumastar.md").exists()
