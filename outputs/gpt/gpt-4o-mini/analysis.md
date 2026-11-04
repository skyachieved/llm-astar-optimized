# Failure cases and cost: outputs/gpt/gpt-4o-mini

Operations of each LLM run against wastar-w2 (= 100) and against llmastar_standard; a win is strictly fewer operations on a query, a tie the same number.

| run | vs wastar-w2: win / tie / loss | ops (geo. mean) | vs llmastar_standard: win / tie / loss |
|---|---|---|---|
| llmastar_cot | 214 / 168 / 618 | 141.4 | 471 / 103 / 426 |
| llmastar_repe | 233 / 131 / 636 | 148.2 | 486 / 62 / 452 |
| llmastar_standard | 203 / 139 / 658 | 147.2 | - |
| quorumastar | 249 / 508 / 243 | 98.9 | 681 / 86 / 233 |
| quorumastar-k0 | 257 / 477 / 266 | 102.9 | 669 / 84 / 247 |
| quorumastar-rm0 | 257 / 487 / 256 | 99.2 | 679 / 85 / 236 |
| quorumastar-vision | 74 / 873 / 53 | 99.4 | 669 / 125 / 206 |
| quorumastar-vtext-fspaper-nosnap-add1-k0 | 203 / 139 / 658 | 147.2 | 0 / 1000 / 0 |

## quorumastar: what reached the search (ops vs wastar-w2 = 100)

| case | queries | ops (geo. mean) | better / equal / worse |
|---|---|---|---|
| no waypoint reached the search | 326 | 100.0 | 0 / 326 / 0 |
| waypoints kept to the end | 462 | 91.9 | 191 / 146 / 125 |
| stall fallback fired | 212 | 114.2 | 58 / 36 / 118 |

## quorumastar: the 10 queries most worse than wastar-w2

| map:sg | ops quorumastar | ops wastar-w2 | ops llmastar_standard | waypoints given | kept targets | stall fallback (pop) |
|---|---|---|---|---|---|---|
| 30:4 | 43 | 10 | 20 | 2 | 0 | yes (41) |
| 1:4 | 77 | 22 | 22 | 2 | 1 | yes (72) |
| 3:7 | 46 | 14 | 16 | 2 | 0 | yes (41) |
| 10:0 | 56 | 20 | 28 | 3 | 0 | yes (41) |
| 7:4 | 72 | 26 | 41 | 2 | 0 | yes (59) |
| 25:0 | 66 | 25 | 121 | 2 | 1 | yes (63) |
| 13:3 | 141 | 54 | 81 | 2 | 0 | yes (73) |
| 58:8 | 44 | 17 | 26 | 2 | 0 | yes (41) |
| 85:9 | 51 | 20 | 33 | 2 | 1 | yes (46) |
| 81:9 | 81 | 32 | 69 | 2 | 1 | yes (79) |

## Cost per query ($0.15 / $0.6 per 1M input / output tokens)

| run | LLM requests | prompt tokens | completion tokens | $ per query | $ per 1,000 queries | source |
|---|---|---|---|---|---|---|
| llmastar_cot | 1.00 | 611 | 384 | 0.00032 | 0.32 | raw log |
| llmastar_repe | 1.00 | 1,163 | 622 | 0.00055 | 0.55 | raw log |
| llmastar_standard | 1.00 | 585 | 596 | 0.00045 | 0.45 | raw log |
| quorumastar | 3.00 | 5,895 | 46 | 0.00091 | 0.91 | raw log |
| quorumastar-k0 | 3.00 | 5,895 | 46 | 0.00091 | 0.91 | raw log |
| quorumastar-rm0 | 3.00 | 5,895 | 46 | 0.00091 | 0.91 | raw log |
| quorumastar-vision | 3.71 | 32,185 | 50 | 0.00486 | 4.86 | raw log |
| quorumastar-vtext-fspaper-nosnap-add1-k0 | 1.00 | 585 | 596 | 0.00045 | 0.45 | raw log |
