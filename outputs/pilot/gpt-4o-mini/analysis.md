# Failure cases and cost: outputs/pilot/gpt-4o-mini

Operations of each LLM run against wastar-w2 (= 100) and against llmastar_standard; a win is strictly fewer operations on a query, a tie the same number.

| run | vs wastar-w2: win / tie / loss | ops (geo. mean) | vs llmastar_standard: win / tie / loss |
|---|---|---|---|
| llmastar_standard | 10 / 5 / 35 | 147.6 | - |
| quorumastar | 3 / 46 / 1 | 96.1 | 36 / 5 / 9 |
| quorumastar-novision | 15 / 23 / 12 | 94.2 | 37 / 4 / 9 |
| quorumastar-vtext+corners+image+relations | 2 / 48 / 0 | 98.5 | 36 / 5 / 9 |
| quorumastar-vtext+corners+image+relations-novision | 16 / 16 / 18 | 99.7 | 35 / 6 / 9 |
| quorumastar-vtext+corners+image+relations-rm0 | 15 / 16 / 19 | 100.2 | 34 / 6 / 10 |
| quorumastar-vtext+corners+relations | 3 / 46 / 1 | 96.1 | 36 / 5 / 9 |

## quorumastar: what reached the search (ops vs wastar-w2 = 100)

| case | queries | ops (geo. mean) | better / equal / worse |
|---|---|---|---|
| no waypoint reached the search | 43 | 100.0 | 0 / 43 / 0 |
| waypoints kept to the end | 7 | 75.2 | 3 / 3 / 1 |
| stall fallback fired | 0 | - | 0 / 0 / 0 |

## quorumastar: the 10 queries most worse than wastar-w2

| map:sg | ops quorumastar | ops wastar-w2 | ops llmastar_standard | waypoints given | kept targets | stall fallback (pop) |
|---|---|---|---|---|---|---|
| 42:0 | 23 | 21 | 29 | 2 | 2 | no |
| 0:0 | 56 | 56 | 112 | 0 | 0 | no |
| 1:0 | 90 | 90 | 432 | 0 | 0 | no |
| 2:0 | 21 | 21 | 30 | 0 | 0 | no |
| 3:0 | 43 | 43 | 221 | 0 | 0 | no |
| 4:0 | 38 | 38 | 68 | 0 | 0 | no |
| 5:0 | 60 | 60 | 88 | 0 | 0 | no |
| 6:0 | 732 | 732 | 732 | 0 | 0 | no |
| 7:0 | 51 | 51 | 48 | 0 | 0 | no |
| 8:0 | 39 | 39 | 53 | 0 | 0 | no |

## Cost per query ($0.15 / $0.6 per 1M input / output tokens)

| run | LLM requests | prompt tokens | completion tokens | $ per query | $ per 1,000 queries | source |
|---|---|---|---|---|---|---|
| llmastar_standard | 1.00 | 575 | 540 | 0.00041 | 0.41 | raw log |
| quorumastar | 3.76 | 33,886 | 50 | 0.00511 | 5.11 | raw log |
| quorumastar-novision | 3.00 | 5,745 | 45 | 0.00089 | 0.89 | raw log |
| quorumastar-vtext+corners+image+relations | 4.90 | 76,098 | 129 | 0.01149 | 11.49 | raw log |
| quorumastar-vtext+corners+image+relations-novision | 4.00 | 42,769 | 122 | 0.00649 | 6.49 | raw log |
| quorumastar-vtext+corners+image+relations-rm0 | 4.00 | 42,769 | 122 | 0.00649 | 6.49 | raw log |
| quorumastar-vtext+corners+relations | 3.76 | 33,886 | 50 | 0.00511 | 5.11 | raw log |
