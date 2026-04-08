#!/usr/bin/env python3
import sys
import os
import re

def test_clip_logic():
    print("\n[TEST] Testing clip_score() logic...")
    try:
        from safe_grader import clip_score
    except ImportError:
        print("  FAIL: Could not import safe_grader")
        return False
    test_values = [-100, -1, 0, 0.005, 0.5, 0.995, 1, 2, 100]
    all_pass = True
    for val in test_values:
        clamped = clip_score(val)
        is_valid = 0.01 <= clamped <= 0.99
        if not is_valid:
            print(f"  FAIL Input: {val} -> {clamped}")
            all_pass = False
    if all_pass: print("  PASS")
    return all_pass

def test_grader_range():
    print("\n[TEST] Testing grader edge cases...")
    try:
        from safe_grader import grade_easy, grade_medium, grade_hard
    except ImportError:
        print("  FAIL: Could not import safe_grader functions")
        return False
    test_cases = [
        ("easy-perfect", lambda: grade_easy("billing", "billing")),
        ("medium-perfect", lambda: grade_medium("billing", "billing", "urgent", "urgent")),
        ("hard-perfect", lambda: grade_hard("billing", "billing", "urgent", "urgent", "sorry understand resolve", [])),
    ]
    all_pass = True
    for name, func in test_cases:
        score = func()[0]
        if not (0.01 <= score <= 0.99):
            print(f"  FAIL {name} -> {score}")
            all_pass = False
    if all_pass: print("  PASS")
    return all_pass

def check_forbidden_patterns():
    print("\n[TEST] Auditing source code for forbidden patterns...")
    # Matches literals like 0, 1, 0.0, 1.0 exactly. 
    # Must be preceded by return, score =, or else.
    # Must NOT be followed by a dot and non-zero digit (e.g. 0.15 must be ignored).
    forbidden = [
        r"\b(return|score|else)\b.*?\b[01](\.0+)?\b(?!\.\d)",
    ]
    bugs = 0
    files = ["safe_grader.py", "inference.py", "support_env.py"]
    for f in files:
        if not os.path.exists(f): continue
        with open(f, 'r', encoding='utf-8') as src:
            for i, line in enumerate(src, 1):
                clean_line = line.split('#')[0]
                for p in forbidden:
                    if re.search(p, clean_line):
                        print(f"  FAIL found in {f}:{i} -> {line.strip()}")
                        bugs += 1
    if bugs == 0: print("  PASS")
    return bugs == 0

def check_inference_compliance():
    print("\n[TEST] Checking inference.py structure...")
    if not os.path.exists("inference.py"): return False
    with open("inference.py", "r", encoding='utf-8') as f:
        content = f.read()
    all_pass = True
    if "from safe_grader import" in content:
        print("  FAIL: inference.py imports safe_grader")
        all_pass = False
    if 'os.environ["API_BASE_URL"]' not in content:
        print("  FAIL: API_BASE_URL missing mandatory indexing")
        all_pass = False
    if 'log_end(' not in content or '[END]' not in content:
        print("  FAIL: [END] formatting logic missing")
        all_pass = False
    if all_pass: print("  PASS")
    return all_pass

def main():
    print("=" * 60)
    print("  PHASE 2 VALIDATOR FIX VERIFICATION")
    print("=" * 60)
    results = [
        ("Clip Logic", test_clip_logic()),
        ("Grader Ranges", test_grader_range()),
        ("String Audit", check_forbidden_patterns()),
        ("Inference Compliance", check_inference_compliance()),
    ]
    print("\n" + "=" * 60)
    print("  TEST SUMMARY")
    print("=" * 60)
    final_pass = True
    for name, passed in results:
        status = "PASS" if passed else "FAIL"
        print(f"  {status}: {name}")
        if not passed: final_pass = False
    print("=" * 60)
    if final_pass: print("\n  ALL TESTS PASSED - SAFE TO SUBMIT")
    else: print("\n  TESTS FAILED")
    return int(0) if final_pass else int(1)

if __name__ == "__main__":
    sys.exit(main())
