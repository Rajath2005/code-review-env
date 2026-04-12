---
title: Code Review Agent (HF Space)
emoji: 🧠
colorFrom: blue
colorTo: green
sdk: docker
app_port: 7860
pinned: false
---

> Lines above: [Hugging Face Space metadata](https://huggingface.co/docs/hub/spaces-config-reference) (must stay at the top of this file for the live Space). Everything from the next heading onward is the normal GitHub readme.

# Code Review Agent — OpenEnv RL Benchmark

> **An OpenEnv RL environment for training and benchmarking AI agents on Python code review.**

## Problem Statement (Real-world)

Modern code review tools rarely expose **structured, explainable training signals** for automated agents. Teams mix linters, ad-hoc PR comments, and opaque model scores—making it hard to **train, compare, and audit** agents that assist with real review work.

This environment simulates **human-like Python code review** as an interactive loop: an agent reads curated snippets, acts (name the bug, submit a fix, or emit a structured audit), and receives a **dense numeric reward** after each `step()`—so you can benchmark policies, run curriculum learning, and measure **partial progress** instead of a single pass/fail bit.

## Use Cases

- **Automated code review assistants** — reward-shaped feedback for models that suggest fixes and findings  
- **CI/CD and merge gates** — compare agents on the same tasks with a stable, programmatic rubric  
- **Security-focused workflows** — progression from bug naming → correct code → multi-category audit JSON  
- **Developer productivity tooling** — reproducible head-to-head evaluation of review agents  
- **Education and hiring** — consistent tasks, graders, and difficulty tiers (easy → medium → hard)

## What Makes This Unique?

- **Multi-dimensional grading (hard task)** — separate signals for bugs, security issues, and style, then a fused score  
- **Real-world-style scenarios** — hand-authored snippets with tests and gold reviews—not toy game MDPs  
- **Deterministic grading** — same response on the same snippet yields the same reward (stochasticity only from **which** snippet is drawn unless you fix `seed` on `reset`)  
- **Designed for agent training** — dense rewards every step, partial credit on medium/hard, clear episode boundaries  
- **OpenEnv + HF Space ready** — typed observations/actions, `openenv.yaml`, Docker, and a baseline `inference.py` that passed Phase-2 validation

## Architecture

| Layer | Role |
|------|------|
| **OpenEnv core** | `CodeReviewEnvironment` — `reset` / `step` / `state` in `server/environment.py` |
| **HTTP API** | FastAPI app — `/reset`, `/step`, `/health`, `/tasks` in `server/app.py` |
| **Task graders** | `tasks/task_easy.py`, `task_medium.py`, `task_hard.py` |
| **Reward safety** | `score_clamp.py` keeps every returned reward strictly inside `(0, 1)` for evaluator compatibility |
| **Baseline agent** | `inference.py` — OpenAI-compatible client, Space URL via `PING_URL`, strict `[START]`/`[STEP]`/`[END]` stdout |

## Quick links

### [Live demo on Hugging Face Space](https://BugHunter28-code-review-env.hf.space)

| | |
|---|---|
| **[Benchmark results](EVALUATION_RESULTS.md)** | Baseline agent scores |
| **[Repository documentation](README.md)** | Complete guide |
| **[GitHub source](https://github.com/Rajath2005/code-review-env)** | Default branch |

---

## The RL loop (agent perspective)

The environment is a **Markov decision process**: agents interact as follows.

```
state = env.reset(task_name="bug_identification")
    ↓ state contains: code_snippet, task_name, instructions, feedback, reward, done
    
for step in range(max_steps):
    action = agent.act(state)      # agent's response: bug type / code / JSON
    state = env.step(action)        # environment returns: observation + reward + done
    
    if state.done:
        break
```

At each step, the agent receives:
- **Observation**: code snippet and task instructions
- **Reward** (strictly inside `(0, 1)` in API responses): immediate signal on response quality
- **Done**: whether the episode ended (task solved or maximum steps reached)

---

## Reward Design

The reward function is **task-specific** and always **normalized** so deployed APIs and baseline logs stay strictly inside the open unit interval (see `score_clamp.py`).

What each task emphasizes:

| Signal | Easy | Medium | Hard |
|--------|------|--------|------|
| **Bug / logic detection** | Primary (name the bug type) | Implicit in passing tests | ~40% weight on structured bug findings |
| **Correctness / repair** | — | Primary (fraction of tests passed) | — |
| **Security issues** | — | — | ~35% via `security_issues` list vs gold |
| **Style / quality** | — | — | ~15% via `style_violations` list vs gold |
| **Response completeness** | Aliases + synonym map + partial overlap | Runnable code + test coverage | JSON validity, keys, list shape, ordering |

**Hard-task fusion**: category scores are weighted, an ordering bonus is applied, then **penalties** cap how much missing critical items or likely hallucinations can reduce the total—before the final clamp.

## Example Output (`inference.py` stdout)

Automated checks parse **exact** stdout lines. The baseline prints (illustrative):

```text
[START] task=bug_identification env=code-review-env model=Qwen/Qwen2.5-72B-Instruct
[STEP] step=1 action="off-by-one error" reward=0.9900 done=true error=null
[END] success=true steps=1 score=0.9900 rewards=0.9900
```

The script ends with a **single JSON object** on stdout, e.g. `{"task_1":0.85,"task_2":0.62,"task_3":0.41}`, with each value strictly between **0** and **1**.

---

## State, action, and reward (formal definition)

### **State Space** — What the agent sees:

```python
class CodeReviewObservation(Observation):
    code_snippet: str            # Python code to review
    task_name: str               # "bug_identification" | "bug_fixing" | "full_review"
    instructions: str            # Task-specific instructions
    feedback: Optional[str]      # Grader feedback from previous step (null on first)
    reward: float                # Reward from previous step (small positive default on reset)
    done: bool                   # Episode complete? (False on reset)
```

### **Action Space** — What the agent can do:

```python
class CodeReviewAction(Action):
    response: str  # Agent's answer (bug type string / fixed code / JSON review)
```

### **Reward Function** — How agents are scored:

| Task | Reward signal (conceptual) | After normalization |
|------|-----------------------------|----------------------|
| **Bug ID (Easy)** | Wrong / partial overlap / exact or alias | Clamped strictly inside `(0, 1)` |
| **Bug Fix (Medium)** | Proportional to tests passed (+ syntax/timeout paths) | Same |
| **Full Review (Hard)** | Weighted category scores + ordering − penalties | Same |

**Dense signals at every step** support stable training rather than sparse end-of-episode feedback.

---

## Live demo

**Hugging Face Space:** https://BugHunter28-code-review-env.hf.space

Select a task, submit a response, and inspect the returned reward in the UI or API.

---

## Quick example: one complete episode

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
  "reward": 0.01,
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
  "feedback": "CORRECT: 'off-by-one error' matches expected bug type",
  "reward": 0.99,
  "done": true
}
```

**Result:** The agent received a high reward (clamped below the upper bound per `score_clamp.py`) and the episode terminated.

---

## Why this is an RL environment

| Aspect | Why it is RL | Implication |
|--------|-----------|------------|
| **Markov property** | Current observation fully determines the next state | Observable state is sufficient for the MDP formulation |
| **Episode Structure** | Fixed max steps, clear terminal conditions | Agents learn when to stop attempting retry |
| **Reward Signal** | Exact, partial, and scored outcomes | Dense learning signal (better than pass/fail) |
| **Generalization** | 32+ diverse snippets, 3 difficulty levels | Curriculum learning + benchmarking possible |
| **Deterministic Grading** | Same response → same score (reproducible) | Fair multi-agent comparison |

**Summary:** You can train an RL policy end-to-end on this environment: it is an interactive loop with explicit `reset` / `step` semantics, not a single-request API.

---

## Tasks

Three tasks with **programmatic graders** and increasing scope. Reported rewards are always **strictly between 0 and 1** (never exactly `0.0` or `1.0` at the API boundary).

### Easy Task — Bug identification (`bug_identification`)

Simulates **triage**: given buggy backend-style Python, the agent must output **only** the bug **type** as a short phrase (e.g. `"off-by-one error"`, `"division by zero"`).

- **Focus**: Syntax-level mistakes, obvious logic flaws, and naming those patterns consistently with the dataset.  
- **Signal**: Exact / alias / synonym match → highest band; partial keyword overlap → mid band; wrong or empty → lowest band (then clamped for the API).

### Medium Task — Bug fixing (`bug_fixing`)

Simulates **patch review**: the agent must return **complete corrected Python** for the shown function so it passes **snippet-specific unit tests**.

- **Focus**: Multiple issues can hide in one snippet—logic, structure, and API misuse are reflected in whether tests pass.  
- **Signal**: Continuous score from **fraction of tests passed**; syntax errors, timeouts, and sandbox failures map to low bands (still strictly inside `(0, 1)`).

### Hard Task — Full code review (`full_review`)

Simulates **structured audit**: the agent must emit **JSON** with `bugs`, `security_issues`, and `style_violations`, each item with `line`, `severity`, `description`, ordered by severity within each list.

- **Focus**: Hidden logic issues, **security-relevant** patterns, and **maintainability / style** concerns—closer to how senior review comments read.  
- **Signal**: Weighted match against gold findings per category, ordering bonus, then capped penalties (see **Reward Design** above).

**Dataset**: 32+ curated snippets—bug type, aliases, fixed code, tests, and gold JSON review per snippet.

**Medium-task execution**: Sandboxed `exec` with a **whitelisted** builtin surface and allowed imports (e.g. `math`, `re`, `json`); per-episode timeout **5s** for the test thread.

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

**Category weights (hard task, conceptual 100% before penalties)**  
*Bugs ≈ 40% · Security ≈ 35% · Style ≈ 15% · Severity ordering ≈ 10%* — see comments in `tasks/task_hard.py` for the exact constants.

**Illustrative decomposition** (numbers before final clamp/penalties):  
If category match scores normalized to ~2/3 bugs, ~1/2 security, ~0 style, plus full ordering credit, the **unnormalized** blend can land around **0.5+**; the implementation then applies **penalties** and **clamp** so the API never returns a boundary value.

---

## Code snippet dataset

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

**Each snippet includes:**
- Buggy code (function definition)
- Bug type (canonical name and aliases)
- Fixed code (reference implementation)
- Test cases (approximately five to ten per snippet with expected outputs)
- Full review (expected bugs, security, and style findings)

---

## Evaluation checklist (judges)

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

# Result: {"feedback": "...", "reward": 0.99, "done": true}  # exact value clamped in (0,1)
```

**Checklist:**
- [ ] `/reset` returns observation with code_snippet, task_name, instructions
- [ ] `/step` accepts action and returns reward + feedback + done
- [ ] Reward is numeric, strictly inside `(0, 1)`, determinate for fixed snippet + response
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
python scripts/benchmark.py --num-episodes 5 --seed 42
python scripts/benchmark.py --num-episodes 5 --seed 42
# Expect identical aggregate scores when the agent policy is deterministic.
```

Also run `python validate_inference_format.py` to confirm the **stdout contract** for automated judging.

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

## Technical specifications

### Observation & Action Spaces (Detailed)

**Observation (what agent sees)**:
```python
class CodeReviewObservation(Observation):
    code_snippet: str            # Raw Python code string
    task_name: str               # "bug_identification" | "bug_fixing" | "full_review"
    instructions: str            # Task-specific instruction text
    feedback: Optional[str]      # Grader feedback from previous step
    reward: float                # Reward from last step, strictly inside (0, 1)
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
- Reward range: **open `(0, 1)`** at the API (clamped away from exact 0.0 / 1.0)

---

## Project structure

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
├── validate_inference_format.py   # Local check: stdout contract for judges
├── score_clamp.py                 # Shared strict (0,1) reward clamp
├── Dockerfile                      # Docker build for HF Spaces
├── run_tests.py                    # Quick test suite
└── README.md                       # This file
```

---

## Running locally

### **Quick Start** (Recommended)

```bash
# Install dependencies
pip install -e .

# Start the server (auto-reload enabled)
uvicorn server.app:app --host 0.0.0.0 --port 7860 --reload
```

Then open **http://localhost:7860** in a browser or HTTP client.

### **With Docker**

```bash
docker build -t code-review-env .
docker run -p 7860:7860 code-review-env
```

---

## Benchmarking your own agent

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

## Testing

```bash
# Quick sanity check
python run_tests.py

# Verbose output
python run_tests.py --verbose
```

Verifies:
- All three tasks reset correctly
- Rewards strictly inside `(0, 1)`
- Test execution sandbox behavior for the medium task
- JSON parsing for the hard task

---

## Reproducibility

**Grading is deterministic**: for a fixed snippet and a fixed agent response string, the grader returns the **same reward** every time—no random noise inside `task_easy` / `task_medium` / `task_hard`.

**Episode variety**: unless you fix randomness, `reset()` draws a snippet from the dataset (`random.choice` when no seed is pinned). For **bit-for-bit reproducible** episodes:

```bash
# Benchmark / batch tools accept --seed
python scripts/benchmark.py --seed 42

# Environment API (Python)
from server.environment import CodeReviewEnvironment
env = CodeReviewEnvironment(seed=42)
obs = env.reset(task_name="bug_identification", seed=42)
```

**Inference baseline**: set `PING_URL` to your Space root when running `inference.py` in CI so the same deployment is hit every run.

For publications or submissions, state explicitly: **seed values** and **commit hash** used for tables.

---

## Key design decisions

| Decision | Rationale | Trade-off |
|----------|-----------|-----------|
| **Dense rewards** | Enables faster training | Requires more grading logic |
| **3-difficulty curriculum** | Agents can learn progressively | More tasks to implement |
| **Sandboxed execution** | Safe code evaluation | Timeout + import restrictions |
| **F1-based hard task** | Rewards precision AND recall | More complex scoring |
| **Fixed 5-step episodes** | Agents learn strategic stopping | May be too short for complex reviews |

---

## References

- **OpenEnv Spec**: https://github.com/openenv-dev/openenv-core
- **Hugging Face Spaces**: https://huggingface.co/docs/hub/spaces
- **RL Benchmarking**: https://openrl-benchmark.com/

---

## Future Work

- **Live GitHub / PR integration** — stream real diffs into the same `Observation` schema  
- **Multi-language reviews** — TypeScript, Go, or Rust snippets with parallel grader interfaces  
- **LLM-in-the-loop grading** — ensemble or critic models on top of deterministic rubrics  
- **Collaborative agents** — multi-turn review threads with tool use (linter, test runner)  
- **Curriculum schedules** — automatic promotion easy → medium → hard by policy performance

## License

MIT License — See LICENSE file for details.

---

## Additional documentation

| File | Purpose |
|------|---------|
| [TEST_GUIDE.md](TEST_GUIDE.md) | Manual testing scenarios and answer formats |
| [EVALUATION_RESULTS.md](EVALUATION_RESULTS.md) | Baseline agent numbers and analysis |
| [HOW_TO_CONFIGURE_HF_SPACE.md](HOW_TO_CONFIGURE_HF_SPACE.md) | Space secrets (`HF_TOKEN`, `API_BASE_URL`, …) |
| [README_HF_SPACE.md](README_HF_SPACE.md) | Hugging Face Space README: required YAML (`title`, `description`, `sdk`, `app_port`, `models`) and short introduction; use as the Space root `README.md` when deploying |

## Support

- **Issues:** [GitHub Issues](https://github.com/Rajath2005/code-review-env/issues)
- **Discussions:** GitHub Discussions on the same repository
- **Live demo:** [code-review-env on Hugging Face Space](https://BugHunter28-code-review-env.hf.space)
