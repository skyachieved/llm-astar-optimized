# Failure cases and cost: outputs/qwen_pilot/qwen2.5-vl-7b-instruct

Operations of each LLM run against wastar-w2 (= 100) and against llmastar_standard-max512; a win is strictly fewer operations on a query, a tie the same number.

| run | vs wastar-w2: win / tie / loss | ops (geo. mean) | vs llmastar_standard-max512: win / tie / loss |
|---|---|---|---|
| llmastar_standard-max512 | 9 / 31 / 10 | 99.6 | - |
| quorumastar-max512 | 6 / 40 / 4 | 97.8 | 13 / 26 / 11 |
| quorumastar-vision-max512 | 1 / 48 / 1 | 101.1 | 11 / 29 / 10 |
| quorumastar-vtext+corners+image+relations-vision-max512 | 3 / 46 / 1 | 101.1 | 11 / 29 / 10 |
| quorumastar-vtext+corners+image-max512 | 5 / 41 / 4 | 103.0 | 12 / 27 / 11 |

## quorumastar-max512: what reached the search (ops vs wastar-w2 = 100)

| case | queries | ops (geo. mean) | better / equal / worse |
|---|---|---|---|
| no waypoint reached the search | 34 | 100.0 | 0 / 34 / 0 |
| waypoints kept to the end | 13 | 86.5 | 5 / 5 / 3 |
| stall fallback fired | 3 | 128.7 | 1 / 1 / 1 |

## quorumastar-max512: the 10 queries most worse than wastar-w2

| map:sg | ops quorumastar-max512 | ops wastar-w2 | ops llmastar_standard-max512 | waypoints given | kept targets | stall fallback (pop) |
|---|---|---|---|---|---|---|
| 45:0 | 126 | 59 | 59 | 1 | 0 | yes (41) |
| 30:0 | 115 | 95 | 176 | 1 | 1 | no |
| 5:0 | 72 | 60 | 60 | 1 | 1 | no |
| 22:0 | 42 | 37 | 37 | 1 | 1 | no |
| 0:0 | 56 | 56 | 56 | 0 | 0 | no |
| 1:0 | 90 | 90 | 177 | 0 | 0 | no |
| 2:0 | 21 | 21 | 21 | 1 | 1 | no |
| 4:0 | 38 | 38 | 38 | 0 | 0 | no |
| 6:0 | 732 | 732 | 727 | 0 | 0 | no |
| 7:0 | 51 | 51 | 51 | 0 | 0 | no |

## Cost per query ($0.15 / $0.6 per 1M input / output tokens)

| run | LLM requests | prompt tokens | completion tokens | $ per query | $ per 1,000 queries | source |
|---|---|---|---|---|---|---|
| llmastar_standard-max512 | 1.00 | 710 | 24 | 0.00012 | 0.12 | raw log |
| quorumastar-max512 | 3.00 | 6,480 | 92 | 0.00103 | 1.03 | raw log |
| quorumastar-vision-max512 | 3.38 | 6,912 | 95 | 0.00109 | 1.09 | raw log |
| quorumastar-vtext+corners+image+relations-vision-max512 | 4.54 | 8,220 | 106 | 0.00130 | 1.30 | raw log |
| quorumastar-vtext+corners+image-max512 | 3.00 | 6,675 | 88 | 0.00105 | 1.05 | raw log |
