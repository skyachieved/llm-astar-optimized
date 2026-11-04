# Failure cases and cost: outputs/gpt_zigzag/gpt-4o-mini

Operations of each LLM run against wastar-w2 (= 100) and against llmastar_standard; a win is strictly fewer operations on a query, a tie the same number.

| run | vs wastar-w2: win / tie / loss | ops (geo. mean) | vs llmastar_standard: win / tie / loss |
|---|---|---|---|
| llmastar_standard | 54 / 24 / 22 | 99.5 | - |
| quorumastar | 21 / 62 / 17 | 99.9 | 26 / 19 / 55 |
| quorumastar-vision | 6 / 88 / 6 | 100.0 | 24 / 21 / 55 |

## quorumastar: what reached the search (ops vs wastar-w2 = 100)

| case | queries | ops (geo. mean) | better / equal / worse |
|---|---|---|---|
| no waypoint reached the search | 49 | 100.0 | 0 / 49 / 0 |
| waypoints kept to the end | 14 | 99.6 | 6 / 4 / 4 |
| stall fallback fired | 37 | 100.0 | 15 / 9 / 13 |

## quorumastar: the 10 queries most worse than wastar-w2

| map:sg | ops quorumastar | ops wastar-w2 | ops llmastar_standard | waypoints given | kept targets | stall fallback (pop) |
|---|---|---|---|---|---|---|
| 73:0 | 917 | 909 | 880 | 1 | 0 | yes (95) |
| 88:0 | 1890 | 1881 | 1714 | 3 | 1 | yes (56) |
| 1:0 | 1913 | 1906 | 1745 | 1 | 0 | yes (85) |
| 9:0 | 1110 | 1106 | 1106 | 2 | 1 | yes (75) |
| 24:0 | 1961 | 1955 | 1936 | 1 | 1 | no |
| 22:0 | 2051 | 2045 | 1974 | 1 | 0 | yes (111) |
| 36:0 | 2079 | 2074 | 2079 | 2 | 1 | yes (56) |
| 3:0 | 1756 | 1752 | 1496 | 1 | 0 | yes (97) |
| 78:0 | 892 | 890 | 792 | 1 | 1 | no |
| 70:0 | 922 | 920 | 963 | 2 | 1 | yes (73) |

## Cost per query ($0.15 / $0.6 per 1M input / output tokens)

| run | LLM requests | prompt tokens | completion tokens | $ per query | $ per 1,000 queries | source |
|---|---|---|---|---|---|---|
| llmastar_standard | 1.00 | 575 | 652 | 0.00048 | 0.48 | raw log |
| quorumastar | 3.00 | 4,985 | 67 | 0.00079 | 0.79 | raw log |
| quorumastar-vision | 3.77 | 33,499 | 73 | 0.00507 | 5.07 | raw log |
