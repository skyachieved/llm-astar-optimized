# Pilot report: quorumastar-vtext+corners+image+relations-vision-max512 (50 queries, outputs/qwen_pilot/qwen2.5-vl-7b-instruct)

## Solo quality per view

| view | abstained | waypoints | good | queries with a good waypoint |
|---|---|---|---|---|
| text | 0/50 | 124 | 38.7% | 58.0% |
| corners | 0/50 | 86 | 39.5% | 58.0% |
| image | 0/50 | 254 | 47.6% | 100.0% |
| relations | 0/50 | 52 | 42.3% | 42.0% |

## Shared bad waypoints (row view's bad waypoints also proposed by the column view; lower = more independent)

| bad of \ also in | text | corners | image | relations |
|---|---|---|---|---|
| text | - | 3.9% | 3.9% | 5.3% |
| corners | 5.8% | - | 7.7% | 3.8% |
| image | 2.3% | 3.0% | - | 0.8% |
| relations | 13.3% | 6.7% | 3.3% | - |

## Voting

As run: 27/50 queries kept at least one waypoint by vote; final waypoints 8, good 75.0%.

Simulated from the same answers (quorum 2): queries with a kept waypoint / kept waypoints / good share.

| views | r = 0 | r = 1 | r = 2 | r = 3 |
|---|---|---|---|---|
| text,corners,image,relations | 27 / 37 / 59.5% | 29 / 41 / 56.1% | 45 / 65 / 47.7% | 46 / 68 / 52.9% |
| text,corners,image | 18 / 22 / 54.5% | 19 / 23 / 52.2% | 33 / 43 / 46.5% | 35 / 47 / 53.2% |
| text,corners,relations | 19 / 20 / 65.0% | 21 / 23 / 60.9% | 32 / 38 / 52.6% | 33 / 38 / 55.3% |
| text,image,relations | 18 / 19 / 57.9% | 21 / 23 / 52.2% | 33 / 41 / 51.2% | 34 / 43 / 55.8% |
| corners,image,relations | 15 / 17 / 58.8% | 15 / 17 / 58.8% | 25 / 28 / 57.1% | 27 / 32 / 56.2% |

## Vision judge

catch rate 73.3% (11/15 bad waypoints removed), false-alarm rate 72.7% (16/22 good removed), abstained 0.

## Search (geometric mean vs A* = 100, lower is better)

| run | n | operation | storage | length |
|---|---|---|---|---|
| astar | 50 | 100.00 | 100.00 | 100.00 |
| wastar-w2 | 50 | 24.34 | 49.25 | 103.18 |
| quorumastar-vtext+corners+image+relations-vision-max512 | 50 | 24.61 | 49.63 | 103.16 |

not run yet: llmastar_standard

## Every LLM run vs weighted A* (w = 2, = 100), by whether the search kept waypoints

| run | waypoints | n | operation | storage | stall fallback |
|---|---|---|---|---|---|
| llmastar_standard-max512 | used | 21 | 99.0 | 100.6 | 0 |
| llmastar_standard-max512 | none | 29 | 100.0 | 100.0 | 0 |
| quorumastar-max512 | used | 13 | 86.5 | 93.9 | 0 |
| quorumastar-max512 | none | 37 | 102.1 | 101.2 | 3 |
| quorumastar-vision-max512 | used | 2 | 89.1 | 94.2 | 0 |
| quorumastar-vision-max512 | none | 48 | 101.6 | 100.9 | 2 |
| quorumastar-vtext+corners+image+relations-vision-max512 | used | 6 | 96.8 | 99.1 | 0 |
| quorumastar-vtext+corners+image+relations-vision-max512 | none | 44 | 101.7 | 101.0 | 1 |
| quorumastar-vtext+corners+image-max512 | used | 12 | 103.6 | 103.4 | 1 |
| quorumastar-vtext+corners+image-max512 | none | 38 | 102.8 | 101.4 | 2 |

LLM: 70 new calls, 416292 tokens (8326 per query).
