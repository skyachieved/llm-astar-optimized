"""Scalability experiment (paper Fig. 3): A* vs LLM-A* on maps enlarged 1x..10x.

  python -m llmastar.scale [--scales 1 2 4 6 8 10] [--samples 10] [--seed 0]     (default: every scale 1..10)

The paper does not say how maps are enlarged. We multiply every coordinate (map size, barriers, start, goal) by
the scale k, draw --samples queries once with a fixed seed, and run both methods on the same queries at every
scale; LLM-A* asks the LLM for waypoints on the scaled map. Rows are appended to outputs/<model>/scalability.csv
as they finish, and (scale, query, method) rows already there are skipped, so an interrupted run resumes.
"""
import argparse
import csv
import json
import os
import random
import time
from concurrent.futures import ProcessPoolExecutor, as_completed

from llmastar.benchmark import DEFAULT_DATASET, load_queries
from llmastar.outputs import OUTPUTS_ROOT, RunPaths
from llmastar.run import build_generator, generate_waypoints, log, search_one

FIELDS = ["scale", "map_id", "sg_idx", "method", "prompt", "operation", "storage", "length", "valid", "n_targets",
          "seconds", "error"]


def scale_query(query, k):
    scaled = dict(query)
    scaled["start"] = [c * k for c in query["start"]]
    scaled["goal"] = [c * k for c in query["goal"]]
    # Coordinates run 0..max with range [0, max + 1]; keep that convention.
    scaled["range_x"] = [query["range_x"][0] * k, (query["range_x"][1] - 1) * k + 1]
    scaled["range_y"] = [query["range_y"][0] * k, (query["range_y"][1] - 1) * k + 1]
    scaled["horizontal_barriers"] = [[v * k for v in b] for b in query["horizontal_barriers"]]
    scaled["vertical_barriers"] = [[v * k for v in b] for b in query["vertical_barriers"]]
    return scaled


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--scales", type=int, nargs="+", default=list(range(1, 11)))
    p.add_argument("--samples", type=int, default=10)
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--prompt", default="standard", choices=("standard", "cot", "repe"))
    p.add_argument("--prompt-set", default="llama", choices=("llama", "gpt"))
    p.add_argument("--generator", default="prompt")
    p.add_argument("--model", default="llama-3-8b-instruct")
    p.add_argument("--base-url", default=os.environ.get("OPENAI_BASE_URL", "http://127.0.0.1:8000/v1"))
    p.add_argument("--temperature", type=float, default=0.0)
    p.add_argument("--max-tokens", type=int, default=2048)
    p.add_argument("--workers", type=int, default=16, help="concurrent LLM requests")
    p.add_argument("--jobs", type=int, default=4, help="search worker processes")
    p.add_argument("--dataset", default=str(DEFAULT_DATASET))
    p.add_argument("--out", default=str(OUTPUTS_ROOT))
    p.add_argument("--cache-dir", default=".cache/llm")
    args = p.parse_args(argv)

    tag = args.prompt if args.generator == "prompt" else args.generator
    samples = random.Random(args.seed).sample(load_queries(args.dataset), args.samples)
    paths = RunPaths(args.model, f"scale_llmastar_{tag}", args.out)
    out_csv = paths.dir / "scalability.csv"
    paths.dir.mkdir(parents=True, exist_ok=True)

    done = set()
    if out_csv.exists():
        with open(out_csv, newline="") as f:
            done = {(int(r["scale"]), int(r["map_id"]), int(r["sg_idx"]), r["method"], r["prompt"]) for r in csv.DictReader(f)}

    def pending(k, q, method):
        return (k, q["map_id"], q["sg_idx"], method, tag if method == "llmastar" else "") not in done

    # Largest scales first, so the longest searches start early.
    todo = [(k, q, m) for k in sorted(args.scales, reverse=True) for q in samples for m in ("astar", "llmastar")
            if pending(k, q, m)]
    log(f"scalability: {len(todo)} searches pending -> {out_csv}")
    if not todo:
        return

    llm_items = [(k, q) for k, q, m in todo if m == "llmastar"]
    waypoints = {}
    if llm_items:
        generated = generate_waypoints(build_generator(args), [scale_query(q, k) for k, q in llm_items], args.workers)
        paths.raw.parent.mkdir(parents=True, exist_ok=True)
        with open(paths.raw, "a", encoding="utf-8") as f:
            for (k, q), result in zip(llm_items, generated):
                waypoints[(k, q["map_id"], q["sg_idx"])] = result.waypoints
                f.write(json.dumps({"scale": k, "map_id": q["map_id"], "sg_idx": q["sg_idx"], "model": args.model,
                                    **result.raw}, ensure_ascii=False) + "\n")

    new_file = not out_csv.exists()
    start = time.time()
    with open(out_csv, "a", newline="") as f, ProcessPoolExecutor(args.jobs) as pool:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        if new_file:
            writer.writeheader()
        futures = {}
        for k, q, method in todo:
            job = (method, {}, scale_query(q, k), waypoints.get((k, q["map_id"], q["sg_idx"])), None)
            futures[pool.submit(search_one, job)] = (k, q, method)
        for i, future in enumerate(as_completed(futures), 1):
            k, q, method = futures[future]
            result = future.result()
            writer.writerow({
                "scale": k, "map_id": q["map_id"], "sg_idx": q["sg_idx"], "method": method,
                "prompt": tag if method == "llmastar" else "", "operation": result["operation"],
                "storage": result["storage"], "length": result["length"], "valid": int(result["valid"]),
                "n_targets": len(result["llm_output"]) if "llm_output" in result else "",
                "seconds": result["seconds"], "error": result["error"],
            })
            f.flush()
            log(f"[search] {i}/{len(todo)} scale={k} map={q['map_id']}:{q['sg_idx']} {method} "
                f"ops={result['operation']} ({result['seconds']:.0f}s, total {time.time() - start:.0f}s)")


if __name__ == "__main__":
    main()
