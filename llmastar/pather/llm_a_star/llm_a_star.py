import ast
import copy
import json
import math
import heapq

from llmastar.env.search import env, plotting
from llmastar.utils import is_lines_collision
from .prompt import sysprompt_parse, example_parse

class LLMAStar:
    """LLM-A* algorithm with cost + heuristics as the priority.

    The search only consumes a waypoint list. Where it comes from is pluggable:
      - pass `waypoints` to `searching` (the runner does this after batching the LLM calls), or
      - give `generator`: any object with `generate(query) -> WaypointResult` (see llmastar.waypoints), or
      - give `llm` (a chat client such as ChatGPT(model, base_url), or 'gpt' / 'llama' for the defaults)
        and `prompt` to use the paper's prompting.
    """

    name = "LLM-A*"

    def __init__(self, llm=None, prompt='standard', generator=None):
        assert prompt in ['standard', 'cot', 'repe'], "Invalid prompt type. Choose 'standard', 'cot', or 'repe'."
        self.prompt = prompt
        if llm == 'gpt':
            from llmastar.model import ChatGPT
            llm = ChatGPT(model="gpt-3.5-turbo")
        elif llm == 'llama':
            from llmastar.model import Llama3
            llm = Llama3()
        elif isinstance(llm, str):
            raise ValueError("Invalid LLM model. Pass a chat client, 'gpt' or 'llama'.")
        self.llm = llm
        if generator is None and llm is not None:
            from llmastar.waypoints import PromptWaypointGenerator
            generator = PromptWaypointGenerator(llm, prompt)
        self.generator = generator

    def _parse_query(self, query):
        """Parse a natural-language query into the dict format using the LLM."""
        if isinstance(query, str):
            if self.llm is None:
                raise ValueError("A natural-language query needs an `llm` to parse it.")
            messages = [{"role": "system", "content": sysprompt_parse}]
            for example in example_parse.values():
                user, assistant = example.split("\n", 1)
                messages += [{"role": "user", "content": user}, {"role": "assistant", "content": assistant}]
            messages.append({"role": "user", "content": query})
            response = self.llm.chat(messages).strip()
            try:
                return json.loads(response)
            except json.JSONDecodeError:
                return ast.literal_eval(response)
        return query

    def _initialize_parameters(self, input_data):
        """Initialize environment parameters from input data."""
        self.s_start = tuple(input_data['start'])
        self.s_goal = tuple(input_data['goal'])
        self.horizontal_barriers = input_data['horizontal_barriers']
        self.vertical_barriers = input_data['vertical_barriers']
        self.range_x = input_data['range_x']
        self.range_y = input_data['range_y']
        self.Env = env.Env(self.range_x[1], self.range_y[1], self.horizontal_barriers, self.vertical_barriers)
        # Adjust range limits
        self.range_x[1] -= 1
        self.range_y[1] -= 1
        self.u_set = self.Env.motions
        self.obs = self.Env.obs
        self.OPEN = []
        self.CLOSED = []
        self.closed_set = set()  # same states as CLOSED, for O(1) membership tests
        self.PARENT = dict()
        self.g = dict()

    def _initialize_targets(self, waypoints):
        """Build the TARGET list from proposed waypoints: drop invalid nodes, ensure start and goal."""
        self.target_list = self._filter_valid_nodes(waypoints)

        if not self.target_list or self.target_list[0] != self.s_start:
            self.target_list.insert(0, self.s_start)
        if not self.target_list or self.target_list[-1] != self.s_goal:
            self.target_list.append(self.s_goal)
        self.i = 1
        self.s_target = self.target_list[1]

    def _filter_valid_nodes(self, nodes):
        """Filter out invalid nodes based on environment constraints."""
        return [(node[0], node[1]) for node in nodes
                if (node[0], node[1]) not in self.obs
                and self.range_x[0] + 1 < node[0] < self.range_x[1] - 1
                and self.range_y[0] + 1 < node[1] < self.range_y[1] - 1]

    def searching(self, query, filepath=None, waypoints=None):
        """
        A* searching algorithm guided by waypoints.
        :param waypoints: [(x, y), ...] proposed waypoints; if None, they are generated with `self.generator`
        :param filepath: if given, save a plot of the search there
        :return: metrics (same definitions as A*), valid, path, visited order, and the TARGET list used
        """
        self.filepath = filepath
        input_data = copy.deepcopy(self._parse_query(query))
        if waypoints is None:
            if self.generator is None:
                raise ValueError("No waypoints given and no waypoint generator / llm configured.")
            waypoints = self.generator.generate(copy.deepcopy(input_data)).waypoints
        self._initialize_parameters(input_data)
        self._initialize_targets(waypoints)

        self.PARENT[self.s_start] = self.s_start
        self.g[self.s_start] = 0
        heapq.heappush(self.OPEN, (self.f_value(self.s_start), self.s_start))

        found = False
        while self.OPEN:
            _, s = heapq.heappop(self.OPEN)
            self.CLOSED.append(s)
            self.closed_set.add(s)

            if s == self.s_goal:  # stop condition
                found = True
                break

            for s_n in self.get_neighbor(s):
                if s_n == self.s_target and self.s_goal != self.s_target :
                    self._update_target()
                    self._update_queue()

                if s_n in self.closed_set:
                    continue

                new_cost = self.g[s] + self.cost(s, s_n)
                if s_n not in self.g:
                    self.g[s_n] = math.inf

                if new_cost < self.g[s_n]:  # conditions for updating Cost
                    self.g[s_n] = new_cost
                    self.PARENT[s_n] = s
                    heapq.heappush(self.OPEN, (self.f_value(s_n), s_n))

        path = self.extract_path(self.PARENT) if found else []
        visited = self.CLOSED
        result = {
            "operation": len(self.CLOSED),
            "storage": len(self.g),
            "length": sum(self._euclidean_distance(path[i], path[i+1]) for i in range(len(path)-1)) if found else None,
            "valid": found,
            "path": path,
            "visited": visited,
            "llm_output": self.target_list
        }
        if self.filepath:
            plot = plotting.Plotting(self.s_start, self.s_goal, self.Env)
            plot.animation(path, visited, False, self.name, self.filepath)
        return result

    @staticmethod
    def _euclidean_distance(p1, p2):
        return math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)

    def _update_queue(self):
        queue = []
        for _, s in self.OPEN:
            heapq.heappush(queue, (self.f_value(s), s))
        self.OPEN = queue

    def _update_target(self):
        """Update the current target in the path."""
        self.i += 1
        if self.i < len(self.target_list):
            self.s_target = self.target_list[self.i]

    def get_neighbor(self, s):
        """Find neighbors of state s that are not in obstacles."""
        return [(s[0] + u[0], s[1] + u[1]) for u in self.u_set]

    def cost(self, s_start, s_goal):
        """Calculate cost for the motion from s_start to s_goal."""
        return math.inf if self.is_collision(s_start, s_goal) else math.hypot(s_goal[0] - s_start[0], s_goal[1] - s_start[1])

    def is_collision(self, s_start, s_end):
        """Check if the line segment (s_start, s_end) collides with any barriers."""
        line1 = [s_start, s_end]
        return any(is_lines_collision(line1, [[h[1], h[0]], [h[2], h[0]]]) for h in self.horizontal_barriers) or \
                any(is_lines_collision(line1, [[v[0], v[1]], [v[0], v[2]]]) for v in self.vertical_barriers) or \
                any(is_lines_collision(line1, [[x, self.range_y[0]], [x, self.range_y[1]]]) for x in self.range_x) or \
                any(is_lines_collision(line1, [[self.range_x[0], y], [self.range_x[1], y]]) for y in self.range_y)

    def f_value(self, s):
        """Compute the f-value for state s."""
        return self.g[s] + self.heuristic(s)

    def extract_path(self, PARENT):
        """Extract the path based on the PARENT set."""
        path = [self.s_goal]
        while path[-1] != self.s_start:
            path.append(PARENT[path[-1]])
        return path[::-1]

    def heuristic(self, s):
        """Calculate heuristic value."""
        return math.hypot(self.s_goal[0] - s[0], self.s_goal[1] - s[1]) + math.hypot(self.s_target[0] - s[0], self.s_target[1] - s[1])
