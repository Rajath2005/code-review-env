---
title: Code Review Agent
emoji: 🧠
colorFrom: blue
colorTo: green
sdk: docker
app_port: 7860
pinned: false
tags:
  - openenv
  - rl
  - code-review
---

# Code Review Agent — OpenEnv RL environment

**Live demo:** https://BugHunter28-code-review-env.hf.space

## Quick links

| Resource | Description |
|----------|-------------|
| [Live UI](https://BugHunter28-code-review-env.hf.space) | Interactive Space interface |
| [GitHub (default branch)](https://github.com/Rajath2005/code-review-env/tree/master) | Source and full documentation |
| [Evaluation results](https://github.com/Rajath2005/code-review-env/blob/master/EVALUATION_RESULTS.md) | Baseline metrics and methodology |
| [Main README](https://github.com/Rajath2005/code-review-env) | Problem statement, reward design, tasks, reproducibility |

## Overview

OpenEnv-compatible reinforcement learning environment for Python code review. Three tasks with increasing scope:

- **Easy — Bug identification:** respond with the bug type as a short phrase.
- **Medium — Bug fixing:** respond with corrected Python that passes snippet-specific tests.
- **Hard — Full review:** respond with structured JSON (`bugs`, `security_issues`, `style_violations`).

## Interactive demo

1. Select a task (easy, medium, or hard).
2. Use **Reset** to load a code snippet.
3. Submit a response.
4. Inspect the returned reward (API values are strictly inside the open interval `(0, 1)` per `score_clamp.py`).

## Baseline evaluation

| Agent | Easy | Medium | Hard | Overall |
|-------|------|--------|------|---------|
| Random | 0.0 | 0.0 | 0.4 | 0.13 |
| Baseline heuristic | 1.0 | 0.0 | 0.37 | 0.46 |
| Gold (oracle) | 1.0 | 0.0 | 1.0 | 0.67 |

See [EVALUATION_RESULTS.md](https://github.com/Rajath2005/code-review-env/blob/master/EVALUATION_RESULTS.md) for methodology and reproduction commands.

## API examples

```bash
curl https://bughunter28-code-review-env.hf.space/health

curl -X POST https://bughunter28-code-review-env.hf.space/reset \
  -H "Content-Type: application/json" \
  -d '{"task_name": "bug_identification"}'

curl -X POST https://bughunter28-code-review-env.hf.space/step \
  -H "Content-Type: application/json" \
  -d '{"response": "off-by-one error"}'
```

## Repository layout

```
code-review-env/
├── scripts/
│   └── benchmark.py
├── EVALUATION_RESULTS.md
├── README.md
├── server/
│   ├── app.py
│   └── environment.py
├── tasks/
│   ├── task_easy.py
│   ├── task_medium.py
│   └── task_hard.py
└── web/
    ├── index.html
    ├── script.js
    └── styles.css
```

## Evaluation criteria

- OpenEnv-style observation, action, and reward per step.
- Deterministic grading for a fixed snippet and response string; optional seeding for episode sampling.
- Automated benchmarking via `scripts/benchmark.py`.
- Web UI for manual validation.
- Open source on GitHub (default branch).

## Support

- **Issues:** [GitHub Issues](https://github.com/Rajath2005/code-review-env/issues)
- **Documentation:** [Main README](https://github.com/Rajath2005/code-review-env)
- **Training / evaluation:** `python scripts/benchmark.py` or integrate a custom agent as described in the main README.

Prepared for the OpenEnv hackathon (2026).
