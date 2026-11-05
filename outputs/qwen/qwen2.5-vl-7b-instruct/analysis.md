# Failure cases and cost: outputs/qwen/qwen2.5-vl-7b-instruct

Operations of each LLM run against wastar-w2 (= 100) and against llmastar_standard-max512; a win is strictly fewer operations on a query, a tie the same number.

| run | vs wastar-w2: win / tie / loss | ops (geo. mean) | vs llmastar_standard-max512: win / tie / loss |
|---|---|---|---|
| llmastar_standard-max512 | 90 / 721 / 189 | 110.8 | - |
| quorumastar-max512 | 134 / 689 / 177 | 103.5 | 275 / 499 / 226 |
| quorumastar-vtext-fspaper-nosnap-add1-k0-max512 | 90 / 721 / 189 | 110.8 | 0 / 1000 / 0 |

## quorumastar-max512: what reached the search (ops vs wastar-w2 = 100)

| case | queries | ops (geo. mean) | better / equal / worse |
|---|---|---|---|
| no waypoint reached the search | 588 | 100.0 | 0 / 588 / 0 |
| waypoints kept to the end | 252 | 100.1 | 88 / 85 / 79 |
| stall fallback fired | 160 | 123.9 | 46 / 16 / 98 |

## quorumastar-max512: the 10 queries most worse than wastar-w2

| map:sg | ops quorumastar-max512 | ops wastar-w2 | ops llmastar_standard-max512 | waypoints given | kept targets | stall fallback (pop) |
|---|---|---|---|---|---|---|
| 76:4 | 66 | 12 | 12 | 1 | 1 | no |
| 79:8 | 124 | 23 | 29 | 1 | 0 | yes (53) |
| 30:9 | 115 | 22 | 22 | 2 | 0 | yes (41) |
| 41:7 | 110 | 22 | 35 | 2 | 0 | yes (63) |
| 35:8 | 93 | 22 | 22 | 1 | 0 | yes (79) |
| 41:1 | 140 | 37 | 37 | 1 | 1 | no |
| 56:9 | 103 | 30 | 489 | 2 | 1 | yes (95) |
| 28:1 | 91 | 28 | 28 | 1 | 0 | yes (67) |
| 3:8 | 49 | 16 | 16 | 1 | 0 | yes (41) |
| 92:1 | 88 | 30 | 30 | 1 | 0 | yes (83) |

## Cost per query ($0.15 / $0.6 per 1M input / output tokens)

| run | LLM requests | prompt tokens | completion tokens | $ per query | $ per 1,000 queries | source |
|---|---|---|---|---|---|---|
| llmastar_standard-max512 | 1.00 | 724 | 27 | 0.00012 | 0.12 | raw log |
| quorumastar-max512 | 3.00 | 6,659 | 131 | 0.00108 | 1.08 | raw log |
| quorumastar-vtext-fspaper-nosnap-add1-k0-max512 | 1.00 | 724 | 27 | 0.00012 | 0.12 | raw log |
