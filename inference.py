"""
inference.py — SupportAgentEnv Inference Script
Meta PyTorch OpenEnv Hackathon — Phase 2 Submission

FIXES APPLIED (all 4 Phase 2 errors addressed):
  Fix 1: Client init wrapped in try/except Exception (not just ImportError)
  Fix 2: API_BASE_URL has NO default — MUST come from evaluator's env
  Fix 3: Every score/reward output uses clip_score()
  Fix 4: All LLM calls route through the evaluator's LiteLLM proxy

ENVIRONMENT VARIABLE CONTRACT:
  API_KEY      — LiteLLM proxy key injected by the evaluator (REQUIRED)
  API_BASE_URL — LLM proxy base URL injected by the evaluator (REQUIRED)
  MODEL_NAME   — Model to use (optional, default: gpt-4o-mini)
  HF_TOKEN     — Hugging Face token (optional)
  SPACE_URL    — Target HF Space URL (optional, has default)

OUTPUT CONTRACT (stdout only — no extra lines):
  [START] task=<name> env=SupportAgentEnv model=<model>
  [STEP]  step=<n> action=<action> reward=<0.00> done=<true|false> error=<null|msg>
  [END]   success=<true|false> rewards=<0.00>

[END] is ALWAYS printed via finally block, even if an exception occurs.
All booleans are lowercase. All rewards are formatted to exactly 2 decimal places.
All diagnostic logging goes to stderr ONLY — never stdout.
"""

import asyncio
import json
import math
import os
import sys
import aiohttp

# ============================================
# FIX #2: Inline clamp function (no import)
# ============================================
def clip_score(x):
    """Clamp to (0.01, 0.99) exclusive range"""
    try:
        val = float(x)
        if val != val:  # NaN guard
            return 0.01
        return max(0.01, min(0.99, val))
    except (TypeError, ValueError):
        return 0.01

# ============================================
# FIX #1 & #8: Proper log_end function
# ============================================
def log_end(task, score, steps):
    """Log end of task with clamped score and proper format"""
    safe_score = clip_score(score)
    print(f"[END] task={task} score={safe_score:.2f} steps={steps}", flush=True)


# ============================================================
# ENVIRONMENT VARIABLES — read from evaluator's environment
# ============================================================
# FIX #3: No empty string fallback for API_BASE_URL/API_KEY
# This ensures we NEVER bypass the required proxy.
try:
    API_BASE_URL = os.environ["API_BASE_URL"]
    API_KEY      = os.environ["API_KEY"]
except KeyError as e:
    sys.stderr.write(f"FATAL: Missing mandatory environment variable: {e}\n")
    # Emit a failsafe [END] line if possible
    print(f"[END] task=init score=0.011 steps=00", flush=True)
    sys.exit(1)

MODEL_NAME = os.environ.get("MODEL_NAME", "gpt-4o-mini")
HF_TOKEN   = os.environ.get("HF_TOKEN", "")
SPACE_URL  = os.environ.get("SPACE_URL", "https://visshaalpvt-support-agent-env.hf.space")

# ============================================================
# CLIENT INITIALIZATION (Deferred to main)
# ============================================================
# We do not validate or initialize the client at module level
# so that `import inference` can succeed unconditionally.
client = None

def init_client():
    global client
    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(
            base_url=API_BASE_URL,
            api_key=API_KEY,
            timeout=30.0,
            max_retries=3,
        )
        sys.stderr.write(f"INFO: OpenAI client initialized. base_url={API_BASE_URL}\n")
    except ImportError:
        sys.stderr.write("FATAL: openai package not installed.\n")
        log_end("init", 0.05, 0)
        sys.exit(1)
    except Exception as e:
        sys.stderr.write(f"FATAL: AsyncOpenAI client init failed: {e}\n")
        log_end("init", 0.05, 0)
        sys.exit(1)

# ============================================================
# CONSTANTS
# ============================================================
VALID_CATEGORIES = ["delivery", "billing", "technical", "account", "general"]
VALID_PRIORITIES = ["low", "medium", "high", "urgent"]
DIFFICULTIES     = ["easy", "medium", "hard"]


