#!/usr/bin/env python3
"""
Verify all rewards in FULL ENV API are strictly (0.01, 0.99).
Tests reset()/step() + JSON serialization matching Scaler validation.
"""

import sys
import json
sys.path.insert(0, '.')

from server.environment import CodeReviewEnvironment, CodeReviewAction
from data.snippets import SNIPPETS


def check_json_reward(name: str, obs_json: dict) -> bool:
    """Validate reward field in API JSON response."""
    score = obs_json.get('reward', 0.0)
    if not (0.0 < score < 1.0):
        print(f"  ❌ {name}: JSON reward {score} violates (0,1)")
        return False
    print(f"  ✅ {name}: JSON reward {score:.4f}")
    return True


def test_all_tasks():
    """Test all 3 tasks via full environment cycles."""
    print("\n" + "="*80)
    print("FULL ENV API BOUNDARY VERIFICATION (reset/step + JSON)")
    print("="*80)
    
    all_pass = True
    env = CodeReviewEnvironment(seed=42)  # Deterministic
    
    tasks = [
        ("bug_identification", lambda s: s["bug_type"]),
        ("bug_fixing", lambda s: s.get("fixed_code", "def broken(): pass")),
        ("full_review", lambda s: json.dumps(s.get("review", {}))),
    ]
    
    for task_name, gold_resp_fn in tasks:
        print(f"\n🧪 TASK: {task_name.upper()}")
        
        # Reset + initial reward check
        obs = env.reset(task_name)
        if not check_json_reward(f"{task_name}-reset", obs.model_dump()):
            all_pass = False
        
        # Gold response (must match the snippet selected by reset(), not a fixed index)
        st = env.state()
        snippet = next(s for s in SNIPPETS if s["id"] == st.snippet_id)
        gold_resp = gold_resp_fn(snippet)
        step_obs = env.step(CodeReviewAction(response=gold_resp))
        if not check_json_reward(f"{task_name}-gold", step_obs.model_dump()):
            all_pass = False
        
        # Bad response (single-step tasks end after gold; start a fresh episode)
        env.reset(task_name)
        bad_resp = "INVALID" if task_name != "full_review" else "{}"
        step_obs = env.step(CodeReviewAction(response=bad_resp))
        if not check_json_reward(f"{task_name}-bad", step_obs.model_dump()):
            all_pass = False
    
    return all_pass


if __name__ == "__main__":
    print("█"*80)
    print(" SCALER PHASE 2 BOUNDARY VALIDATION - FULL ENV API TEST")
    print("█"*80)
    print("\nAll JSON 'reward' MUST be in (0,1) - never exactly 0.0 or 1.0")
    
    passed = test_all_tasks()
    
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    status = "✅ PASS - Ready for HF deploy & Scaler resubmit!" if passed else "❌ FAIL - Fix rewards first"
    print(status)
    
    print("\n" + "█"*80)
    sys.exit(0 if passed else 1)

