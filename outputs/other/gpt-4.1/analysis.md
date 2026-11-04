# Failure cases and cost: outputs/other/gpt-4.1

Operations of each LLM run against wastar-w2 (= 100) and against llmastar_standard; a win is strictly fewer operations on a query, a tie the same number.

| run | vs wastar-w2: win / tie / loss | ops (geo. mean) | vs llmastar_standard: win / tie / loss |
|---|---|---|---|
| llmastar_standard | 332 / 183 / 485 | 116.3 | - |
| quorumastar | 312 / 456 / 232 | 97.7 | 546 / 146 / 308 |

## quorumastar: what reached the search (ops vs wastar-w2 = 100)

| case | queries | ops (geo. mean) | better / equal / worse |
|---|---|---|---|
| no waypoint reached the search | 244 | 100.0 | 0 / 244 / 0 |
| waypoints kept to the end | 541 | 92.3 | 242 / 179 / 120 |
| stall fallback fired | 215 | 109.7 | 70 / 33 / 112 |

## quorumastar: the 10 queries most worse than wastar-w2

| map:sg | ops quorumastar | ops wastar-w2 | ops llmastar_standard | waypoints given | kept targets | stall fallback (pop) |
|---|---|---|---|---|---|---|
| 76:4 | 66 | 12 | 66 | 1 | 1 | no |
| 79:7 | 50 | 16 | 43 | 2 | 0 | yes (41) |
| 75:3 | 52 | 17 | 17 | 2 | 0 | yes (41) |
| 67:3 | 51 | 19 | 36 | 2 | 1 | yes (47) |
| 34:7 | 108 | 41 | 223 | 2 | 1 | yes (77) |
| 18:2 | 72 | 28 | 59 | 1 | 0 | yes (69) |
| 29:4 | 75 | 30 | 224 | 1 | 0 | yes (59) |
| 49:3 | 57 | 23 | 22 | 2 | 1 | yes (55) |
| 27:0 | 44 | 18 | 51 | 1 | 1 | no |
| 69:1 | 53 | 22 | 53 | 1 | 0 | yes (43) |

## Cost per query ($2.0 / $8.0 per 1M input / output tokens)

| run | LLM requests | prompt tokens | completion tokens | $ per query | $ per 1,000 queries | source |
|---|---|---|---|---|---|---|
| llmastar_standard | 1.00 | 585 | 665 | 0.00649 | 6.49 | raw log |
| quorumastar | 3.00 | 5,895 | 46 | 0.01216 | 12.16 | raw log |
