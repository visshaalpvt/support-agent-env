import asyncio
import os
import sys
import aiohttp
from openai import AsyncOpenAI

# ============================================
# ENVIRONMENT VARIABLES (HACKATHON REQUIREMENT)
# ============================================
API_BASE_URL = os.getenv("API_BASE_URL", "https://api.openai.com/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4.1-mini")
HF_TOKEN = os.getenv("HF_TOKEN")
SPACE_URL = os.getenv("SPACE_URL", "https://visshaalpvt-support-agent-env.hf.space")

# CRITICAL: HF_TOKEN is REQUIRED by hackathon
if HF_TOKEN is None:
    raise ValueError("HF_TOKEN environment variable is required")

# Initialize OpenAI client with HF_TOKEN
client = AsyncOpenAI(base_url=API_BASE_URL, api_key=HF_TOKEN)

# Valid categories
VALID_CATEGORIES = ["delivery", "billing", "technical", "account", "general"]


def extract_category(raw_text: str) -> str:
    """Extract valid category from LLM output - handles messy responses"""
    if not raw_text:
        return "general"
    raw_lower = raw_text.strip().lower()
    if raw_lower in VALID_CATEGORIES:
        return raw_lower
    for cat in VALID_CATEGORIES:
        if cat in raw_lower:
            return cat
    return "general"


async def main():
    rewards: list[float] = []
    success = False
    step_count = 0
    category = "error"
    last_error = "null"
    done = False

    # [START] — printed once, unconditionally
    print(f"[START] task=support-agent-env env=SupportAgentEnv model={MODEL_NAME}")

    try:
        async with aiohttp.ClientSession() as session:

            # ========== RESET ENVIRONMENT ==========
            try:
                async with session.post(
                    f"{SPACE_URL}/reset",
                    json={"task_difficulty": "easy"},
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as resp:
                    resp.raise_for_status()
                    ticket = await resp.json()
            except Exception as e:
                print(f"[WARN] Reset failed: {e}", file=sys.stderr)
                ticket = {}

            ticket_text = ticket.get("ticket_text", "")

            # ========== LLM CLASSIFICATION ==========
            try:
                response = await client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "Classify the support ticket into one of these categories: "
                                "delivery, billing, technical, account, general. "
                                "Output ONLY the category name, nothing else."
                            ),
                        },
                        {"role": "user", "content": f"Ticket: {ticket_text}"},
                    ],
                    temperature=0,
                    max_tokens=10,
                )
                raw_category = ""
                if (
                    response.choices
                    and response.choices[0].message
                    and response.choices[0].message.content
                ):
                    raw_category = response.choices[0].message.content
            except Exception as e:
                print(f"[WARN] LLM call failed: {e}", file=sys.stderr)
                raw_category = "general"

            category = extract_category(raw_category)

            # ========== SUBMIT STEP ==========
            try:
                async with session.post(
                    f"{SPACE_URL}/step",
                    json={
                        "classification": category,
                        "priority": "",
                        "response": "",
                    },
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as resp:
                    resp.raise_for_status()
                    data = await resp.json()
            except Exception as e:
                print(f"[WARN] Step failed: {e}", file=sys.stderr)
                data = {}

            # Extract reward and done from response
            reward_data = data.get("reward", {})
            if isinstance(reward_data, dict):
                reward = float(reward_data.get("total", 0.0))
            else:
                try:
                    reward = float(reward_data)
                except (TypeError, ValueError):
                    reward = 0.0

            done = bool(data.get("done", False))
            last_error = data.get("last_action_error") or "null"
            step_count = 1
            rewards.append(reward)

            # [STEP] log
            print(
                f"[STEP] step=1 action={category} reward={reward:.2f} "
                f"done={str(done).lower()} error={last_error}"
            )

            success = reward >= 0.6

    except Exception as e:
        # Unexpected top-level error — emit STEP if not already done
        step_count = max(step_count, 1)
        if not rewards:
            rewards.append(0.0)
        print(
            f"[STEP] step={step_count} action={category} reward=0.00 "
            f"done=false error={str(e)}"
        )
        success = False

    finally:
        # [END] — rewards as comma-separated list, no score= field
        rewards_str = ",".join(f"{r:.2f}" for r in rewards) if rewards else "0.00"
        print(
            f"[END] success={str(success).lower()} steps={step_count} rewards={rewards_str}"
        )


if __name__ == "__main__":
    asyncio.run(main())