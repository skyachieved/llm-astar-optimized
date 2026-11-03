"""Every Quorum-A* setting in one place (METHOD.md 5): defaults, CLI flags and the run-name variant."""
import argparse
from dataclasses import dataclass, fields

VIEWS = ("text", "corners", "image", "relations")
FEWSHOT = ("per-view", "shared", "none", "paper")


@dataclass(frozen=True)
class QuorumConfig:
    views: tuple = ("text", "corners", "image")
    fewshot: str = "per-view"
    n_shots: int = 3
    fewshot_seed: int = 0
    cot: bool = False
    roles: bool = False
    json_mode: bool = True
    snap: bool = True
    snap_cell_radius: int = 2
    snap_corner_radius: float = 3.0
    add_quorum: int = 2
    remove_quorum: int = 2
    vision: bool = True
    stall_k: float = 2.0
    stall_min: int = 20
    prompt: str = "standard"  # used by --fewshot paper (the text view then sends LLM-A*'s exact messages)
    prompt_set: str = "llama"

    def __post_init__(self):
        unknown = set(self.views) - set(VIEWS)
        if unknown or not self.views:
            raise ValueError(f"--views must be a non-empty subset of {','.join(VIEWS)}; got {','.join(self.views)}")
        if self.fewshot not in FEWSHOT:
            raise ValueError(f"--fewshot must be one of {', '.join(FEWSHOT)}")

    @classmethod
    def all_off(cls, prompt="standard", prompt_set="llama"):
        """METHOD.md 6: the setting that reproduces LLM-A* exactly."""
        return cls(views=("text",), fewshot="paper", add_quorum=1, vision=False, snap=False, stall_k=0,
                   prompt=prompt, prompt_set=prompt_set)

    @classmethod
    def from_args(cls, args):
        values = {f.name: getattr(args, f.name) for f in fields(cls) if hasattr(args, f.name)}
        if isinstance(values.get("views"), str):
            values["views"] = tuple(v.strip() for v in values["views"].split(",") if v.strip())
        return cls(**values)

    def variant(self):
        """Run-name suffix for non-default settings, in a fixed order, e.g. quorumastar-novision-k0."""
        d = QuorumConfig()
        parts = []
        if self.views != d.views:
            parts.append("v" + "+".join(self.views))
        if self.fewshot != d.fewshot:
            parts.append("fs" + self.fewshot.replace("-", ""))
        if self.n_shots != d.n_shots:
            parts.append(f"shots{self.n_shots}")
        if self.fewshot_seed != d.fewshot_seed:
            parts.append(f"fsseed{self.fewshot_seed}")
        parts += [name for name, on in (("cot", self.cot), ("roles", self.roles)) if on]
        if not self.json_mode:
            parts.append("nojson")
        if not self.snap:
            parts.append("nosnap")
        if (self.snap_cell_radius, self.snap_corner_radius) != (d.snap_cell_radius, d.snap_corner_radius):
            parts.append(f"snap{self.snap_cell_radius:g}x{self.snap_corner_radius:g}")
        if self.add_quorum != d.add_quorum:
            parts.append(f"add{self.add_quorum}")
        if self.remove_quorum != d.remove_quorum:
            parts.append(f"rm{self.remove_quorum}")
        if not self.vision:
            parts.append("novision")
        if self.stall_k != d.stall_k:
            parts.append(f"k{self.stall_k:g}")
        if self.stall_min != d.stall_min:
            parts.append(f"kmin{self.stall_min}")
        if self.fewshot == "paper" and self.prompt != d.prompt:
            parts.append(self.prompt)
        return "-".join(parts) or None


def add_cli_args(parser):
    d = QuorumConfig()
    g = parser.add_argument_group("Quorum-A* (--method quorumastar; METHOD.md 5)")
    g.add_argument("--views", default=",".join(d.views), help=f"voters, any subset of {','.join(VIEWS)}")
    g.add_argument("--fewshot", default=d.fewshot, choices=FEWSHOT)
    g.add_argument("--n-shots", type=int, default=d.n_shots)
    g.add_argument("--fewshot-seed", type=int, default=d.fewshot_seed)
    g.add_argument("--cot", action="store_true", help="each view reasons briefly before its JSON answer")
    g.add_argument("--roles", action="store_true", help="each view gets its own system role")
    g.add_argument("--json-mode", action=argparse.BooleanOptionalAction, default=d.json_mode)
    g.add_argument("--snap", action=argparse.BooleanOptionalAction, default=d.snap)
    g.add_argument("--snap-cell-radius", type=int, default=d.snap_cell_radius)
    g.add_argument("--snap-corner-radius", type=float, default=d.snap_corner_radius)
    g.add_argument("--add-quorum", type=int, default=d.add_quorum)
    g.add_argument("--remove-quorum", type=int, default=d.remove_quorum, help="0 = no pruning")
    g.add_argument("--vision", action=argparse.BooleanOptionalAction, default=d.vision)
    g.add_argument("--stall-k", type=float, default=d.stall_k, help="0 = no stall fallback")
    g.add_argument("--stall-min", type=int, default=d.stall_min)
    return parser
