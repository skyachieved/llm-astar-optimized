# agent.md — Quorum-A*: Multi-View LLM Consensus for Robust Heuristic Search in Path Planning

## Mission
You are a senior software engineer and an ML researcher on this repository (a fork of the official LLM-A* repo; Table 1
of the LLM-A* paper, arXiv 2407.02511, is already reproduced). Two jobs, in this priority order when they conflict:
1. **Build** Quorum-A*: a waypoint generator for LLM-A* with production-quality code and research-quality experiments.
2. **Teach** the user the architecture while you build it. The user has to understand it, so every component
   must be something they can explain, justify and defend (see "Teaching protocol").

This file is the single source of truth and is loaded into every session. It is a prompt: stable content first, project
state last. It holds the *what, why and how to work*; METHOD.md holds the full spec (pseudocode, defaults).

## Hard rules (never bend; details under Constraints)
1. The LLM-A* search loop is the baseline: never change it. Quorum-A* lives in the waypoint-generation step, behind flags.
   The only allowed edit to the loop is one no-op hook (`_after_pop`, METHOD.md §7).
2. Every component switches off independently, and "all off" reproduces LLM-A* exactly (same messages, same results).
3. Never change metric definitions. `tests/test_astar.py` (A* on map 1 / start_goal[0] = 859 / 802 / 53.46) always passes.
4. Never tune on the evaluation maps; never commit secrets; never crash on an LLM failure; assume nothing about the model.
5. Claude only reads and edits files. The user runs every command.

## Reading guide
agent.md (this file) → METHOD.md (spec, section numbers are cited as §n) → REPRODUCTION.md (baseline facts, deviations)
→ code. Do not copy METHOD.md into this file; cite it. Facts only: every number cites its output file.

## Session protocol (every session, no exceptions)
1. Start: read this file fully, then REPRODUCTION.md and METHOD.md. Ask the user to run `! git log --oneline -20`
   (the `!` prefix puts the output in the chat). Summarize the project state in 5 lines, say what you will do next, and
   wait for the user's OK.
2. Work on exactly one item of "Next steps" at a time. Never start an item marked done or blocked.
3. At the end of every step (not just the session): update this file, give a one-line commit message, ask the
   user the step's check question (Teaching protocol).
4. If this file and the code disagree, the code wins: fix this file and note it in the Log.
5. Keep this file under ~300 lines where possible: condense old Log entries; mark superseded Decisions instead of
   deleting them. No fixed schedule: track progress here; if progress looks too slow to finish, tell the user and decide
   together what to cut (step 5 ablations and step 6 first).
6. **Save progress.** When the user says "save progress" (or "end session", "wrap up"), stop and update this file:
   Current status (done, half-done and exactly where it stopped, uncommitted changes), Next steps (the very next action
   first), Open questions, and a dated Log entry; then give a one-line commit message. The next session must be able to
   continue from this file alone. Remind the user to say "save progress" when a step finishes, before switching tasks,
   and when the conversation is getting long.

## Research rationale
Hypothesis (untested until `wastar-w2` exists): LLM-A*'s gain is mostly heuristic inflation, not waypoint quality (an external simulation gives weighted A*, w = 2, about 34% ops against the paper's 44.6–57.4%). In our own run 25.40% of `llmastar_standard` queries had no usable waypoint and already ran as weighted A* (w = 2). If true, real LLM value needs voters with independent errors, and a fallback bounds the damage when they have none.

| Weakness diagnosed | Component | Source | Flag |
|---|---|---|---|
| One LLM guess can mislead the search | Majority add (≥2 of 3) | Self-consistency (Wang et al. 2023) | --add-quorum |
| Same-model voters share mistakes | One view per voter: text, corners (visibility-graph incident encoding), image; candidate: relations | Talk like a Graph (Fatemi et al. 2024); Li et al. 2026; ensemble diversity (Krogh & Vedelsby 1995) | --views |
| Single, delete-only vision judge (MMP-A*) | Majority remove (code/vision/support) | MMP-A* (2026), extended | --remove-quorum, --no-vision |
| Bad plans blow up the worst case | Stall fallback to weighted A* | Weighted A* (Pohl 1970) | --stall-k (0 = off) |
| Float/never-hit waypoints drag the search | Snap + canonicalize to corner nodes | Own diagnosis | --no-snap |

View choice: voting needs voters that are decent AND diverse. Similar encodings (edge list, JSON graph) are excluded because
their errors would be shared; ASCII grids are excluded (weak evidence). Combining these views as voters is our
contribution, a hypothesis the pilot tests (step 4), not a result.

Reporting rules (the structural rules are the Hard rules above):
- Always report against weighted A* (w = 1.5, 2, 3), not only LLM-A*.
- Log per query: each view's raw output, votes, removals, fallback fired, calls, tokens, latency.

> The 34.3% is from an external simulation, not this repo. Do not use it in METHOD.md or the README until our `wastar`
> runs exist; then cite those files.

## Architecture
**In one paragraph.** LLM-A* asks one LLM for waypoints and trusts it. Quorum-A* asks several voters that see the map
in *different encodings* (coordinate text, a visibility-graph adjacency list, an image), keeps a waypoint only if a quorum
proposes it, deletes waypoints that a quorum of independent checks distrusts, and hands the surviving list to the
unchanged LLM-A* search. If the guidance stalls during the search, a fallback drops the waypoints and the search
continues as weighted A* (w = 2). Voting needs errors that are not shared, hence different views; the fallback bounds
the damage when they are shared anyway.

