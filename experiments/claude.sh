#!/usr/bin/env bash
# Generalization to a frontier reasoning model: Claude Opus 5.5 through Anthropic's OpenAI-compatible endpoint, with
# the defaults fixed on gpt-4o-mini's pilot (nothing is tuned here).
#
# Setting that differs from the other models (Anthropic's API, not a choice of ours): Opus 5.5 always thinks before
# answering, and it rejects temperature, top_p and response_format=json_object. So these runs send none of them
# (--model-sampling): the model samples with its own settings, answers are not deterministic, and the disk cache is
# what makes a rerun reproduce them. max_tokens covers thinking + answer, so it is raised to 16,000 (a limit only).
#
#   read -rsp "Anthropic key: " ANTHROPIC_API_KEY; echo; export ANTHROPIC_API_KEY    # never written to disk
#   bash experiments/claude.sh check                                                 # 20 queries: answers + cost
#   bash experiments/claude.sh main 2>&1 | tee experiments_claude.log                # benchmark, 1,000 queries
#   bash experiments/claude.sh hard 2>&1 | tee -a experiments_claude.log             # dense / large / zigzag
#   (MODEL=claude-fable-5-1 bash experiments/claude.sh check ... for Fable 5.1)
#
# Results: outputs/claude/<model>/ and outputs/claude_{dense,large,zigzag}/<model>/; the check in outputs/claude_check/.
set -u
cd "$(dirname "$0")/.."
: "${ANTHROPIC_API_KEY:?set ANTHROPIC_API_KEY first (read -rsp ...; export ANTHROPIC_API_KEY)}"
MODEL="${MODEL:-claude-opus-5-5}"
URL="${CLAUDE_URL:-https://api.anthropic.com/v1}"
export OPENAI_API_KEY="$ANTHROPIC_API_KEY"  # our client reads OPENAI_API_KEY; this script's processes only
unset OPENAI_BASE_URL
API="--model $MODEL --base-url $URL --prompt-set gpt --model-sampling --max-tokens 16000 --timeout 300"
FAST="--workers 4"
QUORUM="--workers 4"
case "$MODEL" in  # $ per 1M input / output tokens (Anthropic list prices; output includes thinking)
  claude-opus-5-5) PIN=4; POUT=20 ;;
  claude-fable-5-1) PIN=10; POUT=50 ;;
  *) PIN=0; POUT=0 ;;
esac
PRICE="--price-in $PIN --price-out $POUT"

# One test call first: a wrong key or model name fails here, not on every query.
python - "$MODEL" "$URL" <<'PY' || exit 1
import sys
from openai import OpenAI
try:
    r = OpenAI(base_url=sys.argv[2], max_retries=0, timeout=300).chat.completions.create(
        model=sys.argv[1], messages=[{"role": "user", "content": "Say OK."}], max_tokens=2048)
except Exception as e:
    sys.exit(f"!! {sys.argv[1]} did not answer a test call: {e}")
print(f"{sys.argv[1]} answers ({r.choices[0].message.content!r}); starting")
PY

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
    [ "$attempt" = 3 ] && break
    echo "!! $bad queries had a failed call; rerunning (attempt $((attempt + 1)) of 3, cached answers are reused)"
  done
  echo "!! failed calls remain after 3 attempts: check the raw log before using this run"
}

report() {
  python -m llmastar.summary --model "$MODEL" --out "$1"
  python -m llmastar.analysis --dir "$1/$MODEL" $PRICE
}

check() {  # 20 queries: do the answers parse, how many tokens (thinking included), what would the full runs cost?
  local out=outputs/claude_check
  llm $out --method llmastar $API $FAST --limit 20
  llm $out --method quorumastar $API $QUORUM --limit 20
  python - "$out/$MODEL" "$PIN" "$POUT" <<'PY'
import json, sys
from pathlib import Path
from llmastar.analysis import raw_cost
folder, pin, pout = Path(sys.argv[1]), float(sys.argv[2]), float(sys.argv[3])
total = 0
for run in ("llmastar_standard", "quorumastar"):
    rows = [json.loads(l) for l in open(folder / "raw" / f"{run}.jsonl")]
    if run == "llmastar_standard":
        print(run, "parsed", sum(bool(r.get("parse_ok")) for r in rows), "/", len(rows), ";",
              repr((rows[0].get("response") or rows[0].get("llm_error") or "")[:200]))
    else:
        views = [v for r in rows for v in r["views"]]
        print(run, "views answered", sum(not v["abstained"] for v in views), "/", len(views), ";",
              repr((views[0].get("response") or views[0].get("error") or "")[:200]))
    requests, tin, tout = raw_cost(folder / "raw" / f"{run}.jsonl")
    cost = (tin * pin + tout * pout) / 1e6 * 1000
    total += cost
    print(f"  per query: {requests:.2f} requests, {tin:,.0f} prompt + {tout:,.0f} completion tokens (thinking "
          f"included) -> ${cost:,.2f} per 1,000 queries")
print(f"benchmark (1,000 queries, both methods): about ${total:,.0f}; hard maps (300 queries): about "
      f"${0.3 * total:,.0f} or more (their prompts are longer)")
PY
}

main() {  # the comparison on all 1,000 benchmark queries
  local out=outputs/claude
  python -m llmastar.run --method astar $API --out $out
  for w in 1.5 2 3; do python -m llmastar.run --method wastar --weight $w $API --out $out; done
  llm $out --method llmastar $API $FAST
  llm $out --method quorumastar $API $QUORUM
  report $out
  python -m llmastar.figures.fig7_tradeoff --model "$MODEL" --out $out
}

hard() {  # the harder generated maps
  for kind in dense large zigzag; do
    local out=outputs/claude_$kind data="--dataset dataset/generated/$kind.json"
    python -m llmastar.run --method astar $API $data --out $out
    python -m llmastar.run --method wastar --weight 2 $API $data --out $out
    llm $out --method llmastar $API $data $FAST
    llm $out --method quorumastar $API $data $QUORUM
    report $out
  done
}

case "${1:-check}" in
  check) check ;; main) main ;; hard) hard ;; all) main; hard ;;
  *) echo "usage: bash experiments/claude.sh [check|main|hard|all]"; exit 2 ;;
esac
echo "done: $(date)"
