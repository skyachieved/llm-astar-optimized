import hashlib
import json
import os
import threading
from pathlib import Path


def cache_key(payload):
    """sha256 of the canonical JSON encoding of `payload` (everything that determines the response)."""
    blob = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


class DiskCache:
    """One JSON file per key at `root/<key[:2]>/<key>.json`. Writes are atomic, so threads and processes can share it."""

    def __init__(self, root=".cache/llm"):
        self.root = Path(root)

    def path(self, key):
        return self.root / key[:2] / f"{key}.json"

    def get(self, key):
        try:
            with open(self.path(key), encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return None

    def put(self, key, record):
        path = self.path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_name(f"{path.name}.{os.getpid()}.{threading.get_ident()}.tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(record, f, ensure_ascii=False, indent=1)
        os.replace(tmp, path)
