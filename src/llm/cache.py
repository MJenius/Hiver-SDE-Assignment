"""
src/llm/cache.py
Persistent, disk-backed deterministic cache for LLM API calls.
Keyed by SHA-256 of model, prompt, system instruction, temperature, schema, and contextual parameters.
Ensures zero wasted quota and complete experimental reproducibility.
"""

import os
import json
import hashlib
from typing import Dict, Any, Optional

CACHE_DIR = os.path.join("data", "llm_cache")

class DiskLLMCache:
    def __init__(self, cache_dir: str = CACHE_DIR):
        self.cache_dir = cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)

    def _compute_key(self, payload: Dict[str, Any]) -> str:
        serialized = json.dumps(payload, sort_keys=True, default=str)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def get(self, payload: Dict[str, Any]) -> Optional[str]:
        key = self._compute_key(payload)
        path = os.path.join(self.cache_dir, f"{key}.json")
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    entry = json.load(f)
                    return entry.get("response")
            except Exception:
                return None
        return None

    def set(self, payload: Dict[str, Any], response: str):
        key = self._compute_key(payload)
        path = os.path.join(self.cache_dir, f"{key}.json")
        entry = {
            "key": key,
            "payload": payload,
            "response": response
        }
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(entry, f, indent=2)
        except Exception:
            pass
