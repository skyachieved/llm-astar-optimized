import re
from dataclasses import dataclass, field
from typing import Protocol

from llmastar.utils import list_parse


@dataclass
class WaypointResult:
    """Waypoints proposed for one query, before LLM-A* filters them against the map."""
    waypoints: list  # [(x, y), ...] in proposed order; may be empty
    parse_ok: bool  # False if no waypoint list could be read from the model output
    raw: dict = field(default_factory=dict)  # JSON-serializable log record, written to outputs/<model>/raw/


class WaypointGenerator(Protocol):
    """Maps a query (map + start/goal, as loaded by llmastar.benchmark) to waypoints. Must be thread-safe:
    the runner calls `generate` from several threads at once."""
    name: str

    def generate(self, query: dict) -> WaypointResult: ...


_LIST = re.compile(r"\[\[.*?\]\]", re.S)


def _is_number(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def parse_waypoints(text):
    """Read the last [[x, y], ...] list in `text` (the original code's rule) as (x, y) tuples.

    Entries with more than two numbers keep their first two, as the original node filter did;
    anything else non-numeric is dropped. Returns (waypoints, parse_ok).
    """
    if not text or not _LIST.search(text):
        return [], False
    nodes = list_parse(text)
    if not isinstance(nodes, (list, tuple)):  # list_parse returns an error string on bad syntax
        return [], False
    points = [(node[0], node[1]) for node in nodes
              if isinstance(node, (list, tuple)) and len(node) >= 2 and _is_number(node[0]) and _is_number(node[1])]
    return points, bool(points)
