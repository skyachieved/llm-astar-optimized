"""95% confidence intervals and standard deviations for the report, from the committed per-query CSVs.

Usage (from the repository root): python -m llmastar.ci_stats [<repo root> [<output .md>]]
       defaults: repo root ".", output "outputs/report/ci_tables.md"
Read-only: it only reads outputs/**.csv. Standard library only.

Method (matches llmastar/summary.py for the point estimates):
  per query i, r_i = method_i / A*_i over queries where both found a valid path (map_id, sg_idx);
  geometric mean GM = exp(mean(ln r_i)) x 100;
  95% CI = exp(mean(ln r) +- t_{0.975, n-1} * sd(ln r) / sqrt(n)) x 100  (t-interval on log ratios);
  SD = sample standard deviation of the per-query ratios r_i x 100 (arithmetic).
Paired comparisons (method A vs B) use r_i = A_i / B_i the same way.
"""
import csv
import math
import sys
from pathlib import Path

METRICS = ("operation", "storage", "length")


def load(path):
    with open(path, newline="", encoding="utf-8") as f:
        return {(r["map_id"], r["sg_idx"]): r for r in csv.DictReader(f) if r["valid"] == "1"}


def t975(n):
    """Two-sided 95% Student-t quantile with n - 1 degrees of freedom (Cornish-Fisher expansion)."""
    z, df = 1.959963984540054, n - 1
    return z + (z ** 3 + z) / (4 * df) + (5 * z ** 5 + 16 * z ** 3 + 3 * z) / (96 * df ** 2)


def stats(ratios):
    n = len(ratios)
    logs = [math.log(x) for x in ratios]
    m = sum(logs) / n
    sd_log = math.sqrt(sum((x - m) ** 2 for x in logs) / (n - 1))
    half = t975(n) * sd_log / math.sqrt(n)
    pct = [100 * x for x in ratios]
    mean_pct = sum(pct) / n
    sd_pct = math.sqrt(sum((x - mean_pct) ** 2 for x in pct) / (n - 1))
    return {"n": n, "gm": 100 * math.exp(m), "lo": 100 * math.exp(m - half), "hi": 100 * math.exp(m + half),
            "sd": sd_pct}


def paired(a_rows, b_rows, metric):
    return [float(a[metric]) / float(b_rows[k][metric]) for k, a in a_rows.items() if k in b_rows]


def fmt(s):
    return f"{s['gm']:.2f} [{s['lo']:.2f}, {s['hi']:.2f}] (SD {s['sd']:.1f})"


