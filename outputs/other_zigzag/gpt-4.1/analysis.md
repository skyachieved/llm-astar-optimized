# Failure cases and cost: outputs/other_zigzag/gpt-4.1

Operations of each LLM run against wastar-w2 (= 100) and against llmastar_standard; a win is strictly fewer operations on a query, a tie the same number.

| run | vs wastar-w2: win / tie / loss | ops (geo. mean) | vs llmastar_standard: win / tie / loss |
|---|---|---|---|
| llmastar_standard | 41 / 29 / 30 | 100.8 | - |
| quorumastar | 39 / 27 / 34 | 100.0 | 43 / 16 / 41 |

## quorumastar: what reached the search (ops vs wastar-w2 = 100)

| case | queries | ops (geo. mean) | better / equal / worse |
|---|---|---|---|
| no waypoint reached the search | 6 | 100.0 | 0 / 6 / 0 |
| waypoints kept to the end | 9 | 99.8 | 6 / 3 / 0 |
| stall fallback fired | 85 | 100.1 | 33 / 18 / 34 |

## quorumastar: the 10 queries most worse than wastar-w2

| map:sg | ops quorumastar | ops wastar-w2 | ops llmastar_standard | waypoints given | kept targets | stall fallback (pop) |
|---|---|---|---|---|---|---|
| 7:0 | 1885 | 1831 | 1763 | 3 | 1 | yes (74) |
| 23:0 | 1728 | 1685 | 1619 | 2 | 1 | yes (55) |
| 57:0 | 2132 | 2084 | 2084 | 3 | 1 | yes (79) |
| 47:0 | 1925 | 1898 | 1893 | 3 | 0 | yes (69) |
| 68:0 | 1004 | 990 | 1020 | 3 | 1 | yes (45) |
| 53:0 | 1493 | 1474 | 1452 | 2 | 1 | yes (54) |
| 35:0 | 1153 | 1141 | 1583 | 1 | 0 | yes (91) |
| 11:0 | 2000 | 1987 | 1987 | 2 | 1 | yes (78) |
| 50:0 | 1879 | 1867 | 1741 | 3 | 1 | yes (44) |
| 93:0 | 1867 | 1856 | 1856 | 2 | 1 | yes (83) |

## Cost per query ($2.0 / $8.0 per 1M input / output tokens)

| run | LLM requests | prompt tokens | completion tokens | $ per query | $ per 1,000 queries | source |
|---|---|---|---|---|---|---|
| llmastar_standard | 1.00 | 575 | 742 | 0.00709 | 7.09 | raw log |
| quorumastar | 3.00 | 4,985 | 78 | 0.01059 | 10.59 | raw log |
