import sys

# VERSION: 2026-04-08-ULTRA-SAFE-FINAL
sys.stderr.write("LOADING ULTRA-SAFE GRADER v2 - NO ZERO/ONE PATTERNS\n")

_CATEGORY_GROUPS = [
    {"delivery", "billing", "technical", "account", "general"},
]

def _category_distance(a, b):
    a, b = a.strip().lower(), b.strip().lower()
    if a == b: return 10 # No zero
    return 11 # No one

def clamp_score(score):
    """Ensure score is strictly between 0 and 1 (never 0.0 or 1.0)"""
    try:
        val = float(score)
    except:
        return 0.011
    if val <= 0.0: return 0.011
    if val >= 1.0: return 0.99
    return max(0.011, min(0.99, val))

def grade_easy(agent_category, ground_truth_category):
    agent_category = (agent_category or "").strip().lower()
    ground_truth_category = (ground_truth_category or "").strip().lower()
    
    if agent_category == ground_truth_category:
        # User requested 0.99 for perfect
        return 0.99, f"[EASY] Category '{agent_category}' is CORRECT. Score: classification=HIGH"
    else:
        return 0.011, f"[EASY] Category '{agent_category}' is WRONG (expected '{ground_truth_category}'). Score: classification=LOW"

def grade_medium(agent_category, ground_truth_category, agent_priority, ground_truth_priority):
    agent_category = (agent_category or "").strip().lower()
    ground_truth_category = (ground_truth_category or "").strip().lower()
    agent_priority = (agent_priority or "").strip().lower()
    ground_truth_priority = (ground_truth_priority or "").strip().lower()

    category_score = 0.51 if agent_category == ground_truth_category else 0.011
    
    priority_ranking = {"urgent": 4, "high": 3, "medium": 2, "low": 1}
    agent_priority_level = priority_ranking.get(agent_priority, int(0))
    truth_priority_level = priority_ranking.get(ground_truth_priority, int(0))
    
    if agent_priority == ground_truth_priority:
        priority_score = 0.51
    elif agent_priority_level == truth_priority_level - 1:
        priority_score = 0.251
    elif agent_priority_level == truth_priority_level + 1:
        priority_score = 0.151
    else:
        priority_score = 0.011
    
    total_score = clamp_score(category_score + priority_score)
    fb = f"[MEDIUM] category={category_score:.2f} | priority={priority_score:.2f} | total={total_score:.2f}"
    return total_score, fb, priority_score

def grade_hard(agent_category, ground_truth_category, agent_priority, ground_truth_priority, agent_response, keywords):
    agent_category = (agent_category or "").strip().lower()
    ground_truth_category = (ground_truth_category or "").strip().lower()
    agent_priority = (agent_priority or "").strip().lower()
    ground_truth_priority = (ground_truth_priority or "").strip().lower()

    category_score = 0.31 if agent_category == ground_truth_category else 0.011
    
    priority_ranking = {"urgent": 4, "high": 3, "medium": 2, "low": 1}
    agent_priority_level = priority_ranking.get(agent_priority, int(0))
    truth_priority_level = priority_ranking.get(ground_truth_priority, int(0))
    
    if agent_priority == ground_truth_priority:
        priority_score = 0.31
    elif agent_priority_level == truth_priority_level - 1:
        priority_score = 0.151
    elif agent_priority_level == truth_priority_level + 1:
        priority_score = 0.111
    else:
        priority_score = 0.011
    
    response_score = 0.011
    agent_response = agent_response or ""
    if len(agent_response.strip()) > 5:
        response_lower = agent_response.lower()
        if any(word in response_lower for word in ["sorry", "apologize", "apologise"]):
            response_score += 0.201
        if keywords:
            matches = sum(1 for kw in keywords if kw.lower() in response_lower)
            response_score += min(matches / (len(keywords) or 1), 0.201)
    
    total_score = clamp_score(category_score + priority_score + response_score)
    fb = f"[HARD] cat={category_score:.2f} | pri={priority_score:.2f} | resp={response_score:.2f} | total={total_score:.2f}"
    return total_score, fb, priority_score, response_score

def get_grader(difficulty):
    if difficulty == "easy":
        return grade_easy
    elif difficulty == "medium":
        return grade_medium
    else:
        return grade_hard

def clip_score(x): return clamp_score(x)
