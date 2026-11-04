# Failure cases and cost: outputs/gpt_large/gpt-4o-mini

Operations of each LLM run against wastar-w2 (= 100) and against llmastar_standard; a win is strictly fewer operations on a query, a tie the same number.

| run | vs wastar-w2: win / tie / loss | ops (geo. mean) | vs llmastar_standard: win / tie / loss |
|---|---|---|---|
| llmastar_standard | 16 / 7 / 77 | 239.6 | - |
| quorumastar | 11 / 76 / 13 | 100.3 | 79 / 4 / 17 |
| quorumastar-vision | 0 / 97 / 3 | 100.1 | 77 / 7 / 16 |

## quorumastar: what reached the search (ops vs wastar-w2 = 100)

| case | queries | ops (geo. mean) | better / equal / worse |
|---|---|---|---|
| no waypoint reached the search | 71 | 100.0 | 0 / 71 / 0 |
| waypoints kept to the end | 15 | 90.9 | 7 / 4 / 4 |
| stall fallback fired | 14 | 113.0 | 4 / 1 / 9 |

## quorumastar: the 10 queries most worse than wastar-w2

| map:sg | ops quorumastar | ops wastar-w2 | ops llmastar_standard | waypoints given | kept targets | stall fallback (pop) |
|---|---|---|---|---|---|---|
| 36:0 | 246 | 50 | 50 | 2 | 1 | yes (110) |
| 10:0 | 118 | 61 | 2236 | 1 | 1 | no |
| 5:0 | 106 | 65 | 1534 | 1 | 0 | yes (61) |
| 95:0 | 124 | 80 | 1910 | 1 | 0 | yes (51) |
| 27:0 | 153 | 123 | 2880 | 1 | 0 | yes (103) |
| 44:0 | 59 | 49 | 2217 | 1 | 1 | no |
| 37:0 | 1893 | 1697 | 1230 | 1 | 0 | yes (105) |
| 3:0 | 232 | 212 | 264 | 1 | 0 | yes (173) |
| 17:0 | 193 | 183 | 832 | 2 | 0 | yes (81) |
| 11:0 | 173 | 167 | 193 | 1 | 0 | yes (95) |

## Cost per query ($0.15 / $0.6 per 1M input / output tokens)

| run | LLM requests | prompt tokens | completion tokens | $ per query | $ per 1,000 queries | source |
|---|---|---|---|---|---|---|
| llmastar_standard | 1.00 | 647 | 626 | 0.00047 | 0.47 | raw log |
| quorumastar | 3.00 | 8,740 | 51 | 0.00134 | 1.34 | raw log |
| quorumastar-vision | 3.38 | 22,810 | 53 | 0.00345 | 3.45 | raw log |
