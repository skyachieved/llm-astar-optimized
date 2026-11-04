# gpt-4o-mini: results vs. A* (x100, geometric mean)

A* baseline: 100 queries. Ratios use queries where both the run and A* are valid; `valid` is the % of the run's queries with a valid path; `valid_lenient` (LLM-only) inserts a missing start/goal first. `no_targets` (LLM-A*) is the % of queries where no LLM waypoint survived filtering, so the search ran with h = 2 x distance to goal. `paper_*` columns: Table 1 of arXiv 2407.02511 (LLAMA3 rows).

| run | n | operation | storage | length | valid | valid_lenient | no_targets | paper_operation | paper_storage | paper_length | paper_valid |
|---|---|---|---|---|---|---|---|---|---|---|---|
| astar | 100 | 100.00 | 100.00 | 100.00 | 100.00 | - | - | 100.00 | 100.00 | 100.00 | 100.00 |
| llmastar_standard | 100 | 94.94 | 87.98 | 100.35 | 100.00 | - | 18.00 | 44.59 | 64.02 | 102.47 | 100.00 |
| quorumastar | 100 | 95.35 | 85.40 | 100.57 | 100.00 | - | 78.00 | - | - | - | - |
| quorumastar-vision | 100 | 95.42 | 85.48 | 100.65 | 100.00 | - | 95.00 | - | - | - | - |
| wastar-w2 | 100 | 95.42 | 85.49 | 100.66 | 100.00 | - | - | - | - | - | - |
