# gpt-4o-mini: results vs. A* (x100, geometric mean)

A* baseline: 1000 queries. Ratios use queries where both the run and A* are valid; `valid` is the % of the run's queries with a valid path; `valid_lenient` (LLM-only) inserts a missing start/goal first. `no_targets` (LLM-A*) is the % of queries where no LLM waypoint survived filtering, so the search ran with h = 2 x distance to goal. `paper_*` columns: Table 1 of arXiv 2407.02511 (LLAMA3 rows).

| run | n | operation | storage | length | valid | valid_lenient | no_targets | paper_operation | paper_storage | paper_length | paper_valid |
|---|---|---|---|---|---|---|---|---|---|---|---|
| astar | 1000 | 100.00 | 100.00 | 100.00 | 100.00 | - | - | 100.00 | 100.00 | 100.00 | 100.00 |
| dwastar | 1000 | 59.49 | 78.65 | 100.25 | 100.00 | - | - | 60.91 | 78.53 | 100.24 | 100.00 |
| llm_only_standard | 1000 | - | - | 123.09 | 6.30 | 6.30 | - | - | - | 111.05 | 12.60 |
| llm_only_cot | 1000 | - | - | 126.92 | 7.20 | 7.20 | - | - | - | 114.89 | 12.00 |
| llm_only_repe | 1000 | - | - | 114.03 | 8.00 | 8.00 | - | - | - | 138.32 | 16.40 |
| llmastar_standard | 1000 | 50.52 | 68.38 | 102.95 | 100.00 | - | 7.10 | 44.59 | 64.02 | 102.47 | 100.00 |
| llmastar_cot | 1000 | 48.53 | 67.07 | 102.73 | 100.00 | - | 7.60 | 47.60 | 66.27 | 102.46 | 100.00 |
| llmastar_repe | 1000 | 50.84 | 68.97 | 102.51 | 100.00 | - | 4.40 | 64.08 | 80.19 | 102.54 | 100.00 |
| llm_only_cot-stopnl-max100 | 1000 | - | - | - | 0.00 | 0.60 | - | - | - | - | - |
| llm_only_repe-stopnl-max100 | 1000 | - | - | - | 0.00 | 0.60 | - | - | - | - | - |
| llm_only_standard-stopnl-max100 | 1000 | - | - | - | 0.00 | 0.60 | - | - | - | - | - |
| llmastar_cot-stopnl-max100 | 1000 | 34.32 | 56.23 | 102.02 | 100.00 | - | 100.00 | - | - | - | - |
| llmastar_repe-stopnl-max100 | 1000 | 34.32 | 56.23 | 102.02 | 100.00 | - | 100.00 | - | - | - | - |
| llmastar_standard-stopnl-max100 | 1000 | 34.32 | 56.23 | 102.02 | 100.00 | - | 100.00 | - | - | - | - |
| quorumastar | 1000 | 33.95 | 56.08 | 102.00 | 100.00 | - | 51.40 | - | - | - | - |
| quorumastar-k0 | 1000 | 35.32 | 57.41 | 102.01 | 100.00 | - | 32.60 | - | - | - | - |
| quorumastar-rm0 | 1000 | 34.05 | 56.13 | 102.02 | 100.00 | - | 49.90 | - | - | - | - |
| quorumastar-vision | 1000 | 34.10 | 56.09 | 102.03 | 100.00 | - | 84.10 | - | - | - | - |
| quorumastar-vtext-fspaper-nosnap-add1-k0 | 1000 | 50.52 | 68.38 | 102.95 | 100.00 | - | 7.10 | - | - | - | - |
| wastar-w1.5 | 1000 | 40.06 | 60.26 | 100.74 | 100.00 | - | - | - | - | - | - |
| wastar-w2 | 1000 | 34.32 | 56.23 | 102.02 | 100.00 | - | - | - | - | - | - |
| wastar-w3 | 1000 | 29.92 | 53.26 | 103.68 | 100.00 | - | - | - | - | - | - |
