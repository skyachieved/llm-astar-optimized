"""fig6_methods reads outputs/ only, compares methods on the same queries, and never invents a missing run."""
import csv
import shutil
from pathlib import Path

import pytest

from llmastar.figures import fig6_methods

REPO = Path(__file__).resolve().parent.parent
SOURCE = REPO / "outputs" / "llama-3-8b-instruct"


def _copy_rows(src, dst, limit):
    with open(src, newline="") as f:
        reader = csv.DictReader(f)
        rows = [r for _, r in zip(range(limit), reader)]
    with open(dst, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=reader.fieldnames)
        writer.writeheader()
        writer.writerows(rows)


@pytest.fixture
def outputs(tmp_path, monkeypatch):
    model = tmp_path / "outputs" / "fake-model"
    (model / "traces").mkdir(parents=True)
    _copy_rows(SOURCE / "astar.csv", model / "astar.csv", 40)
    _copy_rows(SOURCE / "llmastar_standard.csv", model / "llmastar_standard.csv", 40)
    _copy_rows(SOURCE / "llmastar_cot.csv", model / "quorumastar.csv", 20)  # stands in for a 20-query pilot
    for run in ("astar", "llmastar_standard"):
        shutil.copytree(SOURCE / "traces" / run, model / "traces" / run)
    monkeypatch.chdir(tmp_path)
    return model


def test_figure_with_a_missing_run(outputs):
    fig6_methods.main(["--model", "fake-model"])  # no wastar run, no quorumastar trace
    assert (outputs.parent / "figures" / "fig6_methods_fake-model.png").exists()


def test_averages_use_the_same_queries(outputs):
    runs = {m: fig6_methods._rows(outputs / f"{name}.csv") for m, name in
            {"astar": "astar", "wastar": "wastar-w2", "llmastar": "llmastar_standard",
             "quorumastar": "quorumastar"}.items()}
    means, n = fig6_methods.averages(runs)
    assert n == 20  # the 20 queries the shortest run has, not 40
    assert means["astar"] == {"operation": 100, "storage": 100, "length": 100}
    assert "wastar" not in means  # missing, so not drawn and not estimated
