# Failure cases and cost: outputs/claude/claude-opus-5-5

Operations of each LLM run against wastar-w2 (= 100) and against llmastar_standard; a win is strictly fewer operations on a query, a tie the same number.

| run | vs wastar-w2: win / tie / loss | ops (geo. mean) | vs llmastar_standard: win / tie / loss |
|---|---|---|---|
| llmastar_standard | 499 / 373 / 128 | 89.6 | - |
| quorumastar | 570 / 278 / 152 | 87.5 | 306 / 493 / 201 |

## quorumastar: what reached the search (ops vs wastar-w2 = 100)

| case | queries | ops (geo. mean) | better / equal / worse |
|---|---|---|---|
| no waypoint reached the search | 50 | 100.0 | 0 / 50 / 0 |
| waypoints kept to the end | 732 | 83.3 | 441 / 222 / 69 |
| stall fallback fired | 218 | 100.3 | 129 / 6 / 83 |

## quorumastar: the 10 queries most worse than wastar-w2

| map:sg | ops quorumastar | ops wastar-w2 | ops llmastar_standard | waypoints given | kept targets | stall fallback (pop) |
|---|---|---|---|---|---|---|
| 12:3 | 89 | 26 | 26 | 2 | 1 | yes (72) |
| 69:1 | 56 | 22 | 21 | 1 | 0 | yes (47) |
| 24:8 | 71 | 32 | 30 | 1 | 1 | no |
| 14:9 | 80 | 40 | 40 | 2 | 2 | no |
| 68:5 | 100 | 53 | 100 | 1 | 1 | no |
| 99:9 | 62 | 33 | 25 | 2 | 2 | no |
| 31:9 | 187 | 102 | 102 | 1 | 0 | yes (83) |
| 96:5 | 95 | 52 | 52 | 1 | 0 | yes (49) |
| 82:7 | 179 | 99 | 96 | 2 | 1 | yes (49) |
| 52:7 | 82 | 47 | 82 | 1 | 1 | no |

## Cost per query ($4.0 / $20.0 per 1M input / output tokens)

| run | LLM requests | prompt tokens | completion tokens | $ per query | $ per 1,000 queries | source |
|---|---|---|---|---|---|---|
| llmastar_standard | 1.00 | 801 | 1,099 | 0.02519 | 25.19 | raw log |
| quorumastar | 3.00 | 7,128 | 1,290 | 0.05432 | 54.32 | raw log |
