# qwen2.5-vl-7b-instruct: results vs. A* (x100, geometric mean)

A* baseline: 100 queries. Ratios use queries where both the run and A* are valid; `valid` is the % of the run's queries with a valid path; `valid_lenient` (LLM-only) inserts a missing start/goal first. `no_targets` (LLM-A*) is the % of queries where no LLM waypoint survived filtering, so the search ran with h = 2 x distance to goal. `paper_*` columns: Table 1 of arXiv 2407.02511 (LLAMA3 rows).

| run | n | operation | storage | length | valid | valid_lenient | no_targets | paper_operation | paper_storage | paper_length | paper_valid |
|---|---|---|---|---|---|---|---|---|---|---|---|
| astar | 100 | 100.00 | 100.00 | 100.00 | 100.00 | - | - | 100.00 | 100.00 | 100.00 | 100.00 |
| llmastar_standard-max512 | 100 | 95.42 | 85.49 | 100.66 | 100.00 | - | 100.00 | - | - | - | - |
| quorumastar-max512 | 100 | 95.42 | 85.52 | 100.84 | 100.00 | - | 97.00 | - | - | - | - |
| wastar-w2 | 100 | 95.42 | 85.49 | 100.66 | 100.00 | - | - | - | - | - | - |
