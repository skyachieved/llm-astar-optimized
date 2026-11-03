import base64
import copy
import hashlib
import os
import random
import re
import threading
import time

from .cache import DiskCache, cache_key

DEFAULT_BASE_URL = "https://api.openai.com/v1"
RETRY_STATUS = {408, 409, 429}  # plus every 5xx
PARAM_STATUS = {400, 422}  # where an endpoint reports a parameter it does not accept


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


def _status(error):
    status = getattr(error, "status_code", None)
    return status if isinstance(status, int) else None


def _is_transient(error):
    """Timeouts, dropped connections, rate limits and server errors: worth another try."""
    try:
        import openai
        api_transient = (openai.APITimeoutError, openai.APIConnectionError)
    except (ImportError, AttributeError):
        api_transient = ()
    if isinstance(error, (TimeoutError, ConnectionError) + api_transient):
        return True
    status = _status(error)
    return status is not None and (status in RETRY_STATUS or status >= 500)


def _rejected_param(error, sent):
    """The name of a sent sampling parameter that the endpoint rejected, or None."""
    if _status(error) not in PARAM_STATUS:
        return None
    param = getattr(error, "param", None)
    if param in sent:
        return param
    message = str(getattr(error, "message", "") or error)
    for name in sent:
        if re.search(rf"\b{re.escape(name)}\b", message) and \
                re.search(r"unsupported|not supported|unrecognized|unknown|invalid|not allowed|does not support",
                          message, re.I):
            return name
    return None


def image_part(png_bytes, detail=None):
    """A chat message part carrying a PNG image, in the OpenAI format that vLLM also accepts."""
    url = "data:image/png;base64," + base64.b64encode(png_bytes).decode("ascii")
    part = {"type": "image_url", "image_url": {"url": url}}
    if detail:
        part["image_url"]["detail"] = detail
    return part


def redact_images(messages):
    """A copy of `messages` with every inline image replaced by the sha256 of its data URL. Used for the cache key
    and the cache record, so a key does not depend on how the bytes are encoded and records stay small."""
    redacted = copy.deepcopy(messages)
    for message in redacted:
        content = message.get("content")
        if not isinstance(content, list):
            continue
        for part in content:
            image = part.get("image_url") if isinstance(part, dict) else None
            if isinstance(image, dict) and str(image.get("url", "")).startswith("data:"):
                image["url"] = "sha256:" + hashlib.sha256(image["url"].encode("ascii")).hexdigest()
    return redacted


def _describe(error):
    status = _status(error)
    message = str(getattr(error, "message", "") or error).replace("\n", " ")
    return f"{type(error).__name__}{f' {status}' if status else ''}: {message}"[:500]


