"""
EpisodeContext   –  per-test-case metadata container.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass


@dataclass
class EpisodeContext:
    id: str = uuid.uuid4().hex
    user_goal: str | None = None 