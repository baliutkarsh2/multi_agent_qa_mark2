"""
LLM client wrapper for OpenAI API with structured outputs and function calling.
"""
from __future__ import annotations
import json
import re
from openai import OpenAI
from typing import Any, Dict
from core.config import OPENAI_API_KEY
from core.logging_config import get_logger

log = get_logger("LLM-CLIENT")

class LLMClient:
    def __init__(self, model: str = "gpt-4o-mini"):
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.model = model

    def _extract_json_from_response(self, content: str) -> str:
        """
        Extract JSON from LLM response, handling markdown code blocks.
        """
        # Remove markdown code block formatting
        content = content.strip()
        
        # Check if response is wrapped in markdown code blocks
        if content.startswith("```json"):
            # Extract content between ```json and ```
            match = re.search(r"```json\s*(.*?)\s*```", content, re.DOTALL)
            if match:
                return match.group(1).strip()
        elif content.startswith("```"):
            # Extract content between ``` and ```
            match = re.search(r"```\s*(.*?)\s*```", content, re.DOTALL)
            if match:
                return match.group(1).strip()
        
        # If no markdown formatting, return as-is
        return content

    def request_next_action(self, goal: str, ui_xml: str, history: list[Dict[str,Any]]) -> Dict[str,Any]:
        system = """
You are a mobile UI automation planner. Your goal is to create a precise and correct action to achieve a user's goal.

**RULES FOR TAPPING ACCURATELY:**
1.  **Use Both `resource-id` and `text`:** For maximum accuracy, you **MUST** provide both `resource-id` and `text` in your `tap` action whenever both are available in the UI XML. This is the best way to ensure the correct element is selected.
2.  **Handle Duplicates with `order`:** If multiple elements on the screen have the same identifiers, you **MUST** use the `order` field (e.g., `order: 2` for the second match).
3.  **Fallback to Single Identifiers:** Only use a single identifier (`resource-id` or `text`) if providing both is not possible.

**TYPING GUIDANCE:**
- Use `type` action when you need to enter text into input fields
- First tap on the input field, then use `type` to enter the text
- For search functionality, use `type` followed by `press_key` with "enter"
- Always specify the target element (resource_id or text) for typing actions
- The `text` field in type action should contain the ACTUAL text to type (e.g., "weather", "battery"), NOT placeholder text
- Clear existing text before typing new content by using `press_key` with "back" or selecting all text first

**COMPLETION GUIDANCE:**
- If the goal appears to be achieved, use a `verify` action to confirm completion
- Look for success indicators in the UI that suggest the goal is complete
- Don't continue indefinitely - recognize when the task is done

Available actions and schemas:
- launch_app: {step_id,action:"launch_app",package,rationale}
- tap:        {step_id,action:"tap",resource_id?,text?,order?,rationale}
- type:       {step_id,action:"type",text,resource_id?,input_text?,order?,rationale}
- press_key:  {step_id,action:"press_key",key:"home"|"back"|"recents"|"enter",rationale}
- verify:     {step_id,action:"verify",resource_id?,text?,rationale}
- scroll:     {step_id,action:"scroll",direction:"up|down",until_resource_id?,until_text?,rationale}
- wait:       {step_id,action:"wait",duration (secs),rationale}

**IMPORTANT OPERATIONAL RULES**:
1. To submit a search or form, you **MUST** use `press_key` with the `enter` key after typing.
2. If the goal appears complete, use a `verify` action to confirm.
3. For search actions: tap the search field → clear existing text → type the search term → press enter.
4. The `text` field in type action should be the actual content to type, not placeholder text.

Reply with exactly one JSON object matching one of the schemas. Do not add extra commentary or keys.
"""
        user = f"""
Goal: {goal}

Current UI XML:
{ui_xml}

History:
{json.dumps(history, indent=2)}

Provide the *next* action to take as a single JSON object. If the goal appears achieved, use a verify action to confirm completion.
"""
        log.debug("Requesting next action from LLM")
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role":"system","content":system},
                      {"role":"user","content":user}],
            temperature=0.0,
            max_tokens=256
        )
        content = resp.choices[0].message.content
        log.debug(f"LLM response: {content}")
        
        # Extract JSON from response (handles markdown code blocks)
        json_content = self._extract_json_from_response(content)
        
        try:
            return json.loads(json_content)
        except json.JSONDecodeError as e:
            log.error(f"Failed to parse LLM response as JSON: {content}")
            log.error(f"Extracted content: {json_content}")
            log.error(f"JSON error: {e}")
            # Return a default action to prevent system crash
            return {
                "step_id": "error_recovery",
                "action": "wait",
                "duration": 1.0,
                "rationale": "Error parsing LLM response, waiting to recover"
            }

    def verify_action(self, action_description: str, ui_xml: str) -> Dict[str, Any]:
        """
        Specialized method for verifying if an action was successful.
        Returns a dict with 'verified' boolean and optional 'reason' string.
        """
        system = """
You are a mobile UI automation verifier. Your job is to verify whether a specific action was successful by examining the current UI state.

**VERIFICATION RULES:**
1. Check if the expected UI elements are present after the action
2. Verify that the action achieved its intended goal
3. Look for error messages or unexpected states
4. Consider the context of what the action was supposed to accomplish

**RESPONSE FORMAT:**
Return a JSON object with:
- verified: boolean (true if action was successful, false otherwise)
- reason: string (explanation of why the verification passed or failed)
- confidence: float (0.0 to 1.0, how confident you are in this assessment)

Be thorough but fair in your assessment. If you're unsure, err on the side of caution.
"""
        user = f"""
Action to verify: {action_description}

Current UI XML:
{ui_xml}

Please verify if this action was successful and provide your assessment.
"""
        log.debug("Requesting verification from LLM")
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role":"system","content":system},
                      {"role":"user","content":user}],
            temperature=0.0,
            max_tokens=256
        )
        content = resp.choices[0].message.content
        log.debug(f"LLM verification response: {content}")
        
        # Extract JSON from response (handles markdown code blocks)
        json_content = self._extract_json_from_response(content)
        
        try:
            return json.loads(json_content)
        except json.JSONDecodeError as e:
            log.error(f"Failed to parse LLM verification response as JSON: {content}")
            log.error(f"Extracted content: {json_content}")
            log.error(f"JSON error: {e}")
            # Return a default verification result
            return {
                "verified": False,
                "reason": "Error parsing LLM verification response",
                "confidence": 0.0
            } 