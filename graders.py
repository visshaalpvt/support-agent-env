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
    """Hard: Category (30%) + Priority (30%) + Response (40%)"""
    # Category (30%)
    category_score = 0.3 if agent_category == ground_truth_category else 0.0
    
    # Priority (30%)
    priority_ranking = {"urgent": 4, "high": 3, "medium": 2, "low": 1}
    agent_priority_level = priority_ranking.get(agent_priority, 0)
    truth_priority_level = priority_ranking.get(ground_truth_priority, 0)
    
    if agent_priority == ground_truth_priority:
        priority_score = 0.3
    elif agent_priority_level == truth_priority_level - 1:
        priority_score = 0.15
    elif agent_priority_level == truth_priority_level + 1:
        priority_score = 0.1
    else:
        priority_score = 0.0
    
    # Response (40%)
    response_score = 0.0
    apology_found = 0.0
    keyword_matches = 0.0
    
    if agent_response and len(agent_response.strip()) > 5:
        response_lower = agent_response.lower()
        apology_words = ["apologize", "sorry", "apologise", "regret", "understand", "frustrating"]
        
        for word in apology_words:
            if word in response_lower:
                apology_found = 0.2
                break
        
        if keywords:
            matches = sum(1 for kw in keywords if kw.lower() in response_lower)
            keyword_matches = min(matches / len(keywords), 0.2)
        else:
            keyword_matches = 0.1 if len(response_lower) > 20 else 0.05
        
        response_score = apology_found + keyword_matches
        response_score = min(response_score, 0.4)
    
    total_score = category_score + priority_score + response_score
    total_score = min(total_score, 1.0)
    
    feedback = f"[HARD] category='{agent_category}' {'CORRECT (+0.3)' if agent_category == ground_truth_category else 'WRONG (+0.0)'} | priority='{agent_priority}' {'CORRECT (+0.3)' if agent_priority == ground_truth_priority else f'WRONG (expected {ground_truth_priority}) (+{priority_score:.1f})'} | response: apology found {apology_found:.1f} | keywords matched {keyword_matches:.1f} (+{response_score:.1f}) | total={total_score:.4f}"
    
    return total_score, feedback, priority_score, response_score

def get_grader(difficulty: str):
    if difficulty == "easy":
        return grade_easy
    elif difficulty == "medium":
        return grade_medium
    else:
        return grade_hard
