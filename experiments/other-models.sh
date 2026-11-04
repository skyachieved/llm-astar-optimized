#!/usr/bin/env bash
# Generalization to other OpenAI models with the defaults fixed on gpt-4o-mini's pilot (agent.md step 6, "second model").
# Non-reasoning chat models only: reasoning models reject temperature 0, so LLM-A* could not run under the same settings.
#
#   read -rsp "OpenAI key: " OPENAI_API_KEY; echo; export OPENAI_API_KEY
#   bash experiments/other-models.sh gpt-4.1-mini 2>&1 | tee experiments_gpt-4.1-mini.log
#   bash experiments/other-models.sh gpt-4.1-nano 2>&1 | tee experiments_gpt-4.1-nano.log
#
# Results: outputs/other/<model>/ (benchmark, 1,000 queries) and outputs/other_{dense,large,zigzag}/<model>/.
set -u
cd "$(dirname "$0")/.."
: "${OPENAI_API_KEY:?set OPENAI_API_KEY first (read -rsp ...; export OPENAI_API_KEY)}"
MODEL="${1:?usage: bash experiments/other-models.sh <model>}"
unset OPENAI_BASE_URL
API="--model $MODEL --base-url ${OTHER_URL:-https://api.openai.com/v1} --prompt-set gpt"
FAST="--workers 16"
QUORUM="--workers 8"
case "$MODEL" in  # $ per 1M input / output tokens (OpenAI list prices) for the cost table
  gpt-4.1-mini) PRICE="--price-in 0.40 --price-out 1.60" ;;
  gpt-4.1-nano) PRICE="--price-in 0.10 --price-out 0.40" ;;
  gpt-4.1) PRICE="--price-in 2.00 --price-out 8.00" ;;
  *) PRICE="" ;;
esac

failed_calls() {  # number of records with a failed call in the newest raw log under $1
  python - "$1" <<'PY'
import json, sys
from pathlib import Path
logs = sorted(Path(sys.argv[1]).glob("raw/*.jsonl"), key=lambda p: p.stat().st_mtime)
bad = 0
for line in open(logs[-1], encoding="utf-8") if logs else []:
    r = json.loads(line)
    calls = list(r.get("views") or []) + ([r["judge"]] if r.get("judge") else [])
    bad += bool(r.get("llm_error")) or any(c.get("error") for c in calls)
print(bad)
PY
}

llm() {  # llm <out dir> <args...>: run, then rerun while calls failed (cached answers are reused)
  local out="$1"; shift
  for attempt in 1 2 3; do
    python -m llmastar.run "$@" --out "$out" || return 1
    local bad; bad=$(failed_calls "$out/$MODEL")
    [ "$bad" = "0" ] && return 0
    echo "!! $bad queries had a failed call; rerunning (attempt $((attempt + 1)) of 3, cached answers are reused)"
  done
  echo "!! failed calls remain after 3 attempts: check the raw log before using this run"
}

report() {
  python -m llmastar.summary --model "$MODEL" --out "$1"
  python -m llmastar.analysis --dir "$1/$MODEL" $PRICE
}

out=outputs/other
python -m llmastar.run --method astar $API --out $out
for w in 1.5 2 3; do python -m llmastar.run --method wastar --weight $w $API --out $out; done
llm $out --method llmastar $API $FAST
llm $out --method quorumastar $API $QUORUM
report $out
python -m llmastar.figures.fig7_tradeoff --model "$MODEL" --out $out
for kind in dense large zigzag; do
  out=outputs/other_$kind
  data="--dataset dataset/generated/$kind.json"
  python -m llmastar.run --method astar $API $data --out $out
  python -m llmastar.run --method wastar --weight 2 $API $data --out $out
  llm $out --method llmastar $API $data $FAST
  llm $out --method quorumastar $API $data $QUORUM
  report $out
done
echo "done: $(date)"
