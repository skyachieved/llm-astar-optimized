# Pilot report: quorumastar (50 queries, outputs_pilot/gpt-4o-mini)

## Solo quality per view

| view | abstained | waypoints | good | queries with a good waypoint |
|---|---|---|---|---|
| text | 0/50 | 94 | 53.2% | 78.0% |
| corners | 0/50 | 117 | 54.7% | 80.0% |
| image | 0/50 | 521 | 57.8% | 100.0% |

## Shared bad waypoints (row view's bad waypoints also proposed by the column view; lower = more independent)

| bad of \ also in | text | corners | image |
|---|---|---|---|
| text | - | 6.8% | 11.4% |
| corners | 5.7% | - | 9.4% |
| image | 2.3% | 2.3% | - |

## Voting

As run: 33/50 queries kept at least one waypoint by vote; final waypoints 10, good 90.0%.

Simulated from the same answers (quorum 2): queries with a kept waypoint / kept waypoints / good share.

| views | r = 0 | r = 1 | r = 2 | r = 3 |
|---|---|---|---|---|
| text,corners,image | 33 / 51 / 74.5% | 37 / 62 / 75.8% | 45 / 73 / 64.4% | 47 / 77 / 63.6% |

## Vision judge

catch rate 92.3% (12/13 bad waypoints removed), false-alarm rate 81.6% (31/38 good removed), abstained 0.

## Search (geometric mean vs A* = 100, lower is better)

| run | n | operation | storage | length |
|---|---|---|---|---|
| astar | 50 | 100.00 | 100.00 | 100.00 |
| wastar-w2 | 50 | 24.34 | 49.25 | 103.18 |
| llmastar_standard | 50 | 35.92 | 61.07 | 102.89 |
| quorumastar | 50 | 24.05 | 49.04 | 103.10 |

## Every LLM run vs weighted A* (w = 2, = 100), by whether the search kept waypoints

| run | waypoints | n | operation | storage | stall fallback |
|---|---|---|---|---|---|
| llmastar_standard | used | 47 | 151.3 | 125.7 | 0 |
| llmastar_standard | none | 3 | 100.0 | 100.0 | 0 |
| quorumastar-vtext+corners+image+relations-novision | used | 38 | 96.1 | 99.4 | 3 |
| quorumastar-vtext+corners+image+relations-novision | none | 12 | 112.2 | 103.2 | 6 |
| quorumastar-vtext+corners+image+relations-rm0 | used | 39 | 96.8 | 100.1 | 3 |
| quorumastar-vtext+corners+image+relations-rm0 | none | 11 | 113.4 | 103.5 | 6 |
| quorumastar-vtext+corners+image+relations | used | 12 | 93.9 | 98.7 | 0 |
| quorumastar-vtext+corners+image+relations | none | 38 | 100.0 | 100.0 | 0 |
| quorumastar-vtext+corners+relations | used | 7 | 75.2 | 87.0 | 0 |
| quorumastar-vtext+corners+relations | none | 43 | 100.0 | 100.0 | 0 |
| quorumastar | used | 10 | 94.1 | 97.9 | 0 |
| quorumastar | none | 40 | 100.0 | 100.0 | 0 |

LLM: 14 new calls, 3323880 tokens (66478 per query).
