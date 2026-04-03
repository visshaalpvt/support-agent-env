---
title: SupportAgentEnv
emoji: 🤖
colorFrom: blue
colorTo: green
sdk: docker
pinned: false
app_file: api.py
---

# SupportAgentEnv

OpenEnv environment for training AI agents on customer support tasks.

## Tasks
- **Easy**: Ticket classification (5 categories)
- **Medium**: Classification + Priority detection  
- **Hard**: Classification + Priority + Empathetic response

## API Endpoints
- `POST /reset` - Start new episode
- `POST /step` - Submit action, get reward (0.0-1.0)
- `GET /state` - Get current state
- `GET /health` - Health check

## Deployment
```bash
docker build -t support-agent-env .
docker run -p 7860:7860 support-agent-env
```

## Live Demo
https://huggingface.co/spaces/visshaalpvt/support-agent-env

---

## Technical Architecture

### Observation Space
The environment returns an observation mapping the active episode state:
```python
{
    "ticket_id": "T005",        # Unique ID of the customer complaint
    "customer_message": "...",  # The text block the agent must analyze
    "task_difficulty": "easy",  # "easy" | "medium" | "hard"
    "category_options": [],     # Topography of allowed categories
    "priority_options": [],     # Topography of allowed priorities
    "step_number": 0,           # Tick counter
    "done": False,              # Episode termination status
    "history": []               # Array string of previously evaluated steps
}
```

### Action Space
The agent submits an action payload bounded by Pydantic parameters:
```python
{
    "classification": "billing", # Required: "delivery" | "billing" | "technical" | "account" | "general"
    "priority": "high",          # Required in Medium/Hard: "low" | "medium" | "high" | "urgent"
    "response_text": "..."       # Required in Hard: Raw string apology/resolution
}
```

---

## Baseline Inference Scores
These are the verified deterministic execution scores using public Frontier Models:

| Task Tier | Agent/Model | Expected Score Max |
|-----------|-------------|--------------------|
| **Easy**  | Static Baseline / Random | ~0.20 (20%) |
| **Easy**  | Qwen 72B Instruct | 1.00 (100%) |
| **Medium**| Qwen 72B Instruct | ~0.85 (85%) |
| **Hard**  | GPT-4o / Qwen 72B | ~0.80 - 0.95 |

---

## Agent Setup & Evaluation

**1. Pull and Install**
```bash
git clone https://github.com/visshaalpvt/support-agent-env.git
cd support-agent-env
pip install -r requirements.txt
```

**2. Test Execution Sandbox**
Run the inference script to boot a complete mock-evaluation loop.
```bash
export OPENAI_API_KEY="sk-..."
python inference.py
```
