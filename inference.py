import asyncio
import os
import aiohttp
from openai import AsyncOpenAI
from typing import List, Tuple

# ============================================
# ENVIRONMENT VARIABLES (read by judges)
# ============================================
API_BASE_URL = os.environ.get("API_BASE_URL", "https://api.openai.com/v1")
MODEL_NAME = os.environ.get("MODEL_NAME", "gpt-3.5-turbo")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
HF_TOKEN = os.environ.get("HF_TOKEN", "")

# Use whichever token is available
API_KEY = OPENAI_API_KEY or HF_TOKEN

# Your Space URL (can be overridden by env)
SPACE_URL = os.environ.get("SPACE_URL", "https://visshaalpvt-support-agent-env.hf.space")

# Constants
TASK_NAME = "support-agent-env"
BENCHMARK = "SupportAgentEnv"
SUCCESS_THRESHOLD = 0.6

# ============================================
# AI HELPER FUNCTIONS
# ============================================

async def get_classification(client: AsyncOpenAI, ticket_text: str) -> str:
    """Get category classification from AI"""
    try:
        response = await client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "You are a customer support classifier. Output ONLY one word: delivery, billing, technical, account, or general. Nothing else."},
                {"role": "user", "content": f"Classify this customer ticket:\n\n{ticket_text}\n\nCategory:"}
            ],
            temperature=0,
            max_tokens=10
        )
        result = response.choices[0].message.content.strip().lower()
        # Validate result
        valid_categories = ["delivery", "billing", "technical", "account", "general"]
        if result in valid_categories:
            return result
        return "general"
    except Exception as e:
        print(f"[DEBUG] Classification error: {e}", flush=True)
        return "general"

async def get_priority(client: AsyncOpenAI, ticket_text: str) -> str:
    """Get priority level from AI"""
    try:
        response = await client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "Output ONLY priority level: low, medium, high, or urgent. Nothing else."},
                {"role": "user", "content": f"Ticket:\n\n{ticket_text}\n\nPriority:"}
            ],
            temperature=0,
            max_tokens=10
        )
        result = response.choices[0].message.content.strip().lower()
        valid_priorities = ["low", "medium", "high", "urgent"]
        if result in valid_priorities:
            return result
        return "medium"
    except Exception as e:
        print(f"[DEBUG] Priority error: {e}", flush=True)
        return "medium"

async def get_response(client: AsyncOpenAI, ticket_text: str) -> str:
    """Get empathetic response from AI"""
    try:
        response = await client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "You are a customer support agent. Write a short, empathetic, helpful response to the customer. Include an apology and action plan. Keep it under 100 words."},
                {"role": "user", "content": f"Customer ticket:\n\n{ticket_text}\n\nYour response:"}
            ],
            temperature=0.7,
            max_tokens=150
        )
        result = response.choices[0].message.content.strip()
        if not result or len(result) < 10:
            return "I apologize for the issue. Let me help you resolve this right away."
        return result
    except Exception as e:
        print(f"[DEBUG] Response error: {e}", flush=True)
        return "I apologize for the inconvenience. Our team will assist you immediately."

# ============================================
# MAIN INFERENCE LOOP
# ============================================

async def test_difficulty(session: aiohttp.ClientSession, client: AsyncOpenAI, difficulty: str, step_num: int) -> Tuple[float, str]:
    """
    Test a single difficulty level
    Returns: (reward, action_description)
    """
    try:
        # Step 1: Reset environment with specific difficulty
        async with session.post(
            f"{SPACE_URL}/reset",
            json={"task_difficulty": difficulty},
            headers={"Content-Type": "application/json"}
        ) as resp:
            if resp.status != 200:
                raise Exception(f"Reset failed: HTTP {resp.status}")
            reset_data = await resp.json()
            ticket_text = reset_data.get("ticket_text", "")
        
        # Step 2: Get AI responses based on difficulty
        category = await get_classification(client, ticket_text)
        action_desc = category
        
        # Prepare step payload
        payload = {"classification": category, "priority": "", "response": ""}
        
        if difficulty == "medium":
            priority = await get_priority(client, ticket_text)
            payload["priority"] = priority
            action_desc = f"{category},{priority}"
        
        elif difficulty == "hard":
            priority = await get_priority(client, ticket_text)
            response_text = await get_response(client, ticket_text)
            payload["priority"] = priority
            payload["response"] = response_text
            action_desc = f"{category},{priority},\"{response_text[:50]}...\""
        
        # Step 3: Submit action to environment
        async with session.post(
            f"{SPACE_URL}/step",
            json=payload,
            headers={"Content-Type": "application/json"}
        ) as resp:
            if resp.status != 200:
                raise Exception(f"Step failed: HTTP {resp.status}")
            step_data = await resp.json()
            reward_data = step_data.get("reward", {})
            total_reward = reward_data.get("total", 0.0)
            
            # Extract detailed breakdown for logging
            breakdown = reward_data.get("breakdown", "")
            return total_reward, action_desc, breakdown
            
    except Exception as e:
        print(f"[DEBUG] Error testing {difficulty}: {e}", flush=True)
        return 0.0, f"error_{difficulty}"

# ============================================
# MAIN FUNCTION
# ============================================

async def main():
    # Initialize OpenAI client
    client = AsyncOpenAI(base_url=API_BASE_URL, api_key=API_KEY)
    
    # Store results
    rewards: List[float] = []
    actions: List[str] = []
    success = False
    
    # Print START log (REQUIRED FORMAT)
    print(f'[START] task="{TASK_NAME}" env="{BENCHMARK}" model="{MODEL_NAME}"')
    
    try:
        async with aiohttp.ClientSession() as session:
            # Test all three difficulties
            difficulties = ["easy", "medium", "hard"]
            
            print("-" * 50)
            for idx, difficulty in enumerate(difficulties, start=1):
                reward, action_desc, breakdown = await test_difficulty(session, client, difficulty, idx)
                rewards.append(reward)
                actions.append(action_desc)
                
                # Print STEP log with breakdown (REQUIRED FORMAT)
                # We put breakdown in the diagnostic part of the log
                print(f'[STEP] step={idx} action="{action_desc}" reward={reward:.2f} done=true error=null')
                if difficulty == "hard":
                    print(f"       Diagnostic: {breakdown}")
            print("-" * 50)

        # Calculate final score (average of all rewards)
        final_score = sum(rewards) / len(rewards) if rewards else 0.0
        success = final_score >= SUCCESS_THRESHOLD
        
    except Exception as e:
        print(f'[STEP] step=1 action="error" reward=0.0 done=true error="{str(e)}"')
        final_score = 0.0
        success = False
        rewards = [0.0, 0.0, 0.0]
    
    finally:
        # Print Summary Table
        print("\n" + "=" * 30)
        print("SupportAgentEnv Verification")
        print("=" * 30)
        print(f"Easy Tier:   {rewards[0] if len(rewards)>0 else 0.0:.2f}")
        print(f"Medium Tier: {rewards[1] if len(rewards)>1 else 0.0:.2f}")
        print(f"Hard Tier:   {rewards[2] if len(rewards)>2 else 0.0:.2f}")
        print("-" * 30)
        print(f"OVERALL:     {final_score:.3f} ({'PASS' if success else 'FAIL'})")
        print("=" * 30 + "\n")

        # Print END log (REQUIRED FORMAT)
        rewards_str = ",".join(f"{r:.2f}" for r in rewards)
        print(f'[END] success={str(success).lower()} steps={len(rewards)} score={final_score:.3f} rewards={rewards_str}')

# ============================================
# ENTRY POINT
# ============================================

if __name__ == "__main__":
    asyncio.run(main())
