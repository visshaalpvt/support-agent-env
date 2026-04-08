import math
from tasks.grader import clip_score, grade_easy, grade_medium, grade_hard, get_grader

def check(label, val):
    assert 0.001 <= val <= 0.999, f"OUT OF RANGE: {label} = {val}"
    print(f"  ✓ {label} = {val:.4f}")

print("\n=== clip_score edge cases ===")
check("clip(0.0)",   clip_score(0.0))
check("clip(1.0)",   clip_score(1.0))
check("clip(-999)",  clip_score(-999))
check("clip(999)",   clip_score(999))
check("clip(nan)",   clip_score(float('nan')))
check("clip(inf)",   clip_score(float('inf')))
check("clip(0.5)",   clip_score(0.5))

print("\n=== grade_easy ===")
for cat, truth in [("delivery","delivery"), ("billing","delivery"), ("general","general")]:
    score, fb, c, p, r = grade_easy(cat, truth)
    check(f"easy total ({cat}=={truth})", score)
    check(f"easy cat",   c)
    check(f"easy pri",   p)
    check(f"easy resp",  r)

print("\n=== grade_medium ===")
for cat, truth, pri, tpri in [
    ("billing","billing","high","high"),
    ("delivery","billing","low","urgent"),
    ("technical","technical","medium","high"),
]:
    score, fb, c, p, r = grade_medium(cat, truth, pri, tpri)
    check(f"medium total", score)
    check(f"medium cat",   c)
    check(f"medium pri",   p)
    check(f"medium resp",  r)

print("\n=== grade_hard ===")
for cat, truth, pri, tpri, resp, kws in [
    ("billing","billing","high","high","your bill was processed correctly", ["bill","processed"]),
    ("delivery","delivery","urgent","urgent","", []),
    ("general","technical","low","high","sorry for the inconvenience", ["inconvenience"]),
]:
    score, fb, c, p, r = grade_hard(cat, truth, pri, tpri, resp, kws)
    check(f"hard total", score)
    check(f"hard cat",   c)
    check(f"hard pri",   p)
    check(f"hard resp",  r)

print("\n=== get_grader routing ===")
for d in ["easy","medium","hard","unknown"]:
    g = get_grader(d)
    print(f"  ✓ get_grader('{d}') = {g.__name__}")

print("\n=== inference key check ===")
action = {"category": "billing", "priority": "high", "response_text": "We will help you."}
assert action.get("category") == "billing",       "❌ key 'category' missing"
assert action.get("response_text") == "We will help you.", "❌ key 'response_text' missing"
print("  ✓ inference keys correct")

print("\n✅ ALL TESTS PASSED — safe to resubmit!\n")
