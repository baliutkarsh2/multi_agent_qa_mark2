"""
Standard metrics used by the evaluation framework.
"""

from __future__ import annotations

from typing import List, Dict, Any
from statistics import mean


def success_rate(exec_reports: List[Dict[str, Any]]) -> float:
    """Calculate success rate from execution reports."""
    if not exec_reports:
        return 0.0
    
    successes = []
    for r in exec_reports:
        report = r.get("report", {})
        # Check if success field exists, default to False if not
        success = report.get("success", False)
        successes.append(success)
    
    return sum(successes) / len(successes)


def avg_duration(exec_reports: List[Dict[str, Any]]) -> float:
    """Calculate average duration from execution reports."""
    if not exec_reports:
        return 0.0
    
    durations = []
    for r in exec_reports:
        report = r.get("report", {})
        # Check if duration field exists, skip if not
        if "duration" in report:
            durations.append(report["duration"])
    
    return mean(durations) if durations else 0.0


def verification_success_rate(verify_reports: List[Dict[str, Any]]) -> float:
    """Calculate verification success rate from verification reports."""
    if not verify_reports:
        return 0.0
    
    successful_verifications = sum(1 for v in verify_reports if v.get("verified", False))
    return successful_verifications / len(verify_reports) 