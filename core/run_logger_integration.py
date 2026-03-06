"""
Run Logger Integration Helper

Simple functions to integrate run logging into existing automation runners
and scripts without major code changes.
"""

import uuid
import time
from contextlib import contextmanager
from typing import Optional, Dict, Any
from core.run_logger import RunLogger, set_run_logger, get_run_logger
from pathlib import Path

def start_run_logging(user_goal: str, run_id: Optional[str] = None, logs_dir: str = "logs") -> RunLogger:
    """
    Start run logging for an automation session.
    
    Args:
        user_goal: The user's automation goal
        run_id: Optional custom run ID (auto-generated if not provided)
        logs_dir: Directory to store logs
        
    Returns:
        RunLogger instance
    """
    if run_id is None:
        run_id = str(uuid.uuid4())[:8]
    
    run_logger = RunLogger(run_id, user_goal, logs_dir)
    set_run_logger(run_logger)
    
    return run_logger

def stop_run_logging() -> Optional[str]:
    """
    Stop run logging and save the final log file.
    
    Returns:
        Path to the saved log file, or None if no logger was active
    """
    run_logger = get_run_logger()
    if run_logger:
        log_file = run_logger.save_run_log()
        run_logger.cleanup()
        set_run_logger(None)
        return log_file
    return None

@contextmanager
def run_logging_session(user_goal: str, run_id: Optional[str] = None, logs_dir: str = "logs"):
    """
    Context manager for automatic run logging.
    
    Usage:
        with run_logging_session("Launch weather app") as run_logger:
            # Your automation code here
            run_logger.log_event("step_completed", "AGENT", {"step": "launch_app"})
    
    Args:
        user_goal: The user's automation goal
        run_id: Optional custom run ID
        logs_dir: Directory to store logs
        
    Yields:
        RunLogger instance
    """
    run_logger = start_run_logging(user_goal, run_id, logs_dir)
    try:
        yield run_logger
    finally:
        stop_run_logging()

def quick_log_event(event_type: str, agent: str, data: Dict[str, Any], 
                   episode_id: Optional[str] = None, step_id: Optional[str] = None,
                   action: Optional[str] = None, severity: str = "INFO"):
    """
    Quick logging function that works whether run logging is active or not.
    
    Args:
        event_type: Type of event (e.g., "step_completed", "error")
        agent: Name of the agent or component
        data: Event data dictionary
        episode_id: Optional episode ID
        step_id: Optional step ID
        action: Optional action name
        severity: Log severity level
    """
    run_logger = get_run_logger()
    if run_logger:
        run_logger.log_event(event_type, agent, data, episode_id, step_id, action, severity)
    else:
        # Fallback to regular logging
        from core.logging_config import get_logger
        log = get_logger("QUICK-LOG")
        log.info(f"[{agent}] {event_type}: {data}")

def get_run_summary() -> Optional[Dict[str, Any]]:
    """Get a summary of the current run."""
    run_logger = get_run_logger()
    if run_logger:
        return run_logger.get_run_summary()
    return None

def get_screenshots_dir() -> Optional[Path]:
    """Get the current run's screenshots directory."""
    run_logger = get_run_logger()
    if run_logger:
        return run_logger.get_screenshots_dir()
    return None

def log_automation_step(episode_id: str, step: Dict[str, Any], result: Dict[str, Any], ui_xml: str):
    """
    Log an automation step execution.
    
    Args:
        episode_id: Episode identifier
        step: Step definition
        result: Step execution result
        ui_xml: UI state after step execution
    """
    run_logger = get_run_logger()
    if run_logger:
        run_logger.log_step_execution(episode_id, step, result, ui_xml)

def log_verification(episode_id: str, step: Dict[str, Any], result: Dict[str, Any], 
                    ui_xml: str, screenshot_path: Optional[str] = None):
    """
    Log a verification report.
    
    Args:
        episode_id: Episode identifier
        step: Step definition
        result: Verification result
        ui_xml: UI state during verification
        screenshot_path: Optional screenshot path
    """
    run_logger = get_run_logger()
    if run_logger:
        run_logger.log_verification_report(episode_id, step, result, ui_xml, screenshot_path)

def log_error(agent: str, error: str, episode_id: Optional[str] = None, 
              step_id: Optional[str] = None, context: Optional[Dict[str, Any]] = None):
    """
    Log an error during automation.
    
    Args:
        agent: Agent or component name
        error: Error description
        episode_id: Optional episode identifier
        step_id: Optional step identifier
        context: Optional error context
    """
    run_logger = get_run_logger()
    if run_logger:
        run_logger.log_error(agent, error, episode_id, step_id, context)

# Example integration for existing runners
def integrate_with_existing_runner():
    """
    Example of how to integrate run logging with existing automation code.
    """
    print("🔧 **Run Logger Integration Example**")
    
    # Method 1: Context manager (recommended)
    with run_logging_session("Test automation integration") as run_logger:
        print(f"Run logging started for: {run_logger.user_goal}")
        
        # Your existing automation code here
        episode_id = "episode_001"
        run_logger.log_episode_start(episode_id, "Test episode")
        
        # Simulate some steps
        step = {"action": "launch_app", "package": "com.test", "step_id": "step_001"}
        result = {"success": True, "duration": 1.5}
        ui_xml = "<UI>Test app launched</UI>"
        
        run_logger.log_step_execution(episode_id, step, result, ui_xml)
        
        # Simulate verification
        verification_result = {"verified": True, "confidence": 0.9, "reason": "App visible"}
        run_logger.log_verification_report(episode_id, step, verification_result, ui_xml)
        
        run_logger.log_episode_end(episode_id, "completed", "Test completed successfully")
        
        print("✅ Automation completed with full logging")
    
    print("✅ Run log automatically saved and cleaned up")
    
    # Method 2: Manual start/stop
    print("\n🔄 **Manual Integration Example**")
    
    run_logger = start_run_logging("Manual integration test")
    
    try:
        # Your automation code here
        quick_log_event("manual_step", "MANUAL", {"action": "test_action"})
        log_automation_step("episode_002", {"action": "test"}, {"success": True}, "<UI>Test</UI>")
        
    finally:
        log_file = stop_run_logging()
        print(f"✅ Manual run log saved to: {log_file}")

if __name__ == "__main__":
    integrate_with_existing_runner()
