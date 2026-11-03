"""Fig. 3 (growth factor vs. map scale) with three lines per panel: A*, our LLM-A*, and the paper's LLM-A*.

  python -m llmastar.figures.fig5_scalability_vs_paper [--model llama-3-8b-instruct] [--paper-astar]

Ours: outputs/<model>/scalability.csv (python -m llmastar.scale), same growth factors as fig3_scalability.
The paper: the authors published no numbers, only the plot (docs/static/images/scalability.png in
github.com/SilinMeng0510/llm-astar, LLM-A* with LLAMA3 few-shot, 10 random queries). The values below were read off that
image by eye and are accurate to about +-1 on its axis; they are not the authors' data. The paper only marks scales
1, 2, 4, 6, 8, 10. --paper-astar adds the paper's A* line as a fourth, faint one.
Writes outputs/figures/fig5_scalability_vs_paper_<model>.{png,pdf}.
"""
import argparse
import csv

import matplotlib.pyplot as plt

from llmastar.figures.common import INK, MUTED, SERIES, model_dir, model_slug, save
from llmastar.figures.fig3_scalability import growth_factors

PAPER = "#2a9d8f"
PAPER_SCALES = (1, 2, 4, 6, 8, 10)
PAPER_READ_OFF = {  # growth factor at PAPER_SCALES, read off the paper's Fig. 3
    "operation": {"astar": (1.0, 4.1, 17.3, 40.5, 72.4, 114.8), "llmastar": (1.0, 3.2, 7.7, 20.9, 26.7, 36.3)},
    "storage": {"astar": (1.0, 3.2, 11.4, 24.4, 42.5, 65.4), "llmastar": (1.0, 2.5, 4.9, 11.3, 11.7, 14.4)},
}


def draw(ax, metric, title, ours, paper_astar):
    lines = [("A* (ours)", ours["astar"], SERIES["astar"], "-", "o"),
             ("LLM-A* (ours)", ours["llmastar"], SERIES["llmastar"], "-", "o"),
             ("LLM-A* (paper, read off plot)", dict(zip(PAPER_SCALES, PAPER_READ_OFF[metric]["llmastar"])), PAPER,
              "--", "D")]
    if paper_astar:
        lines.append(("A* (paper, read off plot)", dict(zip(PAPER_SCALES, PAPER_READ_OFF[metric]["astar"])),
                      SERIES["astar"], ":", "D"))
    for label, series, color, style, marker in lines:
        xs, ys = zip(*sorted(series.items()))
        ax.plot(xs, ys, color=color, linestyle=style, linewidth=2, marker=marker, markersize=5, label=label,
                markeredgecolor="white", markeredgewidth=0.8, alpha=0.55 if style == ":" else 1)
        ax.annotate(f"{ys[-1]:.1f}", (xs[-1], ys[-1]), textcoords="offset points", xytext=(7, 0), va="center",
                    fontsize=9, color=INK)
    ax.set_xticks(range(1, 11))
    ax.set_xlim(0.6, 11)
    ax.set_xlabel("Number of Scale", color=INK)
    ax.set_ylabel(f"Growth Factor of {'Operations' if metric == 'operation' else 'Storage'}", color=INK)
    ax.set_title(title, fontsize=12, color=INK)
    ax.grid(color="#e3e3e3", linewidth=0.8)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.legend(loc="upper left", frameon=False, fontsize=9)


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--model", default="llama-3-8b-instruct")
    p.add_argument("--paper-astar", action="store_true", help="also draw the paper's A* line")
    args = p.parse_args(argv)
    path = model_dir(args.model) / "scalability.csv"
    if not path.exists():
        raise SystemExit(f"{path} not found; run `python -m llmastar.scale` first.")
    with open(path, newline="") as f:
        rows = list(csv.DictReader(f))

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.6))
    for ax, metric, title in ((axes[0], "operation", "(a) OPERATION"), (axes[1], "storage", "(b) STORAGE")):
        draw(ax, metric, title, growth_factors(rows, metric), args.paper_astar)
    fig.text(0.5, -0.02, "Paper values are read off the published plot (about +-1), not the authors' data. "
             "Ours: 10 sampled queries, ratio of means.", ha="center", fontsize=8, color=MUTED)
    fig.tight_layout()
    save(fig, f"fig5_scalability_vs_paper_{model_slug(args.model)}")


if __name__ == "__main__":
    main()
