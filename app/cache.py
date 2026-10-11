"""简单 JSON 文件缓存：按 (service, key) 哈希落盘，带 TTL。"""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any

from .config import CACHE_DIR, CACHE_TTL


def _cache_path(service: str, key: str) -> Path:
    digest = hashlib.sha256(key.encode()).hexdigest()[:16]
    return CACHE_DIR / f"{service}_{digest}.json"


def cache_get(service: str, key: str) -> Any | None:
    path = _cache_path(service, key)
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return None
    if time.time() - payload.get("ts", 0) > CACHE_TTL:
        return None
    return payload.get("data")


def cache_set(service: str, key: str, data: Any) -> None:
    path = _cache_path(service, key)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps({"ts": time.time(), "data": data}, ensure_ascii=False))
    tmp.replace(path)
