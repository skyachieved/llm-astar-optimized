# claude-opus-5-5: results vs. A* (x100, geometric mean)

A* baseline: 1000 queries. Ratios use queries where both the run and A* are valid; `valid` is the % of the run's queries with a valid path; `valid_lenient` (LLM-only) inserts a missing start/goal first. `no_targets` (LLM-A*) is the % of queries where no LLM waypoint survived filtering, so the search ran with h = 2 x distance to goal. `paper_*` columns: Table 1 of arXiv 2407.02511 (LLAMA3 rows).

| run | n | operation | storage | length | valid | valid_lenient | no_targets | paper_operation | paper_storage | paper_length | paper_valid |
|---|---|---|---|---|---|---|---|---|---|---|---|
| astar | 1000 | 100.00 | 100.00 | 100.00 | 100.00 | - | - | 100.00 | 100.00 | 100.00 | 100.00 |
| llmastar_standard | 1000 | 30.75 | 54.05 | 101.02 | 100.00 | - | 11.80 | 44.59 | 64.02 | 102.47 | 100.00 |
| quorumastar | 1000 | 30.04 | 53.55 | 101.23 | 100.00 | - | 21.60 | - | - | - | - |
| wastar-w1.5 | 1000 | 40.06 | 60.26 | 100.74 | 100.00 | - | - | - | - | - | - |
| wastar-w2 | 1000 | 34.32 | 56.23 | 102.02 | 100.00 | - | - | - | - | - | - |
| wastar-w3 | 1000 | 29.92 | 53.26 | 103.68 | 100.00 | - | - | - | - | - | - |
