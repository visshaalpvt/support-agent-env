from tasks.grader import grade_episode

print("=" * 50)
print("  SCORE RANGE VALIDATOR")
print("=" * 50)

test_cases = [
    (0.0,    0,  5, "zero steps (edge)"),
    (0.0,    0,  0, "zero sensors (edge)"),
    (0.0,   20,  3, "easy - zero reward"),
    (120.0, 20,  3, "easy - max reward"),
    (-120.0,20,  3, "easy - min reward"),
    (0.0,   40,  4, "medium - zero reward"),
    (320.0, 40,  4, "medium - max reward"),
    (-320.0,40,  4, "medium - min reward"),
    (0.0,   60,  5, "hard - zero reward"),
    (600.0, 60,  5, "hard - max reward"),
    (-600.0,60,  5, "hard - min reward"),
    (999.0, 60,  5, "hard - overflow reward"),
    (-999.0,60,  5, "hard - underflow reward"),
]

all_passed = True
for total_reward, steps, num_sensors, label in test_cases:
    score = grade_episode(total_reward, steps, num_sensors)
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
