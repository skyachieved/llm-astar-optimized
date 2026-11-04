"""Paired tests on per-query operations (agent.md step 7): is a run's difference from another run more than noise?

Both runs answer the same queries, so each query gives one pair (run A, run B). Two tests, both two-sided:
  - Wilcoxon signed-rank on the differences A - B (zero differences dropped, tied ranks averaged; normal approximation
    with the tie correction, as scipy.stats.wilcoxon(method="approx")): uses how big each difference is.
  - Sign test on wins vs. losses (exact binomial, ties dropped): uses only which run was better on each query.
Standard library only, so the submission needs no extra package.
"""
import math


def _ranks(values):
    """Average ranks (1-based) of values, ties sharing the mean of their positions."""
    order = sorted(range(len(values)), key=lambda i: values[i])
    ranks = [0.0] * len(values)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and values[order[j + 1]] == values[order[i]]:
            j += 1
        for k in range(i, j + 1):
            ranks[order[k]] = (i + j) / 2 + 1
        i = j + 1
    return ranks


def wilcoxon(a, b):
    """Two-sided p-value of the Wilcoxon signed-rank test on paired samples a, b (nan if every pair is equal)."""
    d = [x - y for x, y in zip(a, b) if x != y]
    n = len(d)
    if n == 0:
        return math.nan
    abs_d = [abs(x) for x in d]
    ranks = _ranks(abs_d)
    w_plus = sum(r for r, x in zip(ranks, d) if x > 0)
    mean = n * (n + 1) / 4
    ties = {}
    for x in abs_d:
        ties[x] = ties.get(x, 0) + 1
    var = n * (n + 1) * (2 * n + 1) / 24 - sum(t ** 3 - t for t in ties.values()) / 48
    if var <= 0:
        return math.nan
    z = (w_plus - mean) / math.sqrt(var)
    return math.erfc(abs(z) / math.sqrt(2))


def sign_test(wins, losses):
    """Two-sided exact binomial p-value of wins vs. losses at 1/2 (nan without any non-tie)."""
    n = wins + losses
    if n == 0:
        return math.nan
    k = min(wins, losses)
    tail = sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n
    return min(1.0, 2 * tail)


def compare(a_rows, b_rows, metric="operation"):
    """Pair two runs' rows (dicts with map_id, sg_idx, valid, metric) on queries both solved.

    Returns n, wins / ties / losses of a (fewer is a win), the geometric mean of a / b x 100, and both p-values.
    """
    b = {(r["map_id"], r["sg_idx"]): r for r in b_rows if r["valid"] == "1"}
    pairs = [(float(r[metric]), float(b[(r["map_id"], r["sg_idx"])][metric])) for r in a_rows
             if r["valid"] == "1" and (r["map_id"], r["sg_idx"]) in b]
    x = [p for p, _ in pairs]
    y = [q for _, q in pairs]
    wins = sum(p < q for p, q in pairs)
    losses = sum(p > q for p, q in pairs)
    ratio = 100 * math.exp(sum(math.log(p / q) for p, q in pairs) / len(pairs)) if pairs else math.nan
    return {"n": len(pairs), "wins": wins, "ties": len(pairs) - wins - losses, "losses": losses, "ratio": ratio,
            "p_wilcoxon": wilcoxon(x, y), "p_sign": sign_test(wins, losses)}


def fmt_p(p):
    """p-value for a table: '-' when undefined, '< 0.001' below 0.001, otherwise two significant digits."""
    if p is None or (isinstance(p, float) and math.isnan(p)):
        return "-"
    return "< 0.001" if p < 0.001 else f"{p:.2g}"
