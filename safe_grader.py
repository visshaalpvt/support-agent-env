"""
SAFE_GRADER.py - Standalone grader for Meta Hackathon
ALL scores forced to be strictly between 0 and 1 (0.01 to 0.99)
"""

import math
from typing import Tuple, List

# ============================================================
# FORCE SAFE SCORE - THE GOLDEN FUNCTION
# ============================================================

def force_safe(score, min_val: float = 0.01, max_val: float = 0.99) -> float:
    """NEVER returns 0.0 or 1.0. ALWAYS returns between 0.01 and 0.99"""
    if score is None or (isinstance(score, float) and math.isnan(score)):
        return min_val
    try:
        score = float(score)
    except (TypeError, ValueError):
        return min_val
    
    if score <= 0.0:
        return min_val
    if score >= 1.0:
        return max_val
    if score < min_val:
        return min_val
    if score > max_val:
        return max_val
    return score


# ============================================================
# CONSTANTS - ALL between 0.01 and 0.99
# ============================================================

SCORE_PERFECT = 0.95
SCORE_STRONG = 0.75
SCORE_PARTIAL = 0.45
SCORE_WEAK = 0.25
SCORE_FLOOR = 0.15

_CATEGORY_GROUPS = [
    {"billing", "account"},
    {"technical", "delivery"},
    {"general"},
]

_PRIORITY_RANK = {"urgent": 4, "high": 3, "medium": 2, "low": 1}

_EMPATHY_KEYWORDS = [
    "sorry", "apologize", "apologise", "regret",
    "understand", "frustrating", "inconvenience", "sincerely",
]

_RESOLUTION_KEYWORDS = [
    "resolve", "investigate", "fix", "help", "update",
    "process", "team", "soon", "immediately", "escalate",
]


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def _category_distance(a: str, b: str) -> int:
    if a == b:
        return 10  # distance 0
    for group in _CATEGORY_GROUPS:
        if a in group and b in group:
            return 11  # distance 1
    return 12      # distance 2


def _priority_score(agent_priority: str, truth_priority: str) -> Tuple[float, str]:
    ap = _PRIORITY_RANK.get(agent_priority, 0)
    tp = _PRIORITY_RANK.get(truth_priority, 0)

    if ap == 0 or tp == 0:
        return 0.05, f"priority='{agent_priority}' INVALID(+0.05)"

    diff = abs(ap - tp)
    if diff == 0:
        return 0.45, f"priority='{agent_priority}' CORRECT(+0.45)"
    elif diff == 1:
        return 0.25, f"priority='{agent_priority}' NEAR_MISS(+0.25, expected '{truth_priority}')"
    elif diff == 2:
        return 0.10, f"priority='{agent_priority}' FAR_MISS(+0.10, expected '{truth_priority}')"
    else:
        return 0.05, f"priority='{agent_priority}' WRONG(+0.05, expected '{truth_priority}')"


# ============================================================
# GRADE EASY - CLASSIFICATION ONLY
# ============================================================

def grade_easy(agent_category: str, ground_truth_category: str) -> Tuple[float, str]:
    agent_category = (agent_category or "").strip().lower()
    ground_truth_category = (ground_truth_category or "").strip().lower()

    dist = _category_distance(agent_category, ground_truth_category)

    if dist == 10:
        score = SCORE_PERFECT
        fb = f"[EASY] category='{agent_category}' CORRECT (+{SCORE_PERFECT}) | total={SCORE_PERFECT}"
    elif dist == 11:
        score = SCORE_PARTIAL
        fb = f"[EASY] category='{agent_category}' ADJACENT to '{ground_truth_category}' (same semantic group, +{SCORE_PARTIAL}) | total={SCORE_PARTIAL}"
    else:
        score = SCORE_FLOOR
        fb = f"[EASY] category='{agent_category}' WRONG (expected '{ground_truth_category}', +{SCORE_FLOOR}) | total={SCORE_FLOOR}"

    score = force_safe(score)
    assert 0.01 <= score <= 0.99, f"CRITICAL: grade_easy score {score} out of range"
    assert 0.01 <= score <= 0.99, f"CRITICAL: grade_easy score {score} out of range"
    return score, fb


# ============================================================
# GRADE MEDIUM - CLASSIFICATION + PRIORITY
# ============================================================

