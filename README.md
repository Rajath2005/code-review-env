---
title: Code Review Agent — OpenEnv
description: RL environment for training AI agents on Python code review
sdk: docker
app_port: 7860
models:
  - Qwen/Qwen2.5-72B-Instruct
---

# Code Review Agent — OpenEnv RL Benchmark

> **An OpenEnv RL environment for training and benchmarking AI agents on Python code review.**

## 🔥 Quick Links

### 🚀 **[Live Demo on HF Space](https://BugHunter28-code-review-env.hf.space)** ← Try it now!

| | |
|---|---|
| 📊 **[Benchmark Results](EVALUATION_RESULTS.md)** | Baseline agent scores |
| 📖 **[Full Documentation](.)** | Complete guide |
| 🐙 **[GitHub Source](https://github.com/Rajath2005/code-review-env)** | Master branch |

---

## 🔥 The Problem

Code review is the hardest part of shipping software fast — and there is **no standard RL environment** to train, compare, and benchmark agents for real code review. Tools like GitHub Copilot Review and CodeRabbit hint at the massive demand.

This environment provides:
- ✅ **3 difficulty levels** (identification → fixing → full review)
- ✅ **Objective grading** (dense rewards, not sparse end-of-episode)
- ✅ **Real-world dataset** (32+ hand-crafted Python snippets with test cases)
- ✅ **OpenEnv compliant** (standard RL training loop)
- ✅ **Live demo** (Hugging Face Spaces)

---

## 🎯 The RL Loop (Agent Perspective)

**This is a Markov Decision Process**, not just a tool. Here's how agents interact:

```
state = env.reset(task_name="bug_identification")
    ↓ state contains: code_snippet, task_name, instructions, feedback, reward, done
    
for step in range(max_steps):
    action = agent.act(state)      # agent's response: bug type / code / JSON
    state = env.step(action)        # environment returns: observation + reward + done
    
    if state.done:
        break
```

**Key**: At each step, the agent receives:
- 📝 **Observation**: code snippet + task instructions
- 💰 **Reward** (0.0–1.0): immediate signal on how well it did
- ✋ **Done**: whether episode ended (agent solved task or hit max steps)

---

## 📊 State | Action | Reward (Formal Definition)

### **State Space** — What the agent sees:

```python
class CodeReviewObservation(Observation):
    code_snippet: str            # Python code to review
    task_name: str               # "bug_identification" | "bug_fixing" | "full_review"
    instructions: str            # Task-specific instructions
    feedback: Optional[str]      # Grader feedback from previous step (null on first)
    reward: float                # Reward from previous step (0.0 on reset)
    done: bool                   # Episode complete? (False on reset)
```

### **Action Space** — What the agent can do:

```python
class CodeReviewAction(Action):
    response: str  # Agent's answer (bug type string / fixed code / JSON review)
```

### **Reward Function** — How agents are scored:

| Task | Reward Signal | Interpretation |
|------|---------------|-----------------|
| **Bug ID (Easy)** | 0.0 / 0.7 / 1.0 | Wrong / Partial keyword match / Exact or alias |
| **Bug Fix (Medium)** | 0.0–1.0 | Proportional to test cases passed |
| **Full Review (Hard)** | 0.0–1.0 | F1-score (precision + recall) per category + severity bonus |

**Dense signals at EVERY step** → stable training, not sparse end-of-episode.

---

## 🚀 Live Demo

**Hugging Face Space**: https://BugHunter28-code-review-env.hf.space

Try it: select task → submit answer → see reward immediately.

---

## 📋 Quick Example: One Complete Episode

**Task**: `bug_identification` (Easy)

### Step 0: Reset Environment
```python
observation = env.reset(task_name="bug_identification")
```

**Agent sees:**
```json
{
  "code_snippet": "def sum_list(nums):\n    total = 0\n    for i in range(len(nums) + 1):\n        total += nums[i]\n    return total",
  "task_name": "bug_identification",
  "instructions": "Identify the bug and respond with ONLY the bug type as a short phrase.",
  "feedback": null,
  "reward": 0.0,
  "done": false
}
```

### Step 1: Agent Submits Answer
```python
action = CodeReviewAction(response="off-by-one error")
observation = env.step(action)
```

**Agent receives (next state):**
```json
{
  "code_snippet": "def sum_list(nums):\n    total = 0\n    for i in range(len(nums) + 1):\n        total += nums[i]\n    return total",
  "task_name": "bug_identification",
  "instructions": "Identify the bug and respond with ONLY the bug type as a short phrase.",
  "feedback": "✅ CORRECT: 'off-by-one error' matches expected bug type",
  "reward": 1.0,
  "done": true
}
```

**Result**: Agent got **1.0 reward** and episode ended. Perfect!

---

## 🎓 Why This Is an RL Environment (Not Just a "Tool")

| Aspect | Why It's RL | Implication |
|--------|-----------|------------|
| **Markov Property** | Current observation fully determines next state | Observable history satisfies MDP assumption ✓ |
| **Episode Structure** | Fixed max steps, clear terminal conditions | Agents learn when to stop attempting retry |
| **Reward Signal** | Exact, partial, and scored outcomes | Dense learning signal (better than pass/fail) |
| **Generalization** | 32+ diverse snippets, 3 difficulty levels | Curriculum learning + benchmarking possible |
| **Deterministic Grading** | Same response → same score (reproducible) | Fair multi-agent comparison |

**Bottom line**: You can train an RL policy end-to-end on this environment. It's not a one-shot API; it's an interactive problem-solving loop.

---

## 📋 Tasks

Three tasks of increasing difficulty, each with a programmatic grader scoring 0.0 – 1.0.

### Task 1: Bug Identification (Easy)
The agent receives a buggy Python function. It must identify the **bug type** — a short phrase like `"off-by-one error"` or `"infinite recursion"`.

**Reward**:
- 🟢 **1.0** — Exact match or recognized alias (e.g., "off by one" → "off-by-one error")
- 🟡 **0.7** — Partial keyword overlap (agent understood the category but phrasing differs)
- 🔴 **0.0** — Wrong or empty response

**Dataset**: 10 snippets covering: off-by-one, division by zero, wrong initial value, command injection, infinite recursion, null pointer dereference, list mutation, case sensitivity, resource leak, infinite loop, plus 10 more.

### Task 2: Bug Fixing (Medium)
The agent receives the same buggy snippet. It must return **corrected Python code** that passes all test cases.

**Reward** (partial credit):
- 🟢 **1.0** — All test cases pass
- 🟡 **0.6–0.9** — Majority of test cases pass (proportional: `passed / total`)
- 🟡 **0.3** — Code runs without syntax error but fails all test cases
- 🔴 **0.0** — Syntax error or exception on execution

**Example**:
- 3/4 test cases pass → reward = 0.75
- 1/4 test cases pass → reward = 0.25

**Grading**: Code executed in sandboxed Python namespace. Imports whitelisted (math, re, json, datetime, etc.). Timeout: 2.5 seconds per test.

### Task 3: Full Code Review (Hard)
The agent must produce a **structured JSON review** covering bugs, security issues, and style violations — each ordered by severity.

**Required output format**:
```json
{
  "bugs": [
    {"line": 3, "severity": "high", "description": "range(len(nums)+1) causes IndexError"}
  ],
  "security_issues": [],
  "style_violations": [
    {"line": 3, "severity": "low", "description": "Use enumerate() or sum() instead of manual loop"}
  ]
}
```

**Reward scoring** (total 1.0):
- 🎯 **40%** — Bugs found (F1-score: precision + recall on detected bugs)
- 🎯 **35%** — Security issues found (F1-score on security findings)
- 🎯 **15%** — Style violations found (F1-score on style findings)
- 🎯 **10%** — Correct severity ordering (high > medium > low within each category)

**Example**: If agent finds 2/3 bugs correctly, 1/2 security issues, 0/1 style issue, all in correct order:
- Bugs: (2/3) × 0.40 = 0.27
- Security: (1/2) × 0.35 = 0.175
- Style: 0 × 0.15 = 0
- Ordering: 1.0 × 0.10 = 0.10
- **Total reward ≈ 0.535**

---

## 📋 Code Snippet Dataset

**32 hand-crafted Python snippets**, each covering a distinct real-world bug class:

| Bug Type | Category | Example Issue |
|----------|----------|----------------|
| Off-by-one error | Logic | `range(len(nums) + 1)` → IndexError |
| Division by zero | Safety | Missing zero check before `/` |
| Wrong initial value | Logic | `total = 1` instead of `0` |
| Command injection | Security | Unsanitized shell command |
| Infinite recursion | Logic | Missing or wrong base case |
| Null pointer dereference | Safety | Access attribute on None |
| Mutating list while iterating | Logic | `nums.remove()` inside loop |
| Case sensitivity error | Logic | Missing `.lower()` for comparison |
| Resource leak | Safety | File not closed (missing context manager) |
| SQL injection | Security | String formatting in SQL query |
| ... and 22 more | Various | Real-world Python issues |

**Each snippet includes**:
- ✅ Buggy code (function definition)
- ✅ Bug type (canonical name + aliases)
- ✅ Fixed code (correct implementation)
- ✅ Test cases (5–10 per snippet with expected outputs)
- ✅ Full review (expected bugs, security, style findings)

---

## 🔍 For Judges: How to Evaluate This Environment

### **1. Verify It's a Real RL Environment**

**Check structure**:
```bash
curl http://localhost:7860/health
# Should return: {"status": "ok", "environment": "code-review-env", "tasks": [...]}
```

**Run one episode manually**:
```bash
# Reset to get initial observation
curl -X POST http://localhost:7860/reset \
  -H "Content-Type: application/json" \
  -d '{"task_name": "bug_identification"}'

# Submit an action (copy code_snippet from reset response, identify bug)
curl -X POST http://localhost:7860/step \
  -H "Content-Type: application/json" \
  -d '{"response": "off-by-one error"}'

# Result: {"feedback": "...", "reward": 1.0, "done": true}
```

✅ **Checklist**:
- [ ] `/reset` returns observation with code_snippet, task_name, instructions
- [ ] `/step` accepts action and returns reward + feedback + done
- [ ] Reward is numeric (0.0–1.0), determinate, reproducible
- [ ] Same action → same reward (determinism verified)

---

### **2. Run the Benchmark**

```bash
# Evaluate 3 agents (weak/baseline/strong) on all tasks
python scripts/benchmark.py --num-episodes 10 --seed 42 --json results.json

# Output: JSON + formatted table showing:
#   - Weak agent: ~0.13 avg reward (random responses)
#   - Baseline: ~0.46 avg reward (heuristic matching)
#   - Gold: ~0.67 avg reward (oracle - proves environment grading works)
#
# Proves the environment provides meaningful signal
```

**See [EVALUATION_RESULTS.md](EVALUATION_RESULTS.md) for detailed baseline numbers and analysis.**

**Expected results** (from version 0.1.0):

| Agent | Easy | Medium | Hard | Overall |
|-------|------|--------|------|---------|
| Weak (random) | 0.15 | 0.05 | 0.10 | **0.10** |
| Baseline (heuristic) | 0.65 | 0.40 | 0.30 | **0.45** |
| Strong (GPT-4 caliber) | 0.88 | 0.72 | 0.65 | **0.75** |

*Baseline = rule-based responses; Strong = LLM with code understanding.*

---

### **3. Verify Reproducibility**

```bash
# Run 1: seed 42
python scripts/benchmark.py --num-episodes 5 --seed 42

# Run 2: seed 42 (again)
python scripts/benchmark.py --num-episodes 5 --seed 42

# Should be IDENTICAL scores (down to 3 decimal places)
```

Guarantees: Same agent → same reward, always. Fair for multi-agent comparison.

---

### **4. Metrics Interpretation**

| Metric | What It Measures | Benchmark Threshold |
|--------|-----------------|-------------------|
| **Easy task avg reward** | Bug-naming accuracy | Weak: 0.1, Baseline: 0.6, Strong: 0.85+ |
| **Medium task avg reward** | Code-fixing capability | Weak: 0.05, Baseline: 0.4, Strong: 0.70+ |
| **Hard task avg reward** | Structured review quality | Weak: 0.1, Baseline: 0.3, Strong: 0.65+ |
| **Overall (mean of tasks)** | Agent overall code review skill | Weak: 0.08, Baseline: 0.43, Strong: 0.73+ |

---

### **5. Integration with RL Training**

To train an RL agent on this environment:

```python
from server.environment import CodeReviewEnvironment

env = CodeReviewEnvironment()

for episode in range(num_episodes):
    obs = env.reset(task_name="bug_identification")  # or bug_fixing / full_review
    
    for step in range(5):  # max 5 steps per episode
        action = agent.act(obs)  # agent's policy
        obs = env.step(action)
        
        # Use obs.reward for training signal
        agent.train(reward=obs.reward, done=obs.done)
        
        if obs.done:
            break
```

No external datasets needed; grading is built-in.

---

## 🔑 Technical Specifications

### Observation & Action Spaces (Detailed)

**Observation (what agent sees)**:
```python
class CodeReviewObservation(Observation):
    code_snippet: str            # Raw Python code string
    task_name: str               # "bug_identification" | "bug_fixing" | "full_review"
    instructions: str            # Task-specific instruction text
    feedback: Optional[str]      # Grader feedback from previous step
    reward: float                # Reward from last step [0.0, 1.0]
    done: bool                   # Episode over?
```

**Action (what agent submits)**:
```python
class CodeReviewAction(Action):
    response: str  # Varies by task:
                  # - Easy:   bug type phrase (str)
                  # - Medium: Python code (str, may contain newlines)
                  # - Hard:   JSON string (parsed and graded)
```

**Episode Parameters**:
- Max steps per episode: **5**
- Terminal condition: `done=true` when task solved OR max steps reached
- Reward range: **[0.0, 1.0]** (always valid numeric)

---

## 📁 Project Structure

```
.
├── data/
│   └── snippets.py                 # 32 hand-crafted code snippets + test cases
├── scripts/
│   ├── benchmark.py                # Multi-agent evaluation (weak/baseline/strong)
│   └── eval_batch.py               # Deprecated: use benchmark.py
├── server/
│   ├── app.py                      # FastAPI server (OpenEnv endpoints)
│   ├── environment.py              # Core RL environment implementation
│   └── __init__.py
├── tasks/
│   ├── task_easy.py                # Bug identification grader
│   ├── task_medium.py              # Bug fixing grader
│   ├── task_hard.py                # Full review grader
│   └── __init__.py
├── web/
│   ├── index.html                  # Web UI (optional, for manual testing)
│   ├── script.js
│   └── styles.css
├── inference.py                    # Example: LLM-based agent
├── client.py                       # Example: Python client
├── models.py                       # Pydantic models (shared types)
├── openenv.yaml                    # OpenEnv metadata
├── pyproject.toml                  # Python package config
├── DEPLOYMENT_SUMMARY.md           # Deployment notes
├── Dockerfile                      # Docker build for HF Spaces
├── run_tests.py                    # Quick test suite
└── README.md                       # This file
```

---

## ▶️ Running Locally

### **Quick Start** (Recommended)

```bash
# Install dependencies
pip install -e .

# Start the server (auto-reload enabled)
uvicorn server.app:app --host 0.0.0.0 --port 7860 --reload
```

Then open: **http://localhost:7860**

### **With Docker**

```bash
docker build -t code-review-env .
docker run -p 7860:7860 code-review-env
```

---

## 📊 Benchmarking Your Own Agent

### **Run Built-in Benchmark** (3 reference agents)

```bash
python scripts/benchmark.py \
  --num-episodes 10 \
  --seed 42 \
  --output results.json
```

**Output**: Table + JSON file with scores per task.

### **Benchmark Your Custom Agent**

1. Create a class implementing `Agent` interface:

```python
class MyAgent:
    def act(self, observation: dict) -> str:
        # observation has: code_snippet, task_name, instructions, feedback
        # return: your response (bug type / fixed code / JSON review)
        return agent_response
```

2. Edit `scripts/benchmark.py` to include your agent:

```python
agents = {
    "my_custom_agent": MyAgent(),
}

python scripts/benchmark.py --agent my_custom_agent
```

---

## 🧪 Testing

```bash
# Quick sanity check
python run_tests.py

# Verbose output
python run_tests.py --verbose
```

Verifies:
- ✅ All 3 tasks reset correctly
- ✅ Rewards in valid range [0.0, 1.0]
- ✅ Test execution sandbox works (for medium task)
- ✅ JSON parsing (for hard task)

---

## 🔄 Reproducibility & Determinism

**This environment is fully deterministic**:

✅ **Observation**: Same episode → always same code snippet (by seed)  
✅ **Reward**: Same response → always same score (no randomness in grading)  
✅ **Action execution**: Deterministic Python code execution (sandboxed, timeout-protected)

**How to ensure reproducibility**:

```bash
# Always specify seed for training runs
python scripts/benchmark.py --seed 42

# In custom training:
import random
random.seed(42)
env = CodeReviewEnvironment()
```

When submitting results in papers or reports, always state: **"Evaluation uses seed 42. All experiments are reproducible on request."**

---

## ✨ Key Design Decisions

| Decision | Rationale | Trade-off |
|----------|-----------|-----------|
| **Dense rewards** | Enables faster training | Requires more grading logic |
| **3-difficulty curriculum** | Agents can learn progressively | More tasks to implement |
| **Sandboxed execution** | Safe code evaluation | Timeout + import restrictions |
| **F1-based hard task** | Rewards precision AND recall | More complex scoring |
| **Fixed 5-step episodes** | Agents learn strategic stopping | May be too short for complex reviews |

---

## 📚 References

- **OpenEnv Spec**: https://github.com/openenv-dev/openenv-core
- **Hugging Face Spaces**: https://huggingface.co/docs/hub/spaces
- **RL Benchmarking**: https://openrl-benchmark.com/

---

## 📝 License

MIT License — See LICENSE file for details.

---

## 📧 Questions?

- **Report bugs**: Open an issue on GitHub
- **Discuss features**: Use Discussions tab
- **Live demo**: https://BugHunter28-code-review-env.hf.space
