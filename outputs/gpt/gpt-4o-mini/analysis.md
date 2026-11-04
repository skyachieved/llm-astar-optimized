# Failure cases and cost: outputs/gpt/gpt-4o-mini

Operations of each LLM run against wastar-w2 (= 100) and against llmastar_standard; a win is strictly fewer operations on a query, a tie the same number. Left out (fewer than half of the 1000 queries): quorumastar-vtext-fspaper-nosnap-add1-novision-k0.

| run | vs wastar-w2: win / tie / loss | ops (geo. mean) | vs llmastar_standard: win / tie / loss |
|---|---|---|---|
| llmastar_cot | 214 / 168 / 618 | 141.4 | 471 / 103 / 426 |
| llmastar_repe | 233 / 131 / 636 | 148.2 | 486 / 62 / 452 |
| llmastar_standard | 203 / 139 / 658 | 147.2 | - |
| quorumastar | 74 / 873 / 53 | 99.4 | 669 / 125 / 206 |
| quorumastar-k0 | 74 / 861 / 65 | 100.5 | 664 / 123 / 213 |
| quorumastar-novision | 249 / 508 / 243 | 98.9 | 681 / 86 / 233 |
| quorumastar-rm0 | 257 / 487 / 256 | 99.2 | 679 / 85 / 236 |

## quorumastar: what reached the search (ops vs wastar-w2 = 100)

| case | queries | ops (geo. mean) | better / equal / worse |
|---|---|---|---|
| no waypoint reached the search | 792 | 100.0 | 0 / 792 / 0 |
| waypoints kept to the end | 156 | 93.4 | 58 / 67 / 31 |
| stall fallback fired | 52 | 109.1 | 16 / 14 / 22 |

## quorumastar: the 10 queries most worse than wastar-w2

| map:sg | ops quorumastar | ops wastar-w2 | ops llmastar_standard | waypoints given | kept targets | stall fallback (pop) |
|---|---|---|---|---|---|---|
| 34:2 | 298 | 82 | 31 | 1 | 1 | no |
| 10:0 | 56 | 20 | 28 | 2 | 1 | yes (52) |
| 13:3 | 141 | 54 | 81 | 2 | 0 | yes (73) |
| 79:5 | 53 | 22 | 112 | 2 | 1 | yes (48) |
| 25:0 | 48 | 25 | 121 | 1 | 0 | yes (41) |
| 91:7 | 38 | 20 | 33 | 1 | 1 | no |
| 34:9 | 49 | 29 | 229 | 1 | 1 | no |
| 50:7 | 68 | 43 | 51 | 2 | 1 | yes (48) |
| 3:0 | 197 | 128 | 342 | 1 | 0 | yes (55) |
| 79:2 | 34 | 25 | 87 | 1 | 1 | no |

## Cost per query ($0.15 / $0.6 per 1M input / output tokens)

| run | LLM requests | prompt tokens | completion tokens | $ per query | $ per 1,000 queries | source |
|---|---|---|---|---|---|---|
| llmastar_cot | 1.00 | 611 | 384 | 0.00032 | 0.32 | raw log |
| llmastar_repe | 1.00 | 1,163 | 622 | 0.00055 | 0.55 | raw log |
| llmastar_standard | 1.00 | 585 | 596 | 0.00045 | 0.45 | raw log |
| quorumastar | 3.71 | 32,185 | 50 | 0.00486 | 4.86 | raw log |
| quorumastar-k0 | 3.71 | 32,185 | 50 | 0.00486 | 4.86 | raw log |
| quorumastar-novision | 3.00 | 5,895 | 46 | 0.00091 | 0.91 | raw log |
| quorumastar-rm0 | 3.00 | 5,895 | 46 | 0.00091 | 0.91 | raw log |
