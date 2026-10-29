# agent.md — project memory for LLM-A* / Clear Democratic A*

## Goal
Implement and evaluate Clear Democratic A* (CDA*), a waypoint generator for LLM-A* (arXiv 2407.02511, Table 1
reproduced in this repo). Three map views vote on waypoints, waypoints are pruned by majority objection, and a stall
fallback bounds bad plans. The LLM-A* search loop stays unchanged; CDA* is compared against LLM-A* and weighted A*.

## Research rationale
Thesis: LLM-A*'s gain is mostly heuristic inflation (no waypoints = weighted A*, w=2: 34.3% ops vs. the paper's 44.6–57.4%). Real LLM value needs voters with independent errors; a fallback bounds the damage when they aren't.

| Weakness diagnosed | Component | Source | Flag |
|---|---|---|---|
| One LLM guess can mislead the search | Majority add (≥2 of 3) | Self-consistency (Wang et al. 2023) | --add-quorum |
| Same-model voters share mistakes | One view per voter (text/corners/image) | Talk like a Graph (Fatemi et al. 2024); ensemble diversity (Krogh & Vedelsby 1995) | --views |
| Single, delete-only vision judge (MMP-A*) | Majority remove (code/vision/support) | MMP-A* (2026), extended | --remove-quorum, --no-vision |
| Bad plans blow up the worst case | Stall fallback to weighted A* | Weighted A* (Pohl 1970) | --stall-k (0 = off) |
| Float/never-hit waypoints drag the search | Snap + canonicalize to corner nodes | Own diagnosis | --no-snap |

Rules that follow:
- The shared search loop is the baseline: never change it. Every new behavior lives in the waypoint-generation step or behind a flag.
- Every component must be switchable off independently, and "all off" (text view only, one call, no voting, no pruning, no snap, no fallback) must reproduce LLM-A* exactly.
- Always report against weighted A* (w = 1.5, 2, 3), not only LLM-A*.
- Log per query: each view's raw output, votes, removals, fallback fired, calls, tokens, latency.

> Note (2026-10-29): the 34.3% above comes from an external simulation, not from this repo. It must not appear in
> METHOD.md or the README until the `wastar` runs exist; then cite those files (Decisions).

## Constraints
**Session protocol (every session, no exceptions)**
1. Start: read this file fully, then REPRODUCTION.md and METHOD.md. Ask the user to run `! git log --oneline -20`
   (the `!` prefix puts the output in the chat). Summarize the state in 5 lines, then wait for OK.
2. Work on exactly one Next-steps item at a time. Never start an item marked done or blocked.
3. At the end of every step (not just the session), update this file, then give a one-line commit message.
4. If this file and the code disagree, the code wins: fix this file and note it in the Log.

**Working with the user**
- Claude only reads and edits files; the user runs every command. For each step, give exact copy-pasteable
  commands, the conda env (`llmastar` for the project, `vllm` for the model server) and what to report back. Then wait.
- The user cannot reliably copy terminal output. Prefer `! <cmd>` for short checks. Give long or multi-line commands
  as a script in `scripts/` (git-ignored, local only) that has an env guard and writes `logs/<name>.log` (git-ignored).
  Claude then reads `logs/` and `outputs/` directly.
- Shared GPU server: everything lives under /home/minho, and the user reserves the GPU and sets `$CUDA_VISIBLE_DEVICES`.
  The local LLM is vLLM's OpenAI-compatible server (`scripts/serve_local.sh`). The same client must work with
  GPT-4o mini by changing only `--model` / `--base-url`.

**Grader environment**: Ubuntu 22.04, Python 3.11, only `pip install -r requirements.txt`, no GPU, no API keys provided.
The key comes from `OPENAI_API_KEY` (optional `--api-key`). Never crash on LLM failures.

**Never do**
- Tune or pick defaults on the evaluation maps (`dataset/environment_50_30.json`) or on the held-out harder split.
  Few-shot examples come only from self-generated maps.
