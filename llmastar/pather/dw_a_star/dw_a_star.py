import heapq

from llmastar.pather.a_star.a_star import AStar


class DWAStar(AStar):
    """Dynamic Weighted A*: f = g + w * h, with a weight that decays on a fixed schedule.

    The paper only gives "initial weight 2, 0.99 decay". The readings we run (documented in REPRODUCTION.md):
      schedule="pop":   w = max(min_weight, w0 * decay**k), k = heap pops so far, so the search starts greedy and
                        relaxes towards plain A* as it proceeds;
      schedule="depth": w = max(min_weight, w0 * decay**d), d = steps from the start along the state's parent chain
                        (Pohl-style dynamic weighting: greedy near the start, closer to admissible deep in the tree).
    rekey=True (the default, pop schedule only) recomputes every OPEN priority with the current weight whenever it
    changes; rekey=False fixes a state's priority when it is pushed. A depth weight never changes, so rekey does not
    apply to it. min_weight=1 keeps w >= 1; min_weight=0 lets the weight keep decaying below 1, as a bare
    `w *= decay` would. Defaults (pop, re-keyed, w >= 1) match the paper's Table 1 row. Metrics are the same as A*.
    """
    name = "Dynamic WA*"

    def __init__(self, w0=2.0, decay=0.99, schedule="pop", rekey=True, min_weight=1.0):
        super().__init__()
        assert schedule in ("pop", "depth"), "schedule must be 'pop' or 'depth'"
        self.w0, self.decay, self.schedule = w0, decay, schedule
        self.rekey, self.min_weight = rekey, min_weight

    def searching(self, query, filepath=None):
        self.depth = {}
        self.keyed_weight = self.scheduled_weight(0)  # the weight OPEN's priorities were computed with
        return super().searching(query, filepath)

    def scheduled_weight(self, k):
        return max(self.min_weight, self.w0 * self.decay ** k)

    def weight(self, s):
        if self.schedule == "pop":
            return self.scheduled_weight(self.count)
        # f_value(s) is called right after PARENT[s] is (re)assigned, so the parent's depth is known.
        parent = self.PARENT[s]
        self.depth[s] = 0 if parent == s else self.depth[parent] + 1
        return self.scheduled_weight(self.depth[s])

    def before_pop(self):
        if not self.rekey or self.schedule != "pop":
            return
        w = self.scheduled_weight(self.count)
        if w != self.keyed_weight:
            # Same entries (stale duplicates included, as in LLM-A*'s re-keying), new priorities.
            self.OPEN = [(self.f_value(s), s) for _, s in self.OPEN]
            heapq.heapify(self.OPEN)
            self.keyed_weight = w

    def f_value(self, s):
        return self.g[s] + self.weight(s) * self.heuristic(s)
