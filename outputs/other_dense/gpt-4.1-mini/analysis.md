# Failure cases and cost: outputs/other_dense/gpt-4.1-mini

Operations of each LLM run against wastar-w2 (= 100) and against llmastar_standard; a win is strictly fewer operations on a query, a tie the same number.

| run | vs wastar-w2: win / tie / loss | ops (geo. mean) | vs llmastar_standard: win / tie / loss |
|---|---|---|---|
| llmastar_standard | 21 / 16 / 63 | 153.7 | - |
| quorumastar | 23 / 47 / 30 | 102.2 | 65 / 8 / 27 |

## quorumastar: what reached the search (ops vs wastar-w2 = 100)

| case | queries | ops (geo. mean) | better / equal / worse |
|---|---|---|---|
| no waypoint reached the search | 29 | 100.0 | 0 / 29 / 0 |
| waypoints kept to the end | 51 | 97.2 | 17 / 16 / 18 |
| stall fallback fired | 20 | 119.7 | 6 / 2 / 12 |

## quorumastar: the 10 queries most worse than wastar-w2

| map:sg | ops quorumastar | ops wastar-w2 | ops llmastar_standard | waypoints given | kept targets | stall fallback (pop) |
|---|---|---|---|---|---|---|
| 61:0 | 146 | 25 | 56 | 2 | 1 | yes (62) |
| 16:0 | 56 | 26 | 41 | 2 | 0 | yes (41) |
| 44:0 | 109 | 57 | 94 | 1 | 0 | yes (75) |
| 35:0 | 65 | 38 | 38 | 2 | 0 | yes (55) |
| 30:0 | 62 | 37 | 41 | 1 | 1 | no |
| 23:0 | 40 | 25 | 38 | 2 | 2 | no |
| 74:0 | 130 | 105 | 133 | 1 | 0 | yes (55) |
| 81:0 | 45 | 38 | 203 | 4 | 4 | no |
| 36:0 | 87 | 74 | 148 | 1 | 1 | no |
| 67:0 | 47 | 41 | 608 | 3 | 3 | no |

## Cost per query ($0.4 / $1.6 per 1M input / output tokens)

| run | LLM requests | prompt tokens | completion tokens | $ per query | $ per 1,000 queries | source |
|---|---|---|---|---|---|---|
| llmastar_standard | 1.00 | 611 | 1,362 | 0.00242 | 2.42 | raw log |
| quorumastar | 3.00 | 6,935 | 53 | 0.00286 | 2.86 | raw log |
