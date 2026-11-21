# Quorum-A*: Multi-View LLM Consensus for Robust Heuristic Search in Path Planning

We reproduce Table 1 of [LLM-A\*](https://arxiv.org/abs/2407.02511) (Meng et al., 2024) and propose Quorum-A\*: the
same LLM proposes waypoints three times, each time from a differently written map; only waypoints that at least two
answers share are kept, and they are dropped if the search stalls. Built on the
[original LLM-A\* code](https://github.com/SilinMeng0510/llm-astar) (MIT license).

## Setup

Ubuntu 22.04, Python 3.11, no GPU. Run every command from the repository folder.

```bash
conda create -n quorumastar python=3.11 -y
conda activate quorumastar
pip install -r requirements.txt
pytest -q
```

All tests pass without an API key or network; one checks that A\* on the paper's Fig. 1 query gives 859 operations,
802 storage and path length 53.46, as in the paper.

## 1. Check our numbers (no API key, about a minute)

```bash
python -m llmastar.report
python -m llmastar.ci_stats
```

These rebuild the report's tables (`outputs/report/tables.md`) and every 95% confidence interval and standard deviation
(`outputs/report/ci_tables.md`) from the committed per-query results in `outputs/`, for every model; the files come out
identical to the committed ones. Table 1's LLM-only rows and Table 3 are in each run folder's `summary.md` and
`analysis.md`. Do this before section 2, which replaces our GPT-4o mini results with yours.

## 2. Rerun the experiments (GPT-4o mini)

```bash
export OPENAI_API_KEY="paste-your-openai-key-here"
bash experiments/gpt-4o-mini.sh table1      # Table 1: A*, Dynamic WA*, LLM-only and LLM-A* with the paper's 3 prompts
bash experiments/gpt-4o-mini.sh main        # Quorum-A* vs A*, weighted A* and LLM-A*
bash experiments/gpt-4o-mini.sh analyze     # Table 3 and the failure cases, from the cached answers
python -m llmastar.report && python -m llmastar.ci_stats
```

All 1,000 benchmark queries. The scripts print the table (`outputs/gpt/gpt-4o-mini/summary.md`; its `paper_*` columns
are the paper's Llama-3 rows); the last line recomputes the report's tables and CIs from your run. Expected (A\* = 100,
lower is better; report Tables 1 and 2):

| Method | Row | Operations [95% CI] | Storage | Path length |
|---|---|---|---|---|
| LLM-A\*, few-shot | `llmastar_standard` | 50.52 [47.84, 53.35] | 68.38 | 102.95 |
| LLM-A\*, CoT | `llmastar_cot` | 48.53 [46.06, 51.14] | 67.07 | 102.73 |
| LLM-A\*, RePE | `llmastar_repe` | 50.84 [48.16, 53.68] | 68.97 | 102.51 |
| Weighted A\* (w = 2), no LLM | `wastar-w2` | 34.32 [32.74, 35.97] | 56.23 | 102.02 |
| **Quorum-A\*** | `quorumastar` | **33.95 [32.36, 35.61]** | **56.08** | **102.00** |

- A\*, Dynamic WA\* (59.49 / 78.65 / 100.25) and weighted A\* use no LLM and match exactly. GPT-4o mini is not fully
  deterministic even at temperature 0, so the LLM rows can differ slightly. LLM-only paths are valid on 6.3 / 7.2 /
  8.0% of queries (few-shot / CoT / RePE).
- `main` also runs Quorum-A\* with every component switched off (row `quorumastar-vtext-fspaper-nosnap-add1-k0`),
  which gives exactly LLM-A\*'s numbers. `table1` also runs the original code's setting (`stop="\n"`, 100 tokens;
  rows `-stopnl-max100`), which cuts GPT-4o mini's answers before their waypoints (report, Section 4).
- Failed calls (rate limits, timeouts) are rerun automatically; if `!! failed calls remain` appears, run the command
  again. Answers are cached in `.cache/llm/`, so a rerun repeats only the failed calls. The key is never written to
  the cache, the logs or the outputs.
- Cost: `main` is about $1.40; per 1,000 queries, Quorum-A\* costs $0.91 and LLM-A\* $0.45 (report Table 2 and
  Section 5.5).

## 3. Run on your own maps

```bash
bash experiments/run_maps.sh path/to/your_maps.json
```

This runs A\*, weighted A\*, LLM-A\* and Quorum-A\* on every query of the file(s) with the settings of `main` and
prints the table (`outputs/maps/<file name>/`). A file may hold the benchmark format (`dataset/environment_50_30.json`),
one map, one query or a list of queries; nothing in the method depends on a particular map. Another OpenAI-compatible
model: `LLM_MODEL=<name> LLM_BASE_URL=<url> bash experiments/run_maps.sh ...`.

In Python, Quorum-A\* keeps the original interface (`from llmastar.pather import QuorumAStar`):
`QuorumAStar(llm='gpt').searching(query=query)` takes the same query dict as `LLMAStar(llm='gpt', prompt='standard')`
and returns the same keys plus `fallback`. As in the original code, the key may also be set with
`openai.api_key = ...`; `llm=ChatGPT(model=<name>, base_url=<url>)` (`from llmastar.model import ChatGPT`) uses
another model.

## 4. More experiments (same OpenAI key)

```bash
bash experiments/gpt-4o-mini.sh free             # ablations on all 1,000 queries
bash experiments/gpt-4o-mini.sh ablations        # ablations on the first 300 queries
bash experiments/gpt-4o-mini.sh hard             # harder generated maps (dataset/generated/)
bash experiments/other-models.sh gpt-4.1-mini    # other LLMs with the same key; also gpt-4.1
python -m llmastar.report && python -m llmastar.ci_stats
python -m llmastar.figures.fig8_models --report  # report Figure 2 (outputs/figures/)
```

Expected numbers: report Tables 2–3, Figure 2 and Sections 5.4–5.5. `bash experiments/gpt-4o-mini.sh all` runs every
GPT-4o mini command of sections 2 and 4 in one go (all our GPT-4o mini runs together, pilot included, cost about $21
and took about 3.5 hours). Claude Opus 5.5 needs an Anthropic key (`ANTHROPIC_API_KEY`,
`bash experiments/claude.sh main`).

## 5. Runs that need a GPU

Not needed to check our numbers (section 1 rebuilds them). The report's Table 1 also uses the paper's model,
Llama-3-8B-Instruct, served by vLLM in bf16 on one 24 GB GPU (RTX A5000). You need an NVIDIA GPU with at least 24 GB
and a Hugging Face account that has accepted the Llama 3 license on the
[model page](https://huggingface.co/meta-llama/Meta-Llama-3-8B-Instruct) (download about 16 GB).

```bash
conda create -n vllm python=3.11 -y
conda activate vllm
pip install "vllm==0.11.0" "transformers>=4.56,<5"   # vLLM 0.11.0 does not start with transformers 5
hf auth login
hf download meta-llama/Meta-Llama-3-8B-Instruct --local-dir ~/models/Meta-Llama-3-8B-Instruct --exclude "original/*"
CUDA_VISIBLE_DEVICES=0 vllm serve ~/models/Meta-Llama-3-8B-Instruct \
  --served-model-name llama-3-8b-instruct --host 127.0.0.1 --port 8000 \
  --dtype bfloat16 --max-model-len 8192 --gpu-memory-utilization 0.90 --generation-config vllm --seed 0
```

When it prints `Application startup complete`, in a second terminal:

```bash
conda activate quorumastar
OPENAI_API_KEY=dummy python -m llmastar.table1 --jobs 8 --workers 32
```

The results replace ours in `outputs/llama-3-8b-instruct/` (`summary.md`; ours / paper: few-shot 42.99 / 44.59,
CoT 49.63 / 47.60, RePE 69.70 / 64.08 operations; report Table 1). The Qwen2.5-VL-7B runs of report Table 2 use
another server command and `experiments/qwen.sh`; both are in [REPRODUCTION.md](REPRODUCTION.md#setup), which also
explains every setting the paper left open and why some numbers differ.

## Code

| Path | Contents |
|---|---|
| `llmastar/quorumastar/` | Quorum-A\*'s waypoint step: views, canonicalize, vote, checks |
| `llmastar/pather/` | A\*, Dynamic WA\*, LLM-A\* (one hook added) and Quorum-A\*'s stall fallback |
| `llmastar/run.py`, `llmastar/table1.py` | one method over a map file; Table 1 in one command |
| `llmastar/report.py`, `llmastar/ci_stats.py` | the report's tables, CIs and SDs from the committed CSVs |
| `experiments/` | one script per model (every run of the report); `run_maps.sh` for any map file |
| `METHOD.md`, `REPRODUCTION.md` | the method in detail; the Table 1 reproduction and its deviations |
