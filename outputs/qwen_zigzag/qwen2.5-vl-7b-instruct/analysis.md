# Failure cases and cost: outputs/qwen_zigzag/qwen2.5-vl-7b-instruct

Operations of each LLM run against wastar-w2 (= 100) and against llmastar_standard-max512; a win is strictly fewer operations on a query, a tie the same number.

| run | vs wastar-w2: win / tie / loss | ops (geo. mean) | vs llmastar_standard-max512: win / tie / loss |
|---|---|---|---|
| llmastar_standard-max512 | 0 / 100 / 0 | 100.0 | - |
| quorumastar-max512 | 10 / 70 / 20 | 100.0 | 10 / 70 / 20 |

## quorumastar-max512: what reached the search (ops vs wastar-w2 = 100)

| case | queries | ops (geo. mean) | better / equal / worse |
|---|---|---|---|
| no waypoint reached the search | 60 | 100.0 | 0 / 60 / 0 |
| waypoints kept to the end | 2 | 94.7 | 1 / 0 / 1 |
| stall fallback fired | 38 | 100.3 | 9 / 10 / 19 |

## quorumastar-max512: the 10 queries most worse than wastar-w2

| map:sg | ops quorumastar-max512 | ops wastar-w2 | ops llmastar_standard-max512 | waypoints given | kept targets | stall fallback (pop) |
|---|---|---|---|---|---|---|
| 90:0 | 1762 | 1698 | 1698 | 1 | 0 | yes (55) |
| 23:0 | 1728 | 1685 | 1685 | 1 | 0 | yes (53) |
| 16:0 | 1509 | 1474 | 1474 | 2 | 0 | yes (55) |
| 53:0 | 1493 | 1474 | 1474 | 3 | 1 | yes (54) |
| 97:0 | 2240 | 2226 | 2226 | 1 | 0 | yes (101) |
| 11:0 | 1997 | 1987 | 1987 | 3 | 0 | yes (45) |
| 88:0 | 1890 | 1881 | 1881 | 1 | 0 | yes (57) |
| 29:0 | 1874 | 1866 | 1866 | 1 | 0 | yes (115) |
| 50:0 | 1875 | 1867 | 1867 | 1 | 0 | yes (41) |
| 69:0 | 1654 | 1647 | 1647 | 1 | 0 | yes (51) |

## Cost per query ($0.15 / $0.6 per 1M input / output tokens)

| run | LLM requests | prompt tokens | completion tokens | $ per query | $ per 1,000 queries | source |
|---|---|---|---|---|---|---|
| llmastar_standard-max512 | 1.00 | 708 | 18 | 0.00012 | 0.12 | raw log |
| quorumastar-max512 | 3.00 | 5,600 | 78 | 0.00089 | 0.89 | raw log |
