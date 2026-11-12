"""llmastar/ci_stats.py: the report's 95% CIs and SDs from the committed per-query CSVs."""
import math

from llmastar import ci_stats


def test_stats_on_known_ratios():
    s = ci_stats.stats([1.0, 1.0, 1.0])
    assert s["n"] == 3 and math.isclose(s["gm"], 100.0) and math.isclose(s["lo"], 100.0)
    assert math.isclose(s["sd"], 0.0, abs_tol=1e-12)
    s = ci_stats.stats([0.5, 2.0])
    assert math.isclose(s["gm"], 100.0) and s["lo"] < 100.0 < s["hi"]


def test_t_quantile_close_to_table():
    assert abs(ci_stats.t975(1000) - 1.9623) < 1e-3
    assert abs(ci_stats.t975(300) - 1.9680) < 1e-3


def test_report_numbers(tmp_path):
    out = tmp_path / "ci_tables.md"
    ci_stats.main(".", out)
    text = out.read_text(encoding="utf-8")
    # Table 2, GPT-4o mini Quorum-A*, and Table 1, Llama-3-8B LLM-A* few-shot
    assert "| Quorum-A* | 1000 | 33.95 [32.36, 35.61] (SD 35.3)" in text
    assert "| LLM-A* few-shot | 1000 | 42.99 [40.91, 45.19] (SD 55.1)" in text
    # Table 3, last column, GPT-4.1
    assert "- GPT-4.1: n = 756, 96.97 [94.89, 99.10]" in text
