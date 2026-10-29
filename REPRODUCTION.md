# Reproducing LLM-A* (arXiv 2407.02511) with Llama-3-8B-Instruct

Target: Table 1 (A*, Dynamic WA*, and the LLAMA3 rows for LLM-only and LLM-A*) and the reproducible figures,
using Llama-3-8B-Instruct in bf16 served locally by vLLM on one RTX A5000 (24 GB).

## Setup

The commands to install everything, start the model server and run every experiment are in
[README.md](README.md#setup). Our run used:

| Env | Python | Packages |
|---|---|---|
| `vllm` | 3.11 | vLLM 0.11.0, torch 2.8.0+cu128, transformers 4.57.6 (NVIDIA driver 580). vLLM 0.11.0 does not cap transformers, and with transformers 5 it dies at startup (`TokenizersBackend has no attribute all_special_tokens_extended`), so the install pins `transformers<5`. |
| `llmastar` | 3.11 | `pip install -r requirements.txt` (no torch or vLLM) |

The server ran on one RTX A5000 (24 GB) in bf16, with an 8,192-token context and 90% of GPU memory (about 5 GiB of KV
cache, prefix caching on). It was bound to 127.0.0.1, with `--generation-config vllm` and seed 0.

Single runs: `python -m llmastar.run --method {astar,dwastar,llm_only,llmastar} [--prompt standard|cot|repe] [--limit N] [--queries MAP:SG ...]`.
The API key comes from `OPENAI_API_KEY` (any value for vLLM). The endpoint comes from `--base-url` or `OPENAI_BASE_URL`
(default `http://127.0.0.1:8000/v1`).
Every LLM response is cached in `.cache/llm/`, keyed by model, base URL, messages and sampling settings.
Reruns, and the LLM-only runs that reuse the LLM-A* prompts, therefore make no new requests.

## What this reproduction changed, and why

Everything the runs produce is in `outputs/`; nothing is written into the original repository's folders. `logs/` and `.cache/` are local only (git-ignored). `git diff 9414ed8` shows every change against the original repository; 9414ed8 is its last commit.

The original repository has only single-query searches. It has no runner over the 1,000 queries, no Table 1 averages, no Dynamic WA*, no LLM-only check, no scaling experiment and no figure code, so most of the changes fill those gaps. Paths below are under `llmastar/` unless shown otherwise.

| Change | Files | Why |
|---|---|---|
| Llama-3-8B-Instruct through vLLM | `model/chatgpt.py`, `model/__init__.py`, `pather/llm_a_star/prompt.py`, `requirements.txt` | The old client used the 2023 OpenAI library; the new one talks to any OpenAI-compatible server, here vLLM. The paper's Llama 3 prompt is sent as chat messages with the same content. The package no longer loads torch on import, so the experiment env needs none. |
| Experiment code | `run.py`, `benchmark.py`, `summary.py`, `scale.py`, `outputs.py`, `figures/` | The authors did not publish theirs. These run a method over all queries, compute the Table 1 averages, run the Fig. 3 scaling experiment and draw Figs. 1–3. |
| Dynamic WA* | `pather/dw_a_star/` | Table 1 has a Dynamic WA* row, but the original code has no implementation. The paper does not say which reading it used, so we ran five and kept the one that matches (deviation 4). |
| Fixes to the original searches | `pather/a_star/a_star.py`, `pather/llm_a_star/llm_a_star.py`, `env/search/plotting.py` | Every search opened a plot window, which blocks on a server without a display. LLM-A* crashed when an answer had no list. Searches also changed the caller's query. The metrics are unchanged: `tests/test_astar.py` checks the paper's 859 / 802 / 53.46. |
| Swappable waypoint step | `waypoints/`, `pather/llm_a_star/llm_a_star.py` | LLM-A* now takes a list of waypoints instead of calling the LLM itself, so a new waypoint method can replace the prompt without touching the search. It also lets all LLM calls run in parallel before the searches. |
| Extras, not needed for the results | `model/cache.py`, `tests/test_astar.py`, `.github/workflows/test.yml`, `model/llama3.py`, `pather/a_star/a_star.py` | The cache stores every LLM answer, so reruns cost nothing. The tests and CI (now Python 3.11 with pytest) check the metrics. `llama3.py` no longer hardcodes GPU `cuda:3`. A* keeps a set of closed states for faster lookups, with the same result. |
| Docs | `README.md`, `REPRODUCTION.md`, `.gitignore` | README rewritten for this repository; this file; the LLM cache, logs and raw LLM output are git-ignored. |

## Output layout

```
outputs/<model>/<run>.csv                 per-query metrics (run = astar, dwastar, llmastar_cot, llm_only_repe, ...)
outputs/<model>/raw/<run>.jsonl           raw LLM responses + parsed waypoints (git-ignored)
outputs/<model>/traces/<run>/<map>_<sg>.json   path and visited states for map 1 (used by the figures)
outputs/<model>/summary.md, summary.csv   the aggregated table, next to the paper's numbers
outputs/<model>/scalability.csv           Fig. 3 data
outputs/figures/                          figures (PNG + PDF), made by python -m llmastar.figures from outputs/ only
```

## Metrics (unchanged from the original code)

- **operation**: heap pops, including duplicate pops of the same state.
- **storage**: `len(g)`, i.e. every state whose cost was ever evaluated, including neighbors blocked by a barrier.
- **length**: the sum of Euclidean step lengths along the path.
- **Table ratios**: the geometric mean over queries of (method / A*) × 100. Only queries where both the method and A* found a valid path are used.
- **valid**: the percentage of queries with a valid path.

## Results

All 1,000 queries, from `outputs/llama-3-8b-instruct/summary.md`. LLM-only lengths use only the queries whose LLM path is valid (about 100 per prompt).

| Method | Prompt | Ops (ours / paper) | Storage (ours / paper) | Length (ours / paper) | Valid (ours / paper) |
|---|---|---|---|---|---|
| A* | - | 100 / 100 | 100 / 100 | 100 / 100 | 100 / 100 |
| Dynamic WA* | - | 59.49 / 60.91 | 78.65 / 78.53 | 100.25 / 100.24 | 100 / 100 |
| LLM-only | Few-shot | - | - | 110.91 / 111.05 | 10.70 / 12.60 |
| LLM-only | CoT | - | - | 118.53 / 114.89 | 9.70 / 12.00 |
| LLM-only | RePE | - | - | 169.01 / 138.32 | 9.80 / 16.40 |
| LLM-A* | Few-shot | 42.99 / 44.59 | 62.83 / 64.02 | 102.27 / 102.47 | 100 / 100 |
| LLM-A* | CoT | 49.63 / 47.60 | 68.06 / 66.27 | 102.45 / 102.46 | 100 / 100 |
| LLM-A* | RePE | 69.70 / 64.08 | 84.31 / 80.19 | 102.42 / 102.54 | 100 / 100 |

The paper's ordering holds: few-shot LLM-A* saves the most work, then CoT, then RePE; all three keep path length within 2.5% of optimal on average, and LLM-A* beats Dynamic WA* with few-shot and CoT prompts but not with RePE (as in the paper). The 3,000 LLM calls took about 8 minutes on one RTX A5000 (roughly 45 s few-shot, 110 s CoT, 340 s RePE).

## Figures

`python -m llmastar.figures` makes all three; each also runs on its own, e.g. `python -m llmastar.figures.fig1_search --query 1:3`.

| Paper figure | Module (`llmastar.figures.`) | Status |
|---|---|---|
| Fig. 1: A* vs LLM-A* on map 1 / query 0 | `fig1_search` | A* matches exactly (859 / 802 / 53.46). LLM-A* gives 183 / 292 / 56.77 against the paper's 140 / 235 / 53.46: both of Llama's waypoints for this query, (30, 20) and (20, 5), lie on barriers, so LLM-A* drops them (hollow stars) and searches with h = 2 × the distance to the goal (reason 4 below). |
| Fig. 2 (latest version): more A* vs LLM-A* examples | `fig2_examples` | Reproduced. Which queries the paper shows is unknown; ours (map 1, queries 1, 2, 4) were fixed before the run, not picked by result. Query 4 shows a waypoint leading LLM-A* the wrong way (426 operations against A*'s 133). |
| Fig. 3: growth factor vs. map scale | `fig3_scalability` | Reproduced with our reading of the unspecified scaling procedure (deviation 6). At 10×, A* does 107.8 times its 1× operations and LLM-A* 73.0 times; for storage the factors are 76.2 and 45.2. LLM-A* grows more slowly than A* at every scale from 2× on, as in the paper. The curves rest on 10 queries (reason 5 below). |
| Fig. 4: 11×11 Chebyshev-heuristic illustration | none | Not reproducible: hand-made map that is not in the repo, and it uses a different heuristic. |
| Table 1, GPT-3.5 rows | none | Not run (out of scope). The client works with any OpenAI-compatible endpoint (`--model`, `--base-url`). |

## Deviations and interpretations

1. **Prompt transport.** The paper fed hand-written Llama-3 templates (raw special tokens) to a Hugging Face pipeline. We send the same turns as chat messages to `/v1/chat/completions`, and vLLM applies the model's official chat template. The content is identical; only the whitespace around special tokens differs. The original string also began with `\n<|begin_of_text|>`, and the pipeline adds its own BOS, so the paper's runs likely saw a stray newline and a doubled BOS. Ours do not.
2. **Decoding.** The paper does not report decoding settings. We use greedy decoding (temperature 0, as the original `do_sample=False`) with `max_tokens=2048` (the original allowed 8000). There is no `stop="\n"`. The old GPT client used it, and it would truncate CoT / RePE answers. vLLM bf16 kernels are not bit-identical to the HF pipeline, so some responses can differ.
3. **Waypoint parsing.** We use the original rule: the last `[[x, y], ...]` list in the response; entries with more than two numbers keep their first two. When no list parses, LLM-A* gets no waypoints and searches start → goal; the CSV records this as `parse_ok=0`. The original code crashed in this case.
4. **Dynamic WA\*.** The paper gives only "initial weight of 2 and 0.99 decay", and the authors' repository has no implementation. All readings use f = g + w·h. We ran five of them on all 1,000 queries:

   ```bash
   python -m llmastar.run --method dwastar                                     # dwastar
   python -m llmastar.run --method dwastar --no-dwa-rekey                      # dwastar-fixed
   python -m llmastar.run --method dwastar --dwa-schedule depth                # dwastar-depth
   python -m llmastar.run --method dwastar --dwa-min-weight 0                  # dwastar-min0
   python -m llmastar.run --method dwastar --no-dwa-rekey --dwa-min-weight 0   # dwastar-fixed-min0
   ```

   | Run | Reading | Ops | Storage | Length |
   |---|---|---|---|---|
   | `dwastar` | w = max(1, 2·0.99^k), k = heap pops so far; every OPEN priority is recomputed when w changes | 59.49 | 78.65 | 100.25 |
   | `dwastar-fixed` | same weight, but a state's priority is fixed when it is pushed | 33.66 | 61.15 | 105.66 |
   | `dwastar-depth` | w = max(1, 2·0.99^d), d = the state's depth from the start (Pohl-style) | 33.20 | 55.49 | 102.55 |
   | `dwastar-min0` | as `dwastar`, but w keeps decaying below 1 | 105.02 | 141.40 | 100.25 |
   | `dwastar-fixed-min0` | as `dwastar-fixed`, but w keeps decaying below 1 | 46.49 | 82.29 | 108.19 |
   | paper | | 60.91 | 78.53 | 100.24 |

   `dwastar` is within 1.5 points of the paper on every metric, so it is the Table 1 row. Under it, w reaches 1 after 69 pops: the search is greedy for its first 69 expansions and plain A* afterwards, with the states it already closed staying closed. We picked this reading because it matches; w0 and decay are the paper's and nothing was tuned.
5. **LLM-only validity.** The paper does not define it precisely. `valid` requires the path to start at the start, end at the goal, and have no segment crossing a barrier or the map boundary (same collision rule as the search). `valid_lenient` first inserts a missing start / goal. Relative length is the polyline length, computed on queries where the path is valid.
6. **Scalability.** The paper says maps are enlarged 1–10× over 10 random samples, without the procedure. We multiply every coordinate (map size, barriers, start, goal) by k = 1, 2, …, 10 and sample 10 queries with seed 0, using the same queries at every scale. LLM-A* (few-shot) queries the LLM on the scaled map. The growth factor at scale k is the method's mean metric over the 10 queries at k divided by its mean over the same queries at 1×. Our first plot averaged per-query ratios instead. That average is dominated by queries LLM-A* solves in a few dozen operations at 1× (map 52 / query 3 takes 26 operations at 1× and 5,692 at 8×, a 219× growth), and it made the LLM-A* curve jump up and down.
7. **Code fixes that leave the metrics unchanged.** Searches deep-copy the query (the original decremented `range_x` / `range_y` in the caller's dict). The CLOSED membership test uses a set, which gives the same result faster. An exhausted OPEN list returns `valid=False` instead of raising. Plotting is opt-in (`--plot`) and works without a display.

## Likely reasons for differences

Few-shot and CoT LLM-A* land within 2 points of the paper on every metric, and Dynamic WA* within 1.5. The larger gaps are RePE LLM-A* (+5.6 operations, +4.1 storage) and the LLM-only rows. Every LLM number depends only on which waypoints the model returns, so differences in the model's answers are the main suspect.

1. **Different answers from the same model.** The paper does not report decoding settings, and it ran the model through a Hugging Face pipeline. We decode greedily on vLLM, whose bf16 kernels are not bit-identical to the pipeline's, and we send the prompt as chat turns instead of the paper's hand-built string (deviation 1). Each of these can change answers. RePE answers are the longest (about 400 tokens, against about 30 for few-shot), so they have the most room to diverge, which fits RePE being furthest from the paper.
2. **We had to define LLM-only validity.** The paper does not say how it checks an LLM-only path. Ours is strict: the polyline must start and end at the right points, and no segment may cross a barrier or the map boundary. Our valid rates (9.7–10.7%) are below the paper's (12.0–16.4%). Inserting a missing start or goal (`valid_lenient`) changes them by at most 0.4 points, so the gap comes from the collision rule or from the answers themselves.
3. **LLM-only lengths rest on few queries.** The length ratio uses only the ~100 queries whose LLM path is valid, so a handful of long detours moves it a lot. That is the likely reason RePE's is 169 against the paper's 138.
4. **LLM-A* falls back to weighted A\*.** LLM-A* drops any waypoint that lies on a barrier or next to the map edge. When it drops all of them, the only target left is the goal, and the heuristic dist(goal) + dist(target) becomes 2 × the distance to the goal: weighted A* with w = 2. This is how the original code works, not something we changed. It is what happened in Fig. 1, where the search found a path 6% longer than optimal. It happens on 25.4% of the few-shot queries, 9.6% of the CoT queries and 7.1% of the RePE queries (`no_targets` in `summary.md`), so about a quarter of the few-shot LLM-A* row is weighted A* without any guidance from the LLM.
5. **Fig. 3 rests on 10 queries.** Two of them (map 43 / query 0 and map 49 / query 7) account for most of the operations at large scales, so the means mostly follow them. On map 49 / query 7, LLM-A* does more work than A* at 10× (91,459 operations against 75,743). The paper does not list its 10 samples, and a different sample can move both curves.
