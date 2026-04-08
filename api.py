from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any
import random
import json

app = FastAPI(title="SupportAgentEnv")

# Simple in-memory tickets
TICKETS = [
    {"id": "T001", "text": "My order #12345 hasn't arrived yet. It's been 10 days.", "category": "delivery", "priority": "high"},
    {"id": "T002", "text": "I received the wrong item in my order.", "category": "delivery", "priority": "high"},
    {"id": "T003", "text": "How do I reset my password? I can't log in.", "category": "account", "priority": "medium"},
]

current_ticket = None
current_difficulty = "easy"

class StepRequest(BaseModel):
    classification: str
    priority: Optional[str] = ""
    response: Optional[str] = ""

@app.get("/")
async def root():
    return HTMLResponse(content="""
    <html>
        <head><title>SupportAgentEnv</title></head>
        <body style="font-family: Arial; max-width: 800px; margin: 50px auto; padding: 20px;">
            <h1>🤖 SupportAgentEnv</h1>
            <p>API is running! Use <a href="/docs">/docs</a> for API documentation.</p>
            <hr>
            <h3>Quick Test:</h3>
            <button onclick="test()">Load Random Ticket</button>
            <pre id="result"></pre>
            <script>
                async function test() {
                    const res = await fetch('/reset', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: '{"task_difficulty": "easy"}'});
                    const data = await res.json();
                    document.getElementById('result').innerHTML = JSON.stringify(data, null, 2);
                }
            </script>
        </body>
    </html>
    """)

@app.get("/health")
async def health():
    return {"status": "ok", "tickets_loaded": len(TICKETS)}

@app.post("/reset")
async def reset(body: Dict[str, Any] = None):
    global current_ticket, current_difficulty
    difficulty = "easy"
    if body and "task_difficulty" in body:
        difficulty = body["task_difficulty"]
    current_difficulty = difficulty
    current_ticket = random.choice(TICKETS)
    return {
        "ticket_id": current_ticket["id"],
        "ticket_text": current_ticket["text"],
        "step_number": 0,
        "task_level": difficulty,
        "history": [],
        "done": False,
        "info": None
    }

@app.post("/step")
async def step(request: StepRequest):
    global current_ticket
    # Simple scoring - always return a score between 0.01 and 0.99
    score = 0.75
    if request.classification == current_ticket["category"]:
        score = 0.99
    else:
        score = 0.01
    
    return {
        "observation": {
            "ticket_id": current_ticket["id"],
            "ticket_text": current_ticket["text"],
            "step_number": 1,
            "task_level": current_difficulty,
            "history": [f"classified-{request.classification}"],
            "done": True,
            "info": {"feedback": f"Score: {score}"}
        },
        "reward": {
            "total": score,
            "classification_score": 0.5 if request.classification == current_ticket["category"] else 0,
            "priority_score": 0,
            "response_score": 0,
            "penalty": 0,
            "breakdown": f"Category: {request.classification} vs expected {current_ticket['category']}"
        },
        "done": True
    }

@app.get("/state")
async def state():
    return {
        "current_ticket_id": current_ticket["id"] if current_ticket else None,
        "current_ticket_text": current_ticket["text"] if current_ticket else None,
        "task_difficulty": current_difficulty,
        "step_count": 1 if current_ticket else 0,
        "done": False,
        "last_reward": 0.0,
        "history": []
    }
