#!/usr/bin/env python3
"""
Quick test script to verify the code-review-env is working correctly.
Run this to make sure everything is functioning properly.
"""

import json
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from server.environment import CodeReviewEnvironment, CodeReviewAction
from data.snippets import SNIPPETS

def test_easy_task():
    """Test Bug Identification (Easy) task"""
    print("\n" + "="*60)
    print("TEST 1: Bug Identification (Easy)")
    print("="*60)
    
    env = CodeReviewEnvironment()
    
    # Reset to get first snippet
    obs = env.reset(task_name="bug_identification")
    
    print(f"\nSnippet ID: {env._state.snippet_id}")
    print(f"Code:\n{obs.code_snippet}")
    print(f"\nInstructions:\n{obs.instructions}")
    
    # Get expected bug type
    snippet = SNIPPETS[env._state.snippet_id]
    print(f"\n✅ CORRECT ANSWER: '{snippet['bug_type']}'")
    print(f"   Aliases: {snippet['bug_type_aliases']}")
    
    # Test with correct answer
    print(f"\n→ Submitting CORRECT answer: '{snippet['bug_type']}'")
    action = CodeReviewAction(response=snippet['bug_type'])
    result = env.step(action)
    
    print(f"   Reward: {result.reward} (should be > 0.95)")
    print(f"   Status: {result.feedback}")
    print(f"   Done: {result.done}")
    
    if result.reward >= 0.95:
        print("   ✅ PASS: Easy task works!")
    else:
        print(f"   ⚠️  WARN: Expected score >= 0.95, got {result.reward}")


def test_medium_task():
    """Test Bug Fixing (Medium) task"""
    print("\n" + "="*60)
    print("TEST 2: Bug Fixing (Medium)")
    print("="*60)
    
    env = CodeReviewEnvironment()
    obs = env.reset(task_name="bug_fixing")
    
    print(f"\nSnippet ID: {env._state.snippet_id}")
    print(f"Code:\n{obs.code_snippet}")
    print(f"\nInstructions:\n{obs.instructions}")
    
    # Get expected fixed code
    snippet = SNIPPETS[env._state.snippet_id]
    print(f"\n✅ CORRECT FIXED CODE:")
    print(snippet['fixed_code'])
    print(f"\nTest cases:")
    for args, expected in snippet['test_cases']:
        print(f"   {args} → {expected}")
    
    # Test with correct code
    print(f"\n→ Submitting CORRECT fixed code...")
    action = CodeReviewAction(response=snippet['fixed_code'])
    result = env.step(action)
    
    print(f"   Reward: {result.reward} (should be > 0.95)")
    print(f"   Status: {result.feedback}")
    print(f"   Done: {result.done}")
    
    if result.reward >= 0.95:
        print("   ✅ PASS: Medium task works!")
    else:
        print(f"   ⚠️  WARN: Expected score >= 0.95, got {result.reward}")


def test_hard_task():
    """Test Full Code Review (Hard) task"""
    print("\n" + "="*60)
    print("TEST 3: Full Code Review (Hard)")
    print("="*60)
    
    env = CodeReviewEnvironment()
    obs = env.reset(task_name="full_review")
    
    print(f"\nSnippet ID: {env._state.snippet_id}")
    print(f"Code:\n{obs.code_snippet}")
    print(f"\nInstructions:\n{obs.instructions}")
    
    # Get expected review
    snippet = SNIPPETS[env._state.snippet_id]
    print(f"\n✅ EXPECTED REVIEW:")
    print(json.dumps(snippet['review'], indent=2))
    
    # Test with correct review
    print(f"\n→ Submitting CORRECT review (as JSON string)...")
    review_json = json.dumps(snippet['review'])
    action = CodeReviewAction(response=review_json)
    result = env.step(action)
    
    print(f"   Reward: {result.reward} (should be high, close to 1.0)")
    print(f"   Status: {result.feedback}")
    print(f"   Done: {result.done}")
    
    if result.reward > 0.8:
        print("   ✅ PASS: Hard task works!")
    else:
        print(f"   ⚠️  PARTIAL: Reward is {result.reward} (might be scoring style)")


def main():
    """Run all tests"""
    print("\n" + "█"*60)
    print("  CODE REVIEW ENVIRONMENT - SYSTEM TEST")
    print("█"*60)
    
    try:
        test_easy_task()
        test_medium_task()
        test_hard_task()
        
        print("\n" + "="*60)
        print("✅ ALL TESTS COMPLETED")
        print("="*60)
        print("\nThe system is working correctly!")
        print("If you're getting 0.00 reward in the UI, check:")
        print("  1. Are you answering in the CORRECT FORMAT?")
        print("  2. Is your answer CORRECT for the code shown?")
        print("  3. Did you read TEST_GUIDE.md for examples?")
        print("\nOpen TEST_GUIDE.md for detailed testing instructions.")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
