"""
server/app.py — FastAPI server for Code Review Agent
======================================================
Exposes the OpenEnv standard endpoints:
  POST /reset  — start a new episode
  POST /step   — submit an action
  GET  /state  — get current internal state
  GET  /health — liveness check (judges ping this)
  GET  /tasks  — list available tasks
  GET  / — serves web UI (index.html)
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional

from server.environment import (
    CodeReviewEnvironment,
    CodeReviewAction,
    CodeReviewObservation,
    CodeReviewState,
    VALID_TASKS,
)

# ── App setup ─────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Code Review Agent — OpenEnv",
    description=(
        "RL environment for training AI agents to perform Python code review. "
        "Three tasks: bug identification (easy), bug fixing (medium), full review (hard)."
    ),
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Single shared environment instance per server process
env = CodeReviewEnvironment()


# ── Request / Response schemas ────────────────────────────────────────────────

class ResetRequest(BaseModel):
    task_name: Optional[str] = "bug_identification"


class StepRequest(BaseModel):
    response: str


class HealthResponse(BaseModel):
    status: str
    environment: str
    tasks: list[str]


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/health", response_model=HealthResponse, tags=["meta"])
async def health():
    """Liveness check — judges ping this. Must return 200."""
    return HealthResponse(
        status="ok",
        environment="code-review-env",
        tasks=VALID_TASKS,
    )


@app.get("/tasks", tags=["meta"])
async def list_tasks():
    """List all available tasks with descriptions."""
    return {
        "tasks": [
            {
                "name": "bug_identification",
                "difficulty": "easy",
                "description": "Identify the bug type in a buggy Python snippet",
            },
            {
                "name": "bug_fixing",
                "difficulty": "medium",
                "description": "Produce corrected Python code that passes all test cases",
            },
            {
                "name": "full_review",
                "difficulty": "hard",
                "description": "Produce a full JSON review: bugs, security issues, style violations",
            },
        ]
    }


@app.post("/reset", tags=["env"])
async def reset(request: ResetRequest = ResetRequest()):
    """
    Start a new episode.
    Returns the first observation with a random code snippet.
    """
    try:
        obs = env.reset(task_name=request.task_name or "bug_identification")
        return obs.model_dump()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/step", tags=["env"])
async def step(request: StepRequest):
    """
    Submit an action and receive the next observation + reward.
    Must call /reset first.
    """
    try:
        action = CodeReviewAction(response=request.response)
        obs = env.step(action)
        return obs.model_dump()
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/state", tags=["env"])
async def state():
    """Return the current internal episode state."""
    try:
        s = env.state()
        return s.model_dump()
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ── Dev server ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)
