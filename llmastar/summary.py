"""Aggregate outputs/<model>/*.csv into the paper's Table 1 format; writes summary.md and summary.csv.

  python -m llmastar.summary --model llama-3-8b-instruct

operation / storage / length: geometric mean over queries where both the run and A* found a valid path of
(run metric / A* metric) x 100. valid: % of the run's queries with a valid path.
"""
import argparse
import csv
import math
from pathlib import Path

from llmastar.outputs import OUTPUTS_ROOT, model_slug

METRICS = ("operation", "storage", "length")
# Table 1 of arXiv 2407.02511: the baselines and the LLAMA3 rows (operation, storage, length, valid).
PAPER = {
    "astar": (100, 100, 100, 100),
    "dwastar": (60.91, 78.53, 100.24, 100),
    "llm_only_standard": (None, None, 111.05, 12.60),
    "llm_only_cot": (None, None, 114.89, 12.00),
    "llm_only_repe": (None, None, 138.32, 16.40),
    "llmastar_standard": (44.59, 64.02, 102.47, 100),
    "llmastar_cot": (47.60, 66.27, 102.46, 100),
    "llmastar_repe": (64.08, 80.19, 102.54, 100),
}
ORDER = list(PAPER)
NOT_RUNS = {"summary.csv", "scalability.csv"}


def read_rows(path):
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def geomean(values):
    return math.exp(sum(math.log(v) for v in values) / len(values))


def summarize(rows, baseline):
    base = {(r["map_id"], r["sg_idx"]): r for r in baseline if r["valid"] == "1"}
    pairs = [(r, base[(r["map_id"], r["sg_idx"])]) for r in rows
             if r["valid"] == "1" and (r["map_id"], r["sg_idx"]) in base]
    n = len(rows)
    stats = {"n": n, "n_pairs": len(pairs), "valid": 100 * sum(r["valid"] == "1" for r in rows) / n if n else math.nan}
    lenient = [r["valid_lenient"] for r in rows if r.get("valid_lenient") not in (None, "")]
    stats["valid_lenient"] = 100 * lenient.count("1") / len(lenient) if lenient else None
    # LLM-A* queries left with only start and goal as targets: the heuristic is then 2 x distance to goal.
    targets = [r["n_targets"] for r in rows if r.get("n_targets") not in (None, "")]
    stats["no_targets"] = 100 * targets.count("2") / len(targets) if targets else None
    for metric in METRICS:
        ratios = [float(r[metric]) / float(b[metric]) for r, b in pairs if r[metric] != ""]
        stats[metric] = 100 * geomean(ratios) if ratios else None
    return stats


def summarize_file(path, baseline_path):
    rows = read_rows(path)
    baseline = read_rows(baseline_path) if Path(baseline_path).exists() else []
    return summarize(rows, baseline)


def run_csvs(model_dir):
    for path in sorted(Path(model_dir).glob("*.csv")):
        if path.name in NOT_RUNS:
            continue
        with open(path, newline="") as f:
            header = next(csv.reader(f), [])
        if {"map_id", "sg_idx", "valid", *METRICS} <= set(header):
            yield path


def _fmt(value):
    return "-" if value is None or (isinstance(value, float) and math.isnan(value)) else f"{value:.2f}"


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--model", default="llama-3-8b-instruct")
    p.add_argument("--out", default=str(OUTPUTS_ROOT), help="outputs root")
    args = p.parse_args(argv)

    model_dir = Path(args.out) / model_slug(args.model)
    baseline_path = model_dir / "astar.csv"
    if not baseline_path.exists():
        raise SystemExit(f"{baseline_path} not found; run `python -m llmastar.run --method astar` first.")
    baseline = read_rows(baseline_path)

    runs = sorted(run_csvs(model_dir), key=lambda p: (ORDER.index(p.stem) if p.stem in ORDER else len(ORDER), p.stem))
    table = []
    for path in runs:
        stats = summarize(read_rows(path), baseline)
        paper = PAPER.get(path.stem, (None,) * 4)
        table.append({"run": path.stem, **stats, **{f"paper_{k}": v for k, v in zip((*METRICS, "valid"), paper)}})

    columns = ["run", "n", "operation", "storage", "length", "valid", "valid_lenient", "no_targets",
               "paper_operation", "paper_storage", "paper_length", "paper_valid"]
    lines = ["| " + " | ".join(columns) + " |", "|" + "---|" * len(columns)]
    for row in table:
        cells = [row["run"], str(row["n"])] + [_fmt(row[c]) for c in columns[2:]]
        lines.append("| " + " | ".join(cells) + " |")
    markdown = "\n".join(lines)
    print(markdown)

    n_baseline = len(baseline)
    with open(model_dir / "summary.md", "w") as f:
        f.write(f"# {model_slug(args.model)}: results vs. A* (x100, geometric mean)\n\n")
        f.write(f"A* baseline: {n_baseline} queries. Ratios use queries where both the run and A* are valid; "
                "`valid` is the % of the run's queries with a valid path; `valid_lenient` (LLM-only) inserts a "
                "missing start/goal first. `no_targets` (LLM-A*) is the % of queries where no LLM waypoint "
                "survived filtering, so the search ran with h = 2 x distance to goal. "
                "`paper_*` columns: Table 1 of arXiv 2407.02511 (LLAMA3 rows).\n\n")
        f.write(markdown + "\n")
    with open(model_dir / "summary.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns + ["n_pairs"], extrasaction="ignore")
        writer.writeheader()
        for row in table:
            writer.writerow({k: ("" if row.get(k) is None else row.get(k)) for k in columns + ["n_pairs"]})


if __name__ == "__main__":
    main()
