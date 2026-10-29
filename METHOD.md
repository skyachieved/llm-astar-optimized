# Clear Democratic A* (CDA*): method

Specification as of 2026-10-29. The implementation is pending (agent.md, steps 2–3). Step 8 checks that this file
matches the code. Every default below is a CLI flag of `python -m llmastar.run --method cdastar`.

## 1. Setting: what CDA* plugs into

LLM-A* [1] runs A* [2] on an 8-connected grid, with costs and a collision rule that this repo keeps unchanged:

- The LLM proposes waypoints. The search keeps those that pass `LLMAStar._filter_valid_nodes`: not an obstacle
  cell, and strictly inside the map with a one-cell margin (2 ≤ x ≤ 48 and 2 ≤ y ≤ 28 on the benchmark's 51 × 31 grid).
  Start and goal are added at the ends of this TARGET list.
- f(s) = g(s) + h(s), with h(s) = d(s, goal) + d(s, target), where d is Euclidean distance.
- When the search generates the current target as a neighbor, the next waypoint becomes the target and OPEN is re-keyed.
- If no waypoint survives the filter, target = goal and h = 2 · d(s, goal). This is weighted A* [3] with w = 2. In our
  reproduction it happens on 25.4% of the few-shot queries (`no_targets` in
  `outputs/llama-3-8b-instruct/summary.md`).

The waypoint step is pluggable (`llmastar/waypoints/`: query → waypoint list). CDA* is such a generator plus one
optional search hook (§7). The search loop, f-value and metrics are LLM-A*'s.

## 2. Motivation

| Weakness diagnosed | Component | Source | Flag |
|---|---|---|---|
| One LLM guess can mislead the search | Majority add (≥ 2 of 3) | Self-consistency [4] | `--add-quorum` |
| Same-model voters share mistakes | One view per voter (text / corners / image) | Graph encodings [5]; ensemble diversity [6] | `--views` |
| Single, delete-only vision judge (MMP-A* [7]) | Majority remove (code / vision / support) | MMP-A* [7], extended | `--remove-quorum`, `--no-vision` |
| Bad plans blow up the worst case | Stall fallback to weighted A* | Weighted A* [3] | `--stall-k` (0 = off) |
| Float / never-hit waypoints drag the search | Snap + canonicalize to corner nodes | Own diagnosis | `--no-snap` |

**Majority add.** Self-consistency [4] samples several reasoning paths from one model and takes a majority vote.
CDA* also votes, but its voters see different encodings of the map, which aims for errors that are less correlated.
The ensemble view [6] is that an ensemble improves on its members only to the extent they disagree (ambiguity).
Graph-encoding studies [5] show that the way a graph is written as text changes LLM answers substantially, which is
why the voters get different views.

**Majority remove.** In MMP-A* [7] (arXiv:2601.01910v2), an LLM proposes waypoints and a vision-language model
receives the map images. The VLM acts as a single judge, prompted once per map, and keeps or discards the numbered
waypoints ("Do NOT create any new waypoints"). MMP-A* also damps the waypoint term of the heuristic by α^k (α = 0.7).
CDA* keeps the search's heuristic as it is. It replaces the single judge with a majority of three checks, of which
the vision judge is one.

The stall fallback bounds the cost of a misleading plan. If waypoint guidance stalls, the search continues as
weighted A* with w = 2, exactly what LLM-A* does when it has no waypoints.

## 3. Algorithm

```
CDA*(query):                                         # query = map + start/goal
  # waypoint generation (llmastar/cdastar/)
  answers = concurrently, for v in VIEWS:            # one call each, temperature 0
              v.ask(query, fewshot[v])               # abstains on API error / no image input / parse failure
  lists   = [canonicalize(a.points) if SNAP else a.points  for a in answers if not a.abstained]
  W       = majority_add(lists, ADD_QUORUM)          # ids + support (= number of proposing views)
  if REMOVE_QUORUM > 0:
      W   = majority_remove(W, query, REMOVE_QUORUM, vision = not NO_VISION)
  # search (llmastar/pather/): LLM-A*'s loop, unchanged, plus the stall hook (§7)
  return CDAStar(stall_k=STALL_K).searching(query, waypoints=coordinates(W))
```

`majority_add(lists, q)`:
```
  if len(lists) == 1 and q <= 1: return lists[0]           # identity: order and duplicates kept (needed for §6)
  for each list: drop repeated ids (first occurrence wins); pos(id) = (i + 1) / (n + 1) for the i-th of n ids
  keep ids proposed by >= q lists
  order by mean pos over the proposing lists; ties: first appearance in view order (text, corners, image)
  support(id) = number of lists proposing id
```

`majority_remove(W, query, q, vision)`. Every check sees the same list (one pass, so the order of evaluation
does not matter):
```
  P = [start] + W + [goal]
  for each waypoint w = P[i] (0 < i < len(P) - 1):
     code(w)    = collides(P[i-1], w) and collides(w, P[i+1])     # benchmark.segment_collides = the search's rule
     vision(w)  = w's number is in the vision judge's "remove" list  (abstains -> False)
     support(w) = support(w) < number of views that answered
     remove w if code + vision + support >= q
```

## 4. Components

**4.1 Views** (`--views`, default `text,corners,image`). Each view makes one LLM call per query. The views are
called concurrently, at temperature 0 and `--max-tokens` 2048. Answers are JSON: `{"waypoints": [...]}`, requested
with JSON mode (`response_format={"type": "json_object"}`, `--json-mode`, default on). If the endpoint rejects JSON
mode, the request is resent without it. Parsing tries `json.loads` first (code fences stripped) and falls back to
the last bracketed list in the text (`parse_waypoints` rule).
- **text**: the repo's coordinate format (start, goal, horizontal barriers `[y, x1, x2]`, vertical barriers
  `[x, y1, y2]`). Answer: `[[x, y], ...]`.
