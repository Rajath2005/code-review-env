"""
server/environment.py — Code Review Agent
==========================================
Full OpenEnv-spec environment implementation.
Typed Pydantic models + step() / reset() / state() methods.
"""

import random
import sys
import os
from typing import Optional

# Make sure project root is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pydantic import Field

try:
    from openenv.core.env_server import Action, Observation, State, Environment
except ImportError:
    # Fallback base classes if openenv-core not installed yet (local dev)
    from pydantic import BaseModel

    class Action(BaseModel):
        pass

    class Observation(BaseModel):
        reward: float = 0.0
        done: bool = False

    class State(BaseModel):
        pass

    class Environment:
        def reset(self, **kwargs):
            raise NotImplementedError
        def step(self, action):
            raise NotImplementedError
        def state(self):
            raise NotImplementedError

from data.snippets import SNIPPETS
from tasks.task_easy import run_easy_task
from tasks.task_medium import run_medium_task
from tasks.task_hard import run_hard_task


# ── Typed Models ──────────────────────────────────────────────────────────────

class CodeReviewAction(Action):
    """What the agent submits each step."""
    response: str = Field(
        description=(
            "Agent's output — bug type name (easy), "
            "corrected code (medium), or JSON review object (hard)"
        )
    )


class CodeReviewObservation(Observation):
    """
    What the agent sees each step.
    `reward` and `done` are inherited from Observation.
    """
    code_snippet: str = Field(description="The Python code to review")
    task_name: str = Field(
        description="Current task: bug_identification | bug_fixing | full_review"
    )
    instructions: str = Field(description="What the agent must produce")
    feedback: Optional[str] = Field(
        default=None,
        description="Grader feedback from the previous step (null on first step)"
    )


class CodeReviewState(State):
    """Internal episode state — not exposed to the agent."""
    task_name: str
    snippet_id: int
    current_snippet: str
    step_count: int
    last_reward: float
    done: bool


# ── Instructions per task ─────────────────────────────────────────────────────

INSTRUCTIONS = {
    "bug_identification": (
        "Read the Python code carefully. "
        "Identify the bug and respond with ONLY the bug type as a short phrase. "
        "Examples: 'off-by-one error', 'infinite loop', 'division by zero', "
        "'type error', 'command injection', 'null pointer dereference', "
        "'resource leak', 'wrong initial value', 'mutating list while iterating'."
    ),
    "bug_fixing": (
        "Read the Python code carefully. It contains a bug. "
        "Respond with ONLY the corrected, complete Python function. "
        "No explanation, no markdown fences — just the fixed code."
    ),
    "full_review": (
        "Perform a full code review. Respond with ONLY a JSON object:\n"
        '{"bugs": [...], "security_issues": [...], "style_violations": [...]}\n'
        "Each item must have: 'line' (int), 'severity' ('high'/'medium'/'low'), "
        "'description' (str). Order each list by severity (high first)."
    ),
}

MAX_STEPS = 5
VALID_TASKS = list(INSTRUCTIONS.keys())


# ── Environment ───────────────────────────────────────────────────────────────

class CodeReviewEnvironment(Environment):
    """
    RL environment for code review tasks.

    Episode flow:
      reset(task_name) → observation
      step(action)     → observation (with reward + done)
      state()          → internal state

    Three tasks of increasing difficulty:
      bug_identification (easy)   — name the bug type
      bug_fixing         (medium) — produce corrected code
      full_review        (hard)   — full JSON audit
    """

    def __init__(self):
        self._state: Optional[CodeReviewState] = None

    # ── Public API ────────────────────────────────────────────────────────────

    def reset(self, task_name: str = "bug_identification") -> CodeReviewObservation:
        """
        Start a new episode.

        Args:
            task_name: one of bug_identification | bug_fixing | full_review

        Returns:
            Initial observation with a random code snippet.
        """
        if task_name not in VALID_TASKS:
            raise ValueError(
                f"Unknown task '{task_name}'. "
                f"Valid options: {VALID_TASKS}"
            )

        snippet = random.choice(SNIPPETS)

        self._state = CodeReviewState(
            task_name=task_name,
            snippet_id=snippet["id"],
            current_snippet=snippet["code"],
            step_count=0,
            last_reward=0.0,
            done=False,
        )

        return CodeReviewObservation(
            code_snippet=snippet["code"],
            task_name=task_name,
            instructions=INSTRUCTIONS[task_name],
            feedback=None,
            reward=0.0,
            done=False,
        )

    def step(self, action: CodeReviewAction) -> CodeReviewObservation:
        """
        Submit an action and receive the next observation + reward.

        The episode ends when:
          - The grader marks done=True (single-step tasks), OR
          - MAX_STEPS steps have been taken.

        Args:
            action: CodeReviewAction with agent's response string

        Returns:
            Next observation with reward signal.
        """
        if self._state is None:
            raise RuntimeError("Call reset() before step().")
        if self._state.done:
            raise RuntimeError("Episode is done. Call reset() to start a new episode.")

        self._state.step_count += 1

        # Route to correct grader
        if self._state.task_name == "bug_identification":
            reward, feedback, done = run_easy_task(
                action.response, self._state.snippet_id
            )
        elif self._state.task_name == "bug_fixing":
            reward, feedback, done = run_medium_task(
                action.response, self._state.snippet_id
            )
        else:  # full_review
            reward, feedback, done = run_hard_task(
                action.response, self._state.snippet_id
            )

        # Enforce max steps
        if self._state.step_count >= MAX_STEPS:
            done = True

        self._state.last_reward = reward
        self._state.done = done

        return CodeReviewObservation(
            code_snippet=self._state.current_snippet,
            task_name=self._state.task_name,
            instructions=INSTRUCTIONS[self._state.task_name],
            feedback=feedback,
            reward=reward,
            done=done,
        )

    def state(self) -> CodeReviewState:
        """Return the current internal episode state."""
        if self._state is None:
            raise RuntimeError("No active episode. Call reset() first.")
        return self._state