```
query (map + start/goal)
   ├─► V1 text     ─┐  one LLM call each, temperature 0, concurrent; a view ABSTAINS on error,
   ├─► V2 corners  ─┤  unsupported input (e.g. no image) or unparsable answer
   ├─► V3 relations ┘  (walls in words; candidate V4 image: a PNG; --views picks any subset;
                       default text,corners,relations, chosen by the pilot 2026-11-04)
                    ▼
   canonicalize: snap to a free cell (±2), then to the nearest corner node (≤3)      --no-snap
                    ▼
   majority ADD: keep cells proposed by ≥ q views; order by mean position            --add-quorum 2
                    ▼
   majority REMOVE: per waypoint 3 checks — code (both path segments hit walls),
   vision (judge call on the image), support (fewer votes than answering views);
   remove if ≥ q checks object; an abstaining check counts as no objection           --remove-quorum 2, --no-vision
                    ▼
   waypoint list ─► LLM-A* search, UNCHANGED ─► operation / storage / length / path
                      └─ stall hook: pops since target active > k·max(20, Manhattan) ⇒ drop waypoints, target = goal   --stall-k 2
```

| # | Component | Fixes (rationale row) | Input → output | Module (planned) | Flag | Proof |
|---|---|---|---|---|---|---|
| 1 | Views | shared mistakes | query → points (or node IDs) per view | `quorumastar/views.py` | `--views`, `--fewshot` | mock-LLM tests per view |
| 2 | Canonicalize | float / never-hit waypoints | points → cells | `quorumastar/canonical.py` | `--no-snap` | snap unit tests |
| 3 | Majority add | one guess misleads | lists → voted list + support | `quorumastar/voting.py` | `--add-quorum` | vote tests; identity at q = 1 |
| 4 | Majority remove | single delete-only judge | list → pruned list | `quorumastar/pruning.py` | `--remove-quorum`, `--no-vision` | one test per check |
| 5 | Stall fallback | bad plans, worst case | search state → goal-only target | `pather/quorum_a_star/` | `--stall-k` | identical metrics at k = 0 |
| 6 | Generator | glue + logging | query → `WaypointResult` | `quorumastar/__init__.py` | `--method quorumastar` | "all off" = LLM-A* test |

**Data contracts.** *Query*: dict with `start, goal, range_x, range_y, horizontal_barriers` (`[y, x1, x2]`),
`vertical_barriers` (`[x, y1, y2]`) plus `map_id, sg_idx`. *Cell*: `(x, y)`; a canonical waypoint id *is* its cell, so
coordinate answers and corner-id answers vote on the same key. *Generator*: `generate(query) -> WaypointResult(waypoints,
parse_ok, raw)`, thread-safe, never raises. *Result keys of the search*: `operation, storage, length, valid, path,
visited, llm_output`.

**Worked example** (invented numbers, for teaching and as a test oracle). Views: text proposes A, B, C; corners
proposes A, B; image proposes A, B, D (cells A=(10,12), B=(25,20), C=(40,8), D=(5,25)).
Add, quorum 2: A has 3 votes, B 3, C 1, D 1 ⇒ keep A, B. Position = (i+1)/(n+1): A = (1/4, 1/3, 1/4) mean 0.28,
B = (2/4, 2/3, 2/4) mean 0.56 ⇒ order A, B. Remove, quorum 2, on path S–A–B–G: for B, code check fires (S→A is fine but
A→B and B→G both hit walls ⇒ objects), vision judge says "remove 2" ⇒ objects, support 3/3 ⇒ no objection. Two objections
≥ 2 ⇒ B is removed. Final waypoints: [A]. LLM-A* then searches S→A→G.

**Glossary.** *waypoint / target*: an intermediate cell the search is steered through. *corner node*: a free cell diagonal
to a barrier end, where a shortest path can bend; *visibility graph*: corner nodes joined when the straight segment
between them crosses no barrier; the corner view writes it as an *incident* adjacency list (one line per node: ID,
coordinates, visible neighbors with Euclidean distances). *quorum*: minimum number of agreeing voters. *abstain*: a voter casts no vote and no
objection. *snap*: move a point to the nearest valid cell. *stall*: the search spends too many pops on one target.
*weighted A\** (w): f = g + w·h; larger w expands fewer nodes but loses optimality. *operation*: heap pops (duplicates
included); *storage*: `len(g)`; *length*: sum of Euclidean steps.

## Teaching protocol
The user must be able to explain and defend each component. Teach at step boundaries; do not dump code unexplained.
- **Lesson card** (≤12 lines, before coding a component): (1) the weakness it fixes (name the rationale row); (2) the idea
  in one sentence; (3) the mechanism as ≤6 lines of pseudocode or by tracing the worked example with its numbers; (4) how
  it can fail, including the negative result to expect; (5) where it lives: file and test name; (6) its source paper.
- **Plain language, define on first use** (use the Glossary). Prefer one concrete trace over an abstract paragraph.
- **Predict, then measure**: before any experiment, state the hypothesis and ask the user to predict the outcome; after
  it, explain the result, including negative ones, without spin.
