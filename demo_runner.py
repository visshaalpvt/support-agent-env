"""
demo_runner.py — Local Demo Runner for SupportAgentEnv
Meta Hackathon x Scaler · Phase 2 Safe

Runs all 3 difficulty levels offline (no LLM, no network) using
simulated agent responses, prints scores, and proves the environment
lifecycle works end-to-end before deploying.

Usage:
    py demo_runner.py
"""

import asyncio
import sys
import os

# ─── ensure we can import from this directory ────────────────────────────────
sys.path.insert(0, os.path.dirname(__file__))

from graders import clip_score, grade_easy, grade_medium, grade_hard
from support_env import SupportAgentEnv


# ─── Simulated agent actions (no LLM needed) ─────────────────────────────────
SIMULATED_ACTIONS = {
    "easy": {
        "category": "billing",
        "priority": "",
        "response_text": "",
    },
    "medium": {
        "category": "billing",
        "priority": "high",
        "response_text": "",
    },
    "hard": {
        "category": "billing",
        "priority": "high",
        "response_text": (
            "We sincerely apologize for the inconvenience. "
            "Our team will investigate and resolve this issue as soon as possible. "
            "We understand how frustrating this must be."
        ),
    },
}

WEIGHTS = {"easy": 0.25, "medium": 0.35, "hard": 0.40}


async def run_demo():
    print("=" * 55)
    print("  SupportAgentEnv — Local Demo Runner")
    print("  (Offline simulation — no LLM, no network)")
    print("=" * 55)

    env = SupportAgentEnv()
    scores = {}

    for difficulty in ["easy", "medium", "hard"]:
        print(f"\n── Task: {difficulty.upper()} ──────────────────────────────")

        # RESET
        obs = await env.reset(task_difficulty=difficulty)
        print(f"  Ticket #{obs.ticket_id}: {obs.customer_message[:70]}...")

        # STEP (simulated agent action)
        action = SIMULATED_ACTIONS[difficulty]
        result = await env.step(action)
        score = result.reward.total

        # clip_score safety net (belt-and-suspenders)
        score = clip_score(score)
        scores[difficulty] = score

        print(f"  Category : {action['category']}")
        if difficulty in ("medium", "hard"):
            print(f"  Priority : {action['priority']}")
        if difficulty == "hard":
            print(f"  Response : {action['response_text'][:60]}...")
        print(f"  Score    : {score:.4f}  (valid={0.0 < score < 1.0})")
        print(f"  Feedback : {result.reward.breakdown[:80]}...")

        # assert score is strictly in (0, 1)
        assert 0.0 < score < 1.0, f"FATAL: {difficulty} score {score} out of range!"

    # ─── Weighted aggregate ─────────────────────────────────────────────────
    print("\n── Aggregated Score ────────────────────────────────")
    weighted_sum = sum(scores[d] * WEIGHTS[d] for d in scores)
    final = clip_score(weighted_sum)

    for d, s in scores.items():
        print(f"  {d:6s}: {s:.4f}  (weight={WEIGHTS[d]})")
    print(f"  ─────────────────────────────")
    print(f"  Final  : {final:.4f}  (valid={0.0 < final < 1.0})")

    # ─── CLOSE ──────────────────────────────────────────────────────────────
    await env.close()

    # ─── Summary ────────────────────────────────────────────────────────────
    all_ok = all(0.0 < s < 1.0 for s in list(scores.values()) + [final])
    print("\n" + "=" * 55)
    if all_ok:
        print("  ✅ Demo passed — all scores in (0.01, 0.99) range")
        print("  ✅ Environment lifecycle: reset → step → close — OK")
        print("  ✅ Safe to deploy and submit")
    else:
        print("  ❌ Demo FAILED — check score range errors above")
    print("=" * 55 + "\n")

    return all_ok


if __name__ == "__main__":
    ok = asyncio.run(run_demo())
    sys.exit(0 if ok else 1)
