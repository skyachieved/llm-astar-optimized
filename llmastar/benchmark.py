"""The paper's benchmark: 100 maps x 10 start/goal pairs, and the evaluation of LLM-only paths."""
import json
import math
from pathlib import Path

from llmastar.utils import is_lines_collision

DEFAULT_DATASET = Path(__file__).resolve().parent.parent / "dataset" / "environment_50_30.json"


def _environments(data):
    """Normalise a dataset file's content to a list of environments with start_goal pairs.

    Accepted: the benchmark format (a list of environments, each with id, range_x, range_y, horizontal_barriers,
    vertical_barriers and start_goal), a single such environment, a single query (start, goal, range_x, range_y,
    horizontal_barriers, vertical_barriers), or a list of queries. A missing id becomes the item's position.
    """
    items = data if isinstance(data, list) else [data]
    environments = []
    for i, item in enumerate(items):
        if not isinstance(item, dict):
            raise ValueError(f"dataset item {i} is not a JSON object")
        if "start_goal" in item:
            env = dict(item)
        elif "start" in item and "goal" in item:  # a single query
            env = {k: v for k, v in item.items() if k not in ("start", "goal")}
            env["start_goal"] = [[item["start"], item["goal"]]]
        else:
            raise ValueError(f"dataset item {i} has neither start_goal nor start/goal")
        missing = [k for k in ("range_x", "range_y") if k not in env]
        if missing:
            raise ValueError(f"dataset item {i} is missing {', '.join(missing)}")
        env.setdefault("horizontal_barriers", [])
        env.setdefault("vertical_barriers", [])
        env.setdefault("id", env.get("map_id", i))
        environments.append(env)
    return environments


def load_queries(path=DEFAULT_DATASET, limit=None, select=None):
    """Queries in dataset order (map 0 sg 0..9, map 1 sg 0..9, ...), each a dict the pathers accept, plus
    map_id and sg_idx. `select` keeps only these (map_id, sg_idx) pairs; `limit` keeps the first N.
    The file may hold the benchmark format, one environment, one query or a list of queries (see _environments)."""
    with open(path) as f:
        environments = _environments(json.load(f))
    queries = []
    for environment in environments:
        for sg_idx, sg in enumerate(environment["start_goal"]):
            if select is not None and (environment["id"], sg_idx) not in select:
                continue
            queries.append({
                "map_id": environment["id"],
                "sg_idx": sg_idx,
                "start": list(sg[0]),
                "goal": list(sg[1]),
                "range_x": list(environment["range_x"]),
                "range_y": list(environment["range_y"]),
                "horizontal_barriers": environment["horizontal_barriers"],
                "vertical_barriers": environment["vertical_barriers"],
            })
    return queries[:limit] if limit else queries


def segment_collides(p, q, query):
    """The pathers' is_collision rule: barriers plus the map boundary lines at 0 and range max - 1."""
    x_lo, x_hi = query["range_x"][0], query["range_x"][1] - 1
    y_lo, y_hi = query["range_y"][0], query["range_y"][1] - 1
    line = [p, q]
    return any(is_lines_collision(line, [[h[1], h[0]], [h[2], h[0]]]) for h in query["horizontal_barriers"]) or \
        any(is_lines_collision(line, [[v[0], v[1]], [v[0], v[2]]]) for v in query["vertical_barriers"]) or \
        any(is_lines_collision(line, [[x, y_lo], [x, y_hi]]) for x in (x_lo, x_hi)) or \
        any(is_lines_collision(line, [[x_lo, y], [x_hi, y]]) for y in (y_lo, y_hi))


def _polyline_ok(points, query):
    return len(points) >= 2 and not any(segment_collides(a, b, query) for a, b in zip(points, points[1:]) if a != b)


def _polyline_length(points):
    return sum(math.dist(a, b) for a, b in zip(points, points[1:]))


def evaluate_llm_path(query, waypoints):
    """LLM-only baseline: the proposed waypoints are the path, with no search.

    valid:         the path starts at start, ends at goal, and no segment crosses a barrier or the boundary;
    valid_lenient: the same after inserting a missing start / goal (as LLM-A* does with its TARGET list).
    """
    start, goal = tuple(query["start"]), tuple(query["goal"])
    points = [tuple(p) for p in waypoints]
    valid = bool(points) and points[0] == start and points[-1] == goal and _polyline_ok(points, query)
    lenient = list(points)
    if not lenient or lenient[0] != start:
        lenient.insert(0, start)
    if lenient[-1] != goal:
        lenient.append(goal)
    return {"operation": None, "storage": None, "length": _polyline_length(points) if valid else None,
            "valid": valid, "valid_lenient": _polyline_ok(lenient, query), "path": points, "visited": []}
