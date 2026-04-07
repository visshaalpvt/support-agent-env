import asyncio
import os
import aiohttp
from openai import AsyncOpenAI

# ============================================
# MUST USE JUDGES' ENVIRONMENT VARIABLES - NO FALLBACKS!
# ============================================
API_BASE_URL = os.environ["API_BASE_URL"]
API_KEY = os.environ["API_KEY"]
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4.1-mini")

# Your Space URL - configurable via env
SPACE_URL = os.getenv("SPACE_URL", "https://visshaalpvt-support-agent-env.hf.space")

# Initialize client with THEIR proxy
client = AsyncOpenAI(base_url=API_BASE_URL, api_key=API_KEY)

# Valid categories
VALID_CATEGORIES = ["delivery", "billing", "technical", "account", "general"]

def extract_category(raw_text: str) -> str:
    """Extract valid category from potentially messy LLM output"""
    raw_lower = raw_text.strip().lower()
    # Check for exact match
    if raw_lower in VALID_CATEGORIES:
        return raw_lower
    # Check if any valid category appears in the text
    for cat in VALID_CATEGORIES:
        if cat in raw_lower:
            return cat
    # Default to general
    return "general"

async def main():
    # [START] log - NO QUOTES
    print(f'[START] task=support-agent-env env=SupportAgentEnv model={MODEL_NAME}')
    
    async with aiohttp.ClientSession() as session:
        # Step 1: Reset to get a ticket
        async with session.post(f"{SPACE_URL}/reset", json={"task_difficulty": "easy"}) as resp:
            ticket = await resp.json()
            ticket_text = ticket.get("ticket_text", "")
        
        # Step 2: Make LLM call through their proxy
        response = await client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "Classify into: delivery, billing, technical, account, general. Output ONLY the category name."},
                {"role": "user", "content": f"Ticket: {ticket_text}"}
            ],
            temperature=0,
            max_tokens=10
        )
        
        # Extract category with robust parsing
        raw_category = response.choices[0].message.content.strip().lower()
        category = extract_category(raw_category)
        
        # Step 3: Submit to environment
        async with session.post(f"{SPACE_URL}/step", json={"classification": category, "priority": "", "response": ""}) as resp:
            data = await resp.json()
            reward = data.get("reward", {}).get("total", 0)
            done = data.get("done", False)
            # [STEP] log printed IMMEDIATELY after env.step() returns
            print(f'[STEP] step=1 action={category} reward={reward:.2f} done={str(done).lower()} error=null')
    
    # [END] log - NO score= field
    success_str = "true" if reward >= 0.6 else "false"
    print(f'[END] success={success_str} steps=1 rewards={reward:.2f}')

if __name__ == "__main__":
    asyncio.run(main())