- **corners**: a visibility-graph encoding [8]. Corner cells: a horizontal barrier `[y, x1, x2]` gives
  (x1−1, y±1) and (x2+1, y±1); a vertical barrier `[x, y1, y2]` gives (x±1, y1−1) and (x±1, y2+1). Only cells that
  pass the waypoint filter (§1) are kept, deduplicated and numbered 0..N−1 in (x, y) order. The prompt lists the
  nodes with their coordinates, plus S (start) and G (goal), and for each node the nodes it sees, i.e. those whose
  segment has no `segment_collides`. It contains no barrier list. Answer: node ids `[3, 7, ...]`, mapped back to cells.
- **image**: a PNG of the map (matplotlib Agg, 20 px per cell, x and y axes labeled every 5 cells, grid every
  cell, y pointing up, barriers drawn as thick black segments, S and G marked). Answer: `[[x, y], ...]`. Zero-shot.
  If the model has no image input, the request fails and the view abstains (logged).
- A view **abstains** if its call errors or its answer has no parsable list. An abstaining view casts no vote.
- `--cot` (off): each view first gives brief reasoning, then the JSON answer. `--roles` (off): each view gets its own
  system role. Both exist for the ablations in step 5.

**4.2 Few-shot** (`--fewshot`, default `per-view`; `--n-shots` 3; `--fewshot-seed` 0). Examples come from a pool of
self-generated maps (`llmastar/cdastar/fewshot.py`) and never from the evaluation maps. The pool uses the same grid
size and barrier format, with generator parameters fixed a priori (no fit to the benchmark's statistics). A pool map
is accepted only if (a) its straight start–goal segment collides, and (b) its gold waypoints all snap to corner
nodes. Gold waypoints: the A* path is string-pulled (greedy line-of-sight shortcutting with `segment_collides`), and
its interior corners are canonicalized (§4.3). Each example is written in its view's format.
- `per-view`: view k gets pool examples [3k, 3k+3), so the views share no example map.
- `shared`: every view gets examples [0, 3), each in its own format.
- `none`: all views zero-shot.
- `paper`: the **text** view sends exactly the messages of LLM-A*'s `PromptWaypointGenerator` (`--prompt`,
  `--prompt-set`), with no JSON mode and the original parser, so its waypoints pass through unchanged. The other
  views use `per-view` examples.
- The image view is always zero-shot.

**4.3 Canonicalization** (on by default; `--no-snap` turns it off). For every proposed point:
1. Round to the nearest cell. If the cell fails the waypoint filter, take the filter-passing cell within Chebyshev
   distance `--snap-cell-radius` [2] that is closest (Euclidean) to the proposed point. Ties go to the smallest (x, y).
   If there is none, the point is dropped (logged).
2. If a corner node lies within Euclidean distance `--snap-corner-radius` [3], replace the cell with the nearest one
   (ties go to the lower node id). Otherwise the cell is its own id.
3. Consecutive duplicates collapse.

The canonical id of a waypoint is its cell, so votes from coordinate views and node-id views compare directly.
With `--no-snap`, points are used as proposed (floats included). Corner ids still map to their cells.

**4.4 Majority add** (`--add-quorum` [2]); see §3. With a single answering view and quorum 1, it is the identity.

