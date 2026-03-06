"""
memory.py
Two complementary memory stores:
1. EpisodicMemory  –  short-term per-episode retrieval
2. NarrativeMemory –  long-term cross-episode reflection
"""

from __future__ import annotations

import json
import pickle
import uuid
from pathlib import Path
from typing import List, Dict, Any
from core.config import MEMORY_STORE_PATH

MEM_DIR = Path(MEMORY_STORE_PATH)
MEM_DIR.mkdir(exist_ok=True)


class EpisodicMemory:
    def __init__(self) -> None:
        self._store: Dict[str, Dict[str, Any]] = {}

    # -------------------------------------------------- #
    def store(self, key: str, value: Any, tags: List[str] | None = None) -> None:
        self._store[key] = {"value": value, "tags": tags or []}

    def retrieve(self, key: str) -> Any | None:
        """Retrieves an item by its exact key."""
        if key in self._store:
            return self._store[key]["value"]
        return None

    # -------------------------------------------------- #
    def retrieve_similar(self, query: str, k: int = 3) -> List[Any]:
        """
        Naïve similarity based on substring overlap.
        """
        scored = [
            (key, data)
            for key, data in self._store.items()
            if all(tok.lower() in query.lower() for tok in data["tags"])
        ]
        return [d["value"] for key, d in scored][:k]


class NarrativeMemory:
    """
    Disk-backed, multi-episode memory for reflection and analytics.
    """

    def __init__(self) -> None:
        self.file = MEM_DIR / "narrative.pkl"
        if self.file.exists():
            with self.file.open("rb") as f:
                self._store: Dict[str, Any] = pickle.load(f)
        else:
            self._store = {}

    # -------------------------------------------------- #
    def store(self, key: str, value: Any, tags: List[str] | None = None) -> None:
        self._store[key] = {"value": value, "tags": tags or []}
        with self.file.open("wb") as f:
            pickle.dump(self._store, f)

    # -------------------------------------------------- #
    def dump_json(self, path: Path) -> None:
        with path.open("w") as f:
            json.dump(self._store, f, indent=2) 