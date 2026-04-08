---
title: Code Review Agent
emoji: 🔍
colorFrom: blue
colorTo: green
sdk: docker
pinned: false
tags:
  - openenv
  - reinforcement-learning
---
# Code Review Environment — OpenEnv RL Benchmark

## 🔥 Hook
Code review is the hardest part of shipping software fast, and tools like GitHub Copilot Review and CodeRabbit prove the demand for automation. But there is no standard RL environment to train, compare, and benchmark agents for real code review.
**Code Review Environment** fixes that with a production-like OpenEnv gym that scores real bugs, real fixes, and real structured reviews.

## 🚀 Live Demo
Hugging Face Space: https://BugHunter28-code-review-env.hf.space

Quick test:
- Open the Space
- Call `/reset` and `/step` with any task name to see rewards in action

## 🧠 What This Project Does
This is an OpenEnv-compatible RL environment where an agent learns the loop:
`reset → observe code → step(action) → reward → repeat`.

Each episode delivers a buggy Python snippet plus clear instructions. The agent responds with a bug label, a fix, or a structured review, and gets dense, reproducible rewards.

## 🎯 Tasks Breakdown
Three tasks, one environment, increasing difficulty:

1. **bug_identification (easy)**
   - Output a short bug type phrase (example: "off-by-one error")
   - Partial credit for correct category or synonym

2. **bug_fixing (medium)**
   - Output corrected Python code (no explanation)
   - Auto-graded via test execution in a sandbox

3. **full_review (hard)**
   - Output JSON with `bugs`, `security_issues`, `style_violations`
   - Findings ordered by severity (high → medium → low)

## ⚙️ How It Works
System flow is intentionally simple and agent-friendly:
- **FastAPI endpoints:** `GET /health`, `GET /tasks`, `POST /reset`, `POST /step`, `GET /state`
- **Dataset:** 32 real-world Python snippets with bug types, fixes, tests, and review labels
- **Grading:** each task has a dedicated scorer with partial rewards and structured feedback

## 🧪 Reward System (Core Innovation)
Dense rewards make RL training stable and realistic:

- **Partial rewards everywhere** — never a single sparse terminal score
- **Test-case scoring** — medium task reward scales with passing tests
- **F1 + severity weighting** — hard task scores per category and penalizes hallucinations

Hard task scoring weights:

| Component | Weight |
|---|---:|
| Bugs | 0.40 |
| Security issues | 0.35 |
| Style violations | 0.15 |
| Severity ordering | 0.10 |

## 💡 Why This Matters (Judge Bait)
- Code review is a $\$\text{time} + \text{risk}$ bottleneck across every software team
- AI review tools exist, but **no open RL benchmark** trains agents end-to-end on the task
- This environment enables apples-to-apples evaluation with objective rewards and real defects

## 🧱 Architecture
- **FastAPI backend** exposes OpenEnv endpoints for reset/step
- **OpenEnv integration** standardizes observations, actions, and rewards
- **Hugging Face Spaces** deployment for instant testing and demos

## ▶️ How to Run Locally
```bash
# Option A: editable install (recommended)
pip install -e .

# Option B: requirements file (if you prefer)
pip install -r requirements.txt

uvicorn server.app:app --host 0.0.0.0 --port 7860
```

## 📊 Evaluation
Batch evaluation is built in via [scripts/eval_batch.py](scripts/eval_batch.py).

```bash
python scripts/eval_batch.py
python scripts/eval_batch.py --detail
python scripts/eval_batch.py --json
```

Threshold flags are supported for regression checks:
- `--fail-threshold-easy`
- `--fail-threshold-medium`
- `--fail-threshold-medium-tested`
- `--fail-threshold-hard`

## 📁 Project Structure
```
.
├── data/
│   └── snippets.py
├── scripts/
│   └── eval_batch.py
├── server/
│   ├── app.py
│   └── environment.py
├── tasks/
│   ├── task_easy.py
│   ├── task_medium.py
│   └── task_hard.py
├── client.py
├── inference.py
├── models.py
├── openenv.yaml
└── pyproject.toml
```

## ✨ Key Highlights
- 32 real-world code snippets with labeled bugs, fixes, tests, and reviews
- Intelligent grading with partial credit, F1 scoring, and severity weighting
- Multi-task RL environment spanning identification, fixing, and full reviews
- Deployed on Hugging Face Spaces for instant demo

## 🏁 Conclusion
Code Review Environment turns a messy, real-world workflow into a clean RL benchmark. If you want to train or evaluate agents that actually understand code review, this is the gym.
