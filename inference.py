"""
inference.py — Code Review Agent (OpenEnv Hackathon)
Strict stdout format required by judges.
"""

import json
import os
import urllib.request

from openai import OpenAI

from score_clamp import clamp_score

API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")
HF_TOKEN = os.getenv("HF_TOKEN") or os.getenv("OPENAI_API_KEY")

# Validator / pre-submit script export this; fall back to deployed Space.
_default_space = "https://BugHunter28-code-review-env.hf.space"
BASE_URL = (os.getenv("PING_URL") or os.getenv("OPENENV_SPACE_URL") or _default_space).rstrip("/")
TASKS = ["bug_identification", "bug_fixing", "full_review"]
OUTPUT_TASK_KEYS = {
    "bug_identification": "task_1",
    "bug_fixing": "task_2",
    "full_review": "task_3",
}

client = OpenAI(
    base_url=API_BASE_URL,
    api_key=HF_TOKEN or "",
)

SYSTEM_PROMPT = (
    "You are a senior software engineer. Carefully analyze the given Python code "
    "and return only the correct answer based on task instructions. Do not explain."
)


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


def clean_action(action: str) -> str:
    cleaned = (action or "").replace("\n", " ").replace("\r", " ")
    cleaned = cleaned.replace('"', '\\"')
    return cleaned[:120]


def log_start(task: str, env: str = "code-review-env", model: str | None = None):
    """Match hackathon sample: task, env, model (strict stdout for judges)."""
    m = model if model is not None else MODEL_NAME
    print(f"[START] task={task} env={env} model={m}", flush=True)


def log_step(step: int, action: str, reward: float, done: bool, error: str | None = None):
    done_str = "true" if done else "false"
    safe_r = clamp_score(reward)
    if safe_r <= 0.01:
        safe_r = 0.01
    if safe_r >= 0.99:
        safe_r = 0.99
    action_clean = clean_action(action)
    err = "null" if error is None else json.dumps(str(error))
    print(
        f'[STEP] step={step} action="{action_clean}" reward={safe_r:.4f} done={done_str} error={err}',
        flush=True,
    )


def _format_reward_csv(rewards: list[float]) -> str:
    if not rewards:
        return "0.01"
    parts = []
    for r in rewards:
        sr = clamp_score(r)
        if sr <= 0.01:
            sr = 0.01
        if sr >= 0.99:
            sr = 0.99
        parts.append(f"{sr:.4f}")
    return ",".join(parts)


def log_end(success: bool, steps: int, task_score: float, rewards: list[float]):
    """Must include score= (sample inference); missing score parses as 0.0 and fails validation."""
    success_str = "true" if success else "false"
    safe_score = clamp_score(task_score)
    if safe_score <= 0.01:
        safe_score = 0.01
    if safe_score >= 0.99:
        safe_score = 0.99
    rewards_str = _format_reward_csv(rewards)
    print(
        f"[END] success={success_str} steps={steps} score={safe_score:.4f} rewards={rewards_str}",
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
            raw_r = obs.get("reward", 0.01)
            reward = clamp_score(raw_r)
            done = bool(obs.get("done", False))
            steps += 1
            rewards.append(clamp_score(reward))
            log_step(steps, action, reward, done, error=None)
            if done:
                break

        final_reward = rewards[-1] if rewards else 0.01
        task_score = clamp_score(final_reward)
        success = task_score >= 0.7
        log_end(success, steps, task_score, rewards)
        return task_score
    except Exception:
        log_end(False, steps, 0.01, rewards)
        return 0.01


def main():
    scores: dict[str, float] = {}
    for task in TASKS:
        output_key = OUTPUT_TASK_KEYS.get(task, task)
        scores[output_key] = clamp_score(run_task(task))

    scores = {k: clamp_score(v) for k, v in scores.items()}
    print(json.dumps(scores), flush=True)


if __name__ == "__main__":
    main()
