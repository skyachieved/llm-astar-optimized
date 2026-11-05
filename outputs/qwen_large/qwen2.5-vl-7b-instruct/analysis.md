# Failure cases and cost: outputs/qwen_large/qwen2.5-vl-7b-instruct

Operations of each LLM run against wastar-w2 (= 100) and against llmastar_standard-max512; a win is strictly fewer operations on a query, a tie the same number.

| run | vs wastar-w2: win / tie / loss | ops (geo. mean) | vs llmastar_standard-max512: win / tie / loss |
|---|---|---|---|
| llmastar_standard-max512 | 7 / 71 / 22 | 154.4 | - |
| quorumastar-max512 | 6 / 79 / 15 | 105.2 | 26 / 57 / 17 |

## quorumastar-max512: what reached the search (ops vs wastar-w2 = 100)

| case | queries | ops (geo. mean) | better / equal / worse |
|---|---|---|---|
| no waypoint reached the search | 73 | 100.0 | 0 / 73 / 0 |
| waypoints kept to the end | 13 | 114.2 | 3 / 6 / 4 |
| stall fallback fired | 14 | 127.0 | 3 / 0 / 11 |

## quorumastar-max512: the 10 queries most worse than wastar-w2

| map:sg | ops quorumastar-max512 | ops wastar-w2 | ops llmastar_standard-max512 | waypoints given | kept targets | stall fallback (pop) |
|---|---|---|---|---|---|---|
| 14:0 | 1117 | 188 | 2100 | 2 | 2 | no |
| 55:0 | 183 | 73 | 73 | 1 | 0 | yes (111) |
| 49:0 | 257 | 119 | 119 | 1 | 0 | yes (207) |
| 7:0 | 310 | 158 | 3276 | 1 | 0 | yes (179) |
| 70:0 | 210 | 110 | 2572 | 1 | 0 | yes (209) |
| 83:0 | 140 | 87 | 87 | 1 | 1 | no |
| 87:0 | 214 | 147 | 147 | 1 | 0 | yes (117) |
| 86:0 | 212 | 177 | 177 | 1 | 0 | yes (85) |
| 43:0 | 78 | 69 | 69 | 1 | 1 | no |
| 74:0 | 211 | 188 | 188 | 2 | 0 | yes (101) |

## Cost per query ($0.15 / $0.6 per 1M input / output tokens)

| run | LLM requests | prompt tokens | completion tokens | $ per query | $ per 1,000 queries | source |
|---|---|---|---|---|---|---|
| llmastar_standard-max512 | 1.00 | 806 | 115 | 0.00019 | 0.19 | raw log |
| quorumastar-max512 | 3.00 | 10,218 | 320 | 0.00172 | 1.72 | raw log |
