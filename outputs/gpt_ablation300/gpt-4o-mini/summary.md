# gpt-4o-mini: results vs. A* (x100, geometric mean)

A* baseline: 300 queries. Ratios use queries where both the run and A* are valid; `valid` is the % of the run's queries with a valid path; `valid_lenient` (LLM-only) inserts a missing start/goal first. `no_targets` (LLM-A*) is the % of queries where no LLM waypoint survived filtering, so the search ran with h = 2 x distance to goal. `paper_*` columns: Table 1 of arXiv 2407.02511 (LLAMA3 rows).

| run | n | operation | storage | length | valid | valid_lenient | no_targets | paper_operation | paper_storage | paper_length | paper_valid |
|---|---|---|---|---|---|---|---|---|---|---|---|
| astar | 300 | 100.00 | 100.00 | 100.00 | 100.00 | - | - | 100.00 | 100.00 | 100.00 | 100.00 |
| llmastar_standard | 300 | 48.31 | 67.18 | 102.76 | 100.00 | - | 6.67 | 44.59 | 64.02 | 102.47 | 100.00 |
| quorumastar | 300 | 33.18 | 55.54 | 102.02 | 100.00 | - | 47.00 | - | - | - | - |
| quorumastar-add1 | 300 | 41.61 | 62.63 | 102.97 | 100.00 | - | 25.33 | - | - | - | - |
| quorumastar-add3 | 300 | 32.69 | 55.19 | 101.85 | 100.00 | - | 89.33 | - | - | - | - |
| quorumastar-cot | 300 | 33.09 | 55.62 | 102.04 | 100.00 | - | 49.67 | - | - | - | - |
| quorumastar-fsnone | 300 | 35.96 | 57.84 | 102.32 | 100.00 | - | 31.67 | - | - | - | - |
| quorumastar-fsshared | 300 | 32.62 | 55.27 | 101.94 | 100.00 | - | 50.67 | - | - | - | - |
| quorumastar-nosnap | 300 | 33.54 | 55.68 | 101.96 | 100.00 | - | 75.67 | - | - | - | - |
| quorumastar-roles | 300 | 33.55 | 55.78 | 101.97 | 100.00 | - | 51.00 | - | - | - | - |
| quorumastar-vcorners-add1 | 300 | 37.41 | 59.71 | 102.47 | 100.00 | - | 42.67 | - | - | - | - |
| quorumastar-vision | 300 | 32.97 | 55.36 | 101.88 | 100.00 | - | 83.00 | - | - | - | - |
| quorumastar-vrelations-add1 | 300 | 36.54 | 58.44 | 102.83 | 100.00 | - | 32.00 | - | - | - | - |
| quorumastar-vtext+corners+image | 300 | 33.57 | 55.82 | 101.96 | 100.00 | - | 58.00 | - | - | - | - |
| quorumastar-vtext+corners+relations+image | 300 | 33.63 | 55.88 | 102.14 | 100.00 | - | 38.33 | - | - | - | - |
| quorumastar-vtext-add1 | 300 | 36.34 | 57.57 | 102.36 | 100.00 | - | 30.67 | - | - | - | - |
| wastar-w2 | 300 | 33.19 | 55.41 | 101.88 | 100.00 | - | - | - | - | - | - |
