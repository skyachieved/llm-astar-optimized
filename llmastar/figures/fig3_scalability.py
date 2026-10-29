"""Paper Fig. 3: growth factor of operations and storage vs. map scale, A* vs LLM-A*.

  python -m llmastar.figures.fig3_scalability [--model llama-3-8b-instruct]

Reads outputs/<model>/scalability.csv (python -m llmastar.scale). Growth factor at scale k = the method's mean
metric over the sampled queries at k / its mean over the same queries at scale 1. (A mean of per-query ratios is
dominated by queries that LLM-A* solves in a few dozen operations at 1x.)
Writes outputs/figures/fig3_scalability_<model>.{png,pdf}.
"""
import argparse
import csv
from collections import defaultdict
from statistics import mean

import matplotlib.pyplot as plt

from llmastar.figures.common import INK, LABELS, MUTED, SERIES, model_dir, model_slug, save


def growth_factors(rows, metric):
    """{method: {scale: mean metric at scale k / mean metric at scale 1}}, over the queries the method solved at
    every scale, so each point averages the same queries."""
    values = defaultdict(lambda: defaultdict(dict))  # method -> scale -> (map_id, sg_idx) -> value
    for r in rows:
        if r["valid"] == "1" and r[metric]:
            values[r["method"]][int(r["scale"])][(r["map_id"], r["sg_idx"])] = float(r[metric])
    growth = {}
    for method, by_scale in values.items():
        common = set.intersection(*(set(v) for v in by_scale.values()))
        if 1 not in by_scale or not common:
            continue
        base = mean(by_scale[1][q] for q in common)
        growth[method] = {k: mean(v[q] for q in common) / base for k, v in sorted(by_scale.items())}
    return growth


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--model", default="llama-3-8b-instruct")
    args = p.parse_args(argv)
    path = model_dir(args.model) / "scalability.csv"
    if not path.exists():
        raise SystemExit(f"{path} not found; run `python -m llmastar.scale` first.")
    with open(path, newline="") as f:
        rows = list(csv.DictReader(f))

    fig, axes = plt.subplots(2, 1, figsize=(5.5, 7))
    for ax, metric, title in ((axes[0], "operation", "(a) OPERATION"), (axes[1], "storage", "(b) STORAGE")):
        growth = growth_factors(rows, metric)
        scales = sorted({k for by_scale in growth.values() for k in by_scale})
        for method in ("astar", "llmastar"):
            if method not in growth:
                continue
            xs, ys = zip(*growth[method].items())
            ax.plot(xs, ys, color=SERIES[method], linewidth=2, marker="o", markersize=5, label=LABELS[method])
            ax.annotate(f"{ys[-1]:.1f}", (xs[-1], ys[-1]), textcoords="offset points", xytext=(6, 0),
                        va="center", fontsize=9, color=INK)
        ax.set_xticks(scales)
        ax.set_xlabel("Number of Scale", color=INK)
        ax.set_ylabel(f"Growth Factor of {'Operations' if metric == 'operation' else 'Storages'}", color=INK)
        ax.set_title(title, fontsize=11, color=INK, fontweight="bold", y=-0.32)
        ax.grid(True, color="#dddddd", linewidth=0.8, linestyle="--")
        ax.set_axisbelow(True)
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
        ax.spines["left"].set_color(MUTED)
        ax.spines["bottom"].set_color(MUTED)
        ax.tick_params(colors=MUTED)
        ax.legend(loc="upper left", frameon=False)
    fig.tight_layout(h_pad=3)
    save(fig, f"fig3_scalability_{model_slug(args.model)}")


if __name__ == "__main__":
    main()