- **Check question** at the end of every step: one question answerable from the lesson card (e.g. "why does a corner view
  help when the text view is wrong?"). If the answer is wrong, re-explain with a different example before moving on.
- **Explain every diff** in 3–5 plain sentences: what changed, why, what test proves it.
- Never claim more than the evidence supports. In particular the reproduction is faithful for Table 1 but not for the
  paper's scalability magnitudes (see Results); do not describe the code as "verified by the paper".

## Build protocol (one step)
1. Restate the step and its acceptance test. 2. Write the test first (mock LLM, no network). 3. Smallest reviewable diff,
one logical change per commit, on a feature branch. 4. Give the user the exact commands (env, flags, expected output) and
wait. 5. Update this file. 6. Commit message (one line), then the check question.
**Definition of done:** tests pass on Python 3.11 with only `pip install -r requirements.txt`; the Hard rules still hold;
the component's off-switch gives the baseline result; METHOD.md matches the code; no secret, no `scripts/` reference in a
tracked file; this file updated.

## Constraints
**Working with the user.** The user runs every command; give exact copy-pasteable commands, the conda env (`llmastar`
for the project, `vllm` for the model server) and what to report back, then wait. The user cannot reliably copy terminal
output: prefer `! <cmd>` for short checks; give long commands as a script in `scripts/` (git-ignored, local only; env
guard, writes `logs/<name>.log`, which Claude then reads). Shared GPU server, everything under /home/minho; the user
reserves the GPU and sets `$CUDA_VISIBLE_DEVICES`. Local LLM = vLLM's OpenAI-compatible server (`scripts/serve_local.sh`);
the same client works with GPT-4o mini by changing only `--model` / `--base-url`. Git: `origin` is SSH, plain `git push`
works from the user's shell (not from Claude's, which has no SSH agent).

**Target environment.** Ubuntu 22.04, Python 3.11, only `pip install -r requirements.txt`, no GPU. Key from `api_key`,
`openai.api_key` or `OPENAI_API_KEY`. `LLMAStar(llm='gpt', prompt=...)` must keep working. Never require image input,
JSON mode, `seed` or `temperature` (unknown robustness LLMs).

**Never do.** Tune defaults on `dataset/environment_50_30.json` or on the held-out harder split (few-shot examples come
only from self-generated maps). Change the search loop or f-value beyond the no-op hook. Change metric definitions
(operation = heap pops incl. duplicates = `len(CLOSED)`, storage = `len(g)`, length = sum of Euclidean steps). Break
`LLMAStar(...).searching(query=...)` or its result keys. Commit secrets, tokens or personal data. Reference `scripts/`
from tracked files. Describe the project as making A* "cheaper": the framing is better waypoints leading to more
efficient search, at the cost of more LLM calls.

## Current status
- Phase: Quorum-A*. Reproduction (Table 1, Figs. 1–3, ours-vs-paper figures, 92bf3da) and step 1 are done.
- 1b done: the test now pins our 82 / 228 / 53.46 (paper 140 / 235 / 53.46; gap in REPRODUCTION.md), PR #1
  (`fix-1b-test`), merged into main (883e532). All tests pass.
- Branch `quorumastar` (from main 883e532): steps 2a, 2b and 2e done with tests (`tests/test_wastar.py`,
  `tests/test_quorumastar_search.py`); weighted A* w = 1.5 / 2 / 3 run on all 1,000 queries (see Results).
- Second site, dgx (Tailscale, user `ymkwon`, work under `/raid/slpr/ymkwon`, never in `~`): 8× V100-SXM2 16 GB,
  driver 535 (CUDA 12.2). torch 2.8.0+cu128 runs there (sm_70 in the arch list); vLLM 0.11.0 in
  `/raid/slpr/ymkwon/envs/vllm` serves Llama-3-8B-Instruct with `--dtype float16 --tensor-parallel-size 2
  --gpu-memory-utilization 0.90 --max-num-seqs 32 --enforce-eager` (FlexAttention backend; without the last two
  flags the warm-up runs out of memory on 16 GB). These are deviations from the bf16 A5000 Table 1 run.
- dgx parity check passed (see Results): on the first 50 queries, fp16/V100 and the team's bf16/A5000 LLM-A* runs
  agree on 45/50 queries and differ by < 1 point on the averages, so dgx can run the LLM experiments.
- Step 2.0 done on branch `client-2.0` (a–e; f documented, the `-stopnl-max100` Table 1 runs are still to do): see Log.
- Step 2 done: 2c, and 2d (`llmastar/quorumastar/`: config, geometry, canonical, voting, pruning, render, parsing,
  views, fewshot, `QuorumAStarGenerator`; `--method quorumastar`). Nothing has run against a real model yet: every
  test uses a mock. GPT-4o mini has never been called (no API key yet). Next: step 3 on dgx; Qwen2.5-VL-7B on dgx needs the same fp16 parity
  check before step 3; run Table 1 with `--stop-newline --max-tokens 100` for 2.0f.
- 2026-11-03 night: first real-model runs, on GPT-4o mini (dgx GPUs 0-7 all taken by other users; GPT-4o mini is the
  course's model, so it went first). Image reading 2/3, all off = LLM-A* confirmed (0 new requests, identical
  metrics), Quorum-A* ran end to end on 5 queries (see Results). Pilot tooling added (`llmastar/quorumastar/pilot.py`);
  next: the pilot on 50 self-generated maps with GPT-4o mini.
- 2026-11-04: pilot done (see Results). Direction chosen by KC: keep Quorum-A* as the method (claim: it filters the
  waypoints that make LLM-A* worse than no LLM), fix the defaults from the pilot only, then run all 1,000 queries on
  gpt-4o-mini; step 6 (harder generated maps) is a generalization check, not a tuning set.

## Next steps
- [x] 1. Read the repo and REPRODUCTION.md; write agent.md and METHOD.md. *(2026-11-03; layout = METHOD.md §10)*
- [ ] 1b. *(approved 2026-11-03)* Verify the LLM-A* search without an LLM: feed it the waypoints read off the paper's
      Fig. 1 and expect 140 / 235 / 53.46. An exact match verifies the loop independent of the model.
