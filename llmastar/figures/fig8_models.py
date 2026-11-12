"""Operations of weighted A* (w = 2), LLM-A* and Quorum-A* on every model and map set, one panel per map set.

  python -m llmastar.figures.fig8_models [--outputs outputs]

  python -m llmastar.figures.fig8_models --report    # the version in the course report

Reads the per-query CSVs through llmastar.report (the same numbers as outputs/report/tables.md); a model that has not
run a map set is written as "not run yet" in its row, never estimated. Lower is better; A* = 100.
Writes outputs/figures/fig8_models.{png,pdf}. With --report: only the models run on every map set (a model left out on
purpose, see report.SKIPPED, stays in the report's tables), no title line (the caption carries it), weighted A* (w = 2)
named as the report names it, and outputs/figures/fig8_models_report.{png,pdf}.
"""
import argparse
from pathlib import Path

import matplotlib.pyplot as plt

from llmastar.figures.common import INK, MUTED, save
from llmastar.figures.fig7_tradeoff import AQUA, GRID, ORANGE, SURFACE, YELLOW
from llmastar.report import KINDS, MODELS, SKIPPED, metrics

SERIES = [  # run, label, color, marker
    ("wastar-w2", "Weighted A* (w = 2)", YELLOW, "o"),
    ("llmastar_standard", "LLM-A*", ORANGE, "o"),
    ("quorumastar", "Quorum-A*", AQUA, "*"),
]


def panels(outputs):
    """[(title, [(model label, {run: operation or None})])] for the benchmark and each generated-map kind."""
    sets = [("Benchmark (1,000 queries)", lambda bench, hard: bench)]
    sets += [(f"{kind.capitalize()} maps (100)", lambda bench, hard, kind=kind: hard.format(kind=kind))
             for kind in KINDS]
    out = []
    for title, folder_of in sets:
        rows = []
        for label, model, bench, hard, _ in MODELS:
            folder = Path(outputs) / folder_of(bench, hard) / model
            ops = {}
            for run, *_ in SERIES:
                m = metrics(folder, run)
                ops[run] = m["operation"] if m else None
            rows.append((label, ops, SKIPPED.get(model) if title != "Benchmark (1,000 queries)" else None))
        out.append((title, rows))
    return out


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--outputs", default="outputs")
    p.add_argument("--report", action="store_true",
                   help="course-report version: models run on every map set only, no title line, own file name")
    args = p.parse_args(argv)
    data = panels(args.outputs)
    labels = [label for label, *_ in MODELS]
    names = {run: name for run, name, *_ in SERIES}
    if args.report:
        partial = {label for label, model, *_ in MODELS if model in SKIPPED}
        data = [(title, [row for row in rows if row[0] not in partial]) for title, rows in data]
        labels = [label for label in labels if label not in partial]
        names["wastar-w2"] = "No waypoints (weighted A*, w = 2)"
    # The report shrinks the figure to the page width, so its text is drawn larger (same shape, so it takes the same
    # space on the page).
    fs = 1.45 if args.report else 1.0
    fig, axes = plt.subplots(1, len(data), figsize=(13, 3.6) if args.report else (13, 3.4), facecolor=SURFACE,
                             sharey=True)
    for ax, (title, rows) in zip(axes, data):
        ax.set_facecolor(SURFACE)
        values = [v for _, ops, _ in rows for v in ops.values() if v is not None]
        lo, hi = (min(values), max(values)) if values else (0, 100)
        pad = max(1.0, 0.12 * (hi - lo))
        for y, (label, ops, skipped) in enumerate(rows):
            present = [v for v in ops.values() if v is not None]
            if not present:
                ax.text((lo + hi) / 2, y, skipped or "not run yet", ha="center", va="center", fontsize=8 * fs, color=MUTED)
                continue
            ax.plot([min(present), max(present)], [y, y], color=GRID, linewidth=2, zorder=1)
            for run, name, color, marker in SERIES:
                if ops[run] is None:
                    continue
                ring = run == "wastar-w2"  # an open ring drawn on top, so it stays visible under Quorum-A*'s star
                ax.plot(ops[run], y, linestyle="none", marker=marker, markersize=(14 if marker == "*" else 9) * min(fs, 1.2),
                        color=color, markerfacecolor="none" if ring else color,
                        markeredgecolor=color if ring else SURFACE, markeredgewidth=2.0 if ring else 1.0,
                        zorder=4 if ring else (3 if marker == "*" else 2), label=names[run] if y == 0 else None)
            if ops["quorumastar"] is not None:
                ax.annotate(f"{ops['quorumastar']:.1f}", (ops["quorumastar"], y), xytext=(0, 9 * fs),
                            textcoords="offset points", ha="center", fontsize=7.5 * fs, color=INK)
        ax.set_xlim(lo - pad, hi + pad)
        ax.set_ylim(len(rows) - 0.5, -0.6)
        ax.set_title(title, fontsize=10 * fs, color=INK)
        ax.set_xlabel("Operations (A* = 100)", fontsize=9 * fs, color=INK)
        ax.grid(axis="x", color=GRID, linewidth=1, zorder=0)
        ax.tick_params(labelsize=8 * fs, colors=MUTED)
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
        for side in ("left", "bottom"):
            ax.spines[side].set_color(GRID)
    axes[0].set_yticks(range(len(labels)))
    axes[0].set_yticklabels(labels, fontsize=9 * fs, color=INK)
    handles, legend_names = axes[0].get_legend_handles_labels()
    fig.legend(handles, legend_names, loc="lower center", ncol=3, frameon=False, fontsize=9 * fs,
               bbox_to_anchor=(0.5, -0.03))
    if args.report:
        fig.tight_layout(rect=(0, 0.1, 1, 1))
        save(fig, "fig8_models_report")
    else:
        fig.text(0.5, 0.99, "Geometric mean of operations vs A* per model (lower is better); label = Quorum-A*; "
                 "each panel has its own x scale", ha="center", fontsize=9, color=MUTED)
        fig.tight_layout(rect=(0, 0.08, 1, 0.95))
        save(fig, "fig8_models")
    plt.close(fig)


if __name__ == "__main__":
    main()
