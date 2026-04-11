# 🎯 How to Configure HF Space Links & Description

## Quick Answer: Where to Put Links

Your HF Space has **3 places** where links appear:

### 1. 📄 **README.md** (Top Priority - Main Description)
This is what everyone sees first. Edit your README.md:

```markdown
# Code Review Agent — OpenEnv

🚀 **[Live Demo](https://BugHunter28-code-review-env.hf.space)** ← Try it now!

[Source Code](https://github.com/Rajath2005/code-review-env) | [Docs](https://github.com/Rajath2005/code-review-env)
```

### 2. 🏷️ **Tags** (Side Panel)
Edit your `README.md` YAML frontmatter:

```yaml
---
title: Code Review Agent
emoji: 🧠
colorFrom: blue
colorTo: green
sdk: docker
pinned: false
tags:
  - openenv
  - rl
  - code-review
---
```

### 3. ⚙️ **app.yaml** (Advanced Configuration)
Create this file in your repo root for advanced settings:

```yaml
title: Code Review Agent — OpenEnv
description: Interactive RL environment for Python code review. Try the live demo!
sdk: docker
app_port: 7860
models:
  - url: https://BugHunter28-code-review-env.hf.space
    description: Live Demo
```

---

## Step-by-Step: Add Links to Your HF Space

### **Step 1: Update Main README (✅ Already Done)**
Your main `README.md` now has prominent links at the top.

### **Step 2: Configure Space via Web UI**
1. Go to: https://huggingface.co/spaces/BugHunter28/code-review-env/settings
2. Scroll to "About"
3. Add this description:

```
🚀 Interactive RL environment for Python code review

Try Live Demo: https://BugHunter28-code-review-env.hf.space

3 Tasks: Bug ID (Easy) | Bug Fix (Medium) | Full Review (Hard)

Deterministic env with ~32 code snippets and reward grading.

📖 GitHub: https://github.com/Rajath2005/code-review-env
```

### **Step 3: Add Metadata (Optional)**
In your repo, create `app.yaml`:

```yaml
title: Code Review Agent
description: OpenEnv RL environment for Python code review - bug identification, fixing, and structured review
sdk: docker
app_port: 7860
tags: [openenv, reinforcement-learning, code-review]
models:
  - url: https://BugHunter28-code-review-env.hf.space
    name: Live Demo
```

---

## 📊 What Links Show Where

```
HF Space Page Structure:

┌─────────────────────────────────────────────┐
│                                             │
│  Space Title: Code Review Agent            │  ← Title
│  ⭐ Like  💬 Comments                      │
│                                             │
├──────────────────┬──────────────────────────┤
│                  │                          │
│  README Content  │  📊 Side Panel:         │
│  (from .md file) │  - Tags                 │
│                  │  - Models (if app.yaml) │
│  🚀 Links here   │  - About                │
│                  │  - License              │
│                  │  - Links (if specified) │
│                  │                          │
└──────────────────┴──────────────────────────┘
```

---

## ✅ What You Should Do Right Now

1. ✅ Push the updated README (with links) - **Already done**
2. ⬜ Go to Settings: https://huggingface.co/spaces/BugHunter28/code-review-env/settings
3. ⬜ Update the "About" description with:
   ```
   🚀 Live Demo: https://BugHunter28-code-review-env.hf.space
   📖 GitHub: https://github.com/Rajath2005/code-review-env
   ```

---

## 🎨 Pro Tips

### Emoji Guide (What Works in Descriptions)
```
🚀 Launch/Demo
📍 Location/Link
🐙 GitHub
📊 Data/Results
🎯 Goal/Target
⚡ Quick/Fast
🔧 Setup/Config
📖 Documentation
🧠 AI/ML
```

### Perfect HF Space Description Example

```
🧠 OpenEnv RL Environment for Code Review

🚀 Live Demo: https://BugHunter28-code-review-env.hf.space
📖 GitHub: https://github.com/Rajath2005/code-review-env/blob/master

Three Tasks:
🟢 Bug ID (Easy) - Name the bug
🟡 Bug Fix (Medium) - Write corrected code  
🔴 Full Review (Hard) - JSON audit

Features:
✅ Deterministic reward grading
✅ 32+ real-world Python snippets
✅ Dense training signals
✅ Reproducible evaluation (seed=42)

Try the UI or use API endpoints directly!
```

---

## 📱 How It Looks to Judges

### **What They See First:**
```
┌─ Code Review Agent ─────────────────────────────┐
│ Interactive RL environment for Python code review
│
│ 🚀 Live Demo: https://BugHunter28-code-review-env.hf.space
│ 📖 GitHub: https://github.com/Rajath2005/code-review-env
│
│ [Reset]  [Start Review]        Task: [selector]
│
│ Code Snippet ▼                Result ▼
│ ...                            Reward: 1.0
│                               Status: ✅
└─────────────────────────────────────────────────┘

Right side panel:
├─ Tags: openenv, rl, code-review
├─ Models: 1
├─ Created: 2026-04-08
└─ About:
   🚀 Live Demo: https://BugHunter28-code-review-env.hf.space
```

---

## ⚡ One More Thing: Are Static Files Working?

Test in browser console:

```javascript
// Open DevTools (F12), go to Console tab, paste:
fetch('/health').then(r => r.json()).then(console.log)
```

You should see:
```json
{
  "status": "ok",
  "environment": "code-review-env",
  "tasks": ["bug_identification", "bug_fixing", "full_review"]
}
```

If you see an error, the Space rebuild is still in progress (wait 2-3 min).

---

## Summary

✅ Links in README - **Already done**  
⬜ Test at https://BugHunter28-code-review-env.hf.space - **Try it!**  
⬜ Update Space "About" - **Optional but recommended**  
⬜ Create app.yaml - **Advanced, skip for now**

**Everything is ready for submission!** 🎯
