"""Reading the views' answers (METHOD.md 4.1): JSON first (code fences stripped), then the last bracketed list."""
import json
import re

from llmastar.waypoints import parse_waypoints

_FENCE = re.compile(r"```(?:json)?\s*(.*?)```", re.S)
_OBJECT = re.compile(r"\{.*\}", re.S)
_INT_LIST = re.compile(r"\[\s*(?:-?\d+\s*(?:,\s*-?\d+\s*)*)?\]")


def _json_candidates(text):
    fenced = _FENCE.findall(text)
    yield from reversed(fenced)
    yield text
    found = _OBJECT.findall(text)
    yield from reversed(found)


def _load(text, key):
    for candidate in _json_candidates(text):
        try:
            value = json.loads(candidate.strip())
        except (json.JSONDecodeError, ValueError):
            continue
        if isinstance(value, dict) and isinstance(value.get(key), list):
            return value[key]
        if isinstance(value, list):
            return value
    return None


def _is_number(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def parse_points(text):
    """Coordinate answers: {"waypoints": [[x, y], ...]}, else the last [[x, y], ...] in the text.
    Returns (points, ok)."""
    text = text or ""
    items = _load(text, "waypoints")
    if items is not None:
        points = [(p[0], p[1]) for p in items
                  if isinstance(p, (list, tuple)) and len(p) >= 2 and _is_number(p[0]) and _is_number(p[1])]
        if points or items == []:
            return points, True
    return parse_waypoints(text)


def parse_ids(text, key="waypoints"):
    """Integer-id answers: {"waypoints": [3, 7]} (corners view) or {"remove": [2]} (vision judge), else the last
    flat list of integers in the text. Strings such as "S" / "G" and non-integers are dropped. Returns (ids, ok)."""
    text = text or ""
    items = _load(text, key)
    if items is None:
        found = _INT_LIST.findall(text)
        if not found:
            return [], False
        items = json.loads(found[-1])
    ids = []
    for item in items:
        if isinstance(item, bool):
            continue
        if isinstance(item, int) or (isinstance(item, float) and item.is_integer()):
            ids.append(int(item))
        elif isinstance(item, str) and item.strip().isdigit():
            ids.append(int(item.strip()))
    return ids, True
