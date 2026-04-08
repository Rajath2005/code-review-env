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

# 🎯 Code Review Agent — OpenEnv RL Environment

**Live Demo: https://BugHunter28-code-review-env.hf.space**

## ⚡ Quick Links

| Link | Purpose |
|------|---------|
| **[🌐 Live UI](https://BugHunter28-code-review-env.hf.space)** | Interactive demo - try it now! |
| **[📚 GitHub (Master)](https://github.com/Rajath2005/code-review-env/tree/master)** | Source code & documentation |
| **[📊 Evaluation Guide](https://github.com/Rajath2005/code-review-env/blob/master/EVALUATION_RESULTS.md)** | Baseline results & metrics |
| **[📖 Full README](https://github.com/Rajath2005/code-review-env)** | Complete documentation |

---

## 🚀 What Is This?

An **OpenEnv RL environment** for training AI agents to perform Python code review. Three difficulty levels:

- 🟢 **Easy**: Bug Identification (name the bug type)
- 🟡 **Medium**: Bug Fixing (produce corrected code)
- 🔴 **Hard**: Full Review (JSON audit with bugs, security, style)

---

## 🎮 Interactive Demo

**Try it here**: https://BugHunter28-code-review-env.hf.space

1. Select a task (Easy/Medium/Hard)
2. Click "Reset" to load a code snippet
3. Submit your response
4. Get immediate **reward score** (0.0 - 1.0)

---

## 📊 Baseline Evaluation

| Agent | Easy | Medium | Hard | Overall |
|-------|------|--------|------|---------|
| Random | 0.0 | 0.0 | 0.4 | 0.13 |
| Baseline Heuristic | 1.0 | 0.0 | 0.37 | 0.46 |
| Gold (Oracle) | 1.0 | 0.0 | 1.0 | 0.67 |

👉 See full analysis: [EVALUATION_RESULTS.md](https://github.com/Rajath2005/code-review-env/blob/master/EVALUATION_RESULTS.md)

---

## 🔗 API Endpoints

```bash
# Health check
curl https://bughunter28-code-review-env.hf.space/health

# Start episode
curl -X POST https://bughunter28-code-review-env.hf.space/reset \
  -H "Content-Type: application/json" \
  -d '{"task_name": "bug_identification"}'

# Submit action
curl -X POST https://bughunter28-code-review-env.hf.space/step \
  -H "Content-Type: application/json" \
  -d '{"response": "off-by-one error"}'
```

---

## 📋 Repository Structure

```
code-review-env/
├── script.benchmark.py         # Multi-agent evaluation
├── EVALUATION_RESULTS.md       # Baseline metrics
├── README.md                   # Full documentation
├── server/
│   ├── app.py                 # FastAPI server
│   └── environment.py         # RL environment
├── tasks/
│   ├── task_easy.py          # Bug identification
│   ├── task_medium.py        # Bug fixing  
│   └── task_hard.py          # Full review
└── web/
    ├── index.html            # UI interface
    ├── script.js             # JavaScript logic
    └── styles.css            # Styling
```

---

## 🎓 For Judges

✅ **Environment**: Proper OpenEnv with state/action/reward  
✅ **Reproducibility**: Seed-based deterministic scoring  
✅ **Evaluation**: Automated benchmarking with baselines  
✅ **UI**: Interactive demo for manual testing  
✅ **Code**: Open source on GitHub master branch  

---

## 📞 Support

- **Issues?** → Check [GitHub Issues](https://github.com/Rajath2005/code-review-env/issues)
- **Questions?** → See [Full README](https://github.com/Rajath2005/code-review-env)
- **Want to train?** → Use `python scripts/benchmark.py` or create custom agents

---

**Made for OpenEnv Hackathon 2026** 🏆
