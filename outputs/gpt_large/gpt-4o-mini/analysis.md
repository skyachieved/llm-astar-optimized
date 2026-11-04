# Failure cases and cost: outputs/gpt_large/gpt-4o-mini

Operations of each LLM run against wastar-w2 (= 100) and against llmastar_standard; a win is strictly fewer operations on a query, a tie the same number.

| run | vs wastar-w2: win / tie / loss | ops (geo. mean) | vs llmastar_standard: win / tie / loss |
|---|---|---|---|
| llmastar_standard | 16 / 7 / 77 | 239.6 | - |
| quorumastar | 0 / 97 / 3 | 100.1 | 77 / 7 / 16 |

## quorumastar: what reached the search (ops vs wastar-w2 = 100)

| case | queries | ops (geo. mean) | better / equal / worse |
|---|---|---|---|
| no waypoint reached the search | 95 | 100.0 | 0 / 95 / 0 |
| waypoints kept to the end | 1 | 100.0 | 0 / 1 / 0 |
| stall fallback fired | 4 | 103.6 | 0 / 1 / 3 |

## quorumastar: the 10 queries most worse than wastar-w2

| map:sg | ops quorumastar | ops wastar-w2 | ops llmastar_standard | waypoints given | kept targets | stall fallback (pop) |
|---|---|---|---|---|---|---|
| 37:0 | 1893 | 1697 | 1230 | 1 | 0 | yes (105) |
| 17:0 | 189 | 183 | 832 | 1 | 0 | yes (135) |
| 6:0 | 2436 | 2435 | 3448 | 1 | 0 | yes (153) |
| 0:0 | 210 | 210 | 294 | 0 | 0 | no |
| 1:0 | 185 | 185 | 2374 | 0 | 0 | no |
| 2:0 | 56 | 56 | 1697 | 0 | 0 | no |
| 3:0 | 212 | 212 | 264 | 0 | 0 | no |
| 4:0 | 292 | 292 | 288 | 0 | 0 | no |
| 5:0 | 65 | 65 | 1534 | 0 | 0 | no |
| 7:0 | 158 | 158 | 409 | 0 | 0 | no |

## Cost per query ($0.15 / $0.6 per 1M input / output tokens)

| run | LLM requests | prompt tokens | completion tokens | $ per query | $ per 1,000 queries | source |
|---|---|---|---|---|---|---|
| llmastar_standard | 1.00 | 647 | 626 | 0.00047 | 0.47 | raw log |
| quorumastar | 3.38 | 22,810 | 53 | 0.00345 | 3.45 | raw log |