- [ ] 2.0 *(approved 2026-11-03, after 1b)* User-facing interface, one commit each:
  - [x] a. Key from `api_key`, else `openai.api_key`, else `OPENAI_API_KEY`; `LLMAStar(llm='gpt')` keeps working and
        uses `prompt_set="gpt"` (chat completions only).
  - [x] b. Client: 60 s per-call timeout; retry 429 / 5xx / timeouts up to 3× with exponential backoff; on a rejected
        parameter, drop it and retry once; never retry other 4xx; errors returned, never raised or cached; separate
        `--stop-newline` (original `stop="\n"`) and `--max-tokens` flags; "original setup" runs use both
        (stop "\n", max_tokens 100).
  - [x] c. Generator / runner: an LLM failure becomes "no waypoints" plus an `llm_error` column and a printed count.
  - [x] d. Tests with a mock text-only model. [x] e. README as the user-facing interface (install, key, run on a map/query file,
        reproduce Table 1 with one command, output format); `--dataset` accepts a single query file.
  - [~] f. REPRODUCTION.md: `stop="\n"` / `max_tokens` as setup deviations (documented; runs pending); Table 1 reported both ways.
- [ ] 2. Shared infrastructure, each with mock-LLM pytest tests and a CI workflow (Python 3.11, requirements.txt only):
  - [x] a. `_after_pop` hook + `QuorumAStar` stall fallback; identical metrics at `stall_k=0` on a fixed set of maps. *(2026-11-03, branch quorumastar)*
  - [x] b. `--method wastar --weight W` (= `DWAStar(w0=W, decay=1)`); w = 1 equals A*. *(2026-11-03)*
  - [x] c. Client: image message parts (cache stores an image hash), JSON mode with fallback. *(2026-11-03)*
  - [x] d. `llmastar/quorumastar/` modules (METHOD.md §10) *(2026-11-03; all off = LLM-A* tested with a mock model)* + the §6 "all off" test (same messages and cache key as
        `PromptWaypointGenerator`, same results as `LLMAStar`). [x] e. CI pinned to `ubuntu-22.04`. *(2026-11-03)*
- [ ] 3. End to end: `python -m llmastar.run --method quorumastar ...`. Baselines on qwen2.5-vl-7b-instruct (all 1,000):
      astar, wastar w = 1.5 / 2 / 3, llmastar standard / cot / repe; wastar ×3 also on llama-3-8b-instruct. All-off run:
      0 new LLM requests and metrics equal to `llmastar_standard.csv`.
      *(2026-11-03: all-off check passed on gpt-4o-mini, 10 queries; Qwen baselines wait for free GPUs.)*
- [ ] 4. Pilot (50 maps, local model). Ground truth: a waypoint is "bad" if the shortest path through it (start→wp→goal,
      by A*) is > 5% longer than optimal (METHOD.md §11). (i) each candidate view's solo waypoint quality (text, corners,
      image, relations), on self-generated maps only, never the evaluation maps; (ii) how often each shares the same bad
      waypoint with the text and corner views; choose the third view (image or relations) by best combined quality and
      independence, and record the decision and its numbers under Decisions; (iii) vision check catch / false-alarm
      rates; (iv) Quorum-A* vs. LLM-A* vs. weighted A*. Write a go/no-go decision here and wait for the user.
      Tooling: `python -m llmastar.quorumastar.pilot make` / `report` (also: vote agreement and an offline simulation
      of radius-r vote matching, r = 0..3, for every 3-view set).
- [ ] 5. Full runs (1,000) and ablations: each view alone vs. all; quorums; vision; snap; fallback; few-shot
      shared / per-view / none; CoT; roles.
- [ ] 6. Harder generated maps (mazes, more walls, 2–3× size; fixed seed; held-out split never used for defaults) and a
      second model. *(2026-11-04: `python -m llmastar.generate_maps` (dense, large, zigzag; 100 each, seed 1, committed
      in `dataset/generated/`); runs in `experiments/gpt-4o-mini.sh hard`.)*
- [ ] 7. Report support: export what the report needs from `outputs/` only: Table 1 vs. paper; Quorum-A* vs. A*, LLM-A*
      and weighted A* (ops vs. length trade-off with the weighted-A* frontier); ablation bars; failure cases and failed
      experiments, explained; cost table (calls, tokens, seconds per query); reproducibility appendix (models, decoding
      settings, prompts, hardware, commands). Every number cites its output file.
- [ ] 8. Report drafts *(proposed)*: outline per required section, then DRAFT text clearly marked; the user rewrites it.
      Check that every sentence describes what the code does (report–code consistency) and every reference is verified.
- [ ] 9. Submission package: zip from a clean checkout; fresh Python 3.11 env with only `requirements.txt`; run the README
      commands exactly as written; confirm the I/O formats match the baseline repo (query dict in, result keys out) and a
      an unseen map file runs unchanged; scan for secrets and `scripts/` references; METHOD.md matches the code; every
      number in the report draft cites an output file. Ask the user for the package name.
- [ ] 10. Work record: at each step end, add a dated Log line (what, files, commit) so the user can describe their own
      work from artifacts.

## Decisions (date · decision · reason; superseded ones are marked, never deleted)
- 2026-11-03 · `LLMAStar(llm='gpt')` = GPT-4o mini (was gpt-3.5-turbo), Chat Completions, `prompt_set="gpt"`; the course
  evaluates with GPT-4o mini · KC (to confirm with the team). `python -m llmastar.table1` runs every Table 1 row.
