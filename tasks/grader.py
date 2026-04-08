import math

# VERSION: 2026-04-08-FINAL-COMPLIANCE

def clamp_score(x):
    """Force score to be strictly between 0 and 1 (0.01 to 0.99)"""
    try:
        val = float(x)
    except:
        return 0.01
    
    if math.isnan(val) or math.isinf(val):
        return 0.01

    if val <= 0.0:
        return 0.01
    if val >= 1.0:
        return 0.99
    return round(val, 3)

# Alias
clip_score = clamp_score

def grade_episode(total_reward, steps, num_sensors):
    if steps <= 0:
        return 0.01
    return clamp_score(total_reward)

def grade_easy(agent_category, ground_truth_category):
    if agent_category == (ground_truth_category or "").strip().lower():
        score = 0.99
        feedback = "CORRECT"
    else:
        score = 0.01
        feedback = "WRONG"
    final = clamp_score(score)
    # returns: (total, feedback, cat, pri, resp)
    return final, feedback, final, 0.01, 0.01

def grade_medium(agent_category, ground_truth_category, agent_priority, ground_truth_priority):
    cat_score = 0.495 if agent_category == (ground_truth_category or "").strip().lower() else 0.01
    pri_score = 0.495 if agent_priority == (ground_truth_priority or "").strip().lower() else 0.01
    total = clamp_score(cat_score + pri_score)
    fb = f"Total={total}"
    return total, fb, clamp_score(cat_score), clamp_score(pri_score), 0.01

def grade_hard(agent_category, ground_truth_category, agent_priority, ground_truth_priority, agent_response, keywords):
    cat_score = 0.297 if agent_category == (ground_truth_category or "").strip().lower() else 0.01
    pri_score = 0.297 if agent_priority == (ground_truth_priority or "").strip().lower() else 0.01
    resp_score = 0.396 if (agent_response and len(agent_response) > 10) else 0.01
    total = clamp_score(cat_score + pri_score + resp_score)
    fb = f"Total={total}"
    return total, fb, clamp_score(cat_score), clamp_score(pri_score), clamp_score(resp_score)

def get_grader(difficulty):
    return {"easy": grade_easy, "medium": grade_medium, "hard": grade_hard}.get(difficulty, grade_easy)
