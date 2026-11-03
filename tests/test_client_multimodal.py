"""Step 2c: image message parts (the cache keeps only a hash) and JSON mode with a fallback. No network."""
import json

from llmastar.model import ChatGPT, image_part, redact_images
from llmastar.model.cache import cache_key
from tests.test_client import FakeAPI, FakeError, MESSAGES, make_client

PNG_A, PNG_B = b"\x89PNG fake image A", b"\x89PNG fake image B"


def vision_messages(png):
    return [{"role": "user", "content": [{"type": "text", "text": "Which waypoints lie on a wall?"}, image_part(png)]}]


def test_text_only_cache_keys_are_unchanged(tmp_path):
    client = make_client(["a"], tmp_path)
    _, info = client.chat_with_info(MESSAGES)
    old_key = cache_key({"model": client.model, "base_url": client.base_url, "messages": MESSAGES,
                         "sampling": client.sampling})
    assert info["cache_key"] == old_key  # caches written before step 2c still hit


def test_images_are_sent_whole_but_cached_as_a_hash(tmp_path):
    client = make_client(["sees A", "sees B"], tmp_path)
    content_a, info_a = client.chat_with_info(vision_messages(PNG_A))
    content_b, info_b = client.chat_with_info(vision_messages(PNG_B))
    assert (content_a, content_b) == ("sees A", "sees B") and info_a["cache_key"] != info_b["cache_key"]
    assert client.chat_with_info(vision_messages(PNG_A))[1]["cached"]  # same image, same key
    record = json.dumps(client.cache.get(info_a["cache_key"]))
    assert "base64" not in record and "sha256:" in record


def test_redaction_leaves_the_caller_messages_alone():
    messages = vision_messages(PNG_A)
    redacted = redact_images(messages)
    assert messages[0]["content"][1]["image_url"]["url"].startswith("data:image/png;base64,")
    assert redacted[0]["content"][1]["image_url"]["url"].startswith("sha256:")


def test_a_text_only_model_rejecting_the_image_is_an_error_not_a_crash(tmp_path):
    client = make_client([FakeError(400, "this model is not a multimodal model")], tmp_path)
    content, info = client.chat_with_info(vision_messages(PNG_A))
    assert content == "" and info["attempts"] == 1 and "multimodal" in info["error"]


def test_json_mode_is_sent_and_dropped_when_rejected(tmp_path):
    client = make_client([FakeError(400, "'response_format' of type 'json_object' is not supported with this model"),
                          '{"waypoints": [[1, 2]]}'], tmp_path)
    content, info = client.chat_with_info(MESSAGES, json_mode=True)
    assert json.loads(content) == {"waypoints": [[1, 2]]} and info["dropped_params"] == ["response_format"]
    assert client._client.calls[0]["response_format"] == {"type": "json_object"}
    assert "response_format" not in client._client.calls[1]


def test_json_mode_has_its_own_cache_key(tmp_path):
    client = make_client(["plain", "{}"], tmp_path)
    plain = client.chat_with_info(MESSAGES)[1]["cache_key"]
    json_key = client.chat_with_info(MESSAGES, json_mode=True)[1]["cache_key"]
    assert plain != json_key