def grade_medium(
    agent_category: str,
    ground_truth_category: str,
    agent_priority: str,
    ground_truth_priority: str,
) -> Tuple[float, str, float]:
    agent_category = (agent_category or "").strip().lower()
    ground_truth_category = (ground_truth_category or "").strip().lower()
    agent_priority = (agent_priority or "").strip().lower()
    ground_truth_priority = (ground_truth_priority or "").strip().lower()

    # Category component
    dist = _category_distance(agent_category, ground_truth_category)
    if dist == 10:
        cat_score = 0.50
        cat_fb = f"category='{agent_category}' CORRECT(+0.50)"
    elif dist == 11:
        cat_score = 0.20
        cat_fb = f"category='{agent_category}' ADJACENT(+0.20)"
    else:
        cat_score = 0.05
        cat_fb = f"category='{agent_category}' WRONG(+0.05)"

    # Priority component
    pri_score, pri_fb = _priority_score(agent_priority, ground_truth_priority)

    total = round(cat_score + pri_score, 4)
    total = force_safe(total)
    assert 0.01 <= total <= 0.99, f"CRITICAL: grader total {total} out of range"
    assert 0.01 <= total <= 0.99, f"CRITICAL: grade_medium total {total} out of range"

    fb = f"[MEDIUM] {cat_fb} | {pri_fb} | total={total}"
    return total, fb, force_safe(pri_score)


# ============================================================
# GRADE HARD - FULL RESPONSE
# ============================================================

def grade_hard(
    agent_category: str,
    ground_truth_category: str,
    agent_priority: str,
    ground_truth_priority: str,
    agent_response: str,
    keywords: List[str],
) -> Tuple[float, str, float, float]:
    agent_category = (agent_category or "").strip().lower()
    ground_truth_category = (ground_truth_category or "").strip().lower()
    agent_priority = (agent_priority or "").strip().lower()
    ground_truth_priority = (ground_truth_priority or "").strip().lower()
    resp_lower = (agent_response or "").lower()

    base = 0.05

    # Category component
    dist = _category_distance(agent_category, ground_truth_category)
    if dist == 10:
        cat_score = 0.25
        cat_fb = f"category:CORRECT(+0.25)"
    elif dist == 11:
        cat_score = 0.12
        cat_fb = f"category:ADJACENT(+0.12)"
    else:
        cat_score = 0.00
        cat_fb = f"category:WRONG(+0.00, expected '{ground_truth_category}')"

    # Priority component
    ap = _PRIORITY_RANK.get(agent_priority, 0)
    tp = _PRIORITY_RANK.get(ground_truth_priority, 0)
    if ap == 0 or tp == 0:
        pri_score = 0.00
        pri_fb = "priority:INVALID(+0.00)"
    elif abs(ap - tp) == 0:
        pri_score = 0.25
        pri_fb = "priority:CORRECT(+0.25)"
    elif abs(ap - tp) == 1:
        pri_score = 0.20
        pri_fb = "priority:NEAR_MISS(+0.20)"
    elif abs(ap - tp) == 2:
        pri_score = 0.10
        pri_fb = "priority:FAR_MISS(+0.10)"
    else:
        pri_score = 0.00
        pri_fb = f"priority:WRONG(+0.00, expected '{ground_truth_priority}')"

    # Sentiment component
    empathy_hits = sum(1 for w in _EMPATHY_KEYWORDS if w in resp_lower)
    if empathy_hits >= 2:
        sent_score = 0.20
        sent_fb = f"sentiment:EMPATHETIC(+0.20, {empathy_hits} matches)"
    elif empathy_hits == 1:
        sent_score = 0.10
        sent_fb = f"sentiment:PARTIAL(+0.10, {empathy_hits} match)"
    else:
        sent_score = 0.00
        sent_fb = "sentiment:NEUTRAL(+0.00)"

    # Action component
    action_hits = sum(1 for w in _RESOLUTION_KEYWORDS if w in resp_lower)
    if action_hits >= 2:
        act_score = 0.20
        act_fb = f"action:HELPFUL(+0.20, {action_hits} matches)"
    elif action_hits == 1:
        act_score = 0.10
        act_fb = f"action:PARTIAL(+0.10, {action_hits} match)"
    else:
        act_score = 0.00
        act_fb = "action:VAGUE(+0.00)"

    total = round(base + cat_score + pri_score + sent_score + act_score, 4)
    total = force_safe(total)
    assert 0.01 <= total <= 0.99, f"CRITICAL: grader total {total} out of range"

    response_score = round(sent_score + act_score, 4)
    fb = f"[HARD] base(+0.05) | {cat_fb} | {pri_fb} | {sent_fb} | {act_fb} | total={total}"

    return total, fb, force_safe(pri_score), force_safe(response_score)


# ============================================================
# GRADER FACTORY
# ============================================================

def get_grader(difficulty: str):
    if difficulty == "easy":
        return grade_easy
    elif difficulty == "medium":
        return grade_medium
    else:
        return grade_hard


# ============================================================
# FORCE SAFE CLIP FUNCTION FOR BACKWARD COMPATIBILITY
# ============================================================

clip_score = force_safe

import sys
sys.stderr.write("INFO: SAFE_GRADER loaded - ALL scores forced to (0.01, 0.99)\n")
sys.stderr.flush()