- 2026-10-29 · Generators register in `llmastar/waypoints/REGISTRY`; the search consumes a waypoint list · swappable step.
- 2026-10-29 · Temperature 0, `max_tokens` 2048, cache in `.cache/llm/` by model, URL, messages, sampling · free reruns
  (REPRODUCTION.md deviation 2). `scripts/` is git-ignored; figure code is in `llmastar/figures/`.
- 2026-10-29 · The Dynamic WA* row is the `dwastar` reading (w = max(1, 2·0.99^pops), OPEN re-keyed), within 1.5 points of
  the paper (deviation 4). Weighted A* = `DWAStar(w0=w, decay=1)`; its rationale number (34.3%) is external, so add
  `wastar` runs w = 1.5 / 2 / 3 and cite them · user.
- 2026-10-29 · `--fewshot paper`: the text view sends LLM-A*'s exact messages (no JSON mode) and passes waypoints through;
  "all off" = `--views text --fewshot paper --add-quorum 1 --no-vision --no-snap --stall-k 0`; one no-op hook
  `_after_pop(s)` carries the stall fallback, tested for identical metrics at `--stall-k 0` · user; §6, §7.
- 2026-10-29 · One VLM, Qwen2.5-VL-7B-Instruct (bf16), for all views, the vision judge and the LLM-A* rerun; Llama-3-8B
  only for Table 1; GPT-4o mini later as the final model · user. MMP-A* = Ha et al., arXiv:2601.01910 v2 (one VLM
  judge per map keeps or discards numbered waypoints, never adds; heuristic term decays by α^k, α = 0.7); code
  github.com/langkhachhoha/MMP-ASTAR. Canonical waypoint id = the snapped cell (§4.3).
- 2026-10-30 · Step-1 docs went straight to main; later work on a feature branch `quorumastar` from main.
- 2026-11-03 · Method name Quorum-A*; planned names: package `llmastar/quorumastar/`, `--method quorumastar`, classes
  `QuorumAStar`, `QuorumAStarGenerator`, `QuorumConfig`, `pather/quorum_a_star/`, tests `tests/test_quorumastar_*.py` · user.
- 2026-11-03 · Environment constraints → Constraints. Reported Table 1 keeps `stop="\n"` removed (it cuts multi-line CoT/RePE answers),
  recorded as a deviation, with a flag to restore it and both versions reported · user. At most 4 LLM calls per query by
  default (3 views + vision judge), 60 s per call; on error a voter abstains, and with no voters the search runs with no
  waypoints; wall time per query is logged · user.
- 2026-11-03 · agent.md is an agent prompt (Mission, Architecture, Teaching and Build protocols, then state) · user.
- 2026-11-03 · Client retries: 429 / 5xx / timeouts up to 3× with exponential backoff; a rejected parameter is dropped and
  retried once; other 4xx never retried. *Supersedes* "no retries by default" (entry above) · user review.
- 2026-11-03 · `--stop-newline` and `--max-tokens` are separate flags; "original setup" runs use both (stop "\n", 100).
  `llm='gpt'` uses `prompt_set="gpt"`; chat completions only. Steps 1b then 2.0 approved · user review (Q6–Q8).
- 2026-11-03 · Pilot ground truth: a waypoint is bad if start→wp→goal by A* is > 5% longer than optimal. *Supersedes* the
  "> 3 cells from A* corners" rule · user review.
- 2026-11-03 · No fixed schedule; track progress here. "Save progress" protocol added (Session protocol 6) · user.
- 2026-11-03 · Pilot model: gpt-4o-mini instead of the local model (dgx GPUs taken; it is the course's model, about
  $0.007 per query). The pilot run asks all four candidate views at once (5 calls per query, above the default 4,
  measurement only); vote matching radius is measured offline from the same answers before any default changes · KC.
- 2026-11-04 · Default views text,corners,relations with the vision judge (4 calls per query). Pilot only, 3 views +
  judge (A* = 100): text,corners,relations 23.38 / 48.30 / 103.31; text,corners,image 24.05 / 49.04 / 103.10; the
  difference is small (n = 50), so the tie goes to relations' higher solo quality (62.4% vs 57.8%) and lower cost (no
  image view; the judge is then the only image call). The judge stays: it keeps few waypoints but they beat weighted
  A* (75.2 ops on the 7 queries that kept one), and every other query runs exactly as weighted A*. Resolves Q11 · KC.
- 2026-11-04 · All gpt-4o-mini experiments run from `experiments/gpt-4o-mini.sh` (main, free ablations, ablations,
  Table 1 rows, hard maps). Ablations that need new LLM calls use the first 300 benchmark queries (maps 0-29), at
  about $1.5 per run instead of about $5; the main comparison stays on all 1,000. Hard-map kinds and their parameters
  (dense, large = 2x side, zigzag = serpentine walls) were fixed before any run on them and never choose a default.
  A run whose raw log shows a failed call is rerun (cached answers reused) so no result hides an error · KC.
- 2026-11-03 · Views: corners = visibility-graph incident adjacency list (Fatemi et al., arXiv 2310.04560, incident
  encoding best for most prompting methods; Li et al. 2026, arXiv 2604.10690, adjacency lists beat grids on mazes);
  candidate view `relations` (walls and passages in words, coordinate answers); image kept; default stays
  text,corners,image until the pilot picks the third view; ≤ 4 calls per query · user review.

