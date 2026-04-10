"""
inference.py — Code Review Agent (OpenEnv Hackathon)
Strict stdout format required by judges.
"""

import json
import os
import urllib.request

from openai import OpenAI

API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")
HF_TOKEN = os.getenv("HF_TOKEN")

BASE_URL = "https://BugHunter28-code-review-env.hf.space"
TASKS = ["bug_identification", "bug_fixing", "full_review"]
OUTPUT_TASK_KEYS = {
    "bug_identification": "task_1",
    "bug_fixing": "task_2",
    "full_review": "task_3",
}

client = OpenAI(
    base_url=API_BASE_URL,
    api_key=HF_TOKEN
)

SYSTEM_PROMPT = (
    "You are a senior software engineer. Carefully analyze the given Python code "
    "and return only the correct answer based on task instructions. Do not explain."
)


def safe_score(score: float) -> float:
    """Clamp a score to the open interval (0, 1) as required by evaluation.
    Must be strictly between 0 and 1 - not equal to 0.0 or 1.0.
    """
    try:
        value = float(score)
    except (TypeError, ValueError):
        value = 0.01  # Default to minimum valid score

    # First pass: extreme boundaries
    if value <= 0.0:
        return 0.01
    if value >= 1.0:
        return 0.99

    # Round to avoid floating point edge cases
    value = round(value, 4)

    # Second pass: check after rounding
    if value <= 0.0:
        return 0.01
    if value >= 1.0:
        return 0.99

    return value


def post_json(path: str, payload: dict) -> dict:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        BASE_URL + path,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        body = resp.read().decode("utf-8")
    return json.loads(body)


def build_user_prompt(obs: dict) -> str:
    parts = [
        f"Task: {obs.get('task_name', '')}",
        f"Instructions:\n{obs.get('instructions', '')}",
        f"Code:\n{obs.get('code_snippet', '')}",
    ]
    if obs.get("feedback"):
        parts.append(f"Feedback:\n{obs['feedback']}")
    return "\n\n".join(parts)


def call_llm(obs: dict) -> str:
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_user_prompt(obs)},
        ],
        max_tokens=512,
        temperature=0.2,
    )
    content = response.choices[0].message.content
    return (content or "").strip()


def log_start(task: str):
    print(f"[START] task={task} env=code-review-env model={MODEL_NAME}", flush=True)


def clean_action(action: str) -> str:
    cleaned = action.replace("\n", " ").replace("\r", " ")
    cleaned = cleaned.replace('"', "\\\"")
    return cleaned[:120]


def log_step(step: int, action: str, reward: float, done: bool):
    done_str = "true" if done else "false"
    action_clean = clean_action(action)
    print(
        f"[STEP] step={step} action=\"{action_clean}\" "
        f"reward={reward:.2f} done={done_str} error=null",
        flush=True,
    )


def log_end(success: bool, steps: int, rewards: list[float]):
    success_str = "true" if success else "false"
    rewards_str = ",".join(f"{r:.2f}" for r in rewards) if rewards else "0.00"
    print(
        f"[END] success={success_str} steps={steps} rewards={rewards_str}",
        flush=True,
    )


def run_task(task_name: str) -> float:
    rewards: list[float] = []
    steps = 0
    success = False

    log_start(task_name)

    try:
        obs = post_json("/reset", {"task_name": task_name})

        while True:
            action = call_llm(obs)
            obs = post_json("/step", {"response": action})
            reward = float(obs.get("reward", 0.0))
            done = bool(obs.get("done", False))
            steps += 1
            rewards.append(reward)
            log_step(steps, action, reward, done)
            if done:
                break

        final_reward = rewards[-1] if rewards else 0.0
        task_score = safe_score(final_reward)
        success = task_score >= 0.7
        log_end(success, steps, rewards)
        return task_score
    except Exception:
        log_end(False, steps, rewards)
        return safe_score(0.0)


def main():
    scores: dict[str, float] = {}
    for task in TASKS:
        output_key = OUTPUT_TASK_KEYS.get(task, task)
        scores[output_key] = safe_score(run_task(task))

    print(json.dumps(scores), flush=True)


if __name__ == "__main__":
    main()
