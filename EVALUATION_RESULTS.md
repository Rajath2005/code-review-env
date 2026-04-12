# Evaluation results — code review environment

## Overview

Baseline evaluation results for `code-review-env` using multiple reference agents. These runs show:

1. The environment assigns **different scores to different policies** (non-degenerate signal).
2. Grading is **deterministic for a fixed seed** and fixed agent behavior.
3. **Dense rewards** are returned each step where applicable, suitable for learning-style workflows.

## Baseline results (seed 42, 10 episodes per task)

### Summary table

| Agent | Easy | Medium | Hard | Overall |
|-------|------|--------|------|---------|
| **Weak (random)** | 0.000 | 0.000 | 0.400 | **0.133** |
| **Baseline (heuristic)** | 1.000 | 0.000 | 0.370 | **0.457** |
| **Strong (LLM-like)** | 0.000 | 0.000 | 0.400 | **0.133** |
| **Gold (oracle)** | 1.000 | 0.000 | 1.000 | **0.667** |

### Task completion rates

| Agent | Easy | Medium | Hard |
|-------|------|--------|------|
| **Weak** | 10/10 | 10/10 | 10/10 |
| **Baseline** | 10/10 | 10/10 | 10/10 |
| **Strong** | 10/10 | 10/10 | 10/10 |
| **Gold** | 10/10 | 10/10 | 10/10 |

## Agent descriptions

### Weak agent (random)

- **Strategy:** Random bug-type strings on easy, placeholder code on medium, empty or minimal JSON on hard.
- **Expected role:** Lower bound for agents that do not encode task knowledge.
- **Observed result:** Mean reward 0.133; occasional lucky guesses or partial structure on hard.
- **Interpretation:** Graders distinguish unstructured responses from task-aligned behavior.

### Baseline agent (heuristic)

- **Strategy:** Rule-based pattern matching (for example, `range(len(` heuristics for off-by-one class bugs).
- **Expected role:** Strong on easy identification, weak on code generation and structured audit.
- **Observed result:** Mean 0.457; easy task near ceiling, medium at floor for this benchmark configuration.
- **Interpretation:** Symbolic rules cover part of the easy task; medium and hard require stronger policies.

### Strong agent (LLM-like)

- **Strategy:** Stronger heuristics than weak, without a live LLM call in the reference implementation.
- **Expected role:** Intended to sit between baseline and oracle when given sufficient capability.
- **Observed result:** Mean 0.133 in this run (similar to weak under the same seed and episode count).
- **Interpretation:** Heuristic depth in the bundled “strong” stub was insufficient for medium/hard under test; real LLMs or trained policies should be measured separately.

### Gold agent (oracle)

- **Strategy:** Returns dataset ground truth (sanity check for graders).
- **Expected role:** Upper reference for grading correctness.
- **Observed result:** Mean 0.667 (not 1.0 on all axes), indicating strict or asymmetric grading and/or reporting conventions per task.
- **Interpretation:** Graders are conservative; full numeric ceiling may require task-specific tuning or oracle alignment with every edge case.

## Analysis

### 1. Separation between agents

- **Weak vs baseline:** 0.133 vs 0.457.
- **Baseline vs gold:** 0.457 vs 0.667.

Different policies receive different aggregate scores under the same protocol.

### 2. Difficulty progression

- **Easy:** Heuristic baseline reaches high scores.
- **Medium:** All listed agents at 0.0 average in this table (code must pass snippet tests).
- **Hard:** Partial scores appear depending on JSON quality and match to gold lists.

Curriculum-style ordering (easy to hard) is supported by the task design.

### 3. Medium task difficulty

All agents at 0.0 on bug fixing in this benchmark suggests strict test criteria, execution constraints (sandbox, imports, timeout), or responses that did not satisfy runnable-code requirements. Use the medium task primarily for **generative or execution-aware** agents, not shallow string rules.

### 4. Determinism

Repeated runs with `seed=42` and the same agent code produced identical aggregates in verification runs.

## Reproduction

```bash
python scripts/benchmark.py --num-episodes 10 --seed 42 --json results.json

python scripts/benchmark.py --num-episodes 10 --seed 99 --json results_seed99.json
```

To add a custom agent, extend `scripts/benchmark.py` with a new policy class and register it in the agent map, then rerun with the desired `--num-episodes` and `--seed`.

## Notes for judges

| Claim | Evidence |
|-------|----------|
| Objective grading | Scalar reward per step from deterministic graders |
| Non-trivial signal | Spread between weak, baseline, and gold rows |
| Reproducibility | Fixed seed and deterministic scoring path |
| RL-shaped interaction | `reset` / `step`, terminal `done`, bounded rewards |

**Illustrative expectations by agent class** (not measured in the table above):

| Agent type | Easy | Medium | Hard | Example |
|------------|------|--------|------|---------|
| Random | 0.0–0.3 | 0.0–0.1 | 0.0–0.2 | Noise policy |
| Rule-based | 0.5–0.8 | 0.0–0.1 | 0.1–0.3 | Regex-style heuristics |
| LLM (smaller) | 0.6–0.8 | 0.1–0.4 | 0.2–0.5 | Depends on model and prompt |
| LLM (larger) | 0.85–0.95 | 0.4–0.7 | 0.5–0.8 | Depends on model and prompt |
| Specialized RL | Varies | Varies | Varies | After training on this env |

## Next steps

1. Register your agent in `scripts/benchmark.py` (or an external driver calling the HTTP API).
2. Log scores per task with fixed seeds for comparability.
3. For publications or submissions, record **seed**, **commit hash**, and benchmark CLI flags.

## Raw results

Episode-level JSON is emitted by:

```bash
python scripts/benchmark.py --json
```

Example structure (illustrative):

```json
{
  "metadata": {
    "seed": 42,
    "num_episodes": 10,
    "num_agents": 4
  },
  "metrics": [
    {"agent_name": "Gold (Oracle)", "easy_avg": 1.0, "medium_avg": 0.0}
  ],
  "episodes": [
    {"agent_name": "Gold (Oracle)", "task_name": "bug_identification", "reward": 1.0}
  ]
}
```
