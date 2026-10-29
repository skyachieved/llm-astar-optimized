"""Shared helpers for the figures. Figures read only from outputs/ and write PNG + PDF to outputs/figures/."""
import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402,F401
from matplotlib.collections import PatchCollection  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import Rectangle  # noqa: E402

from llmastar.env.search.env import Env  # noqa: E402
from llmastar.outputs import OUTPUTS_ROOT, model_slug  # noqa: E402

FIGURES = OUTPUTS_ROOT / "figures"

INK = "#1f1f1f"
MUTED = "#6b6b6b"
VISITED = "#9a9a9a"
PATH = "#d62728"
START = "#1f4fd6"
GOAL = "#1a8a2e"
STAR = "#f2b705"
# Two-series categorical pair (A*, LLM-A*), as in the paper's Fig. 3.
SERIES = {"astar": "#1f77b4", "llmastar": "#ff7f0e"}
LABELS = {"astar": "A*", "llmastar": "LLM-A* (Ours)"}


def model_dir(model):
    return OUTPUTS_ROOT / model_slug(model)


def load_trace(model, run, map_id, sg_idx):
    path = model_dir(model) / "traces" / run / f"{map_id}_{sg_idx}.json"
    if not path.exists():
        raise SystemExit(f"{path} not found; run `python -m llmastar.run --method ... --trace {map_id}:{sg_idx}` first.")
    with open(path) as f:
        return json.load(f)


def save(fig, name):
    FIGURES.mkdir(parents=True, exist_ok=True)
    for ext in ("png", "pdf"):
        fig.savefig(FIGURES / f"{name}.{ext}", dpi=200, bbox_inches="tight")
    print(f"wrote {FIGURES / name}.png/.pdf")


def draw_search(ax, trace, title):
    """One search: obstacle cells, visited states, path, start/goal, the metric box, and the LLM's waypoints:
    filled stars for those the search used as targets, hollow stars for those LLM-A* dropped (on a barrier or
    next to the map edge)."""
    q = trace["query"]
    obs = Env(q["range_x"][1], q["range_y"][1], q["horizontal_barriers"], q["vertical_barriers"]).obs
    ax.add_collection(PatchCollection([Rectangle((x - 0.5, y - 0.5), 1, 1) for x, y in obs],
                                      facecolor=INK, edgecolor="none"))
    start, goal = tuple(q["start"]), tuple(q["goal"])
    visited = [tuple(p) for p in trace["visited"] if tuple(p) not in (start, goal)]
    if visited:
        ax.scatter(*zip(*visited), s=9, color=VISITED, linewidths=0, zorder=2)
    if trace["path"]:
        ax.plot(*zip(*trace["path"]), color=PATH, linewidth=2, zorder=3, solid_capstyle="round")
    used = {tuple(p) for p in trace.get("targets", [])}
    targets = [p for p in used if p not in (start, goal)]
    if targets:
        ax.scatter(*zip(*targets), marker="*", s=160, color=STAR, edgecolors=INK, linewidths=0.6, zorder=5)
    dropped = [tuple(p) for p in trace.get("waypoints", []) if tuple(p) not in used | {start, goal}]
    if dropped:
        ax.scatter(*zip(*dropped), marker="*", s=160, facecolors="white", edgecolors=INK, linewidths=0.9, zorder=5)
    ax.scatter([start[0]], [start[1]], marker="s", s=60, color=START, zorder=4)
    ax.scatter([goal[0]], [goal[1]], marker="s", s=60, color=GOAL, zorder=4)
    length = f"{trace['length']:.2f}" if trace["length"] is not None else "-"
    ax.text(0.02, 0.97, f'{{"#operation": {trace["operation"]}, "#storage": {trace["storage"]}, "path length": {length}}}',
            transform=ax.transAxes, va="top", ha="left", fontsize=8, color=INK,
            bbox=dict(boxstyle="round,pad=0.3", facecolor="white", edgecolor=MUTED, linewidth=0.8), zorder=6)
    ax.set_title(title, fontsize=12, color=INK)
    ax.set_xlim(q["range_x"][0] - 0.5, q["range_x"][1] - 0.5)
    ax.set_ylim(q["range_y"][0] - 0.5, q["range_y"][1] - 0.5)
    ax.set_aspect("equal")
    ax.axis("off")


def search_legend(fig, with_targets=True):
    handles = [
        Line2D([], [], marker="s", linestyle="none", color=START, markersize=8, label="Start State"),
        Line2D([], [], marker="s", linestyle="none", color=GOAL, markersize=8, label="Goal State"),
        Line2D([], [], marker="s", linestyle="none", color=INK, markersize=8, label="Barriers"),
        Line2D([], [], marker="o", linestyle="none", color=VISITED, markersize=8, label="Visited State"),
        Line2D([], [], color=PATH, linewidth=2, label="Path"),
    ]
    if with_targets:
        handles += [
            Line2D([], [], marker="*", linestyle="none", color=STAR, markeredgecolor=INK, markersize=12,
                   label="LLM waypoint (target)"),
            Line2D([], [], marker="*", linestyle="none", markerfacecolor="white", markeredgecolor=INK,
                   markersize=12, label="LLM waypoint (dropped)"),
        ]
    fig.legend(handles=handles, loc="lower center", ncol=3, frameon=True, fontsize=9, bbox_to_anchor=(0.5, -0.02))
