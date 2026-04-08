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
### An RL Environment for Customer Support Ticket Intelligence

> **Meta PyTorch OpenEnv Hackathon Submission** — Built on the OpenEnv specification.
> The agent reads real customer complaint tickets, classifies their intent, determines urgency, and drafts professional responses — all graded deterministically.

🚀 **Live Space:** https://huggingface.co/spaces/visshaalpvt/support-agent-env
📂 **GitHub Repo:** https://github.com/visshaalpvt/support-agent-env

---

## 1. Problem Statement

Customer support teams process thousands of tickets daily. Misrouting a ticket — sending a billing complaint to the technical team, or treating an urgent outage as low priority — wastes time and damages customer trust.

**What the agent must solve:**
- **Input:** A raw customer support ticket (free-form text, 1–3 sentences)
- **Action:** Classify the ticket's category, determine its priority, and optionally draft an empathetic response
- **Expected output:** Structured classification matching the ground-truth label
- **Success criteria:** The agent earns ≥ 0.6 reward by correctly identifying the ticket's category (and priority/response at higher difficulties)

The environment covers 5 real-world categories (`delivery`, `billing`, `technical`, `account`, `general`) and 25 curated tickets with human-labeled ground truth — making evaluation reproducible and unambiguous.

---

## 2. Objective

The agent's goal is to correctly classify each support ticket into its ground-truth category, assign appropriate priority, and generate an empathetic response — maximizing cumulative reward across all three difficulty levels in a single-step episode.

**Measurable outcome:** Reward ∈ [0.0, 1.0] per episode, with success defined as reward ≥ 0.6.

---

## 3. Environment Overview

| Property | Value |
|:---------|:------|
| **Environment Name** | `SupportAgentEnv` |
| **Benchmark Domain** | Customer Support Automation (NLP/RL) |
| **Episode Type** | Single-step (one action per episode) |
| **Difficulty Levels** | Easy, Medium, Hard |
| **Ticket Pool** | 25 curated tickets across 5 categories |
| **Reward Range** | [0.0, 1.0] with partial credit |

### Episode Flow

```
RESET → observe ticket → LLM inference → STEP (submit action) → receive reward → DONE
```

### Step Flow (per difficulty)

| Phase | Easy | Medium | Hard |
|:------|:-----|:-------|:-----|
| Classify category | ✅ | ✅ | ✅ |
| Assign priority | ❌ | ✅ | ✅ |
| Generate response | ❌ | ❌ | ✅ |

### What the Agent Sees at Each Stage

**After `/reset`:**
```json
{
  "ticket_id": "T005",
  "ticket_text": "My invoice shows incorrect tax amount.",
  "task_level": "easy",
  "step_number": 0,
  "done": false,
  "history": []
}
```

**After `/step`:**
```json
{
  "observation": { "ticket_id": "T005", "done": true, ... },
  "reward": { "total": 1.0, "classification_score": 1.0, "priority_score": 0.0, "response_score": 0.0 },
  "done": true
}
```

---

## 4. Action Space

### Valid Actions

The agent submits a JSON payload to `/step`:

```json
{
  "classification": "billing",   // REQUIRED — one of 5 categories
  "priority":       "high",      // optional for easy; required for medium/hard
  "response":       "We're sorry for the confusion. Our team will investigate and resolve the billing discrepancy shortly."
                                 // optional for easy/medium; required for hard
}
```

### Valid Categories
```
delivery | billing | technical | account | general
```

### Valid Priorities
```
low | medium | high | urgent
```

### Example Valid Action (Hard)
```json
{
  "classification": "billing",
  "priority": "high",
  "response": "We sincerely apologize for the incorrect tax charge. Our billing team will investigate and resolve this within 24 hours."
}
```

### Example Invalid Action (will default to `general` / `medium`)
```json
{
  "classification": "payment issue",   // Not in enum — extracts closest match or defaults
  "priority": "asap"                   // Not in enum — defaults to "medium"
}
```

### Fallback Behavior
- If classification is not in the enum, the LLM extractor searches for partial matches; defaults to `"general"`
- If priority is not in the enum, defaults to `"medium"`
- If response is missing/empty in Hard mode, sentiment and actionability scores are 0

---

## 5. Observation Space

### Reset Observation (`POST /reset`)

| Field | Type | Description |
|:------|:-----|:------------|
| `ticket_id` | `string` | Unique ticket identifier (e.g. `"T005"`) |
| `ticket_text` | `string` | Raw customer complaint text |
| `task_level` | `string` | `"easy"` \| `"medium"` \| `"hard"` |
| `step_number` | `int` | Always `0` after reset |
| `done` | `bool` | Always `false` after reset |
| `history` | `list[str]` | Empty list after reset |

