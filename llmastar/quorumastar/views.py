"""The voters (METHOD.md 4.1): each view writes the same query in a different encoding, makes one LLM call and
returns its waypoints. A view abstains when its call fails, the model has no image input, or nothing parses.

  text       the repo's coordinate format (start, goal, barrier lists); answers [[x, y], ...]
  corners    the visibility graph of corner nodes as an incident adjacency list; answers node ids
  image      a PNG of the map (zero-shot); answers [[x, y], ...]
  relations  the walls in words, with where each can be passed; answers [[x, y], ...]
  paper      LLM-A*'s own prompt and parser, unchanged (the text view under --fewshot paper)
"""
import json
from functools import lru_cache

from llmastar.model.chatgpt import image_part
from llmastar.waypoints import PromptWaypointGenerator, parse_waypoints

from .geometry import collides, corner_nodes, distance
from .parsing import parse_ids, parse_points
from .render import render_map

SYSTEM = ("You plan paths on a 2D grid map. The path goes from the start to the goal and must not cross any wall. "
          "Propose waypoints: points the path should pass through, in order from start to goal, so that the straight "
          "segment between consecutive points (start and goal included) crosses no wall. Use as few waypoints as "
          "possible; good waypoints sit just past the end of a wall. Coordinates are integers [x, y]; x grows to "
          "the right and y grows upward.")
ROLES = {
    "text": "You are a careful planner who works with coordinates.",
    "corners": "You are a graph-search expert who plans routes on graphs.",
    "image": "You are a visual navigator who reads maps by looking at them.",
    "relations": "You are a spatial reasoner who thinks about walls and the gaps around them.",
}
ANSWER_POINTS = 'Answer only with a JSON object: {"waypoints": [[x, y], ...]}.'
ANSWER_IDS = 'Answer only with a JSON object: {"waypoints": [node ids in order from S to G, without S and G]}.'
COT = ' First reason in at most five short sentences in a "reasoning" field, then give "waypoints".'


def _grid(query):
    (x0, x1), (y0, y1) = query["range_x"], query["range_y"]
    return f"The map spans x = {x0}..{x1 - 1} and y = {y0}..{y1 - 1}; its border is a wall."


def _coordinates(query):
    return (f"Start Point: {list(query['start'])}\nGoal Point: {list(query['goal'])}\n"
            f"Horizontal Barriers ([y, x_start, x_end]): {query['horizontal_barriers']}\n"
            f"Vertical Barriers ([x, y_start, y_end]): {query['vertical_barriers']}")


def _endpoints(query):
    return f"Start Point: {list(query['start'])}\nGoal Point: {list(query['goal'])}"


def _relations(query):
    (x0, x1), (y0, y1) = query["range_x"], query["range_y"]
    lines = []
    for y, xa, xb in query["horizontal_barriers"]:
        sides = ([f"x = {xa - 1} or less"] if xa - 1 > x0 + 1 else []) + \
                ([f"x = {xb + 1} or more"] if xb + 1 < x1 - 2 else [])
        gap = " or ".join(sides) if sides else "nowhere (it spans the map)"
        lines.append(f"A wall at y = {y} blocks x = {xa}..{xb}; you can pass it at {gap}.")
    for x, ya, yb in query["vertical_barriers"]:
        sides = ([f"y = {ya - 1} or less"] if ya - 1 > y0 + 1 else []) + \
                ([f"y = {yb + 1} or more"] if yb + 1 < y1 - 2 else [])
        gap = " or ".join(sides) if sides else "nowhere (it spans the map)"
        lines.append(f"A wall at x = {x} blocks y = {ya}..{yb}; you can pass it at {gap}.")
    return "\n".join(lines)


def _graph_key(query):
    return json.dumps({k: query[k] for k in ("start", "goal", "range_x", "range_y", "horizontal_barriers",
                                            "vertical_barriers")}, sort_keys=True)


@lru_cache(maxsize=4096)
def _graph(key):
    query = json.loads(key)
    corners = corner_nodes(query)
    nodes = [(str(i), c) for i, c in enumerate(corners)] + [("S", tuple(query["start"])), ("G", tuple(query["goal"]))]
    lines = []
    for name, cell in nodes:
        seen = [f"{other} ({distance(cell, c):.1f})" for other, c in nodes
                if other != name and not collides(cell, c, query)]
        lines.append(f"Node {name} ({cell[0]}, {cell[1]}): sees {', '.join(seen) if seen else 'nothing'}")
    return corners, "\n".join(lines)


