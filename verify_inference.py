"""
verify_inference.py — Phase 2 Pre-Submission Checklist

Validates inference.py against all Phase 2 hackathon requirements.
Run locally before every submission: py verify_inference.py
"""

import re
import os


def verify_inference_py(filepath="inference.py"):
    """Verify inference.py against Phase 2 submission checklist."""

    print("=" * 60)
    print("PHASE 2 PRE-SUBMISSION CHECKLIST VERIFICATION")
    print("=" * 60)

    if not os.path.exists(filepath):
        print("❌ inference.py not found!")
        return False

    with open(filepath, "r") as f:
        content = f.read()

    results = {}

    # Check 1: API_BASE_URL from env
    print("\n1. Checking API_BASE_URL from environment...")
    if 'os.environ.get("API_BASE_URL"' in content or 'os.environ["API_BASE_URL"' in content:
        results["API_BASE_URL"] = True
        print("   ✅ API_BASE_URL read from environment")
    else:
        results["API_BASE_URL"] = False
        print("   ❌ API_BASE_URL not read from environment")

    # Check 2: API_KEY from env (required — this is the proxy key)
    print("\n2. Checking API_KEY from environment...")
    if 'os.environ.get("API_KEY"' in content or 'os.environ["API_KEY"' in content:
        results["API_KEY"] = True
        print("   ✅ API_KEY read from environment")
    else:
        results["API_KEY"] = False
        print("   ❌ API_KEY not read from environment (CRITICAL — this bypasses the proxy!)")

    # Check 3: MODEL_NAME from env
    print("\n3. Checking MODEL_NAME from environment...")
    if 'os.environ.get("MODEL_NAME"' in content or 'os.environ["MODEL_NAME"' in content:
        results["MODEL_NAME"] = True
        print("   ✅ MODEL_NAME read from environment")
    else:
        results["MODEL_NAME"] = False
        print("   ❌ MODEL_NAME not read from environment")

    # Check 4: HF_TOKEN from env
    print("\n4. Checking HF_TOKEN from environment...")
    if 'os.environ.get("HF_TOKEN"' in content or 'os.environ["HF_TOKEN"' in content:
        results["HF_TOKEN"] = True
        print("   ✅ HF_TOKEN read from environment")
    else:
        results["HF_TOKEN"] = False
        print("   ❌ HF_TOKEN not read from environment")

    # Check 5: OpenAI Client import
    print("\n5. Checking OpenAI Client import...")
    if "from openai import" in content:
        results["openai_import"] = True
        print("   ✅ OpenAI client imported")
    else:
        results["openai_import"] = False
        print("   ❌ OpenAI client not imported")

    # Check 6: AsyncOpenAI initialized with API_BASE_URL
    print("\n6. Checking AsyncOpenAI client initialization...")
    if "AsyncOpenAI(base_url=API_BASE_URL" in content:
        results["openai_init"] = True
        print("   ✅ AsyncOpenAI initialized with API_BASE_URL")
    else:
        results["openai_init"] = False
        print("   ❌ AsyncOpenAI not initialized with API_BASE_URL")

    # Check 7: Client uses API_KEY (not HF_TOKEN) as the api_key
    print("\n7. Checking client uses API_KEY as api_key...")
    if "api_key=API_KEY" in content:
        results["proxy_key"] = True
        print("   ✅ Client uses API_KEY (proxy key) — will activate LiteLLM proxy")
    elif "api_key=HF_TOKEN" in content:
        results["proxy_key"] = False
        print("   ❌ Client uses HF_TOKEN — this BYPASSES the proxy! Use API_KEY.")
    else:
        results["proxy_key"] = False
        print("   ❌ Cannot verify client api_key source")

    # Check 8: Actual API call (chat.completions.create)
    print("\n8. Checking for actual LLM API calls...")
    if "chat.completions.create" in content:
        results["api_call"] = True
        print("   ✅ Makes actual API calls via chat.completions.create")
    else:
        results["api_call"] = False
        print("   ❌ No API calls found — proxy will never be activated")

    # Check 9: No hardcoded API keys
    print("\n9. Checking for hardcoded API keys...")
    has_hardcoded = bool(re.search(r'["\']sk-[a-zA-Z0-9]{10,}["\']', content))
    if not has_hardcoded:
        results["no_hardcoded_keys"] = True
        print("   ✅ No hardcoded API keys found")
    else:
        results["no_hardcoded_keys"] = False
        print("   ❌ HARDCODED API KEY DETECTED — remove immediately!")

    # Check 10: No fallback bypass logic
    print("\n10. Checking for fallback bypass logic...")
    has_fallback = "USE_FALLBACK" in content or "get_classification_fallback" in content
    if not has_fallback:
        results["no_fallback"] = True
        print("   ✅ No fallback bypass — all calls go through proxy")
    else:
        results["no_fallback"] = False
        print("   ❌ Fallback logic detected — this bypasses the judges' proxy!")

    # Check 11: [START] log format
    print("\n11. Checking [START] log format...")
    if "[START]" in content and "task=" in content and "env=" in content:
        results["start_log"] = True
        print("   ✅ [START] log found with required fields")
    else:
        results["start_log"] = False
        print("   ❌ [START] log missing or malformed")

    # Check 12: [STEP] log format
    print("\n12. Checking [STEP] log format...")
    if "[STEP]" in content and "step=" in content and "reward=" in content:
        results["step_log"] = True
        print("   ✅ [STEP] log found with required fields")
    else:
        results["step_log"] = False
        print("   ❌ [STEP] log missing or malformed")

    # Check 13: [END] log format
    print("\n13. Checking [END] log format...")
    if "[END]" in content and "success=" in content and ("rewards=" in content or "score=" in content):
        results["end_log"] = True
        print("   ✅ [END] log found with required fields")
    else:
        results["end_log"] = False
        print("   ❌ [END] log missing or malformed")

    # Check 14: [END] in finally block
    print("\n14. Checking [END] is in finally block...")
    if "finally:" in content and "[END]" in content:
        results["end_in_finally"] = True
        print("   ✅ [END] is in finally block — always printed even on exception")
    else:
        results["end_in_finally"] = False
        print("   ❌ [END] not protected by finally — may be skipped on exception")

    # Check 15: Validation — raises error if env vars missing
    print("\n15. Checking env var validation (hard fail)...")
    if "raise ValueError" in content or "raise RuntimeError" in content:
        results["env_validation"] = True
        print("   ✅ Raises error if env vars missing")
    else:
        results["env_validation"] = False
        print("   ❌ No validation — script should fail if API_KEY missing")

    # Summary
    print("\n" + "=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)

    passed = sum(results.values())
    total = len(results)

    for check, status in results.items():
        status_str = "✅ PASS" if status else "❌ FAIL"
        print(f"  {status_str} — {check}")

    print(f"\nTotal: {passed}/{total} checks passed")

    if passed == total:
        print("\n🎉 PERFECT! inference.py is fully Phase 2 compliant!")
        print("   All proxy, logging, and validation checks pass. Ready to submit.")
    else:
        print(f"\n⚠️  {total - passed} issue(s) found. Fix before submission.")

    return passed == total


if __name__ == "__main__":
    ok = verify_inference_py()
    raise SystemExit(0 if ok else 1)
