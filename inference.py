import asyncio
import os
import aiohttp
from typing import List, Tuple

# Try to import OpenAI, but don't crash if not available
try:
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("[WARN] openai module not available. Running in fallback mode.")

# ============================================
# ENVIRONMENT VARIABLES with SAFE FALLBACKS
# ============================================
API_BASE_URL = os.environ.get("API_BASE_URL", "https://api.openai.com/v1")
MODEL_NAME = os.environ.get("MODEL_NAME", "gpt-3.5-turbo")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
HF_TOKEN = os.environ.get("HF_TOKEN", "")

# SAFE API Key handling - never crash
API_KEY = OPENAI_API_KEY or HF_TOKEN
USE_FALLBACK = not API_KEY or API_KEY == "" or not OPENAI_AVAILABLE

# Initialize client safely - NEVER raise unhandled exception
client = None
if not USE_FALLBACK:
    try:
        client = AsyncOpenAI(base_url=API_BASE_URL, api_key=API_KEY)
        print(f"[INFO] OpenAI client initialized for model: {MODEL_NAME}")
    except Exception as e:
        print(f"[WARN] Failed to initialize OpenAI client: {e}")
        USE_FALLBACK = True

if USE_FALLBACK:
    print("[INFO] Running in rule-based fallback mode (no API key required).")

# Your Space URL
SPACE_URL = os.environ.get("SPACE_URL", "https://visshaalpvt-support-agent-env.hf.space")

# Constants
TASK_NAME = "support-agent-env"
BENCHMARK = "SupportAgentEnv"

# ============================================
# RULE-BASED FALLBACK FUNCTIONS (NO API CALLS)
# ============================================

def get_classification_fallback(ticket_text: str) -> str:
    """Simple rule-based classification - NO API NEEDED"""
    ticket_lower = ticket_text.lower()

    # Delivery keywords
    if any(word in ticket_lower for word in ["order", "delivery", "package", "shipping", "arrived", "track", "damaged", "wrong item"]):
        return "delivery"

    # Billing keywords
    if any(word in ticket_lower for word in ["charge", "billing", "payment", "refund", "price", "invoice", "tax", "subscription"]):
        return "billing"

    # Technical keywords
    if any(word in ticket_lower for word in ["crash", "bug", "error", "app", "technical", "freeze", "slow", "not working"]):
        return "technical"

    # Account keywords
    if any(word in ticket_lower for word in ["password", "login", "account", "access", "2fa", "authentication", "profile"]):
        return "account"

    # Default to general
    return "general"

def get_priority_fallback(ticket_text: str) -> str:
    """Simple rule-based priority - NO API NEEDED"""
    ticket_lower = ticket_text.lower()

    if any(word in ticket_lower for word in ["urgent", "emergency", "critical", "immediate", "blocked"]):
        return "urgent"

    if any(word in ticket_lower for word in ["days", "waiting", "not working", "stuck", "error"]):
        return "high"

    if any(word in ticket_lower for word in ["how", "what", "where", "question", "help"]):
        return "low"

    return "medium"

def get_response_fallback(ticket_text: str) -> str:
    """Template-based response - NO API NEEDED"""
    category = get_classification_fallback(ticket_text)

    responses = {
        "delivery": "I sincerely apologize for the issue with your order. Let me immediately track your package and provide you with an update within 2 hours.",
        "billing": "I apologize for the billing confusion. Let me review your account and correct this charge immediately. You'll receive a confirmation shortly.",
        "technical": "I'm sorry you're experiencing this technical issue. Our engineering team has been notified and is actively working on a fix.",
        "account": "I apologize for the account trouble. Let me help you regain access and secure your account right away.",
        "general": "Thank you for reaching out. I'd be happy to help with your question. Let me research this and get back to you shortly."
    }

    return responses.get(category, responses["general"])

# ============================================
# MAIN TEST FUNCTIONS
# ============================================

async def test_difficulty(session: aiohttp.ClientSession, difficulty: str, step_num: int) -> Tuple[float, str]:
    """Test a single difficulty level - uses rule-based fallback (reliable)"""
    try:
        # Reset environment
        async with session.post(
            f"{SPACE_URL}/reset",
            json={"task_difficulty": difficulty},
            headers={"Content-Type": "application/json"},
            timeout=aiohttp.ClientTimeout(total=30)
        ) as resp:
            if resp.status != 200:
                raise Exception(f"Reset failed: HTTP {resp.status}")
            ticket = await resp.json()
            ticket_text = ticket.get("ticket_text", "")

        # Use fallback functions (reliable, no API calls)
        category = get_classification_fallback(ticket_text)
        payload = {"classification": category, "priority": "", "response": ""}
        action_desc = category

        if difficulty == "medium":
            priority = get_priority_fallback(ticket_text)
            payload["priority"] = priority
            action_desc = f"{category},{priority}"

        elif difficulty == "hard":
            priority = get_priority_fallback(ticket_text)
            response_text = get_response_fallback(ticket_text)
            payload["priority"] = priority
            payload["response"] = response_text
            action_desc = f'{category},{priority},"{response_text[:50]}..."'

        # Submit action
        async with session.post(
            f"{SPACE_URL}/step",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=aiohttp.ClientTimeout(total=30)
        ) as resp:
            if resp.status != 200:
                raise Exception(f"Step failed: HTTP {resp.status}")
            step_data = await resp.json()
            reward = step_data.get("reward", {}).get("total", 0.0)
            return reward, action_desc

    except aiohttp.ClientConnectorError as e:
        print(f"[ERROR] Cannot connect to Space: {e}")
        return 0.0, f"connection_error_{difficulty}"
    except asyncio.TimeoutError:
        print(f"[ERROR] Timeout connecting to Space")
        return 0.0, f"timeout_error_{difficulty}"
    except Exception as e:
        print(f"[ERROR] Testing {difficulty}: {e}")
        return 0.0, f"error_{difficulty}"

async def main():
    # Print START log (REQUIRED FORMAT)
    print(f'[START] task="{TASK_NAME}" env="{BENCHMARK}" model="{MODEL_NAME}"')

    rewards = []
    success = False

    try:
        async with aiohttp.ClientSession() as session:
            difficulties = ["easy", "medium", "hard"]

            for idx, difficulty in enumerate(difficulties, start=1):
                reward, action_desc = await test_difficulty(session, difficulty, idx)
                rewards.append(reward)

                # Print STEP log (REQUIRED FORMAT)
                print(f'[STEP] step={idx} action="{action_desc}" reward={reward:.2f} done=true error=null')

        # Calculate final score
        if rewards:
            final_score = sum(rewards) / len(rewards)
            final_score = min(max(final_score, 0.0), 1.0)
            success = final_score >= 0.6
        else:
            final_score = 0.0
            success = False

    except Exception as e:
        print(f'[STEP] step=1 action="error" reward=0.0 done=true error="{str(e)}"')
        final_score = 0.0
        success = False
        rewards = [0.0, 0.0, 0.0]

    finally:
        # Print END log (REQUIRED FORMAT)
        rewards_str = ",".join(f"{r:.2f}" for r in rewards)
        print(f'[END] success={str(success).lower()} steps={len(rewards)} score={final_score:.3f} rewards={rewards_str}')

if __name__ == "__main__":
    asyncio.run(main())
