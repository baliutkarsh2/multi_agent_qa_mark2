"""LLM-powered supervisor agent."""
from __future__ import annotations
import uuid
from collections import defaultdict
from typing import Dict, Any, List
from core.message_bus import subscribe, Message, publish
from core.registry import register_agent
from evaluation.evaluator import EpisodeEvaluator
from core.memory import NarrativeMemory
from core.logging_config import get_logger

log = get_logger("LLM-SUPERVISOR")

@register_agent("llm_supervisor")
class LLMSupervisorAgent:
    def __init__(self):
        self._eps = {}
        self.eval = EpisodeEvaluator()
        subscribe("exec-report", self.on_exec)
        subscribe("verify-report", self.on_verify)
        subscribe("plan-report", self.on_plan)

    def on_exec(self, msg: Message):
        episode_id = msg.payload["episode_id"]
        ep = self._eps.setdefault(episode_id, {"exec": [], "verify": [], "plans": []})
        ep["exec"].append(msg.payload)
        log.info(f"Execution report received for episode {episode_id}")

    def on_verify(self, msg: Message):
        episode_id = msg.payload["episode_id"]
        ep = self._eps.get(episode_id)
        if not ep:
            log.warning(f"Received verification report for unknown episode {episode_id}")
            return
            
        ep["verify"].append(msg.payload)
        log.info(f"Verification report received for episode {episode_id}: {msg.payload.get('verified')}")
        
        # Check if verification failed
        if not msg.payload.get("verified", False):
            log.warning(f"Verification failed for step {msg.payload.get('step_id')}: {msg.payload.get('reason')}")
            # Could trigger retry logic here if needed
        
        self._check_episode_completion(episode_id)

    def on_plan(self, msg: Message):
        episode_id = msg.payload["episode_id"]
        ep = self._eps.setdefault(episode_id, {"exec": [], "verify": [], "plans": []})
        ep["plans"].append(msg.payload)
        log.info(f"Plan report received for episode {episode_id}")

    def _check_episode_completion(self, episode_id: str):
        """Check if an episode is complete and evaluate it."""
        ep = self._eps.get(episode_id)
        if not ep:
            return
            
        # Count verification steps that were executed
        verify_steps_executed = sum(1 for r in ep["exec"] if r["report"]["step"]["action"] == "verify")
        verify_reports_received = len(ep["verify"])
        
        log.info(f"Episode {episode_id}: {verify_reports_received}/{verify_steps_executed} verifications complete")
        
        # If all verify steps are complete, finish the episode
        if verify_reports_received >= verify_steps_executed and verify_steps_executed > 0:
            self._complete_episode(episode_id)
        elif len(ep["exec"]) > 0 and verify_steps_executed == 0:
            # No verification steps planned, but execution is complete
            self._complete_episode(episode_id)

    def _complete_episode(self, episode_id: str):
        """Complete an episode and publish results."""
        ep = self._eps[episode_id]
        
        try:
            # Evaluate the episode
            score = self.eval.evaluate(ep["exec"], ep["verify"])
            
            # Store in narrative memory
            NarrativeMemory().store(
                f"ep-{episode_id}", 
                score.model_dump(), 
                tags=["episode", "evaluation"]
            )
            
            log.info(f"Episode {episode_id} completed successfully")
            log.info(f"Episode {episode_id} summary: {score.model_dump_json(indent=2)}")
            
            # Calculate verification success rate
            verification_success_rate = 0.0
            if ep["verify"]:
                successful_verifications = sum(1 for v in ep["verify"] if v.get("verified", False))
                verification_success_rate = successful_verifications / len(ep["verify"])
            
            # Publish episode completion with detailed results
            publish(Message(
                "LLM-SUPERVISOR", 
                "episode_done", 
                {
                    "episode_id": episode_id,
                    "reason": "All steps completed and verified",
                    "score": score.model_dump(),
                    "verification_success_rate": verification_success_rate,
                    "total_steps": len(ep["exec"]),
                    "verified_steps": len(ep["verify"])
                }
            ))
            
        except Exception as e:
            log.error(f"Error completing episode {episode_id}: {e}")
            # Still publish completion to prevent hanging
            publish(Message(
                "LLM-SUPERVISOR", 
                "episode_done", 
                {
                    "episode_id": episode_id,
                    "reason": f"Episode completed with errors: {str(e)}",
                    "error": True
                }
            )) 