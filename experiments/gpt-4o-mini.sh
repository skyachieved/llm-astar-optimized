#!/usr/bin/env bash
# Every gpt-4o-mini experiment of the report, in one place (agent.md steps 3, 5, 6 and the Table 1 rows).
#
#   read -rsp "OpenAI key: " OPENAI_API_KEY; echo; export OPENAI_API_KEY
#   bash experiments/gpt-4o-mini.sh all 2>&1 | tee experiments_gpt.log      # or: main | free | ablations | table1 | hard
#
# Every LLM answer is cached in .cache/llm/ (keyed by model, URL, messages and sampling), so a rerun is free and only
# repeats calls that failed. After each LLM run the raw log is checked for failed calls (rate limits, timeouts); if
# any, the same command runs again (at most 3 times), so no result silently contains an abstention caused by an error.
# Defaults are never chosen from these runs: they were fixed on the pilot maps (agent.md Decisions, 2026-11-04).
set -u
cd "$(dirname "$0")/.."
: "${OPENAI_API_KEY:?set OPENAI_API_KEY first (read -rsp ...; export OPENAI_API_KEY)}"
unset OPENAI_BASE_URL
API="--model gpt-4o-mini --base-url https://api.openai.com/v1 --prompt-set gpt"
FAST="--workers 16"   # one short text call per query
QUORUM="--workers 8"  # 4 calls per query, the judge with an image

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

llm() {  # llm <out dir> <args...>: run, then rerun while calls failed
  local out="$1"; shift
  for attempt in 1 2 3; do
    python -m llmastar.run "$@" --out "$out" || return 1
    local bad; bad=$(failed_calls "$out/gpt-4o-mini")
    [ "$bad" = "0" ] && return 0
    echo "!! $bad queries had a failed call; rerunning (attempt $((attempt + 1)) of 3, cached answers are reused)"
  done
  echo "!! failed calls remain after 3 attempts: check the raw log before using this run"
}

report() {  # report <out dir>: summary table and the waypoint split vs weighted A*
  python -m llmastar.summary --model gpt-4o-mini --out "$1"
  python -c "from llmastar.quorumastar.pilot import split_table; print('\n'.join(split_table('$1/gpt-4o-mini')))"
}

main() {  # step 3: the four methods on all 1,000 benchmark queries
  local out=outputs_gpt
  python -m llmastar.run --method astar $API --out $out
  python -m llmastar.run --method wastar --weight 2 $API --out $out
  llm $out --method llmastar $API $FAST
  llm $out --method quorumastar $API $QUORUM
  report $out
  python -m llmastar.figures.fig6_methods --model gpt-4o-mini --out $out
}

free() {  # ablations that reuse the main run's answers (search only) and the other weighted-A* weights
  local out=outputs_gpt
  python -m llmastar.run --method wastar --weight 1.5 $API --out $out
  python -m llmastar.run --method wastar --weight 3 $API --out $out
  llm $out --method quorumastar --no-vision $API $QUORUM
  llm $out --method quorumastar --remove-quorum 0 $API $QUORUM
  llm $out --method quorumastar --stall-k 0 $API $QUORUM
  report $out
}

ablations() {  # step 5: one change at a time, on the first 300 benchmark queries (maps 0-29)
  local out=outputs_gpt_ablation300 lim="--limit 300"
  python -m llmastar.run --method astar $API $lim --out $out
  python -m llmastar.run --method wastar --weight 2 $API $lim --out $out
  llm $out --method llmastar $API $lim $FAST
  llm $out --method quorumastar $API $lim $QUORUM                                     # the default
  llm $out --method quorumastar --views text --add-quorum 1 $API $lim $QUORUM         # one view, no vote
  llm $out --method quorumastar --views corners --add-quorum 1 $API $lim $QUORUM
  llm $out --method quorumastar --views relations --add-quorum 1 $API $lim $QUORUM
  llm $out --method quorumastar --views text,corners,image $API $lim $QUORUM          # image instead of relations
  llm $out --method quorumastar --views text,corners,relations,image $API $lim $QUORUM # four views
  llm $out --method quorumastar --add-quorum 1 $API $lim $QUORUM                      # union instead of a vote
  llm $out --method quorumastar --add-quorum 3 $API $lim $QUORUM                      # unanimity
  llm $out --method quorumastar --no-snap $API $lim $QUORUM
  llm $out --method quorumastar --fewshot shared $API $lim $QUORUM
  llm $out --method quorumastar --fewshot none $API $lim $QUORUM
  llm $out --method quorumastar --cot $API $lim $QUORUM
  llm $out --method quorumastar --roles $API $lim $QUORUM
  report $out
}

table1() {  # Table 1 rows on gpt-4o-mini, as we run them and in the original setup (stop "\n", max_tokens 100)
  for pass in 1 2; do  # the second pass is all cache hits except calls that failed in the first
    python -m llmastar.table1 $API --out outputs_gpt $FAST
    python -m llmastar.table1 $API --out outputs_gpt $FAST --stop-newline --max-tokens 100
  done
}

hard() {  # step 6: generalization to harder generated maps (dataset/generated/, never used for defaults)
  for kind in dense large zigzag; do
    local out=outputs_gpt_$kind data="--dataset dataset/generated/$kind.json"
    python -m llmastar.run --method astar $API $data --out $out
    python -m llmastar.run --method wastar --weight 2 $API $data --out $out
    llm $out --method llmastar $API $data $FAST
    llm $out --method quorumastar $API $data $QUORUM
    report $out
  done
}

case "${1:-all}" in
  main) main ;; free) free ;; ablations) ablations ;; table1) table1 ;; hard) hard ;;
  all) main; free; ablations; table1; hard ;;
  *) echo "usage: bash experiments/gpt-4o-mini.sh [main|free|ablations|table1|hard|all]"; exit 2 ;;
esac
echo "done: $(date)"
