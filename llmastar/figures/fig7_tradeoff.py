"""Operations (and storage) against path length for every method, with the weighted-A* frontier (w = 1.5, 2, 3).

  python -m llmastar.figures.fig7_tradeoff [--model gpt-4o-mini] [--out outputs/gpt]

Reads <out>/<model>/summary.csv only (python -m llmastar.summary writes it); a run that is missing is left out.
Lower-left is better: fewer states for a path closer to optimal. Writes outputs/figures/fig7_tradeoff_<model>.{png,pdf}.
"""
import argparse
import csv
from pathlib import Path

import matplotlib.pyplot as plt

from llmastar.figures.common import INK, MUTED, save
from llmastar.outputs import OUTPUTS_ROOT, model_slug

# Same method colors as fig6 (validated categorical slots): A* blue, weighted A* yellow, LLM-A* orange, Quorum-A* aqua.
BLUE, YELLOW, ORANGE, AQUA = "#2a78d6", "#eda100", "#eb6834", "#1baf7a"
SURFACE, GRID = "#fcfcfb", "#e8e8e6"
POINTS = [  # run, label, color, marker, filled
    ("astar", "A*", BLUE, "o", True),
    ("dwastar", "Dynamic WA*", MUTED, "D", True),
    ("llmastar_standard", "LLM-A* (few-shot)", ORANGE, "o", True),
    ("llmastar_cot", "LLM-A* (CoT)", ORANGE, "^", True),
    ("llmastar_repe", "LLM-A* (RePE)", ORANGE, "s", True),
    ("quorumastar-vision", "Quorum-A* + vision judge", AQUA, "*", False),
    ("quorumastar", "Quorum-A*", AQUA, "*", True),
]
FRONTIER = [("wastar-w1.5", "1.5"), ("wastar-w2", "2"), ("wastar-w3", "3")]


def read_summary(path):
    with open(path, newline="") as f:
        return {r["run"]: r for r in csv.DictReader(f)}


def _style(ax):
    ax.grid(color=GRID, linewidth=1, zorder=0)
    ax.tick_params(labelsize=8, colors=MUTED)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(GRID)


def _draw(ax, s, metric, labels):
    front = [(float(s[r]["length"]), float(s[r][metric]), w) for r, w in FRONTIER if r in s]
    if front:
        ax.plot([x for x, _, _ in front], [y for _, y, _ in front], color=YELLOW, linewidth=2, marker="o",
                markersize=9, markeredgecolor=SURFACE, markeredgewidth=1.5, zorder=3, label="Weighted A* (w)")
        if labels:
            for x, y, w in front:
                ax.annotate(f"w = {w}", (x, y), xytext=(6, 6), textcoords="offset points", fontsize=8, color=INK)
    for run, label, color, marker, filled in POINTS:
        if run not in s:
            continue
        ax.plot(float(s[run]["length"]), float(s[run][metric]), linestyle="none", marker=marker,
                markersize=15 if marker == "*" else 9, color=color,
                markerfacecolor=color if filled else "none", markeredgecolor=SURFACE if filled else color,
                markeredgewidth=1.0 if filled else 1.8, zorder=6 if not filled else 5, label=label)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--model", default="gpt-4o-mini")
    p.add_argument("--out", default=str(OUTPUTS_ROOT), help="outputs root holding <model>/summary.csv")
    p.add_argument("--suffix", default="", help="run-name suffix to read past, e.g. -max512 (llmastar_standard-max512)")
    args = p.parse_args(argv)
    path = Path(args.out) / model_slug(args.model) / "summary.csv"
    if not path.exists():
        raise SystemExit(f"{path} not found; run `python -m llmastar.summary --model {args.model} --out {args.out}`")
    s = read_summary(path)
    if args.suffix:
        s = {(r[:-len(args.suffix)] if r.endswith(args.suffix) else r): row for r, row in s.items()}

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.6), facecolor=SURFACE)
    for ax, metric, title in ((axes[0], "operation", "Operations"), (axes[1], "storage", "Storage")):
        ax.set_facecolor(SURFACE)
        _draw(ax, s, metric, labels=True)
        ax.set_xlabel("Path length (A* = 100)", fontsize=10, color=INK)
        ax.set_ylabel(f"{title} (A* = 100)", fontsize=10, color=INK)
        ax.set_title(f"{title} vs. path length", fontsize=11, color=INK)
        _style(ax)
        # Zoom on weighted A* at w = 2, where Quorum-A* lands (the points overlap at full scale).
        if "wastar-w2" in s:
            x0, y0 = float(s["wastar-w2"]["length"]), float(s["wastar-w2"][metric])
            near = [float(s[r][metric]) for r in ("quorumastar", "quorumastar-vision") if r in s] + [y0]
            span = max(0.6, 1.6 * (max(near) - min(near)))
            inset = ax.inset_axes([0.58, 0.55, 0.38, 0.38])
            inset.set_facecolor(SURFACE)
            _draw(inset, s, metric, labels=False)
            inset.set_xlim(x0 - 0.12, x0 + 0.12)
            inset.set_ylim(y0 - span, y0 + span)
            inset.set_title("zoom at w = 2", fontsize=8, color=MUTED)
            inset.set_xticks([round(x0 - 0.1, 1), round(x0, 1), round(x0 + 0.1, 1)])
            inset.locator_params(axis="y", nbins=4)
            _style(inset)
            ax.indicate_inset_zoom(inset, edgecolor=MUTED, alpha=0.6)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=4, frameon=False, fontsize=8.5, bbox_to_anchor=(0.5, -0.02))
    n = s.get("astar", {}).get("n", "?")
    fig.text(0.5, 1.0, f"{model_slug(args.model)}, {n} queries; geometric mean vs A* (lower-left is better)",
             ha="center", fontsize=9, color=MUTED)
    fig.tight_layout(rect=(0, 0.1, 1, 0.97))
    save(fig, f"fig7_tradeoff_{model_slug(args.model)}")
    plt.close(fig)


if __name__ == "__main__":
    main()
