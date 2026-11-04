# Failure cases and cost: outputs/other_large/gpt-4.1

Operations of each LLM run against wastar-w2 (= 100) and against llmastar_standard; a win is strictly fewer operations on a query, a tie the same number.

| run | vs wastar-w2: win / tie / loss | ops (geo. mean) | vs llmastar_standard: win / tie / loss |
|---|---|---|---|
| llmastar_standard | 23 / 3 / 74 | 200.9 | - |
| quorumastar | 30 / 34 / 36 | 101.7 | 74 / 1 / 25 |

## quorumastar: what reached the search (ops vs wastar-w2 = 100)

| case | queries | ops (geo. mean) | better / equal / worse |
|---|---|---|---|
| no waypoint reached the search | 25 | 100.0 | 0 / 25 / 0 |
| waypoints kept to the end | 31 | 96.0 | 12 / 8 / 11 |
| stall fallback fired | 44 | 106.9 | 18 / 1 / 25 |

## quorumastar: the 10 queries most worse than wastar-w2

| map:sg | ops quorumastar | ops wastar-w2 | ops llmastar_standard | waypoints given | kept targets | stall fallback (pop) |
|---|---|---|---|---|---|---|
| 34:0 | 1155 | 206 | 1447 | 2 | 1 | yes (198) |
| 12:0 | 303 | 99 | 1043 | 3 | 1 | yes (113) |
| 7:0 | 238 | 158 | 3459 | 3 | 1 | yes (66) |
| 13:0 | 385 | 256 | 1949 | 1 | 0 | yes (57) |
| 49:0 | 167 | 119 | 175 | 2 | 0 | yes (69) |
| 58:0 | 137 | 99 | 516 | 2 | 1 | yes (125) |
| 15:0 | 174 | 132 | 296 | 4 | 1 | yes (96) |
| 32:0 | 157 | 123 | 209 | 2 | 0 | yes (41) |
| 55:0 | 93 | 73 | 122 | 3 | 3 | no |
| 56:0 | 1569 | 1234 | 1464 | 1 | 0 | yes (51) |

## Cost per query ($2.0 / $8.0 per 1M input / output tokens)

| run | LLM requests | prompt tokens | completion tokens | $ per query | $ per 1,000 queries | source |
|---|---|---|---|---|---|---|
| llmastar_standard | 1.00 | 647 | 953 | 0.00891 | 8.91 | raw log |
| quorumastar | 3.00 | 8,740 | 83 | 0.01815 | 18.15 | raw log |
