"""The report's tables, from committed outputs only (agent.md step 7): every number here is read from a CSV or an
analysis.md under outputs/, never typed in or estimated.

  python -m llmastar.report [--out outputs/report]

Writes <out>/tables.md:
  1. benchmark (1,000 queries), every model: operation / storage / length of A*, weighted A* (w = 2), LLM-A* and
     Quorum-A*, then paired tests of Quorum-A* against LLM-A* and against weighted A* (llmastar.stats);
  2. the harder generated maps (dense, large, zigzag; 100 each), the same comparison;
  3. cost per query (LLM requests, tokens, $ per 1,000 queries), copied from each folder's analysis.md;
  4. gpt-4o-mini ablations: on all 1,000 queries and on the first 300, each against the default with a paired test;
  5. the pilot (50 self-generated maps) on every model that ran it: the settings the defaults were chosen from.
A model or run that has not been run yet is shown as "not run yet", never filled in.
"""
import argparse
import csv
import re
from pathlib import Path

from llmastar.stats import compare, fmt_p
from llmastar.summary import geomean, summarize

OUT = Path("outputs")
KINDS = ("dense", "large", "zigzag")
# label, model folder name, benchmark folder, folder of each generated-map kind, pilot folder
MODELS = [
    ("GPT-4o mini", "gpt-4o-mini", "gpt", "gpt_{kind}", "pilot"),
    ("GPT-4.1 mini", "gpt-4.1-mini", "other", "other_{kind}", None),
    ("GPT-4.1", "gpt-4.1", "other", "other_{kind}", None),
    ("Qwen2.5-VL-7B", "qwen2.5-vl-7b-instruct", "qwen", "qwen_{kind}", "qwen_pilot"),
    ("Claude Opus 5.5*", "claude-opus-5-5", "claude", "claude_{kind}", None),
]
NOTE_SAMPLING = ("*Claude Opus 5.5 always thinks before answering and its API rejects temperature, top_p and JSON mode,"
                 " so it runs with the model's own sampling (`--model-sampling`, max_tokens 16,000 for thinking +"
                 " answer); every other model runs at temperature 0. Its answers are not deterministic; the cache"
                 " makes a rerun reproduce them.")
METHODS = [("astar", "A*"), ("wastar-w2", "Weighted A* (w = 2)"), ("llmastar_standard", "LLM-A*"),
           ("quorumastar", "Quorum-A*")]
ABLATIONS_1000 = [  # run, what differs from the default
    ("quorumastar-vision", "+ vision judge (removal vote by code, support and an image check)"),
    ("quorumastar-rm0", "no removal step"),
    ("quorumastar-k0", "no stall fallback"),
    ("quorumastar-vtext-fspaper-nosnap-add1-k0", "all off: text view with the paper's prompt, no vote, no snap, "
                                                 "no fallback (= LLM-A*)"),
]
ABLATIONS_300 = [
    ("quorumastar-add1", "add quorum 1: union of the three views, no vote"),
    ("quorumastar-add3", "add quorum 3: all three views must agree"),
    ("quorumastar-vtext-add1", "text view alone"),
    ("quorumastar-vcorners-add1", "corners view alone"),
    ("quorumastar-vrelations-add1", "relations view alone"),
    ("quorumastar-vtext+corners+image", "image view instead of relations"),
    ("quorumastar-vtext+corners+relations+image", "all four views"),
    ("quorumastar-vision", "+ vision judge"),
    ("quorumastar-nosnap", "no snapping to canonical cells"),
    ("quorumastar-fsshared", "few-shot: the same examples for every view"),
    ("quorumastar-fsnone", "few-shot: none"),
    ("quorumastar-cot", "each view reasons briefly before answering"),
    ("quorumastar-roles", "each view gets its own system role"),
]
# The pilot runs on gpt-4o-mini were made while the judge was on by default (outputs/pilot/README.md), so the same
# setting has a different run name there.
PILOT = [  # setting, gpt-4o-mini pilot run, run on a later model
    ("Weighted A* (w = 2)", "wastar-w2", "wastar-w2"),
    ("LLM-A*", "llmastar_standard", "llmastar_standard"),
    ("Quorum-A*: text, corners, relations (default)", "quorumastar-novision", "quorumastar"),
    ("  + vision judge", "quorumastar", "quorumastar-vision"),
    ("  image view instead of relations", None, "quorumastar-vtext+corners+image"),
    ("  all four views + vision judge", "quorumastar-vtext+corners+image+relations",
     "quorumastar-vtext+corners+image+relations-vision"),
]
NOT_RUN = "not run yet"
SKIPPED = {"claude-opus-5-5": "not run (API budget)"}  # map sets a model leaves out on purpose
# LLM runs of a model that carry a sampling suffix in their names (the suffix records a setting that differs from the
# other models; see NOTE_QWEN). Tables look a run up under its plain name first, then with the suffix.
SUFFIX = {"qwen2.5-vl-7b-instruct": "-max512"}
NOTE_QWEN = ("Qwen2.5-VL-7B runs with max_tokens 512 (run names end in -max512; every other model 2,048): its normal"
             " answers are short (LLM-A* about 24 tokens, a view under 100), but now and then it repeats itself up to"
             " the limit, and the fp16 V100 server writes such an answer at about 1.4 tokens per second, so 2,048"
             " tokens took about 24 minutes. The cap only shortens those repetitions.")


