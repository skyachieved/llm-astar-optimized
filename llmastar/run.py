"""Run one method over the benchmark and write outputs/<model>/<run>.csv (+ raw/ and traces/).

  python -m llmastar.run --method astar
  python -m llmastar.run --method llmastar --prompt cot --limit 50

LLM methods first get waypoints for every query (concurrent requests, cached on disk), then run the
searches in worker processes. A search never talks to the LLM.
"""
import argparse
import csv
import json
import os
import time
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed

from llmastar.benchmark import DEFAULT_DATASET, evaluate_llm_path, load_queries
from llmastar.outputs import OUTPUTS_ROOT, RunPaths, run_name
from llmastar.pather import AStar, DWAStar, LLMAStar
from llmastar.waypoints import REGISTRY

METHODS = ("astar", "dwastar", "llm_only", "llmastar")
LLM_METHODS = ("llm_only", "llmastar")
QUERY_KEYS = ("start", "goal", "range_x", "range_y", "horizontal_barriers", "vertical_barriers")
CSV_FIELDS = ["map_id", "sg_idx", "start", "goal", "method", "prompt", "model", "operation", "storage", "length",
              "valid", "valid_lenient", "parse_ok", "n_waypoints", "n_targets", "seconds", "error"]


def log(message):
    print(f"[{time.strftime('%H:%M:%S')}] {message}", flush=True)


def parse_ids(specs):
    """'1:0' -> (1, 0); '1:*' -> (1, None), i.e. every start/goal pair of map 1."""
    ids = []
    for spec in specs or []:
        map_id, sg_idx = spec.split(":")
        ids.append((int(map_id), None if sg_idx == "*" else int(sg_idx)))
    return ids


def matches(ids, query):
    return any(m == query["map_id"] and s in (None, query["sg_idx"]) for m, s in ids)


def build_generator(args):
    from llmastar.model import ChatGPT
    client = ChatGPT(model=args.model, base_url=args.base_url, temperature=args.temperature,
                     max_tokens=args.max_tokens, cache_dir=args.cache_dir)
    return REGISTRY[args.generator](client, args)


def generate_waypoints(generator, queries, workers):
    """Call the generator for every query concurrently (vLLM batches them). An error aborts the run; finished
    responses are already cached, so rerunning resumes where it stopped."""
    results = [None] * len(queries)
    start, cached = time.time(), 0
    pool = ThreadPoolExecutor(max_workers=workers)
    try:
        futures = {pool.submit(generator.generate, query): i for i, query in enumerate(queries)}
        for done, future in enumerate(as_completed(futures), 1):
            result = results[futures[future]] = future.result()
            cached += bool(result.raw.get("cached"))
            if done % 50 == 0 or done == len(queries):
                log(f"[llm] {done}/{len(queries)} ({cached} from cache) {time.time() - start:.0f}s")
    except BaseException:
        pool.shutdown(wait=False, cancel_futures=True)
        raise
    pool.shutdown()
    return results


def search_one(job):
    """Run one query (in a worker process). job = (method, options, query, waypoints, plot_path)."""
    method, options, query, waypoints, plot_path = job
    start = time.time()
    try:
        if method == "astar":
            result = AStar().searching(query, filepath=plot_path)
        elif method == "dwastar":
            result = DWAStar(**options).searching(query, filepath=plot_path)
        elif method == "llmastar":
            result = LLMAStar().searching(query, filepath=plot_path, waypoints=waypoints)
        else:
            result = evaluate_llm_path(query, waypoints)
        result["error"] = ""
    except Exception as e:  # keep the run going; the row records the failure
        result = {"operation": None, "storage": None, "length": None, "valid": False,
                  "path": [], "visited": [], "error": repr(e)}
    result["seconds"] = round(time.time() - start, 3)
    return result


def run_searches(jobs, n_procs):
    if n_procs > 1:
        with ProcessPoolExecutor(n_procs) as pool:
            yield from pool.map(search_one, jobs, chunksize=4)
    else:
        yield from map(search_one, jobs)


def _blank(value, digits=None):
    if value is None:
        return ""
    return round(value, digits) if digits is not None else value


def _points(points):
    return [list(p) for p in points]


