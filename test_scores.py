from tasks.grader import grade_episode

print("=" * 50)
print("  SCORE RANGE VALIDATOR")
print("=" * 50)

test_cases = [
    (0.0,    0,  5, "zero steps (edge)"),
    (0.0,    0,  0, "zero sensors (edge)"),
    (0.5,   20,  3, "easy - mid reward"),
    (1.1,   20,  3, "easy - overflow"),
    (-0.1,  20,  3, "easy - underflow"),
]

all_passed = True
for total_reward, steps, num_sensors, label in test_cases:
    score = grade_episode(total_reward, steps, num_sensors)
    # Check if strictly within (0, 1) and in our new range
    in_range = 0.0 < score < 1.0
    status = "PASS" if in_range else "FAIL"
    if not in_range:
        all_passed = False
    print(f"  [{status}] {label:<30} => score={score:.4f}")

print("=" * 50)
if all_passed:
    print("  ALL PASSED — safe to resubmit!")
else:
    print("  FAILURES FOUND — fix grader before resubmit!")
print("=" * 50)
