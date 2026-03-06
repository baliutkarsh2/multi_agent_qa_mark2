"""LLM-powered executor agent."""
from __future__ import annotations
import time, uuid
from typing import Dict, Any, List
from core.message_bus import subscribe, publish, Message
from core.registry import register_agent, get_agent
from core.memory import EpisodicMemory
from core.llm_client import LLMClient
from core.logging_config import get_logger
from core.run_logger import get_run_logger, log_run_event
from env.android_interface import AndroidDevice, UIState
from env.gesture_utils import tap_at, scroll
from env.ui_utils import get_nth_by_res_id, get_nth_by_text, find_all_by_res_id_and_text, select_nth

log = get_logger("LLM-EXECUTOR")

@register_agent("llm_executor")
class LLMExecutorAgent:
    def __init__(self, device: AndroidDevice):
        self.device = device
        self.memory = EpisodicMemory()
        self.episode_done = False
        subscribe("plan", self.on_plan)
        subscribe("episode_done", self.on_episode_done)

    def on_episode_done(self, msg: Message):
        """Mark episode as done to stop further execution."""
        self.episode_done = True
        log.info("Episode marked as done, stopping execution.")

    def on_plan(self, msg: Message):
        # Check if episode is already done
        if self.episode_done:
            log.info("Episode already done, ignoring plan message.")
            return
            
        step = msg.payload["step"]
        eid  = msg.payload["episode_id"]
        log.info(f"Executing step: {step}")
        result={"step":step,"success":False,"error":None}
        
        try:
            # Check if episode is done before executing any action
            if self.episode_done:
                log.info("Episode marked as done during execution, stopping.")
                return
                
            # All actions that need the current UI state
            try:
                ui_xml = self.device.get_ui_tree().xml
            except Exception as e:
                log.warning(f"Failed to get UI tree: {e}")
                ui_xml = ""
            act=step["action"]

            if act=="launch_app":
                self.device.launch_app(step["package"])
            elif act=="tap":
                # Check if episode is done before executing tap
                if self.episode_done:
                    log.info("Episode done, stopping tap execution.")
                    return
                    
                coord=None
                order = step.get("order", 1)

                # Prioritize searching by both resource-id and text for max accuracy
                if "resource_id" in step and "text" in step:
                    matches = find_all_by_res_id_and_text(ui_xml, step["resource_id"], step["text"])
                    coord = select_nth(matches, order)

                # Fallback to resource-id only
                if not coord and "resource_id" in step:
                    coord=get_nth_by_res_id(ui_xml,step["resource_id"], order)
                
                # Fallback to text only
                if not coord and step.get("text"):
                    coord=get_nth_by_text(ui_xml,step["text"], order)
                
                if not coord: raise RuntimeError("Element not found")
                tap_at(self.device,coord)
            elif act=="press_key":
                # Check if episode is done before executing press_key
                if self.episode_done:
                    log.info("Episode done, stopping press_key execution.")
                    return
                    
                self.device.press_key(step["key"])
            elif act=="type":
                # Check if episode is done before executing type
                if self.episode_done:
                    log.info("Episode done, stopping type execution.")
                    return
                    
                # Handle typing action
                text_to_type = step.get("text", "")
                if not text_to_type:
                    raise RuntimeError("No text specified for type action")
                
                # If a specific element is specified, tap it first to focus
                if "resource_id" in step or "text" in step:
                    coord = None
                    order = step.get("order", 1)
                    
                    # Prioritize searching by both resource-id and text for max accuracy
                    if "resource_id" in step and "text" in step:
                        matches = find_all_by_res_id_and_text(ui_xml, step["resource_id"], step["text"])
                        coord = select_nth(matches, order)
                    
                    # Fallback to resource-id only
                    if not coord and "resource_id" in step:
                        coord = get_nth_by_res_id(ui_xml, step["resource_id"], order)
                    
                    # Fallback to text only
                    if not coord and step.get("text"):
                        coord = get_nth_by_text(ui_xml, step["text"], order)
                    
                    if coord:
                        tap_at(self.device, coord)
                        # Clear existing text
                        import time
                        time.sleep(0.5)  # Wait for focus
                        self.device.clear_text_field()
                        time.sleep(0.5)  # Wait before typing
                    else:
                        log.warning("Target element for typing not found, proceeding anyway")
                
                # Type the text
                self.device.type_text(text_to_type)
            elif act=="verify":
                post_xml=self.device.get_ui_tree().xml
                result["success"]=bool(
                    ("resource_id" in step and get_nth_by_res_id(post_xml,step["resource_id"],1)) or
                    ("text" in step and get_nth_by_text(post_xml,step["text"],1))
                )
            elif act=="scroll":
                scroll(self.device, step["direction"])
            elif act=="wait":
                import time; time.sleep(step["duration"])
            
            result["success"] = True if act not in ["verify"] else result.get("success", False)
        
        except Exception as e:
            result["error"]=str(e)
            log.error(f"Execution error: {e}")
        
        # Take screenshot with error handling
        try:
            shot = self.device.screenshot(step.get("step_id", "action"))
        except Exception as e:
            log.warning(f"Screenshot failed: {e}")
            shot = "screenshot_failed.png"
        
        # Store the updated history
        history = self.memory.retrieve(eid) or []
        history.append(result)
        self.memory.store(eid, history, tags=["history"])
        
        # Get UI snapshot for logging and reporting
        try:
            ui_snapshot = self.device.get_ui_tree().xml
        except Exception as e:
            log.warning(f"Failed to get UI snapshot: {e}")
            ui_snapshot = ""
        
        # Log step execution to run logger if available
        run_logger = get_run_logger()
        if run_logger:
            run_logger.log_step_execution(eid, step, result, ui_snapshot)
        
        # Publish the report, which the planner will listen for
        publish(Message(
            "LLM-EXECUTOR",
            "exec-report",
            {"report":result,"episode_id":eid, "ui_snapshot": ui_snapshot}
        )) 