def visibility_graph(query):
    """(corner cells by node id, the incident adjacency list as text)."""
    return _graph(_graph_key(query))


class View:
    name = ""
    answer = ANSWER_POINTS
    json_mode = True
    zero_shot = False

    def __init__(self, cot=False, roles=False):
        self.cot, self.roles = cot, roles

    def system(self):
        role = ROLES.get(self.name, "") + " " if self.roles else ""
        return role + SYSTEM + " " + self.answer + (COT if self.cot else "")

    def describe(self, query):
        raise NotImplementedError

    def answer_for(self, example):
        return json.dumps({"waypoints": [list(c) for c in example["gold"]]})

    def messages(self, query, examples=()):
        messages = [{"role": "system", "content": self.system()}]
        for example in ([] if self.zero_shot else examples):
            messages += [{"role": "user", "content": self.describe(example)},
                         {"role": "assistant", "content": self.answer_for(example)}]
        messages.append({"role": "user", "content": self.describe(query)})
        return messages

    def parse(self, text, query):
        return parse_points(text)


class TextView(View):
    name = "text"

    def describe(self, query):
        return f"{_grid(query)}\n{_coordinates(query)}"


class RelationsView(View):
    name = "relations"

    def describe(self, query):
        return f"{_grid(query)}\n{_endpoints(query)}\nWalls:\n{_relations(query)}"


class CornersView(View):
    name = "corners"
    answer = ANSWER_IDS

    def describe(self, query):
        _, graph = visibility_graph(query)
        return ("Nodes are free cells next to wall ends. Each line lists a node, its coordinates and the nodes it "
                "can see in a straight line (no wall in between), with the distance.\n" + graph)

    def answer_for(self, example):
        corners, _ = visibility_graph(example)
        index = {c: i for i, c in enumerate(corners)}
        return json.dumps({"waypoints": [index[tuple(c)] for c in example["gold"]]})

    def parse(self, text, query):
        corners, _ = visibility_graph(query)
        ids, ok = parse_ids(text)
        return [corners[i] for i in ids if 0 <= i < len(corners)], ok


class ImageView(View):
    name = "image"
    zero_shot = True

    def describe(self, query):
        text = (f"The image shows the map. {_grid(query)} Black segments are walls, S is the start and G the goal; "
                f"the axes are labelled every 5 cells.\n{_endpoints(query)}")
        return [{"type": "text", "text": text}, image_part(render_map(query))]


class PaperView(View):
    """LLM-A*'s exact messages and parser (`--fewshot paper`), so the "all off" run reuses LLM-A*'s cache."""
    name = "text"
    json_mode = False

    def __init__(self, prompt="standard", prompt_set="llama"):
        super().__init__()
        self._paper = PromptWaypointGenerator(None, prompt, prompt_set)

    def messages(self, query, examples=()):
        return self._paper.messages(query)

    def parse(self, text, query):
        return parse_waypoints(text or "")


VIEWS = {"text": TextView, "corners": CornersView, "image": ImageView, "relations": RelationsView}

JUDGE = ("You check proposed waypoints on a 2D grid map. The image shows the map: black segments are walls, S is the "
         "start, G the goal, and the numbered circles 1..n are the proposed waypoints, joined in order by a dashed "
         "line from S to G. List the numbers of the waypoints that should be removed: a waypoint that lies on or "
         "against a wall, whose dashed segments cross a wall, or that leads into a dead end. Never add or move a "
         'waypoint. Answer only with a JSON object: {"remove": [numbers]}, or {"remove": []} if all are fine.')


def judge_messages(query, waypoints):
    text = f"{_grid(query)}\n{_endpoints(query)}\nWaypoints: " + \
        ", ".join(f"{i} = {list(w)}" for i, w in enumerate(waypoints, start=1))
    return [{"role": "system", "content": JUDGE},
            {"role": "user", "content": [{"type": "text", "text": text}, image_part(render_map(query, waypoints))]}]


def parse_judge(text, n):
    ids, ok = parse_ids(text, key="remove")
    return sorted({i for i in ids if 1 <= i <= n}), ok
