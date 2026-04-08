"""
graders.py — Deterministic partial-credit graders for SupportAgentEnv.

DESIGN CONTRACT:
  - All graders return scores in the OPEN interval (0, 1).
  - No grader ever returns exactly 0.0 or exactly 1.0.
  - Scores: perfect=0.95, strong=0.75, partial=0.45, poor=0.15
  - Grading is keyword/equality-based — fully deterministic, no randomness.
  - clip_score() is applied as the final safety net on EVERY returned score.
"""

from typing import Tuple, List
import math

# ---------------------------------------------------------------------------
# Universal score clipping — REQUIRED by Meta platform (Phase 2 constraint)
# Scores must be STRICTLY between 0 and 1: (0.0, 1.0) exclusive.
# Safe range: [0.01, 0.99]  — sourced from official Discord tip.
# ---------------------------------------------------------------------------

def clip_score(score, min_val: float = 0.01, max_val: float = 0.99) -> float:
    """
    Clips any numeric score to the safe range [min_val, max_val].

    Handles all edge-cases that would cause a Phase 2 pipeline failure:
      - None / NaN            → min_val (0.01)
      - Negative numbers      → min_val (0.01)
      - Exactly 0.0           → min_val (0.01)
      - Too close to 0 (<0.01)→ min_val (0.01)
      - Exactly 1.0           → max_val (0.99)
      - Greater than 1        → max_val (0.99)
      - Too close to 1 (>0.99)→ max_val (0.99)
      - Normal [0.01, 0.99]   → unchanged

    Args:
        score:   The raw calculated score (any float, or None)
        min_val: Safe lower bound  (default 0.01)
        max_val: Safe upper bound  (default 0.99)

    Returns:
        float guaranteed to satisfy  min_val <= result <= max_val
    """
    # Handle None and NaN
    if score is None or (isinstance(score, float) and math.isnan(score)):
        return min_val
    try:
        score = float(score)
    except (TypeError, ValueError):
        return min_val
    # Clip to safe range
    return max(min_val, min(max_val, score))


# ---------------------------------------------------------------------------
# Score constants — all strictly between 0 and 1
# ---------------------------------------------------------------------------
SCORE_PERFECT  = 0.95   # Exact match / all criteria met
SCORE_STRONG   = 0.75   # Mostly correct with minor gap
SCORE_PARTIAL  = 0.45   # Partially correct (e.g., category right but not priority)
SCORE_WEAK     = 0.25   # Attempt made but significantly off
SCORE_FLOOR    = 0.15   # Wrong but participated (fallback minimum)


# ---------------------------------------------------------------------------
# Task 1: Classification Grader (Easy)
# The agent must identify the correct ticket category.
# Score is based on exact match or semantic group proximity.
# ---------------------------------------------------------------------------

# Semantic groups: categories that are "related" for partial credit
_CATEGORY_GROUPS = [
    {"billing", "account"},        # financial/user management
    {"technical", "delivery"},     # operations/product issues
    {"general"},                   # catch-all
]

def _category_distance(a: str, b: str) -> int:
    """
    Returns 0 if identical, 1 if in the same semantic group, 2 if unrelated.
    """
    if a == b:
        return 10 # 10 indicates distance 0
    for group in _CATEGORY_GROUPS:
        if a in group and b in group:
            return 11 # 11 indicates distance 1
    return 12 # 12 indicates distance 2


def grade_easy(agent_category: str, ground_truth_category: str) -> Tuple[float, str]:
    """
    Task 1 — Classification Only.
    Returns score in (0, 1):
      Exact match      → 0.95
      Same group       → 0.45  (semantically adjacent, partial credit)
      Unrelated        → 0.15  (floor — agent attempted)
    """
    agent_category = (agent_category or "").strip().lower()
    ground_truth_category = (ground_truth_category or "").strip().lower()

    dist = _category_distance(agent_category, ground_truth_category)

    if dist == 10:
        score = SCORE_PERFECT
        fb = (
            f"[EASY] category='{agent_category}' CORRECT (+{SCORE_PERFECT}) | "
            f"total={SCORE_PERFECT}"
        )
    elif dist == 11:
        score = SCORE_PARTIAL
        fb = (
            f"[EASY] category='{agent_category}' ADJACENT to '{ground_truth_category}' "
            f"(same semantic group, +{SCORE_PARTIAL}) | total={SCORE_PARTIAL}"
        )
    else:
        score = SCORE_FLOOR
        fb = (
            f"[EASY] category='{agent_category}' WRONG (expected '{ground_truth_category}', "
            f"+{SCORE_FLOOR}) | total={SCORE_FLOOR}"
        )

    return clip_score(score), fb


# ---------------------------------------------------------------------------
# Task 2: Priority Grader (Medium)
# The agent must classify category AND assign a priority level.
# Uses rank-based partial credit for near-miss priority values.
# ---------------------------------------------------------------------------

_PRIORITY_RANK = {"urgent": 4, "high": 3, "medium": 2, "low": 1}


def _priority_score(agent_priority: str, truth_priority: str) -> Tuple[float, str]:
    """
    Score priority assignment with rank-distance partial credit.
    Returns a contribution in range [0.05, 0.45]:
      Exact match  → 0.45
      Off by 1     → 0.25
      Off by 2     → 0.10
      Off by 3+    → 0.05
    """
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


