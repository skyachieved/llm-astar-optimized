"""Step 2d part 2: views, renderer, parsing, few-shot pool, the generator, and the METHOD.md 6 "all off" equivalence.
No network: mock chat clients stand in for the LLM."""
import json

import pytest

from llmastar.benchmark import DEFAULT_DATASET, load_queries
from llmastar.model import ChatGPT
from llmastar.pather import LLMAStar, QuorumAStar
from llmastar.quorumastar import QuorumAStarGenerator, QuorumConfig
from llmastar.quorumastar.fewshot import examples_for, pool
from llmastar.quorumastar.geometry import collides, corner_nodes, passes_filter
from llmastar.quorumastar.parsing import parse_ids, parse_points
from llmastar.quorumastar.render import render_map
from llmastar.quorumastar.views import (JUDGE, CornersView, ImageView, PaperView, RelationsView, TextView,
                                        visibility_graph)
from llmastar.waypoints import PromptWaypointGenerator
from tests.test_client import FakeAPI

FIXED = {(1, 0), (1, 3), (7, 2), (23, 8), (42, 5), (77, 1)}
EXAMPLE = {"start": [5, 10], "goal": [45, 12], "range_x": [0, 51], "range_y": [0, 31],
           "horizontal_barriers": [[16, 15, 40]], "vertical_barriers": []}
IMAGE_VIEWS = QuorumConfig(views=("text", "corners", "image"), vision=True)  # image view + judge (both optional)


@pytest.fixture(scope="module")
def queries():
    return load_queries(select=FIXED)


# ---- config ------------------------------------------------------------------------------------------------------

def test_config_defaults_and_variants():
    assert QuorumConfig().variant() is None
    assert QuorumConfig().views == ("text", "corners", "relations")  # agent.md Decisions 2026-11-04 (pilot)
    assert QuorumConfig(vision=True).variant() == "vision" and not QuorumConfig().vision  # judge off since Q12
    assert QuorumConfig.all_off().variant() == "vtext-fspaper-nosnap-add1-k0"
    with pytest.raises(ValueError):
        QuorumConfig(views=("text", "sonar"))


def test_config_from_cli():
    from llmastar.run import parse_args
    args = parse_args(["--method", "quorumastar", "--views", "text,corners", "--no-vision", "--stall-k", "0"])
    config = QuorumConfig.from_args(args)
    assert config.views == ("text", "corners") and not config.vision and config.stall_k == 0


# ---- parsing and rendering ---------------------------------------------------------------------------------------

@pytest.mark.parametrize("text,points", [
    ('{"waypoints": [[1, 2], [3, 4]]}', [(1, 2), (3, 4)]),
    ('```json\n{"waypoints": [[1, 2]]}\n```', [(1, 2)]),
    ('{"reasoning": "go around", "waypoints": [[5.5, 6]]}', [(5.5, 6)]),
    ("Generated Path: [[7, 8], [9, 10]]", [(7, 8), (9, 10)]),
    ('{"waypoints": []}', []),
])
def test_parse_points(text, points):
    assert parse_points(text) == (points, True)


def test_parse_failures_and_ids():
    assert parse_points("no idea") == ([], False)
    assert parse_ids('{"waypoints": [3, "7", "S", 2.0, true]}') == ([3, 7, 2], True)
    assert parse_ids('{"remove": [2]}', key="remove") == ([2], True)
    assert parse_ids("remove [1, 3]", key="remove") == ([1, 3], True)


def test_render_is_a_png(queries):
    png = render_map(queries[0], waypoints=[(10, 12), (25, 20)])
    assert png[:8] == b"\x89PNG\r\n\x1a\n" and len(png) > 5_000


# ---- views ---------------------------------------------------------------------------------------------------------

def test_views_write_different_encodings(queries):
    q = queries[0]
    text = TextView().messages(q)[-1]["content"]
    corners = CornersView().messages(q)[-1]["content"]
    relations = RelationsView().messages(q)[-1]["content"]
    image = ImageView().messages(q)[-1]["content"]
    assert "Horizontal Barriers" in text and "Node S" in corners and "Barriers" not in corners
    assert "A wall at" in relations and "Horizontal Barriers" not in relations
    assert image[1]["type"] == "image_url" and image[1]["image_url"]["url"].startswith("data:image/png;base64,")


