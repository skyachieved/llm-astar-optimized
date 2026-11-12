# 95% confidence intervals and standard deviations (from the committed CSVs)

Each cell: geometric mean of the per-query ratio x 100 [95% CI] (SD of the per-query ratio x 100).
A* = 100; queries where both the run and A* found a valid path.

## Llama-3-8B (Table 1)  (`outputs/llama-3-8b-instruct`)

| method | n | operation | storage | length |
|---|---|---|---|---|
| Dynamic WA* | 1000 | 59.49 [56.47, 62.68] (SD 40.5) | 78.65 [76.90, 80.45] (SD 24.1) | 100.25 [100.18, 100.31] (SD 1.1) |
| LLM-A* few-shot | 1000 | 42.99 [40.91, 45.19] (SD 55.1) | 62.83 [61.32, 64.37] (SD 30.7) | 102.27 [102.03, 102.50] (SD 4.0) |
| LLM-A* CoT | 1000 | 49.63 [47.04, 52.35] (SD 87.2) | 68.06 [66.16, 70.02] (SD 45.2) | 102.45 [102.20, 102.69] (SD 4.1) |
| LLM-A* RePE | 1000 | 69.70 [65.42, 74.27] (SD 155.6) | 84.31 [81.26, 87.47] (SD 78.4) | 102.42 [102.14, 102.70] (SD 5.0) |
| No waypoints (wA*, w=2) | 1000 | 34.32 [32.74, 35.97] (SD 32.9) | 56.23 [55.08, 57.41] (SD 19.6) | 102.02 [101.77, 102.26] (SD 4.2) |

## GPT-4o mini  (`outputs/gpt/gpt-4o-mini`)

| method | n | operation | storage | length |
|---|---|---|---|---|
| LLM-A* few-shot | 1000 | 50.52 [47.84, 53.35] (SD 86.1) | 68.38 [66.48, 70.34] (SD 44.2) | 102.95 [102.66, 103.23] (SD 4.9) |
| LLM-A* CoT | 1000 | 48.53 [46.06, 51.14] (SD 76.2) | 67.07 [65.30, 68.90] (SD 39.3) | 102.73 [102.48, 102.99] (SD 4.3) |
| LLM-A* RePE | 1000 | 50.84 [48.16, 53.68] (SD 75.8) | 68.97 [67.06, 70.93] (SD 42.1) | 102.51 [102.27, 102.75] (SD 4.0) |
| wA* w=1.5 | 1000 | 40.06 [38.25, 41.96] (SD 32.8) | 60.26 [59.09, 61.46] (SD 18.7) | 100.74 [100.61, 100.87] (SD 2.1) |
| No waypoints (wA*, w=2) | 1000 | 34.32 [32.74, 35.97] (SD 32.9) | 56.23 [55.08, 57.41] (SD 19.6) | 102.02 [101.77, 102.26] (SD 4.2) |
| wA* w=3 | 1000 | 29.92 [28.52, 31.38] (SD 34.6) | 53.26 [52.09, 54.45] (SD 21.2) | 103.68 [103.29, 104.07] (SD 7.1) |
| Quorum-A* | 1000 | 33.95 [32.36, 35.61] (SD 35.3) | 56.08 [54.90, 57.28] (SD 20.5) | 102.00 [101.75, 102.26] (SD 4.4) |

Paired operation ratio (A / B x 100) [95% CI] (SD):

- Quorum-A* vs LLM-A* few-shot: n = 1000, 67.19 [64.27, 70.24] (SD 45.0)
- Quorum-A* vs No waypoints (wA*, w=2): n = 1000, 98.92 [97.28, 100.59] (SD 30.9)
- LLM-A* few-shot vs No waypoints (wA*, w=2): n = 1000, 147.22 [140.89, 153.84] (SD 303.5)

## GPT-4.1 mini  (`outputs/other/gpt-4.1-mini`)

