import asyncio
import os
import aiohttp
import sys
import math

# VERSION: 2026-04-08-OPENENV-COMPLIANT
# [COMPLIANCE] Using OpenAI SDK for all LLM calls (Rule #1)
# [COMPLIANCE] Using HF_TOKEN env var (Rule #4)
# [COMPLIANCE] Enforcing strictly lowercase booleans and null errors (Rule #3)
# [COMPLIANCE] Unified [END] format (Rule #2)

def clip_score(x):
    """Clip score to strictly between 0 and 1 (0.01 to 0.99)"""
    try:
        val = float(x)
    except Exception:
        return 0.01
    if val <= 0.0:
        return 0.01
    if val >= 1.0:
        return 0.99
    return max(0.01, min(0.99, val))

# ============================================
# COMPLIANCE: Mandatory Env Vars
# ============================================
try:
    API_BASE_URL = os.environ["API_BASE_URL"]
    HF_TOKEN     = os.environ["HF_TOKEN"]
except KeyError as e:
    sys.stderr.write(f"FATAL: Missing mandatory environment variable: {e}\n")
    # [COMPLIANCE] [END] format even for init failures
    print(f"[END] success=false steps=0 rewards=0.01", flush=True)
    sys.exit(1)

MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4.1-mini")
SPACE_URL  = os.getenv("SPACE_URL", "https://visshaalpvt-support-agent-env.hf.space")

# ============================================
# CLIENT INITIALIZATION
# ============================================
client = None
try:
    from openai import AsyncOpenAI
    # [COMPLIANCE] Using HF_TOKEN as api_key
    client = AsyncOpenAI(base_url=API_BASE_URL, api_key=HF_TOKEN)
except ImportError:
    sys.stderr.write("FATAL: openai package not installed.\n")
    print(f"[END] success=false steps=0 rewards=0.01", flush=True)
    sys.exit(1)
except Exception as e:
    sys.stderr.write(f"FATAL: OpenAI client init failed: {e}\n")
    print(f"[END] success=false steps=0 rewards=0.01", flush=True)
    sys.exit(1)

VALID_CATEGORIES = ["delivery", "billing", "technical", "account", "general"]
VALID_PRIORITIES = ["low", "medium", "high", "urgent"]

# ============================================
# PARSERS
# ============================================
def extract_category(raw_text: str) -> str:
    if not raw_text: return "general"
    raw = raw_text.strip().lower()
    if raw in VALID_CATEGORIES: return raw
    for cat in VALID_CATEGORIES:
        if cat in raw: return cat
    return "general"

def extract_priority(raw_text: str) -> str:
    if not raw_text: return "medium"
    raw = raw_text.strip().lower()
    if raw in VALID_PRIORITIES: return raw
    for pri in VALID_PRIORITIES:
        if pri in raw: return pri
    return "medium"

# ============================================
# LLM INTERACTION (Rule #1: Use OpenAI Client)
# ============================================
async def get_action_llm(messages, max_tokens=10):
    try:
        response = await client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            temperature=0.01,
            max_tokens=max_tokens
        )
        if response.choices and response.choices[0].message and response.choices[0].message.content:
            return response.choices[0].message.content.strip()
    except Exception as e:
        sys.stderr.write(f"WARN: LLM call failed: {e}\n")
    return ""

# ============================================
# TASK ENGINE
# ============================================
async def run_task(session: aiohttp.ClientSession, difficulty: str) -> float:
    task_name = f"support-{difficulty}"
    current_reward = 0.01
    step_count = 0
    action_str = "none"
    done = False
    last_error = "null"

    print(f"[START] task={task_name} env=SupportAgentEnv model={MODEL_NAME}", flush=True)

    try:
        # RESET
        async with session.post(f"{SPACE_URL}/reset", json={"task_difficulty": difficulty}) as resp:
            resp.raise_for_status()
            ticket = await resp.json()
            ticket_text = ticket.get("ticket_text", "")

        # LLM Logic (Classification)
        category = await get_action_llm([
            {"role": "system", "content": f"Classify into one: {', '.join(VALID_CATEGORIES)}. Output word only."},
            {"role": "user", "content": ticket_text}
        ])
        category = extract_category(category)
        
        priority = ""
        if difficulty in ["medium", "hard"]:
            res = await get_action_llm([
                {"role": "system", "content": f"Classify priority into one: {', '.join(VALID_PRIORITIES)}. Output word only."},
                {"role": "user", "content": ticket_text}
            ])
            priority = extract_priority(res)
            
        agent_response = ""
        if difficulty == "hard":
            agent_response = await get_action_llm([
                {"role": "system", "content": "Write a professional, empathetic customer response under 50 words."},
                {"role": "user", "content": ticket_text}
            ], max_tokens=100)

        # Action string
        if difficulty == "easy": action_str = category
        elif difficulty == "medium": action_str = f"{category}|{priority}"
        else: action_str = f"{category}|{priority}|response"

        # STEP
        async with session.post(f"{SPACE_URL}/step", json={
            "classification": category,
            "priority": priority,
            "response": agent_response
        }) as resp:
            resp.raise_for_status()
            data = await resp.json()
            
            raw_data = data.get("reward", {})
            if isinstance(raw_data, dict):
                current_reward = float(raw_data.get("total", 0.01))
            else:
                current_reward = float(raw_data)
            
            done = bool(data.get("done", False))
            # [COMPLIANCE] Ensure error is 'null' if not present
            last_error = data.get("last_action_error") or "null"
            step_count = 1

    except Exception as e:
        last_error = str(e).replace('\n', ' ')
        step_count = 1
        current_reward = 0.01

    finally:
        # [STEP] format validation (Rule #3)
        final_step_reward = clip_score(current_reward)
        is_done_str = "true" if done else "false"
        print(f"[STEP] step={step_count} action={action_str} reward={final_step_reward:.2f} done={is_done_str} error={last_error}", flush=True)

    return final_step_reward

async def main():
    all_rewards = []
    total_steps = 0
    success = True
    
    try:
        async with aiohttp.ClientSession() as session:
            for diff in ["easy", "medium", "hard"]:
                rew = await run_task(session, diff)
                all_rewards.append(f"{rew:.2f}")
                total_steps += 1
    except Exception as e:
        sys.stderr.write(f"FATAL: {e}\n")
        success = False
        if not all_rewards: all_rewards = ["0.01"]

    # [COMPLIANCE] [END] Format (Rule #2)
    rew_str = ",".join(all_rewards)
    succ_str = "true" if success else "false"
    print(f"[END] success={succ_str} steps={total_steps} rewards={rew_str}", flush=True)

if __name__ == "__main__":
    asyncio.run(main())