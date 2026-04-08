import math

# VERSION: 2026-04-08-DEFINITIVE-STRUCT-V6

def clamp_score(x):
    """OpenEnv requirement: scores must be strictly in (0.0, 1.0)"""
    try:
        val = float(x)
    except (ValueError, TypeError):
        return 0.01

    if math.isnan(val) or math.isinf(val):
        return 0.01

    if val <= 0.0:
        return 0.01
    if val >= 1.0:
        return 0.99
    return round(val, 3)

# Alias for compatibility
clip_score = clamp_score

# ============================================
# GRADE_EPISODE — Required by Meta validator
# ============================================
def grade_episode(total_reward, steps, num_sensors):
    if steps <= 0:
        return 0.01
    return clamp_score(total_reward)

# ============================================
# EASY GRADER
# ============================================
def grade_easy(agent_category, ground_truth_category):
    if agent_category == ground_truth_category:
        raw_score = 1.0
        feedback = f"[EASY] Category '{agent_category}' is CORRECT."
    else:
        raw_score = 0.0
        feedback = f"[EASY] Category '{agent_category}' is WRONG (expected '{ground_truth_category}')."
    
    final_score = clamp_score(raw_score)
    return final_score, feedback, final_score, 0.01, 0.01

# ============================================
# MEDIUM GRADER
# ============================================
def grade_medium(agent_category, ground_truth_category, agent_priority, ground_truth_priority):
    category_score = 0.5 if agent_category == ground_truth_category else 0.0
    
    priority_ranking = {"urgent": 4, "high": 3, "medium": 2, "low": 1}
    agent_level = priority_ranking.get(agent_priority, 0)
    truth_level = priority_ranking.get(ground_truth_priority, 0)
    
    if agent_priority == ground_truth_priority:
        priority_score = 0.5
    elif agent_level == truth_level - 1:
        priority_score = 0.25
    elif agent_level == truth_level + 1:
        priority_score = 0.15
    else:
        priority_score = 0.0
    
    raw_score = category_score + priority_score
    final_score = clamp_score(raw_score)
    
    fb = f"[MEDIUM] Cat={agent_category}, Pri={agent_priority} | Score={final_score}"
    return final_score, fb, clamp_score(category_score), clamp_score(priority_score), 0.01

# ============================================
# HARD GRADER
# ============================================
def grade_hard(agent_category, ground_truth_category, agent_priority, ground_truth_priority, agent_response, keywords):
    category_score = 0.3 if agent_category == ground_truth_category else 0.0
    
    priority_ranking = {"urgent": 4, "high": 3, "medium": 2, "low": 1}
    agent_level = priority_ranking.get(agent_priority, 0)
    truth_level = priority_ranking.get(ground_truth_priority, 0)
    
    if agent_priority == ground_truth_priority:
        priority_score = 0.3
    elif agent_level == truth_level - 1:
        priority_score = 0.15
    elif agent_level == truth_level + 1:
        priority_score = 0.1
    else:
        priority_score = 0.0
    
    response_score = 0.0
    if agent_response and len(agent_response.strip()) > 5:
        lower = agent_response.lower()
        if any(w in lower for w in ["sorry", "apologize"]):
            response_score += 0.2
        if keywords:
            matches = sum(1 for kw in keywords if kw.lower() in lower)
            response_score += min(matches / len(keywords), 0.2)
    
    raw_score = category_score + priority_score + response_score
    final_score = clamp_score(raw_score)
    
    fb = f"[HARD] total={final_score}"
    return final_score, fb, clamp_score(category_score), clamp_score(priority_score), clamp_score(response_score)

def get_grader(difficulty):
    if difficulty == "easy":
        return grade_easy
    elif difficulty == "medium":
        return grade_medium
    else:
        return grade_hard