**4.5 Majority remove** (`--remove-quorum` [2], 0 = off; `--no-vision` drops check (b)); see §3.
- The **vision judge** is one call per query. It gets the §4.1 image with the post-add waypoints drawn as numbers 1..n,
  connected by a dashed line from S to G. Prompt: remove waypoints that lie on or against a wall, or whose route
  crosses a wall or leads into a dead end; never add or move any. Answer: `{"remove": [2, 5]}`.
- If the judge abstains (error, no image input, unparsable answer), it objects to nothing.
- "Number of views that answered" counts the views that did not abstain. If the image view abstains, an id backed by
  both text views is therefore fully supported.

**4.6 Search**: `CDAStar(LLMAStar)`. The loop and f-value are inherited and unchanged.

**4.7 Stall fallback** (`--stall-k` [2], 0 = off; `--stall-min` [20]). A target becomes active at the start, or when
the search switches to it. Its budget is `k × max(stall_min, |ax − tx| + |ay − ty|)`, where a is the node being
expanded when the target became active (the start for the first target) and t is the target. When the pops since
activation exceed the budget and the target is not the goal, the remaining waypoints are dropped and target = goal.
OPEN is then re-keyed with `_update_queue` (the same as on a target switch), and the search continues as weighted
A* with w = 2. The fallback fires at most once per query, and it is logged with the pop count and the dropped waypoints.

## 5. Defaults and flags

| Flag | Default | Meaning |
|---|---|---|
| `--views` | `text,corners,image` | voters, one call each |
| `--fewshot` | `per-view` | `per-view` / `shared` / `none` / `paper` |
| `--n-shots`, `--fewshot-seed` | 3, 0 | examples per view; pool seed |
| `--cot`, `--roles` | off | CoT answers; per-view system roles |
| `--json-mode / --no-json-mode` | on | `response_format=json_object` (not sent in `paper` mode) |
| `--snap / --no-snap` | on | canonicalization (§4.3) |
| `--snap-cell-radius`, `--snap-corner-radius` | 2, 3 | §4.3 |
| `--add-quorum` | 2 | §4.4 |
| `--remove-quorum` | 2 | §4.5; 0 = no pruning |
| `--vision / --no-vision` | on | vision judge (check b) |
| `--stall-k`, `--stall-min` | 2, 20 | §4.7; `--stall-k 0` = off |
| `--temperature`, `--max-tokens` | 0, 2048 | sampling (existing flags) |
| `--model`, `--base-url`, `--api-key` | `llama-3-8b-instruct`, `$OPENAI_BASE_URL` or `http://127.0.0.1:8000/v1`, `$OPENAI_API_KEY` | endpoint; the key is never logged or cached |

The run name is `cdastar` for the defaults; non-default flags are appended in a fixed order as `-<variant>`, as
for `dwastar` (e.g. `cdastar-novision`).

## 6. "All off" reproduces LLM-A*

`--method cdastar --views text --fewshot paper --add-quorum 1 --no-vision --no-snap --stall-k 0`
- One call, with the same messages and sampling as LLM-A*, hence the same cache key: the run reuses the cached
  LLM-A* answers.
- The original parser runs, voting is the identity (§4.4), and pruning cannot fire. One answering view means
  support never objects and vision is off, so the code check alone stays below quorum 2.
- The search is LLM-A*'s loop with an inert hook.

Tests in step 2 (mock LLM, no network): the messages and the cache key equal `PromptWaypointGenerator`'s, and
operation, storage, length, path and `llm_output` equal `LLMAStar`'s on a fixed set of queries. Step 3 adds an
end-to-end check that the run sends 0 new requests and that its CSV metrics equal `llmastar_standard.csv`.

## 7. The search hook

The only change to `LLMAStar.searching` is one call right after a state is popped and closed:

```python
_, s = heapq.heappop(self.OPEN)
self.CLOSED.append(s)
self.closed_set.add(s)
self._after_pop(s)          # new: LLMAStar._after_pop does nothing
```

`CDAStar` overrides `_after_pop` (stall check, §4.7) and `_update_target` (it calls the parent's method, then
records the activation pop and node). With `--stall-k 0`, `_after_pop` returns immediately. A test checks that
operation, storage and length match `LLMAStar` on a fixed set of maps, and `tests/test_astar.py` keeps checking
859 / 802 / 53.46.

## 8. Per-query log

`outputs/<model>/raw/<run>.jsonl` (git-ignored), one record per query:
- per view: messages hash, raw response, parsed points, canonical cells, abstained and error, usage
  (prompt and completion tokens), latency, cache hit;
- votes (cell → proposing views, mean position), the post-add list, and per waypoint the code / vision / support
  objections and whether it was removed;
