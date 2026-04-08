"""
graders.py — Deterministic grading functions for SupportAgentEnv

SCORING POLICY (per hackathon Phase 2 requirement):
  - All scores are in the OPEN interval (0, 1) — never exactly 0.0 or 1.0
  - Partial credit is used at all difficulty levels
  - Scoring is fully deterministic (no randomness)

Score scale:
  0.95 — perfect match
  0.75 — strong partial match
  0.45 — weak partial match
  0.15 — poor / completely wrong (minimum, never 0)
"""

from typing import Tuple, List


# ============================================================
# TASK 1 GRADER — Category Classification (Easy)
# ============================================================

def grade_easy(agent_category: str, ground_truth_category: str) -> Tuple[float, str]:
    """
    Score: category accuracy only.
    Scores are in (0, 1) — perfect=0.95, wrong=0.15.
    """
    if agent_category == ground_truth_category:
        score = 0.95
        feedback = (
            f"[EASY] Category '{agent_category}' CORRECT. "
            f"Score: classification=0.95 | total=0.95"
        )
    else:
        score = 0.15
        feedback = (
            f"[EASY] Category '{agent_category}' WRONG (expected '{ground_truth_category}'). "
            f"Score: classification=0.15 | total=0.15"
        )
    return score, feedback


# ============================================================
# TASK 2 GRADER — Classification + Priority (Medium)
# ============================================================

def grade_medium(
    agent_category: str,
    ground_truth_category: str,
    agent_priority: str,
    ground_truth_priority: str,
) -> Tuple[float, str, float]:
    """
    Score: category (50%) + priority (50%).
    Uses partial credit — scores always in (0, 1).

    Category scoring:
      correct  → 0.45
      wrong    → 0.10

    Priority scoring:
      correct     → 0.45
      off by 1    → 0.25 (one level too low)  / 0.15 (one level too high)
      off by 2+   → 0.05

    Total range: [0.15, 0.90]
    """
    # Category component
    if agent_category == ground_truth_category:
        category_score = 0.45
        cat_fb = f"category='{agent_category}' CORRECT(+0.45)"
    else:
        category_score = 0.10
        cat_fb = f"category='{agent_category}' WRONG(exp:'{ground_truth_category}')(+0.10)"

    # Priority component — rank-based with partial credit
    priority_rank = {"urgent": 4, "high": 3, "medium": 2, "low": 1}
    agent_rank = priority_rank.get(agent_priority, 0)
    truth_rank = priority_rank.get(ground_truth_priority, 0)
    rank_diff = agent_rank - truth_rank

    if agent_priority == ground_truth_priority:
        priority_score = 0.45
        pri_fb = f"priority='{agent_priority}' CORRECT(+0.45)"
    elif rank_diff == -1:
        priority_score = 0.25
        pri_fb = f"priority='{agent_priority}' ONE_LOW(exp:'{ground_truth_priority}')(+0.25)"
    elif rank_diff == 1:
        priority_score = 0.15
        pri_fb = f"priority='{agent_priority}' ONE_HIGH(exp:'{ground_truth_priority}')(+0.15)"
    else:
        priority_score = 0.05
        pri_fb = f"priority='{agent_priority}' WRONG(exp:'{ground_truth_priority}')(+0.05)"

    total = round(category_score + priority_score, 4)
    # Clamp to open interval (0, 1) as safety
    total = max(0.10, min(total, 0.95))
    feedback = f"[MEDIUM] {cat_fb} | {pri_fb} | total={total:.4f}"
    return total, feedback, priority_score


# ============================================================
# TASK 3 GRADER — Full Response (Hard)
# ============================================================

def grade_hard(
    agent_category: str,
    ground_truth_category: str,
    agent_priority: str,
    ground_truth_priority: str,
    agent_response: str,
    keywords: List[str],
) -> Tuple[float, str, float, float]:
    """
    Score: Weighted multi-metric grading.
      Category  — 28% weight (0.07 – 0.28)
      Priority  — 28% weight (0.07 – 0.28)
      Sentiment — 19% weight (0.05 – 0.19)
      Action    — 19% weight (0.05 – 0.19)

    Total range: [0.24, 0.94] → always in open interval (0, 1)
    """
    # ---- 1. Category (28%) ----
    if agent_category == ground_truth_category:
        category_score = 0.28
        cat_fb = "category:CORRECT(+0.28)"
    else:
        category_score = 0.07
        cat_fb = f"category:WRONG(exp:{ground_truth_category})(+0.07)"

    # ---- 2. Priority (28%) — rank-based partial credit ----
    priority_rank = {"urgent": 4, "high": 3, "medium": 2, "low": 1}
    agent_rank = priority_rank.get(agent_priority, 0)
    truth_rank = priority_rank.get(ground_truth_priority, 0)

    if agent_priority == ground_truth_priority:
        priority_score = 0.28
        pri_fb = "priority:CORRECT(+0.28)"
    elif abs(agent_rank - truth_rank) == 1:
        priority_score = 0.14
        pri_fb = "priority:NEAR_MISS(+0.14)"
    else:
        priority_score = 0.07
        pri_fb = f"priority:WRONG(exp:{ground_truth_priority})(+0.07)"

    # ---- 3. Sentiment & Empathy (19%) ----
    empathy_words = {"sorry", "apologize", "regret", "understand", "frustrating", "apologise"}
    sentiment_score = 0.05  # minimum — never 0
    sentiment_fb = "sentiment:MISSING(+0.05)"
    if agent_response:
        resp_lower = agent_response.lower()
        matches = [w for w in empathy_words if w in resp_lower]
        if len(matches) >= 2:
            sentiment_score = 0.19
            sentiment_fb = f"sentiment:STRONG_EMPATHY(+0.19)"
        elif len(matches) == 1:
            sentiment_score = 0.12
            sentiment_fb = f"sentiment:EMPATHETIC(+0.12)"
        else:
            sentiment_score = 0.05
            sentiment_fb = "sentiment:NEUTRAL(+0.05)"

    # ---- 4. Actionability & Resolution (19%) ----
    resolution_words = {"resolve", "investigate", "help", "fix", "update", "process", "team", "soon"}
    action_score = 0.05  # minimum — never 0
    action_fb = "action:MISSING(+0.05)"
    if agent_response:
        resp_lower = agent_response.lower()
        match_count = sum(1 for w in resolution_words if w in resp_lower)
        if match_count >= 3:
            action_score = 0.19
            action_fb = f"action:HIGHLY_ACTIONABLE(+0.19)"
        elif match_count == 2:
            action_score = 0.14
            action_fb = f"action:ACTIONABLE(+0.14)"
        elif match_count == 1:
            action_score = 0.09
            action_fb = f"action:PARTIAL(+0.09)"
        else:
            action_score = 0.05
            action_fb = "action:VAGUE(+0.05)"

    total = round(category_score + priority_score + sentiment_score + action_score, 4)
    # Safety clamp to open interval (0, 1)
    total = max(0.15, min(total, 0.94))

    feedback = (
        f"[HARD] {cat_fb} | {pri_fb} | {sentiment_fb} | {action_fb} | total={total}"
    )
    response_score = round(sentiment_score + action_score, 4)
    return total, feedback, priority_score, response_score


# ============================================================
# GRADER REGISTRY
# ============================================================

def get_grader(difficulty: str):
    """Return the appropriate grader function for the given difficulty."""
    if difficulty == "easy":
        return grade_easy
    elif difficulty == "medium":
        return grade_medium
    else:
        return grade_hard
