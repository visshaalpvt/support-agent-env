import asyncio
import os
import aiohttp
from openai import AsyncOpenAI

# Environment variables (read by judges)
API_BASE_URL = os.environ.get("API_BASE_URL", "https://api.openai.com/v1")
MODEL_NAME = os.environ.get("MODEL_NAME", "gpt-3.5-turbo")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
HF_TOKEN = os.environ.get("HF_TOKEN", "")
SPACE_URL = os.environ.get("SPACE_URL", "https://visshaalpvt-support-agent-env.hf.space")

# Use whichever token is available
API_KEY = OPENAI_API_KEY or HF_TOKEN

MAX_STEPS = 1
MAX_TOTAL_REWARD = 1.0
SUCCESS_SCORE_THRESHOLD = 0.7
TASK_NAME = "support-agent-env"
BENCHMARK = "SupportAgentEnv"

async def main():
    client = AsyncOpenAI(base_url=API_BASE_URL, api_key=API_KEY)
    
    history = []
    rewards = []
    steps_taken = 0
    score = 0.0
    success = False
    
    # Print START log (REQUIRED FORMAT)
    print(f'[START] task="{TASK_NAME}" env="{BENCHMARK}" model="{MODEL_NAME}"')
    
    try:
        async with aiohttp.ClientSession() as session:
            # Step 1: Reset environment
            async with session.post(
                f"{SPACE_URL}/reset",
                json={"task_difficulty": "easy"},
                headers={"Content-Type": "application/json"}
            ) as resp:
                if resp.status != 200:
                    raise Exception(f"Reset failed: {resp.status}")
                reset_data = await resp.json()
                ticket_text = reset_data.get("ticket_text", "")
            
            # Step 2: Get classification from OpenAI
            openai_response = await client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": "You are a customer support agent. Classify the ticket into one category: delivery, billing, technical, account, general. Respond with ONLY the category name, nothing else."},
                    {"role": "user", "content": f"Ticket: {ticket_text}\n\nCategory:"}
                ],
                temperature=0,
                max_tokens=10
            )
            action = openai_response.choices[0].message.content.strip().lower()
            
            # Step 3: Submit action to environment
            async with session.post(
                f"{SPACE_URL}/step",
                json={"classification": action, "priority": "", "response": ""},
                headers={"Content-Type": "application/json"}
            ) as resp:
                if resp.status != 200:
                    raise Exception(f"Step failed: {resp.status}")
                step_data = await resp.json()
                reward = step_data.get("reward", {}).get("total", 0.0)
                done = step_data.get("done", True)
                error = None
                
        rewards.append(reward)
        steps_taken = 1
        score = reward  # Since MAX_TOTAL_REWARD = 1.0
        success = score >= SUCCESS_SCORE_THRESHOLD
        
        # Print STEP log (REQUIRED FORMAT)
        print(f'[STEP] step=1 action="{action}" reward={reward} done={done} error={error}')
        
        history.append(f"Step 1: {action!r} -> reward {reward:+.2f}")
        
    except Exception as e:
        error_msg = str(e)
        print(f'[STEP] step=1 action="error" reward=0.0 done=true error="{error_msg}"')
        success = False
        steps_taken = 0
        score = 0.0
        rewards = [0.0]
    
    finally:
        # Print END log (REQUIRED FORMAT)
        print(f'[END] success={success} steps={steps_taken} score={score} rewards={rewards}')

if __name__ == "__main__":
    asyncio.run(main())
