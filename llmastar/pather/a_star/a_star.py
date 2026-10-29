import copy
import math
import heapq

from llmastar.env.search import env, plotting
from llmastar.utils import is_lines_collision

class AStar:
    """AStar set the cost + heuristics as the priority
    """
    name = "A*"

    def __init__(self):
        pass

    def searching(self, query, filepath=None):
        """
        A_star Searching.
        :param query: dict with start, goal, range_x, range_y, horizontal_barriers, vertical_barriers
        :param filepath: if given, save a plot of the search there
        :return: metrics (operation = heap pops incl. duplicates, storage = len(g), length = sum of
                 Euclidean steps), valid (goal reached), path (start -> goal) and visited order
        """
        query = copy.deepcopy(query)  # the range adjustment below must not leak into the caller's query
        self.filepath = filepath
        self.s_start = (query['start'][0], query['start'][1])
        self.s_goal = (query['goal'][0], query['goal'][1])
        
        self.horizontal_barriers = query['horizontal_barriers']
        self.vertical_barriers = query['vertical_barriers']
        self.range_x = query['range_x']
        self.range_y = query['range_y']
        self.Env = env.Env(self.range_x[1], self.range_y[1], self.horizontal_barriers, self.vertical_barriers)  # class Env
        self.range_x[1] -= 1
        self.range_y[1] -= 1
        self.u_set = self.Env.motions  # feasible input set
        self.obs = self.Env.obs  # position of obstacles
        self.OPEN = []  # priority queue / OPEN set
        self.CLOSED = []  # CLOSED set / VISITED order
        self.closed_set = set()  # same states as CLOSED, for O(1) membership tests
        self.PARENT = dict()  # recorded parent
        self.g = dict()  # cost to come
        self.count = 0  # heap pops so far

        self.PARENT[self.s_start] = self.s_start
        self.g[self.s_start] = 0
        # self.g[self.s_goal] = math.inf
        heapq.heappush(self.OPEN,
                    (self.f_value(self.s_start), self.s_start))

        found = False
        while self.OPEN:
            self.count += 1
            self.before_pop()
            _, s = heapq.heappop(self.OPEN)
            self.CLOSED.append(s)
            self.closed_set.add(s)

            if s == self.s_goal:  # stop condition
                found = True
                break

            for s_n in self.get_neighbor(s):
                if s_n in self.closed_set:
                    continue
                new_cost = self.g[s] + self.cost(s, s_n)

                if s_n not in self.g:
                    self.g[s_n] = math.inf

                if new_cost < self.g[s_n]:  # conditions for updating Cost
                    self.g[s_n] = new_cost
                    self.PARENT[s_n] = s
                    heapq.heappush(self.OPEN, (self.f_value(s_n), s_n))

        path = self.extract_path(self.PARENT)[::-1] if found else []
        visited = self.CLOSED
        result = {"operation": self.count, "storage": len(self.g),
                  "length": sum(self._euclidean_distance(path[i], path[i+1]) for i in range(len(path)-1)) if found else None,
                  "valid": found, "path": path, "visited": visited}
        if self.filepath:
            plotting.Plotting(self.s_start, self.s_goal, self.Env).animation(path, visited, False, self.name, self.filepath)
        return result
    
    def before_pop(self):
        """Hook for subclasses that change priorities during the search (e.g. Dynamic WA* re-keying OPEN)."""

    @staticmethod
    def _euclidean_distance(p1, p2):
        return math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)
    
    def updated_queue(self):
        queue = []
        for _, s in self.OPEN:
            heapq.heappush(queue, (self.f_value(s), s))
        return queue
            
            
    def get_target(self):
        self.i += 1
        if self.i < len(self.target_list):
            self.s_target = self.target_list[self.i]

    def get_neighbor(self, s):
        """
        find neighbors of state s that not in obstacles.
        :param s: state
        :return: neighbors
        """
        
        neighbors = [(s[0] + u[0], s[1] + u[1]) for u in self.u_set]
        return neighbors 

    def cost(self, s_start, s_goal):
        """
        Calculate Cost for this motion
        :param s_start: starting node
        :param s_goal: end node
        :return:  Cost for this motion
        :note: Cost function could be more complicate!
        """

        if self.is_collision(s_start, s_goal):
            return math.inf

        return math.hypot(s_goal[0] - s_start[0], s_goal[1] - s_start[1])

    def is_collision(self, s_start, s_end):
        """
        check if the line segment (s_start, s_end) is collision.
        :param s_start: start node
        :param s_end: end node
        :return: True: is collision / False: not collision
        """

        line1=[s_start, s_end]
        for horizontal in self.horizontal_barriers:
            line2 = [[horizontal[1], horizontal[0]], [horizontal[2], horizontal[0]]]
            if is_lines_collision(line1, line2):
                return True
        for vertical in self.vertical_barriers:
            line2 = [[vertical[0], vertical[1]], [vertical[0], vertical[2]]]
            if is_lines_collision(line1, line2):
                return True
        for x in self.range_x:
            line2 = [[x, self.range_y[0]], [x, self.range_y[1]]]
            if is_lines_collision(line1, line2):
                return True
        for y in self.range_y:
            line2 = [[self.range_x[0], y], [self.range_x[1], y]]
            if is_lines_collision(line1, line2):
                return True
        return False

    def f_value(self, s):
        """
        f = g + h. (g: Cost to come, h: heuristic value)
        :param s: current state
        :return: f
        """

        return self.g[s] + self.heuristic(s)

    def extract_path(self, PARENT):
        """
        Extract the path based on the PARENT set.
        :return: The planning path
        """

        path = [self.s_goal]
        s = self.s_goal

        while True:
            s = PARENT[s]
            path.append(s)

            if s == self.s_start:
                break

        return list(path)

    def heuristic(self, s):
        """
        Calculate heuristic.
        :param s: current node (state)
        :return: heuristic function value
        """
        goal = self.s_goal  # goal node
        
        return math.hypot(goal[0] - s[0], goal[1] - s[1])
