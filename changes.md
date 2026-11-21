# Changes on `readme-grading-steps` (2026-11-20 to 11-21)

For review before merging into `main`. Four commits: `3e3cb4d`, `2beaa72`, `d48e6e6`, `a492567`. The Python code
(`llmastar/`) and the commands of the existing experiment scripts are unchanged; what changed is the README,
REPRODUCTION.md, the header comments of `experiments/qwen.sh`, `.gitignore`, and one new script,
`experiments/run_maps.sh`. This file is for the review only: leave it out of the zip.

**Why.** The TAs grade by following the README in a fresh Ubuntu 22.04 / Python 3.11 environment with only
`pip install -r requirements.txt`, no GPU and their own GPT-4o mini key, and they run hidden maps through it ("Points
will be deducted if your results cannot be reproduced by following the README"; Notice, Code Files items 3–5). The old
README (335 lines) mixed results, method notes and GPU setup; the new one (140 lines) is the grading path, in order.

## 1. README.md, rewritten

- **Order:** Setup → 1. Check our numbers (no key) → 2. Rerun the experiments (GPT-4o mini) → 3. Run on your own
  maps → 4. More experiments → 5. Runs that need a GPU → Code. Code blocks hold only terminal commands, and the only
  thing a TA edits is the API key.
- **Section 1 comes first:** `python -m llmastar.report` and `python -m llmastar.ci_stats` rebuild
  `outputs/report/tables.md` and `ci_tables.md` from the committed CSVs, identical to the committed files. It has to
  come before section 2, because `table1` and `main` overwrite `outputs/gpt/gpt-4o-mini/`.
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

## 3. REPRODUCTION.md

- Setup no longer links back to a README section that pointed here (a circular link). It points to README section 5
  for the Llama-3 Table 1 commands, keeps the Fig. 3 commands (`scale`, `figures`) and adds general commands for
  Qwen2.5-VL-7B (download, vLLM on two GPUs in fp16, `bash experiments/qwen.sh main`).
- The environment table calls the experiment env `quorumastar` (was `llmastar`).

## 4. experiments/qwen.sh, header comments only

The serve command in the header used the dgx server's personal paths and GPU numbers; it is now the same general
command as in REPRODUCTION.md. No code line changed.

## 5. .gitignore

`/assignment_guidelines/` (course files, local only) and `/outputs/maps/` (results of `run_maps.sh`).

## How it was checked

- **Fresh environment** (clone of `2beaa72`, conda env with Python 3.11, only `requirements.txt`): `pytest -q`
  passes, and section 1 rebuilds `tables.md` and `ci_tables.md` identical to the committed files.
- **README commands with a free local model** (Ollama `llama3:8b`, first 50 queries; we had no GPT-4o mini key):
  A\*, Dynamic WA\* and weighted A\* are identical query by query to the committed results; Quorum-A\*'s 150 view
  calls all answered; the all-off run equals LLM-A\* on 49 of 50 queries (the other one was an LLM-A\* call that timed
  out at 60 s on the local GPU, not a code issue); `run_maps.sh` runs end to end. The later commits change text only.
- **Report** (`report.pdf` of 2026-11-21): every number checked against the committed outputs (`tables.md`,
  `ci_tables.md`, `summary.md`, `analysis.md`, `outputs/pilot/`) and against the paper's Table 1, GPT-3.5 values
  included. All match.
- **Leaks:** no API key in a tracked file (only the fake `sk-secret` in `tests/test_client.py`); no personal data
  outside `agent.md`.

## Report revisions (Overleaf; the report is not in this repo)

1. **Figure 2:** use `outputs/figures/fig8_models_report.png`, the version the README command makes (larger text,
   legend "No waypoints (weighted A\*, w = 2)", no empty Claude row). Upload it and use
   `\includegraphics[width=\textwidth]{fig8_models_report.png}`. In the caption, replace "Claude ran on the
   benchmark only." with "Claude, run on the benchmark only, is in Table~\ref{tab:main}." (use Table 2's actual
   label). Check that the report stays at 5 pages.
2. **Abstract:** replace "and with those four, Quorum-A\*'s gain is close to what dropping every waypoint gives" with
   "and with the three GPT models, Quorum-A\*'s gain is close to what dropping every waypoint gives". It holds for the
   GPT models (32 / 19 / 14% against 33 / 21 / 16%) but not for Qwen (9.8% against 6.6%); Section 5.3 already says
   "For the GPT models".
3. **Section 4, Reproducibility:** replace "Two commands rebuild every table, CI and SD from our committed results
   without an API key: python -m llmastar.report and python -m llmastar.ci_stats. The README lists the commands for
   every rerun." with "Without an API key, python -m llmastar.report and python -m llmastar.ci_stats rebuild our
   tables, CIs and SDs (outputs/report/) from the committed results; Table 1's LLM-only rows and Table 3 are in each
   run's summary.md and analysis.md. The README lists the commands for every rerun except the pilot." (keep the
   `\texttt` formatting). The two commands do not rebuild Table 1's LLM-only rows or Table 3, and the pilot has no
   rerun command.

## Before submitting

1. Review this branch and merge it into `main` (a pull request leaves a record for the contribution reports).
2. Build the zip from `main`. `git archive` takes only committed files, so `.git`, `.cache/`,
   `assignment_guidelines/`, logs and caches stay out. Then delete `agent.md`, `CLAUDE.md` and this `changes.md`
   from the export (notes for our AI assistant and for this review, with personal data in `agent.md`). From the
   repository folder:

   ```bash
   T=TeamName_CodeFile
   rm -rf ~/submit && mkdir ~/submit
   git archive --prefix=$T/ main | tar -x -C ~/submit
   rm ~/submit/$T/agent.md ~/submit/$T/CLAUDE.md ~/submit/$T/changes.md
   cd ~/submit && python3 -m zipfile -c $T.zip $T/
   ```

3. Test the zip like a TA: unzip it into a new folder, create a fresh Python 3.11 env, run
   `pip install -r requirements.txt`, `pytest -q`, then `python -m llmastar.report && python -m llmastar.ci_stats`;
   `outputs/report/` must come out identical.
4. Known leftover, harmless: 18 code comments mention `agent.md` (e.g. "agent.md step 7"), which is not in the zip.
