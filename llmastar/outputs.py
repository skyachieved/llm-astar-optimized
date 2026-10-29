"""Output layout: everything one model's runs produce lives in outputs/<model>/.

  <run>.csv            per-query metrics, <run> = <method>[_<tag>][-<variant>], e.g. astar, llmastar_cot
  raw/<run>.jsonl      raw LLM responses (git-ignored)
  traces/<run>/<map>_<sg>.json   path + visited states for selected queries (used by the figures)
  plots/<run>/<map>_<sg>.png     optional per-query plots (git-ignored)
  summary.md, summary.csv        aggregated table (python -m llmastar.summary)
"""
import re
from pathlib import Path

OUTPUTS_ROOT = Path("outputs")


def model_slug(model):
    """'meta-llama/Meta-Llama-3-8B-Instruct' -> 'meta-llama-3-8b-instruct'; 'llama-3-8b-instruct' is unchanged."""
    return re.sub(r"[^a-z0-9._-]+", "-", model.rstrip("/").split("/")[-1].lower())


def run_name(method, tag=None, variant=None):
    name = f"{method}_{tag}" if tag else method
    return f"{name}-{variant}" if variant else name


class RunPaths:
    def __init__(self, model, run, root=OUTPUTS_ROOT):
        self.dir = Path(root) / model_slug(model)
        self.csv = self.dir / f"{run}.csv"
        self.raw = self.dir / "raw" / f"{run}.jsonl"
        self.traces = self.dir / "traces" / run
        self.plots = self.dir / "plots" / run

    def trace(self, map_id, sg_idx):
        return self.traces / f"{map_id}_{sg_idx}.json"

    def plot(self, map_id, sg_idx):
        return self.plots / f"{map_id}_{sg_idx}.png"
