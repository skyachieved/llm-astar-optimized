# Changes on `readme-grading-steps` (2026-11-20 to 11-21)

What we changed for the submission, for review before the merge into `main`. A review note, not part of the
submission. The search code and the experiments' commands are unchanged: the README was rewritten, one script was
added, and the rest are documentation, comments and file removals.

**Why.** The TAs grade by following the README in a fresh Ubuntu 22.04 / Python 3.11 environment with only
`pip install -r requirements.txt`, no GPU and their own GPT-4o mini key, and they run hidden maps through it ("Points
will be deducted if your results cannot be reproduced by following the README"; Notice, Code Files items 3–5). The
report now links this repository, which is public, so the repository is part of what the TAs and peer reviewers see.

## 1. README.md, rewritten (335 → 140 lines)

- **Order:** Setup → 1. Check our numbers (no key) → 2. Rerun the experiments (GPT-4o mini) → 3. Run on your own
  maps → 4. More experiments → 5. Runs that need a GPU → Code. Code blocks hold only terminal commands, and the only
  thing a TA edits is the API key.
- **Section 1 comes first:** `python -m llmastar.report` and `python -m llmastar.ci_stats` rebuild
  `outputs/report/tables.md` and `ci_tables.md` from the committed CSVs, identical to the committed files. It comes
  before section 2 because `table1` and `main` overwrite `outputs/gpt/gpt-4o-mini/`.
- **Section 2:** `table1`, `main`, `analyze` (Table 3, from the answers `main` cached), then `report` and `ci_stats`.
  Expected table with 95% CIs (= report Tables 1–2). Notes: the no-LLM rows match exactly and the LLM rows can move
  slightly; the all-off row equals LLM-A\*; the `stop="\n"` rows; failed calls rerun automatically; `main` costs
  about $1.40; `summary.md`'s `paper_*` columns hold the paper's Llama-3 rows.
- **Section 3:** `experiments/run_maps.sh` for any map file; the Python interface (`QuorumAStar(llm='gpt')` takes the
  baseline's query dict and returns its keys plus `fallback`); `openai.api_key` works as in the original code;
  another model through `LLM_MODEL` / `LLM_BASE_URL` or `llm=ChatGPT(model=..., base_url=...)`.
- **Section 4:** `free`, `ablations`, `hard`, `other-models.sh`, `report` / `ci_stats`, Figure 2
  (`python -m llmastar.figures.fig8_models --report`); `gpt-4o-mini.sh all` with what all our GPT-4o mini runs
  cost (about $21 and 3.5 hours, pilot included); Claude needs `ANTHROPIC_API_KEY`.
- **Section 5:** Llama-3-8B-Instruct for the report's Table 1 on one 24 GB GPU (vLLM env, model download, server,
  `python -m llmastar.table1`); Qwen points to REPRODUCTION.md.
- **Removed:** the results sections (now in the report and the expected table), the old setup and run sections
  (replaced by sections 1–5), "What's where" (now "Code"), "Inspirations" and the BibTeX "Credit". The intro keeps the
  credit line for the original code (MIT) and the paper; the idea sources are in the report's references and
  METHOD.md (MedRAG only in the report).

## 2. experiments/run_maps.sh (new)

Runs A\*, weighted A\* (w = 2), LLM-A\* and Quorum-A\* with `main`'s settings on any map file(s): the benchmark
format, one map, one query or a list of queries. Failed calls are rerun up to 3 times (cached answers are reused).
Results go to `outputs/maps/<file>/<model>/` (git-ignored). `LLM_MODEL` / `LLM_BASE_URL` select another
OpenAI-compatible model.

## 3. agent.md and CLAUDE.md removed

Both were notes for our AI assistant (CLAUDE.md only loaded agent.md), not documentation, and agent.md held personal
data. They are no longer in the repository the report links, nor in a zip built from it; they stay in the git
history (`git show 84b97d0:agent.md`). All 21 mentions of agent.md now point to METHOD.md 11 or were dropped:
comments and docstrings in `llmastar/` and `tests/`, the headers of `experiments/gpt-4o-mini.sh` (also its "step N"
labels) and `experiments/other-models.sh`, `outputs/pilot/README.md`, and the one sentence `report.py` writes into
`outputs/report/tables.md` (changed in both, so the rebuilt file stays identical).

## 4. METHOD.md

The header no longer refers to agent.md's plan; the rationale table and the vote's tie-break example name the final
default views (text, corners, relations) instead of the image view; "step N" references are reworded; the
implementation map lists `pilot.py`; section 11 records the pilot's choice (relations).

## 5. REPRODUCTION.md and experiments/qwen.sh

- REPRODUCTION.md, Setup: no longer a circular link to the README. It points to README section 5 for the Llama-3
  Table 1 commands, keeps the Fig. 3 commands (`scale`, `figures`) and adds general commands for Qwen2.5-VL-7B
  (download, vLLM on two GPUs in fp16, `bash experiments/qwen.sh main`). The environment table calls the experiment
  env `quorumastar` (was `llmastar`).
- `experiments/qwen.sh`: the serve command in the header used the dgx server's personal paths and GPU numbers; it is
  now the same general command as in REPRODUCTION.md (header comments only).

## 6. .gitignore

`/assignment_guidelines/` (course files, local only) and `/outputs/maps/` (results of `run_maps.sh`).

## 7. Report (report.pdf of 2026-11-21 15:36, still 5 pages; the source is in Overleaf)

- **Table 1** has the paper's format: A\*, Dynamic WA\*, LLM-only and LLM-A\* rows for Llama-3-8B and GPT-4o mini,
  with Valid columns and the paper's values next to ours. The Paper header says "(GPT rows: GPT-3.5†)", and the note
  explains that we use GPT-4o mini, the course's model, where the paper used GPT-3.5. The abstract says "We reproduce
  Table 1 of LLM-A\*" (was "the LLM-A\* rows of Table 1").
- **Cost:** a new Section 5.5 (cost-efficiency analysis, one of the course's additional-credit items) and a $/1k
  column in Table 2; Section 5.4 is now "Harder maps and ablations".
- **Figure 2** is `outputs/figures/fig8_models_report.png`, the picture the README's command makes (four models,
  larger text, legend "No waypoints (weighted A\*, w = 2)"); its caption says "Claude, run on the benchmark only, is
  in Table 2."
- **Abstract:** "with the three GPT models, Quorum-A\*'s gain is close to what dropping every waypoint gives" (was
  "with those four": with Qwen, dropping every waypoint saves 9.8% and Quorum-A\* 6.6%), and a link to this
  repository: "All code is available at https://github.com/skyachieved/llm-astar-optimized."
- **Reproducibility paragraph:** "Without an API key, python -m llmastar.report and python -m llmastar.ci_stats
  rebuild our tables, CIs and SDs (outputs/report/) from the committed results; Table 1's LLM-only rows and Table 3
  are in each run's summary.md and analysis.md. The README lists the commands for every rerun except the pilot."
  (was "Two commands rebuild every table, CI and SD … for every rerun", which those two commands do not do).

## How it was checked

- **Fresh environment** (clone of `2beaa72`, conda env with Python 3.11, only `requirements.txt`): `pytest -q`
  passes, and section 1 rebuilds `tables.md` and `ci_tables.md` identical to the committed files.
- **README commands with a free local model** (Ollama `llama3:8b`, first 50 queries; we had no GPT-4o mini key):
  A\*, Dynamic WA\* and weighted A\* are identical query by query to the committed results; Quorum-A\*'s 150 view
  calls all answered; the all-off run equals LLM-A\* on 49 of 50 queries (the other one was an LLM-A\* call that timed
  out at 60 s on the local GPU, not a code issue); `run_maps.sh` runs end to end.
- **After the last code edits** (branch at `43e7b6f`, conda env with Python 3.11): `pytest -q` passes (147 tests),
  and `report` and `ci_stats` rebuild `tables.md` and `ci_tables.md` identical to the committed files (`git status`
  clean). Every experiment script passes `bash -n`.
- **Report** (15:36 version): every number checked against the committed outputs (`tables.md`, `ci_tables.md`,
  `summary.md`, `analysis.md`, `outputs/pilot/`) and against the paper's Table 1, GPT-3.5 values included. All match.
- **Leaks:** no API key in a tracked file (only the fake `sk-secret` in `tests/test_client.py`); with agent.md gone,
  none of our personal data in the tree (`setup.py` keeps the original author's contact, as in the original code).
