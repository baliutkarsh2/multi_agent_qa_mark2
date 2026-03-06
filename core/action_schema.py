
"""Shared action schemas for single-step LLM planning."""
from __future__ import annotations
from typing import Literal, Optional, TypedDict, Union

class LaunchAppAction(TypedDict):
    step_id: str
    action: Literal["launch_app"]
    package: str
    rationale: str

class TapAction(TypedDict, total=False):
    step_id: str
    action: Literal["tap"]
    resource_id: Optional[str]
    text: Optional[str]
    order: Optional[int]
    rationale: str

class TypeAction(TypedDict, total=False):
    step_id: str
    action: Literal["type"]
    text: str
    resource_id: Optional[str]
    input_text: Optional[str]
    order: Optional[int]
    rationale: str

class VerifyAction(TypedDict, total=False):
    step_id: str
    action: Literal["verify"]
    resource_id: Optional[str]
    text: Optional[str]
    rationale: str

class ScrollAction(TypedDict):
    step_id: str
    action: Literal["scroll"]
    direction: Literal["up", "down"]
    until_resource_id: Optional[str]
    until_text: Optional[str]
    rationale: str

class WaitAction(TypedDict):
    step_id: str
    action: Literal["wait"]
    duration: float
    rationale: str

class PressKeyAction(TypedDict):
    step_id: str
    action: Literal["press_key"]
    key: Literal["home", "back", "recents", "enter"]
    rationale: str

NextAction = Union[LaunchAppAction, TapAction, TypeAction, VerifyAction, ScrollAction, WaitAction, PressKeyAction] 