- Change the shared LLM-A* search loop or its f-value. New behavior goes in waypoint generation or behind a flag
  whose off state is identical to the baseline. The one allowed change is the no-op `_after_pop` hook (METHOD.md §7).
- Change metric definitions: operation = heap pops including duplicates (`len(CLOSED)`), storage = `len(g)`,
  length = sum of Euclidean steps.
- Break `LLMAStar(...).searching(query=...)` or its result keys (`operation, storage, length, valid, path, visited,
  llm_output`).
- Break `tests/test_astar.py::test_astar_matches_paper_figure1` (A* on map 1 / start_goal[0] = 859 / 802 / 53.46).
- Commit secrets, tokens, API keys or personal data; reference `scripts/` from tracked files; describe the project
  as making A* "cheaper". The framing is: better waypoints lead to more efficient search, at the cost of more LLM calls.

**Engineering / research**: small reviewable diffs, one logical change per commit, on a feature branch (main is the
only long-lived branch). State the hypothesis before each experiment, report negative results honestly, and cite
sources in METHOD.md and docstrings.

## Current status
- Phase: CDA*. The LLM-A* reproduction (Table 1 + Figs. 1–3) is done (commits 823a892, a536281 on main).
- Last completed: Step 1 (agent.md, METHOD.md with the spec, defaults, citations and module layout), 2026-10-29.
  Committed directly to main on 2026-10-30, together with the user's pending README.md change.
- Waiting on the user: run `scripts/get_qwen_vl.sh` (checks Qwen2.5-VL support in vLLM 0.11.0, then downloads the
  model), then serve it with `scripts/serve_local.sh qwen2.5-vl`.
- Next: Step 2.

## Next steps
- [x] 1. Read the repo and REPRODUCTION.md; write agent.md (with the Table 1 results and their paths) and METHOD.md
      (pseudocode, all defaults, citations). Propose the module layout. *(2026-10-29; layout = METHOD.md §10)*
- [ ] 2. Shared infrastructure: views, canonicalization, voting, pruning, safety net, each with pytest unit tests using
      a mock LLM (no network), including a test that "all off" reproduces LLM-A* exactly. Add a GitHub Actions
      workflow that runs pytest on Python 3.11 with only `pip install -r requirements.txt`, mirroring the grader.
      Sub-items, one commit each:
  - [ ] a. `_after_pop` no-op hook + `CDAStar` stall fallback; test: identical operation/storage/length with
        `stall_k=0` on a fixed set of maps (METHOD.md §7).
  - [ ] b. `--method wastar --weight W` (= `DWAStar(w0=W, decay=1)`); test: w = 1 equals A*.
  - [ ] c. Client: `api_key`, image message parts (cache stores an image hash), JSON mode with fallback, LLM errors
        logged and never raised to the runner.
  - [ ] d. `llmastar/cdastar/` modules (METHOD.md §10), each with mock-LLM tests, including the §6 "all off" test
        (same messages and cache key as `PromptWaypointGenerator`, same search results as `LLMAStar`).
  - [ ] e. CI: pin `.github/workflows/test.yml` (exists, `ubuntu-latest`) to `ubuntu-22.04`.
- [ ] 3. CDA* end-to-end behind the runner: `python -m llmastar.run --method cdastar ...`.
  - [ ] Baselines on qwen2.5-vl-7b-instruct, all 1,000 maps: astar, wastar w = 1.5 / 2 / 3, llmastar standard / cot /
        repe. Also wastar ×3 under `outputs/llama-3-8b-instruct/`. Record the files in Results.
  - [ ] All-off end-to-end check: 0 new LLM requests, metrics equal to `llmastar_standard.csv`.
- [ ] 4. Pilot (50 maps, local model). Hypotheses and measurements: (i) each view's solo waypoint quality; (ii) how
      often views share the same wrong waypoint; (iii) vision check catch and false-alarm rates, ground truth =
      waypoints > 3 cells from the A* path's corners; (iv) CDA* vs. LLM-A* vs. weighted A* (w = 1.5, 2, 3). Write a
      go/no-go decision here and wait for the user's approval.
