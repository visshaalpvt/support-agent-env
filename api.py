from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import random
import json

from safe_grader import grade_easy, grade_medium, grade_hard, force_safe

app = FastAPI(title="SupportAgentEnv")

# Allow any origin for hackathon runner
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Ticket data ─────────────────────────────────────────────────────────────
# Load from tickets.json; inline fallback so the server never crashes.
try:
    with open("tickets.json", "r") as f:
        TICKETS = json.load(f).get("tickets", [])
except Exception:
    TICKETS = [
        {"id": "T001", "text": "My order has not arrived", "ground_truth_category": "delivery", "ground_truth_priority": "high", "keywords": ["order", "arrived"]},
        {"id": "T002", "text": "I was charged twice", "ground_truth_category": "billing", "ground_truth_priority": "urgent", "keywords": ["charge", "refund"]},
    ]

# Map old field names to new ones (backwards compat)
for t in TICKETS:
    if "category" in t and "ground_truth_category" not in t:
        t["ground_truth_category"] = t["category"]
    if "priority" in t and "ground_truth_priority" not in t:
        t["ground_truth_priority"] = t["priority"]

current_ticket: Optional[dict] = None
current_difficulty: str = "easy"


# ── Request models ──────────────────────────────────────────────────────────

class StepRequest(BaseModel):
    classification: str
    priority: Optional[str] = ""
    response: Optional[str] = ""


# ── Endpoints ───────────────────────────────────────────────────────────────

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
        "ticket_text": current_ticket.get("text", ""),
        "step_number": 0,
        "task_level": difficulty,
        "history": [],
        "done": False,
        "info": None,
    }


@app.post("/step")
async def step(request: StepRequest):
    global current_ticket, current_difficulty

    if current_ticket is None:
        return {
            "observation": {"ticket_id": "none", "ticket_text": "", "step_number": 1,
                            "task_level": current_difficulty, "history": [], "done": True, "info": {}},
            "reward": {"total": 0.15, "breakdown": "No ticket loaded — call /reset first"},
            "done": True,
        }

    agent_cat = (request.classification or "").strip().lower()
    agent_pri = (request.priority or "").strip().lower()
    agent_resp = (request.response or "").strip()

    truth_cat = current_ticket.get("ground_truth_category", "general")
    truth_pri = current_ticket.get("ground_truth_priority", "medium")
    keywords  = current_ticket.get("keywords", [])

    # ── Use safe_grader based on difficulty ──────────────────────────────
    if current_difficulty == "easy":
        score, feedback = grade_easy(agent_cat, truth_cat)
    elif current_difficulty == "medium":
        score, feedback, pri_score = grade_medium(agent_cat, truth_cat, agent_pri, truth_pri)
    else:  # hard
        score, feedback, pri_score, resp_score = grade_hard(
            agent_cat, truth_cat, agent_pri, truth_pri, agent_resp, keywords
        )

    # Final safety clamp
    score = force_safe(score)

    return {
        "observation": {
            "ticket_id": current_ticket["id"],
            "ticket_text": current_ticket.get("text", ""),
            "step_number": 1,
            "task_level": current_difficulty,
            "history": [f"classified-{agent_cat}"],
            "done": True,
            "info": {"feedback": feedback},
        },
        "reward": {
            "total": score,
            "breakdown": feedback,
        },
        "done": True,
    }


@app.get("/state")
async def state():
    return {
        "current_ticket_id": current_ticket["id"] if current_ticket else None,
        "current_ticket_text": current_ticket.get("text") if current_ticket else None,
        "task_difficulty": current_difficulty,
        "step_count": 1 if current_ticket else 0,
        "done": current_ticket is not None,
        "last_reward": 0.0,
        "history": [],
    }
