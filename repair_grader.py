import re

def fix_safe_grader():
    with open('safe_grader.py', 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Silence stdout
    content = content.replace(
        'print("✅ SAFE_GRADER loaded - ALL scores forced to (0.01, 0.99)", flush=True)',
        'import sys; sys.stderr.write("INFO: SAFE_GRADER loaded - ALL scores forced to (0.01, 0.99)\\n"); sys.stderr.flush()'
    )

    # 2. Buffer grade_hard scores
    content = content.replace('base = 0.10', 'base = 0.05')
    content = content.replace('base(+0.10)', 'base(+0.05)')

    # 3. Add assertions
    # Add to grade_easy
    content = content.replace(
        'score = force_safe(score)',
        'score = force_safe(score)\n    assert 0.01 <= score <= 0.99, f"CRITICAL: grade_easy score {score} out of range"'
    )

    # Add to grade_medium and grade_hard (they both use 'total = force_safe(total)')
    content = content.replace(
        'total = force_safe(total)',
        'total = force_safe(total)\n    assert 0.01 <= total <= 0.99, f"CRITICAL: grader total {total} out of range"'
    )

    with open('safe_grader.py', 'w', encoding='utf-8') as f:
        f.write(content)

if __name__ == "__main__":
    fix_safe_grader()
    print("repaired safe_grader.py")
