import hashlib
import json

from llmastar.pather.llm_a_star.prompt import gpt_prompt, llama_prompt, llama_template_to_messages
from .base import WaypointResult, parse_waypoints


class PromptWaypointGenerator:
    """The paper's waypoint step: one few-shot / CoT / RePE prompt, one LLM call, parse the last [[x, y], ...] list.

    `client` is anything with `chat(messages) -> str` (ChatGPT for OpenAI-compatible endpoints such as vLLM,
    Llama3 for a local HF pipeline). prompt_set "llama" sends the paper's Llama-3 few-shot dialogue as chat
    turns; "gpt" sends the paper's GPT completion-style prompt as a single user message.
    """

    def __init__(self, client, prompt="standard", prompt_set="llama"):
        assert prompt in ("standard", "cot", "repe"), "prompt must be standard, cot or repe"
        assert prompt_set in ("llama", "gpt"), "prompt_set must be llama or gpt"
        self.client, self.prompt, self.prompt_set = client, prompt, prompt_set
        self.name = f"prompt-{prompt}"

    def messages(self, query):
        fields = {"start": list(query["start"]), "goal": list(query["goal"]),
                  "horizontal_barriers": query["horizontal_barriers"], "vertical_barriers": query["vertical_barriers"]}
        if self.prompt_set == "llama":
            return llama_template_to_messages(llama_prompt[self.prompt], **fields)
        return [{"role": "user", "content": gpt_prompt[self.prompt].format(**fields).strip()}]

    def generate(self, query):
        messages = self.messages(query)
        chat_with_info = getattr(self.client, "chat_with_info", None)
        if chat_with_info is not None:
            response, info = chat_with_info(messages)
        else:
            response, info = self.client.chat(messages), {}
        waypoints, parse_ok = parse_waypoints(response)
        raw = {
            "generator": "prompt",
            "prompt": self.prompt,
            "prompt_set": self.prompt_set,
            "messages_sha256": hashlib.sha256(json.dumps(messages, sort_keys=True).encode()).hexdigest(),
            "query_message": messages[-1]["content"],
            "response": response,
            "waypoints": [list(p) for p in waypoints],
            "parse_ok": parse_ok,
            **info,
        }
        return WaypointResult(waypoints, parse_ok, raw)
