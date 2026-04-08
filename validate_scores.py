"""
validate_scores.py — Pre-Submission Score Range Validator
SupportAgentEnv · Meta Hackathon x Scaler · Phase 2 Safe

Run this script BEFORE every submission to confirm:
  - clip_score() behaves correctly on all edge cases
  - grade_easy / grade_medium / grade_hard NEVER return 0.0 or 1.0
  - No score is outside the open interval (0, 1)

Usage:
    py validate_scores.py
"""

import sys
import math

# ─── import safe_grader ─────────────────────────────────────────────────────────
try:
    from safe_grader import clip_score, grade_easy, grade_medium, grade_hard
except ImportError as e:
    print(f"FATAL: Could not import safe_grader.py: {e}", file=sys.stderr)
    sys.exit(1)

PASS = "✅ PASS"
FAIL = "❌ FAIL"
all_ok = True


def check(label: str, result: float, expected=None, must_be_in_range=True):
    global all_ok
    issues = []

    # Must be a float
    if not isinstance(result, float):
        issues.append(f"type={type(result).__name__} (expected float)")

    # Must be strictly in (0, 1)
    if must_be_in_range:
        if result <= 0.0:
            issues.append(f"score {result} <= 0.0 — WILL FAIL PHASE 2")
        if result >= 1.0:
            issues.append(f"score {result} >= 1.0 — WILL FAIL PHASE 2")

    # Exact expected value check
    if expected is not None and result != expected:
        issues.append(f"expected {expected}, got {result}")

    ok = len(issues) == 0
    if not ok:
        all_ok = False
    status = PASS if ok else FAIL
    detail = f"  → {', '.join(issues)}" if issues else ""
    print(f"  {status} | {label}: {result}{detail}")


# ─── 1. clip_score() edge cases ─────────────────────────────────────────────
print("\n══════════════════════════════════════════")
print("  1. clip_score() Edge Cases")
print("══════════════════════════════════════════")

clip_cases = [
    (0.0,         0.01,  "exactly 0.0  → 0.01"),
    (1.0,         0.99,  "exactly 1.0  → 0.99"),
    (0.5,         0.5,   "mid 0.5      → 0.5 (unchanged)"),
    (-0.5,        0.01,  "negative     → 0.01"),
    (2.0,         0.99,  "above 1      → 0.99"),
    (0.001,       0.01,  "too-close-0  → 0.01"),
    (0.9999,      0.99,  "too-close-1  → 0.99"),
    (None,        0.01,  "None         → 0.01"),
    (float("nan"),0.01,  "NaN          → 0.01"),
    (float("inf"),0.99,  "Inf          → 0.99"),
    (0.42,        0.42,  "normal 0.42  → 0.42 (unchanged)"),
    (0.01,        0.01,  "min boundary → 0.01"),
    (0.99,        0.99,  "max boundary → 0.99"),
]

for inp, expected, label in clip_cases:
    result = clip_score(inp)
    check(label, result, expected=expected)


# ─── 2. grade_easy — all paths ──────────────────────────────────────────────
print("\n══════════════════════════════════════════")
print("  2. grade_easy() — All Score Paths")
print("══════════════════════════════════════════")

easy_cases = [
    ("billing",   "billing",   "exact match       → ~0.95"),
    ("account",   "billing",   "adjacent group    → ~0.45"),
    ("general",   "billing",   "wrong category    → ~0.15"),
    ("",          "billing",   "empty string      → floor"),
    (None,        "billing",   "None input        → floor"),
    ("gibberish###!!", "billing", "garbage input  → floor"),
]

for agent_cat, truth_cat, label in easy_cases:
    score, _ = grade_easy(agent_cat, truth_cat)
    check(label, score)


# ─── 3. grade_medium — all paths ────────────────────────────────────────────
print("\n══════════════════════════════════════════")
print("  3. grade_medium() — All Score Paths")
print("══════════════════════════════════════════")

medium_cases = [
    ("billing",  "billing",  "urgent",  "urgent",  "cat+pri exact   → ~0.95"),
    ("billing",  "billing",  "high",    "urgent",  "cat exact, pri near → ~0.75"),
    ("billing",  "billing",  "low",     "urgent",  "cat exact, pri far  → ~0.60"),
    ("account",  "billing",  "urgent",  "urgent",  "cat adjacent, pri exact → ~0.65"),
    ("general",  "billing",  "low",     "urgent",  "cat wrong, pri wrong → ~0.10"),
    ("",         "billing",  "",        "urgent",  "all empty        → floor"),
    (None,       "billing",  None,      "urgent",  "all None         → floor"),
    ("???",      "billing",  "???",     "urgent",  "garbage inputs   → floor"),
]

