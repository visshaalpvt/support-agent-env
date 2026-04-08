"""Quick compliance check without emoji (Windows-safe)."""
import re

content = open("inference.py", "r", encoding="utf-8").read()

checks = [
    ("API_BASE_URL env", 'os.environ.get("API_BASE_URL"' in content),
    ("API_KEY env", 'os.environ.get("API_KEY"' in content),
    ("MODEL_NAME env", 'os.environ.get("MODEL_NAME"' in content),
    ("HF_TOKEN env", 'os.environ.get("HF_TOKEN"' in content),
    ("openai import", "from openai import" in content),
    ("AsyncOpenAI(base_url=API_BASE_URL", "AsyncOpenAI(base_url=API_BASE_URL" in content),
    ("api_key=API_KEY", "api_key=API_KEY" in content),
    ("chat.completions.create", "chat.completions.create" in content),
    ("no hardcoded sk- keys", not re.search(r'["\']sk-[a-zA-Z0-9]{10,}["\']', content)),
    ("no USE_FALLBACK", "USE_FALLBACK" not in content),
    ("[START] log", "[START]" in content and "task=" in content and "env=" in content),
    ("[STEP] log", "[STEP]" in content and "step=" in content and "reward=" in content),
    ("[END] log (rewards= or score=)", "[END]" in content and "success=" in content and ("rewards=" in content or "score=" in content)),
    ("[END] in finally", "finally:" in content and "[END]" in content),
    ("raise ValueError", "raise ValueError" in content),
]

passed = 0
for name, ok in checks:
    status = "PASS" if ok else "FAIL"
    if ok:
        passed += 1
    print(f"  [{status}] {name}")

print()
print(f"Total: {passed}/{len(checks)} checks passed")
raise SystemExit(0 if passed == len(checks) else 1)
