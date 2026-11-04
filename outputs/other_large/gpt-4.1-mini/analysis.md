# Failure cases and cost: outputs/other_large/gpt-4.1-mini

Operations of each LLM run against wastar-w2 (= 100) and against llmastar_standard; a win is strictly fewer operations on a query, a tie the same number.

| run | vs wastar-w2: win / tie / loss | ops (geo. mean) | vs llmastar_standard: win / tie / loss |
|---|---|---|---|
| llmastar_standard | 17 / 13 / 70 | 247.1 | - |
| quorumastar | 26 / 44 / 30 | 102.0 | 68 / 9 / 23 |

## quorumastar: what reached the search (ops vs wastar-w2 = 100)

| case | queries | ops (geo. mean) | better / equal / worse |
|---|---|---|---|
| no waypoint reached the search | 37 | 100.0 | 0 / 37 / 0 |
| waypoints kept to the end | 28 | 98.4 | 9 / 7 / 12 |
| stall fallback fired | 35 | 107.2 | 17 / 0 / 18 |

## quorumastar: the 10 queries most worse than wastar-w2

| map:sg | ops quorumastar | ops wastar-w2 | ops llmastar_standard | waypoints given | kept targets | stall fallback (pop) |
|---|---|---|---|---|---|---|
| 32:0 | 246 | 123 | 219 | 2 | 0 | yes (111) |
| 52:0 | 423 | 253 | 777 | 2 | 1 | yes (159) |
| 95:0 | 128 | 80 | 155 | 2 | 1 | yes (89) |
| 7:0 | 237 | 158 | 184 | 1 | 1 | no |
| 58:0 | 137 | 99 | 288 | 2 | 0 | yes (125) |
| 27:0 | 160 | 123 | 161 | 1 | 0 | yes (41) |
| 23:0 | 85 | 66 | 69 | 1 | 1 | no |
| 55:0 | 93 | 73 | 1935 | 3 | 3 | no |
| 89:0 | 848 | 682 | 833 | 1 | 1 | no |
| 31:0 | 241 | 195 | 1364 | 2 | 0 | yes (57) |

## Cost per query ($0.4 / $1.6 per 1M input / output tokens)

| run | LLM requests | prompt tokens | completion tokens | $ per query | $ per 1,000 queries | source |
|---|---|---|---|---|---|---|
| llmastar_standard | 1.00 | 647 | 1,397 | 0.00249 | 2.49 | raw log |
| quorumastar | 3.00 | 8,740 | 65 | 0.00360 | 3.60 | raw log |
