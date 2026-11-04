#!/usr/bin/env bash
# Generalization to a second, open model: Qwen2.5-VL-7B-Instruct served by vLLM (agent.md step 6, "second model").
# Defaults were fixed on gpt-4o-mini's pilot and are not changed here.
#
#   1. In one tmux window, serve the model (GPUs that are free, e.g. 6,7; stop it with Ctrl+c when done):
#        source /raid/slpr/ymkwon/envs/vllm/bin/activate
#        CUDA_DEVICE_ORDER=PCI_BUS_ID CUDA_VISIBLE_DEVICES=6,7 vllm serve /raid/slpr/ymkwon/models/Qwen2.5-VL-7B-Instruct \
#          --served-model-name qwen2.5-vl-7b-instruct --host 127.0.0.1 --port 8012 --dtype float16 \
#          --tensor-parallel-size 2 --max-model-len 16384 --gpu-memory-utilization 0.90 --max-num-seqs 32 \
#          --enforce-eager --limit-mm-per-prompt '{"image": 1}' --generation-config vllm --seed 0
#   2. In another window (repository folder, .venv), with a dummy key (never the OpenAI key):
#        OPENAI_API_KEY=dummy bash experiments/qwen.sh check     # 10 queries: answers parse? (fp16 sanity check)
#        OPENAI_API_KEY=dummy bash experiments/qwen.sh all 2>&1 | tee experiments_qwen.log
#
# Prompts: LLM-A* uses the paper's few-shot dialogue as chat turns (--prompt-set llama), as in our Llama-3 Table 1.
set -u
cd "$(dirname "$0")/.."
: "${OPENAI_API_KEY:?set OPENAI_API_KEY=dummy (the local server ignores it)}"
MODEL=qwen2.5-vl-7b-instruct
API="--model $MODEL --base-url ${QWEN_URL:-http://127.0.0.1:8012/v1} --prompt-set llama"
FAST="--workers 32"
QUORUM="--workers 16"

failed_calls() {  # number of records with a failed call in the newest raw log under $1
  python - "$1" <<'EOF'
import json, sys
from pathlib import Path
logs = sorted(Path(sys.argv[1]).glob("raw/*.jsonl"), key=lambda p: p.stat().st_mtime)
bad = 0
for line in open(logs[-1], encoding="utf-8") if logs else []:
    r = json.loads(line)
    calls = list(r.get("views") or []) + ([r["judge"]] if r.get("judge") else [])
    bad += bool(r.get("llm_error")) or any(c.get("error") for c in calls)
print(bad)
EOF
}

llm() {  # llm <out dir> <args...>: run, then rerun while calls failed (cached answers are reused)
  local out="$1"; shift
  for attempt in 1 2 3; do
    python -m llmastar.run "$@" --out "$out" || return 1
    local bad; bad=$(failed_calls "$out/$MODEL")
    [ "$bad" = "0" ] && return 0
    echo "!! $bad queries had a failed call; rerunning (attempt $((attempt + 1)) of 3)"
  done
  echo "!! failed calls remain after 3 attempts: check the raw log before using this run"
}

report() {
  python -m llmastar.summary --model $MODEL --out "$1"
  python -c "from llmastar.quorumastar.pilot import split_table; print('\n'.join(split_table('$1/$MODEL')))"
  python -m llmastar.analysis --dir "$1/$MODEL"
}

check() {  # does the fp16 V100 server answer in a parsable format? (10 queries, prints the first answers)
  local out=outputs/qwen_check
  llm $out --method llmastar $API $FAST --limit 10
  llm $out --method quorumastar $API $QUORUM --limit 10
  python - <<EOF
import json
for name in ("llmastar_standard", "quorumastar"):
    rows = [json.loads(l) for l in open("$out/$MODEL/raw/" + name + ".jsonl")]
    if name == "llmastar_standard":
        print(name, "parsed", sum(r["parse_ok"] for r in rows), "/ 10;", repr(rows[0]["response"][:300]))
    else:
        views = [v for r in rows for v in r["views"]]
        print(name, "views answered", sum(not v["abstained"] for v in views), "/", len(views), ";",
              repr(views[0]["response"][:200]))
EOF
}

main() {  # the comparison on all 1,000 benchmark queries
  local out=outputs/qwen
  python -m llmastar.run --method astar $API --out $out
  for w in 1.5 2 3; do python -m llmastar.run --method wastar --weight $w $API --out $out; done
  llm $out --method llmastar $API $FAST
  llm $out --method quorumastar $API $QUORUM
  llm $out --method quorumastar --views text --fewshot paper --add-quorum 1 --no-snap --stall-k 0 $API $FAST  # all off
  report $out
  python -m llmastar.figures.fig7_tradeoff --model $MODEL --out $out
}

hard() {  # the harder generated maps
  for kind in dense large zigzag; do
    local out=outputs/qwen_$kind data="--dataset dataset/generated/$kind.json"
    python -m llmastar.run --method astar $API $data --out $out
    python -m llmastar.run --method wastar --weight 2 $API $data --out $out
    llm $out --method llmastar $API $data $FAST
    llm $out --method quorumastar $API $data $QUORUM
    report $out
  done
}

case "${1:-all}" in
  check) check ;; main) main ;; hard) hard ;; all) main; hard ;;
  *) echo "usage: OPENAI_API_KEY=dummy bash experiments/qwen.sh [check|main|hard|all]"; exit 2 ;;
esac
echo "done: $(date)"
