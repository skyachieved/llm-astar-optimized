# Failure cases and cost: outputs/other_dense/gpt-4.1

Operations of each LLM run against wastar-w2 (= 100) and against llmastar_standard; a win is strictly fewer operations on a query, a tie the same number.

| run | vs wastar-w2: win / tie / loss | ops (geo. mean) | vs llmastar_standard: win / tie / loss |
|---|---|---|---|
| llmastar_standard | 30 / 4 / 66 | 151.6 | - |
| quorumastar | 32 / 31 / 37 | 102.6 | 63 / 1 / 36 |

## quorumastar: what reached the search (ops vs wastar-w2 = 100)

| case | queries | ops (geo. mean) | better / equal / worse |
|---|---|---|---|
| no waypoint reached the search | 15 | 100.0 | 0 / 15 / 0 |
| waypoints kept to the end | 59 | 96.2 | 28 / 13 / 18 |
| stall fallback fired | 26 | 120.7 | 4 / 3 / 19 |

## quorumastar: the 10 queries most worse than wastar-w2

| map:sg | ops quorumastar | ops wastar-w2 | ops llmastar_standard | waypoints given | kept targets | stall fallback (pop) |
|---|---|---|---|---|---|---|
| 11:0 | 267 | 66 | 192 | 3 | 1 | yes (83) |
| 8:0 | 62 | 28 | 33 | 3 | 1 | yes (56) |
| 66:0 | 79 | 42 | 790 | 2 | 2 | no |
| 87:0 | 67 | 37 | 29 | 2 | 0 | yes (41) |
| 49:0 | 52 | 30 | 41 | 3 | 3 | no |
| 35:0 | 65 | 38 | 38 | 1 | 0 | yes (55) |
| 27:0 | 88 | 54 | 69 | 1 | 0 | yes (41) |
| 1:0 | 47 | 29 | 31 | 2 | 2 | no |
| 23:0 | 40 | 25 | 46 | 2 | 2 | no |
| 10:0 | 114 | 78 | 1042 | 1 | 0 | yes (65) |

## Cost per query ($2.0 / $8.0 per 1M input / output tokens)

| run | LLM requests | prompt tokens | completion tokens | $ per query | $ per 1,000 queries | source |
|---|---|---|---|---|---|---|
| llmastar_standard | 1.00 | 611 | 879 | 0.00825 | 8.25 | raw log |
| quorumastar | 3.00 | 6,935 | 64 | 0.01438 | 14.38 | raw log |
