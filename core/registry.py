"""
Simple agent registry so other components can discover agents by name.
"""

from __future__ import annotations

from typing import Dict, Type, Callable

_REGISTRY: Dict[str, Callable] = {}


def register_agent(name: str) -> Callable:
    def wrapper(cls: Type) -> Type:
        _REGISTRY[name] = cls
        return cls

    return wrapper


def get_agent(name: str):
    return _REGISTRY[name] 