### Step Observation (`POST /step`)

Same fields as reset observation, plus:
- `done` is `true` (single-step episode ends immediately)
- `history` contains the last action taken
- `reward.breakdown` contains human-readable grading feedback

---

## 6. Reward Design

### Easy (Category Only)

| Outcome | Reward |
|:--------|:-------|
| Correct category | **1.0** |
| Wrong category | **0.0** |

### Medium (Category + Priority)

| Outcome | Reward |
|:--------|:-------|
| Correct category | **+0.5** |
| Correct priority | **+0.5** |
| Priority off by 1 level (too low) | **+0.25** |
| Priority off by 1 level (too high) | **+0.15** |
| Wrong priority (>1 off) | **+0.0** |

### Hard (Weighted Multi-Metric)

| Metric | Weight | Criteria |
|:-------|:-------|:---------|
| Category accuracy | **30%** | Exact match with ground truth |
| Priority / SLA | **30%** | Exact match (+0.3); ±1 level (+0.15); else 0 |
| Sentiment & Empathy | **20%** | Response contains: *sorry, apologize, regret, understand, frustrating* |
| Actionability | **20%** | Response contains ≥ 2 of: *resolve, help, investigate, team, fix, update, process, soon* (+0.2); 1 keyword (+0.1) |

**Reward scale:** 0.0 – 1.0 per episode.
**Success threshold:** `reward >= 0.6` → `success=true`

---

## 7. Termination Conditions

| Condition | Done | Notes |
|:----------|:-----|:------|
| Action submitted via `/step` | `true` | Single-step — always terminates after one action |
| Max steps reached | `true` | Max steps = 1 per difficulty |
| Server error / timeout | `true` | `done=false`, `reward=0.0` is logged |

The episode ends immediately after the first `/step` call at all difficulty levels. There is no multi-turn loop — the environment is single-step by design to isolate classification quality.

---

## 8. Grading Logic

Grading is fully deterministic — no randomness in scoring:

1. **Category match:** String equality between `agent_category` and `ground_truth_category`
2. **Priority scoring:** Rank-based comparison using `{urgent:4, high:3, medium:2, low:1}`; partial credit for ±1 rank difference
3. **Sentiment scoring:** Keyword presence check against a fixed empathy vocabulary list
4. **Actionability scoring:** Keyword count check against a fixed resolution vocabulary list

Ground truth labels are stored in `tickets.json` and are never exposed to the agent during inference. The grader in `graders.py` runs server-side, ensuring the agent cannot manipulate the score.

---

## 9. LLM Interface / Inference Flow

The `inference.py` script handles the full agent loop:

```
1. Read env vars: API_BASE_URL, API_KEY / HF_TOKEN, MODEL_NAME, SPACE_URL
2. Validate: raise ValueError if no API key found
3. Initialize: AsyncOpenAI(base_url=API_BASE_URL, api_key=effective_key)

For each difficulty in [easy, medium, hard]:
  a. Print [START]
  b. POST /reset → get ticket text
  c. LLM call → classify_ticket(ticket_text)           [ always ]
  d. LLM call → classify_priority(ticket_text, cat)    [ medium/hard ]
  e. LLM call → generate_response(ticket_text, ...)    [ hard only ]
  f. POST /step with action payload
  g. Parse reward from response
  h. Print [STEP]
  i. Print [END]
```

### Prompt Design

**Category classification prompt:**
> "Classify the following support ticket into exactly one of: delivery, billing, technical, account, general. Output ONLY the single category word."

**Priority prompt:**
> "Determine urgency: low, medium, high, urgent. Output ONLY the single priority word."

**Response generation prompt:**
> "Write a concise, empathetic, actionable response. Must include empathy words AND resolution words. Under 80 words."

### Invalid Output Handling
- LLM returns verbose text → `extract_category()` / `extract_priority()` scans for substring match
- LLM call raises exception → graceful fallback to `"general"` / `"medium"` / hardcoded empathetic response
- All LLM errors logged to `stderr` only (no stdout pollution)

---

## 10. Error Handling

| Failure Scenario | Behavior |
|:-----------------|:---------|
| `/reset` call fails | Continues with empty ticket; logs to stderr |
| LLM API call fails | Falls back to safe defaults; logs to stderr |
| `/step` call fails | `reward=0.0`, `done=false`; continues to `[END]` |
| Any top-level exception | Caught by outer `try/except`; always emits `[STEP]` + `[END]` |

