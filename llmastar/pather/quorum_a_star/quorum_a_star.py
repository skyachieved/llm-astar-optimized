import heapq

from llmastar.pather.llm_a_star.llm_a_star import LLMAStar


class QuorumAStar(LLMAStar):
    """LLM-A*'s search with one addition: a stall fallback (METHOD.md 4.7).

    The loop, f-value and metrics are inherited unchanged. A target becomes *active* at the start of the search
    and whenever the search switches to the next waypoint. Its pop budget is
        k * max(stall_min, |ax - tx| + |ay - ty|),
    where a is the node being expanded when the target became active (the start for the first target) and t is
    the target. If more pops than that pass while the same target is active and it is not the goal, the remaining
    waypoints are dropped, the goal becomes the target and OPEN is re-keyed, so the search continues as weighted
    A* with w = 2 (h = 2 * distance to goal), exactly what LLM-A* does when it has no waypoints.

    The fallback fires at most once per query. `stall_k=0` turns it off; the search is then LLM-A* exactly.
    """
    name = "Quorum-A*"

    def __init__(self, llm=None, prompt="standard", generator=None, stall_k=2.0, stall_min=20):
        super().__init__(llm=llm, prompt=prompt, generator=generator)
        assert stall_k >= 0 and stall_min >= 0
        self.stall_k, self.stall_min = stall_k, stall_min

    def _initialize_targets(self, waypoints):
        super()._initialize_targets(waypoints)
        self.pops = 0
        self.fallback = None  # set to a dict when the fallback fires
        self._activate_target(self.s_start)

    def _activate_target(self, node):
        """Record where and when the current target became active, and its pop budget."""
        self.active_since = self.pops
        manhattan = abs(node[0] - self.s_target[0]) + abs(node[1] - self.s_target[1])
        self.budget = self.stall_k * max(self.stall_min, manhattan)

    def _update_target(self):
        super()._update_target()
        self._activate_target(self._expanding)

    def _after_pop(self, s):
        self.pops += 1
        self._expanding = s
        if self.stall_k == 0 or self.fallback is not None or self.s_target == self.s_goal:
            return
        if self.pops - self.active_since > self.budget:
            dropped = self.target_list[self.i:-1]
            self.fallback = {"pop": self.pops, "node": s, "target": self.s_target, "dropped": dropped}
            self.target_list = self.target_list[:self.i] + [self.s_goal]
            self.i = len(self.target_list) - 1
            self.s_target = self.s_goal
            self._update_queue()

    def searching(self, query, filepath=None, waypoints=None):
        self._expanding = None
        result = super().searching(query, filepath=filepath, waypoints=waypoints)
        result["fallback"] = self.fallback
        return result

    # `_update_queue` re-keys OPEN with the parent's rule; kept here only to document that the fallback uses it.
    def _update_queue(self):
        queue = []
        for _, s in self.OPEN:
            heapq.heappush(queue, (self.f_value(s), s))
        self.OPEN = queue
