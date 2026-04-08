import sys
import math

# VERSION: 2026-04-08-DEFINITIVE-STRUCT-V5

MIN_SCORE = 0.01
MAX_SCORE = 0.99

def clip_score(score):
    """Ensure score is strictly between 0 and 1 (never 0.0 or 1.0)."""
    try:
        val = float(score)
    except Exception:
        return MIN_SCORE

    if math.isnan(val) or math.isinf(val):
        return MIN_SCORE

    # Strictly clamp to (0.01, 0.99)
    return max(MIN_SCORE, min(MAX_SCORE, val))

# Alias
clamp_score = clip_score

# ============================================
# GRADE_EPISODE — Required by Meta validator
# ============================================
def grade_episode(total_reward, steps, num_sensors):
    """
    Universal entry point called by Meta validator.
    Maps total_reward (cumulative) → final score in (0.001, 0.999).
    Since our environment returns normalized rewards (0-1) per step,
    and all tasks are 1 step, we just return the clipped reward.
    """
    if steps <= 0:
        return MIN_SCORE  # safe default for edge cases

    # In our multi-task env, total_reward is already the normalized score (0.001 to 0.999)
    # for a single-step episode.
    return clip_score(total_reward)

# ============================================
# EASY GRADER
# ============================================
def grade_easy(agent_category, ground_truth_category):
    agent_category = (agent_category or "").strip().lower()
    ground_truth_category = (ground_truth_category or "").strip().lower()
    cat_score = clip_score(0.95 if agent_category == ground_truth_category else 0.05)
    final_score = clip_score(cat_score)
    return final_score, f"[EASY] total={final_score:.4f}", cat_score, MIN_SCORE, MIN_SCORE

# ============================================
# MEDIUM GRADER
# ============================================
def grade_medium(agent_category, ground_truth_category, agent_priority, ground_truth_priority):
    agent_category = (agent_category or "").strip().lower()
    ground_truth_category = (ground_truth_category or "").strip().lower()
    agent_priority = (agent_priority or "").strip().lower()
    ground_truth_priority = (ground_truth_priority or "").strip().lower()
    cat_score = clip_score(0.45 if agent_category == ground_truth_category else 0.05)
    priority_ranking = {"urgent": 4, "high": 3, "medium": 2, "low": 1}
    ap = priority_ranking.get(agent_priority, 0)
    tp = priority_ranking.get(ground_truth_priority, 0)
    if agent_priority == ground_truth_priority:
        pri_raw = 0.45
    elif abs(ap - tp) == 1:
        pri_raw = 0.20
    else:
        pri_raw = 0.05
    pri_score = clip_score(pri_raw)
    final_score = clip_score(cat_score + pri_score)
    return final_score, f"[MEDIUM] total={final_score:.4f}", cat_score, pri_score, MIN_SCORE

# ============================================
# HARD GRADER
# ============================================
def grade_hard(agent_category, ground_truth_category, agent_priority, ground_truth_priority, agent_response, keywords):
    agent_category = (agent_category or "").strip().lower()
    ground_truth_category = (ground_truth_category or "").strip().lower()
    agent_priority = (agent_priority or "").strip().lower()
    ground_truth_priority = (ground_truth_priority or "").strip().lower()
    agent_response = (agent_response or "").strip().lower()
    cat_score = clip_score(0.40 if agent_category == ground_truth_category else 0.05)
    priority_ranking = {"urgent": 4, "high": 3, "medium": 2, "low": 1}
    ap = priority_ranking.get(agent_priority, 0)
    tp = priority_ranking.get(ground_truth_priority, 0)
    if agent_priority == ground_truth_priority:
        pri_raw = 0.35
    elif abs(ap - tp) == 1:
        pri_raw = 0.15
    else:
        pri_raw = 0.05
    pri_score = clip_score(pri_raw)
    if keywords:
        hits = sum(1 for kw in keywords if kw.lower() in agent_response)
        resp_raw = 0.10 + 0.20 * (hits / len(keywords))
    else:
        resp_raw = 0.15 if len(agent_response) > 20 else 0.05
    resp_score = clip_score(resp_raw)
    final_score = clip_score(cat_score + pri_score + resp_score)
    return final_score, f"[HARD] total={final_score:.4f}", cat_score, pri_score, resp_score

def get_grader(difficulty: str):
    return {"easy": grade_easy, "medium": grade_medium, "hard": grade_hard}.get(difficulty, grade_easy)
