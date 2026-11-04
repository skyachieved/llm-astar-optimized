# Failure cases and cost: outputs/other/gpt-4.1-mini

Operations of each LLM run against wastar-w2 (= 100) and against llmastar_standard; a win is strictly fewer operations on a query, a tie the same number.

| run | vs wastar-w2: win / tie / loss | ops (geo. mean) | vs llmastar_standard: win / tie / loss |
|---|---|---|---|
| llmastar_standard | 304 / 176 / 520 | 123.0 | - |
| quorumastar | 274 / 499 / 227 | 97.3 | 545 / 148 / 307 |

## quorumastar: what reached the search (ops vs wastar-w2 = 100)

| case | queries | ops (geo. mean) | better / equal / worse |
|---|---|---|---|
| no waypoint reached the search | 314 | 100.0 | 0 / 314 / 0 |
| waypoints kept to the end | 507 | 92.6 | 219 / 155 / 133 |
| stall fallback fired | 179 | 106.6 | 55 / 30 / 94 |

## quorumastar: the 10 queries most worse than wastar-w2

| map:sg | ops quorumastar | ops wastar-w2 | ops llmastar_standard | waypoints given | kept targets | stall fallback (pop) |
|---|---|---|---|---|---|---|
| 30:4 | 43 | 10 | 11 | 1 | 0 | yes (41) |
| 4:0 | 38 | 13 | 13 | 1 | 1 | no |
| 18:2 | 72 | 28 | 34 | 1 | 0 | yes (69) |
| 85:2 | 57 | 23 | 23 | 1 | 1 | no |
| 8:9 | 91 | 38 | 281 | 1 | 1 | no |
| 27:0 | 41 | 18 | 21 | 1 | 1 | no |
| 1:4 | 50 | 22 | 22 | 2 | 0 | yes (43) |
| 13:3 | 121 | 54 | 66 | 2 | 1 | yes (66) |
| 44:8 | 47 | 22 | 27 | 1 | 0 | yes (41) |
| 75:3 | 36 | 17 | 26 | 2 | 2 | no |

## Cost per query ($0.4 / $1.6 per 1M input / output tokens)

| run | LLM requests | prompt tokens | completion tokens | $ per query | $ per 1,000 queries | source |
|---|---|---|---|---|---|---|
| llmastar_standard | 1.00 | 585 | 1,056 | 0.00192 | 1.92 | raw log |
| quorumastar | 3.00 | 5,895 | 44 | 0.00243 | 2.43 | raw log |
