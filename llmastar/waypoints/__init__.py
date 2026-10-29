"""Waypoint generation: map + start/goal -> waypoint list. LLM-A*'s search consumes the list and nothing else."""
from .base import WaypointGenerator, WaypointResult, parse_waypoints
from .prompting import PromptWaypointGenerator

# Generators selectable with `python -m llmastar.run --generator NAME`. Each entry builds a generator from a
# chat client and the parsed CLI args. New waypoint methods (e.g. Clear Democratic A*) register here.
REGISTRY = {
    "prompt": lambda client, args: PromptWaypointGenerator(client, args.prompt, args.prompt_set),
}