## Conventions
- `CLAUDE.md` contains only `@agent.md`. Layout: `llmastar/run.py` (one method over the benchmark), `summary.py` (Table 1
  format), `scale.py` (Fig. 3), `figures/`, `pather/` (A*, DWA*, LLM-A*: search only, no LLM code), `waypoints/` (`base.py`:
  `WaypointGenerator`, `WaypointResult`, `parse_waypoints`; `prompting.py`: the paper's prompts), `model/` (`ChatGPT` client
  + `cache.py`), `benchmark.py` (`load_queries`, `evaluate_llm_path`, `segment_collides`), `outputs.py`.
  `dataset/environment_50_30.json`: 100 maps × 10 queries on a 51 × 31 grid. Generators must be thread-safe.
- Waypoint filter and the no-survivor fallback: METHOD.md §1.
- Outputs: `outputs/<model>/<run>.csv`, `raw/<run>.jsonl` (git-ignored), `traces/<run>/<map>_<sg>.json`, `summary.md`,
  `summary.csv`, `scalability.csv`; `outputs/figures/`. `<model>` = served name (`llama-3-8b-instruct` for Table 1,
  `qwen2.5-vl-7b-instruct` for Quorum-A*). Run name `<method>[_<tag>][-<variant>]`, e.g. `wastar-w2`, `quorumastar`.
- CSV columns: `map_id, sg_idx, start, goal, method, prompt, model, operation, storage, length, valid, valid_lenient,
  parse_ok, n_waypoints, n_targets, seconds, error` (+ METHOD.md §8 columns). Table ratios: geometric mean of
  (run / A*) × 100 over queries valid in both; `no_targets` = % of queries with `n_targets == 2`.
- Tests: `pytest -q tests` (env `llmastar`); CI `.github/workflows/test.yml`. Local scripts (git-ignored):
  `scripts/serve_local.sh [llama3|qwen2.5-vl|DIR] [name]`, `scripts/get_qwen_vl.sh`, `scripts/setup_vllm_env.sh`.

## How to run
Envs: `llmastar` (Python 3.11, `pip install -r requirements.txt`) and `vllm` (`vllm==0.11.0`, `transformers>=4.56,<5`).
Models in `~/models/` (Qwen2.5-VL not downloaded yet).
```bash
bash scripts/get_qwen_vl.sh && bash scripts/serve_local.sh qwen2.5-vl   # env vllm; or: serve_local.sh llama3
export OPENAI_API_KEY=dummy                                              # env llmastar
python -m llmastar.run --method astar --jobs 8                           # also dwastar
python -m llmastar.run --method llmastar --prompt standard --jobs 8 --workers 32   # cot, repe; --limit 50 = pilot
python -m llmastar.scale --jobs 8 && python -m llmastar.summary && python -m llmastar.figures
pytest -q tests
```
Add `--model qwen2.5-vl-7b-instruct` to use (and write outputs for) the Qwen server.

## Results
- 2026-10-29 · Table 1 reproduction · llama-3-8b-instruct · all 1,000 queries · `outputs/llama-3-8b-instruct/summary.md`.
  Ops / storage / length (A* = 100), paper in brackets: dwastar 59.49 / 78.65 / 100.25 (60.91 / 78.53 / 100.24);
  llmastar_standard 42.99 / 62.83 / 102.27 (44.59 / 64.02 / 102.47), no_targets 25.40%; llmastar_cot 49.63 / 68.06 /
  102.45 (47.60 / 66.27 / 102.46); llmastar_repe 69.70 / 84.31 / 102.42 (64.08 / 80.19 / 102.54); all valid 100%.
  LLM-only valid 10.70 / 9.70 / 9.80% (paper 12.60 / 12.00 / 16.40%). Other DWA* readings are in the same file.
- 2026-10-29 · Fig. 1 query: ours 183 / 292 / 56.77, paper 140 / 235 / 53.46 (both Llama waypoints fell on walls).
- 2026-11-03 · Fig. 3 scalability at 10× · `outputs/llama-3-8b-instruct/scalability.csv`, `outputs/figures/fig5_*`: A* 107.8 ops /
  76.2 storage (paper ≈ 115 / ≈ 65); LLM-A* 73.0 / 45.2 (paper ≈ 36 / ≈ 14). The paper's curve is read off its published image
  (about ±1), not the authors' data. Three of our 10 queries get no LLM-A* saving at 10×; cause not yet tested.
- 2026-10-29 · `llmastar_standard` had `no_targets` = 25.40% (those queries ran as weighted A*, w = 2) ·
  `outputs/llama-3-8b-instruct/summary.md`.
- 2026-11-03 · Weighted A* (constant w) · all 1,000 queries · `outputs/llama-3-8b-instruct/wastar-w{1.5,2,3}.csv`,
  `summary.md`. Ops / storage / length (A* = 100): w = 1.5: 40.06 / 60.26 / 100.74; w = 2: 34.32 / 56.23 / 102.02;
  w = 3: 29.92 / 53.26 / 103.68; all valid 100%. So weighted A* with w = 2 expands fewer nodes (34.32) than LLM-A*
  standard (42.99) at a shorter path (102.02 vs 102.27), with no LLM call. This confirms the Research-rationale
  hypothesis on our own data; the external 34.3% can now be replaced by this file.
- 2026-11-03 · dgx parity check · llama-3-8b-instruct, `llmastar --prompt standard --limit 50` · fp16 on 2× V100
  (dgx, `outputs_dgx/`, not committed) vs. the committed bf16 A5000 run. Identical metrics on 45/50 queries; averages
  (A* = 100) ops 45.36 vs 44.89, storage 62.41 vs 61.76, length 101.57 vs 101.60, no_targets 22.0% vs 22.0%, valid
  100% both. The 5 differing queries go both ways (ops 505→453, 80→75, 346→407, 388→523, 111→140). 50 LLM calls took
  69 s (eager mode). Reading: fp16 changes a few greedy answers, not the averages.
