import asyncio
import random
import json
from typing import Dict, Any, Optional, List
from schema import SupportObservation, SupportActionResult, SupportState
from graders import get_grader

class SupportAgentEnv:
    def __init__(self, tickets_file: str = "tickets.json"):
        with open(tickets_file, 'r') as f:
            data = json.load(f)
            self.tickets = data.get('tickets', data if isinstance(data, list) else [])
        self.current_ticket = None
        self.current_task_difficulty = "easy"
        self.step_count = 0
        self.done = False
        self.history = []
        self.last_reward = 0.0
        
    async def reset(self, task_difficulty: str = "easy") -> SupportObservation:
        """Reset the environment to start a new episode"""
        self.current_ticket = random.choice(self.tickets)
        self.current_task_difficulty = task_difficulty
        self.step_count = 0
        self.done = False
        self.history = []
        self.last_reward = 0.0
        
        return SupportObservation(
            ticket_id=self.current_ticket.get('id', 'T001'),
            customer_message=self.current_ticket.get('text', ''),
            category_options=["delivery", "billing", "technical", "account", "general"],
            priority_options=["low", "medium", "high", "urgent"],
            task_difficulty=task_difficulty,
            step_number=self.step_count,
            done=self.done,
            history=self.history,
            info=None,
            feedback=""
        )
    
    async def step(self, action: Dict[str, Any]) -> SupportActionResult:
        """Process an action and return observation and reward"""
        if self.done:
            # Auto-reset if done
            await self.reset(self.current_task_difficulty)
        
        self.step_count += 1
        
        # Get ground truth
        ground_truth_category = self.current_ticket.get('ground_truth_category', 'general')
        ground_truth_priority = self.current_ticket.get('ground_truth_priority', 'medium')
        keywords = self.current_ticket.get('keywords', [])
        
        # Get agent action
        agent_category = action.get('category', '')
        agent_priority = action.get('priority', '')
        agent_response = action.get('response_text', '')
        
        # Grade based on difficulty
        grader = get_grader(self.current_task_difficulty)
        
        if self.current_task_difficulty == "easy":
            score, feedback = grader(agent_category, ground_truth_category)
            priority_score = 0
            response_score = 0
        elif self.current_task_difficulty == "medium":
            score, feedback, priority_score = grader(
                agent_category, ground_truth_category,
                agent_priority, ground_truth_priority
            )
            response_score = 0
        else:  # hard
            score, feedback, priority_score, response_score = grader(
                agent_category, ground_truth_category,
                agent_priority, ground_truth_priority,
                agent_response, keywords
            )
        
        self.last_reward = score
        self.done = True
        
        # Record history
        self.history.append(f"classified-{agent_category} | priority={agent_priority} | response=\"{agent_response[:50]}...\"")
        
        observation = SupportObservation(
            ticket_id=self.current_ticket.get('id', 'T001'),
            customer_message=self.current_ticket.get('text', ''),
            category_options=["delivery", "billing", "technical", "account", "general"],
            priority_options=["low", "medium", "high", "urgent"],
            task_difficulty=self.current_task_difficulty,
            step_number=self.step_count,
            done=self.done,
            history=self.history,
            info=None,
            feedback=feedback
        )
        
        return SupportActionResult(
            observation=observation,
            reward=score,
            done=self.done,
            info={"feedback": feedback}
        )
    
    async def state(self) -> SupportState:
        """Get current state"""
        return SupportState(
            current_ticket_id=self.current_ticket.get('id') if self.current_ticket else None,
            current_ticket_text=self.current_ticket.get('text') if self.current_ticket else None,
            task_difficulty=self.current_task_difficulty,
            step_count=self.step_count,
            done=self.done,
            last_reward=self.last_reward,
            history=self.history
        )
    
    async def close(self):
        """Clean up resources"""
        pass
