"""LLM-powered planner agent."""
from __future__ import annotations
import uuid
from typing import Dict, Any, List
from core.message_bus import Message, publish, subscribe
from core.registry import register_agent
from core.memory import EpisodicMemory
from core.episode import EpisodeContext
from core.llm_client import LLMClient
from core.logging_config import get_logger
from core.run_logger import get_run_logger, log_run_event
from env.android_interface import UIState
import os
import time

log = get_logger("LLM-PLANNER")

@register_agent("llm_planner")
class LLMPlannerAgent:
    def __init__(self):
        self.llm = LLMClient()
        self.memory = EpisodicMemory()
        self.max_steps = 20  # Maximum steps per episode
        self.toggle_episodes = set()  # Track episodes that have performed a toggle
        self.toggle_executed = False  # Track if toggle has been executed in current episode
        subscribe("exec-report", self.on_exec_report)
        subscribe("verification-complete", self.on_verification_complete)
        subscribe("critical-failure", self.on_critical_failure)

    def on_exec_report(self, msg: Message):
        # After a step is executed, wait for verification before planning next action
        episode_id = msg.payload["episode_id"]
        ui_state = UIState(msg.payload["ui_snapshot"])
        
        history = self.memory.retrieve(episode_id) or []
        
        # Failsafe for empty history
        if not history:
            log.error(f"History not found for episode {episode_id}. Ending episode.")
            publish(Message("LLM-PLANNER", "episode_done", {"reason": "History lost."}))
            return

        user_goal = history[0].get("user_goal", "No goal found in history.")
        
        # Check if we've reached the maximum number of steps
        if len(history) >= self.max_steps:
            log.info(f"Maximum steps ({self.max_steps}) reached for episode {episode_id}. Ending episode.")
            publish(Message("LLM-PLANNER", "episode_done", {"reason": "Maximum steps reached."}))
            return
        
        # Store the execution report and wait for verification
        # The planner will be triggered again after verification completes
        log.info(f"Execution completed for episode {episode_id}, waiting for verification before planning next action")
        
        # Store execution result in history
        execution_result = {
            "type": "execution",
            "step": msg.payload["report"],
            "ui_state": ui_state.xml,
            "timestamp": time.time()
        }
        history.append(execution_result)
        self.memory.store(episode_id, history, tags=["history"])

    def on_verification_complete(self, msg: Message):
        """Handle verification completion and plan next action."""
        episode_id = msg.payload["episode_id"]
        verification_result = msg.payload["verification_result"]
        
        history = self.memory.retrieve(episode_id) or []
        if not history:
            log.error(f"History not found for episode {episode_id} during verification completion.")
            return
            
        user_goal = history[0].get("user_goal", "No goal found in history.")
        
        # Check if we've reached the maximum number of steps
        if len(history) >= self.max_steps:
            log.info(f"Maximum steps ({self.max_steps}) reached for episode {episode_id}. Ending episode.")
            publish(Message("LLM-PLANNER", "episode_done", {"reason": "Maximum steps reached."}))
            return
        
        # Store verification result
        verification_record = {
            "type": "verification",
            "result": verification_result,
            "timestamp": time.time()
        }
        history.append(verification_record)
        self.memory.store(episode_id, history, tags=["history"])
        
        # Check verification success
        if not verification_result.get("verified", False):
            log.warning(f"Verification failed for episode {episode_id}: {verification_result.get('reason', 'Unknown error')}")
            # Could implement retry logic here
        
        # Now plan the next action based on verified state
        try:
            current_ui_state = UIState(verification_result.get("ui_xml", ""))
        except Exception as e:
            log.warning(f"Failed to create UI state from verification result: {e}")
            # Get fresh UI state
            try:
                from env.android_interface import AndroidDevice
                device = AndroidDevice()  # This should be injected properly
                current_ui_state = UIState(device.get_ui_tree().xml)
            except Exception as e2:
                log.error(f"Failed to get current UI state: {e2}")
                publish(Message("LLM-PLANNER", "episode_done", {"reason": "Failed to get UI state for planning."}))
                return
        
        self.act(user_goal, current_ui_state, EpisodeContext(id=episode_id, user_goal=user_goal))

    def on_critical_failure(self, msg: Message):
        """Handle critical failures that require manual intervention."""
        episode_id = msg.payload["episode_id"]
        step = msg.payload["step"]
        failure_result = msg.payload["failure_result"]
        
        log.error(f"Critical failure detected for episode {episode_id}: {step['action']} - {failure_result.get('reason', 'Unknown error')}")
        
        # Store critical failure in history
        history = self.memory.retrieve(episode_id) or []
        critical_failure_record = {
            "type": "critical_failure",
            "step": step,
            "failure_result": failure_result,
            "timestamp": time.time(),
            "requires_manual_intervention": True
        }
        history.append(critical_failure_record)
        self.memory.store(episode_id, history, tags=["history"])
        
        # End episode due to critical failure
        publish(Message("LLM-PLANNER", "episode_done", {
            "reason": f"Critical failure: {failure_result.get('reason', 'Unknown error')}",
            "failure_type": "verification_failure",
            "requires_manual_intervention": True
        }))
        
        log.info(f"Episode {episode_id} terminated due to critical failure")

    def act(self, user_goal: str, ui_state: UIState, episode: EpisodeContext):
        history = self.memory.retrieve(episode.id) or []
        
        if not history:
            history.append({"user_goal": user_goal})
            # Reset toggle execution flag for new episode
            self.toggle_executed = False
            
            # Log episode start to run logger if available
            run_logger = get_run_logger()
            if run_logger:
                run_logger.log_episode_start(episode.id, user_goal)
            
        log.info(f"Planning next action for goal: {user_goal} (step {len(history)})")
        
        action = self.llm.request_next_action(user_goal, ui_state.xml, history)
        
        if not action or "action" not in action:
            log.warning("LLM did not return a valid action. Ending episode.")
            
            # Log episode end to run logger if available
            run_logger = get_run_logger()
            if run_logger:
                run_logger.log_episode_end(episode.id, "failed", "No further actions from LLM")
            
            publish(Message("LLM-PLANNER", "episode_done", {"reason": "No further actions from LLM."}))
            return
            
        # Check if this is a toggle action and we should end the episode
        if self._is_toggle_action(action, user_goal):
            if self.toggle_executed:
                log.info("Toggle already executed in this episode, ending immediately.")
                
                # Log episode end to run logger if available
                run_logger = get_run_logger()
                if run_logger:
                    run_logger.log_episode_end(episode.id, "completed", "Toggle already executed - stopping")
                
                publish(Message("LLM-PLANNER", "episode_done", {"reason": "Toggle already executed - stopping."}))
                return
                
            log.info("Toggle action detected. Executing toggle ONCE and then STOPPING.")
            # Mark toggle as executed
            self.toggle_executed = True
            # Execute the toggle action first
            history.append(action)
            self.memory.store(episode.id, history, tags=["history"])
            publish(Message("LLM-PLANNER", "plan", {"step": action, "episode_id": episode.id}))
            # End the episode immediately after planning the toggle action
            
            # Log episode end to run logger if available
            run_logger = get_run_logger()
            if run_logger:
                run_logger.log_episode_end(episode.id, "completed", "Toggle action executed. Goal Reached")
            
            publish(Message("LLM-PLANNER", "episode_done", {"reason": "Toggle action executed. Goal Reached."}))
            return
            
        # Check if the action indicates completion
        if self._is_completion_action(action, user_goal):
            log.info("Completion action detected. Ending episode.")
            
            # Log episode end to run logger if available
            run_logger = get_run_logger()
            if run_logger:
                run_logger.log_episode_end(episode.id, "completed", "Goal completed")
            
            publish(Message("LLM-PLANNER", "episode_done", {"reason": "Goal completed."}))
            return
            
        history.append(action)
        self.memory.store(episode.id, history, tags=["history"])
        
        publish(Message("LLM-PLANNER", "plan", {"step": action, "episode_id": episode.id}))

    def _is_completion_action(self, action: Dict[str, Any], goal: str) -> bool:
        """Check if the action indicates the goal has been completed."""
        # Check for verify actions that might indicate completion
        if action.get("action") == "verify":
            rationale = action.get("rationale", "").lower()
            goal_lower = goal.lower()
            
            # Check if the verification is for the final goal
            completion_keywords = ["complete", "finished", "done", "achieved", "success"]
            if any(keyword in rationale for keyword in completion_keywords):
                return True
                
            # Check if the verification is checking for the goal itself
            if any(word in rationale for word in goal_lower.split()):
                return True
        
        # Check for toggle actions (like Wi-Fi switches) - end episode after first toggle
        if action.get("action") == "tap":
            rationale = action.get("rationale", "").lower()
            
            # Check if this is a toggle action (switch, checkbox, etc.)
            toggle_indicators = ["switch", "toggle", "enable", "disable", "turn on", "turn off"]
            navigation_indicators = ["access", "navigate", "open", "go to", "tap on"]
            
            # Only consider it a completion if it's actually a toggle action, not navigation
            has_toggle_keywords = any(indicator in rationale for indicator in toggle_indicators)
            has_navigation_keywords = any(indicator in rationale for indicator in navigation_indicators)
            
            if has_toggle_keywords and not has_navigation_keywords:
                # Check if the goal is related to toggling something
                goal_lower = goal.lower()
                if any(word in goal_lower for word in ["wifi", "wi-fi", "enable", "disable", "toggle"]):
                    return True
        
        return False 

    def _is_toggle_action(self, action: Dict[str, Any], goal: str) -> bool:
        """Check if this is a toggle action that should end the episode."""
        if action.get("action") == "tap":
            rationale = action.get("rationale", "").lower()
            resource_id = action.get("resource_id", "").lower()
            text = action.get("text", "").lower()
            
            # Check if this is actually a toggle/switch action (not navigation)
            toggle_indicators = ["switch", "toggle", "turn on", "turn off"]
            navigation_indicators = ["access", "navigate", "open", "go to", "tap on"]
            
            # Only consider it a toggle if it contains toggle keywords AND doesn't contain navigation keywords
            has_toggle_keywords = any(indicator in rationale for indicator in toggle_indicators)
            has_navigation_keywords = any(indicator in rationale for indicator in navigation_indicators)
            
            # Also check if the resource_id or text suggests it's a switch/toggle
            is_switch_element = "switch" in resource_id or "switch" in text or "toggle" in resource_id or "toggle" in text
            
            # Check if this is clicking on Wi-Fi text (which can toggle the switch)
            is_wifi_text = "wi-fi" in text.lower() or "wifi" in text.lower()
            
            if has_toggle_keywords and not has_navigation_keywords:
                # Check if the goal is related to toggling something
                goal_lower = goal.lower()
                if any(word in goal_lower for word in ["wifi", "wi-fi", "enable", "disable", "toggle"]):
                    return True
            
            # If it's a switch element, consider it a toggle regardless of rationale
            if is_switch_element:
                goal_lower = goal.lower()
                if any(word in goal_lower for word in ["wifi", "wi-fi", "enable", "disable", "toggle"]):
                    return True
            
            # If it's clicking on Wi-Fi text and the goal is about Wi-Fi, consider it a toggle
            if is_wifi_text:
                goal_lower = goal.lower()
                if any(word in goal_lower for word in ["wifi", "wi-fi", "enable", "disable", "toggle"]):
                    return True
        
        return False 