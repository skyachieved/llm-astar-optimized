"""The pilot (METHOD.md 11, agent.md step 4), on self-generated maps only; the evaluation maps never choose a default.

  python -m llmastar.quorumastar.pilot make   [--size 50] [--seed 1] [--out pilot/pilot_maps.json]
  python -m llmastar.quorumastar.pilot report --dir outputs_pilot/<model> [--run quorumastar] [--dataset ...]

`make` writes a dataset in the benchmark format: `size` maps from the few-shot generator (same parameters, fixed a
priori) under a seed namespace disjoint from the few-shot pool's, one start/goal each, every map solvable and with a
blocked straight start-goal segment. Unlike the pool, no condition on the A* path is imposed (that would favour easy
maps). Maps identical to a few-shot example are skipped.

`report` reads <dir>/raw/<run>.jsonl (a quorumastar run over that dataset; run it with every candidate view, e.g.
--views text,corners,image,relations) and the run CSVs in <dir>, and prints (and writes to <dir>/pilot_<run>.md):
  - solo quality per view: abstentions, waypoints, share good, share of queries with a good waypoint;
  - independence: for views a, b the share of a's bad waypoints that b also proposed;
  - voting, as run and simulated offline from the same answers for every 3-view set and matching radius r
    (r = 0 is the exact-cell vote that ran; r > 0 counts cells within Chebyshev distance r as the same proposal);
  - the vision judge's catch and false-alarm rates;
  - search metrics (geometric mean vs A* = 100) of the runs present, on the queries all of them solved.
  - every LLM run vs weighted A* (w = 2), split by whether the search kept waypoints (n_targets > 2).
A waypoint w is bad if it fails the search's filter, is unreachable, or len A*(s, w) + len A*(w, g) > 1.05 len A*(s, g)
(METHOD.md 11), computed on canonical cells.
"""
import argparse
import csv
import itertools
import json
import math
import random
from functools import lru_cache
from pathlib import Path

from llmastar.benchmark import load_queries
from llmastar.pather import AStar

from .fewshot import MIN_START_GOAL, _random_free_cell, _random_map, pool
from .geometry import collides, passes_filter

BAD_RATIO = 1.05
RADII = (0, 1, 2, 3)
METRICS = ("operation", "storage", "length")


# ---- maps ---------------------------------------------------------------------------------------------------------

def _barriers(m):
    return (sorted(map(tuple, m["horizontal_barriers"])), sorted(map(tuple, m["vertical_barriers"])))


def make_maps(size=50, seed=1, max_tries=100_000):
    rng = random.Random(f"quorumastar-pilot-{seed}")
    taken = {(tuple(map(tuple, _barriers(e)[0])), tuple(map(tuple, _barriers(e)[1]))) for e in pool(0, 12)}
    maps = []
    for _ in range(max_tries):
        if len(maps) == size:
            break
        m = _random_map(rng)
        start, goal = _random_free_cell(rng, m), _random_free_cell(rng, m)
        if math.dist(start, goal) < MIN_START_GOAL:
            continue
        q = dict(m, start=list(start), goal=list(goal))
        key = (tuple(map(tuple, _barriers(m)[0])), tuple(map(tuple, _barriers(m)[1])))
        if key in taken or not collides(start, goal, q) or not AStar().searching(q)["valid"]:
            continue
        taken.add(key)
        maps.append({"id": len(maps), **m, "start_goal": [[list(start), list(goal)]]})
    if len(maps) < size:
        raise RuntimeError(f"pilot: only {len(maps)} of {size} maps accepted")
    return maps


# ---- ground truth -------------------------------------------------------------------------------------------------

def _qkey(query):
    return json.dumps({k: query[k] for k in ("range_x", "range_y", "horizontal_barriers", "vertical_barriers")},
                      sort_keys=True)


@lru_cache(maxsize=65536)
def _length(qkey, a, b):
    if a == b:
        return 0.0
    r = AStar().searching(dict(json.loads(qkey), start=list(a), goal=list(b)))
    return r["length"] if r["valid"] else math.inf


def is_bad(cell, query, ratio=BAD_RATIO):
    cell = tuple(cell)
    if not passes_filter(cell, query):
        return True
    k, s, g = _qkey(query), tuple(query["start"]), tuple(query["goal"])
    through = _length(k, s, cell) + _length(k, cell, g)
    return through > ratio * _length(k, s, g)


# ---- offline vote simulation --------------------------------------------------------------------------------------

