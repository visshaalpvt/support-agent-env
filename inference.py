import asyncio
import os
import aiohttp
import sys
import math

# ============================================
# COMPLIANCE: Standalone clip_score (Bug #2)
# ============================================
def clip_score(x):
    """Guarantees score is strictly between 0.01 and 0.99"""
    try:
        val = float(x)
        if math.isnan(val): return 0.011
        if val != val: return 0.011 # Backup NaN guard
        return max(0.011, min(0.99, val))
    except (TypeError, ValueError):
        return 0.011

# ============================================
# COMPLIANCE: Mandatory Env Vars (Bug #3)
# ============================================
try:
    API_BASE_URL = os.environ["API_BASE_URL"]
    HF_TOKEN     = os.environ["HF_TOKEN"]
except KeyError as e:
    sys.stderr.write(f"FATAL: Missing mandatory environment variable: {e}\n")
    # Emit a safety [END] for the evaluator's ingestion
    print(f"[END] task=init score=0.011 steps=0", flush=True)
    sys.exit(1)

MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4.1-mini")
SPACE_URL  = os.getenv("SPACE_URL", "https://visshaalpvt-support-agent-env.hf.space")

# ============================================
# CLIENT INITIALIZATION
# ============================================
client = None
try:
    from openai import AsyncOpenAI
    client = AsyncOpenAI(base_url=API_BASE_URL, api_key=HF_TOKEN)
except ImportError:
    sys.stderr.write("FATAL: openai package not installed.\n")
    print(f"[END] task=init score=0.011 steps=0", flush=True)
    sys.exit(1)
except Exception as e:
    sys.stderr.write(f"FATAL: OpenAI client init failed: {e}\n")
    print(f"[END] task=init score=0.011 steps=0", flush=True)
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
# LLM INTERACTION
# ============================================
async def get_action_llm(messages, max_tokens=10):
    try:
        response = await client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            temperature=0.011, # Non-zero literal
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
    reward = 0.011
    step_count = 0
    action_str = "none"
    done = False
    last_error = "null"

    # [START] log
    print(f"[START] task={task_name} env=SupportAgentEnv model={MODEL_NAME}", flush=True)

    try:
        # RESET
        async with session.post(f"{SPACE_URL}/reset", json={"task_difficulty": difficulty}) as resp:
            resp.raise_for_status()
            ticket = await resp.json()
            ticket_text = ticket.get("ticket_text", "")

        # LLM Logic
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

        # Build action string
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
            
            raw_r = data.get("reward", {})
            if isinstance(raw_r, dict):
                reward = float(raw_r.get("total", 0.011))
            else:
                reward = float(raw_r)
            
            done = bool(data.get("done", False))
            last_error = data.get("last_action_error") or "null"
            step_count = 1

        # [STEP] log
        print(f"[STEP] step={step_count} action={action_str} reward={reward:.2f} done={'true' if done else 'false'} error={last_error}", flush=True)

    except Exception as e:
        last_error = str(e)
        step_count = 1
        print(f"[STEP] step={step_count} action=error reward=0.01 done=false error={last_error}", flush=True)
    
    finally:
        # [END] log - COMPLIANCE: Bug #1 fix
        score = clip_score(reward)
        print(f"[END] task={task_name} score={score:.2f} steps={step_count}", flush=True)
    
    return score

async def main():
    try:
        async with aiohttp.ClientSession() as session:
            # Phase 2 Evaluator expects sequential runs of easy -> medium -> hard
            for diff in ["easy", "medium", "hard"]:
                await run_task(session, diff)
    except Exception as e:
        sys.stderr.write(f"FATAL: main execution failed: {e}\n")
        # Safety log to ensure the validator sees a non-crashed END line
        print(f"[END] task=support-agent-env score=0.011 steps=1", flush=True)

if __name__ == "__main__":
    asyncio.run(main())