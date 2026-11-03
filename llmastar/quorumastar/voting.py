"""Majority add (METHOD.md 3, 4.4): keep the waypoints that at least `quorum` views proposed.

Each view's list is deduplicated (first occurrence wins) and every waypoint gets a relative position
(i + 1) / (n + 1) in its list. Kept waypoints are ordered by their mean position over the views that proposed them;
ties go to first appearance in view order. support(w) = number of views that proposed w.
With one view and quorum <= 1 the list is returned unchanged (order and duplicates kept), which the "all off"
setting needs to reproduce LLM-A* exactly.
"""
from dataclasses import dataclass, field


@dataclass
class Vote:
    waypoints: list  # kept, in order
    support: dict = field(default_factory=dict)  # waypoint -> number of proposing views
    position: dict = field(default_factory=dict)  # waypoint -> mean relative position


def majority_add(lists, quorum=2):
    """`lists`: one list of hashable waypoints per answering view, in view order."""
    if len(lists) == 1 and quorum <= 1:
        only = list(lists[0])
        return Vote(only, {w: 1 for w in only}, {})
    positions, first_seen = {}, {}
    for view, items in enumerate(lists):
        unique = list(dict.fromkeys(items))
        for i, w in enumerate(unique):
            positions.setdefault(w, []).append((i + 1) / (len(unique) + 1))
            first_seen.setdefault(w, (view, i))
    kept = [w for w, ps in positions.items() if len(ps) >= quorum]
    mean = {w: sum(positions[w]) / len(positions[w]) for w in kept}
    kept.sort(key=lambda w: (mean[w], first_seen[w]))
    return Vote(kept, {w: len(positions[w]) for w in kept}, mean)
