"""Quorum-A*: multi-view LLM consensus for LLM-A*'s waypoint step (METHOD.md). The search itself is
llmastar.pather.QuorumAStar; this package turns a query into a waypoint list.

Step 2d, part 1 (this commit): the deterministic core, which needs no LLM.
  geometry   waypoint filter, corner nodes, visibility
  canonical  snap a proposed point to a cell, then to a nearby corner node (METHOD.md 4.3)
  voting     majority add (4.4)
  pruning    majority remove with the code / vision / support checks (4.5)
Part 2 adds the views, the image renderer, the few-shot pool and the generator.
"""