- [ ] 5. Full runs (1,000 maps) and ablations: each view alone vs. all three, add/remove quorums, vision on/off, snap
      on/off, safety net on/off, few-shot shared / per-view / none, CoT, roles.
- [ ] 6. Harder generated maps (mazes, more walls, 2–3× size; fixed seed; held-out split never used to pick defaults),
      and a second model for generalization.
- [ ] 7. Figures in outputs/figures/ (ops vs. path-length trade-off with the weighted-A* frontier; ablation bars;
      failure-case visualizations) and a cost table (calls, tokens, time per query).
- [ ] 8. Final checks: clean Python 3.11 install from requirements.txt, README quickstart, no secrets in the repo,
      METHOD.md matches the code.

## Decisions
- 2026-10-29 · LLM-A* consumes a waypoint list; generators plug in via `llmastar/waypoints/REGISTRY` · new methods
  never touch the search (REPRODUCTION.md, "Swappable waypoint step").
- 2026-10-29 · Decoding: temperature 0, `max_tokens` 2048, no stop sequence; every response cached in `.cache/llm/`,
  keyed by model, base URL, messages and sampling · reproducible reruns at no cost (REPRODUCTION.md deviation 2).
- 2026-10-29 · The Dynamic WA* row is the `dwastar` reading (w = max(1, 2·0.99^pops), OPEN re-keyed) · within
  1.5 points of the paper (REPRODUCTION.md deviation 4).
- 2026-10-29 · `scripts/` is git-ignored and local only. Figure code lives in `llmastar/figures/`
  (`python -m llmastar.figures`), not `scripts/figures/` as the CDA* brief says · the user wants no helper scripts online.
