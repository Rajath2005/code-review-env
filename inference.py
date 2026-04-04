"""
inference.py — Code Review Agent
==================================
Mandatory file for OpenEnv hackathon submission.

STDOUT FORMAT (strictly enforced by judges):
  [START] task=<task_name> env=<benchmark> model=<model_name>
  [STEP]  step=<n> action=<action_str> reward=<0.00> done=<true|false> error=<msg|null>
  [END]   success=<true|false> steps=<n> rewards=<r1,r2,...,rn>

Environment variables required:
  API_BASE_URL   — LLM endpoint (default: HuggingFace router)
  MODEL_NAME     — model identifier
  HF_TOKEN       — your HuggingFace API key
"""

import os
import sys
import json
import re
import random

from openai import OpenAI

# ── Env vars ──────────────────────────────────────────────────────────────────
API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME   = os.getenv("MODEL_NAME",   "Qwen/Qwen2.5-72B-Instruct")
API_KEY      = os.getenv("HF_TOKEN") or os.getenv("API_KEY", "")
BENCHMARK    = os.getenv("BENCHMARK",    "code-review-env")
MAX_STEPS    = int(os.getenv("MAX_STEPS", "3"))

# ── Tasks to run ──────────────────────────────────────────────────────────────
TASKS = ["bug_identification", "bug_fixing", "full_review"]

# ── OpenAI client (points at HF router) ──────────────────────────────────────
client = OpenAI(api_key=API_KEY, base_url=API_BASE_URL)

# ── Inline environment (no server needed for inference) ───────────────────────
# We import the environment and graders directly so inference.py runs standalone
sys.path.insert(0, os.path.dirname(__file__))

from data.snippets import SNIPPETS
from tasks.task_easy   import run_easy_task
from tasks.task_medium import run_medium_task
from tasks.task_hard   import run_hard_task


# ── Minimal inline env (mirrors server/environment.py without FastAPI) ────────

class InlineEnv:
    """
    Lightweight version of CodeReviewEnvironment for inference.
    Avoids needing a running server — judges can run this directly.
    """

    INSTRUCTIONS = {
        "bug_identification": (
            "Read the Python code carefully. "
            "Identify the bug and respond with ONLY the bug type. "
            "Example: 'off-by-one error', 'infinite loop', 'division by zero', "
            "'type error', 'command injection', 'null pointer dereference'."
        ),
        "bug_fixing": (
            "Read the Python code carefully. It contains a bug. "
            "Respond with ONLY the corrected, complete Python function — "
            "no explanation, no markdown fences, just the fixed code."
        ),
        "full_review": (
            "Perform a full code review. Respond with ONLY a JSON object: "
            '{"bugs": [...], "security_issues": [...], "style_violations": [...]} '
            "Each item needs: 'line' (int), 'severity' ('high'/'medium'/'low'), "
            "'description' (str). Order each list by severity (high first)."
        ),
    }

    def __init__(self):
        self._snippet = None
        self._task    = None
        self._steps   = 0
        self._done    = False

    def reset(self, task_name: str = "bug_identification") -> dict:
        self._snippet = random.choice(SNIPPETS)
        self._task    = task_name
        self._steps   = 0
        self._done    = False
        return {
            "code_snippet": self._snippet["code"],
            "task_name":    task_name,
            "instructions": self.INSTRUCTIONS[task_name],
            "feedback":     None,
            "reward":       0.0,
            "done":         False,
        }

    def step(self, action: str) -> dict:
        if self._done:
            raise RuntimeError("Episode finished — call reset() first.")

        self._steps += 1

        if self._task == "bug_identification":
            reward, feedback, done = run_easy_task(action, self._snippet["id"])
        elif self._task == "bug_fixing":
            reward, feedback, done = run_medium_task(action, self._snippet["id"])
        else:
            reward, feedback, done = run_hard_task(action, self._snippet["id"])

        if self._steps >= MAX_STEPS:
            done = True

        self._done = done

        return {
            "code_snippet": self._snippet["code"],
            "task_name":    self._task,
            "instructions": self.INSTRUCTIONS[self._task],
            "feedback":     feedback,
            "reward":       reward,
            "done":         done,
        }


# ── LLM agent ─────────────────────────────────────────────────────────────────

