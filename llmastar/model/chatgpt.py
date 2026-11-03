import os
import threading
import time

from .cache import DiskCache, cache_key

DEFAULT_BASE_URL = "https://api.openai.com/v1"


def resolve_api_key(api_key=None):
    """The key to use: `api_key` if given, else `openai.api_key`, else OPENAI_API_KEY; None if there is none."""
    if api_key:
        return api_key
    try:
        import openai
        module_key = getattr(openai, "api_key", None)
    except ImportError:
        module_key = None
    return module_key or os.environ.get("OPENAI_API_KEY") or None


# This class talks to any OpenAI-compatible Chat Completions endpoint (OpenAI, a local vLLM server, ...)
class ChatGPT:
    """Chat client with an on-disk response cache.

    The API key comes from `api_key`, else `openai.api_key` (as the original repository set it), else the
    OPENAI_API_KEY environment variable; any dummy value works for vLLM. The key is never logged or cached.
    The endpoint comes from `base_url`, else OPENAI_BASE_URL, else OpenAI. Every response is cached under `cache_dir`, keyed by model, base URL,
    messages and sampling settings, so reruns never repeat a request. No stop sequences are sent, so
    multi-line CoT / RePE answers are returned whole.
    """

    def __init__(self, model="gpt-4o-mini", base_url=None, temperature=0.0, max_tokens=2048, top_p=1.0,
                 seed=None, cache_dir=".cache/llm", timeout=600.0, max_retries=5, api_key=None):
        self.model = model
        self._api_key = api_key
        self.base_url = (base_url or os.environ.get("OPENAI_BASE_URL") or DEFAULT_BASE_URL).rstrip("/")
        self.sampling = {"temperature": temperature, "max_tokens": max_tokens, "top_p": top_p, "seed": seed}
        self.cache = DiskCache(cache_dir) if cache_dir else None
        self.timeout = timeout
        self.max_retries = max_retries
        self._client = None
        self._lock = threading.Lock()

    def _get_client(self):
        # Created on the first cache miss, so fully cached runs need neither a key nor a server.
        with self._lock:
            if self._client is None:
                from openai import OpenAI
                api_key = resolve_api_key(self._api_key)
                if not api_key:
                    raise RuntimeError("No API key: pass api_key, set openai.api_key or set OPENAI_API_KEY "
                                       "(any dummy value works for a local vLLM server).")
                self._client = OpenAI(api_key=api_key, base_url=self.base_url,
                                      timeout=self.timeout, max_retries=self.max_retries)
            return self._client

    def chat_with_info(self, messages, **overrides):
        """Return (content, info); info has the cache key, whether it was a cache hit, finish reason and usage."""
        sampling = {**self.sampling, **overrides}
        request = {"model": self.model, "base_url": self.base_url, "messages": messages, "sampling": sampling}
        key = cache_key(request)
        record = self.cache.get(key) if self.cache is not None else None
        cached = record is not None
        if record is None:
            start = time.time()
            completion = self._get_client().chat.completions.create(
                model=self.model, messages=messages, **{k: v for k, v in sampling.items() if v is not None})
            choice = completion.choices[0]
            record = {
                "request": request,
                "response": {
                    "content": choice.message.content or "",
                    "finish_reason": choice.finish_reason,
                    "usage": completion.usage.model_dump() if completion.usage else None,
                    "latency": round(time.time() - start, 3),
                },
                "created": time.strftime("%Y-%m-%dT%H:%M:%S"),
            }
            if self.cache is not None:
                self.cache.put(key, record)
        response = record["response"]
        info = {"cache_key": key, "cached": cached, "finish_reason": response.get("finish_reason"),
                "usage": response.get("usage")}
        return response["content"], info

    def chat(self, messages, **overrides):
        return self.chat_with_info(messages, **overrides)[0]

    def ask(self, prompt, **overrides):
        """Single-turn helper: send `prompt` as one user message."""
        return self.chat([{"role": "user", "content": prompt}], **overrides)
