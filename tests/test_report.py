"""llmastar.report and fig8_models read committed outputs only and mark what has not run instead of filling it in."""
import csv

from llmastar import report
from llmastar.figures import fig8_models

HEADER = ["map_id", "sg_idx", "valid", "operation", "storage", "length", "n_targets"]
OPS = {"astar": [100, 200, 300], "wastar-w2": [40, 60, 90], "llmastar_standard": [50, 90, 150],
       "quorumastar": [40, 50, 90]}
ANALYSIS = """# Failure cases and cost

## Cost per query ($0.15 / $0.6 per 1M input / output tokens)

| run | LLM requests | prompt tokens | completion tokens | $ per query | $ per 1,000 queries | source |
|---|---|---|---|---|---|---|
| llmastar_standard | 1.00 | 585 | 596 | 0.00045 | 0.45 | raw log |
| quorumastar | 3.00 | 5,895 | 46 | 0.00091 | 0.91 | raw log |
"""


def _write(folder, ops):
    folder.mkdir(parents=True, exist_ok=True)
    for run, values in ops.items():
        with open(folder / f"{run}.csv", "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(HEADER)
            w.writerows([i, 0, 1, v, v, 100, 3] for i, v in enumerate(values))


def test_tables_from_outputs(tmp_path):
    out = tmp_path / "outputs"
    _write(out / "gpt" / "gpt-4o-mini", OPS)
    (out / "gpt" / "gpt-4o-mini" / "analysis.md").write_text(ANALYSIS)
    text = report.build(out)
    assert "| GPT-4o mini | Quorum-A* | 31.07 |" in text  # (0.4 x 0.25 x 0.3) ** (1/3) x 100
    assert "| GPT-4o mini | 3 / 0 / 0 | 64.4 |" in text  # vs LLM-A*: fewer operations on all three
    assert "| 1 / 2 / 0 | 94.1 |" in text  # vs weighted A*: one win, two ties
    assert "| GPT-4o mini | quorumastar | 3.00 | 5,895 | 46 | 0.91 | $0.15 / $0.6 |" in text
    assert "| Qwen2.5-VL-7B | Quorum-A* | not run yet |" in text
    assert "| GPT-4.1 | dense | not run yet |" in text


def test_fig8_marks_models_not_run(tmp_path, monkeypatch):
    out = tmp_path / "outputs"
    _write(out / "gpt" / "gpt-4o-mini", OPS)
    monkeypatch.chdir(tmp_path)
    data = fig8_models.panels(out)
    bench = {label: ops for label, ops, _ in data[0][1]}
    assert bench["GPT-4o mini"]["quorumastar"] is not None
    assert bench["GPT-4.1"]["quorumastar"] is None
    assert data[1][1][-1][2] == "not run (API budget)"  # Claude's hard maps are left out on purpose
    fig8_models.main(["--outputs", str(out)])
    assert (tmp_path / "outputs" / "figures" / "fig8_models.png").exists()


def test_fig8_report_version_leaves_out_partial_models(tmp_path, monkeypatch):
    # The course-report version draws only models run on every map set, so no panel says "not run".
    out = tmp_path / "outputs"
    _write(out / "gpt" / "gpt-4o-mini", OPS)
    monkeypatch.chdir(tmp_path)
    drawn = []
    monkeypatch.setattr(fig8_models.plt.Axes, "set_yticklabels", lambda self, labels, **kw: drawn.append(labels))
    fig8_models.main(["--outputs", str(out), "--report"])
    assert (tmp_path / "outputs" / "figures" / "fig8_models_report.png").exists()
    assert not (tmp_path / "outputs" / "figures" / "fig8_models.png").exists()
    assert "Claude Opus 5.5*" not in drawn[0] and "GPT-4o mini" in drawn[0]


def test_suffixed_runs_are_found(tmp_path):
    # Qwen's LLM runs carry -max512 in their names; the tables look them up under the plain name.
    out = tmp_path / "outputs"
    ops = {"astar": OPS["astar"], "wastar-w2": OPS["wastar-w2"], "llmastar_standard-max512": OPS["llmastar_standard"],
           "quorumastar-max512": OPS["quorumastar"]}
    _write(out / "qwen" / "qwen2.5-vl-7b-instruct", ops)
    (out / "qwen" / "qwen2.5-vl-7b-instruct" / "analysis.md").write_text(
        ANALYSIS.replace("| quorumastar |", "| quorumastar-max512 |"))
    text = report.build(out)
    assert "| Qwen2.5-VL-7B | Quorum-A* | 31.07 |" in text
    assert "| Qwen2.5-VL-7B | 3 / 0 / 0 | 64.4 |" in text
    # Local model: tokens without a price (analysis.md applies its default price, which does not apply here).
    assert "| Qwen2.5-VL-7B | quorumastar-max512 | 3.00 | 5,895 | 46 | - | - |" in text