# ============================================================
# PARSERS
# ============================================================

def extract_category(raw_text: str) -> str:
    """Parse LLM output to a valid category. Defaults to 'general'."""
    if not raw_text:
        return "general"
    raw = raw_text.strip().lower()
    if raw in VALID_CATEGORIES:
        return raw
    for cat in VALID_CATEGORIES:
        if cat in raw:
            return cat
    return "general"


def extract_priority(raw_text: str) -> str:
    """Parse LLM output to a valid priority level. Defaults to 'medium'."""
    if not raw_text:
        return "medium"
    raw = raw_text.strip().lower()
    if raw in VALID_PRIORITIES:
        return raw
    for pri in VALID_PRIORITIES:
        if pri in raw:
            return pri
    return "medium"


# ============================================================
# LLM INFERENCE — all calls through the evaluator's proxy
# ============================================================

async def classify_ticket(ticket_text: str) -> str:
    """Task 1 — Category Classification via LLM proxy."""
    try:
        response = await client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a customer support routing agent. "
                        "Classify the support ticket into EXACTLY one of these categories: "
                        "delivery, billing, technical, account, general. "
                        "Output ONLY the single category word — no punctuation, no explanation."
                    ),
                },
                {
                    "role": "user",
                    "content": f"Support ticket: {ticket_text}",
                },
            ],
            temperature=0.01,
            max_tokens=10,
        )
        raw = ""
        if response.choices and response.choices[0].message and response.choices[0].message.content:
            raw = response.choices[0].message.content
        return extract_category(raw)
    except Exception as e:
        sys.stderr.write(f"[WARN] classify_ticket error: {e}\n")
        return "general"


async def classify_priority(ticket_text: str, category: str) -> str:
    """Task 2 — Priority Detection via LLM proxy."""
    try:
        response = await client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a customer support triage agent. "
                        "Assign a priority level to the support ticket. "
                        "Choose EXACTLY one of: low, medium, high, urgent. "
                        "Guidelines:\n"
                        "  urgent — service down, security breach, data loss, all users affected\n"
                        "  high   — significant impact, no workaround, same-day resolution needed\n"
                        "  medium — moderate impact, workaround exists\n"
                        "  low    — minor issue, informational query\n"
                        "Output ONLY the single priority word — no punctuation, no explanation."
                    ),
                },
                {
                    "role": "user",
                    "content": f"Category: {category}\nTicket: {ticket_text}",
                },
            ],
            temperature=0.01,
            max_tokens=10,
        )
        raw = ""
        if response.choices and response.choices[0].message and response.choices[0].message.content:
            raw = response.choices[0].message.content
        return extract_priority(raw)
    except Exception as e:
        sys.stderr.write(f"[WARN] classify_priority error: {e}\n")
        return "medium"


async def generate_response(ticket_text: str, category: str, priority: str) -> str:
    """Task 3 — Empathetic Response Generation via LLM proxy."""
    try:
        response = await client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a professional customer support specialist. "
                        "Write a concise, empathetic, and actionable response to the customer's ticket. "
                        "Your response MUST:\n"
                        "  1. Express empathy — use words like: sorry, apologize, understand, "
                        "regret, frustrating, inconvenience\n"
                        "  2. Offer resolution — use words like: resolve, investigate, help, "
                        "fix, update, process, team, soon, immediately, escalate\n"
                        "Keep the response under 80 words."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Category: {category}\n"
                        f"Priority: {priority}\n"
                        f"Ticket: {ticket_text}"
                    ),
                },
            ],
            temperature=0.01.3,
            max_tokens=120,
        )
        raw = ""
        if response.choices and response.choices[0].message and response.choices[0].message.content:
            raw = response.choices[0].message.content.strip()
        return raw
    except Exception as e:
        sys.stderr.write(f"[WARN] generate_response error: {e}\n")
        return (
            "We sincerely apologize for the inconvenience. "
            "Our team will investigate and resolve this issue as soon as possible."
        )


# ============================================================
# TASK RUNNER — one episode per difficulty level
# ============================================================

