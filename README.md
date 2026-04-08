---
title: Code Review Agent
emoji: 🧠
colorFrom: blue
colorTo: green
sdk: docker
pinned: false
tags:
  - openenv
---

# Code Review Agent — OpenEnv RL Benchmark

> An RL environment for training and evaluating AI agents on real-world Python code review tasks.

## 🔥 The Problem

Code review is the hardest part of shipping software fast, and tools like GitHub Copilot Review and CodeRabbit prove the massive industry demand for automation. But **there is no standard RL environment to train, compare, and benchmark agents for real code review**.

This **Code Review Environment** fixes that with a production-like OpenEnv gym that scores:
- Real bugs (identification)
- Real fixes (with test-case execution)
- Real structured reviews (with security & style analysis)

## 🚀 Live Demo

**Hugging Face Space**: https://BugHunter28-code-review-env.hf.space

Quick start: Open the Space, select a task, and submit your answer to see rewards in action.

---

## Tasks

Three tasks of increasing difficulty, each with a programmatic grader scoring 0.0 – 1.0.

### Task 1: Bug Identification (Easy)
The agent receives a buggy Python function. It must identify the **bug type** — a short phrase like `"off-by-one error"` or `"infinite recursion"`.

- **Reward 1.0** — exact match or recognised alias
- **Reward 0.7** — partial keyword overlap (agent understood the category)
- **Reward 0.0** — wrong or empty

### Task 2: Bug Fixing (Medium)
The agent receives the same buggy snippet. It must return **corrected Python code** that passes all test cases.

- **Reward 1.0** — all test cases pass
- **Reward 0.3–0.9** — proportional to test cases passed
- **Reward 0.0** — syntax error or all tests fail

The grader executes the submitted code in a sandboxed namespace and runs test cases automatically.

### Task 3: Full Code Review (Hard)
The agent must produce a **structured JSON review** covering bugs, security issues, and style violations — each ordered by severity.

```json
{
  "bugs": [
    {"line": 3, "severity": "high", "description": "range(len(nums)+1) causes IndexError"}
  ],
  "security_issues": [],
  "style_violations": [
    {"line": 3, "severity": "low", "description": "Use enumerate() instead of manual index loop"}
  ]
}
```

Scoring uses F1-style precision + recall per category, plus a severity ordering bonus:

| Component | Weight |
|-----------|--------|
| Bugs found | 40% |
| Security issues found | 35% |
| Style violations found | 15% |
| Correct severity ordering | 10% |

---

## Observation & Action Spaces

### Observation
```python
class CodeReviewObservation(Observation):
    code_snippet: str       # the Python function to review
    task_name: str          # bug_identification | bug_fixing | full_review
    instructions: str       # what the agent must do
    feedback: Optional[str] # feedback from previous step
    reward: float           # last step reward (inherited)
    done: bool              # episode over (inherited)
```

### Action
```python
class CodeReviewAction(Action):
    response: str  # agent's output — bug name, fixed code, or JSON review
```

### Reward Function
- Partial credit at every step — never just sparse end-of-episode signal
- Easy: keyword matching with aliases (tolerates natural phrasing variation)
- Medium: proportional to test cases passed (rewards partial fixes)
- Hard: F1-style per category + ordering bonus (rewards structured, well-prioritised output)

---

## Code Snippet Dataset

10 hand-crafted Python snippets, each covering a distinct real-world bug class:

| # | Bug Type | Category |
|---|----------|----------|
| 0 | Off-by-one error | Logic |
| 1 | Division by zero | Safety |
| 2 | Wrong initial value | Logic |
| 3 | Command injection | Security |

---

## 📁 Project Structure

```
.
├── data/
│   └── snippets.py                # Code snippet dataset
├── scripts/
│   └── eval_batch.py              # Batch evaluation script
├── server/
│   ├── app.py                     # FastAPI server
│   └── environment.py             # OpenEnv gym implementation
├── tasks/
│   ├── task_easy.py               # Bug identification grader
│   ├── task_medium.py             # Bug fixing grader
│   └── task_hard.py               # Full review grader
├── web/
│   ├── index.html                 # UI frontend
│   ├── script.js                  # JavaScript handler
│   └── styles.css                 # Styling
├── client.py                      # Example client
├── inference.py                   # Inference agent
├── openenv.yaml                   # OpenEnv config
├── pyproject.toml                 # Python package config
└── README.md                      # This file
```

---

## ▶️ Running Locally

### Option A: Editable Install (Recommended)
```bash
pip install -e .
uvicorn server.app:app --host 0.0.0.0 --port 7860
```

### Option B: With Requirements File
```bash
pip install -r requirements.txt
uvicorn server.app:app --host 0.0.0.0 --port 7860
```

Then open `http://localhost:7860` in your browser.

---

## 📊 Batch Evaluation

Test the environment systematically with built-in evaluation:

```bash
python scripts/eval_batch.py                    # Summary results
python scripts/eval_batch.py --detail           # Detailed per-task breakdown
python scripts/eval_batch.py --json             # JSON output for CI/CD
```

Threshold flags for regression testing:
- `--fail-threshold-easy 0.8`
- `--fail-threshold-medium 0.7`
- `--fail-threshold-hard 0.6`

---

## 🧪 Quick API Test

```bash
curl -X POST http://localhost:7860/reset \
  -H "Content-Type: application/json" \
  -d '{"task_name": "bug_identification"}'

# Response:
# {
#   "code_snippet": "def sum_list(nums):\n    ...",
#   "task_name": "bug_identification",
#   "instructions": "Read the Python code...",
#   "feedback": null,
#   "reward": 0.0,
#   "done": false
# }
```

---

## ✨ Key Features

- **Multi-level tasks** progressing from easy identification to hard structured reviews
- **Intelligent grading** with exact, partial, and weighted scoring
- **Test-case execution** for bug-fixing validation
- **Production dataset** with 32+ real-world Python snippets
- **OpenEnv compatible** for standard RL training
- **Hugging Face Spaces ready** for instant deployment
- **Dense rewards** for stable training signal

---

## 🏁 Why Judges Will Love This

1. **Real-world impact**: Code review is a $$$-time bottleneck every software team faces
2. **Objective grading**: Not just pass/fail — dense, reproducible rewards per task
3. **Complete pipeline**: From raw code → identification → fixing → full review
4. **Deployed and tested**: Running live on Hugging Face Spaces with immediate demo access
5. **Open-source**: Building a benchmark the entire RL community can use

---

## 📝 License

MIT - See LICENSE file for details.
