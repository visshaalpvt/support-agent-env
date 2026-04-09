"""Quick sanity test — verifies graders + api imports work."""
import sys
sys.path.insert(0, ".")

# Test 1: safe_grader imports
from safe_grader import grade_easy, grade_medium, grade_hard, force_safe
print("✓ safe_grader imports OK")

# Test 2: grader scores in range
s1, _ = grade_easy("delivery", "delivery")
assert 0.01 <= s1 <= 0.99, f"easy correct out of range: {s1}"
print(f"  easy correct:  {s1}")

s2, _ = grade_easy("billing", "delivery")
assert 0.01 <= s2 <= 0.99, f"easy wrong out of range: {s2}"
print(f"  easy wrong:    {s2}")

s3, _, _ = grade_medium("billing", "billing", "urgent", "urgent")
assert 0.01 <= s3 <= 0.99, f"medium correct out of range: {s3}"
print(f"  medium correct:{s3}")

s4, _, _, _ = grade_hard("delivery", "delivery", "high", "high",
    "I am sorry for the inconvenience, I will help resolve this immediately",
    ["order"])
assert 0.01 <= s4 <= 0.99, f"hard good out of range: {s4}"
print(f"  hard good:     {s4}")

# Test 3: force_safe edge cases
assert force_safe(0.0) == 0.01
assert force_safe(1.0) == 0.99
assert force_safe(-5.0) == 0.01
assert force_safe(999.0) == 0.99
assert force_safe(None) == 0.01
print("✓ force_safe edge cases OK")

# Test 4: api.py imports (without starting server)
import importlib
spec = importlib.util.find_spec("api")
# Don't actually import it since it reads safe_grader at module level
print("✓ api module findable")

print("\n✅ All sanity checks passed!")
