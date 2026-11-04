# Failure cases and cost: outputs/gpt_dense/gpt-4o-mini

Operations of each LLM run against wastar-w2 (= 100) and against llmastar_standard; a win is strictly fewer operations on a query, a tie the same number.

| run | vs wastar-w2: win / tie / loss | ops (geo. mean) | vs llmastar_standard: win / tie / loss |
|---|---|---|---|
| llmastar_standard | 21 / 9 / 70 | 200.1 | - |
| quorumastar | 15 / 68 / 17 | 100.4 | 73 / 4 / 23 |
| quorumastar-vision | 4 / 92 / 4 | 98.4 | 71 / 8 / 21 |

## quorumastar: what reached the search (ops vs wastar-w2 = 100)

| case | queries | ops (geo. mean) | better / equal / worse |
|---|---|---|---|
| no waypoint reached the search | 49 | 100.0 | 0 / 49 / 0 |
| waypoints kept to the end | 33 | 96.1 | 10 / 15 / 8 |
| stall fallback fired | 18 | 110.0 | 5 / 4 / 9 |

## quorumastar: the 10 queries most worse than wastar-w2

| map:sg | ops quorumastar | ops wastar-w2 | ops llmastar_standard | waypoints given | kept targets | stall fallback (pop) |
|---|---|---|---|---|---|---|
| 45:0 | 63 | 24 | 40 | 1 | 0 | yes (59) |
| 35:0 | 65 | 38 | 756 | 1 | 0 | yes (55) |
| 72:0 | 43 | 33 | 39 | 2 | 2 | no |
| 46:0 | 33 | 28 | 103 | 1 | 1 | no |
| 80:0 | 215 | 185 | 350 | 1 | 1 | no |
| 36:0 | 85 | 74 | 86 | 1 | 1 | no |
| 82:0 | 40 | 35 | 35 | 1 | 1 | no |
| 12:0 | 85 | 76 | 73 | 1 | 0 | yes (55) |
| 33:0 | 106 | 95 | 187 | 1 | 0 | yes (69) |
| 88:0 | 75 | 68 | 73 | 1 | 0 | yes (41) |

## Cost per query ($0.15 / $0.6 per 1M input / output tokens)

| run | LLM requests | prompt tokens | completion tokens | $ per query | $ per 1,000 queries | source |
|---|---|---|---|---|---|---|
| llmastar_standard | 1.00 | 611 | 741 | 0.00054 | 0.54 | raw log |
| quorumastar | 3.00 | 6,935 | 48 | 0.00107 | 1.07 | raw log |
| quorumastar-vision | 3.59 | 28,782 | 52 | 0.00435 | 4.35 | raw log |
