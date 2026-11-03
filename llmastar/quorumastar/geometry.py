"""Map geometry shared by the Quorum-A* stages. Every rule here mirrors the search's own (no new geometry)."""
import math
from functools import lru_cache

from llmastar.benchmark import segment_collides
from llmastar.env.search import env


def _key(query):
    return (tuple(query["range_x"]), tuple(query["range_y"]),
            tuple(map(tuple, query["horizontal_barriers"])), tuple(map(tuple, query["vertical_barriers"])))


@lru_cache(maxsize=256)
def _obstacles(key):
    range_x, range_y, horizontal, vertical = key
    return frozenset(env.Env(range_x[1], range_y[1], [list(h) for h in horizontal], [list(v) for v in vertical]).obs)


def obstacles(query):
    """The search's obstacle cells (barrier cells and the map border)."""
    return _obstacles(_key(query))


def passes_filter(cell, query):
    """LLMAStar._filter_valid_nodes for one cell: not an obstacle and strictly inside the map with a one-cell margin
    (2 <= x <= 48 and 2 <= y <= 28 on the benchmark's 51 x 31 grid)."""
    x, y = cell[0], cell[1]
    (x0, x1), (y0, y1) = query["range_x"], query["range_y"]
    return (x, y) not in obstacles(query) and x0 + 1 < x < x1 - 2 and y0 + 1 < y < y1 - 2


def collides(p, q, query):
    """True if the straight segment p-q crosses a barrier or the border (the search's collision rule)."""
    return tuple(p) != tuple(q) and segment_collides(list(p), list(q), query)


def corner_nodes(query):
    """Free cells diagonal to a barrier end, where a shortest path can bend (METHOD.md 4.1, corners view).
    Only cells that pass the waypoint filter are kept, deduplicated and sorted by (x, y); the index is the node id."""
    cells = set()
    for y, x1, x2 in query["horizontal_barriers"]:
        for x in (x1 - 1, x2 + 1):
            cells.update({(x, y - 1), (x, y + 1)})
    for x, y1, y2 in query["vertical_barriers"]:
        for y in (y1 - 1, y2 + 1):
            cells.update({(x - 1, y), (x + 1, y)})
    return sorted(c for c in cells if passes_filter(c, query))


def distance(p, q):
    return math.dist(p, q)
