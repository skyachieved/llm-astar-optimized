"""A*, LLM-A* and Quorum-A* side by side: the search on one query (top) and the averages over the benchmark
(bottom, with weighted A* w = 2 as the no-LLM reference that agent.md requires next to every LLM result).

  python -m llmastar.figures.fig6_methods [--model qwen2.5-vl-7b-instruct] [--query 1:0]
      [--llm-run llmastar_standard] [--quorum-run quorumastar] [--wastar-run wastar-w2] [--out outputs]

Reads <out>/<model>/{astar,<runs>}.csv and traces/<run>/<map>_<sg>.json only; a run that does not exist yet is
drawn as an empty panel saying so (nothing is estimated). The averages use only the queries that every plotted run
has and where all of them found a path, so the methods are compared on the same queries; n is in the subtitle.
Writes outputs/figures/fig6_methods_<model>.{png,pdf}.
"""
import argparse
import csv
import math
from pathlib import Path

import matplotlib.pyplot as plt

from llmastar.figures.common import INK, MUTED, draw_search, model_slug, save, search_legend
from llmastar.outputs import OUTPUTS_ROOT

# Fixed method order and colors (validated categorical slots 1-4: blue, yellow, orange, aqua); color follows the method.
METHODS = [("astar", "A*", "#2a78d6"), ("wastar", "Weighted A* (w=2)", "#eda100"),
           ("llmastar", "LLM-A*", "#eb6834"), ("quorumastar", "Quorum-A*", "#1baf7a")]
METRICS = [("operation", "Operations"), ("storage", "Storage"), ("length", "Path length")]
SURFACE = "#fcfcfb"
GRID = "#e8e8e6"


def _rows(path):
    if not Path(path).exists():
        return None
    with open(path, newline="") as f:
        return {(r["map_id"], r["sg_idx"]): r for r in csv.DictReader(f)}


def _trace(directory, run, map_id, sg_idx):
    import json
    path = directory / "traces" / run / f"{map_id}_{sg_idx}.json"
    if not path.exists():
        return None
    with open(path) as f:
        return json.load(f)


def _geomean(values):
    return math.exp(sum(math.log(v) for v in values) / len(values))


def averages(runs):
    """{method: {metric: 100 * geomean(run / A*)}} over the queries every run has and solved; and that n."""
    astar = runs["astar"]
    present = {m: r for m, r in runs.items() if r is not None}
    common = set(astar)
    for rows in present.values():
        common &= {k for k, r in rows.items() if r["valid"] == "1"}
    out = {}
    for method, rows in present.items():
        out[method] = {metric: 100 * _geomean([float(rows[k][metric]) / float(astar[k][metric]) for k in common])
                       for metric, _ in METRICS} if common else None
    return out, len(common)


def _placeholder(ax, title, note, like):
    """An empty panel the size of a search panel (`like` is a trace for the map extent)."""
    q = like["query"]
    ax.set_xlim(q["range_x"][0] - 0.5, q["range_x"][1] - 0.5)
    ax.set_ylim(q["range_y"][0] - 0.5, q["range_y"][1] - 0.5)
    ax.set_aspect("equal")
    ax.set_title(title, fontsize=12, color=INK)
    ax.text(0.5, 0.5, note, transform=ax.transAxes, ha="center", va="center", fontsize=9, color=MUTED)
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_color(GRID)


