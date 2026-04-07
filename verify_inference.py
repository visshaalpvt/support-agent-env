import re
import os

def verify_inference_py(filepath="inference.py"):
    """Verify inference.py against Phase 2 submission checklist"""

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
    if 'os.getenv("API_BASE_URL")' in content or 'os.environ.get("API_BASE_URL"' in content:
        results['API_BASE_URL'] = True
        print("   ✅ API_BASE_URL read from environment")
    else:
        results['API_BASE_URL'] = False
        print("   ❌ API_BASE_URL not read from environment")

    # Check 2: API_KEY from env (or HF_TOKEN fallback)
    print("\n2. Checking API_KEY from environment...")
    if 'os.getenv("API_KEY")' in content or 'os.environ.get("API_KEY"' in content:
        results['API_KEY'] = True
        print("   ✅ API_KEY read from environment")
    else:
        results['API_KEY'] = False
        print("   ❌ API_KEY not read from environment")

    # Check 3: MODEL_NAME from env
    print("\n3. Checking MODEL_NAME from environment...")
    if 'os.getenv("MODEL_NAME"' in content or 'os.environ.get("MODEL_NAME"' in content:
        results['MODEL_NAME'] = True
        print("   ✅ MODEL_NAME read from environment")
    else:
        results['MODEL_NAME'] = False
        print("   ❌ MODEL_NAME not read from environment")

    # Check 4: OpenAI Client import
    print("\n4. Checking OpenAI Client import...")
    if 'from openai import' in content:
        results['openai_import'] = True
        print("   ✅ OpenAI client imported")
    else:
        results['openai_import'] = False
        print("   ❌ OpenAI client not imported")

    # Check 5: AsyncOpenAI initialization with base_url and api_key
    print("\n5. Checking AsyncOpenAI client initialization...")
    if 'AsyncOpenAI(base_url=API_BASE_URL' in content:
        results['openai_init'] = True
        print("   ✅ AsyncOpenAI initialized with API_BASE_URL and API_KEY")
    else:
        results['openai_init'] = False
        print("   ❌ AsyncOpenAI not initialized correctly")

    # Check 6: Actual API call (chat.completions.create)
    print("\n6. Checking for actual LLM API calls...")
    if 'chat.completions.create' in content:
        results['api_call'] = True
        print("   ✅ Makes actual API calls via chat.completions.create")
    else:
        results['api_call'] = False
        print("   ❌ No API calls found — judges require real proxy usage")

    # Check 7: No hardcoded API keys
    print("\n7. Checking for hardcoded API keys...")
    has_hardcoded = bool(re.search(r'["\']sk-[a-zA-Z0-9]{10,}["\']', content))
    if not has_hardcoded:
        results['no_hardcoded_keys'] = True
        print("   ✅ No hardcoded API keys found")
    else:
        results['no_hardcoded_keys'] = False
        print("   ❌ HARDCODED API KEY DETECTED — remove immediately!")

    # Check 8: No fallback bypass logic
    print("\n8. Checking for fallback bypass logic...")
    has_fallback = 'USE_FALLBACK' in content or 'get_classification_fallback' in content
    if not has_fallback:
        results['no_fallback'] = True
        print("   ✅ No fallback bypass — all calls go through proxy")
    else:
        results['no_fallback'] = False
        print("   ❌ Fallback logic detected — this bypasses the judges' proxy!")

    # Check 9: [START] log format
    print("\n9. Checking [START] log format...")
    if '[START]' in content and 'task=' in content and 'env=' in content:
        results['start_log'] = True
        print("   ✅ [START] log found with required fields")
    else:
        results['start_log'] = False
        print("   ❌ [START] log missing or malformed")

    # Check 10: [STEP] log format
    print("\n10. Checking [STEP] log format...")
    if '[STEP]' in content and 'step=' in content and 'reward=' in content:
        results['step_log'] = True
        print("   ✅ [STEP] log found with required fields")
    else:
        results['step_log'] = False
        print("   ❌ [STEP] log missing or malformed")

    # Check 11: [END] log format
    print("\n11. Checking [END] log format...")
    if '[END]' in content and 'success=' in content and 'score=' in content:
        results['end_log'] = True
        print("   ✅ [END] log found with required fields")
    else:
        results['end_log'] = False
        print("   ❌ [END] log missing or malformed")

    # Check 12: Validation — hard fail if env vars missing
    print("\n12. Checking env var validation (hard fail)...")
    if 'raise ValueError' in content or 'raise RuntimeError' in content:
        results['env_validation'] = True
        print("   ✅ Raises error if env vars missing")
    else:
        results['env_validation'] = False
        print("   ❌ No validation — script should fail if API_BASE_URL/API_KEY missing")

    # Summary
    print("\n" + "=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)

    passed = sum(results.values())
    total = len(results)

    for check, status in results.items():
        status_str = "✅ PASS" if status else "❌ FAIL"
        print(f"{status_str} - {check}")

    print(f"\nTotal: {passed}/{total} checks passed")

    if passed == total:
        print("\n🎉 PERFECT! inference.py is fully Phase 2 compliant!")
        print("   Ready to submit — all proxy, logging, and validation checks pass.")
    else:
        print(f"\n⚠️ {total - passed} issues found. Fix before submission.")

    return passed == total

if __name__ == "__main__":
    verify_inference_py()
