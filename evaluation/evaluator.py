"""
EpisodeEvaluator – aggregates step-level metrics into episode-level report.
"""

from __future__ import annotations

from typing import List, Dict, Any
from pydantic import BaseModel
from .metrics import success_rate, avg_duration, verification_success_rate


class EpisodeScore(BaseModel):
    success_rate: float
    avg_duration: float
    verified_steps: int
    total_steps: int
    verification_success_rate: float


class EpisodeEvaluator:
    def evaluate(self, exec_reports: List[Dict[str, Any]], verify_reports: List[Dict[str, Any]]) -> EpisodeScore:
        return EpisodeScore(
            success_rate=success_rate(exec_reports),
            avg_duration=avg_duration(exec_reports),
            verified_steps=len(verify_reports),
            total_steps=len(exec_reports),
            verification_success_rate=verification_success_rate(verify_reports)
        ) 