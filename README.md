# Quorum-A*: Multi-View LLM Consensus for Robust Heuristic Search in Path Planning

This repository reproduces the LLM-A\* rows of Table 1 of [LLM-A\*](https://arxiv.org/abs/2407.02511)
(Meng et al., 2024) and runs our method, Quorum-A\*. Quorum-A\* asks the same LLM for waypoints three times, each
time with the map written differently, keeps only the waypoints that at least two answers propose, and drops them
if the search stalls; the LLM-A\* search itself is unchanged. The code builds on the
[original LLM-A\* repository](https://github.com/SilinMeng0510/llm-astar) (MIT license, see `LICENSE`).

Sections 1–6 need only Ubuntu 22.04, Python 3.11, `requirements.txt` and a GPT-4o mini API key, no GPU. Section 7
adds other API models and section 8 the runs that need a GPU. Run the sections in order, in one terminal, from the
repository folder. The only line to edit is the API key in section 1.

## 1. Setup

```bash
conda create -n quorumastar python=3.11 -y
conda activate quorumastar
pip install -r requirements.txt
pytest -q
export OPENAI_API_KEY="paste-your-openai-key-here"
```

- All tests pass without an API key or network. One of them checks that A\* on the paper's Fig. 1 query gives 859
  operations, 802 storage and path length 53.46, as in the paper.
- Sections 2–6 use GPT-4o mini through the OpenAI API. The key is never written to the cache, the logs or the
  outputs; `openai.api_key` in Python also works, as in the original repository.
- Every LLM answer is cached in `.cache/llm/` (empty in a fresh copy), so running a command again sends only the
  requests that failed.

## 2. Table 1 reproduction (GPT-4o mini)

```bash
python -m llmastar.table1 --model gpt-4o-mini --base-url https://api.openai.com/v1 --prompt-set gpt
```

This runs A\*, Dynamic WA\*, and LLM-A\* and LLM-only with the paper's three prompts on all 1,000 benchmark
queries (100 maps × 10 start/goal pairs), prints the table and writes `outputs/gpt-4o-mini/summary.md`.
Expected, relative to A\* (= 100; lower is better), from our run (`outputs/gpt/gpt-4o-mini/summary.md`, report
Table 1):

| LLM-A\* prompt (row) | Operations [95% CI] | Storage | Path length |
|---|---|---|---|
| few-shot (`llmastar_standard`) | 50.52 [47.84, 53.35] | 68.38 | 102.95 |
| CoT (`llmastar_cot`) | 48.53 [46.06, 51.14] | 67.07 | 102.73 |
| RePE (`llmastar_repe`) | 50.84 [48.16, 53.68] | 68.97 | 102.51 |

- Every path is valid. A\* and Dynamic WA\* (`dwastar`, 59.49 / 78.65 / 100.25) use no LLM and match exactly.
  The `paper_*` columns of the printed table are the paper's Llama 3 rows.
- GPT-4o mini is not fully deterministic even at temperature 0, so the LLM-A\* rows of a rerun can differ slightly
  from ours.
- We send no stop sequence and allow 2,048 output tokens. The original repository's `stop="\n"` with 100 tokens cuts
  every GPT-4o mini answer before its waypoints (report, Section 4); `--stop-newline --max-tokens 100` restores it.
- The report's Table 1 also uses the paper's model, Llama-3-8B-Instruct, which needs a GPU: section 8a.

## 3. Quorum-A\* on GPT-4o mini

```bash
bash experiments/gpt-4o-mini.sh main
python -m llmastar.report
python -m llmastar.ci_stats
```

The script runs A\*, weighted A\* (w = 2), LLM-A\* (few-shot; it reuses the answers of section 2) and Quorum-A\*
(3 requests per query) on the 1,000 queries. It also checks that Quorum-A\* with every component switched off gives
exactly LLM-A\*'s results. It writes `outputs/gpt/gpt-4o-mini/` and prints the table; the last two commands
recompute the report's tables and tests from your rerun. Expected (A\* = 100; report Table 2):

| Method (row) | Operations [95% CI] | Storage | Path length |
|---|---|---|---|
| Weighted A\* (w = 2), no LLM (`wastar-w2`) | 34.32 [32.74, 35.97] | 56.23 | 102.02 |
| LLM-A\* (`llmastar_standard`) | 50.52 [47.84, 53.35] | 68.38 | 102.95 |
| **Quorum-A\*** (`quorumastar`) | **33.95 [32.36, 35.61]** | **56.08** | **102.00** |
| Quorum-A\*, all components off (`quorumastar-vtext-fspaper-nosnap-add1-k0`) | same as LLM-A\* | | |

- Weighted A\* (w = 2) is LLM-A\* without waypoints and matches exactly.
- The script reruns any command whose log shows a failed call (rate limit, timeout). If it prints
  `!! failed calls remain`, run it again.
- `bash experiments/gpt-4o-mini.sh all` runs sections 3, 4 and 6 and the Table 1 variants in one go.
- Before any rerun, `python -m llmastar.report` and `python -m llmastar.ci_stats` alone rebuild the report's
  tables, confidence intervals and standard deviations exactly from our committed per-query results, for every
  model, with no API key and no GPU (report, Section 4, "Reproducibility"). This section's run replaces our
  GPT-4o mini results with yours.

## 4. Ablations (GPT-4o mini)

Each component of Quorum-A\* removed one at a time.

```bash
bash experiments/gpt-4o-mini.sh free        # all 1,000 queries
bash experiments/gpt-4o-mini.sh ablations   # first 300 queries
python -m llmastar.report
python -m llmastar.ci_stats
```

Expected operations (A\* = 100), each against the default with a paired Wilcoxon test (report, Section 5.4):

| Queries | Variant | Operations | p |
|---|---|---|---|
| 1,000 | default | 33.95 | |
| 1,000 | no stall fallback | 35.32 | < 0.001 |
| 1,000 | no removal step | 34.05 | 0.13 |
| 1,000 | + vision judge | 34.10 | 0.54 |
| 300 | default | 33.18 | |
| 300 | the three answers without a vote (union) | 41.61 | < 0.001 |
| 300 | text view alone / corners alone / relations alone | 36.34 / 37.41 / 36.54 | < 0.001 / 0.015 / 0.0036 |
| 300 | no few-shot examples | 35.96 | 0.0012 |
| 300 | LLM-A\* / weighted A\* (w = 2), for reference | 48.31 / 33.19 | |

`outputs/report/tables.md` (section 4) lists every variant (unanimity, image view, four views, no snapping, shared
few-shot examples, CoT, roles), none of which differs significantly from the default.

## 5. Your own maps

Nothing in the method depends on a particular map: the grid size and the walls come from the input. Quorum-A\*
keeps the original repository's input and output format: in Python,
`from llmastar.pather import QuorumAStar` and `QuorumAStar(llm='gpt').searching(query=query, filepath='quorum.png')`
take the same `query` dict as the original's `LLMAStar(llm='gpt', prompt='standard').searching(...)` and return the
same keys (`operation`, `storage`, `length`, `valid`, `path`, `visited`, `llm_output`) plus `fallback`.

To run whole map files (A\*, weighted A\* with w = 2, LLM-A\* and Quorum-A\*, with the settings of section 3):

```bash
bash experiments/run_maps.sh path/to/your_maps.json      # one or more files; no argument runs the benchmark
```

- A map file may hold the benchmark format of `dataset/environment_50_30.json` (a list of maps, each with `id`,
  `range_x`, `range_y`, `horizontal_barriers`, `vertical_barriers` and `start_goal` pairs), a single map, a single
  query (`start`, `goal`, `range_x`, `range_y` and the two barrier lists) or a list of queries. The PNG pictures of
  the maps are not needed.
- Results for `your_maps.json` go to `outputs/maps/your_maps/gpt-4o-mini/`: one CSV per method with one row per
  query, and `summary.md` (A\* = 100; its `paper_*` columns refer to the benchmark only).
- A failed LLM call never stops a run: that query runs without waypoints and the `llm_error` column says why.
  Calls time out after 60 s and are retried up to 3 times, and the script reruns any failed call.
- Another OpenAI-compatible model: put that provider's key in `OPENAI_API_KEY` and run
  `LLM_MODEL=<model name> LLM_BASE_URL=<its URL> bash experiments/run_maps.sh your_maps.json` (or pass `--model`
  and `--base-url` to `llmastar.run`). `experiments/gpt-4o-mini.sh` and `llm="gpt"` always use GPT-4o mini.

## 6. Additional credit: harder maps (GPT-4o mini)

```bash
bash experiments/gpt-4o-mini.sh hard
python -m llmastar.report
```

The maps are committed in `dataset/generated/` (100 each, same format as the benchmark, made by
`python -m llmastar.generate_maps` with a fixed seed and never used to choose a setting): `dense` (more walls),
`large` (101 × 61) and `zigzag` (winding corridors). Expected operations (A\* = 100; report Figure 2):

| Maps | Weighted A\* (w = 2) | LLM-A\* | Quorum-A\* |
|---|---|---|---|
| dense | 26.90 | 53.84 | 27.01 |
| large | 20.10 | 48.17 | 20.16 |
| zigzag | 95.42 | 94.94 | 95.35 |

## 7. Additional credit: other LLMs

Same defaults as GPT-4o mini; nothing is tuned per model. Expected operations (A\* = 100, [95% CI]); weighted A\*
(w = 2) is 34.32 for every model.

| Model | LLM-A\* | Quorum-A\* | Needs |
|---|---|---|---|
| GPT-4.1 mini | 42.21 [40.05, 44.47] | 33.39 [31.85, 35.00] | the OpenAI key |
| GPT-4.1 | 39.90 [37.92, 41.97] | 33.53 [31.97, 35.16] | the OpenAI key |
| Claude Opus 5.5 (closed) | 30.75 [29.26, 32.31] | 30.04 [28.62, 31.52] | an Anthropic key |
| Qwen2.5-VL-7B (open) | 38.03 [36.17, 39.99] | 35.52 [33.88, 37.24] | a GPU (section 8b) |
| Llama-3-8B-Instruct (open; Table 1) | 42.99 [40.91, 45.19] | not run | a GPU (section 8a) |

`python -m llmastar.figures.fig8_models --report` draws the report's model figure from the committed results.

**GPT-4.1 mini and GPT-4.1.** Each command runs the benchmark and the harder maps.

```bash
bash experiments/other-models.sh gpt-4.1-mini
bash experiments/other-models.sh gpt-4.1
```

**Claude Opus 5.5 (closed model).** It needs an Anthropic API key and runs with the model's own sampling (it
thinks before answering and its API does not accept a temperature), so a rerun's answers differ from ours.

```bash
export ANTHROPIC_API_KEY="paste-your-anthropic-key-here"
bash experiments/claude.sh check   # 20 queries: do the answers parse
bash experiments/claude.sh main    # 1,000 queries
```

## 8. Runs that need a GPU

The course environment has no GPU. These runs are not needed to check our numbers: `python -m llmastar.report`
and `python -m llmastar.ci_stats` rebuild them from the committed per-query results with no GPU and no API key
(section 3). To rerun them, vLLM serves the model in its own conda env. One-time setup:

```bash
conda create -n vllm python=3.11 -y
conda activate vllm
pip install "vllm==0.11.0" "transformers>=4.56,<5"   # vLLM 0.11.0 does not start with transformers 5
```

### 8a. Table 1 with Llama-3-8B-Instruct, the paper's model

The report's Table 1 uses Llama-3-8B-Instruct, served by vLLM in bf16 on one 24 GB GPU (RTX A5000). This needs an
NVIDIA GPU with at least 24 GB and a Hugging Face account that has accepted the Llama 3 license on the
[model page](https://huggingface.co/meta-llama/Meta-Llama-3-8B-Instruct) (download about 16 GB):

```bash
conda activate vllm
hf auth login
hf download meta-llama/Meta-Llama-3-8B-Instruct --local-dir ~/models/Meta-Llama-3-8B-Instruct --exclude "original/*"
CUDA_VISIBLE_DEVICES=0 vllm serve ~/models/Meta-Llama-3-8B-Instruct \
  --served-model-name llama-3-8b-instruct --host 127.0.0.1 --port 8000 \
  --dtype bfloat16 --max-model-len 8192 --gpu-memory-utilization 0.90 \
  --generation-config vllm --seed 0
```

When it prints `Application startup complete`, in a second terminal:

```bash
conda activate quorumastar
OPENAI_API_KEY=dummy python -m llmastar.table1 --jobs 8 --workers 32
OPENAI_API_KEY=dummy python -m llmastar.scale --jobs 8   # Fig. 3 data
python -m llmastar.figures
```

The LLM calls took about 8 minutes on the A5000. Results go to `outputs/llama-3-8b-instruct/` and replace the
committed ones (copy that folder first to keep them). Ours / paper, A\* = 100:

| LLM-A\* prompt | Operations | Storage | Path length |
|---|---|---|---|
| few-shot | 42.99 / 44.59 | 62.83 / 64.02 | 102.27 / 102.47 |
| CoT | 49.63 / 47.60 | 68.06 / 66.27 | 102.45 / 102.46 |
| RePE | 69.70 / 64.08 | 84.31 / 80.19 | 102.42 / 102.54 |

[REPRODUCTION.md](REPRODUCTION.md) explains every setting the paper left open and why some numbers differ.

### 8b. Qwen2.5-VL-7B-Instruct (other LLMs, section 7)

We served it in fp16 on two 16 GB V100s (download about 17 GB):

```bash
conda activate vllm
hf download Qwen/Qwen2.5-VL-7B-Instruct --local-dir ~/models/Qwen2.5-VL-7B-Instruct
CUDA_VISIBLE_DEVICES=0,1 vllm serve ~/models/Qwen2.5-VL-7B-Instruct \
  --served-model-name qwen2.5-vl-7b-instruct --host 127.0.0.1 --port 8012 --dtype float16 \
  --tensor-parallel-size 2 --max-model-len 16384 --gpu-memory-utilization 0.90 --max-num-seqs 32 \
  --enforce-eager --limit-mm-per-prompt '{"image": 1}' --generation-config vllm --seed 0
```

When it prints `Application startup complete`, in a second terminal:

```bash
conda activate quorumastar
OPENAI_API_KEY=dummy bash experiments/qwen.sh main     # benchmark; `all` adds the pilot and the harder maps
```

Results go to `outputs/qwen/qwen2.5-vl-7b-instruct/`; the run names end in `-max512` because Qwen runs with
max_tokens 512 (report, Section 4). Other GPUs or bf16 change some answers (report, Section 5.1). On one GPU with
at least 24 GB, `CUDA_VISIBLE_DEVICES=0` without `--tensor-parallel-size 2` should work, but we did not test it.

## 9. Where the code is

| Path | What it holds |
|---|---|
| `llmastar/quorumastar/` | Quorum-A\*'s waypoint step: views, canonicalize, vote, checks |
| `llmastar/pather/quorum_a_star/` | the stall fallback |
| `llmastar/pather/llm_a_star/` | LLM-A\*'s search (one hook added) |
| `llmastar/run.py` | one method over a map file, to `outputs/<model>/<run>.csv` |
| `llmastar/table1.py` | Table 1 in one command |
| `llmastar/report.py`, `llmastar/ci_stats.py` | the report's tables, CIs and SDs from the committed CSVs |
| `experiments/` | one script per model (every run of the report); `run_maps.sh` for any map file |
| `METHOD.md`, `REPRODUCTION.md` | the method in detail; deviations from the paper |