for ac, tc, ap, tp, label in medium_cases:
    score, _, _ = grade_medium(ac, tc, ap, tp)
    check(label, score)


# ─── 4. grade_hard — all paths ──────────────────────────────────────────────
print("\n══════════════════════════════════════════")
print("  4. grade_hard() — All Score Paths")
print("══════════════════════════════════════════")

# Simulates the empathy + resolution keyword responses the LLM produces
full_response = (
    "We sincerely apologize for the inconvenience. "
    "Our team will investigate and resolve this issue immediately."
)
partial_response = "We understand your frustration."
empty_response = ""

hard_cases = [
    ("billing", "billing", "urgent", "urgent", full_response,    [], "all correct, full response → ~0.90"),
    ("billing", "billing", "high",   "urgent", full_response,    [], "pri near-miss, full response → ~0.85"),
    ("account", "billing", "medium", "urgent", partial_response, [], "cat adjacent, partial response → ~0.50"),
    ("general", "billing", "low",    "urgent", empty_response,   [], "all wrong, empty response → ~0.10"),
    ("",        "billing", "",       "urgent", "",               [], "all empty → floor"),
    (None,      "billing", None,     "urgent", None,             [], "all None → floor"),
    ("###",     "billing", "???",    "urgent", "!!!",            [], "garbage inputs → floor"),
]

for ac, tc, ap, tp, resp, kw, label in hard_cases:
    score, _, _, _ = grade_hard(ac, tc, ap, tp, resp, kw)
    check(label, score)


# ─── 5. Final aggregation clipping ──────────────────────────────────────────
print("\n══════════════════════════════════════════")
print("  5. Aggregated Score (weighted average)")
print("══════════════════════════════════════════")

agg_cases = [
    (0.95, 0.85, 0.70, "all strong scores"),
    (0.15, 0.10, 0.10, "all weak scores"),
    (0.01, 0.01, 0.01, "all at minimum"),
    (0.99, 0.99, 0.99, "all at maximum"),
    (0.5,  0.5,  0.5,  "all mid scores"),
]

weights = [0.25, 0.35, 0.40]
for s1, s2, s3, label in agg_cases:
    raw = s1 * weights[0] + s2 * weights[1] + s3 * weights[2]
    agg = clip_score(raw)
    check(f"aggregate {label}", agg)
    print(f"         raw={raw:.4f} → clipped={agg:.4f}")


# ─── 6. safe_return_score assertion gate ────────────────────────────────────
print("\n══════════════════════════════════════════")
print("  6. safe_return_score() Assertion Gate")
print("══════════════════════════════════════════")

def safe_return_score(score, task_name="unknown"):
    clipped = clip_score(score)
    assert 0 < clipped < 1, f"FATAL: '{task_name}' score {clipped} not in (0,1)"
    return clipped

gate_cases = [0.01, 0.15, 0.45, 0.75, 0.95, 0.99]
gate_ok = True
for s in gate_cases:
    try:
        r = safe_return_score(s, "test")
        check(f"assertion gate safe_return_score({s})", r)
    except AssertionError as e:
        print(f"  {FAIL} | assertion failed for {s}: {e}")
        gate_ok = False
        all_ok = False

# Test that 0.0 and 1.0 are clipped BEFORE the assertion sees them
for bad in [0.0, 1.0, -1.0, 2.0]:
    try:
        r = safe_return_score(bad, "test")
        check(f"assertion gate safe_return_score({bad}) → clipped", r)
    except AssertionError as e:
        print(f"  {FAIL} | assertion unexpectedly fired for {bad}: {e}")
        all_ok = False


# ─── Final Result ────────────────────────────────────────────────────────────
print("\n══════════════════════════════════════════")
if all_ok:
    print("  ✅ ALL TESTS PASSED — Safe to submit!")
else:
    print("  ❌ SOME TESTS FAILED — DO NOT SUBMIT")
    print("  Fix all FAIL cases before pushing to HF Spaces.")
print("══════════════════════════════════════════\n")

sys.exit(0 if all_ok else 1)
