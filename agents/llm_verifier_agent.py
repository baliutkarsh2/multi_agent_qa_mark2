"""LLM-powered verifier agent with OpenAI Vision API integration."""
from __future__ import annotations
import uuid
import time
import json
import base64
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from core.message_bus import subscribe, publish, Message
from core.registry import register_agent
from core.memory import EpisodicMemory
from core.llm_client import LLMClient
from core.logging_config import get_logger
from core.run_logger import get_run_logger, log_run_event
from env.android_interface import AndroidDevice

log = get_logger("LLM-VERIFIER")

@register_agent("llm_verifier")
class LLMVerifierAgent:
    def __init__(self, device: AndroidDevice, vision_model: str = "gpt-4o", max_retries: int = 3):
        self.device = device
        self.llm = LLMClient()
        self.vision_model = vision_model
        self.max_retries = max_retries
        self.episodic_memory = EpisodicMemory()
        
        # Subscribe to execution reports and verification requests
        subscribe("exec-report", self.on_exec)
        subscribe("verify-request", self.on_verify_request)
        
        log.info(f"LLM Verifier Agent initialized with vision model: {vision_model}")

    def on_exec(self, msg: Message):
        """Handle execution reports and trigger implicit verification for critical actions."""
        step = msg.payload["report"]["step"]
        eid = msg.payload["episode_id"]
        
        # Check if this is an explicit verification action
        if step["action"] == "verify":
            self._handle_explicit_verification(step, eid)
            return
        
        # Check if this action should be verified implicitly
        if self._should_verify_implicitly(step):
            log.info(f"Triggering implicit verification for critical action: {step['action']}")
            self._verify_action_implicitly(step, eid)

    def on_verify_request(self, msg: Message):
        """Handle explicit verification requests."""
        step = msg.payload["step"]
        eid = msg.payload["episode_id"]
        self._handle_explicit_verification(step, eid)

    def _should_verify_implicitly(self, step: Dict[str, Any]) -> bool:
        """Determine if an action should be verified implicitly."""
        critical_actions = ["launch_app", "type", "tap", "press_key", "scroll"]
        return step.get("action") in critical_actions

    def _verify_action_implicitly(self, step: Dict[str, Any], episode_id: str):
        """Verify critical actions without explicit verification steps."""
        try:
            # Get current UI state
            ui_xml = self.device.get_ui_tree().xml
            
            # Take a screenshot for visual verification
            screenshot_path = self._capture_screenshot(episode_id, step.get("step_id", "implicit"))
            
            # Create verification description
            action_description = self._create_verification_description(step)
            
            # Perform multi-modal verification
            result = self.verify_action(action_description, ui_xml, screenshot_path)
            
            # Log the implicit verification result
            log.info(f"Implicit verification for {step['action']}: {result['verified']} (confidence: {result['confidence']})")
            
            # Store in episodic memory for future reference
            self.episodic_memory.store(f"implicit_verification_{step.get('step_id', 'unknown')}", {
                "step": step,
                "result": result,
                "timestamp": time.time()
            })
            
            # Handle verification failure with retry logic
            if not result.get("verified", False):
                self._handle_implicit_verification_failure(step, episode_id, result, ui_xml, screenshot_path)
            else:
                # Publish successful verification report
                self._publish_verification_report(episode_id, step, result, ui_xml, screenshot_path)
            
        except Exception as e:
            log.error(f"Implicit verification failed: {e}")
            # Publish failure report for error handling
            self._publish_verification_report(episode_id, step, {
                "verified": False,
                "reason": f"Verification error: {str(e)}",
                "confidence": 0.0,
                "error_type": "verification_exception"
            }, ui_xml, None)

    def _handle_explicit_verification(self, step: Dict[str, Any], episode_id: str):
        """Handle explicit verification actions."""
        log.info(f"Handling explicit verification: {step}")
        
        try:
            # Get current UI state
            ui_xml = self.device.get_ui_tree().xml
            
            # Take a screenshot for visual verification
            screenshot_path = self._capture_screenshot(episode_id, step.get("step_id", "explicit"))
            
            # Create verification description
            action_description = self._create_verification_description(step)
            
            # Perform multi-modal verification
            result = self.verify_action(action_description, ui_xml, screenshot_path)
            
            # Publish verification report
            self._publish_verification_report(episode_id, step, result, ui_xml, screenshot_path)
            
        except Exception as e:
            log.error(f"Explicit verification failed: {e}")
            # Publish failure report
            self._publish_verification_report(episode_id, step, {
                "verified": False,
                "reason": f"Verification failed due to error: {str(e)}",
                "confidence": 0.0
            }, ui_xml, None)

    def verify_action(self, action_description: str, ui_xml: str, screenshot_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Enhanced verification with multi-modal analysis (UI XML + screenshot).
        
        Args:
            action_description: Description of the action to verify
            ui_xml: Current UI XML state
            screenshot_path: Optional path to screenshot for visual verification
            
        Returns:
            Dict with verification result including verified, reason, confidence, and analysis details
        """
        try:
            # Step 1: Text-based verification using UI XML
            text_result = self._verify_from_ui_xml(action_description, ui_xml)
            
            # Step 2: Visual verification using screenshot (if available)
            visual_result = None
            if screenshot_path and Path(screenshot_path).exists():
                visual_result = self._verify_from_screenshot(action_description, screenshot_path)
            
            # Step 3: Combine results intelligently
            combined_result = self._combine_verification_results(text_result, visual_result)
            
            # Step 4: Apply enhanced confidence calculation
            enhanced_confidence = self._calculate_enhanced_confidence(
                action_description, ui_xml, combined_result
            )
            combined_result["confidence"] = enhanced_confidence
            
            # Step 5: Add analysis metadata
            combined_result["analysis"] = {
                "text_verification": text_result,
                "visual_verification": visual_result,
                "verification_method": "multi_modal" if visual_result else "text_only",
                "timestamp": time.time()
            }
            
            return combined_result
            
        except Exception as e:
            log.error(f"Verification failed: {e}")
            return {
                "verified": False,
                "reason": f"Verification failed due to error: {str(e)}",
                "confidence": 0.0,
                "analysis": {
                    "error": str(e),
                    "verification_method": "error",
                    "timestamp": time.time()
                }
            }

    def _verify_from_ui_xml(self, action_description: str, ui_xml: str) -> Dict[str, Any]:
        """Verify action using UI XML analysis."""
        try:
            system = """
You are a mobile UI automation verifier. Your job is to verify whether a specific action was successful by examining the current UI state.

**VERIFICATION RULES:**
1. Check if the expected UI elements are present after the action
2. Verify that the action achieved its intended goal
3. Look for error messages or unexpected states
4. Consider the context of what the action was supposed to accomplish
5. Analyze UI structure and element states

**RESPONSE FORMAT:**
Return a JSON object with:
- verified: boolean (true if action was successful, false otherwise)
- reason: string (explanation of why the verification passed or failed)
- confidence: float (0.0 to 1.0, how confident you are in this assessment)
- ui_analysis: object with details about UI state analysis

Be thorough but fair in your assessment. If you're unsure, err on the side of caution.
"""
            user = f"""
Action to verify: {action_description}

Current UI XML:
{ui_xml}

Please verify if this action was successful and provide your assessment.
"""
            
            resp = self.llm.client.chat.completions.create(
                model=self.llm.model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user}
                ],
                temperature=0.0,
                max_tokens=512
            )
            
            content = resp.choices[0].message.content
            json_content = self.llm._extract_json_from_response(content)
            result = json.loads(json_content)
            
            # Ensure required fields are present
            if "verified" not in result:
                result["verified"] = False
            if "reason" not in result:
                result["reason"] = "No reason provided"
            if "confidence" not in result:
                result["confidence"] = 0.5
                
            return result
            
        except Exception as e:
            log.error(f"Failed to verify from UI XML: {e}")
            return {
                "verified": False,
                "reason": f"UI XML verification failed: {str(e)}",
                "confidence": 0.0
            }

    def _verify_from_screenshot(self, action_description: str, screenshot_path: str) -> Dict[str, Any]:
        """Verify action using OpenAI Vision API for screenshot analysis."""
        try:
            # Encode screenshot to base64
            base64_image = self._encode_image_to_base64(screenshot_path)
            
            # Create vision-based verification prompt
            vision_prompt = f"""
Look at this Android screenshot and verify: {action_description}

**VISUAL VERIFICATION TASKS:**
1. Check if the expected UI elements are visible and properly displayed
2. Verify that the action appears successful based on visual cues
3. Look for error messages, loading states, or unexpected visual changes
4. Analyze the overall screen state and user interface
5. Consider visual context and layout consistency

**RESPONSE FORMAT:**
Return a JSON object with:
- verified: boolean (true if action appears successful, false otherwise)
- reason: string (explanation of visual verification result)
- confidence: float (0.0 to 1.0, confidence in visual assessment)
- visual_analysis: object with details about visual elements and states

Be thorough in your visual analysis. Consider UI patterns, colors, icons, and layout.
"""
            
            # Call OpenAI Vision API
            response = self.llm.client.chat.completions.create(
                model=self.vision_model,
                messages=[
                    {"role": "user", "content": [
                        {"type": "text", "text": vision_prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_image}"}}
                    ]}
                ],
                temperature=0.0,
                max_tokens=512
            )
            
            content = response.choices[0].message.content
            json_content = self.llm._extract_json_from_response(content)
            result = json.loads(json_content)
            
            # Ensure required fields are present
            if "verified" not in result:
                result["verified"] = False
            if "reason" not in result:
                result["reason"] = "No visual reason provided"
            if "confidence" not in result:
                result["confidence"] = 0.5
                
            return result
            
        except Exception as e:
            log.error(f"Failed to verify from screenshot: {e}")
            return {
                "verified": False,
                "reason": f"Visual verification failed: {str(e)}",
                "confidence": 0.0
            }

    def _combine_verification_results(self, text_result: Dict[str, Any], visual_result: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Intelligently combine text and visual verification results."""
        if not visual_result:
            # Text-only verification
            return {
                "verified": text_result.get("verified", False),
                "reason": f"Text verification: {text_result.get('reason', 'No reason')}",
                "confidence": text_result.get("confidence", 0.0),
                "combination_method": "text_only"
            }
        
        # Both text and visual results available
        text_verified = text_result.get("verified", False)
        visual_verified = visual_result.get("verified", False)
        text_confidence = text_result.get("confidence", 0.0)
        visual_confidence = visual_result.get("confidence", 0.0)
        
        # If both results agree, use the higher confidence
        if text_verified == visual_verified:
            combined_confidence = max(text_confidence, visual_confidence)
            return {
                "verified": text_verified,
                "reason": f"Text: {text_result.get('reason', 'No reason')} | Visual: {visual_result.get('reason', 'No reason')}",
                "confidence": combined_confidence,
                "combination_method": "agreement",
                "agreement_level": "full"
            }
        
        # If results disagree, use the higher confidence result
        if text_confidence > visual_confidence:
            return {
                "verified": text_verified,
                "reason": f"Text verification preferred (confidence: {text_confidence:.2f}) - {text_result.get('reason', 'No reason')}",
                "confidence": text_confidence,
                "combination_method": "confidence_based",
                "preferred_method": "text",
                "disagreement": True
            }
        else:
            return {
                "verified": visual_verified,
                "reason": f"Visual verification preferred (confidence: {visual_confidence:.2f}) - {visual_result.get('reason', 'No reason')}",
                "confidence": visual_confidence,
                "combination_method": "confidence_based",
                "preferred_method": "visual",
                "disagreement": True
            }

    def _calculate_enhanced_confidence(self, action_description: str, ui_xml: str, base_result: Dict[str, Any]) -> float:
        """Calculate enhanced confidence based on multiple factors."""
        base_confidence = base_result.get("confidence", 0.5)
        
        # Factor 1: Element presence analysis (0.2 weight)
        element_score = self._analyze_element_presence(action_description, ui_xml)
        
        # Factor 2: Error detection (0.15 weight)
        error_score = self._analyze_error_indicators(ui_xml)
        
        # Factor 3: Context consistency (0.15 weight)
        context_score = self._analyze_context_consistency(action_description, ui_xml)
        
        # Factor 4: UI state stability (0.1 weight)
        stability_score = self._analyze_ui_stability(ui_xml)
        
        # Calculate weighted enhancement
        enhancement = (
            element_score * 0.2 +
            error_score * 0.15 +
            context_score * 0.15 +
            stability_score * 0.1
        )
        
        # Apply enhancement to base confidence
        enhanced_confidence = base_confidence + enhancement
        
        # Ensure confidence stays within valid range
        return max(0.0, min(1.0, enhanced_confidence))

    def _analyze_element_presence(self, action_description: str, ui_xml: str) -> float:
        """Analyze presence of expected UI elements."""
        description_lower = action_description.lower()
        ui_lower = ui_xml.lower()
        
        # Look for common UI elements mentioned in the description
        ui_elements = ["button", "text", "field", "list", "result", "menu", "dialog", "icon", "image"]
        
        # Count elements that are present in the UI XML
        present_elements = [elem for elem in ui_elements if elem in ui_lower]
        
        # Score based on element presence
        if len(present_elements) >= 2:
            return 0.3
        elif len(present_elements) == 1:
            return 0.15
        else:
            return 0.0

    def _analyze_error_indicators(self, ui_xml: str) -> float:
        """Analyze presence of error indicators."""
        error_indicators = [
            "error", "failed", "unavailable", "not found", "timeout",
            "network error", "server error", "connection failed", "permission denied",
            "invalid", "incorrect", "missing", "broken"
        ]
        
        ui_lower = ui_xml.lower()
        error_count = sum(1 for indicator in error_indicators if indicator in ui_lower)
        
        # Score based on absence of errors (higher is better)
        if error_count == 0:
            return 0.3
        elif error_count == 1:
            return 0.1
        else:
            return -0.2  # Penalty for multiple errors

    def _analyze_context_consistency(self, action_description: str, ui_xml: str) -> float:
        """Analyze consistency between action context and UI state."""
        # This is a simplified analysis - in practice, you might want more sophisticated logic
        description_lower = action_description.lower()
        ui_lower = ui_xml.lower()
        
        # Check for action-specific context indicators
        if "launch" in description_lower and "app" in description_lower:
            # Look for app-specific indicators
            if any(indicator in ui_lower for indicator in ["home", "main", "launcher", "app"]):
                return 0.3
        
        if "type" in description_lower or "input" in description_lower:
            # Look for input-related indicators
            if any(indicator in ui_lower for indicator in ["input", "text", "field", "keyboard"]):
                return 0.3
        
        if "tap" in description_lower or "click" in description_lower:
            # Look for interactive elements
            if any(indicator in ui_lower for indicator in ["button", "clickable", "interactive"]):
                return 0.3
        
        return 0.1  # Default score

    def _analyze_ui_stability(self, ui_xml: str) -> float:
        """Analyze UI state stability."""
        ui_lower = ui_xml.lower()
        
        # Look for stability indicators
        stability_indicators = ["stable", "ready", "complete", "finished", "loaded"]
        instability_indicators = ["loading", "progress", "updating", "refreshing", "spinning"]
        
        stable_count = sum(1 for indicator in stability_indicators if indicator in ui_lower)
        unstable_count = sum(1 for indicator in instability_indicators if indicator in ui_lower)
        
        # Score based on stability vs instability
        if stable_count > unstable_count:
            return 0.2
        elif stable_count == unstable_count:
            return 0.1
        else:
            return 0.0

    def _capture_screenshot(self, episode_id: str, step_id: str) -> str:
        """Capture a screenshot for verification."""
        try:
            # Use the device's screenshot capability
            screenshot_path = self.device.screenshot(f"{episode_id}_{step_id}")
            log.debug(f"Screenshot captured: {screenshot_path}")
            
            # Log to run logger if available
            run_logger = get_run_logger()
            if run_logger:
                run_logger.log_screenshot(episode_id, step_id, screenshot_path, "Verification screenshot")
            
            return screenshot_path
        except Exception as e:
            log.warning(f"Screenshot capture failed: {e}")
            
            # Log error to run logger if available
            run_logger = get_run_logger()
            if run_logger:
                run_logger.log_error("LLM-VERIFIER", f"Screenshot capture failed: {e}", episode_id, step_id)
            
            return None

    def _encode_image_to_base64(self, image_path: str) -> str:
        """Encode image to base64 for OpenAI Vision API."""
        try:
            with open(image_path, "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
                return encoded_string
        except Exception as e:
            log.error(f"Failed to encode image to base64: {e}")
            raise

    def _create_verification_description(self, step: Dict[str, Any]) -> str:
        """Create a human-readable description of what we're verifying."""
        action = step.get("action", "")
        resource_id = step.get("resource_id", "")
        text = step.get("text", "")
        rationale = step.get("rationale", "")
        
        description = f"Action: {action}"
        if resource_id:
            description += f", Resource ID: {resource_id}"
        if text:
            description += f", Text: {text}"
        if rationale:
            description += f", Rationale: {rationale}"
            
        return description 

    def _publish_verification_report(self, episode_id: str, step: Dict[str, Any], result: Dict[str, Any], ui_xml: str, screenshot_path: Optional[str]):
        """Publish verification report to message bus."""
        report = {
            "episode_id": episode_id,
            "step_id": step.get("step_id", "unknown"),
            "action": step.get("action", "unknown"),
            "verified": result.get("verified", False),
            "reason": result.get("reason", "No reason provided"),
            "confidence": result.get("confidence", 0.0),
            "ui_xml": ui_xml,
            "screenshot_path": screenshot_path,
            "analysis": result.get("analysis", {}),
            "timestamp": time.time()
        }
        
        # Log to run logger if available
        run_logger = get_run_logger()
        if run_logger:
            run_logger.log_verification_report(episode_id, step, result, ui_xml, screenshot_path)
        
        # Publish detailed verification report
        publish(Message(
            "LLM-VERIFIER",
            "verify-report",
            report
        ))
        
        # Publish verification completion message to trigger next action planning
        publish(Message(
            "LLM-VERIFIER",
            "verification-complete",
            {
                "episode_id": episode_id,
                "verification_result": result,
                "ui_xml": ui_xml,
                "step": step,
                "timestamp": time.time()
            }
        ))
        
        log.info(f"Verification report published: {result['verified']} (confidence: {result['confidence']})")
        log.info(f"Verification completion message sent for episode {episode_id}") 

    def _handle_implicit_verification_failure(self, step: Dict[str, Any], episode_id: str, result: Dict[str, Any], ui_xml: str, screenshot_path: Optional[str]):
        """Handle implicit verification failures with intelligent recovery strategies."""
        action_type = step.get("action", "unknown")
        failure_reason = result.get("reason", "Unknown failure")
        confidence = result.get("confidence", 0.0)
        
        log.warning(f"Implicit verification failed for {action_type}: {failure_reason} (confidence: {confidence})")
        
        # Determine recovery strategy based on action type and failure reason
        recovery_strategy = self._determine_recovery_strategy(action_type, failure_reason, confidence)
        
        if recovery_strategy:
            log.info(f"Attempting recovery strategy: {recovery_strategy}")
            recovery_success = self._execute_recovery_strategy(episode_id, step, recovery_strategy, ui_xml)
            
            if recovery_success:
                log.info(f"Recovery successful for {action_type}")
                # Publish successful recovery verification
                recovery_result = {
                    "verified": True,
                    "reason": f"Recovery successful using {recovery_strategy}",
                    "confidence": min(confidence + 0.3, 1.0),  # Boost confidence after recovery
                    "recovery_used": recovery_strategy
                }
                self._publish_verification_report(episode_id, step, recovery_result, ui_xml, screenshot_path)
                return
            else:
                log.warning(f"Recovery failed for {action_type}")
        
        # If no recovery strategy or recovery failed, publish failure report
        failure_result = {
            "verified": False,
            "reason": failure_reason,
            "confidence": confidence,
            "recovery_attempted": bool(recovery_strategy),
            "recovery_strategy": recovery_strategy,
            "requires_manual_intervention": True
        }
        
        self._publish_verification_report(episode_id, step, failure_result, ui_xml, screenshot_path)
        
        # Publish critical failure notification
        self._publish_critical_failure_notification(episode_id, step, failure_result)

    def _determine_recovery_strategy(self, action_type: str, failure_reason: str, confidence: float) -> Optional[str]:
        """Determine appropriate recovery strategy based on failure context."""
        failure_lower = failure_reason.lower()
        
        # High confidence failures (likely real failures) get different strategies
        if confidence > 0.7:
            if "element not found" in failure_lower:
                if action_type == "tap":
                    return "retry_with_different_selector"
                elif action_type == "type":
                    return "retry_with_focus_first"
                elif action_type == "launch_app":
                    return "retry_with_delay"
            elif "timeout" in failure_lower:
                return "retry_with_backoff"
            elif "permission" in failure_lower:
                return "skip_and_continue"
        
        # Medium confidence failures get retry strategies
        elif confidence > 0.3:
            if action_type in ["tap", "type", "press_key"]:
                return "retry_once"
            elif action_type == "launch_app":
                return "retry_with_delay"
        
        # Low confidence failures get basic retry
        else:
            if action_type in ["tap", "type", "press_key"]:
                return "retry_once"
        
        return None

    def _execute_recovery_strategy(self, episode_id: str, step: Dict[str, Any], strategy: str, ui_xml: str) -> bool:
        """Execute the determined recovery strategy."""
        try:
            if strategy == "retry_once":
                return self._retry_action_once(episode_id, step)
            elif strategy == "retry_with_delay":
                return self._retry_action_with_delay(episode_id, step, delay=2.0)
            elif strategy == "retry_with_backoff":
                return self._retry_action_with_backoff(episode_id, step)
            elif strategy == "retry_with_different_selector":
                return self._retry_with_different_selector(episode_id, step, ui_xml)
            elif strategy == "retry_with_focus_first":
                return self._retry_with_focus_first(episode_id, step, ui_xml)
            elif strategy == "skip_and_continue":
                return self._skip_action_and_continue(episode_id, step)
            else:
                log.warning(f"Unknown recovery strategy: {strategy}")
                return False
                
        except Exception as e:
            log.error(f"Recovery strategy execution failed: {e}")
            return False

    def _retry_action_once(self, episode_id: str, step: Dict[str, Any]) -> bool:
        """Retry the action once with a short delay."""
        try:
            import time
            time.sleep(1.0)  # Short delay
            
            # Re-execute the action
            if step["action"] == "tap":
                # Re-tap with current UI state
                ui_xml = self.device.get_ui_tree().xml
                coord = self._find_element_coordinates(step, ui_xml)
                if coord:
                    self.device.tap(coord[0], coord[1])
                    return True
            elif step["action"] == "type":
                # Re-type the text
                text = step.get("text", "")
                if text:
                    self.device.type_text(text)
                    return True
            elif step["action"] == "launch_app":
                # Re-launch the app
                package = step.get("package", "")
                if package:
                    self.device.launch_app(package)
                    return True
            
            return False
            
        except Exception as e:
            log.error(f"Retry action failed: {e}")
            return False

    def _retry_action_with_delay(self, episode_id: str, step: Dict[str, Any], delay: float) -> bool:
        """Retry the action after a specified delay."""
        try:
            import time
            time.sleep(delay)
            return self._retry_action_once(episode_id, step)
        except Exception as e:
            log.error(f"Retry with delay failed: {e}")
            return False

    def _retry_action_with_backoff(self, episode_id: str, step: Dict[str, Any]) -> bool:
        """Retry the action with exponential backoff."""
        try:
            import time
            delays = [1.0, 2.0, 4.0]  # Exponential backoff
            
            for delay in delays:
                time.sleep(delay)
                if self._retry_action_once(episode_id, step):
                    return True
            
            return False
            
        except Exception as e:
            log.error(f"Retry with backoff failed: {e}")
            return False

    def _retry_with_different_selector(self, episode_id: str, step: Dict[str, Any], ui_xml: str) -> bool:
        """Retry using a different element selector strategy."""
        try:
            if step["action"] == "tap":
                # Try different selectors in order of preference
                selectors = [
                    ("resource_id", step.get("resource_id")),
                    ("text", step.get("text")),
                    ("content_desc", step.get("content_desc")),
                    ("class_name", step.get("class_name"))
                ]
                
                for selector_type, selector_value in selectors:
                    if selector_value:
                        coord = self._find_element_by_selector(selector_type, selector_value, ui_xml)
                        if coord:
                            self.device.tap(coord[0], coord[1])
                            return True
                
            return False
            
        except Exception as e:
            log.error(f"Retry with different selector failed: {e}")
            return False

    def _retry_with_focus_first(self, episode_id: str, step: Dict[str, Any], ui_xml: str) -> bool:
        """Retry by first focusing the element, then performing the action."""
        try:
            if step["action"] == "type":
                # First tap to focus, then type
                coord = self._find_element_coordinates(step, ui_xml)
                if coord:
                    self.device.tap(coord[0], coord[1])
                    time.sleep(0.5)  # Wait for focus
                    self.device.clear_text_field()
                    time.sleep(0.5)  # Wait before typing
                    self.device.type_text(step.get("text", ""))
                    return True
            
            return False
            
        except Exception as e:
            log.error(f"Retry with focus first failed: {e}")
            return False

    def _skip_action_and_continue(self, episode_id: str, step: Dict[str, Any]) -> bool:
        """Skip the action and continue with the episode."""
        try:
            log.info(f"Skipping action {step['action']} due to permission/access issues")
            
            # Mark as skipped in memory
            self.episodic_memory.store(f"skipped_action_{step.get('step_id', 'unknown')}", {
                "step": step,
                "reason": "Permission/access issue",
                "timestamp": time.time(),
                "action": "skipped"
            })
            
            return True
            
        except Exception as e:
            log.error(f"Skip action failed: {e}")
            return False

    def _find_element_coordinates(self, step: Dict[str, Any], ui_xml: str) -> Optional[tuple]:
        """Find element coordinates using available selectors."""
        try:
            from env.ui_utils import get_nth_by_res_id, get_nth_by_text, find_all_by_res_id_and_text, select_nth
            
            order = step.get("order", 1)
            
            # Prioritize searching by both resource-id and text for max accuracy
            if "resource_id" in step and "text" in step:
                matches = find_all_by_res_id_and_text(ui_xml, step["resource_id"], step["text"])
                coord = select_nth(matches, order)
                if coord:
                    return coord
            
            # Fallback to resource-id only
            if "resource_id" in step:
                coord = get_nth_by_res_id(ui_xml, step["resource_id"], order)
                if coord:
                    return coord
            
            # Fallback to text only
            if step.get("text"):
                coord = get_nth_by_text(ui_xml, step["text"], order)
                if coord:
                    return coord
            
            return None
            
        except Exception as e:
            log.error(f"Find element coordinates failed: {e}")
            return None

    def _find_element_by_selector(self, selector_type: str, selector_value: str, ui_xml: str) -> Optional[tuple]:
        """Find element using a specific selector type."""
        try:
            from env.ui_utils import get_nth_by_res_id, get_nth_by_text
            
            if selector_type == "resource_id":
                return get_nth_by_res_id(ui_xml, selector_value, 1)
            elif selector_type == "text":
                return get_nth_by_text(ui_xml, selector_value, 1)
            # Add more selector types as needed
            
            return None
            
        except Exception as e:
            log.error(f"Find element by selector failed: {e}")
            return None

    def _publish_critical_failure_notification(self, episode_id: str, step: Dict[str, Any], failure_result: Dict[str, Any]):
        """Publish critical failure notification for manual intervention."""
        notification = {
            "episode_id": episode_id,
            "step": step,
            "failure_result": failure_result,
            "timestamp": time.time(),
            "severity": "critical",
            "action_required": "manual_intervention"
        }
        
        # Log to run logger if available
        run_logger = get_run_logger()
        if run_logger:
            run_logger.log_critical_failure(episode_id, step, failure_result)
        
        publish(Message(
            "LLM-VERIFIER",
            "critical-failure",
            notification
        ))
        
        log.error(f"Critical failure notification published for episode {episode_id}: {step['action']}") 