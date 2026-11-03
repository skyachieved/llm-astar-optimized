"""Waypoint generation: map + start/goal -> waypoint list. LLM-A*'s search consumes the list and nothing else."""
from .base import WaypointGenerator, WaypointResult, parse_waypoints
from .prompting import PromptWaypointGenerator

# Generators selectable with `python -m llmastar.run --generator NAME`. Each entry builds a generator from a
# chat client and the parsed CLI args. New waypoint methods (e.g. Quorum-A*) register here.
def _quorumastar(client, args):
    from llmastar.quorumastar import QuorumAStarGenerator, QuorumConfig  # imported late: it imports this package
    return QuorumAStarGenerator(client, QuorumConfig.from_args(args))


REGISTRY = {
    "prompt": lambda client, args: PromptWaypointGenerator(client, args.prompt, args.prompt_set),
    "quorumastar": _quorumastar,
}
