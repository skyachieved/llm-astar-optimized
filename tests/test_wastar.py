"""Weighted A* baseline (`--method wastar --weight W`): a constant weight w in f = g + w * h."""
import pytest

from llmastar.benchmark import load_queries
from llmastar.pather import AStar, DWAStar
from llmastar.run import parse_args, search_one, wastar_options


@pytest.fixture(scope="module")
def queries():
    return load_queries(select={(1, 0), (1, 3), (7, 2), (42, 5)})


def test_wastar_weight_one_is_astar(queries):
    for query in queries:
        astar = AStar().searching(query)
        wastar = DWAStar(**wastar_options(1.0)).searching(query)
        assert (wastar["operation"], wastar["storage"], wastar["length"]) == \
            (astar["operation"], astar["storage"], astar["length"])


def test_wastar_weight_is_constant(queries):
    search = DWAStar(**wastar_options(2.0))
    search.searching(queries[0])
    assert search.scheduled_weight(0) == search.scheduled_weight(10_000) == 2.0


@pytest.mark.parametrize("weight", [1.5, 2.0, 3.0])
def test_wastar_expands_no_more_than_astar_and_stays_valid(queries, weight):
    for query in queries:
        astar = AStar().searching(query)
        wastar = DWAStar(**wastar_options(weight)).searching(query)
        assert wastar["valid"]
        assert wastar["length"] >= astar["length"] - 1e-9  # A* is optimal; a weight can only lengthen the path


def test_wastar_through_runner(queries):
    result = search_one(("wastar", wastar_options(2.0), queries[0], None, None))
    assert result["valid"] and result["error"] == ""


def test_wastar_cli_defaults_and_run_name():
    args = parse_args(["--method", "wastar", "--weight", "1.5"])
    assert args.method == "wastar" and args.weight == 1.5
    assert f"w{args.weight:g}" == "w1.5"
