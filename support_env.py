"""
support_env.py — SupportAgentEnv core environment implementation.

Implements the OpenEnv interface:
  reset(task_difficulty) → SupportObservation
  step(action)          → SupportActionResult
  state()               → SupportState
  close()               → None

Graders are fully deterministic and return scores in (0.01, 0.99) exclusive.
"""

import asyncio
import random
import json
from typing import Dict, Any, Optional, List
from schema import SupportObservation, SupportActionResult, SupportState, SupportReward
from tasks.grader import get_grader


class SupportAgentEnv:
    def __init__(self, tickets_file: str = "tickets.json"):
        with open(tickets_file, "r") as f:
            data = json.load(f)
            self.tickets = data.get("tickets", data if isinstance(data, list) else [])
        self.current_ticket = None
        self.current_task_difficulty = "easy"
        self.step_count = 0
        self.done = False
        self.history: List[str] = []
        self.last_reward = 0.15  # floor default

    async def reset(self, task_difficulty: str = "easy") -> SupportObservation:
        """Reset the environment to start a new episode."""
        self.current_ticket = random.choice(self.tickets)
        self.current_task_difficulty = task_difficulty
        self.step_count = 0
        self.done = False
        self.history = []
        self.last_reward = 0.15

        return SupportObservation(
            ticket_id=self.current_ticket.get("id", "T001"),
            customer_message=self.current_ticket.get("text", ""),
            category_options=["delivery", "billing", "technical", "account", "general"],
            priority_options=["low", "medium", "high", "urgent"],
            task_difficulty=task_difficulty,
            step_number=self.step_count,
            done=self.done,
            history=self.history,
            info=None,
            feedback="",
        )

    async def step(self, action: Dict[str, Any]) -> SupportActionResult:
        """Process one agent action and return reward + observation."""
        if self.done:
            # Auto-reset if episode already ended
            await self.reset(self.current_task_difficulty)

        self.step_count += 1

        # Ground truth labels
        ground_truth_category = self.current_ticket.get("ground_truth_category", "general")
        ground_truth_priority = self.current_ticket.get("ground_truth_priority", "medium")
        keywords = self.current_ticket.get("keywords", [])

        # Agent action
        agent_category = (action.get("category") or "general").strip().lower()
        agent_priority = (action.get("priority") or "medium").strip().lower()
        agent_response = (action.get("response_text") or "").strip()

        # Grade using the appropriate grader
        grader = get_grader(self.current_task_difficulty)

        if self.current_task_difficulty == "easy":
            score, feedback, c_score, p_score, r_score = grader(agent_category, ground_truth_category)
        elif self.current_task_difficulty == "medium":
            score, feedback, c_score, p_score, r_score = grader(
                agent_category,
                ground_truth_category,
                agent_priority,
                ground_truth_priority,
            )
        else:  # hard
            score, feedback, c_score, p_score, r_score = grader(
                agent_category,
                ground_truth_category,
                agent_priority,
                ground_truth_priority,
                agent_response,
                keywords,
            )

        self.last_reward = score
        self.done = True

        # ... history logic ...
        preview = agent_response[:50] + "..." if len(agent_response) > 50 else agent_response
        self.history.append(
            f"classified={agent_category} | priority={agent_priority} | response=\"{preview}\""
        )

        # Build observation
        observation = SupportObservation(
            ticket_id=self.current_ticket.get("id", "T001"),
            customer_message=self.current_ticket.get("text", ""),
            category_options=["delivery", "billing", "technical", "account", "general"],
            priority_options=["low", "medium", "high", "urgent"],
            task_difficulty=self.current_task_difficulty,
            step_number=self.step_count,
            done=self.done,
            history=self.history,
            info=None,
            feedback=feedback,
        )

        # REDUNDANT CLAMP for safety - Consistency with 0.01/0.99
        def safe_clamp(x):
            try:
                val = float(x)
            except Exception:
                return 0.01
            if val <= 0.0:
                return 0.01
            if val >= 1.0:
                return 0.99
            return val

        # CLIP EVERY SCORE FIELD individually
        score = safe_clamp(score)
        c_score = safe_clamp(c_score)
        p_score = safe_clamp(p_score)
        r_score = safe_clamp(r_score)

        reward_obj = SupportReward(
            total=score,
            breakdown=feedback,
            classification_score=c_score,
            priority_score=p_score,
            response_score=r_score,
        )

        return SupportActionResult(
            observation=observation,
            reward=reward_obj,
            done=self.done,
            info={
                "feedback": feedback,
                "ground_truth": {
                    "category": ground_truth_category,
                    "priority": ground_truth_priority,
                },
            },
        )

    async def state(self) -> SupportState:
        """Get current environment state."""
        return SupportState(
            current_ticket_id=self.current_ticket.get("id") if self.current_ticket else None,
            current_ticket_text=self.current_ticket.get("text") if self.current_ticket else None,
            task_difficulty=self.current_task_difficulty,
            step_count=self.step_count,
            done=self.done,
            last_reward=self.last_reward,
            history=self.history,
        )

    async def close(self):
        """Clean up resources."""
        pass
