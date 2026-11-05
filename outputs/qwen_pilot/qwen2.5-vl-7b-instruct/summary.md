# qwen2.5-vl-7b-instruct: results vs. A* (x100, geometric mean)

A* baseline: 50 queries. Ratios use queries where both the run and A* are valid; `valid` is the % of the run's queries with a valid path; `valid_lenient` (LLM-only) inserts a missing start/goal first. `no_targets` (LLM-A*) is the % of queries where no LLM waypoint survived filtering, so the search ran with h = 2 x distance to goal. `paper_*` columns: Table 1 of arXiv 2407.02511 (LLAMA3 rows).

| run | n | operation | storage | length | valid | valid_lenient | no_targets | paper_operation | paper_storage | paper_length | paper_valid |
|---|---|---|---|---|---|---|---|---|---|---|---|
| astar | 50 | 100.00 | 100.00 | 100.00 | 100.00 | - | - | 100.00 | 100.00 | 100.00 | 100.00 |
| llmastar_standard-max512 | 50 | 24.24 | 49.37 | 103.97 | 100.00 | - | 58.00 | - | - | - | - |
| quorumastar-max512 | 50 | 23.79 | 48.88 | 103.12 | 100.00 | - | 74.00 | - | - | - | - |
| quorumastar-vision-max512 | 50 | 24.60 | 49.57 | 103.18 | 100.00 | - | 96.00 | - | - | - | - |
| quorumastar-vtext+corners+image+relations-vision-max512 | 50 | 24.61 | 49.63 | 103.16 | 100.00 | - | 88.00 | - | - | - | - |
| quorumastar-vtext+corners+image-max512 | 50 | 25.07 | 50.16 | 103.15 | 100.00 | - | 76.00 | - | - | - | - |
| wastar-w2 | 50 | 24.34 | 49.25 | 103.18 | 100.00 | - | - | - | - | - | - |
