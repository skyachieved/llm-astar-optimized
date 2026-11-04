"""llmastar.stats: paired tests on per-query metrics (reference values from scipy.stats 1.x)."""
import math

from llmastar import stats

A = [10, 12, 15, 9, 30, 22, 18, 7, 11, 40, 25, 13]
B = [11, 12, 13, 9, 35, 20, 18, 9, 10, 45, 25, 16]


def test_wilcoxon_matches_scipy_approx():
    # scipy.stats.wilcoxon(A, B, method="approx").pvalue: zeros dropped, tied ranks averaged, tie-corrected variance
    assert math.isclose(stats.wilcoxon(A, B), 0.23049390578587947, rel_tol=1e-9)


def test_wilcoxon_is_symmetric_and_nan_without_differences():
    assert math.isclose(stats.wilcoxon(A, B), stats.wilcoxon(B, A))
    assert math.isnan(stats.wilcoxon([1, 2, 3], [1, 2, 3]))


def test_sign_test_matches_binomial():
    assert math.isclose(stats.sign_test(4, 2), 0.6875)  # scipy.stats.binomtest(4, 6).pvalue
    assert math.isclose(stats.sign_test(0, 10), 0.001953125)
    assert stats.sign_test(5, 5) == 1.0
    assert math.isnan(stats.sign_test(0, 0))


def _rows(values, valid=None):
    return [{"map_id": str(i), "sg_idx": "0", "valid": "1" if valid is None or valid[i] else "0", "operation": str(v)}
            for i, v in enumerate(values)]


def test_compare_pairs_valid_queries_only():
    a = _rows([10, 20, 30, 40], valid=[1, 1, 1, 0])
    b = _rows([20, 20, 15, 1])
    c = stats.compare(a, b)
    assert (c["n"], c["wins"], c["ties"], c["losses"]) == (3, 1, 1, 1)
    assert math.isclose(c["ratio"], 100.0)  # (0.5 x 1 x 2) ** (1/3) = 1
    assert c["p_sign"] == 1.0


def test_fmt_p():
    assert stats.fmt_p(math.nan) == "-"
    assert stats.fmt_p(0.0002) == "< 0.001"
    assert stats.fmt_p(0.0123) == "0.012"
