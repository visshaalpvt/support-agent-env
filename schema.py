from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class SupportAction(BaseModel):
    category: str
    priority: Optional[str] = ""
    response_text: Optional[str] = ""

class SupportObservation(BaseModel):
    ticket_id: str
    customer_message: str
    category_options: List[str]
    priority_options: List[str]
    task_difficulty: str
    step_number: int
    done: bool
    history: List[str]
    info: Optional[Dict[str, Any]] = None
    feedback: str = ""

class SupportReward(BaseModel):
    total: float
    breakdown: str
    classification_score: Optional[float] = 0.01
    priority_score: Optional[float] = 0.01
    response_score: Optional[float] = 0.01

class SupportActionResult(BaseModel):
    observation: SupportObservation
    reward: SupportReward
    done: bool
    info: Optional[Dict[str, Any]] = None

class SupportState(BaseModel):
    current_ticket_id: Optional[str] = None
    current_ticket_text: Optional[str] = None
    task_difficulty: str = ""
    step_count: int = 0
    done: bool = False
    last_reward: float = 0.01
    history: List[str] = []