def rows(path):
    path = Path(path)
    if not path.exists():
        return None
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def resolve(folder, run):
    """The run's name in this folder: plain, else with the model's suffix (SUFFIX), else plain."""
    folder = Path(folder)
    suffixed = run + SUFFIX.get(folder.name, "")
    return suffixed if not (folder / f"{run}.csv").exists() and (folder / f"{suffixed}.csv").exists() else run


def metrics(folder, run):
    """operation / storage / length of a run against A* in the same folder (summary.py's definition), or None."""
    r, base = rows(Path(folder) / f"{resolve(folder, run)}.csv"), rows(Path(folder) / "astar.csv")
    return summarize(r, base) if r and base else None


def _num(x, digits=2):
    return "-" if x is None else f"{x:.{digits}f}"


def _cells(m):
    return [_num(m["operation"]), _num(m["storage"]), _num(m["length"])] if m else [NOT_RUN] * 3


def _test_cells(folder, run, other):
    a, b = rows(Path(folder) / f"{resolve(folder, run)}.csv"), rows(Path(folder) / f"{resolve(folder, other)}.csv")
    if not a or not b:
        return [NOT_RUN] * 3
    c = compare(a, b)
    return [f"{c['wins']} / {c['ties']} / {c['losses']}", _num(c["ratio"], 1),
            f"{fmt_p(c['p_wilcoxon'])} / {fmt_p(c['p_sign'])}"]


def _table(header, body):
    lines = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    lines += ["| " + " | ".join(str(c) for c in row) + " |" for row in body]
    return lines


def benchmark_tables(out=OUT):
    body, tests = [], []
    for label, model, bench, _, _ in MODELS:
        folder = out / bench / model
        for run, name in METHODS:
            if run == "astar":
                continue
            body.append([label, name, *_cells(metrics(folder, run))])
        tests.append([label, *_test_cells(folder, "quorumastar", "llmastar_standard"),
                      *_test_cells(folder, "quorumastar", "wastar-w2")])
    return (_table(["model", "method", "operation", "storage", "length"], body), _table(
        ["model", "vs LLM-A*: win / tie / loss", "ops ratio", "p (Wilcoxon / sign)",
         "vs weighted A*: win / tie / loss", "ops ratio", "p (Wilcoxon / sign)"], tests))


def hard_table(out=OUT):
    body = []
    for label, model, _, hard, _ in MODELS:
        for kind in KINDS:
            folder = out / hard.format(kind=kind) / model
            ops = [metrics(folder, run) for run in ("wastar-w2", "llmastar_standard", "quorumastar")]
            if not any(ops) and model in SKIPPED:
                body.append([label, kind, SKIPPED[model], "", "", "", "", "", ""])
                continue
            body.append([label, kind, *[_num(m["operation"]) if m else NOT_RUN for m in ops],
                         *_test_cells(folder, "quorumastar", "llmastar_standard")[::2],
                         *_test_cells(folder, "quorumastar", "wastar-w2")[::2]])
    return _table(["model", "maps", "ops weighted A*", "ops LLM-A*", "ops Quorum-A*",
                   "vs LLM-A*: W / T / L", "p (Wilcoxon / sign)", "vs weighted A*: W / T / L",
                   "p (Wilcoxon / sign)"], body)


def cost_rows(analysis_md):
    """{run: (requests, prompt tokens, completion tokens, $ per 1,000)} from an analysis.md cost table."""
    path = Path(analysis_md)
    if not path.exists():
        return {}
    text = path.read_text()
    price = re.search(r"## Cost per query \(\$([\d.]+) / \$([\d.]+)", text)
    found = {}
    for line in text.split("## Cost per query", 1)[-1].splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) == 7 and cells[0] not in ("run", "---") and not cells[0].startswith("-"):
            found[cells[0]] = (cells[1], cells[2], cells[3], cells[5])
    return {"price": price.groups() if price else None, **found}


