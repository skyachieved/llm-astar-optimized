"""Failure-case and cost analysis (llmastar/analysis.py) on a tiny fake outputs directory."""
import json

from llmastar import analysis

HEAD = "map_id,sg_idx,operation,storage,length,valid,n_waypoints,n_targets,fallback,fallback_pop,prompt_tokens,completion_tokens\n"


def _write(path, rows):
    path.write_text(HEAD + "".join(",".join(map(str, r)) + "\n" for r in rows))


def test_report(tmp_path):
    _write(tmp_path / "wastar-w2.csv", [(0, i, 100, 100, 50, 1, "", "", "", "", "", "") for i in range(4)])
    _write(tmp_path / "llmastar_standard.csv", [(0, i, 150, 120, 50, 1, 3, 4, "", "", "", "") for i in range(4)])
    _write(tmp_path / "quorumastar.csv", [(0, 0, 100, 100, 50, 1, 0, 2, 0, "", 1000, 10),   # no waypoint
                                          (0, 1, 50, 80, 50, 1, 1, 3, 0, "", 1000, 10),     # kept, better
                                          (0, 2, 200, 150, 50, 1, 2, 2, 1, 40, 1000, 10),   # fallback, worse
                                          (0, 3, 100, 100, 50, 1, 0, 2, 0, "", 1000, 10)])
    _write(tmp_path / "quorumastar-tiny.csv", [(0, 0, 100, 100, 50, 1, 0, 2, 0, "", 1000, 10)])
    (tmp_path / "raw").mkdir()
    (tmp_path / "raw" / "llmastar_standard.jsonl").write_text(
        "".join(json.dumps({"usage": {"prompt_tokens": 2000, "completion_tokens": 400}}) + "\n" for _ in range(4)))
    text = analysis.report(tmp_path, worst=2)
    assert "| quorumastar | 1 / 2 / 1 | 100.0 | 3 / 0 / 1 |" in text
    assert "| no waypoint reached the search | 2 | 100.0 | 0 / 2 / 0 |" in text
    assert "| stall fallback fired | 1 | 200.0 | 0 / 0 / 1 |" in text
    assert "| 0:2 | 200 | 100 | 150 | 2 | 0 | yes (40) |" in text  # the worst query comes first
    assert "| llmastar_standard | 1.00 | 2,000 | 400 | 0.00054 | 0.54 | raw log |" in text
    assert "| quorumastar | - | 1,000 | 10 |" in text and "Left out" in text and "quorumastar-tiny" in text
    assert (tmp_path / "analysis.md").exists()
