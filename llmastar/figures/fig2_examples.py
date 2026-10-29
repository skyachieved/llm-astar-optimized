"""Paper Fig. 2 (latest arXiv version): more A* vs LLM-A* comparisons, one row per query.

  python -m llmastar.figures.fig2_examples [--model llama-3-8b-instruct] [--run llmastar_standard] [--queries 1:1 1:2 1:4]

Reads the same traces as Fig. 1 (the runner saves map 1 by default; add --trace to save others);
writes outputs/figures/fig2_examples_<model>.{png,pdf}.
"""
import argparse

import matplotlib.pyplot as plt

from llmastar.figures.common import draw_search, load_trace, model_slug, save, search_legend


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--model", default="llama-3-8b-instruct")
    p.add_argument("--run", default="llmastar_standard")
    p.add_argument("--queries", nargs="+", default=["1:1", "1:2", "1:4"], metavar="MAP:SG")
    args = p.parse_args(argv)

    rows = len(args.queries)
    fig, axes = plt.subplots(rows, 2, figsize=(11, 3.6 * rows), squeeze=False)
    for row, spec in enumerate(args.queries):
        map_id, sg_idx = (int(v) for v in spec.split(":"))
        draw_search(axes[row][0], load_trace(args.model, "astar", map_id, sg_idx), f"A*  (map {map_id}, query {sg_idx})")
        draw_search(axes[row][1], load_trace(args.model, args.run, map_id, sg_idx), f"LLM-A*  (map {map_id}, query {sg_idx})")
    search_legend(fig)
    fig.tight_layout(rect=(0, 0.08, 1, 1))
    save(fig, f"fig2_examples_{model_slug(args.model)}")


if __name__ == "__main__":
    main()
