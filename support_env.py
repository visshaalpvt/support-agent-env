import random
import json
from schema import SupportObservation, SupportActionResult, SupportState
from graders import get_grader

class SupportAgentEnv:
    def __init__(self):
        with open("tickets.json", "r") as f:
            data = json.load(f)
            self.tickets = data.get("tickets", [])
        self.current_ticket = None
        self.current_difficulty = "easy"
        self.step_count = 0
        self.done = False
        self.history = []
        self.last_reward = 0.0

    async def reset(self, task_difficulty="easy"):
        self.current_ticket = random.choice(self.tickets)
        self.current_difficulty = task_difficulty
        self.step_count = 0
        self.done = False
        self.history = []
        self.last_reward = 0.0
        return SupportObservation(
            ticket_id=self.current_ticket.get("id", ""),
            customer_message=self.current_ticket.get("text", ""),
            category_options=["delivery", "billing", "technical", "account", "general"],
            priority_options=["low", "medium", "high", "urgent"],
            task_difficulty=task_difficulty,
            step_number=0,
            done=False,
            history=[],
            feedback=""
        )

    async def step(self, action):
        self.step_count = 1
        self.done = True
        grader = get_grader(self.current_difficulty)
        category = action.get("category", "")
        truth_cat = self.current_ticket.get("ground_truth_category", "general")
        
        if self.current_difficulty == "easy":
            score, feedback = grader(category, truth_cat)
        elif self.current_difficulty == "medium":
            score, feedback, _ = grader(category, truth_cat, "", "")
        else:
            score, feedback, _, _ = grader(category, truth_cat, "", "", "", [])
        
        self.last_reward = score
        obs = SupportObservation(
            ticket_id=self.current_ticket.get("id", ""),
            customer_message=self.current_ticket.get("text", ""),
            category_options=[],
            priority_options=[],
            task_difficulty=self.current_difficulty,
            step_number=1,
            done=True,
            history=[f"classified-{category}"],
            feedback=feedback
        )
        return SupportActionResult(observation=obs, reward=score, done=True, info={})

    async def state(self):
        return SupportState(
            current_ticket_id=self.current_ticket.get("id") if self.current_ticket else None,
            current_ticket_text=self.current_ticket.get("text") if self.current_ticket else None,
            task_difficulty=self.current_difficulty,
            step_count=self.step_count,
            done=self.done,
            last_reward=self.last_reward,
            history=self.history
        )

    async def close(self):
        pass
