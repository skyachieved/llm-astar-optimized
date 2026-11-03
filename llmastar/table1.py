"""Reproduce Table 1 with one command: A*, Dynamic WA*, then LLM-A* and LLM-only with the paper's three prompts,
then the summary table.

  python -m llmastar.table1 --model gpt-4o-mini --base-url https://api.openai.com/v1 --prompt-set gpt
  python -m llmastar.table1 --limit 50            # a quick pilot on the first 50 queries (local vLLM default)

Every LLM answer is cached (.cache/llm/), so the LLM-only runs reuse the LLM-A* answers and a rerun after a failure
only repeats the calls that failed. Results go to <out>/<model>/ and <out>/<model>/summary.md.
"""
import argparse
import os

from llmastar import run, summary

PROMPTS = ("standard", "cot", "repe")


def parse_args(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--model", default="llama-3-8b-instruct")
    p.add_argument("--base-url", default=os.environ.get("OPENAI_BASE_URL", "http://127.0.0.1:8000/v1"))
    p.add_argument("--api-key", default=None)
    p.add_argument("--prompt-set", default="llama", choices=("llama", "gpt"))
    p.add_argument("--generator", default="prompt")
    p.add_argument("--max-tokens", type=int, default=2048)
    p.add_argument("--stop-newline", action="store_true")
    p.add_argument("--limit", type=int)
    p.add_argument("--dataset")
    p.add_argument("--out", default=str(run.OUTPUTS_ROOT))
    p.add_argument("--cache-dir", default=".cache/llm")
    p.add_argument("--jobs", type=int, default=4)
    p.add_argument("--workers", type=int, default=16)
    return p.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    common = ["--model", args.model, "--out", args.out, "--jobs", str(args.jobs)]
    if args.limit:
        common += ["--limit", str(args.limit)]
    if args.dataset:
        common += ["--dataset", args.dataset]
    llm = ["--base-url", args.base_url, "--prompt-set", args.prompt_set, "--generator", args.generator,
           "--max-tokens", str(args.max_tokens), "--workers", str(args.workers), "--cache-dir", args.cache_dir]
    if args.api_key:
        llm += ["--api-key", args.api_key]
    if args.stop_newline:
        llm += ["--stop-newline"]

    run.main(["--method", "astar", *common])
    run.main(["--method", "dwastar", *common])
    for prompt in PROMPTS:
        run.main(["--method", "llmastar", "--prompt", prompt, *common, *llm])
        run.main(["--method", "llm_only", "--prompt", prompt, *common, *llm])
    summary.main(["--model", args.model, "--out", args.out])


if __name__ == "__main__":
    main()
