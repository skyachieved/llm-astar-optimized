"""Majority remove (METHOD.md 3, 4.5): delete a waypoint when at least `quorum` independent checks object.

On the path P = [start] + W + [goal], for each waypoint w = P[i]:
  code     both segments P[i-1]-w and w-P[i+1] cross a wall (the search's collision rule)
  vision   the vision judge listed w's number (1..n) for removal; a judge that abstained objects to nothing
  support  fewer views proposed w than answered
Every check sees the same list (one pass), so the order of evaluation does not matter.
"""
from dataclasses import dataclass, field

from .geometry import collides


@dataclass
class Pruning:
    waypoints: list  # kept, in order
    checks: list = field(default_factory=list)  # per input waypoint: dict(waypoint, code, vision, support, removed)


def majority_remove(waypoints, query, quorum=2, support=None, n_answered=1, vision_remove=None):
    """`vision_remove`: 1-based numbers the vision judge wants removed, or None if vision is off or abstained."""
    if quorum <= 0:
        return Pruning(list(waypoints), [])
    path = [tuple(query["start"])] + [tuple(w) for w in waypoints] + [tuple(query["goal"])]
    support = support or {}
    vision_remove = set(vision_remove or ())
    kept, checks = [], []
    for i, w in enumerate(waypoints, start=1):
        code = collides(path[i - 1], path[i], query) and collides(path[i], path[i + 1], query)
        vision = i in vision_remove
        low_support = support.get(w, n_answered) < n_answered
        removed = code + vision + low_support >= quorum
        checks.append({"waypoint": tuple(w), "code": code, "vision": vision, "support": low_support,
                       "removed": removed})
        if not removed:
            kept.append(w)
    return Pruning(kept, checks)
