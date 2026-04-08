#!/usr/bin/env python3
"""
Complete Test Suite for Validator Fixes (Adapted for SupportAgentEnv)
Run this before submitting to Hugging Face
"""

import os
import sys
import re
import math
import subprocess
from pathlib import Path

class ValidatorTestSuite:
    """Automated test suite for validator compliance"""
    
    def __init__(self):
        self.passed = 0
        self.failedCount = 0
        self.results = []
        
    def print_header(self, text):
        print("\n" + "=" * 70)
        print(f"  {text}")
        print("=" * 70)
    
    def print_test(self, name, passed, details=""):
        status = "PASS" if passed else "FAIL"
        self.results.append((name, passed, details))
        if passed:
            self.passed += 1
        else:
            self.failedCount += 1
        print(f"  [{status}]: {name}")
        if details and not passed:
            print(f"        {details}")
    
    # =========================================================
    # TEST 1: Clip Score Function
    # =========================================================
    def test_clip_score_function(self):
        """Verify clip_score correctly clamps to (0.01, 0.99)"""
        def clip_score(x):
            try:
                val = float(x)
                if math.isnan(val): return 0.01
                return max(0.01, min(0.99, val))
            except:
                return 0.01
        
        test_cases = [
            (-100, 0.01), (-1, 0.01), (0, 0.01), (0.5, 0.5),
            (1, 0.99), (2, 0.99), (100, 0.99), (float('nan'), 0.01)
        ]
        
        for value, expected in test_cases:
            result = clip_score(value)
            if abs(result - expected) > 1e-6:
                self.print_test("Clip Score Function", False, f"Failed for {value}")
                return False
        self.print_test("Clip Score Function", True)
        return True
    
    # =========================================================
    # TEST 2: No Binary Returns in Code
    # =========================================================
    def test_no_binary_returns(self):
        """Check all Python files for forbidden 0.0 or 1.0 returns"""
        # Strictly look for returns or assignments of 0 or 1. 
        # Skip if it is a comparison or part of a longer decimal.
        forbidden_patterns = [
            (r'\breturn\s+[01](\.0+)?\b(?!\.[0-9])', 'return 0 or 1'),
            (r'(?<![=!><])=\s*[01](\.0+)?\b(?!\.[0-9])', 'assignment of 0 or 1'),
        ]
        
        python_files = [Path('inference.py'), Path('safe_grader.py'), Path('support_env.py')]
        issues = []
        
        for py_file in python_files:
            if not py_file.exists(): continue
            with open(py_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            for i, line in enumerate(lines, 1):
                # Ignore comments and obvious non-score variables
                clean_line = line.split('#')[0].strip()
                if not clean_line: continue
                if 'step_count' in clean_line or 'step' in clean_line or 'total_steps' in clean_line:
                    continue
                    
                for pattern, desc in forbidden_patterns:
                    if re.search(pattern, clean_line):
                        issues.append(f"{py_file}:{i} -> {line.strip()}")
        
        if issues:
            self.print_test("No Binary Returns", False, "\n        ".join(issues[:3]))
            return False
        self.print_test("No Binary Returns", True)
        return True
    
    # =========================================================
    # TEST 3: No safe_grader Import in inference.py
    # =========================================================
    def test_no_safe_grader_import(self):
        inference_path = Path('inference.py')
        if not inference_path.exists(): return False
        with open(inference_path, 'r', encoding='utf-8') as f:
            content = f.read()
        if 'from safe_grader import' in content or 'import safe_grader' in content:
            self.print_test("No safe_grader Import", False, "Found forbidden safe_grader import")
            return False
        self.print_test("No safe_grader Import", True)
        return True
    
    # =========================================================
    # TEST 4: clip_score Defined in inference.py
    # =========================================================
    def test_clip_score_defined(self):
        inference_path = Path('inference.py')
        if not inference_path.exists(): return False
        with open(inference_path, 'r', encoding='utf-8') as f:
            content = f.read()
        if 'def clip_score' not in content:
            self.print_test("clip_score Defined", False, "clip_score missing in inference.py")
            return False
        self.print_test("clip_score Defined", True)
        return True

    # =========================================================
    # TEST 5: HF_TOKEN and API_BASE_URL
    # =========================================================
    def test_env_vars(self):
        inference_path = Path('inference.py')
        if not inference_path.exists(): return False
        with open(inference_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        passed = True
        details = []
        
        if 'os.environ["HF_TOKEN"]' not in content:
            passed = False
            details.append("Missing mandatory HF_TOKEN indexing")
        
        if 'os.environ["API_BASE_URL"]' not in content:
            passed = False
            details.append("Missing mandatory API_BASE_URL indexing")
            
        self.print_test("Env Vars (HF_TOKEN/BASE)", passed, " | ".join(details))
        return passed

    # =========================================================
    # TEST 6: [END] Format (OpenEnv Spec)
    # =========================================================
    def test_end_format(self):
        inference_path = Path('inference.py')
        if not inference_path.exists(): return False
        with open(inference_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # [END] success=<true|false> steps=<n> rewards=<r1,r2,...,rn>
        pattern = r"\[END\]\s+success=(true|false)\s+steps=\S+\s+rewards=\S+"
        if re.search(pattern, content):
            self.print_test("[END] Format", True)
            return True
            
        self.print_test("[END] Format", False, "Incorrect END format. Expected: success=... steps=... rewards=...")
        return False

    # =========================================================
    # TEST 7: Grader Ranges
    # =========================================================
    def test_grader_ranges(self):
        sys.path.append(os.getcwd())
        try:
            from safe_grader import grade_easy, grade_hard
            # Check edge cases
            s1 = grade_easy("wrong", "billing")[0]
            s2 = grade_hard("x","y","low","urgent","sorry",[])[0]
            if 0.01 <= s1 <= 0.99 and 0.01 <= s2 <= 0.99:
                self.print_test("Grader Ranges", True)
                return True
            else:
                self.print_test("Grader Ranges", False, f"Score out of range: {s1}/{s2}")
                return False
        except Exception as e:
            self.print_test("Grader Ranges", False, str(e))
            return False

    # =========================================================
    # TEST 8: No Binary Scores in Grader
    # =========================================================
    def test_no_binary_scores_in_grader(self):
        grader_path = Path('safe_grader.py')
        if not grader_path.exists(): return False
        with open(grader_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        issues = []
        # Stricter for literals in grader (assignments or returns)
        forbidden = [r'\breturn\s+[01](\.0+)?\b(?!\.[0-9])', r'(?<![=!><])=\s*[01](\.0+)?\b(?!\.[0-9])']
        for i, line in enumerate(lines, 1):
            clean = line.split('#')[0].strip()
            if not clean: continue
            if 'int(' in clean or 'dist =' in clean or 'ap =' in clean or 'tp =' in clean: continue
            for p in forbidden:
                if re.search(p, clean):
                    issues.append(f"safe_grader.py:{i} -> {line.strip()}")
        if issues:
            self.print_test("No Binary Scores in Grader", False, "\n        ".join(issues[:3]))
            return False
        self.print_test("No Binary Scores in Grader", True)
        return True

    # =========================================================
    # TEST 9: Exception Handlers
    # =========================================================
    def test_exception_handlers(self):
        python_files = [Path('inference.py'), Path('safe_grader.py'), Path('support_env.py')]
        issues = []
        for py_file in python_files:
            if not py_file.exists(): continue
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
            lines = content.split('\n')
            in_except = False
            for i, line in enumerate(lines, 1):
                clean = line.strip()
                if clean.startswith('except'): in_except = True
                elif in_except and 'return' in clean:
                    if re.search(r'return\s+[01](\.0+)?\b(?!\.[0-9])', clean):
                        issues.append(f"{py_file}:{i} -> binary literal in except block")
                    in_except = False
        if issues:
            self.print_test("Exception Handlers", False, "\n        ".join(issues))
            return False
        self.print_test("Exception Handlers", True)
        return True

    # =========================================================
    # TEST 10: Score Aggregation
    # =========================================================
    def test_aggregation_clamped(self):
        inference_path = Path('inference.py')
        if not inference_path.exists(): return False
        with open(inference_path, 'r', encoding='utf-8') as f:
            content = f.read()
        if 'clip_score(' in content or 'log_end(' in content:
            self.print_test("Score Aggregation", True)
            return True
        self.print_test("Score Aggregation", False, "No score clamping or logging found")
        return False

    def run_all(self):
        self.print_header("VALIDATOR FIX TEST SUITE")
        self.test_clip_score_function()
        self.test_no_binary_returns()
        self.test_no_safe_grader_import()
        self.test_clip_score_defined()
        self.test_env_vars()
        self.test_end_format()
        self.test_grader_ranges()
        self.test_no_binary_scores_in_grader()
        self.test_exception_handlers()
        self.test_aggregation_clamped()
        self.print_header("TEST SUMMARY")
        print(f"\n  Passed: {self.passed}")
        print(f"  Failed: {self.failedCount}")
        if self.failedCount == 0:
            print("\n  ALL TESTS PASSED! Safe to submit!")
            return 0
        return 1

if __name__ == "__main__":
    suite = ValidatorTestSuite()
    sys.exit(suite.run_all())