| method | n | operation | storage | length |
|---|---|---|---|---|
| LLM-A* few-shot | 1000 | 42.21 [40.05, 44.47] (SD 67.1) | 63.09 [61.47, 64.74] (SD 35.4) | 102.26 [102.02, 102.50] (SD 4.2) |
| No waypoints (wA*, w=2) | 1000 | 34.32 [32.74, 35.97] (SD 32.9) | 56.23 [55.08, 57.41] (SD 19.6) | 102.02 [101.77, 102.26] (SD 4.2) |
| Quorum-A* | 1000 | 33.39 [31.85, 35.00] (SD 33.6) | 55.79 [54.64, 56.96] (SD 19.6) | 101.95 [101.72, 102.18] (SD 4.0) |

Paired operation ratio (A / B x 100) [95% CI] (SD):

- Quorum-A* vs LLM-A* few-shot: n = 1000, 79.11 [76.03, 82.31] (SD 44.3)
- Quorum-A* vs No waypoints (wA*, w=2): n = 1000, 97.30 [95.65, 98.97] (SD 27.1)
- LLM-A* few-shot vs No waypoints (wA*, w=2): n = 1000, 122.99 [118.15, 128.03] (SD 251.6)

## GPT-4.1  (`outputs/other/gpt-4.1`)

| method | n | operation | storage | length |
|---|---|---|---|---|
| LLM-A* few-shot | 1000 | 39.90 [37.92, 41.97] (SD 57.3) | 61.19 [59.72, 62.70] (SD 30.4) | 102.51 [102.24, 102.78] (SD 4.6) |
| No waypoints (wA*, w=2) | 1000 | 34.32 [32.74, 35.97] (SD 32.9) | 56.23 [55.08, 57.41] (SD 19.6) | 102.02 [101.77, 102.26] (SD 4.2) |
| Quorum-A* | 1000 | 33.53 [31.97, 35.16] (SD 33.3) | 55.67 [54.51, 56.85] (SD 20.0) | 101.84 [101.61, 102.07] (SD 4.0) |

Paired operation ratio (A / B x 100) [95% CI] (SD):

- Quorum-A* vs LLM-A* few-shot: n = 1000, 84.04 [81.22, 86.95] (SD 55.0)
- Quorum-A* vs No waypoints (wA*, w=2): n = 1000, 97.70 [96.11, 99.32] (SD 30.6)
- LLM-A* few-shot vs No waypoints (wA*, w=2): n = 1000, 116.26 [112.26, 120.40] (SD 183.5)

## Qwen2.5-VL-7B  (`outputs/qwen/qwen2.5-vl-7b-instruct`)

| method | n | operation | storage | length |
|---|---|---|---|---|
| LLM-A* few-shot | 1000 | 38.03 [36.17, 39.99] (SD 58.4) | 59.29 [57.90, 60.72] (SD 30.2) | 102.27 [102.01, 102.53] (SD 4.5) |
| No waypoints (wA*, w=2) | 1000 | 34.32 [32.74, 35.97] (SD 32.9) | 56.23 [55.08, 57.41] (SD 19.6) | 102.02 [101.77, 102.26] (SD 4.2) |
| Quorum-A* | 1000 | 35.52 [33.88, 37.24] (SD 34.5) | 57.31 [56.09, 58.55] (SD 21.0) | 102.19 [101.94, 102.45] (SD 4.4) |

Paired operation ratio (A / B x 100) [95% CI] (SD):

- Quorum-A* vs LLM-A* few-shot: n = 1000, 93.39 [90.65, 96.20] (SD 44.4)
- Quorum-A* vs No waypoints (wA*, w=2): n = 1000, 103.51 [101.85, 105.19] (SD 42.3)
- LLM-A* few-shot vs No waypoints (wA*, w=2): n = 1000, 110.83 [107.87, 113.88] (SD 199.6)

## Claude Opus 5.5  (`outputs/claude/claude-opus-5-5`)

| method | n | operation | storage | length |
|---|---|---|---|---|
| LLM-A* few-shot | 1000 | 30.75 [29.26, 32.31] (SD 36.7) | 54.05 [52.87, 55.26] (SD 21.6) | 101.02 [100.83, 101.20] (SD 3.3) |
| No waypoints (wA*, w=2) | 1000 | 34.32 [32.74, 35.97] (SD 32.9) | 56.23 [55.08, 57.41] (SD 19.6) | 102.02 [101.77, 102.26] (SD 4.2) |
| Quorum-A* | 1000 | 30.04 [28.62, 31.52] (SD 32.2) | 53.55 [52.41, 54.72] (SD 19.6) | 101.23 [101.03, 101.44] (SD 3.6) |

