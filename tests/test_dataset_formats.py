"""Step 2.0e: `--dataset` takes the benchmark file, one environment, one query or a list of queries, so the code
runs on unseen maps without edits."""
import json

import pytest

from llmastar.benchmark import DEFAULT_DATASET, load_queries
from llmastar.pather import AStar

with open(DEFAULT_DATASET) as f:
    ENV = json.load(f)[1]  # map 1
QUERY = {"start": ENV["start_goal"][0][0], "goal": ENV["start_goal"][0][1], "range_x": ENV["range_x"],
         "range_y": ENV["range_y"], "horizontal_barriers": ENV["horizontal_barriers"],
         "vertical_barriers": ENV["vertical_barriers"]}


def _write(tmp_path, data):
    path = tmp_path / "data.json"
    path.write_text(json.dumps(data))
    return path


@pytest.mark.parametrize("data,n", [([ENV], 10), (ENV, 10), (QUERY, 1), ([QUERY, QUERY], 2)])
def test_formats_load(tmp_path, data, n):
    queries = load_queries(_write(tmp_path, data))
    assert len(queries) == n
    result = AStar().searching(queries[0])
    assert (result["operation"], result["storage"]) == (859, 802)  # map 1 / sg 0 whatever the wrapping


def test_bad_items_say_what_is_wrong(tmp_path):
    with pytest.raises(ValueError, match="neither start_goal nor start/goal"):
        load_queries(_write(tmp_path, {"range_x": [0, 51]}))
    with pytest.raises(ValueError, match="missing range_y"):
        load_queries(_write(tmp_path, {"start": [1, 1], "goal": [2, 2], "range_x": [0, 51]}))


def test_runner_on_a_single_query_file(tmp_path):
    from llmastar import run
    run.main(["--method", "astar", "--dataset", str(_write(tmp_path, QUERY)), "--out", str(tmp_path), "--jobs", "1",
              "--trace"])
    assert (tmp_path / "llama-3-8b-instruct" / "astar.csv").exists()


def test_table1_in_one_command(tmp_path, monkeypatch):
    """All Table 1 rows plus summary.md, with a mock text-only model registered as a generator."""
    from llmastar import table1
    from llmastar.waypoints import REGISTRY, PromptWaypointGenerator

    class TextClient:
        def chat_with_info(self, messages):
            return "Generated Path: [[45, 25], [24, 16], [5, 5]]", {"cached": False}

    monkeypatch.setitem(REGISTRY, "mock", lambda client, args: PromptWaypointGenerator(TextClient(), args.prompt))
    table1.main(["--generator", "mock", "--limit", "2", "--jobs", "1", "--out", str(tmp_path)])
    model_dir = tmp_path / "llama-3-8b-instruct"
    names = {p.stem for p in model_dir.glob("*.csv")}
    assert {"astar", "dwastar", "llmastar_mock", "llm_only_mock", "summary"} <= names
    assert (model_dir / "summary.md").exists()
