"""
A super-lightweight in-process pub/sub message bus.
"""

from __future__ import annotations

import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Any

Subscriber = Callable[["Message"], None]
_bus: Dict[str, List[Subscriber]] = defaultdict(list)


@dataclass
class Message:
    sender: str
    channel: str
    payload: Dict[str, Any]
    id: str = field(default_factory=lambda: uuid.uuid4().hex)


# -------------------------------------------------- #
def publish(msg: Message) -> None:
    for cb in _bus[msg.channel]:
        cb(msg)


# -------------------------------------------------- #
def subscribe(channel: str, callback: Subscriber) -> None:
    _bus[channel].append(callback) 