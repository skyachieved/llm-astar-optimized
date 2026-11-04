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

    Same interface as the baseline repository's LLMAStar:
        QuorumAStar(llm="gpt").searching(query=query, filepath="plot.png")
    `llm` is "gpt" (GPT-4o mini, key from openai.api_key or OPENAI_API_KEY), "llama", or any chat client; the
    waypoints then come from QuorumAStarGenerator with `config` (default: METHOD.md 5). The result has LLM-A*'s keys
    plus "fallback". Passing `waypoints` to `searching`, or a `generator`, skips the LLM as in LLMAStar.
    """
    name = "Quorum-A*"

    def __init__(self, llm=None, prompt="standard", generator=None, stall_k=None, stall_min=None, config=None):
        from llmastar.quorumastar.config import QuorumConfig  # imported late: llmastar.quorumastar imports pather
        if config is None:
            config = QuorumConfig(prompt=prompt, prompt_set="gpt" if llm == "gpt" else "llama")
        if stall_k is not None or stall_min is not None:
            from dataclasses import replace
            config = replace(config, stall_k=config.stall_k if stall_k is None else stall_k,
                             stall_min=config.stall_min if stall_min is None else stall_min)
        if generator is None and llm is not None:
            from llmastar.quorumastar import QuorumAStarGenerator
            generator = QuorumAStarGenerator(self._client(llm), config)
        super().__init__(llm=None, prompt=prompt, generator=generator)
        self.llm = getattr(generator, "client", None)  # for natural-language queries, as in LLMAStar
        self.config = config
        assert config.stall_k >= 0 and config.stall_min >= 0
        self.stall_k, self.stall_min = config.stall_k, config.stall_min

    @staticmethod
    def _client(llm):
        if llm == "gpt":
            from llmastar.model import ChatGPT
            return ChatGPT(model="gpt-4o-mini")
        if llm == "llama":
            from llmastar.model import Llama3
            return Llama3()
        if isinstance(llm, str):
            raise ValueError("Invalid LLM model. Pass a chat client, 'gpt' or 'llama'.")
        return llm

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
