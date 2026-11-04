# Failure cases and cost: outputs/gpt_ablation300/gpt-4o-mini

Operations of each LLM run against wastar-w2 (= 100) and against llmastar_standard; a win is strictly fewer operations on a query, a tie the same number.

| run | vs wastar-w2: win / tie / loss | ops (geo. mean) | vs llmastar_standard: win / tie / loss |
|---|---|---|---|
| llmastar_standard | 63 / 45 / 192 | 145.5 | - |
| quorumastar | 25 / 258 / 17 | 99.3 | 198 / 36 / 66 |
| quorumastar-add1 | 86 / 94 / 120 | 107.2 | 188 / 16 / 96 |
| quorumastar-add3 | 18 / 275 / 7 | 98.5 | 197 / 40 / 63 |
| quorumastar-cot | 22 / 261 / 17 | 99.9 | 196 / 38 / 66 |
| quorumastar-fsnone | 45 / 219 / 36 | 98.8 | 202 / 35 / 63 |
| quorumastar-fsshared | 25 / 260 / 15 | 98.4 | 196 / 39 / 65 |
| quorumastar-nosnap | 1 / 291 / 8 | 100.3 | 190 / 43 / 67 |
| quorumastar-roles | 18 / 265 / 17 | 100.0 | 194 / 37 / 69 |
| quorumastar-vcorners-add1 | 117 / 50 / 133 | 112.5 | 184 / 6 / 110 |
| quorumastar-vrelations-add1 | 107 / 69 / 124 | 108.7 | 193 / 15 / 92 |
| quorumastar-vtext+corners+image | 17 / 272 / 11 | 99.9 | 197 / 38 / 65 |
| quorumastar-vtext+corners+relations+image | 23 / 249 / 28 | 101.1 | 192 / 35 / 73 |
| quorumastar-vtext-add1 | 87 / 88 / 125 | 107.9 | 188 / 19 / 93 |

## quorumastar: what reached the search (ops vs wastar-w2 = 100)

| case | queries | ops (geo. mean) | better / equal / worse |
|---|---|---|---|
| no waypoint reached the search | 232 | 100.0 | 0 / 232 / 0 |
| waypoints kept to the end | 50 | 90.7 | 19 / 21 / 10 |
| stall fallback fired | 18 | 117.0 | 6 / 5 / 7 |

## quorumastar: the 10 queries most worse than wastar-w2

| map:sg | ops quorumastar | ops wastar-w2 | ops llmastar_standard | waypoints given | kept targets | stall fallback (pop) |
|---|---|---|---|---|---|---|
| 10:0 | 56 | 20 | 28 | 2 | 1 | yes (52) |
| 13:3 | 141 | 54 | 81 | 2 | 0 | yes (73) |
| 25:0 | 48 | 25 | 121 | 1 | 0 | yes (41) |
| 3:0 | 197 | 128 | 342 | 1 | 0 | yes (55) |
| 6:1 | 45 | 34 | 35 | 1 | 1 | no |
| 26:1 | 70 | 58 | 58 | 2 | 2 | no |
| 27:8 | 21 | 18 | 65 | 1 | 1 | no |
| 9:3 | 28 | 25 | 36 | 1 | 1 | no |
| 8:0 | 255 | 228 | 247 | 1 | 0 | yes (41) |
| 26:6 | 21 | 19 | 27 | 1 | 1 | no |

## Cost per query ($0.15 / $0.6 per 1M input / output tokens)

| run | LLM requests | prompt tokens | completion tokens | $ per query | $ per 1,000 queries | source |
|---|---|---|---|---|---|---|
| llmastar_standard | 1.00 | 584 | 598 | 0.00045 | 0.45 | raw log |
| quorumastar | 3.75 | 33,537 | 50 | 0.00506 | 5.06 | raw log |
| quorumastar-add1 | 4.00 | 42,951 | 56 | 0.00648 | 6.48 | raw log |
| quorumastar-add3 | 3.15 | 11,319 | 46 | 0.00173 | 1.73 | raw log |
| quorumastar-cot | 3.72 | 32,615 | 50 | 0.00492 | 4.92 | raw log |
| quorumastar-fsnone | 4.00 | 38,866 | 92 | 0.00588 | 5.88 | raw log |
| quorumastar-fsshared | 3.72 | 31,206 | 49 | 0.00471 | 4.71 | raw log |
| quorumastar-nosnap | 3.39 | 20,452 | 48 | 0.00310 | 3.10 | raw log |
| quorumastar-roles | 3.70 | 31,723 | 50 | 0.00479 | 4.79 | raw log |
| quorumastar-vcorners-add1 | 2.00 | 40,121 | 20 | 0.00603 | 6.03 | raw log |
| quorumastar-vrelations-add1 | 2.00 | 37,807 | 24 | 0.00569 | 5.69 | raw log |
| quorumastar-vtext+corners+image | 3.61 | 64,509 | 99 | 0.00974 | 9.74 | raw log |
| quorumastar-vtext+corners+relations+image | 4.85 | 74,527 | 119 | 0.01125 | 11.25 | raw log |
| quorumastar-vtext-add1 | 2.00 | 37,600 | 23 | 0.00565 | 5.65 | raw log |