def test_corner_graph_and_ids(queries):
    q = queries[0]
    corners, graph = visibility_graph(q)
    assert corners == corner_nodes(q) and graph.count("\n") == len(corners) + 1
    view = CornersView()
    assert view.parse('{"waypoints": [0, 1, 999]}', q) == ([corners[0], corners[1]], True)


def test_relations_sentence():
    text = RelationsView().describe(EXAMPLE)
    assert "A wall at y = 16 blocks x = 15..40; you can pass it at x = 14 or less or x = 41 or more." in text


def test_paper_view_is_llmastar(queries):
    for q in queries:
        assert PaperView().messages(q) == PromptWaypointGenerator(None).messages(q)


# ---- few-shot pool -------------------------------------------------------------------------------------------------

def test_pool_is_deterministic_and_never_an_evaluation_map():
    with open(DEFAULT_DATASET) as f:
        evaluation = {json.dumps([e["horizontal_barriers"], e["vertical_barriers"]]) for e in json.load(f)}
    examples = pool(0, 12)
    assert examples == pool(0, 12)
    for e in examples:
        assert json.dumps([e["horizontal_barriers"], e["vertical_barriers"]]) not in evaluation
        assert collides(e["start"], e["goal"], e)  # (a) the straight line is blocked
        assert set(map(tuple, e["gold"])) <= set(corner_nodes(e))  # (b) gold waypoints are corner nodes


def test_per_view_examples_share_no_map():
    maps = [{json.dumps(e, sort_keys=True) for e in examples_for(i, "per-view", 3, 0, 3)} for i in range(3)]
    assert all(len(m) == 3 for m in maps) and not (maps[0] & maps[1] or maps[0] & maps[2] or maps[1] & maps[2])
    assert examples_for(1, "shared") == examples_for(0, "shared") and examples_for(0, "none") == []


def test_few_shot_answers_are_correct_json(queries):
    example = examples_for(1, "per-view")[0]
    corners, _ = visibility_graph(example)
    ids = json.loads(CornersView().answer_for(example))["waypoints"]
    assert [corners[i] for i in ids] == [tuple(c) for c in example["gold"]]


# ---- the generator with a scripted mock model ---------------------------------------------------------------------

class ScriptedModel:
    """Answers by view: it recognizes the corners view (node ids), the image view (an image part), the vision judge
    (its system prompt) and the text view (anything else)."""

    def __init__(self, text=None, corners=None, image=None, judge=None):
        self.answers = {"text": text, "corners": corners, "image": image, "judge": judge}
        self.calls = []

    def chat_with_info(self, messages, json_mode=False):
        system, last = messages[0]["content"], messages[-1]["content"]
        kind = "judge" if system == JUDGE else "corners" if "node ids" in system else \
            "image" if isinstance(last, list) else "text"
        self.calls.append(kind)
        answer = self.answers[kind]
        if isinstance(answer, Exception):
            return "", {"error": str(answer)}
        return answer, {"cached": False, "usage": {"prompt_tokens": 10, "completion_tokens": 5}}


def _ids(cells, query):
    corners, _ = visibility_graph(query)
    return json.dumps({"waypoints": [corners.index(c) for c in cells]})


def test_generator_votes_judges_and_prunes():
    corner, other = (14, 15), (30, 20)  # corner is a corner node of EXAMPLE; other is a free cell
    assert corner in corner_nodes(EXAMPLE) and passes_filter(other, EXAMPLE)
    model = ScriptedModel(text=json.dumps({"waypoints": [corner, other]}), corners=_ids([corner], EXAMPLE),
                          image=json.dumps({"waypoints": [[13.6, 15.2], other]}), judge='{"remove": []}')
    result = QuorumAStarGenerator(model, IMAGE_VIEWS).generate(EXAMPLE)
    raw = result.raw
    assert sorted(model.calls) == ["corners", "image", "judge", "text"]
    assert [v["cell"] for v in raw["votes"]] == [list(corner), list(other)]  # (13.6, 15.2) snapped to the corner
    assert [v["support"] for v in raw["votes"]] == [3, 2]
    # `other`: support 2 < 3 objects; code: corner->other crosses the wall, other->goal does too, so it is removed
    assert result.waypoints == [corner] and raw["pruning"][1]["removed"]
    assert raw["calls"] == 4 and raw["prompt_tokens"] == 40 and raw["llm_error"] == ""