- the vision judge's call record (as for a view) and its `remove` ids;
- final waypoints, `parse_ok`, totals (calls, prompt tokens, completion tokens, wall time).

`outputs/<model>/<run>.csv` gains `fallback`, `fallback_pop`, `calls`, `prompt_tokens`, `completion_tokens` and
`llm_seconds`. These are blank for runs where they don't apply.

## 9. Baselines and model

- **A\*** and **weighted A\*** with w ∈ {1.5, 2, 3}: f = g + w · h. Implemented as `DWAStar(w0=w, decay=1)`, a constant
  weight, so no new search code is needed. It runs as `--method wastar --weight W`, with run names `wastar-w1.5`,
  `wastar-w2` and `wastar-w3`.
- **LLM-A\*** (`--method llmastar --prompt standard|cot|repe`), rerun on the CDA* model.
- **Model:** Qwen2.5-VL-7B-Instruct [9] (bf16, vLLM 0.11.0) for all views, the vision judge and the LLM-A* baseline.
  Llama-3-8B-Instruct stays for the Table 1 reproduction only. GPT-4o mini (`--model gpt-4o-mini --base-url
  https://api.openai.com/v1`) comes later as the grading model.

## 10. Implementation map (proposed)

```
llmastar/cdastar/
  __init__.py     CDAStarGenerator (WaypointGenerator); registered as "cdastar" in llmastar/waypoints/REGISTRY
  config.py       CDAConfig dataclass with every default above; add_cli_args(parser) / from_args(args); run-name variant
  geometry.py     waypoint filter (mirrors LLMAStar._filter_valid_nodes), corner nodes, visibility, string pulling
  render.py       map -> PNG bytes (optionally with numbered waypoints)
  views.py        TextView, CornersView, ImageView, PaperTextView: messages(query, examples) and parse(text)
  parsing.py      JSON answer parsing with regex fallback
  fewshot.py      seeded pool of generated maps, solved by A*, gold waypoints
  canonical.py    snap + canonicalize (§4.3)
  voting.py       majority add (§4.4)
  pruning.py      code / vision / support checks, majority remove (§4.5)
llmastar/pather/llm_a_star/llm_a_star.py   + no-op _after_pop hook (§7), the only change to the search
llmastar/pather/cda_a_star/cda_a_star.py   CDAStar(LLMAStar): stall fallback
llmastar/model/chatgpt.py                  + api_key, image parts in messages (cache stores an image hash,
                                             not the bytes), JSON mode with fallback, errors returned, not raised
llmastar/run.py                            + --method cdastar / wastar, CDA* flags, --weight, --api-key;
                                             LLM failures become logged rows, never a crash
tests/test_cdastar_*.py                    mock-LLM unit tests per module + the §6 / §7 equivalence tests
```

## References

1. S. Meng, Y. Wang, C.-F. Yang, N. Peng, K.-W. Chang. *LLM-A\*: Large Language Model Enhanced Incremental Heuristic
   Search on Path Planning.* arXiv:2407.02511, 2024.
2. P. E. Hart, N. J. Nilsson, B. Raphael. *A Formal Basis for the Heuristic Determination of Minimum Cost Paths.*
   IEEE Trans. Systems Science and Cybernetics 4(2):100–107, 1968.
3. I. Pohl. *Heuristic Search Viewed as Path Finding in a Graph.* Artificial Intelligence 1(3–4):193–204, 1970.
4. X. Wang, J. Wei, D. Schuurmans, Q. Le, E. Chi, S. Narang, A. Chowdhery, D. Zhou. *Self-Consistency Improves Chain
   of Thought Reasoning in Language Models.* ICLR 2023 (arXiv:2203.11171).
5. B. Fatemi, J. Halcrow, B. Perozzi. *Talk like a Graph: Encoding Graphs for Large Language Models.* ICLR 2024
   (arXiv:2310.04560).
6. A. Krogh, J. Vedelsby. *Neural Network Ensembles, Cross Validation, and Active Learning.* NIPS 7, 231–238, 1995.
7. M. H. Ha, K. L. Ta, H. Phan, T. Doan, T. Dao, D. Tran, H. T. T. Binh. *MMP-A\*: Multimodal Perception Enhanced
   Incremental Heuristic Search on Path Planning.* arXiv:2601.01910 (v2, 22 Jan 2026). Code:
   https://github.com/langkhachhoha/MMP-ASTAR
8. T. Lozano-Pérez, M. A. Wesley. *An Algorithm for Planning Collision-Free Paths among Polyhedral Obstacles.*
   Communications of the ACM 22(10):560–570, 1979.
9. S. Bai et al. *Qwen2.5-VL Technical Report.* arXiv:2502.13923, 2025.