def parse_args(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--method", required=True, choices=METHODS)
    p.add_argument("--prompt", default="standard", choices=("standard", "cot", "repe"))
    p.add_argument("--prompt-set", default="llama", choices=("llama", "gpt"),
                   help="llama: the paper's Llama-3 few-shot dialogue as chat turns; gpt: its GPT completion prompt")
    p.add_argument("--generator", default="prompt", choices=sorted(REGISTRY), help="waypoint generator")
    p.add_argument("--model", default="llama-3-8b-instruct", help="served model name; also names outputs/<model>/")
    p.add_argument("--base-url", default=os.environ.get("OPENAI_BASE_URL", "http://127.0.0.1:8000/v1"))
    p.add_argument("--temperature", type=float, default=0.0)
    p.add_argument("--max-tokens", type=int, default=2048)
    p.add_argument("--limit", type=int, help="only the first N queries (dataset order: map 0 sg 0..9, map 1 ...)")
    p.add_argument("--queries", nargs="+", metavar="MAP:SG", help="only these queries, e.g. 1:0 or 1:* (whole map)")
    p.add_argument("--trace", nargs="*", default=["1:*"], metavar="MAP:SG",
                   help="save path + visited states for these queries, used by the figures (default: map 1)")
    p.add_argument("--plot", action="store_true", help="also save a PNG per query under outputs/<model>/plots/")
    p.add_argument("--workers", type=int, default=16, help="concurrent LLM requests")
    p.add_argument("--jobs", type=int, default=4, help="search worker processes")
    p.add_argument("--dwa-w0", type=float, default=2.0, help="Dynamic WA* initial weight")
    p.add_argument("--dwa-decay", type=float, default=0.99, help="Dynamic WA* weight decay")
    p.add_argument("--dwa-schedule", default="pop", choices=("pop", "depth"), help="Dynamic WA* decay schedule")
    p.add_argument("--dwa-rekey", action=argparse.BooleanOptionalAction, default=True,
                   help="Dynamic WA*: recompute OPEN priorities whenever the weight changes (pop schedule only); "
                        "--no-dwa-rekey fixes each priority at push time")
    p.add_argument("--dwa-min-weight", type=float, default=1.0,
                   help="Dynamic WA*: lower bound of the weight (0 lets it decay below 1)")
    p.add_argument("--dataset", default=str(DEFAULT_DATASET))
    p.add_argument("--out", default=str(OUTPUTS_ROOT), help="outputs root")
    p.add_argument("--cache-dir", default=".cache/llm")
    return p.parse_args(argv)


def dwa_variant(args):
    """Run-name suffix for non-default Dynamic WA* settings, e.g. dwastar-depth, dwastar-fixed-min0."""
    parts = [] if args.dwa_schedule == "pop" else [args.dwa_schedule]
    if args.dwa_schedule == "pop" and not args.dwa_rekey:
        parts.append("fixed")
    if args.dwa_min_weight != 1.0:
        parts.append(f"min{args.dwa_min_weight:g}")
    if args.dwa_w0 != 2.0:
        parts.append(f"w{args.dwa_w0:g}")
    if args.dwa_decay != 0.99:
        parts.append(f"decay{args.dwa_decay:g}")
    return "-".join(parts) or None


def main(argv=None):
    args = parse_args(argv)
    selected = parse_ids(args.queries)
    queries = [q for q in load_queries(args.dataset) if not selected or matches(selected, q)][:args.limit]
    is_llm = args.method in LLM_METHODS
    tag = (args.prompt if args.generator == "prompt" else args.generator) if is_llm else None
    variant = dwa_variant(args) if args.method == "dwastar" else None
    run = run_name(args.method, tag, variant)
    paths = RunPaths(args.model, run, args.out)
    paths.dir.mkdir(parents=True, exist_ok=True)
    log(f"{run}: {len(queries)} queries -> {paths.csv}")

    generated = [None] * len(queries)
    if is_llm:
        generated = generate_waypoints(build_generator(args), queries, args.workers)
        paths.raw.parent.mkdir(parents=True, exist_ok=True)
        with open(paths.raw, "w", encoding="utf-8") as f:
            for query, result in zip(queries, generated):
                record = {"map_id": query["map_id"], "sg_idx": query["sg_idx"], "model": args.model,
                          "base_url": args.base_url, **result.raw}
                f.write(json.dumps(record, ensure_ascii=False) + "\n")

    options = {"w0": args.dwa_w0, "decay": args.dwa_decay, "schedule": args.dwa_schedule,
               "rekey": args.dwa_rekey, "min_weight": args.dwa_min_weight} if args.method == "dwastar" else {}
    if args.plot:
        paths.plots.mkdir(parents=True, exist_ok=True)
    jobs = [(args.method, options, query, gen.waypoints if gen else None,
             str(paths.plot(query["map_id"], query["sg_idx"])) if args.plot else None)
            for query, gen in zip(queries, generated)]

    traced = parse_ids(args.trace)
    rows, start = [], time.time()
    for i, (query, gen, result) in enumerate(zip(queries, generated, run_searches(jobs, args.jobs)), 1):
        rows.append({
            "map_id": query["map_id"], "sg_idx": query["sg_idx"],
            "start": json.dumps(query["start"]), "goal": json.dumps(query["goal"]),
            "method": args.method, "prompt": tag or "", "model": args.model if is_llm else "",
            "operation": _blank(result["operation"]), "storage": _blank(result["storage"]),
            "length": _blank(result["length"], 6), "valid": int(result["valid"]),
            "valid_lenient": int(result["valid_lenient"]) if "valid_lenient" in result else "",
            "parse_ok": int(gen.parse_ok) if gen else "", "n_waypoints": len(gen.waypoints) if gen else "",
            "n_targets": len(result["llm_output"]) if "llm_output" in result else "",
            "seconds": result["seconds"], "error": result["error"],
        })
        if matches(traced, query):
            paths.traces.mkdir(parents=True, exist_ok=True)
            trace = {
                "run": run, "method": args.method, "prompt": tag, "model": args.model if is_llm else None,
                "map_id": query["map_id"], "sg_idx": query["sg_idx"], "query": {k: query[k] for k in QUERY_KEYS},
                "operation": result["operation"], "storage": result["storage"], "length": result["length"],
                "valid": result["valid"], "path": _points(result["path"]), "visited": _points(result["visited"]),
                "waypoints": _points(gen.waypoints) if gen else [], "targets": _points(result.get("llm_output", [])),
            }
            with open(paths.trace(query["map_id"], query["sg_idx"]), "w") as f:
                json.dump(trace, f)
        if i % 100 == 0 or i == len(queries):
            log(f"[search] {i}/{len(queries)} {time.time() - start:.0f}s")

    with open(paths.csv, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    from llmastar.summary import summarize_file
    stats = summarize_file(paths.csv, paths.dir / "astar.csv")
    errors = sum(1 for r in rows if r["error"])
    log(f"wrote {paths.csv}: n={stats['n']} valid={stats['valid']:.2f}% errors={errors} "
        + " ".join(f"{m}={stats[m]:.2f}" for m in ("operation", "storage", "length") if stats.get(m) is not None))


if __name__ == "__main__":
    main()
