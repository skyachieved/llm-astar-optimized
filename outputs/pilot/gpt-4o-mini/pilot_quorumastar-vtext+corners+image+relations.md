# Pilot report: quorumastar-vtext+corners+image+relations (50 queries, outputs_pilot/gpt-4o-mini)

## Solo quality per view

| view | abstained | waypoints | good | queries with a good waypoint |
|---|---|---|---|---|
| text | 0/50 | 94 | 53.2% | 78.0% |
| corners | 0/50 | 117 | 54.7% | 80.0% |
| image | 0/50 | 521 | 57.8% | 100.0% |
| relations | 0/50 | 93 | 62.4% | 86.0% |

## Shared bad waypoints (row view's bad waypoints also proposed by the column view; lower = more independent)

| bad of \ also in | text | corners | image | relations |
|---|---|---|---|---|
| text | - | 6.8% | 11.4% | 25.0% |
| corners | 5.7% | - | 9.4% | 15.1% |
| image | 2.3% | 2.3% | - | 2.3% |
| relations | 31.4% | 22.9% | 14.3% | - |

## Voting

As run: 45/50 queries kept at least one waypoint by vote; final waypoints 12, good 83.3%.

Simulated from the same answers (quorum 2): queries with a kept waypoint / kept waypoints / good share.

| views | r = 0 | r = 1 | r = 2 | r = 3 |
|---|---|---|---|---|
| text,corners,image,relations | 45 / 80 / 66.2% | 46 / 91 / 67.0% | 49 / 100 / 61.0% | 50 / 102 / 63.7% |
| text,corners,image | 33 / 51 / 74.5% | 37 / 62 / 75.8% | 45 / 73 / 64.4% | 47 / 77 / 63.6% |
| text,corners,relations | 41 / 55 / 63.6% | 42 / 57 / 64.9% | 47 / 66 / 59.1% | 48 / 70 / 58.6% |
| text,image,relations | 32 / 45 / 66.7% | 39 / 57 / 68.4% | 46 / 74 / 63.5% | 47 / 77 / 63.6% |
| corners,image,relations | 39 / 51 / 68.6% | 41 / 59 / 67.8% | 42 / 65 / 64.6% | 45 / 70 / 68.6% |

## Vision judge

catch rate 88.9% (24/27 bad waypoints removed), false-alarm rate 83.0% (44/53 good removed), abstained 0.

## Search (geometric mean vs A* = 100, lower is better)

| run | n | operation | storage | length |
|---|---|---|---|---|
| astar | 50 | 100.00 | 100.00 | 100.00 |
| wastar-w2 | 50 | 24.34 | 49.25 | 103.18 |
| llmastar_standard | 50 | 35.92 | 61.07 | 102.89 |
| quorumastar-vtext+corners+image+relations | 50 | 23.98 | 49.09 | 102.80 |

LLM: 0 new calls, 3811373 tokens (76227 per query).
