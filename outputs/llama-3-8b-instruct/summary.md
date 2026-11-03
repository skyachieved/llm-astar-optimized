# llama-3-8b-instruct: results vs. A* (x100, geometric mean)

A* baseline: 1000 queries. Ratios use queries where both the run and A* are valid; `valid` is the % of the run's queries with a valid path; `valid_lenient` (LLM-only) inserts a missing start/goal first. `no_targets` (LLM-A*) is the % of queries where no LLM waypoint survived filtering, so the search ran with h = 2 x distance to goal. `paper_*` columns: Table 1 of arXiv 2407.02511 (LLAMA3 rows).

| run | n | operation | storage | length | valid | valid_lenient | no_targets | paper_operation | paper_storage | paper_length | paper_valid |
|---|---|---|---|---|---|---|---|---|---|---|---|
| astar | 1000 | 100.00 | 100.00 | 100.00 | 100.00 | - | - | 100.00 | 100.00 | 100.00 | 100.00 |
| dwastar | 1000 | 59.49 | 78.65 | 100.25 | 100.00 | - | - | 60.91 | 78.53 | 100.24 | 100.00 |
| llm_only_standard | 1000 | - | - | 110.91 | 10.70 | 10.70 | - | - | - | 111.05 | 12.60 |
| llm_only_cot | 1000 | - | - | 118.53 | 9.70 | 9.90 | - | - | - | 114.89 | 12.00 |
| llm_only_repe | 1000 | - | - | 169.01 | 9.80 | 10.20 | - | - | - | 138.32 | 16.40 |
| llmastar_standard | 1000 | 42.99 | 62.83 | 102.27 | 100.00 | - | 25.40 | 44.59 | 64.02 | 102.47 | 100.00 |
| llmastar_cot | 1000 | 49.63 | 68.06 | 102.45 | 100.00 | - | 9.60 | 47.60 | 66.27 | 102.46 | 100.00 |
| llmastar_repe | 1000 | 69.70 | 84.31 | 102.42 | 100.00 | - | 7.10 | 64.08 | 80.19 | 102.54 | 100.00 |
| dwastar-depth | 1000 | 33.20 | 55.49 | 102.55 | 100.00 | - | - | - | - | - | - |
| dwastar-fixed | 1000 | 33.66 | 61.15 | 105.66 | 100.00 | - | - | - | - | - | - |
| dwastar-fixed-min0 | 1000 | 46.49 | 82.29 | 108.19 | 100.00 | - | - | - | - | - | - |
| dwastar-min0 | 1000 | 105.02 | 141.40 | 100.25 | 100.00 | - | - | - | - | - | - |