Paired operation ratio (A / B x 100) [95% CI] (SD):

- Quorum-A* vs LLM-A* few-shot: n = 1000, 97.69 [96.07, 99.34] (SD 34.1)
- Quorum-A* vs No waypoints (wA*, w=2): n = 1000, 87.53 [85.84, 89.25] (SD 24.2)
- LLM-A* few-shot vs No waypoints (wA*, w=2): n = 1000, 89.60 [87.75, 91.48] (SD 91.3)

## Ablations (GPT-4o mini): operation ratio, variant / default x 100 [95% CI] (SD)

`outputs/gpt/gpt-4o-mini` (default vs A*: 33.95 [32.36, 35.61] (SD 35.3))

- no stall fallback: vs default n = 1000, 104.05 [102.80, 105.31] (SD 42.5); vs A* 35.32 [33.59, 37.14] (SD 51.6)
- no removal checks: vs default n = 1000, 100.32 [100.03, 100.61] (SD 6.2); vs A* 34.05 [32.47, 35.72] (SD 35.2)
- + vision judge: vs default n = 1000, 100.47 [98.90, 102.06] (SD 40.1); vs A* 34.10 [32.53, 35.76] (SD 32.9)

`outputs/gpt_ablation300/gpt-4o-mini` (default vs A*: 33.18 [30.27, 36.36] (SD 39.4))

- no vote (union): vs default n = 300, 125.43 [119.51, 131.64] (SD 78.4); vs A* 41.61 [38.31, 45.19] (SD 40.1)
- unanimity: vs default n = 300, 98.54 [95.64, 101.53] (SD 26.3); vs A* 32.69 [29.79, 35.88] (SD 36.3)
- text view only: vs default n = 300, 109.53 [105.82, 113.36] (SD 49.2); vs A* 36.34 [33.24, 39.72] (SD 43.0)
- corners view only: vs default n = 300, 112.75 [106.79, 119.04] (SD 79.1); vs A* 37.41 [34.07, 41.07] (SD 42.7)
- relations view only: vs default n = 300, 110.13 [106.03, 114.39] (SD 64.6); vs A* 36.54 [33.47, 39.89] (SD 39.5)
- image instead of relations: vs default n = 300, 101.19 [98.58, 103.86] (SD 28.5); vs A* 33.57 [30.58, 36.85] (SD 39.2)
- four views: vs default n = 300, 101.37 [99.69, 103.08] (SD 21.2); vs A* 33.63 [30.69, 36.85] (SD 39.4)
- no snap: vs default n = 300, 101.11 [98.83, 103.45] (SD 22.9); vs A* 33.54 [30.62, 36.75] (SD 36.1)
- few-shot shared: vs default n = 300, 98.34 [95.74, 101.01] (SD 23.8); vs A* 32.62 [29.75, 35.78] (SD 39.1)
- few-shot none: vs default n = 300, 108.39 [104.38, 112.55] (SD 51.9); vs A* 35.96 [32.82, 39.40] (SD 42.0)
- CoT: vs default n = 300, 99.74 [97.38, 102.14] (SD 23.7); vs A* 33.09 [30.14, 36.33] (SD 37.5)
- roles: vs default n = 300, 101.12 [98.74, 103.57] (SD 30.8); vs A* 33.55 [30.51, 36.89] (SD 42.0)
- + vision judge: vs default n = 300, 99.38 [96.84, 101.98] (SD 23.4); vs A* 32.97 [30.07, 36.14] (SD 36.2)

## Queries where the vote passed waypoints on: Quorum-A* / no-waypoint search x 100 [95% CI] (SD)

- GPT-4o mini: n = 674, 98.40 [95.99, 100.88] (SD 37.6)
- GPT-4.1 mini: n = 686, 96.08 [93.73, 98.50] (SD 32.7)
- GPT-4.1: n = 756, 96.97 [94.89, 99.10] (SD 35.2)
- Qwen2.5-VL-7B: n = 412, 108.72 [104.60, 113.01] (SD 64.3)
- Claude Opus 5.5: n = 950, 86.92 [85.16, 88.71] (SD 24.8)

## Harder maps: operations vs A* [95% CI] (SD), and Quorum-A* / no-waypoint search