- 2026-11-03 · Stall fallback on the Fig. 1 query with the paper's waypoints (`tests/test_quorumastar_search.py`):
  k = 2 fires at pop 80 (leg (24, 15) -> (5, 6): budget 56, 57 pops used), one pop before the target; k = 3 never
  fires. Result unchanged either way. Evidence that k = 2 is tight; the pilot (self-generated maps) decides k.

- 2026-11-03 · First real-model runs · gpt-4o-mini (OpenAI API, KC's key) · `outputs_gpt/gpt-4o-mini/` (dgx, not
  committed). (a) Image reading (`scripts/vl_smoke.py`, 3 pool maps, seed 99): S and G within 2 cells on 2/3 maps,
  max error 3 on the third. (b) All off = LLM-A* on the first 10 queries: `llmastar_standard` 56.27 / 70.99 / 101.04,
  all-off run 56.27 / 70.99 / 101.04 with 10/10 from cache (0 new requests). (c) Quorum-A* default (text, corners,
  image; quorum 2; vision judge) on the first 5 queries: 0 abstentions, 0 errors, 100% valid, 16 calls, 243,726 tokens
  (about 49k per query, about $0.007); ops / storage 38.62 / 58.74 vs LLM-A* 36.90 / 57.02 on the same 5 (n = 5, no
  conclusion). Mechanism: on 4/5 queries no cell got 2 votes, so the search ran without waypoints; on 0:0 text and
  corners chose the two corner cells of one wall end ((24, 9) and (26, 9)), which the exact-cell vote counts apart;
  the image view answers long axis-aligned paths on multiples of 5. These are evaluation queries: they only show the
  pipeline runs and suggest what the pilot should measure; no default is changed from them.

- 2026-11-04 · Pilot (METHOD.md 11) · gpt-4o-mini · 50 self-generated maps (`pilot make`, seed 1) ·
  `outputs_pilot/gpt-4o-mini/` (dgx, not committed), `pilot_quorumastar-vtext+corners+image+relations.md`.
  Search (A* = 100; ops / storage / length): wastar-w2 24.34 / 49.25 / 103.18; llmastar_standard 35.92 / 61.07 /
  102.89; Quorum-A* with all four views and the vision judge 23.98 / 49.09 / 102.80; without the judge 24.27 / 49.39 /
  102.87; without any removal 24.39 / 49.66 / 102.96. Against weighted A* (= 100), split by whether the search kept
  waypoints: LLM-A* kept them on 47/50 queries at ops 151.3 (its waypoints make search worse than no LLM); Quorum-A*
  with judge kept them on 12/50 at ops 93.9 and ran as weighted A* on the other 38 (100.0); without judge 38/50 at
  96.1, and the 12 others at 112.2 (6 stall fallbacks). Solo quality (good waypoints / queries with a good one):
  text 53.2% / 78%, corners 54.7% / 80%, image 57.8% / 100% (521 waypoints, about 10 per answer), relations 62.4% / 86%.
  Shared bad waypoints: relations repeats text's (31.4% of its bad ones), image almost never repeats anyone (2.3%).
  Vote (quorum 2, exact cell): 45/50 queries keep a waypoint with 4 views, 66.2% good; text,corners,image 33/50,
  74.5% good; text,corners,relations 41/50, 63.6%. Matching radius r = 1..3 adds coverage but no quality (r = 2:
  61.0% with 4 views), so exact-cell voting stays. Vision judge: catch 88.9% (24/27 bad), false alarm 83.0% (44/53
  good): it keeps few waypoints, but the ones it keeps beat weighted A*. 245 calls, 3.81 M tokens (76k per query).
  Reading: Quorum-A* removes LLM-A*'s loss (36 -> 24 ops) and matches, not beats, the no-LLM weighted A* overall.
- 2026-11-04 · Pilot, 3 views + judge (the 4-call budget) · same maps: text,corners,image 24.05 / 49.04 / 103.10,
  waypoints kept on 10/50 (ops 94.1 vs weighted A*); text,corners,relations 23.38 / 48.30 / 103.31, kept on 7/50
  (ops 75.2, storage 87.0 vs weighted A*); every query without waypoints equals weighted A* (100.0).

## Open questions
- Q10. `--stall-k` default: 2 (METHOD.md) fired on the Fig. 1 query one pop early. Keep 2 and let the pilot decide, or
  change METHOD.md to 3 now?

## Log
- 2026-11-04 (yumin0-0) · `experiments/gpt-4o-mini.sh` (every gpt-4o-mini run, with a rerun on failed calls);
  `llmastar/generate_maps.py` + `dataset/generated/{dense,large,zigzag,pilot}.json` (`tests/test_generate_maps.py`);
  on the first 15 maps weighted A* (w = 2) needs 33.6% / 16.4% / 100.0% of A*'s operations on dense / large / zigzag,
  so zigzag is the case where weighted A* gains nothing. Main 1,000-query run on gpt-4o-mini started 00:17.
- 2026-11-04 (yumin0-0) · Default views text,corners,relations (Decisions); METHOD.md 4.1 and 5, README overview.
- 2026-11-04 (yumin0-0) · Pilot on gpt-4o-mini (see Results); `pilot report` now also splits every LLM run against
  weighted A* by whether the search kept waypoints (`split_table`, `tests/test_quorumastar_pilot.py`).
