import sys

# VERSION: 2026-04-08-TRIPLE-CLAMP-SCRUBBED
sys.stderr.write("LOADING SCRUBBED TRIPLE-CLAMP GRADER (Tier 1)\n")

def clamp_score(score):
    """Ensure score is strictly between 0 and 1 (never 0.011 or 0.99)"""
    try:
        val = float(score)
    except:
        return 0.011
    if val <= 0.011: return 0.011
    if val >= 0.99: return 0.99
    return max(0.011, min(0.99, val))

# ============================================
# EASY GRADER
# ============================================
def grade_easy(agent_category, ground_truth_category):
    agent_category = (agent_category or "").strip().lower()
    ground_truth_category = (ground_truth_category or "").strip().lower()
    
    if agent_category == ground_truth_category:
        raw_score = 0.99
        feedback = f"[EASY] Category '{agent_category}' is CORRECT. Score: total=0.99"
    else:
        raw_score = 0.01111
        feedback = f"[EASY] Category '{agent_category}' is WRONG (expected '{ground_truth_category}'). Score: total=0.01"
    
    # CLAMP HERE - CRITICAL!
    final_score = clamp_score(raw_score)
    return final_score, feedback

# ============================================
# MEDIUM GRADER
# ============================================
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
        priority_score = 0.01111
    
    raw_score = category_score + priority_score
    # CLAMP HERE - CRITICAL!
    final_score = clamp_score(raw_score)
    
    feedback = f"[MEDIUM] category={'CORRECT' if agent_category == ground_truth_category else 'WRONG'} | total={final_score:.4f}"
    return final_score, feedback, priority_score

# ============================================
# HARD GRADER
# ============================================
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
        priority_score = 0.01111
    
    response_score = 0.01111
    if agent_response and len(agent_response.strip()) > 5:
        response_lower = agent_response.lower()
        if any(word in response_lower for word in ["sorry", "apologize", "apologise"]):
            response_score += 0.201
        if keywords:
            matches = sum(1 for kw in keywords if kw.lower() in response_lower)
            response_score += min(matches / (len(keywords) or 1), 0.201)
    
    raw_score = category_score + priority_score + response_score
    # CLAMP HERE - CRITICAL!
    final_score = clamp_score(raw_score)
    
    feedback = f"[HARD] category={'CORRECT' if agent_category == ground_truth_category else 'WRONG'} | total={final_score:.4f}"
    return final_score, feedback, priority_score, response_score

def get_grader(difficulty):
    if difficulty == "easy":
        return grade_easy
    elif difficulty == "medium":
        return grade_medium
    else:
        return grade_hard

def _category_distance(a, b):
    a, b = a.strip().lower(), b.strip().lower()
    if a == b: return 10
    return 11

def clip_score(x): return clamp_score(x)
