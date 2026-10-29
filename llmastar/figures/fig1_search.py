"""Paper Fig. 1: A* vs LLM-A* search on one query (default: map 1, start/goal 0, few-shot prompt).

  python -m llmastar.figures.fig1_search [--model llama-3-8b-instruct] [--run llmastar_standard] [--query 1:0]

Reads outputs/<model>/traces/{astar,<run>}/<map>_<sg>.json; writes outputs/figures/fig1_search_<model>.{png,pdf}.
"""
import argparse

import matplotlib.pyplot as plt

from llmastar.figures.common import draw_search, load_trace, model_slug, save, search_legend


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--model", default="llama-3-8b-instruct")
    p.add_argument("--run", default="llmastar_standard")
    p.add_argument("--query", default="1:0", metavar="MAP:SG")
    args = p.parse_args(argv)
    map_id, sg_idx = (int(v) for v in args.query.split(":"))

    astar = load_trace(args.model, "astar", map_id, sg_idx)
    llm = load_trace(args.model, args.run, map_id, sg_idx)
    fig, axes = plt.subplots(2, 1, figsize=(6, 7.6))
    draw_search(axes[0], astar, "A*")
    draw_search(axes[1], llm, "LLM-A*")
    search_legend(fig)
    fig.tight_layout(rect=(0, 0.12, 1, 1))
    save(fig, f"fig1_search_{model_slug(args.model)}")


if __name__ == "__main__":
    main()
