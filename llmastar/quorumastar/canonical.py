"""Canonicalization (METHOD.md 4.3): proposed points -> cells, so votes from different views compare directly.

1. Round to the nearest cell. If it fails the waypoint filter, take the filter-passing cell within Chebyshev
   distance `cell_radius` that is closest (Euclidean) to the proposed point; ties go to the smallest (x, y). If there
   is none, the point is dropped.
2. If a corner node lies within Euclidean distance `corner_radius`, use the nearest one (ties: lower node id).
3. Consecutive duplicates collapse.
"""
import math

from .geometry import corner_nodes, distance, passes_filter


def _round(v):
    return math.floor(v + 0.5)  # half up, not Python's banker's rounding


def snap_cell(point, query, cell_radius=2):
    """Step 1 for one point; None if no filter-passing cell is near enough."""
    cell = (_round(point[0]), _round(point[1]))
    if passes_filter(cell, query):
        return cell
    candidates = [(cell[0] + dx, cell[1] + dy) for dx in range(-cell_radius, cell_radius + 1)
                  for dy in range(-cell_radius, cell_radius + 1)]
    candidates = [c for c in candidates if passes_filter(c, query)]
    if not candidates:
        return None
    return min(candidates, key=lambda c: (distance(c, point), c))


def snap_corner(cell, corners, corner_radius=3):
    """Step 2 for one cell: the nearest corner node within `corner_radius`, else the cell itself."""
    best = None
    for node_id, corner in enumerate(corners):
        d = distance(corner, cell)
        if d <= corner_radius and (best is None or d < best[0]):
            best = (d, node_id, corner)
    return best[2] if best else cell


def canonicalize(points, query, cell_radius=2, corner_radius=3, corners=None):
    """Returns (cells, dropped): the canonical cells in order, and the proposed points that had no cell nearby."""
    corners = corner_nodes(query) if corners is None else corners
    cells, dropped = [], []
    for point in points:
        cell = snap_cell(point, query, cell_radius)
        if cell is None:
            dropped.append(tuple(point))
            continue
        cell = snap_corner(cell, corners, corner_radius)
        if not cells or cells[-1] != cell:
            cells.append(cell)
    return cells, dropped
