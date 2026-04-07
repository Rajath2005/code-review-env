# Code Review Agent — OpenEnv Environment

> An RL environment for training and evaluating AI agents on real-world Python code review tasks.

## Problem Statement

Create a standardized RL environment where agents learn to identify bugs, fix code, and perform full reviews on Python snippets with objective grading and reproducible rewards.

## Hugging Face Space

Live deployment: https://BugHunter28-code-review-env.hf.space

## Why This Exists

Code review is one of the most time-consuming tasks in software development. Tools like CodeRabbit and GitHub Copilot Review demonstrate massive industry demand — but **no open RL environment exists to systematically train and benchmark agents on this problem**.

This environment fills that gap. It provides a structured, reproducible gym where agents learn to:
- Identify bug types from code
- Produce correct bug fixes verified by test execution
- Perform multi-category security and style audits

The environment is directly useful for the RL/agent research community to train, compare, and evaluate code-reviewing language models.

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

## How Reward Works

- Dense rewards with partial credit per step
- Easy task uses bug-type keyword matching
- Medium task scores by test-case pass rate
- Hard task scores F1 per category plus severity ordering bonus

---

## Code Snippet Dataset

10 hand-crafted Python snippets, each covering a distinct real-world bug class:

| # | Bug Type | Category |
|---|----------|----------|
| 0 | Off-by-one error | Logic |
| 1 | Division by zero | Safety |
| 2 | Wrong initial value | Logic |
| 3 | Command injection | Security |

## Run Locally

1. Install dependencies: `pip install -e .`
2. Start the server: `uvicorn server.app:app --host 0.0.0.0 --port 7860`
3. Run inference: `python inference.py`
