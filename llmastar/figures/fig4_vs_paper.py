"""Ours vs. the paper vs. A*: Table 1 (LLAMA3 rows) and the Fig. 1 query.

  python -m llmastar.figures.fig4_vs_paper [--model llama-3-8b-instruct]

Reads outputs/<model>/summary.csv (python -m llmastar.summary) and the map 1 / query 0 traces of astar and
llmastar_standard. Writes outputs/figures/fig4_table1_vs_paper_<model>.{png,pdf} and fig4_fig1_vs_paper_<model>.{png,pdf}.

The paper reports per-query numbers only for its Fig. 1 query (140 / 235 / 53.46, from the figure itself), so
every other comparison is on the Table 1 averages, which are ratios to A* (A* = 100).
"""
import argparse
import csv

import matplotlib.pyplot as plt

from llmastar.figures.common import INK, MUTED, SERIES, load_trace, model_dir, model_slug, save

OURS, PAPER = SERIES["llmastar"], "#6b8fb3"
RUNS = [("dwastar", "Dynamic WA*"), ("llmastar_standard", "LLM-A*\nfew-shot"), ("llmastar_cot", "LLM-A*\nCoT"),
        ("llmastar_repe", "LLM-A*\nRePE")]
METRICS = [("operation", "Operations (A* = 100)"), ("storage", "Storage (A* = 100)"),
           ("length", "Path length (A* = 100)")]
PAPER_FIG1 = {"operation": 140, "storage": 235, "length": 53.46}  # LLM-A* in the paper's Fig. 1


def table1(model):
    path = model_dir(model) / "summary.csv"
    if not path.exists():
        raise SystemExit(f"{path} not found; run `python -m llmastar.summary` first.")
    with open(path, newline="") as f:
        return {r["run"]: r for r in csv.DictReader(f)}


def plot_table1(model):
    rows = table1(model)
    fig, axes = plt.subplots(1, 3, figsize=(12, 3.8))
    for ax, (metric, title) in zip(axes, METRICS):
        for i, (run, _) in enumerate(RUNS):
            ours, paper = float(rows[run][metric]), float(rows[run][f"paper_{metric}"])
            ax.plot([i, i], [ours, paper], color=MUTED, linewidth=1, zorder=1)
            ax.scatter([i], [ours], s=64, color=OURS, edgecolors="white", linewidths=1.5, zorder=3,
                       label="Ours" if i == 0 else None)
            ax.scatter([i], [paper], s=64, color=PAPER, edgecolors="white", linewidths=1.5, zorder=3,
                       label="Paper" if i == 0 else None)
            ours_above = ours >= paper
            for value, color, above in ((ours, OURS, ours_above), (paper, PAPER, not ours_above)):
                ax.annotate(f"{value:.1f}", (i, value), textcoords="offset points", xytext=(0, 8 if above else -14),
                            ha="center", fontsize=8, color=INK)
        ax.axhline(100, color=SERIES["astar"], linestyle="--", linewidth=1.5, zorder=0, label="A* (= 100)")
        ax.set_xticks(range(len(RUNS)), [label for _, label in RUNS], fontsize=8)
        ax.set_xlim(-0.5, len(RUNS) - 0.5)
        ax.set_title(title, fontsize=11, color=INK)
        ax.grid(axis="y", color="#e3e3e3", linewidth=0.8)
        ax.set_axisbelow(True)
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
    axes[0].set_ylim(0, 110)
    axes[1].set_ylim(0, 110)
    axes[2].set_ylim(98, 105)  # zoomed: every method is within a few percent of optimal
    axes[0].legend(loc="lower right", frameon=False, fontsize=9)
    fig.suptitle("Table 1 (LLAMA3 rows): ours vs. the paper, relative to A*", fontsize=12, color=INK)
    fig.tight_layout()
    save(fig, f"fig4_table1_vs_paper_{model_slug(model)}")


def plot_fig1_query(model):
    astar, ours = load_trace(model, "astar", 1, 0), load_trace(model, "llmastar_standard", 1, 0)
    fig, axes = plt.subplots(1, 3, figsize=(10, 3.4))
    for ax, (metric, title) in zip(axes, (("operation", "Operations"), ("storage", "Storage"),
                                          ("length", "Path length"))):
        values = [("A*", astar[metric], SERIES["astar"]), ("LLM-A*\nours", ours[metric], OURS),
                  ("LLM-A*\npaper", PAPER_FIG1[metric], PAPER)]
        ax.bar(range(3), [v for _, v, _ in values], color=[c for _, _, c in values], width=0.6)
        for i, (_, v, _) in enumerate(values):
            ax.annotate(f"{v:.2f}" if metric == "length" else f"{v:.0f}", (i, v), textcoords="offset points",
                        xytext=(0, 3), ha="center", fontsize=9, color=INK)
        ax.set_xticks(range(3), [label for label, _, _ in values], fontsize=9)
        ax.set_title(title, fontsize=11, color=INK)
        ax.set_ylim(0, max(v for _, v, _ in values) * 1.15)
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
    fig.suptitle("Fig. 1 query (map 1, query 0): A* vs. LLM-A*, ours and the paper's", fontsize=12, color=INK)
    fig.tight_layout()
    save(fig, f"fig4_fig1_vs_paper_{model_slug(model)}")


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--model", default="llama-3-8b-instruct")
    args = p.parse_args(argv)
    plot_table1(args.model)
    plot_fig1_query(args.model)


if __name__ == "__main__":
    main()
