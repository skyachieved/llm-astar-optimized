# Failure cases and cost: outputs/qwen_dense/qwen2.5-vl-7b-instruct

Operations of each LLM run against wastar-w2 (= 100) and against llmastar_standard-max512; a win is strictly fewer operations on a query, a tie the same number.

| run | vs wastar-w2: win / tie / loss | ops (geo. mean) | vs llmastar_standard-max512: win / tie / loss |
|---|---|---|---|
| llmastar_standard-max512 | 17 / 48 / 35 | 144.2 | - |
| quorumastar-max512 | 15 / 63 / 22 | 103.0 | 42 / 28 / 30 |

## quorumastar-max512: what reached the search (ops vs wastar-w2 = 100)

| case | queries | ops (geo. mean) | better / equal / worse |
|---|---|---|---|
| no waypoint reached the search | 56 | 100.0 | 0 / 56 / 0 |
| waypoints kept to the end | 26 | 99.6 | 9 / 4 / 13 |
| stall fallback fired | 18 | 118.9 | 6 / 3 / 9 |

## quorumastar-max512: the 10 queries most worse than wastar-w2

| map:sg | ops quorumastar-max512 | ops wastar-w2 | ops llmastar_standard-max512 | waypoints given | kept targets | stall fallback (pop) |
|---|---|---|---|---|---|---|
| 11:0 | 172 | 66 | 66 | 2 | 0 | yes (71) |
| 4:0 | 64 | 27 | 27 | 3 | 3 | no |
| 16:0 | 57 | 26 | 443 | 3 | 0 | yes (41) |
| 98:0 | 81 | 38 | 31 | 2 | 0 | yes (55) |
| 44:0 | 109 | 57 | 57 | 2 | 0 | yes (75) |
| 73:0 | 64 | 38 | 36 | 2 | 2 | no |
| 30:0 | 62 | 37 | 34 | 1 | 1 | no |
| 23:0 | 40 | 25 | 29 | 2 | 2 | no |
| 32:0 | 58 | 38 | 210 | 2 | 2 | no |
| 46:0 | 33 | 28 | 28 | 1 | 1 | no |

## Cost per query ($0.15 / $0.6 per 1M input / output tokens)

| run | LLM requests | prompt tokens | completion tokens | $ per query | $ per 1,000 queries | source |
|---|---|---|---|---|---|---|
| llmastar_standard-max512 | 1.00 | 756 | 51 | 0.00014 | 0.14 | raw log |
| quorumastar-max512 | 3.00 | 7,908 | 171 | 0.00129 | 1.29 | raw log |
