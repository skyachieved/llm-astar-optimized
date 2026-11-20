#!/usr/bin/env bash
# A*, weighted A* (w = 2), LLM-A* and Quorum-A* on GPT-4o mini for any map file(s), with the settings of the report's
# runs (experiments/gpt-4o-mini.sh main). Nothing here depends on a particular map: size and walls come from the file.
#
#   export OPENAI_API_KEY="..."
#   bash experiments/run_maps.sh path/to/maps.json [more.json ...]    # no argument: the benchmark
#
# Another OpenAI-compatible model: LLM_MODEL=<name> LLM_BASE_URL=<url> bash experiments/run_maps.sh ...
# (that provider's key in OPENAI_API_KEY). Results then go to outputs/maps/<name>/<model>/.
#
# A file may hold the benchmark format (dataset/environment_50_30.json), one map, one query or a list of queries.
# Results for <name>.json go to outputs/maps/<name>/gpt-4o-mini/: one CSV per method and summary.md (A* = 100).
# After each LLM run the raw log is checked for failed calls (rate limits, timeouts); if any, the same command runs
# again (at most 3 times, cached answers are reused), so no result silently contains an abstention caused by an error.
set -u
here=$(pwd)
files=()
for f in "$@"; do
  case "$f" in /*) files+=("$f") ;; *) files+=("$here/$f") ;; esac  # paths are relative to where it is run
done
cd "$(dirname "$0")/.."
[ ${#files[@]} -gt 0 ] || files=("$(pwd)/dataset/environment_50_30.json")
: "${OPENAI_API_KEY:?set OPENAI_API_KEY first (export OPENAI_API_KEY=...)}"
unset OPENAI_BASE_URL
MODEL="${LLM_MODEL:-gpt-4o-mini}"
API="--model $MODEL --base-url ${LLM_BASE_URL:-https://api.openai.com/v1} --prompt-set gpt"
SLUG=$(python -c "from llmastar.outputs import model_slug; print(model_slug('$MODEL'))")  # the output folder name
FAST="--workers 16"   # LLM-A*: one request per query
QUORUM="--workers 8"  # Quorum-A*: three requests per query

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
    local bad; bad=$(failed_calls "$out/$SLUG")
    [ "$bad" = "0" ] && return 0
    [ "$attempt" = 3 ] && break
    echo "!! $bad queries had a failed call; rerunning (attempt $((attempt + 1)) of 3, cached answers are reused)"
  done
  echo "!! failed calls remain after 3 attempts: run the same command again"
}

for f in "${files[@]}"; do
  [ -f "$f" ] || { echo "!! no such file: $f"; exit 2; }
  out="outputs/maps/$(basename "$f" .json)"
  echo "== $f -> $out/$SLUG"
  python -m llmastar.run --method astar $API --dataset "$f" --out "$out" || exit 1
  python -m llmastar.run --method wastar --weight 2 $API --dataset "$f" --out "$out" || exit 1
  llm "$out" --method llmastar $API --dataset "$f" $FAST
  llm "$out" --method quorumastar $API --dataset "$f" $QUORUM
  python -m llmastar.summary --model $MODEL --out "$out"
done
echo "done: $(date)"