- dense, GPT-4o mini: no waypoints 26.90 [23.13, 31.28] (SD 30.6); LLM-A* 53.84 [43.74, 66.26] (SD 143.7); Quorum-A* 27.01 [23.27, 31.34] (SD 30.3); Quorum-A* / no waypoints 100.40 [96.52, 104.43] (SD 20.3)
- dense, GPT-4.1 mini: no waypoints 26.90 [23.13, 31.28] (SD 30.6); LLM-A* 41.36 [34.74, 49.23] (SD 64.1); Quorum-A* 27.48 [23.78, 31.75] (SD 29.9); Quorum-A* / no waypoints 102.15 [96.53, 108.11] (SD 52.9)
- dense, GPT-4.1: no waypoints 26.90 [23.13, 31.28] (SD 30.6); LLM-A* 40.80 [33.79, 49.25] (SD 123.0); Quorum-A* 27.61 [23.81, 32.01] (SD 29.9); Quorum-A* / no waypoints 102.62 [96.65, 108.95] (SD 40.7)
- dense, Qwen2.5-VL-7B: no waypoints 26.90 [23.13, 31.28] (SD 30.6); LLM-A* 38.79 [31.75, 47.38] (SD 74.0); Quorum-A* 27.72 [23.84, 32.23] (SD 30.9); Quorum-A* / no waypoints 103.04 [97.63, 108.75] (SD 32.2)

- large, GPT-4o mini: no waypoints 20.10 [16.66, 24.25] (SD 29.4); LLM-A* 48.17 [38.49, 60.28] (SD 85.8); Quorum-A* 20.16 [16.68, 24.36] (SD 29.4); Quorum-A* / no waypoints 100.28 [95.48, 105.33] (SD 42.7)
- large, GPT-4.1 mini: no waypoints 20.10 [16.66, 24.25] (SD 29.4); LLM-A* 49.66 [40.83, 60.40] (SD 79.2); Quorum-A* 20.50 [16.98, 24.76] (SD 29.1); Quorum-A* / no waypoints 102.01 [98.56, 105.57] (SD 18.1)
- large, GPT-4.1: no waypoints 20.10 [16.66, 24.25] (SD 29.4); LLM-A* 40.38 [33.11, 49.25] (SD 60.2); Quorum-A* 20.43 [16.90, 24.71] (SD 29.8); Quorum-A* / no waypoints 101.66 [95.15, 108.61] (SD 53.2)
- large, Qwen2.5-VL-7B: no waypoints 20.10 [16.66, 24.25] (SD 29.4); LLM-A* 31.03 [24.50, 39.30] (SD 90.6); Quorum-A* 21.14 [17.49, 25.57] (SD 32.5); Quorum-A* / no waypoints 105.20 [100.15, 110.50] (SD 54.8)

- zigzag, GPT-4o mini: no waypoints 95.42 [91.89, 99.08] (SD 16.9); LLM-A* 94.94 [91.48, 98.53] (SD 17.0); Quorum-A* 95.35 [91.83, 99.01] (SD 16.9); Quorum-A* / no waypoints 99.93 [99.83, 100.02] (SD 0.5)
- zigzag, GPT-4.1 mini: no waypoints 95.42 [91.89, 99.08] (SD 16.9); LLM-A* 96.01 [92.68, 99.46] (SD 16.0); Quorum-A* 95.41 [91.86, 99.10] (SD 17.0); Quorum-A* / no waypoints 99.99 [99.85, 100.14] (SD 0.7)
- zigzag, GPT-4.1: no waypoints 95.42 [91.89, 99.08] (SD 16.9); LLM-A* 96.14 [92.84, 99.55] (SD 15.9); Quorum-A* 95.44 [91.88, 99.14] (SD 17.0); Quorum-A* / no waypoints 100.03 [99.88, 100.17] (SD 0.7)
- zigzag, Qwen2.5-VL-7B: no waypoints 95.42 [91.89, 99.08] (SD 16.9); LLM-A* 95.42 [91.89, 99.08] (SD 16.9); Quorum-A* 95.42 [91.83, 99.14] (SD 17.1); Quorum-A* / no waypoints 100.00 [99.75, 100.25] (SD 1.2)