def _compact_metrics(ax, trace):
    """draw_search's metric box is written for a full-width panel; in a third of the width it overlaps the
    neighbour, so it is shortened here (same numbers)."""
    length = f"{trace['length']:.2f}" if trace["length"] is not None else "-"
    for text in ax.texts:
        if text.get_text().startswith('{"#operation"'):
            text.set_text(f"ops {trace['operation']}  storage {trace['storage']}  length {length}")
            text.set_fontsize(7.5)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--model", default="llama-3-8b-instruct")
    p.add_argument("--query", default="1:0", metavar="MAP:SG")
    p.add_argument("--llm-run", default="llmastar_standard")
    p.add_argument("--quorum-run", default="quorumastar")
    p.add_argument("--wastar-run", default="wastar-w2")
    p.add_argument("--out", default=str(OUTPUTS_ROOT), help="outputs root holding <model>/ (e.g. outputs/gpt)")
    args = p.parse_args(argv)
    map_id, sg_idx = args.query.split(":")
    names = {"astar": "astar", "wastar": args.wastar_run, "llmastar": args.llm_run, "quorumastar": args.quorum_run}
    directory = Path(args.out) / model_slug(args.model)
    runs = {m: _rows(directory / f"{run}.csv") for m, run in names.items()}
    if runs["astar"] is None:
        raise SystemExit(f"{directory / 'astar.csv'} not found; run `python -m llmastar.run --method astar "
                         f"--model {args.model}` first.")

    fig = plt.figure(figsize=(12, 7.4), facecolor=SURFACE)
    # Rows: the searches, the search legend, the averages.
    grid = fig.add_gridspec(3, 3, height_ratios=[1, 0.14, 1.05], hspace=0.28, wspace=0.18, bottom=0.1, top=0.96)

    # Top: the three searches on one query.
    traces = {m: _trace(directory, names[m], map_id, sg_idx) for m in ("astar", "llmastar", "quorumastar")}
    like = next((t for t in traces.values() if t), None)
    if like is None:
        raise SystemExit(f"no trace for query {args.query} in {directory / 'traces'}")
    for col, method in enumerate(("astar", "llmastar", "quorumastar")):
        ax = fig.add_subplot(grid[0, col])
        label = dict((m, lab) for m, lab, _ in METHODS)[method]
        if traces[method] is None:
            _placeholder(ax, label, f"{names[method]}: no trace for {args.query}\n(not run yet, or run without\n"
                                    f"--trace {args.query})", like)
        else:
            draw_search(ax, traces[method], label)
            _compact_metrics(ax, traces[method])

    # Bottom: averages relative to A* (= 100), one small multiple per metric, same queries for every method.
    means, n = averages(runs)
    shown = [(m, lab, color) for m, lab, color in METHODS if means.get(m)]
    missing = [lab for m, lab, _ in METHODS if not means.get(m)]
    for col, (metric, title) in enumerate(METRICS):
        ax = fig.add_subplot(grid[2, col])
        ax.set_facecolor(SURFACE)
        values = [means[m][metric] for m, _, _ in shown]
        bars = ax.bar(range(len(shown)), values, width=0.62, color=[c for _, _, c in shown],
                      edgecolor=SURFACE, linewidth=2, zorder=3)
        for bar, value in zip(bars, values):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1.5, f"{value:.1f}", ha="center",
                    va="bottom", fontsize=9, color=INK)
        ax.set_xticks(range(len(shown)), [lab.replace(" (", "\n(") for _, lab, _ in shown], fontsize=8, color=INK)
        ax.set_title(f"{title} (A* = 100)", fontsize=11, color=INK)
        ax.set_ylim(0, max(values + [100]) * 1.15)
        ax.grid(axis="y", color=GRID, linewidth=1, zorder=0)
        ax.tick_params(axis="y", labelsize=8, colors=MUTED)
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
        for side in ("left", "bottom"):
            ax.spines[side].set_color(GRID)
    subtitle = (f"{model_slug(args.model)}; bottom: geometric mean over the n = {n} queries every plotted run has and "
                f"solved (lower is better)")
    if missing:
        subtitle += f"; not run yet: {', '.join(missing)}"
    fig.text(0.5, 0.005, subtitle, ha="center", va="bottom", fontsize=9, color=MUTED)
    search_legend(fig)
    legend = fig.legends[-1]  # one row in its own strip between the panels, instead of three rows under the bars
    handles, labels = legend.legend_handles, [t.get_text() for t in legend.get_texts()]
    legend.remove()
    strip = fig.add_subplot(grid[1, :])
    strip.axis("off")
    strip.legend(handles=handles, labels=labels, loc="center", ncol=len(handles), frameon=False, fontsize=8.5)
    save(fig, f"fig6_methods_{model_slug(args.model)}")
    plt.close(fig)


if __name__ == "__main__":
    main()
