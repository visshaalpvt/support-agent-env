from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, Dict, Any
import json
import random
from support_env import SupportAgentEnv
from schema import SupportAction, SupportObservation

app = FastAPI(title="SupportAgentEnv", description="Customer Support Environment for OpenEnv")

env = SupportAgentEnv()

class ResetRequest(BaseModel):
    task_difficulty: str = "easy"

class StepRequest(BaseModel):
    classification: str
    priority: Optional[str] = ""
    response: Optional[str] = ""

@app.get("/")
async def root():
    """Serve the frontend UI"""
    with open("templates/index.html", "r") as f:
        return HTMLResponse(content=f.read())

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "ok", "tickets_loaded": len(env.tickets)}

@app.post("/reset")
async def reset(request: ResetRequest):
    """Reset environment and get initial observation"""
    obs = await env.reset(task_difficulty=request.task_difficulty)
    return {
        "ticket_id": obs.ticket_id,
        "ticket_text": obs.customer_message,
        "step_number": obs.step_number,
        "task_level": obs.task_difficulty,
        "history": obs.history,
        "done": obs.done,
        "info": obs.info
    }

@app.post("/step")
async def step(request: StepRequest):
    """Submit an action and get reward"""
    action = {
        "category": request.classification,
        "priority": request.priority or "",
        "response_text": request.response or ""
    }
    result = await env.step(action)
    return {
        "observation": {
            "ticket_id": result.observation.ticket_id,
            "ticket_text": result.observation.customer_message,
            "step_number": result.observation.step_number,
            "task_level": result.observation.task_difficulty,
            "history": result.observation.history,
            "done": result.done,
            "info": result.info
        },
        "reward": {
            "total": result.reward.total,
            "classification_score": result.reward.classification_score,
            "priority_score": result.reward.priority_score,
            "response_score": result.reward.response_score,
            "penalty": 0,
            "breakdown": result.reward.breakdown
        },
        "done": result.done
    }

@app.get("/state")
async def get_state():
    """Get current environment state"""
    state = await env.state()
    return state
