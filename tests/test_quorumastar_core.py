"""Step 2d part 1: the deterministic Quorum-A* stages (no LLM). The worked example is agent.md's teaching example."""
import pytest

from llmastar.benchmark import load_queries
from llmastar.pather import LLMAStar
from llmastar.quorumastar.canonical import canonicalize, snap_cell
from llmastar.quorumastar.geometry import collides, corner_nodes, passes_filter
from llmastar.quorumastar.pruning import majority_remove
from llmastar.quorumastar.voting import majority_add

# The worked example in agent.md: cells and an invented map where A->B and B->G cross a wall.
A, B, C, D = (10, 12), (25, 20), (40, 8), (5, 25)
EXAMPLE = {"start": [5, 10], "goal": [45, 12], "range_x": [0, 51], "range_y": [0, 31],
           "horizontal_barriers": [[16, 15, 40]], "vertical_barriers": []}


@pytest.fixture(scope="module")
def queries():
    return load_queries(select={(1, 0), (7, 2), (42, 5)})


# ---- geometry -----------------------------------------------------------------------------------------------------

def test_filter_is_the_search_filter(queries):
    for query in queries:
        search = LLMAStar()
        search._initialize_parameters(dict(query, range_x=list(query["range_x"]), range_y=list(query["range_y"])))
        cells = [(x, y) for x in range(-1, 53) for y in range(-1, 33)]
        assert [c for c in cells if passes_filter(c, query)] == search._filter_valid_nodes(cells)


def test_corner_nodes_are_free_and_diagonal_to_barrier_ends():
    corners = corner_nodes(EXAMPLE)  # wall y = 16, x = 15..40 -> ends at x = 14 and 41, one cell above and below
    assert corners == [(14, 15), (14, 17), (41, 15), (41, 17)]
    assert all(passes_filter(c, EXAMPLE) for c in corners)


# ---- canonicalization ---------------------------------------------------------------------------------------------

def test_snap_rounds_half_up_and_leaves_free_cells():
    assert snap_cell((9.5, 12.4), EXAMPLE) == (10, 12)


def test_snap_moves_a_wall_cell_to_the_nearest_free_cell():
    on_wall = (20, 16)
    assert not passes_filter(on_wall, EXAMPLE)
    snapped = snap_cell(on_wall, EXAMPLE)
    assert passes_filter(snapped, EXAMPLE) and max(abs(snapped[0] - 20), abs(snapped[1] - 16)) == 1


def test_points_far_outside_are_dropped():
    cells, dropped = canonicalize([(100, 100), A], EXAMPLE)
    assert dropped == [(100, 100)] and cells == [A]


def test_points_near_a_corner_become_that_corner_and_duplicates_collapse():
    cells, _ = canonicalize([(13, 15), (14.4, 14.6), A], EXAMPLE)
    assert cells == [(14, 15), A]


# ---- majority add (worked example) --------------------------------------------------------------------------------

def test_worked_example_add():
    vote = majority_add([[A, B, C], [A, B], [A, B, D]], quorum=2)
    assert vote.waypoints == [A, B]
    assert vote.support == {A: 3, B: 3}
    assert vote.position[A] == pytest.approx((1 / 4 + 1 / 3 + 1 / 4) / 3)  # 0.28
    assert vote.position[B] == pytest.approx((2 / 4 + 2 / 3 + 2 / 4) / 3)  # 0.56


def test_add_is_the_identity_for_one_view_at_quorum_one():
    raw = [B, A, A, (5.5, 7.25)]
    assert majority_add([raw], quorum=1).waypoints == raw  # order, duplicates and floats kept


def test_add_orders_by_mean_position_then_view_order():
    vote = majority_add([[A, B], [B, A]], quorum=2)  # equal means: first appearance in view order wins
    assert vote.waypoints == [A, B]


# ---- majority remove (worked example) -----------------------------------------------------------------------------

def test_worked_example_geometry():
    s, g = tuple(EXAMPLE["start"]), tuple(EXAMPLE["goal"])
    assert not collides(s, A, EXAMPLE) and collides(A, B, EXAMPLE) and collides(B, g, EXAMPLE)


def test_worked_example_remove():
    pruned = majority_remove([A, B], EXAMPLE, quorum=2, support={A: 3, B: 3}, n_answered=3, vision_remove=[2])
    assert pruned.waypoints == [A]
    check_b = pruned.checks[1]
    assert (check_b["code"], check_b["vision"], check_b["support"], check_b["removed"]) == (True, True, False, True)


def test_an_abstaining_judge_objects_to_nothing():
    pruned = majority_remove([A, B], EXAMPLE, quorum=2, support={A: 3, B: 3}, n_answered=3, vision_remove=None)
    assert pruned.waypoints == [A, B]  # only the code check objects to B: 1 < 2


def test_low_support_plus_code_removes():
    pruned = majority_remove([A, B], EXAMPLE, quorum=2, support={A: 3, B: 2}, n_answered=3)
    assert pruned.waypoints == [A]


def test_one_answering_view_never_triggers_support():
    pruned = majority_remove([A, B], EXAMPLE, quorum=2, support={A: 1, B: 1}, n_answered=1)
    assert pruned.waypoints == [A, B]


def test_quorum_zero_is_off():
    assert majority_remove([A, B], EXAMPLE, quorum=0).waypoints == [A, B]
