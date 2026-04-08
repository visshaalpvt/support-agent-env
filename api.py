from fastapi import FastAPI, Body
import os
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any
import json
import random
from support_env import SupportAgentEnv
from tasks.grader import clip_score
from schema import SupportAction, SupportObservation

app = FastAPI(title="SupportAgentEnv", description="Customer Support Environment for OpenEnv")

# ============================================
# CORS MIDDLEWARE (FIXES CROSS-ORIGIN ISSUES)
# ============================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    # Try multiple paths
    html_paths = [
        "templates/index.html",
        os.path.join(os.path.dirname(__file__), "templates", "index.html")
    ]
    
    for path in html_paths:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return HTMLResponse(content=f.read())
    
    # Fallback if file not found
    return HTMLResponse(content="""
    <!DOCTYPE html>
    <html>
    <head>
        <title>SupportAgentEnv</title>
        <style>
            body { font-family: Arial; max-width: 800px; margin: 50px auto; padding: 20px; }
            .card { background: #f5f5f5; padding: 20px; border-radius: 10px; }
            button { background: #007bff; color: white; padding: 10px; border: none; border-radius: 5px; cursor: pointer; }
        </style>
    </head>
    <body>
        <h1>🤖 SupportAgentEnv</h1>
        <div class="card">
            <h2>Customer Support Training Environment</h2>
            <p>API is running! Use <a href="/docs">/docs</a> for API documentation.</p>
            <button onclick="loadTicket()">Load Random Ticket</button>
            <div id="ticket"></div>
        </div>
        <script>
            async function loadTicket() {
                const response = await fetch('/reset', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({task_difficulty: 'easy'})
                });
                const data = await response.json();
                document.getElementById('ticket').innerHTML = `<p><strong>Ticket:</strong> ${data.ticket_text}</p>`;
            }
        </script>
    </body>
    </html>
    """)

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "ok", "tickets_loaded": len(env.tickets)}

# ============================================
# FIXED /reset ENDPOINT - Accepts empty body {}
# ============================================
@app.post("/reset")
async def reset(body: Dict[str, Any] = Body(default={})):
    """
    Reset environment. Accepts empty body {} or body with task_difficulty.
    Defaults to "easy" if not specified.
    """
    difficulty = body.get("task_difficulty", "easy")
    obs = await env.reset(task_difficulty=difficulty)
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
            "total": clip_score(result.reward.total),
            "classification_score": clip_score(result.reward.classification_score),
            "priority_score": clip_score(result.reward.priority_score),
            "response_score": clip_score(result.reward.response_score),
            "penalty": 0.001,
            "breakdown": result.reward.breakdown
        },
        "done": result.done,
        "last_action_error": None
    }

@app.get("/state")
async def get_state():
    """Get current environment state"""
    state = await env.state()
    return state
