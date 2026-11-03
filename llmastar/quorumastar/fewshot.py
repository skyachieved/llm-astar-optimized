"""Few-shot examples from self-generated maps (METHOD.md 4.2). The evaluation maps are never used.

A pool map is a random map on the benchmark's grid (51 x 31) with the same barrier format. Its generator parameters
are fixed a priori, not fitted to the benchmark. A map is accepted only if (a) its straight start-goal segment
collides and (b) its gold waypoints all snap to corner nodes. Gold waypoints: the A* path is string-pulled (greedy
line-of-sight shortcutting with the search's collision rule), and its interior points are canonicalized.
"""
import random
from functools import lru_cache

from llmastar.pather import AStar

from .canonical import snap_corner
from .geometry import collides, corner_nodes, passes_filter

GRID_X, GRID_Y = (0, 51), (0, 31)
N_HORIZONTAL, N_VERTICAL = (1, 3), (1, 3)  # barriers per map
H_LENGTH, V_LENGTH = (8, 22), (6, 16)  # barrier length in cells
MIN_START_GOAL = 15  # Euclidean distance between start and goal
MAX_TRIES = 10_000


def string_pull(path, query):
    """Greedy line-of-sight shortcutting: from each kept point, jump to the farthest later point it can see."""
    if len(path) <= 2:
        return list(path)
    pulled, i = [path[0]], 0
    while i < len(path) - 1:
        j = len(path) - 1
        while j > i + 1 and collides(path[i], path[j], query):
            j -= 1
        pulled.append(path[j])
        i = j
    return pulled


def _random_map(rng):
    horizontal, vertical = [], []
    for _ in range(rng.randint(*N_HORIZONTAL)):
        length = rng.randint(*H_LENGTH)
        x1 = rng.randint(GRID_X[0], GRID_X[1] - 1 - length)
        horizontal.append([rng.randint(4, GRID_Y[1] - 5), x1, x1 + length])
    for _ in range(rng.randint(*N_VERTICAL)):
        length = rng.randint(*V_LENGTH)
        y1 = rng.randint(GRID_Y[0], GRID_Y[1] - 1 - length)
        vertical.append([rng.randint(4, GRID_X[1] - 5), y1, y1 + length])
    return {"range_x": list(GRID_X), "range_y": list(GRID_Y),
            "horizontal_barriers": horizontal, "vertical_barriers": vertical}


def _random_free_cell(rng, query):
    while True:
        cell = (rng.randint(GRID_X[0] + 2, GRID_X[1] - 3), rng.randint(GRID_Y[0] + 2, GRID_Y[1] - 3))
        if passes_filter(cell, query):
            return cell


def gold_waypoints(query):
    """Canonical interior points of the string-pulled A* path, or None if one of them is not a corner node."""
    result = AStar().searching(query)
    if not result["valid"]:
        return None
    pulled = string_pull([tuple(p) for p in result["path"]], query)
    corners = corner_nodes(query)
    corner_set = set(corners)
    gold = []
    for point in pulled[1:-1]:
        cell = snap_corner(point, corners)
        if cell not in corner_set:
            return None
        if not gold or gold[-1] != cell:
            gold.append(cell)
    return gold or None


@lru_cache(maxsize=16)
def pool(seed=0, size=12):
    """`size` accepted examples, each a dict: query fields plus "gold" (list of cells). Deterministic in `seed`."""
    rng = random.Random(f"quorumastar-fewshot-{seed}")
    examples = []
    for _ in range(MAX_TRIES):
        if len(examples) == size:
            break
        query = _random_map(rng)
        start = _random_free_cell(rng, query)
        goal = _random_free_cell(rng, query)
        if ((start[0] - goal[0]) ** 2 + (start[1] - goal[1]) ** 2) ** 0.5 < MIN_START_GOAL:
            continue
        query.update(start=list(start), goal=list(goal))
        if not collides(start, goal, query):
            continue
        gold = gold_waypoints(query)
        if gold:
            examples.append({**query, "gold": gold})
    if len(examples) < size:
        raise RuntimeError(f"few-shot pool: only {len(examples)} of {size} maps accepted")
    return tuple(examples)


def examples_for(view_index, mode, n_shots=3, seed=0, n_views=3):
    """The examples a view gets: per-view = pool[3k, 3k+3) (no shared map), shared = pool[0, 3), none = []."""
    if mode == "none" or n_shots <= 0:
        return []
    if mode == "shared":
        return list(pool(seed, n_shots))
    examples = pool(seed, n_shots * max(n_views, 1))
    return list(examples[view_index * n_shots:(view_index + 1) * n_shots])
