# Code Review Environment - Testing Guide

## 🎯 Why You're Getting Reward: 0.00

Your UI is **working correctly**. The **reward 0.00 means your answer is INCORRECT**, not that the system is broken.

---

## 📋 Task-Specific Response Formats

### **TASK 1: Bug Identification (Easy) ✓ SIMPLEST**

**What to do:**
- Read the buggy code
- Respond with ONLY the bug type (short phrase)
- **No explanation, no markdown, nothing else**

**Examples of CORRECT answers:**
```
off-by-one error
division by zero
wrong initial value
infinite loop
command injection
null pointer dereference
```

**Examples of WRONG answers:**
```
❌ There is an off-by-one error
❌ off-by-one
❌ The bug is off-by-one error
❌ off by one error (might work if in synonym list)
```

**Scoring:**
- ✅ 1.0 = Exact match + known aliases
- 🟡 0.7 = Partial keyword overlap
- ❌ 0.0 = Completely wrong

**SNIPPET 0 (available on load):**
```python
def sum_list(nums):
    total = 0
    for i in range(len(nums) + 1):  # ← BUG HERE
        total += nums[i]
    return total
```
✅ **CORRECT ANSWER:** `off-by-one error`

---

### **TASK 2: Bug Fixing (Medium) ⚠️ HARDER**

**What to do:**
- Read the buggy code
- Respond with ONLY the corrected Python function
- **No markdown fences, no explanation**
- The fixed code must pass all test cases

**Format:**
```
def function_name(args):
    # corrected code here
    return value
```

**WRONG format:**
```
❌ ```python
def sum_list(nums):
    ...
```

❌ Here's the fix:
def sum_list(nums):
    ...
```

**Scoring:**
- ✅ 1.0 = All test cases pass
- 🟡 0.6-0.9 = Majority pass (proportional)
- 🟡 0.3 = Code runs but fails tests
- ❌ 0.0 = Syntax error / exception

**SNIPPET 0 - TEST CASES:**
```python
Input: [1, 2, 3]     → Expected: 6
Input: [10, 20]      → Expected: 30
Input: [0]           → Expected: 0
Input: []            → Expected: 0
```

❌ **WRONG:** Just copying the buggy code (will get 0.0)

✅ **CORRECT:**
```
def sum_list(nums):
    total = 0
    for i in range(len(nums)):
        total += nums[i]
    return total
```

---

### **TASK 3: Full Code Review (Hard) 🔥 MOST COMPLEX**

**What to do:**
- Read the code carefully
- Respond with ONLY a JSON object
- **No markdown, no explanation**
- Structure: `{"bugs": [...], "security_issues": [...], "style_violations": [...]}`

**Format per finding:**
```json
{
  "line": 3,
  "severity": "high",
  "description": "Descriptive message about the issue"
}
```

**WRONG Format:**
```
❌ ```json
{
  ...
}
```

❌ The bugs are:
- Line 3: ...

❌ {"bugs": ["off-by-one error"]}  (missing structure)
```

**Severity levels:**
- `"high"` — Critical bug or security issue
- `"medium"` — Important but not critical
- `"low"` — Minor, style, or optimization

**Scoring breakdown:**
- 40% — Bugs found (precision + recall)
- 35% — Security issues found
- 15% — Style violations found
- 10% — Correct severity ordering

**SNIPPET 0 - EXPECTED REVIEW:**
```json
{
  "bugs": [
    {
      "line": 3,
      "severity": "high",
      "description": "range(len(nums) + 1) causes IndexError on last iteration"
    }
  ],
  "security_issues": [],
  "style_violations": [
    {
      "line": 3,
      "severity": "low",
      "description": "Use enumerate() or sum() instead of manual index loop"
    }
  ]
}
```

---

## ✅ Step-by-Step Testing

### **Test 1: Easy Task (Bug Identification)**

1. Open the UI in browser
2. Select: **"Bug Identification (Easy)"**
3. Click: **"Start Review"** (green button)
4. You'll see: A buggy Python snippet
5. **Look for the bug type** (from the list above)
6. Type your answer in the textarea
7. Click: **"Submit Response"**
8. **Check Result:**
   - ✅ If correct → Status shows "Correct", Reward shows 1.00
   - ❌ If wrong → Status shows "Incorrect", Reward shows 0.00

### **Test 2: Medium Task (Bug Fixing)**

1. Select: **"Bug Fixing (Medium)"**
2. Click: **"Start Review"**
3. You'll see: A buggy function with a note about test cases
4. **Write the corrected code** (no markdown, just code)
5. Click: **"Submit Response"**
6. **Check Result:**
   - ✅ If all tests pass → Reward 1.00
   - 🟡 If partial pass → Reward 0.6-0.9
   - ❌ If syntax error → Reward 0.0

### **Test 3: Hard Task (Full Review)**

1. Select: **"Full Review (Hard)"**
2. Click: **"Start Review"**
3. **Analyze the code** for:
   - Bugs (logic errors, runtime errors)
   - Security issues (injection, unsafe operations)
   - Style violations (inefficiency, bad practices)
4. **Write JSON response** with all three categories
5. Click: **"Submit Response"**
6. **Check Result:**
   - ✅ If you found all issues → High reward
   - 🟡 If you found some → Medium reward
   - ❌ If invalid JSON → Reward 0.0

---

## 🐛 Common Issues & Fixes

| Issue | Cause | Fix |
|-------|-------|-----|
| Reward 0.00 always | Answer format wrong | Read task format carefully above |
| Reward 0.00 always | Answer is empty | Make sure you type something |
| Reward 0.00 always | Using markdown in medium/hard | Remove ``` fences |
| Episode Incorrect | Syntax error in code (medium) | Check Python syntax |
| No reward appearing | API not responding | Check browser console (F12) |
| Episode Complete | Already submitted once | Click "Reset" button |

---

## 🔍 Debug (Browser Console)

Open **F12 → Console** and check for errors:

```javascript
// Should see: POST to /step endpoint
// Should see: Response with reward field
```

If you see network errors:
- ❌ API might be down
- ❌ CORS might be blocking requests
- ❌ Wrong URL in API_BASE_URL

---

## ✨ UI Checks (After CSS Fixes)

- [ ] No text overlapping in Result panel ✓
- [ ] Feedback text wraps cleanly ✓
- [ ] Reward value is visible and readable ✓
- [ ] Status pill shows correct status ✓
- [ ] Code snippets scroll properly ✓
- [ ] Layout is clean and professional ✓

---

## 📌 Summary

**Your system is working correctly!** The 0.00 reward means you're just entering the wrong answer format or wrong logic. Use the examples above to understand what each task expects, and you'll get positive rewards.

🎉 **Now try again with the correct formats!**
