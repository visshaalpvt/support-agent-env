import sys
import math

# VERSION: 2026-04-08-DEFINITIVE-STRUCT-V3

def clip_score(score):
    """Ensure score is strictly between 0 and 1 (never 0.0 or 1.0)."""
    try:
        val = float(score)
    except Exception:
        return 0.001

    if math.isnan(val):
        return 0.001
    if math.isinf(val):
        return 0.999 if val > 0 else 0.001

    # Strictly clamp to (0.001, 0.999)
    if val <= 0.001:
        return 0.001
    if val >= 0.999:
        return 0.999
    return round(val, 6)

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
        return 0.001  # safe default for edge cases

    # In our multi-task env, total_reward is already the normalized score (0.001 to 0.999)
    # for a single-step episode.
    return clip_score(total_reward)

# ============================================
# EASY GRADER
# ============================================
def grade_easy(agent_category, ground_truth_category):
    agent_category = (agent_category or "").strip().lower()
    ground_truth_category = (ground_truth_category or "").strip().lower()

    is_correct = (agent_category == ground_truth_category)
    raw_status = 0.95 if is_correct else 0.05

    cat_score = clip_score(raw_status)
    final_score = clip_score(cat_score)

    # Return 5-tuple: (total, feedback, cat, pri, res)
    return final_score, f"[EASY] total={final_score:.2f}", cat_score, 0.01, 0.01

# ============================================
# MEDIUM GRADER
# ============================================
def grade_medium(agent_category, ground_truth_category, agent_priority, ground_truth_priority):
    agent_category = (agent_category or "").strip().lower()
    ground_truth_category = (ground_truth_category or "").strip().lower()
    agent_priority = (agent_priority or "").strip().lower()
    ground_truth_priority = (ground_truth_priority or "").strip().lower()

    cat_raw = 0.45 if agent_category == ground_truth_category else 0.05

    priority_ranking = {"urgent": 4, "high": 3, "medium": 2, "low": 1}
    agent_pri_level = priority_ranking.get(agent_priority, 0)
    truth_pri_level = priority_ranking.get(ground_truth_priority, 0)

    if agent_priority == ground_truth_priority:
        pri_raw = 0.45
    elif agent_pri_level == truth_pri_level - 1:
        pri_raw = 0.20
    elif agent_pri_level == truth_pri_level + 1:
        pri_raw = 0.10
    else:
        pri_raw = 0.05

    category_score = clip_score(cat_raw)
    priority_score = clip_score(pri_raw)

    # Sum is at most 0.45+0.45=0.90, safely within (0.01, 0.99)
    total_raw = category_score + priority_score
    final_score = clip_score(total_raw)

    fb = f"[MEDIUM] total={final_score:.4f}"
    # Return 5-tuple: (total, feedback, cat, pri, res)
    return final_score, fb, category_score, priority_score, 0.01

# ============================================
# HARD GRADER
# ============================================
def grade_hard(agent_category, ground_truth_category, agent_priority, ground_truth_priority, agent_response, keywords):
    agent_category = (agent_category or "").strip().lower()
    ground_truth_category = (ground_truth_category or "").strip().lower()
    agent_priority = (agent_priority or "").strip().lower()
    ground_truth_priority = (ground_truth_priority or "").strip().lower()

    cat_raw = 0.28 if agent_category == ground_truth_category else 0.05

    priority_ranking = {"urgent": 4, "high": 3, "medium": 2, "low": 1}
    agent_pri_level = priority_ranking.get(agent_priority, 0)
    truth_pri_level = priority_ranking.get(ground_truth_priority, 0)

    if agent_priority == ground_truth_priority:
        pri_raw = 0.28
    elif agent_pri_level == truth_pri_level - 1:
        pri_raw = 0.11
    elif agent_pri_level == truth_pri_level + 1:
        pri_raw = 0.10
    else:
        pri_raw = 0.05

    resp_raw = 0.05
    if agent_response and len(agent_response.strip()) > 5:
        res_lower = agent_response.lower()
        if any(word in res_lower for word in ["sorry", "apologize", "apologise"]):
            resp_raw += 0.18
        if keywords:
            matches = sum(1 for kw in keywords if kw.lower() in res_lower)
            resp_raw += min(matches / (len(keywords) or 1), 0.18)

    category_score = clip_score(cat_raw)
    priority_score = clip_score(pri_raw)
    response_score = clip_score(resp_raw)

    # Max total: 0.28+0.28+0.41=0.97, safely within (0.01, 0.99)
    total_raw = category_score + priority_score + response_score
    final_score = clip_score(total_raw)

    fb = f"[HARD] total={final_score:.4f}"
    # Return 5-tuple: (total, feedback, cat, pri, res)
    return final_score, fb, category_score, priority_score, response_score


def get_grader(difficulty):
    if difficulty == "easy":
        return grade_easy
    elif difficulty == "medium":
        return grade_medium
    else:
        return grade_hard
