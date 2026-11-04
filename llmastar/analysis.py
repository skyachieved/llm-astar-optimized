"""Failure cases and cost of the LLM runs in one outputs directory (agent.md step 7), for the report.

  python -m llmastar.analysis --dir outputs/gpt/gpt-4o-mini [--reference wastar-w2] [--baseline llmastar_standard]

Reads <dir>/<run>.csv for every llmastar* / quorumastar* run and, when present, <dir>/raw/<run>.jsonl (token use and
requests per query; the raw logs stay on the machine that ran them, so run this there). Writes <dir>/analysis.md:
  1. win / tie / loss on operations of every LLM run against the reference (weighted A*, w = 2) and against LLM-A*;
  2. Quorum-A* split by what reached the search: no waypoint, waypoints kept to the end, stall fallback fired;
  3. the queries where Quorum-A* does most worse than the reference, with what happened on them;
  4. cost per query: LLM requests, prompt and completion tokens (cached answers count: they were paid once),
     and the price at --price-in / --price-out dollars per million tokens (gpt-4o-mini list price by default).
"""
import argparse
import csv
import json
import math
from pathlib import Path

PRICE_IN, PRICE_OUT = 0.15, 0.60  # gpt-4o-mini, $ per 1M input / output tokens (OpenAI list price)


def _rows(path):
    with open(path, newline="") as f:
        return {(r["map_id"], r["sg_idx"]): r for r in csv.DictReader(f)}


def _gm(ratios):
    return 100 * math.exp(sum(map(math.log, ratios)) / len(ratios)) if ratios else float("nan")


def _f(x, digits=1):
    return "-" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{x:.{digits}f}"


def llm_runs(directory):
    return sorted(p.stem for p in Path(directory).glob("*.csv")
                  if p.stem.startswith(("llmastar", "quorumastar")) and "stopnl" not in p.stem)


def win_tie_loss(run, ref):
    keys = [k for k in run if k in ref and run[k]["valid"] == "1" and ref[k]["valid"] == "1"]
    win = sum(int(run[k]["operation"]) < int(ref[k]["operation"]) for k in keys)
    loss = sum(int(run[k]["operation"]) > int(ref[k]["operation"]) for k in keys)
    return win, len(keys) - win - loss, loss, _gm([float(run[k]["operation"]) / float(ref[k]["operation"])
                                                    for k in keys])


def quorum_groups(run, ref):
    groups = {"no waypoint reached the search": [], "waypoints kept to the end": [], "stall fallback fired": []}
    for k, r in run.items():
        if k not in ref or r["valid"] != "1":
            continue
        ratio = float(r["operation"]) / float(ref[k]["operation"])
        if r.get("fallback") == "1":
            groups["stall fallback fired"].append(ratio)
        elif int(r["n_targets"] or 2) > 2:
            groups["waypoints kept to the end"].append(ratio)
        else:
            groups["no waypoint reached the search"].append(ratio)
    return groups


def raw_cost(path):
    """(requests, prompt tokens, completion tokens) per query from a raw log, or None."""
    if not path.exists():
        return None
    n = req = tin = tout = 0
    for line in open(path, encoding="utf-8"):
        r = json.loads(line)
        n += 1
        if "views" in r:  # Quorum-A*: the views and the judge
            calls = list(r["views"]) + ([r["judge"]] if r.get("judge") else [])
            req += len(calls)
            tin += sum(c.get("prompt_tokens") or 0 for c in calls)
            tout += sum(c.get("completion_tokens") or 0 for c in calls)
        else:  # LLM-A* / LLM-only: one request
            usage = r.get("usage") or {}
            req += 1
            tin += usage.get("prompt_tokens") or 0
            tout += usage.get("completion_tokens") or 0
    return (req / n, tin / n, tout / n) if n else None


def csv_cost(run):
    """Fallback without the raw log: Quorum-A*'s CSV has the token columns (requests unknown)."""
    tin = [int(r["prompt_tokens"]) for r in run.values() if r.get("prompt_tokens")]
    tout = [int(r["completion_tokens"]) for r in run.values() if r.get("completion_tokens")]
    return (None, sum(tin) / len(tin), sum(tout) / len(tout)) if tin else None


