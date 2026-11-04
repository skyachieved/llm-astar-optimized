# Failure cases and cost: outputs/gpt_dense/gpt-4o-mini

Operations of each LLM run against wastar-w2 (= 100) and against llmastar_standard; a win is strictly fewer operations on a query, a tie the same number.

| run | vs wastar-w2: win / tie / loss | ops (geo. mean) | vs llmastar_standard: win / tie / loss |
|---|---|---|---|
| llmastar_standard | 21 / 9 / 70 | 200.1 | - |
| quorumastar | 4 / 92 / 4 | 98.4 | 71 / 8 / 21 |

## quorumastar: what reached the search (ops vs wastar-w2 = 100)

| case | queries | ops (geo. mean) | better / equal / worse |
|---|---|---|---|
| no waypoint reached the search | 85 | 100.0 | 0 / 85 / 0 |
| waypoints kept to the end | 12 | 87.2 | 3 / 7 / 2 |
| stall fallback fired | 3 | 101.7 | 1 / 0 / 2 |

## quorumastar: the 10 queries most worse than wastar-w2

| map:sg | ops quorumastar | ops wastar-w2 | ops llmastar_standard | waypoints given | kept targets | stall fallback (pop) |
|---|---|---|---|---|---|---|
| 33:0 | 106 | 95 | 187 | 1 | 0 | yes (69) |
| 56:0 | 112 | 107 | 847 | 1 | 0 | yes (79) |
| 3:0 | 29 | 28 | 28 | 1 | 1 | no |
| 57:0 | 62 | 60 | 1023 | 1 | 1 | no |
| 0:0 | 42 | 42 | 42 | 0 | 0 | no |
| 1:0 | 29 | 29 | 170 | 0 | 0 | no |
| 2:0 | 193 | 193 | 169 | 0 | 0 | no |
| 4:0 | 27 | 27 | 26 | 0 | 0 | no |
| 5:0 | 566 | 566 | 566 | 0 | 0 | no |
| 6:0 | 1234 | 1234 | 1243 | 0 | 0 | no |

## Cost per query ($0.15 / $0.6 per 1M input / output tokens)

| run | LLM requests | prompt tokens | completion tokens | $ per query | $ per 1,000 queries | source |
|---|---|---|---|---|---|---|
| llmastar_standard | 1.00 | 611 | 741 | 0.00054 | 0.54 | raw log |
| quorumastar | 3.59 | 28,782 | 52 | 0.00435 | 4.35 | raw log |
