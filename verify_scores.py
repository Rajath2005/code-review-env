#!/usr/bin/env python3
"""
Verify that all task scores are strictly within (0, 1) range.
Tests all three tasks with various inputs to ensure no score equals 0.0 or 1.0.
"""

import sys
import json
sys.path.insert(0, '.')

from tasks.task_easy import run_easy_task
from tasks.task_medium import run_medium_task
from tasks.task_hard import run_hard_task
from data.snippets import SNIPPETS


def check_score(name: str, score: float) -> bool:
    """Verify score is strictly between 0 and 1."""
    if score <= 0.0:
        print(f"  ❌ {name}: Score is {score} (violates: must be > 0.0)")
        return False
    if score >= 1.0:
        print(f"  ❌ {name}: Score is {score} (violates: must be < 1.0)")
        return False
    if isinstance(score, float) and (score == int(score)):
        print(f"  ⚠️  {name}: Score is {score} (integer, might be problematic)")
        return False
    print(f"  ✅ {name}: {score:.4f}")
    return True


def test_easy_task():
    """Test easy task scores with various responses."""
    print("\n" + "="*60)
    print("TESTING: Bug Identification (Easy)")
    print("="*60)
    
    all_pass = True
    
    # Test with correct answer
    for snippet in SNIPPETS[:3]:
        score, feedback, done = run_easy_task(snippet["bug_type"], snippet["id"])
        if not check_score(f"Easy-{snippet['id']} (correct)", score):
            all_pass = False
    
    # Test with incorrect answers
    for snippet in SNIPPETS[:2]:
        score, feedback, done = run_easy_task("random garbage text xyz", snippet["id"])
        if not check_score(f"Easy-{snippet['id']} (wrong)", score):
            all_pass = False
    
    return all_pass


def test_medium_task():
    """Test medium task scores."""
    print("\n" + "="*60)
    print("TESTING: Bug Fixing (Medium)")
    print("="*60)
    
    all_pass = True
    
    # Test with correct fixed code
    for snippet in SNIPPETS[:3]:
        if snippet.get("fixed_code"):
            score, feedback, done = run_medium_task(snippet["fixed_code"], snippet["id"])
            if not check_score(f"Medium-{snippet['id']} (correct)", score):
                all_pass = False
    
    # Test with incorrect code
    for snippet in SNIPPETS[:2]:
        score, feedback, done = run_medium_task("def broken(): pass\n# total garbage", snippet["id"])
        if not check_score(f"Medium-{snippet['id']} (wrong)", score):
            all_pass = False
    
    return all_pass


def test_hard_task():
    """Test hard task scores."""
    print("\n" + "="*60)
    print("TESTING: Full Code Review (Hard)")
    print("="*60)
    
    all_pass = True
    
    # Test with correct review
    for snippet in SNIPPETS[:2]:
        if snippet.get("review"):
            response = json.dumps(snippet["review"])
            score, feedback, done = run_hard_task(response, snippet["id"])
            if not check_score(f"Hard-{snippet['id']} (correct)", score):
                all_pass = False
    
    # Test with invalid JSON
    score, feedback, done = run_hard_task("not json", SNIPPETS[0]["id"])
    if not check_score(f"Hard-0 (invalid json)", score):
        all_pass = False
    
    # Test with missing keys
    score, feedback, done = run_hard_task('{}', SNIPPETS[0]["id"])
    if not check_score(f"Hard-0 (missing keys)", score):
        all_pass = False
    
    # Test with empty lists
    empty_review = {"bugs": [], "security_issues": [], "style_violations": []}
    score, feedback, done = run_hard_task(json.dumps(empty_review), SNIPPETS[0]["id"])
    if not check_score(f"Hard-0 (empty review)", score):
        all_pass = False
    
    return all_pass


if __name__ == "__main__":
    print("\n" + "█"*60)
    print("  SCORE BOUNDARIES VERIFICATION TEST")
    print("█"*60)
    print("\nAll scores MUST be strictly within (0, 1):")
    print("  - Cannot be exactly 0.0")
    print("  - Cannot be exactly 1.0")
    print("  - Must use clamping to 0.01-0.99")
    
    results = []
    results.append(("Easy Task", test_easy_task()))
    results.append(("Medium Task", test_medium_task()))
    results.append(("Hard Task", test_hard_task()))
    
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    for task_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {task_name}")
    
    all_passed = all(p for _, p in results)
    
    print("\n" + "█"*60)
    if all_passed:
        print("  ✅ ALL SCORES ARE VALID - Ready for HF deployment!")
        print("█"*60)
        sys.exit(0)
    else:
        print("  ❌ SOME SCORES VIOLATE CONSTRAINTS - DO NOT DEPLOY!")
        print("█"*60)
        sys.exit(1)