**Critical:** `[END]` is always printed — it lives in a `finally` block that cannot be skipped.

---

## 11. Logging Format

All logs go to **stdout only**. Debug messages go to **stderr**.

### Required Format (exact)

```
[START] task=<task_name> env=<benchmark> model=<model_name>
[STEP] step=<n> action=<action_str> reward=<0.00> done=<true|false> error=<msg|null>
[END] success=<true|false> steps=<n> rewards=<r1,r2,...,rn>
```

### Rules
- `reward` → 2 decimal places (`0.00`, `1.00`, `0.85`)
- `done`, `success` → lowercase booleans (`true` / `false`)
- `error` → `null` if no error, otherwise the exception message
- `[END]` → always printed, even on exception (lives in `finally` block)
- No extra `print()` calls on stdout (use `sys.stderr` for debug)

### Example Output

```
[START] task=support-easy env=SupportAgentEnv model=gpt-4.1-mini
[STEP] step=1 action=billing reward=1.00 done=true error=null
[END] success=true steps=1 rewards=1.00

[START] task=support-medium env=SupportAgentEnv model=gpt-4.1-mini
[STEP] step=1 action=billing|high reward=0.85 done=true error=null
[END] success=true steps=1 rewards=0.85

[START] task=support-hard env=SupportAgentEnv model=gpt-4.1-mini
[STEP] step=1 action=billing|high|response reward=0.90 done=true error=null
[END] success=true steps=1 rewards=0.90
```

---

## 12. Dependencies

```
fastapi>=0.104.1       — REST API framework for the environment server
uvicorn>=0.24.0        — ASGI server
pydantic>=2.4.2        — Schema validation
python-multipart>=0.0.6 — File upload support (FastAPI req.)
openai>=1.6.1          — LLM client (required by hackathon)
aiohttp>=3.9.0         — Async HTTP client for inference.py
openenv-core>=0.2.0    — OpenEnv specification base
```

**Python version:** 3.11 (slim Docker image — minimizes RAM and build time)

All packages are chosen to fit within the **2 vCPU / 8 GB RAM** HF Space resource limit.

---

## 13. Deployment Requirements

| Requirement | Value |
|:------------|:------|
| **HF Space Name** | `visshaalpvt/support-agent-env` |
| **Space URL** | https://huggingface.co/spaces/visshaalpvt/support-agent-env |
| **SDK** | Docker |
| **Port** | 7860 |
| **Space Status** | Must be `Running` before submission |
| **Build Status** | Must be fully built (no failed layers) |

### Environment Variables (set in HF Space Secrets)

| Variable | Required | Default | Description |
|:---------|:---------|:--------|:------------|
| `API_KEY` | ✅ yes | — | LLM proxy API key (injected by evaluator) |
| `API_BASE_URL` | ✅ yes | `https://api.openai.com/v1` | LLM proxy base URL |
| `MODEL_NAME` | optional | `gpt-4.1-mini` | Model to use for inference |
| `HF_TOKEN` | ✅ yes | — | Hugging Face token (hackathon requirement) |
| `SPACE_URL` | optional | Deployed HF Space URL | Override target environment URL |

---

## 14. Submission Checklist

- [x] `inference.py` at project root
- [x] `requirements.txt` with all dependencies
- [x] `README.md` with full PRD
- [x] Deployed HF Space in **Running** state
- [x] `API_BASE_URL` read from environment variable
- [x] `API_KEY` / `HF_TOKEN` read from environment variable
- [x] `MODEL_NAME` read from environment with default
- [x] OpenAI Python client used for all LLM calls (`AsyncOpenAI`)
- [x] `[START]` / `[STEP]` / `[END]` format exact
- [x] `reward` formatted to 2 decimal places
- [x] Booleans lowercase (`true` / `false`)
- [x] `[END]` always printed (in `finally` block)
- [x] No hardcoded API keys
- [x] No fallback bypass logic
- [x] All 3 difficulty levels demonstrated
- [x] GitHub repo is public
- [x] Resource usage within 2 vCPU / 8 GB limit

---

## 15. Docker Build

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 7860
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "7860"]
```

```bash
# Local dev
docker build -t support-agent-env .
docker run -p 7860:7860 \
  -e API_KEY=your-key \
  -e API_BASE_URL=https://your-proxy/v1 \
  support-agent-env

# Run inference demo
python inference.py
```
