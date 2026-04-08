import sys
import subprocess
import os

def check_no_graders_import():
    """Fail if any file still imports graders.py"""
    failed_files = []
    for root, dirs, files in os.walk("."):
        for file in files:
            if file.endswith(".py") and file != "check_submission.py" and file != "fix_submission.ps1":
                path = os.path.join(root, file)
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                    if "from graders import" in content or "import graders" in content:
                        failed_files.append(path)
    
    if failed_files:
        print(f"❌ FAIL: These files still import graders.py:")
        for f in failed_files:
            print(f"  - {f}")
        return False
    print("✅ PASS: No files import graders.py")
    return True

def check_no_raw_returns():
    """Fail if any raw 0 or 1 returns exist"""
    import re
    failed = []
    # Pattern to catch return 0, return 1, return 0.0, return 1.0 (with or without ending newline/whitespace)
    pattern = re.compile(r'return\s+(0|1|0\.0|1\.0)\s*$', re.MULTILINE)
    for root, dirs, files in os.walk("."):
        for file in files:
            if file.endswith(".py"):
                path = os.path.join(root, file)
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                    matches = pattern.findall(content)
                    if matches:
                        failed.append(f"{path} (found {len(matches)} raw returns)")
                        
    if failed:
        print(f"❌ FAIL: Raw return values found:")
        for f in failed:
            print(f"  - {f}")
        return False
    print("✅ PASS: No raw 0/1 returns")
    return True

if __name__ == "__main__":
    print("Running Pre-Submission Validation...")
    ok1 = check_no_graders_import()
    ok2 = check_no_raw_returns()
    sys.exit(0 if (ok1 and ok2) else 1)
