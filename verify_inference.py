import re
import os

def verify_inference_py(filepath="inference.py"):
    """Verify inference.py against pre-submission checklist"""
    
    print("=" * 60)
    print("PRE-SUBMISSION CHECKLIST VERIFICATION")
    print("=" * 60)
    
    if not os.path.exists(filepath):
        print("❌ inference.py not found!")
        return False
    
    with open(filepath, "r") as f:
        content = f.read()
    
    results = {}
    
    # Check 1: API_BASE_URL variable
    print("\n1. Checking API_BASE_URL...")
    if 'API_BASE_URL = os.environ.get("API_BASE_URL"' in content or "API_BASE_URL = os.getenv" in content:
        results['API_BASE_URL'] = True
        print("   ✅ API_BASE_URL defined correctly")
    else:
        results['API_BASE_URL'] = False
        print("   ❌ API_BASE_URL missing or incorrect")
    
    # Check 2: MODEL_NAME variable
    print("\n2. Checking MODEL_NAME...")
    if 'MODEL_NAME = os.environ.get("MODEL_NAME"' in content or "MODEL_NAME = os.getenv" in content:
        results['MODEL_NAME'] = True
        print("   ✅ MODEL_NAME defined correctly")
    else:
        results['MODEL_NAME'] = False
        print("   ❌ MODEL_NAME missing or incorrect")
    
    # Check 3: HF_TOKEN variable
    print("\n3. Checking HF_TOKEN...")
    if 'HF_TOKEN = os.environ.get("HF_TOKEN"' in content or "HF_TOKEN = os.getenv" in content:
        results['HF_TOKEN'] = True
        print("   ✅ HF_TOKEN defined correctly")
    else:
        results['HF_TOKEN'] = False
        print("   ❌ HF_TOKEN missing")
    
    # Check 4: OpenAI Client import
    print("\n4. Checking OpenAI Client import...")
    if 'from openai import' in content:
        results['openai_import'] = True
        print("   ✅ OpenAI client imported")
    else:
        results['openai_import'] = False
        print("   ❌ OpenAI client not imported")
    
    # Check 5: OpenAI Client initialization
    print("\n5. Checking OpenAI Client initialization...")
    if 'AsyncOpenAI(' in content or 'OpenAI(' in content:
        results['openai_init'] = True
        print("   ✅ OpenAI client initialized")
    else:
        results['openai_init'] = False
        print("   ❌ OpenAI client not initialized")
    
    # Check 6: [START] log format
    print("\n6. Checking [START] log format...")
    start_match = re.search(r'print\(f?\[START\].*?\)', content)
    if start_match:
        results['start_log'] = True
        print(f"   ✅ [START] log found: {start_match.group(0)[:80]}...")
    else:
        results['start_log'] = False
        print("   ❌ [START] log missing")
    
    # Check 7: [STEP] log format
    print("\n7. Checking [STEP] log format...")
    step_match = re.search(r'print\(f?\[STEP\].*?\)', content)
    if step_match:
        results['step_log'] = True
        print(f"   ✅ [STEP] log found: {step_match.group(0)[:80]}...")
    else:
        results['step_log'] = False
        print("   ❌ [STEP] log missing")
    
    # Check 8: [END] log format
    print("\n8. Checking [END] log format...")
    end_match = re.search(r'print\(f?\[END\].*?\)', content)
    if end_match:
        results['end_log'] = True
        print(f"   ✅ [END] log found: {end_match.group(0)[:80]}...")
    else:
        results['end_log'] = False
        print("   ❌ [END] log missing")
    
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
        print("\n🎉 PERFECT! inference.py meets ALL pre-submission requirements!")
        print("   You are ready to check the box and submit!")
    else:
        print(f"\n⚠️ {total - passed} issues found. Please fix before submission.")
    
    return passed == total

if __name__ == "__main__":
    verify_inference_py()
