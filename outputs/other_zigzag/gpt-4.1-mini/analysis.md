# Failure cases and cost: outputs/other_zigzag/gpt-4.1-mini

Operations of each LLM run against wastar-w2 (= 100) and against llmastar_standard; a win is strictly fewer operations on a query, a tie the same number.

| run | vs wastar-w2: win / tie / loss | ops (geo. mean) | vs llmastar_standard: win / tie / loss |
|---|---|---|---|
| llmastar_standard | 26 / 50 / 24 | 100.6 | - |
| quorumastar | 35 / 32 / 33 | 100.0 | 39 / 21 / 40 |

## quorumastar: what reached the search (ops vs wastar-w2 = 100)

| case | queries | ops (geo. mean) | better / equal / worse |
|---|---|---|---|
| no waypoint reached the search | 7 | 100.0 | 0 / 7 / 0 |
| waypoints kept to the end | 10 | 99.8 | 3 / 6 / 1 |
| stall fallback fired | 83 | 100.0 | 32 / 19 / 32 |

## quorumastar: the 10 queries most worse than wastar-w2

| map:sg | ops quorumastar | ops wastar-w2 | ops llmastar_standard | waypoints given | kept targets | stall fallback (pop) |
|---|---|---|---|---|---|---|
| 7:0 | 1887 | 1831 | 1597 | 1 | 0 | yes (81) |
| 16:0 | 1509 | 1474 | 1494 | 2 | 1 | yes (57) |
| 57:0 | 2132 | 2084 | 2084 | 3 | 1 | yes (79) |
| 77:0 | 1568 | 1547 | 1547 | 4 | 2 | yes (75) |
| 35:0 | 1153 | 1141 | 1285 | 1 | 0 | yes (91) |
| 94:0 | 905 | 899 | 928 | 4 | 1 | yes (89) |
| 93:0 | 1867 | 1856 | 1849 | 2 | 1 | yes (83) |
| 97:0 | 2239 | 2226 | 2222 | 2 | 1 | yes (101) |
| 91:0 | 1426 | 1418 | 1418 | 3 | 1 | yes (57) |
| 69:0 | 1656 | 1647 | 1656 | 3 | 1 | yes (53) |

## Cost per query ($0.4 / $1.6 per 1M input / output tokens)

| run | LLM requests | prompt tokens | completion tokens | $ per query | $ per 1,000 queries | source |
|---|---|---|---|---|---|---|
| llmastar_standard | 1.00 | 575 | 1,060 | 0.00193 | 1.93 | raw log |
| quorumastar | 3.00 | 4,985 | 77 | 0.00212 | 2.12 | raw log |
