"""
Run Logger for Multi-Agent QA System

Captures all logs, verification reports, screenshots, and agent activities
during a single automation run and saves them to a timestamped JSON file.
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from core.logging_config import get_logger

log = get_logger("RUN-LOGGER")

@dataclass
class RunEvent:
    """Represents a single event during the automation run."""
    timestamp: float
    event_type: str
    agent: str
    episode_id: Optional[str]
    step_id: Optional[str]
    action: Optional[str]
    data: Dict[str, Any]
    severity: str = "INFO"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

@dataclass
class RunMetadata:
    """Metadata about the automation run."""
    run_id: str
    start_time: float
    end_time: Optional[float]
    user_goal: str
    total_episodes: int
    successful_episodes: int
    failed_episodes: int
    total_steps: int
    successful_steps: int
    failed_steps: int
    verification_success_rate: float
    average_confidence: float
    system_info: Dict[str, Any]

class RunLogger:
    """Centralized logger for capturing all QA automation activities."""
    
    def __init__(self, run_id: str, user_goal: str, logs_dir: str = "logs"):
        self.run_id = run_id
        self.user_goal = user_goal
        self.logs_dir = Path(logs_dir)
        self.run_dir = self.logs_dir / f"run_{run_id}"
        self.screenshots_dir = self.run_dir / "screenshots"
        
        # Create directories
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self.screenshots_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize data structures
        self.events = []
        self.episodes = {}
        self.verification_reports = []
        self.screenshots = []
        self.errors = []
        self.start_time = time.time()
        self.end_time = None
        
        # Capture system information
        self.system_info = self._capture_system_info()
        
        # Log initialization
        log.info(f"Run logger initialized for run {run_id}")
        self.log_event("run_start", "SYSTEM", {
            "user_goal": user_goal,
            "run_id": run_id,
            "start_time": datetime.fromtimestamp(self.start_time).isoformat()
        })
    
    def get_screenshots_dir(self) -> Path:
        """Get the run-specific screenshots directory path."""
        return self.screenshots_dir

    def _capture_system_info(self) -> Dict[str, Any]:
        """Capture system information at run start."""
        try:
            import platform
            import sys
            import os
            
            return {
                "platform": platform.platform(),
                "python_version": sys.version,
                "python_executable": sys.executable,
                "working_directory": os.getcwd(),
                "environment_variables": {
                    k: v for k, v in os.environ.items() 
                    if not any(secret in k.lower() for secret in ['key', 'password', 'secret', 'token'])
                }
            }
        except Exception as e:
            log.warning(f"Failed to capture system info: {e}")
            return {"error": str(e)}
    
    def _log_run_start(self):
        """Log the start of the automation run."""
        self.log_event(
            event_type="run_start",
            agent="SYSTEM",
            data={
                "user_goal": self.user_goal,
                "run_id": self.run_id,
                "start_time": datetime.fromtimestamp(self.start_time).isoformat()
            }
        )
    
    def log_event(self, event_type: str, agent: str, data: Dict[str, Any], 
                  episode_id: Optional[str] = None, step_id: Optional[str] = None, 
                  action: Optional[str] = None, severity: str = "INFO"):
        """Log a single event during the run."""
        event = RunEvent(
            timestamp=time.time(),
            event_type=event_type,
            agent=agent,
            episode_id=episode_id,
            step_id=step_id,
            action=action,
            data=data,
            severity=severity
        )
        
        self.events.append(event)
        
        # Log to console as well
        log_level = getattr(log, severity.lower(), log.info)
        log_level(f"[{agent}] {event_type}: {data}")
    
    def log_episode_start(self, episode_id: str, user_goal: str):
        """Log the start of an episode."""
        self.episodes[episode_id] = {
            "episode_id": episode_id,
            "user_goal": user_goal,
            "start_time": time.time(),
            "end_time": None,
            "steps": [],
            "verification_reports": [],
            "screenshots": [],
            "status": "running",
            "total_steps": 0,
            "successful_steps": 0,
            "failed_steps": 0
        }
        
        self.log_event(
            event_type="episode_start",
            agent="LLM-PLANNER",
            episode_id=episode_id,
            data={"user_goal": user_goal}
        )
    
    def log_episode_end(self, episode_id: str, status: str, reason: str = None):
        """Log the end of an episode."""
        if episode_id in self.episodes:
            self.episodes[episode_id]["end_time"] = time.time()
            self.episodes[episode_id]["status"] = status
            self.episodes[episode_id]["end_reason"] = reason
            
            # Calculate episode metrics
            episode = self.episodes[episode_id]
            duration = episode["end_time"] - episode["start_time"]
            success_rate = episode["successful_steps"] / max(episode["total_steps"], 1)
            
            self.log_event(
                event_type="episode_end",
                agent="LLM-PLANNER",
                episode_id=episode_id,
                data={
                    "status": status,
                    "reason": reason,
                    "duration": duration,
                    "total_steps": episode["total_steps"],
                    "successful_steps": episode["successful_steps"],
                    "failed_steps": episode["failed_steps"],
                    "success_rate": success_rate
                }
            )
    
    def log_step_execution(self, episode_id: str, step: Dict[str, Any], 
                          result: Dict[str, Any], ui_xml: str):
        """Log a step execution."""
        step_data = {
            "step": step,
            "result": result,
            "ui_xml": ui_xml,
            "timestamp": time.time()
        }
        
        if episode_id in self.episodes:
            self.episodes[episode_id]["steps"].append(step_data)
            self.episodes[episode_id]["total_steps"] += 1
            
            if result.get("success", False):
                self.episodes[episode_id]["successful_steps"] += 1
            else:
                self.episodes[episode_id]["failed_steps"] += 1
        
        self.log_event(
            event_type="step_execution",
            agent="LLM-EXECUTOR",
            episode_id=episode_id,
            step_id=step.get("step_id"),
            action=step.get("action"),
            data=step_data
        )
    
    def log_verification_report(self, episode_id: str, step: Dict[str, Any], 
                               result: Dict[str, Any], ui_xml: str, screenshot_path: Optional[str]):
        """Log a verification report."""
        verification_data = {
            "step": step,
            "result": result,
            "ui_xml": ui_xml,
            "screenshot_path": screenshot_path,
            "timestamp": time.time()
        }
        
        self.verification_reports.append(verification_data)
        
        if episode_id in self.episodes:
            self.episodes[episode_id]["verification_reports"].append(verification_data)
        
        self.log_event(
            event_type="verification_report",
            agent="LLM-VERIFIER",
            episode_id=episode_id,
            step_id=step.get("step_id"),
            action=step.get("action"),
            data={
                "verified": result.get("verified", False),
                "confidence": result.get("confidence", 0.0),
                "reason": result.get("reason", "No reason provided"),
                "screenshot_path": screenshot_path
            }
        )
    
    def log_screenshot(self, episode_id: str, step_id: str, screenshot_path: str, 
                       description: str = ""):
        """Log a screenshot capture."""
        screenshot_data = {
            "episode_id": episode_id,
            "step_id": step_id,
            "screenshot_path": screenshot_path,
            "description": description,
            "timestamp": time.time()
        }
        
        self.screenshots.append(screenshot_data)
        
        if episode_id in self.episodes:
            self.episodes[episode_id]["screenshots"].append(screenshot_data)
        
        self.log_event(
            event_type="screenshot_captured",
            agent="LLM-VERIFIER",
            episode_id=episode_id,
            step_id=step_id,
            data=screenshot_data
        )
    
    def log_error(self, agent: str, error: str, episode_id: Optional[str] = None, 
                  step_id: Optional[str] = None, context: Dict[str, Any] = None):
        """Log an error during execution."""
        error_data = {
            "error": error,
            "context": context or {},
            "timestamp": time.time()
        }
        
        self.errors.append(error_data)
        
        self.log_event(
            event_type="error",
            agent=agent,
            episode_id=episode_id,
            step_id=step_id,
            data=error_data,
            severity="ERROR"
        )
    
    def log_critical_failure(self, episode_id: str, step: Dict[str, Any], 
                            failure_result: Dict[str, Any]):
        """Log a critical failure that requires manual intervention."""
        self.log_event(
            event_type="critical_failure",
            agent="LLM-VERIFIER",
            episode_id=episode_id,
            step_id=step.get("step_id"),
            action=step.get("action"),
            data={
                "failure_result": failure_result,
                "requires_manual_intervention": True
            },
            severity="CRITICAL"
        )
    
    def get_run_summary(self) -> Dict[str, Any]:
        """Generate a summary of the run."""
        end_time = time.time()
        duration = end_time - self.start_time
        
        # Calculate overall metrics
        total_episodes = len(self.episodes)
        successful_episodes = sum(1 for ep in self.episodes.values() if ep["status"] == "completed")
        failed_episodes = total_episodes - successful_episodes
        
        total_steps = sum(ep["total_steps"] for ep in self.episodes.values())
        successful_steps = sum(ep["successful_steps"] for ep in self.episodes.values())
        failed_steps = sum(ep["failed_steps"] for ep in self.episodes.values())
        
        # Calculate verification success rate
        total_verifications = len(self.verification_reports)
        successful_verifications = sum(1 for vr in self.verification_reports if vr["result"].get("verified", False))
        verification_success_rate = successful_verifications / max(total_verifications, 1)
        
        # Calculate average confidence
        confidences = [vr["result"].get("confidence", 0.0) for vr in self.verification_reports]
        average_confidence = sum(confidences) / max(len(confidences), 1)
        
        return {
            "run_id": self.run_id,
            "user_goal": self.user_goal,
            "start_time": self.start_time,
            "end_time": end_time,
            "duration": duration,
            "total_episodes": total_episodes,
            "successful_episodes": successful_episodes,
            "failed_episodes": failed_episodes,
            "total_steps": total_steps,
            "successful_steps": successful_steps,
            "failed_steps": failed_steps,
            "verification_success_rate": verification_success_rate,
            "average_confidence": average_confidence,
            "total_verifications": total_verifications,
            "successful_verifications": successful_verifications,
            "total_screenshots": len(self.screenshots),
            "total_errors": len(self.errors)
        }
    
    def save_run_log(self) -> str:
        """Save the complete run log to a JSON file."""
        try:
            # Generate run summary
            run_summary = self.get_run_summary()
            
            # Prepare complete run data
            run_data = {
                "metadata": run_summary,
                "system_info": self.system_info,
                "events": [event.to_dict() for event in self.events],
                "episodes": self.episodes,
                "verification_reports": self.verification_reports,
                "screenshots": self.screenshots,
                "errors": self.errors
            }
            
            # Save to JSON file
            timestamp = datetime.fromtimestamp(self.start_time).strftime("%Y%m%d_%H%M%S")
            filename = f"run_{self.run_id}_{timestamp}.json"
            filepath = self.run_dir / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(run_data, f, indent=2, default=str, ensure_ascii=False)
            
            log.info(f"Run log saved to: {filepath}")
            return str(filepath)
            
        except Exception as e:
            log.error(f"Failed to save run log: {e}")
            raise
    
    def cleanup(self):
        """Clean up resources and save final log."""
        try:
            self.save_run_log()
            log.info(f"Run logger cleanup completed for run {self.run_id}")
        except Exception as e:
            log.error(f"Failed to cleanup run logger: {e}")

# Global run logger instance
_current_run_logger: Optional[RunLogger] = None

def get_run_logger() -> Optional[RunLogger]:
    """Get the current run logger instance."""
    return _current_run_logger

def set_run_logger(run_logger: RunLogger):
    """Set the current run logger instance."""
    global _current_run_logger
    _current_run_logger = run_logger

def log_run_event(event_type: str, agent: str, data: Dict[str, Any], 
                  episode_id: Optional[str] = None, step_id: Optional[str] = None, 
                  action: Optional[str] = None, severity: str = "INFO"):
    """Convenience function to log events to the current run logger."""
    if _current_run_logger:
        _current_run_logger.log_event(event_type, agent, data, episode_id, step_id, action, severity)
    else:
        # Fallback to regular logging if no run logger is set
        log.info(f"[{agent}] {event_type}: {data}")
