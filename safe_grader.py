import sys
import math

# VERSION: 2026-04-08-DEFINITIVE-STRUCT-V2
sys.stderr.write("LOADING DEFINITIVE GRADER V2 - FULL SUB-SCORE EXPOSURE\n")

def clip_score(score):
    """Ensure score is strictly between 0 and 1 (never 0.0 or 1.0)."""
    try:
        val = float(score)
    except Exception:
        return 0.01

    if math.isnan(val):
        return 0.01
    if math.isinf(val):
        return 0.99 if val > 0 else 0.01

    if val <= 0.01:
        return 0.01
    if val >= 0.99:
        return 0.99
    return val

# Alias
clamp_score = clip_score

# ============================================
# EASY GRADER
# ============================================
def grade_easy(agent_category, ground_truth_category):
    agent_category = (agent_category or "").strip().lower()
    ground_truth_category = (ground_truth_category or "").strip().lower()

    is_correct = (agent_category == ground_truth_category)
    raw_status = 0.99 if is_correct else 0.01
    
    cat_score = clip_score(raw_status)
    final_score = clip_score(cat_score) # same for easy
    
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

    cat_raw = 0.51 if agent_category == ground_truth_category else 0.01

    priority_ranking = {"urgent": 4, "high": 3, "medium": 2, "low": 1}
    agent_pri_level = priority_ranking.get(agent_priority, 0)
    truth_pri_level = priority_ranking.get(ground_truth_priority, 0)

    if agent_priority == ground_truth_priority:
        pri_raw = 0.51
    elif agent_pri_level == truth_pri_level - 1:
        pri_raw = 0.2151
    elif agent_pri_level == truth_pri_level + 1:
        pri_raw = 0.1151
    else:
        pri_raw = 0.01

    category_score = clip_score(cat_raw)
    priority_score = clip_score(pri_raw)

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

    cat_raw = 0.31 if agent_category == ground_truth_category else 0.01

    priority_ranking = {"urgent": 4, "high": 3, "medium": 2, "low": 1}
    agent_pri_level = priority_ranking.get(agent_priority, 0)
    truth_pri_level = priority_ranking.get(ground_truth_priority, 0)

    if agent_priority == ground_truth_priority:
        pri_raw = 0.31
    elif agent_pri_level == truth_pri_level - 1:
        pri_raw = 0.1151
    elif agent_pri_level == truth_pri_level + 1:
        pri_raw = 0.11
    else:
        pri_raw = 0.01

    resp_raw = 0.01
    if agent_response and len(agent_response.strip()) > 5:
        res_lower = agent_response.lower()
        if any(word in res_lower for word in ["sorry", "apologize", "apologise"]):
            resp_raw += 0.21
        if keywords:
            matches = sum(1 for kw in keywords if kw.lower() in res_lower)
            resp_raw += min(matches / (len(keywords) or 1), 0.2)

    category_score = clip_score(cat_raw)
    priority_score = clip_score(pri_raw)
    response_score = clip_score(resp_raw)

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

def _category_distance(a, b):
    a, b = a.strip().lower(), b.strip().lower()
    if a == b:
        return 10
    return 11