def cost_table(out=OUT):
    body = []
    for label, model, bench, _, _ in MODELS:
        c = cost_rows(out / bench / model / "analysis.md")
        price = c.pop("price", None)
        price_note = f"${price[0]} / ${price[1]}" if price else "-"
        if not c:
            body.append([label, NOT_RUN, "", "", "", "", ""])
        for run in ("llmastar_standard", "quorumastar", "quorumastar-vision"):
            name = run if run in c else run + SUFFIX.get(model, "")
            if name in c:
                body.append([label, name, *c[name], price_note])
    return _table(["model", "run", "LLM requests / query", "prompt tokens / query", "completion tokens / query",
                   "$ per 1,000 queries", "price in / out per 1M tokens"], body)


def ablation_table(folder, runs):
    folder = Path(folder)
    default = metrics(folder, "quorumastar")
    body = [["quorumastar", "default", *_cells(default), "-", "-"]]
    for run, what in runs:
        m = metrics(folder, run)
        if not m:
            body.append([run, what, NOT_RUN, "", "", "", ""])
            continue
        t = _test_cells(folder, run, "quorumastar")
        body.append([run, what, *_cells(m), t[0], t[2]])
    for run, name in (("wastar-w2", "weighted A* (w = 2)"), ("llmastar_standard", "LLM-A*")):
        body.append([run, name, *_cells(metrics(folder, run)), "", ""])
    return _table(["run", "differs from the default", "operation", "storage", "length",
                   "vs default: win / tie / loss", "p (Wilcoxon / sign)"], body)


def pilot_table(out=OUT):
    pilots = [(label, out / pilot / model) for label, model, _, _, pilot in MODELS if pilot]
    body = []
    for setting, first, later in PILOT:
        row = [setting]
        for i, (_, folder) in enumerate(pilots):
            run = first if i == 0 else later
            m = metrics(folder, run) if run else None
            row.append(_num(m["operation"]) if m else ("not run" if run is None else NOT_RUN))
        body.append(row)
    return _table(["setting (operation, A* = 100)", *[label for label, _ in pilots]], body)


def build(out=OUT):
    bench, tests = benchmark_tables(out)
    parts = [
        "# Report tables",
        "",
        "Generated by `python -m llmastar.report` from the committed outputs; do not edit by hand. operation / storage"
        " / length: geometric mean over queries of (method / A*) x 100 (llmastar/summary.py). Paired tests"
        " (llmastar/stats.py) compare operations query by query: a win is strictly fewer operations; ops ratio is the"
        " geometric mean of Quorum-A* / other x 100; p-values are two-sided.",
        "",
        "## 1. Benchmark (1,000 queries)",
        "",
        *bench,
        "",
        NOTE_SAMPLING,
        "",
        NOTE_QWEN,
        "",
        "Quorum-A* against each baseline, query by query:",
        "",
        *tests,
        "",
        "## 2. Harder generated maps (100 queries each)",
        "",
        *hard_table(out),
        "",
        "## 3. Cost per query (benchmark; from each folder's analysis.md)",
        "",
        *cost_table(out),
        "",
        "Qwen2.5-VL-7B runs on our own GPUs, so its tokens are shown without a price. Claude's completion tokens"
        " include its thinking.",
        "",
        "## 4. Ablations (gpt-4o-mini)",
        "",
        "All 1,000 queries:",
        "",
        *ablation_table(out / "gpt" / "gpt-4o-mini", ABLATIONS_1000),
        "",
        "First 300 queries:",
        "",
        *ablation_table(out / "gpt_ablation300" / "gpt-4o-mini", ABLATIONS_300),
        "",
        "These are evaluation queries: they describe the method and were not used to choose the defaults, which came"
        " from the pilot below (agent.md Decisions).",
        "",
        "## 5. Pilot (50 self-generated maps; where the defaults came from)",
        "",
        *pilot_table(out),
        "",
    ]
    return "\n".join(parts)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--outputs", default=str(OUT), help="the outputs folder to read")
    p.add_argument("--out", default="outputs/report", help="where tables.md goes")
    args = p.parse_args(argv)
    text = build(Path(args.outputs))
    Path(args.out).mkdir(parents=True, exist_ok=True)
    (Path(args.out) / "tables.md").write_text(text)
    print(f"wrote {Path(args.out) / 'tables.md'}")


if __name__ == "__main__":
    main()
