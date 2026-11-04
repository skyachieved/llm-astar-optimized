# Failure cases and cost: outputs/gpt_zigzag/gpt-4o-mini

Operations of each LLM run against wastar-w2 (= 100) and against llmastar_standard; a win is strictly fewer operations on a query, a tie the same number.

| run | vs wastar-w2: win / tie / loss | ops (geo. mean) | vs llmastar_standard: win / tie / loss |
|---|---|---|---|
| llmastar_standard | 54 / 24 / 22 | 99.5 | - |
| quorumastar | 6 / 88 / 6 | 100.0 | 24 / 21 / 55 |

## quorumastar: what reached the search (ops vs wastar-w2 = 100)

| case | queries | ops (geo. mean) | better / equal / worse |
|---|---|---|---|
| no waypoint reached the search | 86 | 100.0 | 0 / 86 / 0 |
| waypoints kept to the end | 2 | 100.1 | 0 / 0 / 2 |
| stall fallback fired | 12 | 100.0 | 6 / 2 / 4 |

## quorumastar: the 10 queries most worse than wastar-w2

| map:sg | ops quorumastar | ops wastar-w2 | ops llmastar_standard | waypoints given | kept targets | stall fallback (pop) |
|---|---|---|---|---|---|---|
| 88:0 | 1890 | 1881 | 1714 | 1 | 0 | yes (61) |
| 1:0 | 1913 | 1906 | 1745 | 1 | 0 | yes (85) |
| 36:0 | 2079 | 2074 | 2079 | 2 | 1 | yes (56) |
| 70:0 | 922 | 920 | 963 | 1 | 1 | no |
| 44:0 | 1695 | 1693 | 1543 | 1 | 0 | yes (103) |
| 11:0 | 1988 | 1987 | 1987 | 1 | 1 | no |
| 0:0 | 2034 | 2034 | 1912 | 0 | 0 | no |
| 2:0 | 2031 | 2031 | 2034 | 0 | 0 | no |
| 3:0 | 1752 | 1752 | 1496 | 0 | 0 | no |
| 4:0 | 1552 | 1552 | 1552 | 1 | 0 | yes (103) |

## Cost per query ($0.15 / $0.6 per 1M input / output tokens)

| run | LLM requests | prompt tokens | completion tokens | $ per query | $ per 1,000 queries | source |
|---|---|---|---|---|---|---|
| llmastar_standard | 1.00 | 575 | 652 | 0.00048 | 0.48 | raw log |
| quorumastar | 3.77 | 33,499 | 73 | 0.00507 | 5.07 | raw log |