def test_default_is_text_corners_relations_without_judge():
    corner = (14, 15)
    model = ScriptedModel(text=json.dumps({"waypoints": [corner]}), corners=_ids([corner], EXAMPLE),
                          judge='{"remove": []}')  # the scripted model answers relations like text (no image part)
    result = QuorumAStarGenerator(model).generate(EXAMPLE)
    assert [v["view"] for v in result.raw["views"]] == ["text", "corners", "relations"]
    assert sorted(model.calls) == ["corners", "text", "text"] and result.raw["judge"] is None  # 3 calls, no judge
    assert result.waypoints == [corner] and result.raw["votes"][0]["support"] == 3


def test_an_abstaining_view_and_judge():
    corner = (14, 15)
    model = ScriptedModel(text=json.dumps({"waypoints": [corner]}), corners=_ids([corner], EXAMPLE),
                          image=RuntimeError("model has no image input"), judge=RuntimeError("no image input"))
    result = QuorumAStarGenerator(model, IMAGE_VIEWS).generate(EXAMPLE)
    assert result.waypoints == [corner]
    assert [v["abstained"] for v in result.raw["views"]] == [False, False, True]
    assert result.raw["judge"]["abstained"] and result.raw["llm_error"] == ""  # some views answered


def test_all_views_failing_is_an_llm_error_not_a_crash(queries):
    down = RuntimeError("Connection error")
    result = QuorumAStarGenerator(ScriptedModel(down, down, down, down)).generate(queries[0])
    assert result.waypoints == [] and not result.parse_ok and "Connection error" in result.raw["llm_error"]


def test_generate_never_raises(queries):
    class Broken:
        def chat_with_info(self, messages, json_mode=False):
            raise ValueError("boom")
    result = QuorumAStarGenerator(Broken()).generate(queries[0])
    assert result.waypoints == [] and "boom" in result.raw["llm_error"]


# ---- METHOD.md 6: "all off" reproduces LLM-A* ---------------------------------------------------------------------

ANSWERS = ["Generated Path: [[45, 25], [24, 16], [5, 5]]", "Generated Path: [[10.5, 7.25], [10.5, 7.25], [30, 2]]",
           "Generated Path: [[0, 0], [100, 100]]", "I do not know.", "Generated Path: [[20, 15], [35, 10]]"]


@pytest.mark.parametrize("answer", ANSWERS)
def test_all_off_sends_the_same_request_and_gives_the_same_search(queries, tmp_path, answer):
    llmastar_client = ChatGPT(cache_dir=str(tmp_path / "a"), api_key="dummy")
    llmastar_client._client = FakeAPI([answer] * len(queries))
    quorum_client = ChatGPT(cache_dir=str(tmp_path / "a"), api_key="dummy")  # same cache directory
    quorum_client._client = FakeAPI([])  # any request would fail: everything must come from the cache
    paper = PromptWaypointGenerator(llmastar_client)
    quorum = QuorumAStarGenerator(quorum_client, QuorumConfig.all_off())
    for q in queries:
        expected = paper.generate(q)
        got = quorum.generate(q)
        assert got.raw["views"][0]["cache_key"] == expected.raw["cache_key"]  # same messages and sampling
        assert got.raw["views"][0]["cached"] and got.raw["calls"] == 0  # 0 new requests
        assert got.waypoints == expected.waypoints and got.parse_ok == expected.parse_ok
        base = LLMAStar().searching(q, waypoints=expected.waypoints)
        ours = QuorumAStar(stall_k=0).searching(q, waypoints=got.waypoints)
        for key in ("operation", "storage", "length", "valid", "path", "llm_output"):
            assert ours[key] == base[key], key


# ---- runner, end to end, offline ------------------------------------------------------------------------------------

def test_runner_quorumastar_offline(tmp_path, monkeypatch):
    """No server and no key: every view fails, the run finishes, rows are valid, the new columns are filled."""
    import csv

    import openai

    from llmastar import run
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setattr(openai, "api_key", None, raising=False)
    run.main(["--method", "quorumastar", "--limit", "2", "--jobs", "1", "--trace", "--out", str(tmp_path),
              "--cache-dir", str(tmp_path / "cache")])
    with open(tmp_path / "llama-3-8b-instruct" / "quorumastar.csv", newline="") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 2 and all(r["valid"] == "1" and r["llm_error"] and r["fallback"] == "0" for r in rows)
    assert all(r["calls"] == "3" for r in rows)  # 3 views tried, judge skipped (no waypoints)
