"""Quorum-A*: multi-view LLM consensus for LLM-A*'s waypoint step (METHOD.md). The search itself is
llmastar.pather.QuorumAStar; this package turns a query into a waypoint list.

The deterministic core, which needs no LLM:
  geometry   waypoint filter, corner nodes, visibility
  canonical  snap a proposed point to a cell, then to a nearby corner node (METHOD.md 4.3)
  voting     majority add (4.4)
  pruning    majority remove with the code / vision / support checks (4.5)
Part 2: config, render, parsing, views, fewshot and QuorumAStarGenerator (below).
"""

import hashlib
import json
import time
from concurrent.futures import ThreadPoolExecutor

from llmastar.waypoints import WaypointResult

from .canonical import canonicalize
from .config import QuorumConfig
from .fewshot import examples_for
from .geometry import corner_nodes
from .pruning import majority_remove
from .views import VIEWS, PaperView, judge_messages, parse_judge
from .voting import majority_add

__all__ = ["QuorumAStarGenerator", "QuorumConfig"]


def _sha(messages):
    return hashlib.sha256(json.dumps(messages, sort_keys=True, default=str).encode()).hexdigest()


def _call(client, messages, json_mode):
    """One chat call -> (text, record). Never raises."""
    start = time.time()
    try:
        if json_mode:
            text, info = client.chat_with_info(messages, json_mode=True)
        else:
            text, info = client.chat_with_info(messages)
    except Exception as error:  # noqa: BLE001 - a client without the error contract
        text, info = "", {"error": f"{type(error).__name__}: {error}"[:500]}
    usage = info.get("usage") or {}
    return text or "", {"cached": bool(info.get("cached")), "error": info.get("error", ""),
                        "prompt_tokens": usage.get("prompt_tokens") or 0,
                        "completion_tokens": usage.get("completion_tokens") or 0,
                        "seconds": round(time.time() - start, 3), "cache_key": info.get("cache_key"),
                        "dropped_params": info.get("dropped_params", [])}


class QuorumAStarGenerator:
    """Quorum-A*'s waypoint step (METHOD.md 3): views -> canonicalize -> majority add -> majority remove.

    `generate(query) -> WaypointResult` is thread-safe and never raises. raw holds the per-query log of METHOD.md 8.
    """
    name = "quorumastar"

    def __init__(self, client, config=None):
        self.client = client
        self.config = config or QuorumConfig()
        c = self.config
        self.views = []
        for i, name in enumerate(c.views):
            if name == "text" and c.fewshot == "paper":
                view, examples = PaperView(c.prompt, c.prompt_set), []
            else:
                view = VIEWS[name](cot=c.cot, roles=c.roles)
                mode = "per-view" if c.fewshot == "paper" else c.fewshot
                examples = [] if view.zero_shot else examples_for(i, mode, c.n_shots, c.fewshot_seed, len(c.views))
            self.views.append((view, examples))

    def _ask_view(self, view, examples, query):
        messages = view.messages(query, examples)
        text, record = _call(self.client, messages, view.json_mode and self.config.json_mode)
        points, ok = view.parse(text, query) if not record["error"] else ([], False)
        record.update(view=view.name, messages_sha256=_sha(messages), response=text,
                      points=[list(p) for p in points], parse_ok=ok, abstained=bool(record["error"]) or not ok)
        return points, record

    def generate(self, query):
        try:
            return self._generate(query)
        except Exception as error:  # noqa: BLE001 - never stop a run (agent.md hard rule 4)
            return WaypointResult([], False, {"generator": self.name, "llm_error": f"{type(error).__name__}: "
                                                                                    f"{error}"[:500]})

    def _generate(self, query):
        c = self.config
        started = time.time()
        if len(self.views) == 1:
            answers = [self._ask_view(*self.views[0], query)]
        else:
            with ThreadPoolExecutor(len(self.views)) as pool:
                answers = list(pool.map(lambda ve: self._ask_view(*ve, query), self.views))

        corners = corner_nodes(query) if c.snap else None
        lists, records = [], []
        for points, record in answers:
            if not record["abstained"]:
                if c.snap:
                    cells, dropped = canonicalize(points, query, c.snap_cell_radius, c.snap_corner_radius, corners)
                    record.update(cells=[list(p) for p in cells], dropped=[list(p) for p in dropped])
                else:
                    cells = [tuple(p) for p in points]
                lists.append(cells)
            records.append(record)

        vote = majority_add(lists, c.add_quorum) if lists else majority_add([[]], 1)
        waypoints = vote.waypoints

        judge = None
        vision_remove = None
        if c.remove_quorum > 0 and c.vision and waypoints:
            text, judge = _call(self.client, judge_messages(query, waypoints), c.json_mode)
            ids, ok = parse_judge(text, len(waypoints)) if not judge["error"] else ([], False)
            judge.update(view="judge", response=text, remove=ids, parse_ok=ok, abstained=bool(judge["error"]) or not ok)
            vision_remove = None if judge["abstained"] else ids

        pruning = majority_remove(waypoints, query, c.remove_quorum, vote.support, len(lists), vision_remove)
        calls = records + ([judge] if judge else [])
        errors = [f"{r['view']}: {r['error']}" for r in calls if r["error"]]
        raw = {
            "generator": self.name,
            "views": records,
            "votes": [{"cell": list(w), "support": vote.support.get(w), "position": vote.position.get(w)}
                      for w in vote.waypoints],
            "judge": judge,
            "pruning": [{**chk, "waypoint": list(chk["waypoint"])} for chk in pruning.checks],
            "waypoints": [list(w) for w in pruning.waypoints],
            "parse_ok": bool(lists),
            "cached": all(r["cached"] for r in calls) if calls else False,
            "calls": sum(1 for r in calls if not r["cached"]),
            "prompt_tokens": sum(r["prompt_tokens"] for r in calls),
            "completion_tokens": sum(r["completion_tokens"] for r in calls),
            "llm_seconds": round(time.time() - started, 3),
            # every view failing is an LLM failure; a single abstaining view is normal operation
            "llm_error": "; ".join(errors) if errors and not lists else "",
        }
        return WaypointResult(list(pruning.waypoints), bool(lists), raw)