def simulate_vote(lists, radius=0, quorum=2):
    """Waypoints kept when cells within Chebyshev `radius` of each other count as one proposal (single linkage).
    `lists`: one list of cells per answering view. A group is kept if >= quorum distinct views proposed a cell in it;
    it is represented by its cell with the most views, ties to the earliest (view order, then list order).
    radius 0 keeps exactly the cells voting.majority_add keeps (order aside)."""
    cells = [(v, i, tuple(c)) for v, items in enumerate(lists) for i, c in enumerate(dict.fromkeys(map(tuple, items)))]
    parent = list(range(len(cells)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for i, j in itertools.combinations(range(len(cells)), 2):
        a, b = cells[i][2], cells[j][2]
        if max(abs(a[0] - b[0]), abs(a[1] - b[1])) <= radius:
            parent[find(i)] = find(j)
    groups = {}
    for i, cell in enumerate(cells):
        groups.setdefault(find(i), []).append(cell)
    kept = []
    for members in groups.values():
        if len({v for v, _, _ in members}) < quorum:
            continue
        views_of = {}
        for v, i, c in members:
            views_of.setdefault(c, set()).add(v)
        first = {}
        for v, i, c in members:
            first.setdefault(c, (v, i))
        kept.append(min(views_of, key=lambda c: (-len(views_of[c]), first[c])))
    return kept


# ---- report -------------------------------------------------------------------------------------------------------

def _pct(a, b):
    return f"{100 * a / b:.1f}%" if b else "-"


def _view_cells(record):
    return [tuple(c) for c in record.get("cells", record.get("points", []))]


def _rows(path):
    with open(path, newline="") as f:
        return {(r["map_id"], r["sg_idx"]): r for r in csv.DictReader(f)}


def search_table(directory, run):
    names = ["astar", "wastar-w2", "llmastar_standard", run]
    present = {n: _rows(directory / f"{n}.csv") for n in names if (directory / f"{n}.csv").exists()}
    if "astar" not in present:
        return ["(no astar.csv in this directory)"]
    common = set(present["astar"])
    for rows in present.values():
        common &= {k for k, r in rows.items() if r["valid"] == "1"}
    lines = [f"| run | n | " + " | ".join(METRICS) + " |", "|---|---|" + "---|" * len(METRICS)]
    for name, rows in present.items():
        vals = []
        for m in METRICS:
            ratios = [float(rows[k][m]) / float(present["astar"][k][m]) for k in common]
            vals.append(f"{100 * math.exp(sum(map(math.log, ratios)) / len(ratios)):.2f}" if ratios else "-")
        lines.append(f"| {name} | {len(common)} | " + " | ".join(vals) + " |")
    missing = [n for n in names if n not in present]
    if missing:
        lines.append(f"\nnot run yet: {', '.join(missing)}")
    return lines


def split_table(directory, reference="wastar-w2"):
    """Every LLM run vs weighted A* (= 100), split by whether the search ended with waypoints (n_targets > 2: the
    target list always holds start and goal). A stall fallback clears the waypoints, so those queries count as
    'none' and the fallback column says how many of them it was."""
    directory = Path(directory)
    if not (directory / f"{reference}.csv").exists():
        return [f"(no {reference}.csv in this directory)"]
    ref = _rows(directory / f"{reference}.csv")
    lines = ["| run | waypoints | n | operation | storage | stall fallback |", "|---|---|---|---|---|---|"]
    for path in sorted(directory.glob("*.csv")):
        if not path.stem.startswith(("llmastar", "quorumastar")):
            continue
        rows = _rows(path)
        for label, used in (("used", True), ("none", False)):
            keys = [k for k, r in rows.items() if k in ref and r["valid"] == "1" and ref[k]["valid"] == "1"
                    and (int(r["n_targets"] or 0) > 2) == used]
            vals = []
            for m in ("operation", "storage"):
                ratios = [float(rows[k][m]) / float(ref[k][m]) for k in keys]
                vals.append(f"{100 * math.exp(sum(map(math.log, ratios)) / len(ratios)):.1f}" if ratios else "-")
            fallback = sum(rows[k].get("fallback") == "1" for k in keys)
            lines.append(f"| {path.stem} | {label} | {len(keys)} | {vals[0]} | {vals[1]} | {fallback} |")
    return lines


def report(directory, run, dataset):
    directory = Path(directory)
    if not (directory / "raw" / f"{run}.jsonl").exists():
        found = sorted(p.stem for p in (directory / "raw").glob("quorumastar*.jsonl"))
        raise SystemExit(f"no {directory / 'raw' / (run + '.jsonl')}; quorumastar runs here: {found or 'none'}")
    queries ={(str(q["map_id"]), str(q["sg_idx"])): q for q in load_queries(dataset)}
    records = []
    for line in open(directory / "raw" / f"{run}.jsonl", encoding="utf-8"):
        r = json.loads(line)
        key = (str(r["map_id"]), str(r["sg_idx"]))
        if key in queries:
            records.append((queries[key], r))
    if not records:
        raise SystemExit(f"no record of {directory / 'raw' / (run + '.jsonl')} matches a query of {dataset}")
    views = list(dict.fromkeys(v["view"] for _, r in records for v in r.get("views", [])))
    out = [f"# Pilot report: {run} ({len(records)} queries, {directory})", ""]

    # solo quality and the per-query answers
    answers = []  # per query: {view: [cells]} for the views that answered
    solo = {v: {"abstain": 0, "wp": 0, "good": 0, "q_good": 0, "answered": 0} for v in views}
    for query, r in records:
        got = {}
        for rec in r.get("views", []):
            s = solo[rec["view"]]
            if rec["abstained"]:
                s["abstain"] += 1
                continue
            cells = list(dict.fromkeys(_view_cells(rec)))
            got[rec["view"]] = cells
            good = [c for c in cells if not is_bad(c, query)]
            s["answered"] += 1
            s["wp"] += len(cells)
            s["good"] += len(good)
            s["q_good"] += bool(good)
        answers.append((query, r, got))
    out += ["## Solo quality per view", "", "| view | abstained | waypoints | good | queries with a good waypoint |",
            "|---|---|---|---|---|"]
    for v, s in solo.items():
        out.append(f"| {v} | {s['abstain']}/{len(records)} | {s['wp']} | {_pct(s['good'], s['wp'])} | "
                   f"{_pct(s['q_good'], s['answered'])} |")

    # independence
    out += ["", "## Shared bad waypoints (row view's bad waypoints also proposed by the column view; lower = more "
                "independent)", "", "| bad of \\ also in | " + " | ".join(views) + " |", "|---|" + "---|" * len(views)]
    for a in views:
        cells = []
        for v in views:
            bad = shared = 0
            for query, _, got in answers:
                if a in got and v in got:
                    for c in got[a]:
                        if is_bad(c, query):
                            bad += 1
                            shared += c in got[v]
            cells.append("-" if a == v else _pct(shared, bad))
        out.append(f"| {a} | " + " | ".join(cells) + " |")

    # voting as run
    voted = sum(bool(r.get("votes")) for _, r in records)
    final = [(q, tuple(w)) for q, r in records for w in r.get("waypoints", [])]
    out += ["", "## Voting", "", f"As run: {voted}/{len(records)} queries kept at least one waypoint by vote; final "
            f"waypoints {len(final)}, good {_pct(sum(not is_bad(w, q) for q, w in final), len(final))}.", "",
            "Simulated from the same answers (quorum 2): queries with a kept waypoint / kept waypoints / good share.",
            "", "| views | " + " | ".join(f"r = {r}" for r in RADII) + " |", "|---|" + "---|" * len(RADII)]
    for combo in [tuple(views)] + ([c for c in itertools.combinations(views, 3)] if len(views) > 3 else []):
        cells = []
        for radius in RADII:
            n_q = n_wp = n_good = 0
            for query, _, got in answers:
                kept = simulate_vote([got[v] for v in combo if v in got], radius)
                n_q += bool(kept)
                n_wp += len(kept)
                n_good += sum(not is_bad(c, query) for c in kept)
            cells.append(f"{n_q} / {n_wp} / {_pct(n_good, n_wp)}")
        out.append(f"| {','.join(combo)} | " + " | ".join(cells) + " |")

    # vision judge
    shown_bad = shown_good = caught = false_alarm = abstained = 0
    for query, r in records:
        judge = r.get("judge")
        if not judge:
            continue
        if judge.get("abstained"):
            abstained += 1
            continue
        removed = set(judge.get("remove") or [])
        for i, vote in enumerate(r.get("votes", []), start=1):
            if is_bad(vote["cell"], query):
                shown_bad += 1
                caught += i in removed
            else:
                shown_good += 1
                false_alarm += i in removed
    out += ["", "## Vision judge", "", f"catch rate {_pct(caught, shown_bad)} ({caught}/{shown_bad} bad waypoints "
            f"removed), false-alarm rate {_pct(false_alarm, shown_good)} ({false_alarm}/{shown_good} good removed), "
            f"abstained {abstained}."]

    # search metrics and cost
    calls = sum(r.get("calls", 0) for _, r in records)
    tokens = sum(r.get("prompt_tokens", 0) + r.get("completion_tokens", 0) for _, r in records)
    out += ["", "## Search (geometric mean vs A* = 100, lower is better)", ""] + search_table(directory, run)
    out += ["", "## Every LLM run vs weighted A* (w = 2, = 100), by whether the search kept waypoints", ""]
    out += split_table(directory)
    out += ["", f"LLM: {calls} new calls, {tokens} tokens ({tokens / len(records):.0f} per query)."]
    text = "\n".join(out)
    print(text)
    (directory / f"pilot_{run}.md").write_text(text + "\n", encoding="utf-8")
    return text


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    m = sub.add_parser("make")
    m.add_argument("--size", type=int, default=50)
    m.add_argument("--seed", type=int, default=1)
    m.add_argument("--out", default="pilot/pilot_maps.json")
    r = sub.add_parser("report")
    r.add_argument("--dir", required=True, help="outputs root/<model>, e.g. outputs_pilot/gpt-4o-mini")
    r.add_argument("--run", default="quorumastar")
    r.add_argument("--dataset", default="pilot/pilot_maps.json")
    args = p.parse_args(argv)
    if args.cmd == "make":
        maps = make_maps(args.size, args.seed)
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        with open(args.out, "w") as f:
            json.dump(maps, f)
        print(f"wrote {args.out}: {len(maps)} maps (seed {args.seed}, disjoint from the few-shot pool)")
    else:
        report(args.dir, args.run, args.dataset)


if __name__ == "__main__":
    main()