# This class talks to any OpenAI-compatible Chat Completions endpoint (OpenAI, a local vLLM server, ...)
class ChatGPT:
    """Chat client with an on-disk response cache.

    The API key comes from `api_key`, else `openai.api_key` (as the original repository set it), else the
    OPENAI_API_KEY environment variable; any dummy value works for vLLM. The key is never logged or cached.
    The endpoint comes from `base_url`, else OPENAI_BASE_URL, else OpenAI. Every response is cached under
    `cache_dir`, keyed by model, base URL, messages and sampling settings, so reruns never repeat a request.

    Failures never raise. Each call has a `timeout` (60 s). Timeouts, dropped connections, 408 / 409 / 429 and 5xx
    are retried up to `max_retries` (3) times with exponential backoff. If the endpoint rejects a sampling
    parameter (e.g. a model without `temperature`), that parameter is dropped and the request is sent once more.
    Any other error (401, 404, other 4xx, no key) is not retried. A failed call returns "" with `info["error"]` set,
    and is not cached, so a rerun tries again.

    Messages may contain images (`image_part`); the cache key and the cache record hold only their sha256.
    `json_mode=True` sends `response_format={"type": "json_object"}`, dropped like any rejected parameter.

    Sampling: no stop sequence by default, so multi-line CoT / RePE answers are returned whole; `stop=["\\n"]` with
    `max_tokens=100` is the original repository's setting. `stop` enters the cache key only when it is set, so
    caches written before it existed stay valid.
    """

    def __init__(self, model="gpt-4o-mini", base_url=None, temperature=0.0, max_tokens=2048, top_p=1.0,
                 seed=None, cache_dir=".cache/llm", timeout=60.0, max_retries=3, api_key=None, stop=None):
        self.model = model
        self._api_key = api_key
        self.base_url = (base_url or os.environ.get("OPENAI_BASE_URL") or DEFAULT_BASE_URL).rstrip("/")
        self.sampling = {"temperature": temperature, "max_tokens": max_tokens, "top_p": top_p, "seed": seed}
        if stop is not None:
            self.sampling["stop"] = stop
        self.cache = DiskCache(cache_dir) if cache_dir else None
        self.timeout = timeout
        self.max_retries = max_retries
        self._client = None
        self._lock = threading.Lock()
        self._sleep = time.sleep  # replaced in tests

    def _get_client(self):
        # Created on the first cache miss, so fully cached runs need neither a key nor a server.
        with self._lock:
            if self._client is None:
                from openai import OpenAI
                api_key = resolve_api_key(self._api_key)
                if not api_key:
                    raise RuntimeError("No API key: pass api_key, set openai.api_key or set OPENAI_API_KEY "
                                       "(any dummy value works for a local vLLM server).")
                # Retries are ours (see the class docstring), so the SDK's own are off.
                self._client = OpenAI(api_key=api_key, base_url=self.base_url, timeout=self.timeout, max_retries=0)
            return self._client

    def _create(self, messages, sampling):
        """One request with the retry policy. Returns (completion, None, attempts, dropped) or (None, error, ...)."""
        params = {k: v for k, v in sampling.items() if v is not None}
        attempts, retries, dropped = 0, 0, []
        while True:
            attempts += 1
            try:
                completion = self._get_client().chat.completions.create(model=self.model, messages=messages, **params)
                return completion, None, attempts, dropped
            except Exception as error:  # noqa: BLE001 - every failure becomes a returned error
                param = None if dropped else _rejected_param(error, params)
                if param is not None:
                    params.pop(param)
                    dropped.append(param)
                    continue
                if _is_transient(error) and retries < self.max_retries:
                    self._sleep(2 ** retries + random.uniform(0, 0.5))
                    retries += 1
                    continue
                return None, _describe(error), attempts, dropped

    def chat_with_info(self, messages, json_mode=False, **overrides):
        """Return (content, info). info has the cache key, whether it was a cache hit, finish reason, usage, the
        number of attempts, any dropped parameters and, on failure, `error` (content is then "").

        `messages` may carry images (see `image_part`); a model without image input fails the call, which the caller
        treats as an abstention. `json_mode=True` asks for a JSON object (`response_format`); an endpoint that rejects
        it gets the request again without it, so callers must still parse leniently."""
        sampling = {**self.sampling, **overrides}
        if json_mode:
            sampling["response_format"] = {"type": "json_object"}
        request = {"model": self.model, "base_url": self.base_url, "messages": redact_images(messages),
                   "sampling": sampling}
        key = cache_key(request)
        record = self.cache.get(key) if self.cache is not None else None
        cached = record is not None
        attempts = 0
        if record is None:
            start = time.time()
            completion, error, attempts, dropped = self._create(messages, sampling)
            if error is not None:
                return "", {"cache_key": key, "cached": False, "finish_reason": None, "usage": None,
                            "attempts": attempts, "dropped_params": dropped, "error": error}
            choice = completion.choices[0]
            record = {
                "request": request,
                "response": {
                    "content": choice.message.content or "",
                    "finish_reason": choice.finish_reason,
                    "usage": completion.usage.model_dump() if completion.usage else None,
                    "latency": round(time.time() - start, 3),
                    **({"dropped_params": dropped} if dropped else {}),
                },
                "created": time.strftime("%Y-%m-%dT%H:%M:%S"),
            }
            if self.cache is not None:
                self.cache.put(key, record)
        response = record["response"]
        info = {"cache_key": key, "cached": cached, "finish_reason": response.get("finish_reason"),
                "usage": response.get("usage"), "attempts": attempts,
                "dropped_params": response.get("dropped_params", [])}
        return response["content"], info

    def chat(self, messages, **overrides):
        return self.chat_with_info(messages, **overrides)[0]

    def ask(self, prompt, **overrides):
        """Single-turn helper: send `prompt` as one user message."""
        return self.chat([{"role": "user", "content": prompt}], **overrides)