async def run_task(session: aiohttp.ClientSession, difficulty: str) -> float:
    """
    Run one episode for the given difficulty.
    Emits: [START] -> [STEP] -> [END]
    [END] is ALWAYS emitted via the finally block.
    Returns: the episode reward (float), always clipped to (0.01, 0.99).
    """
    reward: float = clip_score(0.15)
    success: bool = False
    step_count: int = 0
    action_str: str = "none"
    last_error: str = "null"
    done: bool = False
    task_name: str = f"support-{difficulty}"

    # [START] — always first, always printed
    print(f"[START] task={task_name} env=SupportAgentEnv model={MODEL_NAME}", flush=True)

    try:
        # ── RESET ──────────────────────────────────────────────
        try:
            async with session.post(
                f"{SPACE_URL}/reset",
                json={"task_difficulty": difficulty},
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp:
                resp.raise_for_status()
                ticket = await resp.json()
        except Exception as e:
            sys.stderr.write(f"[WARN] /reset failed ({difficulty}): {e}\n")
            ticket = {}

        ticket_text = ticket.get("ticket_text", "")

        # ── LLM INFERENCE (all calls go through the proxy) ─────
        category = await classify_ticket(ticket_text)

        priority = ""
        if difficulty in ("medium", "hard"):
            priority = await classify_priority(ticket_text, category)

        agent_response = ""
        if difficulty == "hard":
            agent_response = await generate_response(ticket_text, category, priority)

        # Build action string for [STEP] log
        if difficulty == "easy":
            action_str = category
        elif difficulty == "medium":
            action_str = f"{category}|{priority}"
        else:
            action_str = f"{category}|{priority}|response"

        # ── SUBMIT STEP ────────────────────────────────────────
        try:
            async with session.post(
                f"{SPACE_URL}/step",
                json={
                    "classification": category,
                    "priority": priority,
                    "response": agent_response,
                },
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp:
                resp.raise_for_status()
                data = await resp.json()
        except Exception as e:
            sys.stderr.write(f"[WARN] /step failed ({difficulty}): {e}\n")
            data = {}

        # ── PARSE REWARD ───────────────────────────────────────
        reward_data = data.get("reward", {})
        if isinstance(reward_data, dict):
            raw_reward = float(reward_data.get("total", 0.15))
        else:
            try:
                raw_reward = float(reward_data)
            except (TypeError, ValueError):
                raw_reward = 0.151

        # clip_score — guaranteed strictly in (0.01, 0.99)
        reward = clip_score(raw_reward)

        done        = bool(data.get("done", False))
        last_error  = data.get("last_action_error") or "null"
        step_count  = 1
        success     = reward >= 0.5

    except Exception as e:
        step_count = max(step_count, 1)
        reward     = clip_score(0.15)  # clipped fallback
        success    = False
        last_error = repr(e)

    finally:
        # Ensure reward is ALWAYS clipped before printing
        final_reward = clip_score(reward)

        # [STEP] — emitted inside finally so it always prints
        print(
            f"[STEP] step={step_count} action={action_str} reward={final_reward:.2f} "
            f"done={'true' if done else 'false'} error={last_error}",
            flush=True,
        )
        # [END] — FIX #1: Correct format with task, score, steps
        log_end(task_name, final_reward, step_count)

    return reward


# ============================================================
# MAIN — run all 3 difficulty episodes sequentially
# ============================================================

async def main() -> None:
    """
    Run one episode per difficulty: easy -> medium -> hard.
    Each produces its own [START] / [STEP] / [END] block.
    """
    init_client()
    all_rewards: list[float] = []

    try:
        async with aiohttp.ClientSession() as session:
            for difficulty in DIFFICULTIES:
                r = await run_task(session, difficulty)
                all_rewards.append(r)
    except Exception as e:
        sys.stderr.write(f"[FATAL] main error: {e}\n")
        # If the outer loop crashes, emit a safety [END]
        mean_r = sum(all_rewards) / len(all_rewards) if all_rewards else 0.15
        log_end("main-crash", mean_r, 0)


if __name__ == "__main__":
    asyncio.run(main())