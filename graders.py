from typing import Tuple, List

def grade_easy(agent_category: str, ground_truth_category: str) -> Tuple[float, str]:
    """Easy: Only category matters"""
    if agent_category == ground_truth_category:
        return 1.0, f"[EASY] Category '{agent_category}' is CORRECT. Score: classification=1.0 | total=1.0"
    else:
        return 0.0, f"[EASY] Category '{agent_category}' is WRONG (expected '{ground_truth_category}'). Score: classification=0.0 | total=0.0"

def grade_medium(agent_category: str, ground_truth_category: str, 
                 agent_priority: str, ground_truth_priority: str) -> Tuple[float, str, float]:
    """Medium: Category (50%) + Priority (50%)"""
    category_score = 0.5 if agent_category == ground_truth_category else 0.0
    
    # Priority scoring with partial credit
    priority_ranking = {"urgent": 4, "high": 3, "medium": 2, "low": 1}
    agent_priority_level = priority_ranking.get(agent_priority, 0)
    truth_priority_level = priority_ranking.get(ground_truth_priority, 0)
    
    if agent_priority == ground_truth_priority:
        priority_score = 0.5
        priority_feedback = f"priority='{agent_priority}' CORRECT"
    elif agent_priority_level == truth_priority_level - 1:
        priority_score = 0.25
        priority_feedback = f"priority='{agent_priority}' WRONG (expected '{ground_truth_priority}') - One level off (+0.25)"
    elif agent_priority_level == truth_priority_level + 1:
        priority_score = 0.15
        priority_feedback = f"priority='{agent_priority}' WRONG (expected '{ground_truth_priority}') - One level too high (+0.15)"
    else:
        priority_score = 0.0
        priority_feedback = f"priority='{agent_priority}' WRONG (expected '{ground_truth_priority}') (+0.0)"
    
    total_score = category_score + priority_score
    feedback = f"[MEDIUM] category='{agent_category}' {'CORRECT (+0.5)' if agent_category == ground_truth_category else f'WRONG (expected {ground_truth_category}) (+0.0)'} | {priority_feedback} | total={total_score:.4f}"
    
    return total_score, feedback, priority_score

def grade_hard(agent_category: str, ground_truth_category: str,
               agent_priority: str, ground_truth_priority: str,
               agent_response: str, keywords: List[str]) -> Tuple[float, str, float, float]:
    """
    Hard: Category (30%) + Priority (30%) + Sentiment (20%) + Actionability (20%)
    Total Score: 1.0 (Sum of weighted metrics)
    """
    # 1. Category Metric (30%)
    category_score = 0.3 if agent_category == ground_truth_category else 0.0
    category_fb = f"category:CORRECT(+0.3)" if category_score > 0 else f"category:WRONG(exp:{ground_truth_category})"

    # 2. Priority Metric (30%) - Partial credit for "near misses"
    priority_ranking = {"urgent": 4, "high": 3, "medium": 2, "low": 1}
    agent_p = priority_ranking.get(agent_priority, 0)
    truth_p = priority_ranking.get(ground_truth_priority, 0)
    
    if agent_priority == ground_truth_priority:
        priority_score = 0.3
        priority_fb = f"priority:CORRECT(+0.3)"
    elif abs(agent_p - truth_p) == 1:
        priority_score = 0.15
        priority_fb = f"priority:NEAR_MISS(+0.15)"
    else:
        priority_score = 0.0
        priority_fb = f"priority:WRONG(exp:{ground_truth_priority})"

    # 3. Sentiment & Empathy Metric (20%)
    sentiment_score = 0.0
    empathy_keywords = ["sorry", "apologize", "regret", "understand", "frustrating", "apologise"]
    if agent_response:
        resp_lower = agent_response.lower()
        if any(word in resp_lower for word in empathy_keywords):
            sentiment_score = 0.2
            sentiment_fb = "sentiment:EMPATHETIC(+0.2)"
        else:
            sentiment_fb = "sentiment:NEUTRAL(+0.0)"
    else:
        sentiment_fb = "sentiment:MISSING(+0.0)"

    # 4. Actionability & Resolution Metric (20%)
    action_score = 0.0
    resolution_keywords = ["resolve", "help", "investigate", "team", "fix", "update", "process", "soon"]
    if agent_response:
        resp_lower = agent_response.lower()
        match_count = sum(1 for kw in resolution_keywords if kw in resp_lower)
        if match_count >= 2:
            action_score = 0.2
            action_fb = "action:HELPFUL(+0.2)"
        elif match_count == 1:
            action_score = 0.1
            action_fb = "action:PARTIAL(+0.1)"
        else:
            action_fb = "action:VAGUE(+0.0)"
    else:
        action_fb = "action:MISSING(+0.0)"

    total_score = round(category_score + priority_score + sentiment_score + action_score, 4)
    feedback = f"[HARD] {category_fb} | {priority_fb} | {sentiment_fb} | {action_fb} | total={total_score}"
    
    return total_score, feedback, priority_score, (sentiment_score + action_score)

def get_grader(difficulty: str):
    if difficulty == "easy":
        return grade_easy
    elif difficulty == "medium":
        return grade_medium
    else:
        return grade_hard
