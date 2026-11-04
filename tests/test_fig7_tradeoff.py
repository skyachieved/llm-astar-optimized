"""fig7_tradeoff reads only summary.csv and leaves out runs it does not find."""
import csv

from llmastar.figures import fig7_tradeoff


def test_tradeoff_figure(tmp_path, monkeypatch):
    model = tmp_path / "outputs" / "gpt" / "fake-model"
    model.mkdir(parents=True)
    rows = [("astar", 100, 100, 100), ("wastar-w1.5", 40, 60, 100.7), ("wastar-w2", 34.3, 56.2, 102.0),
            ("wastar-w3", 29.9, 53.3, 103.7), ("llmastar_standard", 50.5, 68.4, 103.0), ("quorumastar", 34.0, 56.1, 102.0)]
    with open(model / "summary.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["run", "n", "operation", "storage", "length"])
        w.writerows((r, 1000, o, s, l) for r, o, s, l in rows)
    monkeypatch.chdir(tmp_path)
    fig7_tradeoff.main(["--model", "fake-model", "--out", str(model.parent)])  # no dwastar, cot, repe, vision run
    assert (tmp_path / "outputs" / "figures" / "fig7_tradeoff_fake-model.png").exists()