def report(directory, reference="wastar-w2", baseline="llmastar_standard", price_in=PRICE_IN, price_out=PRICE_OUT,
           worst=10):
    d = Path(directory)
    ref = _rows(d / f"{reference}.csv")
    base = _rows(d / f"{baseline}.csv") if (d / f"{baseline}.csv").exists() else None
    runs = {name: _rows(d / f"{name}.csv") for name in llm_runs(d)}
    small = [name for name, run in runs.items() if len(run) < len(ref) / 2]  # e.g. a 10-query check run
    runs = {name: run for name, run in runs.items() if name not in small}
    out = [f"# Failure cases and cost: {d}", "",
           f"Operations of each LLM run against {reference} (= 100) and against {baseline}; a win is strictly fewer "
           "operations on a query, a tie the same number.", "",
           f"| run | vs {reference}: win / tie / loss | ops (geo. mean) | vs {baseline}: win / tie / loss |",
           "|---|---|---|---|"]
    if small:
        out[2] += f" Left out (fewer than half of the {len(ref)} queries): {', '.join(small)}."
    for name, run in runs.items():
        w, t, l, gm = win_tie_loss(run, ref)
        vs_base = "-" if base is None or name == baseline else "{} / {} / {}".format(*win_tie_loss(run, base)[:3])
        out.append(f"| {name} | {w} / {t} / {l} | {_f(gm)} | {vs_base} |")

    for name in [n for n in runs if n.startswith("quorumastar")][:1] or []:
        run = runs[name]
        out += ["", f"## {name}: what reached the search (ops vs {reference} = 100)", "",
                "| case | queries | ops (geo. mean) | better / equal / worse |", "|---|---|---|---|"]
        for label, ratios in quorum_groups(run, ref).items():
            out.append(f"| {label} | {len(ratios)} | {_f(_gm(ratios))} | {sum(x < 1 for x in ratios)} / "
                       f"{sum(x == 1 for x in ratios)} / {sum(x > 1 for x in ratios)} |")
        keys = [k for k in run if k in ref and run[k]["valid"] == "1"]
        keys.sort(key=lambda k: -float(run[k]["operation"]) / float(ref[k]["operation"]))
        out += ["", f"## {name}: the {worst} queries most worse than {reference}", "",
                f"| map:sg | ops {name} | ops {reference} | ops {baseline} | waypoints given | kept targets | "
                "stall fallback (pop) |", "|---|---|---|---|---|---|---|"]
        for k in keys[:worst]:
            r = run[k]
            b = base[k]["operation"] if base and k in base else "-"
            fb = f"yes ({r['fallback_pop']})" if r.get("fallback") == "1" else "no"
            out.append(f"| {k[0]}:{k[1]} | {r['operation']} | {ref[k]['operation']} | {b} | {r['n_waypoints']} | "
                       f"{int(r['n_targets'] or 2) - 2} | {fb} |")

    out += ["", f"## Cost per query (${price_in} / ${price_out} per 1M input / output tokens)", "",
            "| run | LLM requests | prompt tokens | completion tokens | $ per query | $ per 1,000 queries | source |",
            "|---|---|---|---|---|---|---|"]
    for name, run in runs.items():
        cost, source = raw_cost(d / "raw" / f"{name}.jsonl"), "raw log"
        if cost is None:
            cost, source = csv_cost(run), "CSV"
        if cost is None:
            out.append(f"| {name} | - | - | - | - | - | no raw log here |")
            continue
        req, tin, tout = cost
        dollars = (tin * price_in + tout * price_out) / 1e6
        out.append(f"| {name} | {_f(req, 2)} | {tin:,.0f} | {tout:,.0f} | {dollars:.5f} | {1000 * dollars:.2f} | "
                   f"{source} |")
    text = "\n".join(out)
    print(text)
    (d / "analysis.md").write_text(text + "\n", encoding="utf-8")
    return text


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--dir", required=True, help="an outputs directory with runs, e.g. outputs/gpt/gpt-4o-mini")
    p.add_argument("--reference", default="wastar-w2")
    p.add_argument("--baseline", default="llmastar_standard")
    p.add_argument("--price-in", type=float, default=PRICE_IN)
    p.add_argument("--price-out", type=float, default=PRICE_OUT)
    p.add_argument("--worst", type=int, default=10)
    args = p.parse_args(argv)
    report(args.dir, args.reference, args.baseline, args.price_in, args.price_out, args.worst)


if __name__ == "__main__":
    main()
