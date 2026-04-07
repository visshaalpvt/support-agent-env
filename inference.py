import asyncio
import os
import aiohttp
from openai import AsyncOpenAI

# ============================================
# MUST USE JUDGES' INJECTED ENVIRONMENT VARIABLES
# ============================================
API_BASE_URL = os.getenv("API_BASE_URL")
API_KEY = os.getenv("API_KEY") or os.getenv("HF_TOKEN")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4.1-mini")

# CRITICAL: These MUST exist, otherwise fail
if not API_BASE_URL or not API_KEY:
    raise ValueError("API_BASE_URL and API_KEY environment variables are required")

# Your Space URL (this is YOUR environment, not the LLM)
SPACE_URL = os.getenv("SPACE_URL", "https://visshaalpvt-support-agent-env.hf.space")

# Constants
TASK_NAME = "support-agent-env"
BENCHMARK = "SupportAgentEnv"

# Initialize client with THEIR proxy
client = AsyncOpenAI(base_url=API_BASE_URL, api_key=API_KEY)

# ============================================
# LLM FUNCTIONS - ACTUAL API CALLS VIA PROXY
# ============================================

async def get_classification(ticket_text: str) -> str:
    """Classify ticket via LLM proxy."""
    response = await client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {
                "role": "system",
                "content": "You are a support ticket classifier. Classify the ticket into exactly one category. Output ONLY one of these words: delivery, billing, technical, account, general"
            },
            {
                "role": "user",
                "content": f"Classify this support ticket:\n\n{ticket_text}"
            }
        ],
        temperature=0,
        max_tokens=10
    )
    result = response.choices[0].message.content.strip().lower()
    # Ensure we return a valid category
    valid = ["delivery", "billing", "technical", "account", "general"]
    for v in valid:
        if v in result:
            return v
    return "general"


async def get_priority(ticket_text: str) -> str:
    """Determine priority via LLM proxy."""
    response = await client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {
                "role": "system",
                "content": "You are a support ticket priority assessor. Output ONLY one of these words: urgent, high, medium, low"
            },
            {
                "role": "user",
                "content": f"Assess the priority of this support ticket:\n\n{ticket_text}"
            }
        ],
        temperature=0,
        max_tokens=10
    )
    result = response.choices[0].message.content.strip().lower()
    valid = ["urgent", "high", "medium", "low"]
    for v in valid:
        if v in result:
            return v
    return "medium"


async def get_response(ticket_text: str, category: str) -> str:
    """Generate empathetic response via LLM proxy."""
    response = await client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {
                "role": "system",
                "content": "You are a helpful, empathetic customer support agent. Write a brief, professional response (2-3 sentences) that acknowledges the issue, apologizes sincerely, and offers a concrete next step."
            },
            {
                "role": "user",
                "content": f"Category: {category}\n\nCustomer ticket:\n{ticket_text}\n\nWrite a helpful response:"
            }
        ],
        temperature=0.3,
        max_tokens=150
    )
    return response.choices[0].message.content.strip()


# ============================================
# MAIN EVALUATION LOOP
# ============================================

async def main():
    # Print START log - NO QUOTES around values
    print(f'[START] task={TASK_NAME} env={BENCHMARK} model={MODEL_NAME}')

    rewards = []

    async with aiohttp.ClientSession() as session:
        # ---- EASY ----
        async with session.post(
            f"{SPACE_URL}/reset",
            json={"task_difficulty": "easy"},
            timeout=aiohttp.ClientTimeout(total=30)
        ) as resp:
            ticket = await resp.json()
            ticket_text = ticket.get("ticket_text", "")

        category = await get_classification(ticket_text)

        async with session.post(
            f"{SPACE_URL}/step",
            json={"classification": category, "priority": "", "response": ""},
            timeout=aiohttp.ClientTimeout(total=30)
        ) as resp:
            data = await resp.json()
            reward = data.get("reward", {}).get("total", 0)
            rewards.append(reward)
            print(f'[STEP] step=1 action={category} reward={reward:.2f} done=false error=null')

        # ---- MEDIUM ----
        async with session.post(
            f"{SPACE_URL}/reset",
            json={"task_difficulty": "medium"},
            timeout=aiohttp.ClientTimeout(total=30)
        ) as resp:
            ticket = await resp.json()
            ticket_text = ticket.get("ticket_text", "")

        category = await get_classification(ticket_text)
        priority = await get_priority(ticket_text)

        async with session.post(
            f"{SPACE_URL}/step",
            json={"classification": category, "priority": priority, "response": ""},
            timeout=aiohttp.ClientTimeout(total=30)
        ) as resp:
            data = await resp.json()
            reward = data.get("reward", {}).get("total", 0)
            rewards.append(reward)
            print(f'[STEP] step=2 action={category},{priority} reward={reward:.2f} done=false error=null')

        # ---- HARD ----
        async with session.post(
            f"{SPACE_URL}/reset",
            json={"task_difficulty": "hard"},
            timeout=aiohttp.ClientTimeout(total=30)
        ) as resp:
            ticket = await resp.json()
            ticket_text = ticket.get("ticket_text", "")

        category = await get_classification(ticket_text)
        priority = await get_priority(ticket_text)
        response_text = await get_response(ticket_text, category)

        async with session.post(
            f"{SPACE_URL}/step",
            json={"classification": category, "priority": priority, "response": response_text},
            timeout=aiohttp.ClientTimeout(total=30)
        ) as resp:
            data = await resp.json()
            reward = data.get("reward", {}).get("total", 0)
            rewards.append(reward)
            print(f'[STEP] step=3 action={category},{priority},"{response_text[:50]}..." reward={reward:.2f} done=true error=null')

    # Print END log
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    final_score = sum(rewards) / len(rewards) if rewards else 0
    print(f'[END] success={str(final_score >= 0.6).lower()} steps={len(rewards)} score={final_score:.3f} rewards={rewards_str}')


if __name__ == "__main__":
    asyncio.run(main())
