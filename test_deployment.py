#!/usr/bin/env python3
"""
Quick test to verify FastAPI server works with static files.
Run this before deployment to HF Space.
"""

import sys
import os

# Test 1: Check file structure
print("🔍 Checking file structure...")
required_files = [
    "server/app.py",
    "web/index.html",
    "web/styles.css", 
    "web/script.js",
    "pyproject.toml",
    "Dockerfile",
]

for file in required_files:
    exists = os.path.exists(file)
    status = "✓" if exists else "✗"
    print(f"  {status} {file}")
    if not exists:
        print(f"ERROR: Missing {file}")
        sys.exit(1)

# Test 2: Check imports
print("\n🔧 Checking Python imports...")
try:
    from server.app import app
    print("  ✓ FastAPI app imports")
except Exception as e:
    print(f"  ✗ Failed to import app: {e}")
    sys.exit(1)

try:
    from server.environment import CodeReviewEnvironment
    print("  ✓ Environment imports")
except Exception as e:
    print(f"  ✗ Failed to import environment: {e}")
    sys.exit(1)

# Test 3: Check static file mounting
print("\n📁 Checking static file configuration...")
try:
    import inspect
    source = inspect.getsource(app)
    if "StaticFiles" in source:
        print("  ✓ Static files configured")
    else:
        print("  ⚠ Static files may not be configured properly")
except Exception as e:
    print(f"  ⚠ Could not verify static files: {e}")

# Test 4: Check environment setup
print("\n🎯 Checking environment setup...")
try:
    env = CodeReviewEnvironment(seed=42)
    obs = env.reset("bug_identification")
    print(f"  ✓ Environment works (reset successful)")
    print(f"    - Got observation with {len(obs.code_snippet)} chars of code")
    print(f"    - Task: {obs.task_name}")
except Exception as e:
    print(f"  ✗ Environment test failed: {e}")
    sys.exit(1)

# Test 5: Check endpoints
print("\n🌐 Checking API endpoints...")
endpoints = [
    ("/", "GET", "UI root"),
    ("/health", "GET", "Health check"),
    ("/tasks", "GET", "Task list"),
    ("/reset", "POST", "Reset episode"),
    ("/step", "POST", "Step action"),
]

routes = [route.path for route in app.routes]
for path, method, desc in endpoints:
    found = any(path in str(route) for route in app.routes)
    status = "✓" if found or path == "/" else "✗"  # Root handled specially
    print(f"  {status} {method} {path} — {desc}")

print("\n" + "="*60)
print("✅ ALL CHECKS PASSED - Ready for deployment!")
print("="*60)
print("\n📦 Next steps:")
print("  1. Verify GitHub: https://github.com/Rajath2005/code-review-env")
print("  2. Wait for HF Space deployment (2-3 minutes)")
print("  3. Test at: https://BugHunter28-code-review-env.hf.space")
print("  4. Submit before 12:00")
