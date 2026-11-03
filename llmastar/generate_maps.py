"""Harder generated maps for the generalization check (agent.md step 6). Never used to choose a default.

  python -m llmastar.generate_maps --kind dense  --size 100 --seed 1 --out dataset/generated/dense.json
  python -m llmastar.generate_maps --kind large  --size 100 --seed 1 --out dataset/generated/large.json
  python -m llmastar.generate_maps --kind zigzag --size 100 --seed 1 --out dataset/generated/zigzag.json

Kinds (parameters fixed a priori, before any result on these maps was seen):
  dense   the benchmark's 51 x 31 grid with 3-5 horizontal and 3-5 vertical barriers (the pool and pilot have 1-3 each)
  large   a 101 x 61 grid (twice the benchmark's side) with 4-8 barriers of each kind, twice as long
  zigzag  51 x 31; 3-5 vertical walls across the whole height, each with one 3-5 cell gap, alternately at the top and
          at the bottom, start left of the first wall and goal right of the last: a serpentine corridor in which the
          straight-line heuristic points the wrong way most of the time
Every map has one start/goal pair whose straight segment is blocked and that A* solves. The output is the benchmark
format (a list of environments with id, range_x, range_y, horizontal_barriers, vertical_barriers, start_goal), so
`python -m llmastar.run --dataset <file>` and `QuorumAStar().searching(query)` take it unchanged.
"""
import argparse
import json
import math
import random
from pathlib import Path

from llmastar.benchmark import segment_collides
from llmastar.pather import AStar

KINDS = ("dense", "large", "zigzag")
MAX_TRIES = 200_000


def _free(cell, query):
    """Inside the search's margin and not on a barrier line (the search's own filter, see quorumastar.geometry)."""
    from llmastar.quorumastar.geometry import passes_filter
    return passes_filter(cell, query)


def _random_cell(rng, query, x_range=None):
    (x0, x1), (y0, y1) = query["range_x"], query["range_y"]
    lo, hi = x_range or (x0 + 2, x1 - 3)
    if lo > hi:
        return None
    for _ in range(1000):
        cell = (rng.randint(lo, hi), rng.randint(y0 + 2, y1 - 3))
        if _free(cell, query):
            return cell
    return None


def _barriers(rng, width, height, n_h, n_v, h_len, v_len):
    horizontal, vertical = [], []
    for _ in range(rng.randint(*n_h)):
        length = rng.randint(*h_len)
        x1 = rng.randint(0, width - 1 - length)
        horizontal.append([rng.randint(4, height - 5), x1, x1 + length])
    for _ in range(rng.randint(*n_v)):
        length = rng.randint(*v_len)
        y1 = rng.randint(0, height - 1 - length)
        vertical.append([rng.randint(4, width - 5), y1, y1 + length])
    return horizontal, vertical


def _candidate(kind, rng):
    if kind == "dense":
        width, height = 51, 31
        horizontal, vertical = _barriers(rng, width, height, (3, 5), (3, 5), (8, 22), (6, 16))
        query = {"range_x": [0, width], "range_y": [0, height], "horizontal_barriers": horizontal,
                 "vertical_barriers": vertical}
        return query, _random_cell(rng, query), _random_cell(rng, query), 25
    if kind == "large":
        width, height = 101, 61
        horizontal, vertical = _barriers(rng, width, height, (4, 8), (4, 8), (16, 44), (12, 32))
        query = {"range_x": [0, width], "range_y": [0, height], "horizontal_barriers": horizontal,
                 "vertical_barriers": vertical}
        return query, _random_cell(rng, query), _random_cell(rng, query), 50
    # zigzag
    width, height = 51, 31
    k = rng.randint(3, 5)
    step = (width - 17) / (k - 1)  # walls between x = 8 and x = width - 9, so start and goal have room
    vertical = []
    for i in range(k):
        x = round(8 + i * step) + rng.randint(-2, 2)
        gap = rng.randint(3, 5)
        if i % 2 == 0:  # gap at the top
            vertical.append([x, 0, height - 1 - gap - 1])
        else:  # gap at the bottom
            vertical.append([x, gap + 1, height - 1])
    xs = [v[0] for v in vertical]
    query = {"range_x": [0, width], "range_y": [0, height], "horizontal_barriers": [], "vertical_barriers": vertical}
    start = _random_cell(rng, query, (2, min(xs) - 2))
    goal = _random_cell(rng, query, (max(xs) + 2, width - 3))
    return query, start, goal, 0


def make_maps(kind, size=100, seed=1):
    if kind not in KINDS:
        raise ValueError(f"kind must be one of {', '.join(KINDS)}")
    rng = random.Random(f"llmastar-generate-maps-{kind}-{seed}")
    maps, seen = [], set()
    for _ in range(MAX_TRIES):
        if len(maps) == size:
            break
        query, start, goal, min_distance = _candidate(kind, rng)
        if start is None or goal is None or math.dist(start, goal) < min_distance:
            continue
        key = json.dumps([query["horizontal_barriers"], query["vertical_barriers"], start, goal])
        q = dict(query, start=list(start), goal=list(goal))
        if key in seen or not segment_collides(list(start), list(goal), q) or not AStar().searching(q)["valid"]:
            continue
        seen.add(key)
        maps.append({"id": len(maps), **query, "start_goal": [[list(start), list(goal)]]})
    if len(maps) < size:
        raise RuntimeError(f"{kind}: only {len(maps)} of {size} maps accepted")
    return maps


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--kind", required=True, choices=KINDS)
    p.add_argument("--size", type=int, default=100)
    p.add_argument("--seed", type=int, default=1)
    p.add_argument("--out", required=True)
    args = p.parse_args(argv)
    maps = make_maps(args.kind, args.size, args.seed)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w") as f:
        json.dump(maps, f)
    print(f"wrote {args.out}: {len(maps)} {args.kind} maps (seed {args.seed})")


if __name__ == "__main__":
    main()
