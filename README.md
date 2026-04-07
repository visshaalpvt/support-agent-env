---
title: SupportAgentEnv
emoji: 🤖
colorFrom: blue
colorTo: green
sdk: docker
pinned: false
app_file: api.py
tags:
  - openenv
---

# SupportAgentEnv

**SupportAgentEnv** is a complete, real-world customer support automation environment built on the **OpenEnv** specification. 

### 💡 Motivation
Most reinforcement learning and agentic frameworks rely on games or synthetic "toy" tasks. **SupportAgentEnv** bridges the gap to industrial AI by simulating the actual workflow of a human customer support specialist: identifying customer needs, determining urgency based on service-level agreements (SLAs), and drafting professional, empathetic communications. This environment provides a verifiable benchmark for assessing an LLM agent's reasoning, classification accuracy, and tone alignment in a business context.

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

## Final Evaluation & Grading Strategy

To ensure a high-fidelity assessment of agentic behavior, we implement a **Weighted Partial-Reward Grader** for the 'Hard' tier:

| Metric | Weight | Description |
| :--- | :--- | :--- |
| **Category Accuracy** | 30% | Correct classification among 5 labels. |
| **Priority/SLA** | 30% | Alignment with ticket urgency (partial credit for 1-level offsets). |
| **Sentiment** | 20% | Detection of empathetic language (Professionalism & Empathy). |
| **Actionability** | 20% | Presence of resolution paths (Helpfulness & Clarity). |

### 🛠️ Environment Design
- **Single-Step Episodes**: Minimizes noise from long-horizon trajectories to isolate classification and response generation quality.
- **Dynamic Action Space**: Supports categorical strings (category/priority) and free-form raw text (responses).
- **Richer Info Logs**: Returns full ground truth metadata in the `info` object for transparency during training or testing.

## Baseline Inference Scores
These are verified deterministic execution scores using public Frontier Models:

| Task Tier | Agent/Model | Expected Score | Score Composition |
|-----------|-------------|----------------|-------------------|
| **Easy**  | GPT-4o / Qwen 2.5 | 1.00 | 100% Cat |
| **Medium**| GPT-4o / Qwen 2.5 | ~0.85 | 50% Cat + 35% Prio |
| **Hard**  | GPT-4o | ~0.90+ | Full multi-metric alignment |
| **Hard**  | Simple GPT-3.5 | ~0.60 | Misses nuance/empathy |

---

## Agent Setup & Evaluation

**1. Pull and Install**
```bash
git clone https://github.com/visshaalpvt/support-agent-env.git
cd support-agent-env
pip install -r requirements.txt
```

**2. Run the Demo (requires LLM proxy env vars)**
```bash
export API_BASE_URL="<your-proxy-url>"
export API_KEY="<your-api-key>"
export MODEL_NAME="gpt-4.1-mini"
python inference.py
```

> **Note:** The inference script requires `API_BASE_URL` and `API_KEY` environment variables.
> During hackathon evaluation, these are injected automatically by the judges' infrastructure.

