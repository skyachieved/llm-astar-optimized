"""Map -> PNG for the image view and the vision judge (METHOD.md 4.1, 4.5).

20 px per cell, x and y labelled every 5 cells, a light grid line every cell, y pointing up, barriers as thick black
segments, S and G marked. With `waypoints`, they are drawn as numbers 1..n joined by a dashed line from S to G.
"""
import io

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

PX_PER_CELL = 20
DPI = 100


def render_map(query, waypoints=None):
    (x0, x1), (y0, y1) = query["range_x"], query["range_y"]
    width, height = (x1 - x0) * PX_PER_CELL / DPI, (y1 - y0) * PX_PER_CELL / DPI
    fig, ax = plt.subplots(figsize=(width + 0.8, height + 0.6), dpi=DPI)
    try:
        ax.set_xlim(x0, x1 - 1)
        ax.set_ylim(y0, y1 - 1)
        ax.set_aspect("equal")
        ax.set_xticks(range(x0, x1, 5))
        ax.set_yticks(range(y0, y1, 5))
        ax.set_xticks(range(x0, x1), minor=True)
        ax.set_yticks(range(y0, y1), minor=True)
        ax.grid(which="minor", color="#dddddd", linewidth=0.5)
        ax.grid(which="major", color="#bbbbbb", linewidth=0.8)
        ax.tick_params(labelsize=7)
        for y, xa, xb in query["horizontal_barriers"]:
            ax.plot([xa, xb], [y, y], color="black", linewidth=3, solid_capstyle="butt")
        for x, ya, yb in query["vertical_barriers"]:
            ax.plot([x, x], [ya, yb], color="black", linewidth=3, solid_capstyle="butt")
        start, goal = query["start"], query["goal"]
        if waypoints:
            xs = [start[0]] + [w[0] for w in waypoints] + [goal[0]]
            ys = [start[1]] + [w[1] for w in waypoints] + [goal[1]]
            ax.plot(xs, ys, linestyle="--", color="#1f77b4", linewidth=1.2)
            for i, w in enumerate(waypoints, start=1):
                ax.annotate(str(i), (w[0], w[1]), color="white", fontsize=8, fontweight="bold", ha="center",
                            va="center", bbox={"boxstyle": "circle,pad=0.2", "fc": "#1f77b4", "ec": "none"})
        for point, label, color in ((start, "S", "#2ca02c"), (goal, "G", "#d62728")):
            ax.annotate(label, (point[0], point[1]), color="white", fontsize=9, fontweight="bold", ha="center",
                        va="center", bbox={"boxstyle": "square,pad=0.25", "fc": color, "ec": "none"})
        fig.tight_layout(pad=0.3)
        buffer = io.BytesIO()
        fig.savefig(buffer, format="png", dpi=DPI)
        return buffer.getvalue()
    finally:
        plt.close(fig)
