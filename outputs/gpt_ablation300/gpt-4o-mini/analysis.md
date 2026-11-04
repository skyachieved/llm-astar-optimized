# Failure cases and cost: outputs/gpt_ablation300/gpt-4o-mini

Operations of each LLM run against wastar-w2 (= 100) and against llmastar_standard; a win is strictly fewer operations on a query, a tie the same number.

| run | vs wastar-w2: win / tie / loss | ops (geo. mean) | vs llmastar_standard: win / tie / loss |
|---|---|---|---|
| llmastar_standard | 63 / 45 / 192 | 145.5 | - |
| quorumastar | 84 / 143 / 73 | 99.9 | 196 / 21 / 83 |
| quorumastar-add1 | 91 / 36 / 173 | 125.4 | 153 / 8 / 139 |
| quorumastar-add3 | 18 / 275 / 7 | 98.5 | 197 / 40 / 63 |
| quorumastar-cot | 75 / 157 / 68 | 99.7 | 194 / 25 / 81 |
| quorumastar-fsnone | 91 / 103 / 106 | 108.3 | 190 / 21 / 89 |
| quorumastar-fsshared | 82 / 158 / 60 | 98.3 | 201 / 27 / 72 |
| quorumastar-nosnap | 36 / 225 / 39 | 101.1 | 186 / 35 / 79 |
| quorumastar-roles | 72 / 160 / 68 | 101.1 | 193 / 25 / 82 |
| quorumastar-vcorners-add1 | 117 / 50 / 133 | 112.7 | 183 / 6 / 111 |
| quorumastar-vision | 25 / 258 / 17 | 99.3 | 198 / 36 / 66 |
| quorumastar-vrelations-add1 | 110 / 60 / 130 | 110.1 | 190 / 14 / 96 |
| quorumastar-vtext+corners+image | 62 / 188 / 50 | 101.1 | 197 / 32 / 71 |
| quorumastar-vtext+corners+relations+image | 93 / 112 / 95 | 101.3 | 199 / 20 / 81 |
| quorumastar-vtext-add1 | 86 / 81 / 133 | 109.5 | 183 / 16 / 101 |

## quorumastar: what reached the search (ops vs wastar-w2 = 100)

| case | queries | ops (geo. mean) | better / equal / worse |
|---|---|---|---|
| no waypoint reached the search | 81 | 100.0 | 0 / 81 / 0 |
| waypoints kept to the end | 150 | 92.7 | 60 / 49 / 41 |
| stall fallback fired | 69 | 117.7 | 24 / 13 / 32 |

## quorumastar: the 10 queries most worse than wastar-w2

| map:sg | ops quorumastar | ops wastar-w2 | ops llmastar_standard | waypoints given | kept targets | stall fallback (pop) |
|---|---|---|---|---|---|---|
| 1:4 | 77 | 22 | 22 | 2 | 1 | yes (72) |
| 3:7 | 46 | 14 | 16 | 2 | 0 | yes (41) |
| 10:0 | 56 | 20 | 28 | 3 | 0 | yes (41) |
| 7:4 | 72 | 26 | 41 | 2 | 0 | yes (59) |
| 25:0 | 66 | 25 | 121 | 2 | 1 | yes (63) |
| 13:3 | 141 | 54 | 81 | 2 | 0 | yes (73) |
| 8:9 | 91 | 38 | 41 | 1 | 1 | no |
| 18:2 | 61 | 28 | 88 | 2 | 1 | yes (57) |
| 10:6 | 54 | 26 | 692 | 1 | 0 | yes (41) |
| 27:0 | 35 | 18 | 29 | 2 | 2 | no |

## Cost per query ($0.15 / $0.6 per 1M input / output tokens)

| run | LLM requests | prompt tokens | completion tokens | $ per query | $ per 1,000 queries | source |
|---|---|---|---|---|---|---|
| llmastar_standard | 1.00 | 584 | 598 | 0.00045 | 0.45 | raw log |
| quorumastar | 3.00 | 5,888 | 45 | 0.00091 | 0.91 | raw log |
| quorumastar-add1 | 3.00 | 5,888 | 45 | 0.00091 | 0.91 | raw log |
| quorumastar-add3 | 3.00 | 5,888 | 45 | 0.00091 | 0.91 | raw log |
| quorumastar-cot | 3.00 | 5,954 | 45 | 0.00092 | 0.92 | raw log |
| quorumastar-fsnone | 3.00 | 1,819 | 82 | 0.00032 | 0.32 | raw log |
| quorumastar-fsshared | 3.00 | 4,421 | 44 | 0.00069 | 0.69 | raw log |
| quorumastar-nosnap | 3.00 | 5,888 | 45 | 0.00091 | 0.91 | raw log |
| quorumastar-roles | 3.00 | 5,926 | 45 | 0.00092 | 0.92 | raw log |
| quorumastar-vcorners-add1 | 1.00 | 3,082 | 11 | 0.00047 | 0.47 | raw log |
| quorumastar-vision | 3.75 | 33,537 | 50 | 0.00506 | 5.06 | raw log |
| quorumastar-vrelations-add1 | 1.00 | 773 | 16 | 0.00013 | 0.13 | raw log |
| quorumastar-vtext+corners+image | 3.00 | 42,044 | 95 | 0.00636 | 6.36 | raw log |
| quorumastar-vtext+corners+relations+image | 4.00 | 42,925 | 113 | 0.00651 | 6.51 | raw log |
| quorumastar-vtext-add1 | 1.00 | 566 | 16 | 0.00009 | 0.09 | raw log |