- 2026-10-29 · main is the only branch on origin. CDA* work goes on the feature branch `cdastar`, one commit per step
  or sub-step · small reviewable diffs. 2026-10-30: the step 1 docs went directly to main (user's choice; docs only).
  Create `cdastar` from main when step 2 starts.
- 2026-10-29 · (Q1) The rationale's 34.3% (weighted A*, w = 2) comes from an external simulation. Add `wastar` runs
  (w = 1.5, 2, 3, all 1,000 maps) under `outputs/` and cite those files; the number is not used in METHOD.md or the
  README until then · user decision.
- 2026-10-29 · (Q2) `--fewshot paper` makes the text view send LLM-A*'s exact messages (no JSON mode) and pass its
  parsed waypoints through unchanged. "All off" = `--views text --fewshot paper --add-quorum 1 --no-vision --no-snap
  --stall-k 0`. A test shows identical searches to `LLMAStar`, reusing the cached answers · user decision; METHOD.md §6.
- 2026-10-29 · (Q3) One no-op hook, `_after_pop(s)`, in `LLMAStar.searching` right after a pop. `CDAStar` uses it for
  the stall fallback. Test: identical operation/storage/length with `--stall-k 0` on a fixed set of maps · user
  decision; METHOD.md §7.
- 2026-10-29 · (Q4) One VLM, Qwen2.5-VL-7B-Instruct (bf16, served name `qwen2.5-vl-7b-instruct`), for all three views,
  the vision judge and the LLM-A* baseline rerun. Llama-3-8B is for the Table 1 reproduction only, and GPT-4o mini
  comes later as the grading model. vLLM 0.11.0's supported-models page lists `Qwen2_5_VLForConditionalGeneration`
  (T + I + V, V1 ✅); `scripts/get_qwen_vl.sh` checks the installed version too · user decision.
- 2026-10-29 · (Q5) MMP-A* = Ha, Ta, Phan, Doan, Dao, Tran, Binh, "MMP-A*: Multimodal Perception Enhanced Incremental
  Heuristic Search on Path Planning", arXiv:2601.01910 (v2, 22 Jan 2026), code github.com/langkhachhoha/MMP-ASTAR.
  Checked against arxiv.org/html/2601.01910v2: a single VLM judge, prompted once per map, keeps or discards numbered
  waypoints and never adds any; the waypoint heuristic term decays by α^k (α = 0.7). Qwen2.5-VL is among its VLMs.
- 2026-10-29 · Weighted A* is `DWAStar(w0=w, decay=1)` (constant weight), not a new search · no new search code.
- 2026-10-29 · Canonical waypoint id = its (snapped) cell, so coordinate and node-id views vote directly · METHOD.md §4.3.

## Conventions
- `CLAUDE.md` contains only `@agent.md`, so every session loads this file. METHOD.md is the CDA* spec; keep it in
  sync with the code.
- Layout: `llmastar/run.py` (one method over the benchmark), `summary.py` (Table 1 format), `scale.py` (Fig. 3),
  `figures/` (figures from `outputs/` only), `pather/` (A*, DWA*, LLM-A*: search only, no LLM code), `waypoints/`
  (`base.py`: `WaypointGenerator` protocol, `WaypointResult(waypoints, parse_ok, raw)`, `parse_waypoints`;
  `prompting.py`: the paper's prompts), `model/` (`ChatGPT` OpenAI-compatible client + `cache.py`), `benchmark.py`
  (`load_queries`, `evaluate_llm_path`, `segment_collides`), `outputs.py` (paths).
  `dataset/environment_50_30.json`: 100 maps × 10 queries, 51 × 31 grid. CDA* modules: METHOD.md §10 (planned).
- Generators must be thread-safe (`generate(query)` is called from many threads).
- Waypoint filter applied by the search: `LLMAStar._filter_valid_nodes` (not an obstacle, 2 ≤ x ≤ 48, 2 ≤ y ≤ 28 on
  the benchmark grid). If no waypoint survives, the target is the goal and h = 2 × distance to goal (weighted A*, w = 2).
- Outputs: `outputs/<model>/<run>.csv`, `raw/<run>.jsonl` (git-ignored), `traces/<run>/<map>_<sg>.json`,
  `summary.md`, `summary.csv`, `scalability.csv`; `outputs/figures/`; `.cache/llm/` and `logs/` are git-ignored.
  `<model>` = served name: `llama-3-8b-instruct` (Table 1), `qwen2.5-vl-7b-instruct` (CDA*).
- Run name: `<method>[_<tag>][-<variant>]`; tag = prompt name for generator `prompt`, else the generator name.
  Planned: `wastar-w1.5|w2|w3`, `cdastar[-<non-default flags>]`.
- CSV columns: `map_id, sg_idx, start, goal, method, prompt, model, operation, storage, length, valid, valid_lenient,
  parse_ok, n_waypoints, n_targets, seconds, error` (CDA* adds the METHOD.md §8 columns).
- Table ratios: geometric mean over queries of (run / A*) × 100, on queries where both are valid.
  `no_targets` = % of queries with `n_targets == 2`.
- Tests: `pytest -q tests` (env `llmastar`). CI: `.github/workflows/test.yml` (ubuntu-latest, Python 3.11,
  `pip install -r requirements.txt`, `pytest -q tests`) on pushes and PRs to main.
- Local scripts (git-ignored): `scripts/serve_local.sh [llama3|qwen2.5-vl|DIR] [name]` (log
  `logs/vllm_<name>.log`), `scripts/get_qwen_vl.sh` (log `logs/get_qwen_vl.log`), `scripts/setup_vllm_env.sh`.

## How to run
Envs: `llmastar` (Python 3.11, `pip install -r requirements.txt`, no torch) and `vllm` (Python 3.11,
`vllm==0.11.0`, `transformers>=4.56,<5`). Models: `~/models/Meta-Llama-3-8B-Instruct`, `~/models/Qwen2.5-VL-7B-Instruct`.
```bash
# model (env vllm): check support + download once, then serve in its own terminal (GPU=0 is the default)
bash scripts/get_qwen_vl.sh
bash scripts/serve_local.sh qwen2.5-vl        # or: bash scripts/serve_local.sh llama3  (Table 1 model)
# public equivalent of serve_local.sh (README)
CUDA_VISIBLE_DEVICES=0 vllm serve ~/models/Meta-Llama-3-8B-Instruct \
  --served-model-name llama-3-8b-instruct --host 127.0.0.1 --port 8000 \
  --dtype bfloat16 --max-model-len 8192 --gpu-memory-utilization 0.90 \
  --generation-config vllm --seed 0
# experiments (env llmastar)
export OPENAI_API_KEY=dummy
python -m llmastar.run --method astar --jobs 8
python -m llmastar.run --method dwastar --jobs 8
python -m llmastar.run --method llmastar --prompt standard --jobs 8 --workers 32   # also cot, repe; --limit 50 for a pilot
python -m llmastar.run --method llm_only --prompt standard --jobs 8 --workers 32
python -m llmastar.scale --jobs 8
python -m llmastar.summary && python -m llmastar.figures
pytest -q tests
```
Add `--model qwen2.5-vl-7b-instruct` to any run to use (and write outputs for) the Qwen server.

## Results
- 2026-10-29 · Table 1 reproduction · llama-3-8b-instruct (vLLM bf16, greedy) · all 1,000 queries ·
  `outputs/llama-3-8b-instruct/summary.md` (per-run CSVs next to it). Ops / storage / length / valid, ×100 vs. A*
  (paper in brackets):
  - dwastar: 59.49 / 78.65 / 100.25 / 100 (60.91 / 78.53 / 100.24 / 100)
  - llmastar_standard: 42.99 / 62.83 / 102.27 / 100 (44.59 / 64.02 / 102.47 / 100); no_targets 25.40%
  - llmastar_cot: 49.63 / 68.06 / 102.45 / 100 (47.60 / 66.27 / 102.46 / 100); no_targets 9.60%
  - llmastar_repe: 69.70 / 84.31 / 102.42 / 100 (64.08 / 80.19 / 102.54 / 100); no_targets 7.10%
  - llm_only standard / cot / repe: length 110.91 / 118.53 / 169.01, valid 10.70 / 9.70 / 9.80%
    (paper 111.05 / 114.89 / 138.32, valid 12.60 / 12.00 / 16.40%)
- 2026-10-29 · Other DWA* readings · same file: dwastar-fixed 33.66 / 61.15 / 105.66; dwastar-depth
  33.20 / 55.49 / 102.55; dwastar-min0 105.02 / 141.40 / 100.25; dwastar-fixed-min0 46.49 / 82.29 / 108.19.
- 2026-10-29 · Figs. 1–3 · `outputs/figures/`; numbers in REPRODUCTION.md ("Figures").
- Weighted A* (w = 1.5, 2, 3): **not run yet** (step 3).

## Open questions
1. [answered 2026-10-29] Source of the rationale's 34.3% → external simulation; see Decisions (Q1).
2. [answered 2026-10-29] Exact LLM-A* reproduction → `--fewshot paper`; see Decisions (Q2).
3. [answered 2026-10-29] Fallback inside the search → one no-op hook; see Decisions (Q3).
4. [answered 2026-10-29] Model for the image view and the vision judge → Qwen2.5-VL-7B-Instruct; see Decisions (Q4).
5. [answered 2026-10-29] MMP-A* reference → arXiv:2601.01910; see Decisions (Q5).

## Log
- 2026-10-30 · The user committed step 1 (agent.md, METHOD.md, CLAUDE.md, README.md) to main and pushed it.
  Implementation starts another day at step 2a. `scripts/git_push.sh` now pushes the current branch.
- 2026-10-29 · CDA* kickoff session. Created agent.md. Fixed against the code: figure code is in `llmastar/figures/`
  (`scripts/` is git-ignored), and a CI workflow already exists (`ubuntu-latest`). Recorded the user's answers to Q1–Q5;
  verified MMP-A* on arXiv and Qwen2.5-VL in vLLM 0.11.0's docs. `serve_local.sh` now takes the model as an argument
  and adds the vision settings automatically; added `get_qwen_vl.sh`. Wrote METHOD.md, which completes step 1.
- 2026-10-29 · Earlier sessions: reproduced LLM-A* Table 1 and Figs. 1–3 with Llama-3-8B-Instruct on vLLM
  (main 823a892, docs a536281).