def build_prompt(obs: dict) -> str:
    """Build the system + user prompt from an observation."""
    return (
        f"You are an expert Python code reviewer.\n\n"
        f"Task: {obs['task_name']}\n\n"
        f"Instructions:\n{obs['instructions']}\n\n"
        f"Code to review:\n```python\n{obs['code_snippet']}\n```\n\n"
        + (f"Previous feedback: {obs['feedback']}\n\n" if obs.get("feedback") else "")
        + "Your response:"
    )


def call_llm(prompt: str) -> str:
    """Call LLM via OpenAI-compatible client. Returns agent response string."""
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert Python code reviewer. "
                        "Follow instructions exactly. Give precise, concise responses."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=512,
            temperature=0.2,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"ERROR: {e}"


# ── Logging helpers (MANDATORY FORMAT) ───────────────────────────────────────

def log_start(task: str):
    """[START] task=<> env=<> model=<>"""
    print(f"[START] task={task} env={BENCHMARK} model={MODEL_NAME}", flush=True)


def log_step(step: int, action: str, reward: float, done: bool, error: str | None):
    """[STEP] step=<n> action=<> reward=<0.00> done=<true|false> error=<msg|null>"""
    # Sanitise action: collapse to single line, cap length for readability
    action_clean = action.replace("\n", " ").replace("\r", "")[:120]
    done_str  = "true" if done else "false"
    error_str = error if error else "null"
    print(
        f"[STEP] step={step} action={action_clean} "
        f"reward={reward:.2f} done={done_str} error={error_str}",
        flush=True,
    )


def log_end(success: bool, steps: int, rewards: list[float]):
    """[END] success=<true|false> steps=<n> rewards=<r1,r2,...>"""
    success_str  = "true" if success else "false"
    rewards_str  = ",".join(f"{r:.2f}" for r in rewards)
    print(
        f"[END] success={success_str} steps={steps} rewards={rewards_str}",
        flush=True,
    )


# ── Episode runner ────────────────────────────────────────────────────────────

def run_episode(task_name: str) -> dict:
    """
    Run one episode for a given task.
    Returns summary dict with total_reward, steps, success.
    """
    env     = InlineEnv()
    rewards = []
    steps   = 0
    success = False

    log_start(task_name)

    try:
        obs = env.reset(task_name=task_name)

        while True:
            prompt = build_prompt(obs)
            action = call_llm(prompt)

            # Detect LLM errors
            error = None
            if action.startswith("ERROR:"):
                error = action[7:].strip()[:80]

            obs    = env.step(action)
            reward = obs["reward"]
            done   = obs["done"]
            steps += 1

            rewards.append(reward)
            log_step(steps, action, reward, done, error)

            if done:
                break

        # Episode success = final reward >= 0.7
        success = rewards[-1] >= 0.7 if rewards else False

    except Exception as e:
        # Always emit [END] even on exception
        log_end(False, steps, rewards)
        raise

    log_end(success, steps, rewards)

    return {
        "task":         task_name,
        "total_reward": sum(rewards),
        "final_reward": rewards[-1] if rewards else 0.0,
        "steps":        steps,
        "success":      success,
    }


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    random.seed(42)  # reproducible snippet selection

    print(f"# Code Review Agent — inference.py", flush=True)
    print(f"# Model: {MODEL_NAME}", flush=True)
    print(f"# API:   {API_BASE_URL}", flush=True)
    print(f"# Tasks: {', '.join(TASKS)}", flush=True)
    print(flush=True)

    results = []

    for task in TASKS:
        try:
            summary = run_episode(task)
            results.append(summary)
        except Exception as e:
            print(f"# ERROR in task {task}: {e}", flush=True)
            # Emit minimal END log so judges don't miss it
            print(f"[END] success=false steps=0 rewards=0.00", flush=True)

    # Final summary
    print(flush=True)
    print("# === FINAL RESULTS ===", flush=True)
    for r in results:
        print(
            f"# Task: {r['task']:<20} "
            f"final_reward={r['final_reward']:.2f}  "
            f"success={str(r['success']).lower()}",
            flush=True,
        )

    avg = sum(r["final_reward"] for r in results) / len(results) if results else 0.0
    print(f"# Average final reward: {avg:.2f}", flush=True)


if __name__ == "__main__":
    main()
