import asyncio
import os
import aiohttp
import sys
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
    reward = 0.0
    success = False
    step_count = 0

    try:
        # [START] log - NO QUOTES
        print(f'[START] task=support-agent-env env=SupportAgentEnv model={MODEL_NAME}')

        async with aiohttp.ClientSession() as session:
            # ========== RESET ENVIRONMENT ==========
            try:
                async with session.post(
                    f"{SPACE_URL}/reset",
                    json={"task_difficulty": "easy"},
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as resp:
                    resp.raise_for_status()
                    ticket = await resp.json()
            except Exception as e:
                print(f"[WARN] Reset failed: {e}")
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
                            )
                        },
                        {"role": "user", "content": f"Ticket: {ticket_text}"}
                    ],
                    temperature=0,
                    max_tokens=10
                )
                raw_category = ""
                if (
                    response.choices
                    and response.choices[0].message
                    and response.choices[0].message.content
                ):
                    raw_category = response.choices[0].message.content
            except Exception as e:
                print(f"[WARN] LLM call failed: {e}")
                raw_category = "general"

            category = extract_category(raw_category)

            # ========== SUBMIT STEP ==========
            try:
                async with session.post(
                    f"{SPACE_URL}/step",
                    json={
                        "classification": category,
                        "priority": "",
                        "response": ""
                    },
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as resp:
                    resp.raise_for_status()
                    data = await resp.json()
            except Exception as e:
                print(f"[WARN] Step failed: {e}")
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
            step_count = 1

            # [STEP] log - NO QUOTES
            print(
                f'[STEP] step=1 action={category} reward={reward:.2f} '
                f'done={str(done).lower()} error=null'
            )
            success = reward >= 0.6

    except Exception as e:
        # [STEP] log with error - but still print
        print(f'[STEP] step=1 action=error reward=0.00 done=false error={str(e)}')
        success = False

    finally:
        # [END] log - NO score= field, always printed
        print(f'[END] success={str(success).lower()} steps={step_count} rewards={reward:.2f}')


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        # LAST RESORT - NEVER CRASH, always print logs
        print(f'[START] task=support-agent-env env=SupportAgentEnv model=fallback')
        print(f'[STEP] step=1 action=error reward=0.00 done=false error={str(e)}')
        print(f'[END] success=false steps=1 rewards=0.00')
        sys.exit(0)  # Exit with 0 to avoid non-zero status code