def main(root, out):
    root = Path(root)
    # (label, folder, {method label: run name})
    models = [
        ("Llama-3-8B (Table 1)", "outputs/llama-3-8b-instruct",
         {"Dynamic WA*": "dwastar", "LLM-A* few-shot": "llmastar_standard", "LLM-A* CoT": "llmastar_cot",
          "LLM-A* RePE": "llmastar_repe", "No waypoints (wA*, w=2)": "wastar-w2"}),
        ("GPT-4o mini", "outputs/gpt/gpt-4o-mini",
         {"LLM-A* few-shot": "llmastar_standard", "LLM-A* CoT": "llmastar_cot", "LLM-A* RePE": "llmastar_repe",
          "wA* w=1.5": "wastar-w1.5", "No waypoints (wA*, w=2)": "wastar-w2", "wA* w=3": "wastar-w3",
          "Quorum-A*": "quorumastar"}),
        ("GPT-4.1 mini", "outputs/other/gpt-4.1-mini",
         {"LLM-A* few-shot": "llmastar_standard", "No waypoints (wA*, w=2)": "wastar-w2", "Quorum-A*": "quorumastar"}),
        ("GPT-4.1", "outputs/other/gpt-4.1",
         {"LLM-A* few-shot": "llmastar_standard", "No waypoints (wA*, w=2)": "wastar-w2", "Quorum-A*": "quorumastar"}),
        ("Qwen2.5-VL-7B", "outputs/qwen/qwen2.5-vl-7b-instruct",
         {"LLM-A* few-shot": "llmastar_standard-max512", "No waypoints (wA*, w=2)": "wastar-w2",
          "Quorum-A*": "quorumastar-max512"}),
        ("Claude Opus 5.5", "outputs/claude/claude-opus-5-5",
         {"LLM-A* few-shot": "llmastar_standard", "No waypoints (wA*, w=2)": "wastar-w2", "Quorum-A*": "quorumastar"}),
    ]
    lines = ["# 95% confidence intervals and standard deviations (from the committed CSVs)", "",
             "Each cell: geometric mean of the per-query ratio x 100 [95% CI] (SD of the per-query ratio x 100).",
             "A* = 100; queries where both the run and A* found a valid path.", ""]
    for label, folder, runs in models:
        base = load(root / folder / "astar.csv")
        lines += [f"## {label}  (`{folder}`)", "", "| method | n | operation | storage | length |", "|---|---|---|---|---|"]
        loaded = {m: load(root / folder / f"{run}.csv") for m, run in runs.items()}
        for m, rows in loaded.items():
            cells = [fmt(stats(paired({k: r for k, r in rows.items()}, base, metric))) for metric in METRICS]
            n = stats(paired(rows, base, "operation"))["n"]
            lines.append(f"| {m} | {n} | " + " | ".join(cells) + " |")
        lines.append("")
        if "Quorum-A*" in loaded:
            lines += ["Paired operation ratio (A / B x 100) [95% CI] (SD):", ""]
            pairs = [("Quorum-A*", "LLM-A* few-shot"), ("Quorum-A*", "No waypoints (wA*, w=2)"),
                     ("LLM-A* few-shot", "No waypoints (wA*, w=2)")]
            for a, b in pairs:
                s = stats(paired(loaded[a], loaded[b], "operation"))
                lines.append(f"- {a} vs {b}: n = {s['n']}, {fmt(s)}")
            lines.append("")

    # ablations (GPT-4o mini) and harder maps: paired operation ratio vs the default / no-waypoint search
    abl = [("outputs/gpt/gpt-4o-mini", "quorumastar", [("no stall fallback", "quorumastar-k0"),
                                                      ("no removal checks", "quorumastar-rm0"),
                                                      ("+ vision judge", "quorumastar-vision")]),
           ("outputs/gpt_ablation300/gpt-4o-mini", "quorumastar", [
               ("no vote (union)", "quorumastar-add1"), ("unanimity", "quorumastar-add3"),
               ("text view only", "quorumastar-vtext-add1"), ("corners view only", "quorumastar-vcorners-add1"),
               ("relations view only", "quorumastar-vrelations-add1"),
               ("image instead of relations", "quorumastar-vtext+corners+image"),
               ("four views", "quorumastar-vtext+corners+relations+image"), ("no snap", "quorumastar-nosnap"),
               ("few-shot shared", "quorumastar-fsshared"), ("few-shot none", "quorumastar-fsnone"),
               ("CoT", "quorumastar-cot"), ("roles", "quorumastar-roles"), ("+ vision judge", "quorumastar-vision")])]
    lines += ["## Ablations (GPT-4o mini): operation ratio, variant / default x 100 [95% CI] (SD)", ""]
    for folder, default, variants in abl:
        d = load(root / folder / f"{default}.csv")
        base = load(root / folder / "astar.csv")
        lines.append(f"`{folder}` (default vs A*: {fmt(stats(paired(d, base, 'operation')))})")
        lines.append("")
        for name, run in variants:
            v = load(root / folder / f"{run}.csv")
            s = stats(paired(v, d, "operation"))
            a = stats(paired(v, base, "operation"))
            lines.append(f"- {name}: vs default n = {s['n']}, {fmt(s)}; vs A* {fmt(a)}")
        lines.append("")
    # Table 3: queries where the vote passed waypoints on (stall fallback fired, or waypoints kept), vs no waypoints
    lines += ["## Queries where the vote passed waypoints on: Quorum-A* / no-waypoint search x 100 [95% CI] (SD)", ""]
    for label, folder, runs in models[1:]:
        q, w2 = load(root / folder / f"{runs['Quorum-A*']}.csv"), load(root / folder / "wastar-w2.csv")
        sel = {k: r for k, r in q.items() if r.get("fallback") == "1" or int(r["n_targets"] or 2) > 2}
        lines.append(f"- {label}: n = {len(sel)}, {fmt(stats(paired(sel, w2, 'operation')))}")
    lines.append("")
    hard = [("GPT-4o mini", "gpt", "gpt-4o-mini", "quorumastar", "llmastar_standard"),
            ("GPT-4.1 mini", "other", "gpt-4.1-mini", "quorumastar", "llmastar_standard"),
            ("GPT-4.1", "other", "gpt-4.1", "quorumastar", "llmastar_standard"),
            ("Qwen2.5-VL-7B", "qwen", "qwen2.5-vl-7b-instruct", "quorumastar-max512", "llmastar_standard-max512")]
    lines += ["## Harder maps: operations vs A* [95% CI] (SD), and Quorum-A* / no-waypoint search", ""]
    for kind in ("dense", "large", "zigzag"):
        for label, prefix, model, q, l in hard:
            folder = root / f"outputs/{prefix}_{kind}/{model}"
            base, w2 = load(folder / "astar.csv"), load(folder / "wastar-w2.csv")
            qa, la = load(folder / f"{q}.csv"), load(folder / f"{l}.csv")
            lines.append(f"- {kind}, {label}: no waypoints {fmt(stats(paired(w2, base, 'operation')))}; "
                         f"LLM-A* {fmt(stats(paired(la, base, 'operation')))}; "
                         f"Quorum-A* {fmt(stats(paired(qa, base, 'operation')))}; "
                         f"Quorum-A* / no waypoints {fmt(stats(paired(qa, w2, 'operation')))}")
        lines.append("")
    Path(out).write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    args = sys.argv[1:3]
    main(args[0] if args else ".", args[1] if len(args) > 1 else "outputs/report/ci_tables.md")
