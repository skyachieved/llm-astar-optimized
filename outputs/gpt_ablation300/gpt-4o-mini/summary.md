# gpt-4o-mini: results vs. A* (x100, geometric mean)

A* baseline: 300 queries. Ratios use queries where both the run and A* are valid; `valid` is the % of the run's queries with a valid path; `valid_lenient` (LLM-only) inserts a missing start/goal first. `no_targets` (LLM-A*) is the % of queries where no LLM waypoint survived filtering, so the search ran with h = 2 x distance to goal. `paper_*` columns: Table 1 of arXiv 2407.02511 (LLAMA3 rows).

| run | n | operation | storage | length | valid | valid_lenient | no_targets | paper_operation | paper_storage | paper_length | paper_valid |
|---|---|---|---|---|---|---|---|---|---|---|---|
| astar | 300 | 100.00 | 100.00 | 100.00 | 100.00 | - | - | 100.00 | 100.00 | 100.00 | 100.00 |
| llmastar_standard | 300 | 48.31 | 67.18 | 102.76 | 100.00 | - | 6.67 | 44.59 | 64.02 | 102.47 | 100.00 |
| quorumastar | 300 | 32.97 | 55.36 | 101.88 | 100.00 | - | 83.00 | - | - | - | - |
| quorumastar-add1 | 300 | 35.59 | 57.49 | 102.38 | 100.00 | - | 27.00 | - | - | - | - |
| quorumastar-add3 | 300 | 32.69 | 55.19 | 101.85 | 100.00 | - | 89.67 | - | - | - | - |
| quorumastar-cot | 300 | 33.17 | 55.55 | 101.97 | 100.00 | - | 85.33 | - | - | - | - |
| quorumastar-fsnone | 300 | 32.79 | 55.17 | 101.90 | 100.00 | - | 59.00 | - | - | - | - |
| quorumastar-fsshared | 300 | 32.66 | 55.09 | 101.88 | 100.00 | - | 81.67 | - | - | - | - |
| quorumastar-nosnap | 300 | 33.30 | 55.49 | 101.91 | 100.00 | - | 97.67 | - | - | - | - |
| quorumastar-roles | 300 | 33.18 | 55.50 | 101.96 | 100.00 | - | 85.67 | - | - | - | - |
| quorumastar-vcorners-add1 | 300 | 37.34 | 59.62 | 102.47 | 100.00 | - | 42.33 | - | - | - | - |
| quorumastar-vrelations-add1 | 300 | 36.09 | 58.14 | 102.74 | 100.00 | - | 32.67 | - | - | - | - |
| quorumastar-vtext+corners+image | 300 | 33.16 | 55.31 | 101.95 | 100.00 | - | 84.67 | - | - | - | - |
| quorumastar-vtext+corners+relations+image | 300 | 33.57 | 55.62 | 102.06 | 100.00 | - | 78.33 | - | - | - | - |
| quorumastar-vtext-add1 | 300 | 35.82 | 57.27 | 102.38 | 100.00 | - | 30.67 | - | - | - | - |
| wastar-w2 | 300 | 33.19 | 55.41 | 101.88 | 100.00 | - | - | - | - | - | - |