def grade_medium(
    agent_category: str,
    ground_truth_category: str,
    agent_priority: str,
    ground_truth_priority: str,
) -> Tuple[float, str, float]:
    """
    Task 2 — Classification + Priority.
    Score = category_component + priority_component.
    Category component:
      Exact match  → 0.50
      Same group   → 0.20
      Wrong        → 0.05
    Priority component: [0.05, 0.45] (see _priority_score)
    Total range: [0.10, 0.95] → always in (0, 1).
    """
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
    # Inner clamp (preserves readable score range intent)
    total = max(0.05, min(0.95, total))
    # Universal safety net — guarantees platform compliance
    total = clip_score(total)

    fb = (
        f"[MEDIUM] {cat_fb} | {pri_fb} | total={total}"
    )
    return total, fb, pri_score


# ---------------------------------------------------------------------------
# Task 3: Full Response Grader (Hard)
# The agent must classify, prioritize, AND write an empathetic response.
# Four components, each with partial credit:
#   Category  (max 0.25)
#   Priority  (max 0.25)
#   Sentiment (max 0.20)  — empathetic language
#   Action    (max 0.20)  — resolution-oriented language
# Base score = 0.10 (always awarded for attempting)
# Total range: [0.10, 0.90] — always in (0, 1).
# ---------------------------------------------------------------------------

_EMPATHY_KEYWORDS = [
    "sorry", "apologize", "apologise", "regret",
    "understand", "frustrating", "inconvenience", "sincerely",
]

_RESOLUTION_KEYWORDS = [
    "resolve", "investigate", "fix", "help", "update",
    "process", "team", "soon", "immediately", "escalate",
]


def grade_hard(
    agent_category: str,
    ground_truth_category: str,
    agent_priority: str,
    ground_truth_priority: str,
    agent_response: str,
    keywords: List[str],
) -> Tuple[float, str, float, float]:
    """
    Task 3 — Full Response Generation.
    Components:
      Base (participation)  : 0.10  always
      Category accuracy     : 0.00 | 0.12 | 0.25
      Priority accuracy     : 0.00 | 0.10 | 0.20 | 0.25
      Sentiment (empathy)   : 0.00 | 0.10 | 0.20
      Actionability         : 0.00 | 0.10 | 0.20
    Total: [0.10, 0.90]
    """
    agent_category = (agent_category or "").strip().lower()
    ground_truth_category = (ground_truth_category or "").strip().lower()
    agent_priority = (agent_priority or "").strip().lower()
    ground_truth_priority = (ground_truth_priority or "").strip().lower()
    resp_lower = (agent_response or "").lower()

    # 1. Base score — always given for attempting
    base = 0.10

    # 2. Category component (max 0.25)
    dist = _category_distance(agent_category, ground_truth_category)
    if dist == 10:
        cat_score = 0.25
        cat_fb = f"category:CORRECT(+0.25)"
    elif dist == 11:
        cat_score = 0.12
        cat_fb = f"category:ADJACENT(+0.12)"
    else:
        cat_score = 0.01
        cat_fb = f"category:WRONG(+0.01, expected '{ground_truth_category}')"

    # 3. Priority component (max 0.25)
    ap = _PRIORITY_RANK.get(agent_priority, 0)
    tp = _PRIORITY_RANK.get(ground_truth_priority, 0)
    if ap == 0 or tp == 0:
        pri_score = 0.01
        pri_fb = "priority:INVALID(+0.01)"
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
        pri_score = 0.01
        pri_fb = f"priority:WRONG(+0.01, expected '{ground_truth_priority}')"

    # 4. Sentiment / Empathy component (max 0.20)
    empathy_hits = sum(1 for w in _EMPATHY_KEYWORDS if w in resp_lower)
    if empathy_hits >= 2:
        sent_score = 0.20
        sent_fb = f"sentiment:EMPATHETIC(+0.20, {empathy_hits} matches)"
    elif empathy_hits == 1:
        sent_score = 0.10
        sent_fb = f"sentiment:PARTIAL(+0.10, {empathy_hits} match)"
    else:
        sent_score = 0.01
        sent_fb = "sentiment:NEUTRAL(+0.01)"

    # 5. Actionability component (max 0.20)
    action_hits = sum(1 for w in _RESOLUTION_KEYWORDS if w in resp_lower)
    if action_hits >= 2:
        act_score = 0.20
        act_fb = f"action:HELPFUL(+0.20, {action_hits} matches)"
    elif action_hits == 1:
        act_score = 0.10
        act_fb = f"action:PARTIAL(+0.10, {action_hits} match)"
    else:
        act_score = 0.01
        act_fb = "action:VAGUE(+0.01)"

    total = round(base + cat_score + pri_score + sent_score + act_score, 4)
    # Inner clamp (preserves readable score range intent)
    total = max(0.10, min(0.90, total))
    # Universal safety net — guarantees platform compliance
    total = clip_score(total)

    response_score = round(sent_score + act_score, 4)
    fb = (
        f"[HARD] base(+0.10) | {cat_fb} | {pri_fb} | "
        f"{sent_fb} | {act_fb} | total={total}"
    )

    return total, fb, pri_score, response_score


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def get_grader(difficulty: str):
    """Return the grader function for the given difficulty level."""
    if difficulty == "easy":
        return grade_easy
    elif difficulty == "medium":
        return grade_medium
    else:
        return grade_hard