- 2026-11-03 (yumin0-0) · Step 3 on gpt-4o-mini (see Results) and the pilot tooling: `llmastar/quorumastar/pilot.py`
  (`make`: 50 maps from the few-shot generator under a disjoint seed namespace; `report`: solo quality, shared bad
  waypoints, voting as run and simulated at radius 0..3, vision catch / false-alarm, search vs A*), with
  `tests/test_quorumastar_pilot.py`.
- 2026-11-03 (yumin0-0) · Submission interface: `QuorumAStar(llm="gpt").searching(query=..., filepath=...)` builds
  QuorumAStarGenerator on GPT-4o mini, same result keys as LLMAStar plus `fallback` (the course requires the baseline
  repository's input/output format on hidden maps); README example (`tests/test_quorumastar_api.py`).
- 2026-11-03 (yumin0-0) · PR #2 merged (main b24bc15). Added `llmastar/figures/fig6_methods.py` (team request): A*,
  LLM-A*, Quorum-A* searches on one query + averages vs A* with weighted A* (w=2), all on the same queries; a run that
  does not exist is drawn as an empty panel, never estimated (`tests/test_fig6_methods.py`). Current
  `outputs/figures/fig6_methods_llama-3-8b-instruct.png` has no Quorum-A* yet. Qwen2.5-VL-7B download started on dgx.
- 2026-11-03 (KC = yumin0-0, branch `quorumastar`) · 2d part 2: config (flags, run-name variants), render (PNG, numbered
  waypoints), parsing (JSON, fenced, fallback list, ids), views (text / corners / image / relations / paper), fewshot
  (seeded pool of generated maps, gold = string-pulled A* corners; never an evaluation map), generator (concurrent
  views, abstentions, vision judge, per-query log), runner (`--method quorumastar`, CSV `fallback, fallback_pop, calls,
  prompt_tokens, completion_tokens, llm_seconds`). §6 test: all off sends LLM-A*'s exact request (same cache key, 0
  new requests) and gives identical search results. Prompt sizes on the benchmark: corners view up to ~9.6k chars
  (~3k tokens), fits 8,192. 110 tests pass. Note: commits up to 20b81a3 carry author KC <kichul0914@gmail.com>, the
  same person as yumin0-0.
- 2026-11-03 (KC, branch `quorumastar`) · 2c: `image_part`, `redact_images` (cache key and record hold a sha256),
  `json_mode` falls back when rejected (`tests/test_client_multimodal.py`). 2d part 1: `llmastar/quorumastar/`
  geometry (filter = the search's, checked cell by cell), canonical (§4.3), voting (§4.4), pruning (§4.5);
  `tests/test_quorumastar_core.py` uses agent.md's worked example as the oracle. 84 tests pass.
- 2026-11-03 (KC, branch `client-2.0`) · 2.0a key order + `llm='gpt'` (`tests/test_client.py`); 2.0b client: 60 s
  timeout, 3 retries with backoff on timeouts / connection / 408 / 409 / 429 / 5xx, one retry without a rejected
  parameter, other errors returned and not cached, `--api-key`, `--stop-newline`; 2.0c/d generator never raises,
  `llm_error` CSV column + printed count, LLMAStar warns (`tests/test_llm_failures.py`); 2.0e `--dataset` takes one
  map / one query / a list of queries, `python -m llmastar.table1`, README "Use it on your own maps"
  (`tests/test_dataset_formats.py`); 2.0f deviation text in REPRODUCTION.md (2 and 7). 63 tests pass.
- 2026-11-03 (KC) · 1b fixed (PR #1): test pins 82 / 228 / 53.46; no reading of (24, 16) within ±2 cells gives
  storage 235. dgx set up (V100 16 GB, driver 535): torch 2.8.0+cu128 runs on sm_70; vLLM 0.11.0 serves
  Llama-3-8B in fp16 on two GPUs (OOM on warm-up fixed with --max-num-seqs 32 --enforce-eager); 50-query parity
  check vs. the bf16 run passed (45/50 identical, averages within 1 point).
- 2026-11-03 (KC, branch `quorumastar`) · 2b: `--method wastar --weight W` in `run.py` (+ `tests/test_wastar.py`,
  fc04acb); 2a: `_after_pop` hook in `llm_a_star.py`, `pather/quorum_a_star/` with the stall fallback
  (+ `tests/test_quorumastar_search.py`, 2830268); 2e: CI on ubuntu-22.04 (9db5674). Ran wastar w = 1.5 / 2 / 3 on
  all 1,000 queries and refreshed `summary.md` / `summary.csv`. Found the 1b test failing on main (fixed in PR #1).
- 2026-11-03 · Applied review (retry policy, pilot ground truth, hypothesis wording, Q6–Q8, incident-encoded corners,
  candidate `relations`; METHOD.md §11, README "Inspirations"). Rewrote this file as an agent prompt; recorded the
  environment constraints; rendered ours-vs-paper figures. Added the 1b test
  (`tests/test_astar.py`, paper's Fig. 1 waypoints: storage 235, length 53.46 asserted; operation not asserted).
  Original GPT client: `openai.api_key`, completions endpoint, `stop=["\n"]`, `max_tokens=100`; ours sends `top_p`,
  retries 5× with a 600 s timeout and aborts a run on a generator error.
- 2026-10-29/30 · Method spec written; Qwen2.5-VL and MMP-A* checked; step-1 docs on main, `origin` switched to SSH.
  Table 1 and Figs. 1–3 reproduced with Llama-3-8B-Instruct on vLLM (main 823a892, docs a536281).
