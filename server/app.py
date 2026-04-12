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
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional

def clamp_reward(reward: float) -> float:
    """Clamp reward to (0.01, 0.99) to satisfy Scaler validator."""
    return max(0.01, min(0.99, float(reward)))


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

# Serve static files (web UI) - with robust path handling
try:
    # Try multiple possible paths for the web directory
    web_dir = None
    for possible_path in [
        os.path.join(os.path.dirname(__file__), "..", "web"),
        os.path.join(os.getcwd(), "web"),
        "/app/web",  # Docker container path
    ]:
        if os.path.exists(possible_path):
            web_dir = os.path.abspath(possible_path)
            print(f"✓ Found web directory: {web_dir}")
            break
    
    if web_dir:
        app.mount("/static", StaticFiles(directory=web_dir), name="static")
except Exception as e:
    print(f"⚠ Warning: Could not mount static files: {e}")

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
        obs.reward = clamp_reward(obs.reward)
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
        obs.reward = clamp_reward(obs.reward)
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


@app.get("/", tags=["ui"])
async def root():
    """Serve the web UI (index.html)."""
    from fastapi.responses import HTMLResponse
    
    # Try multiple possible paths
    html_paths = [
        os.path.join(os.path.dirname(__file__), "..", "web", "index.html"),
        os.path.join(os.getcwd(), "web", "index.html"),
        "/app/web/index.html",
    ]
    
    for html_path in html_paths:
        if os.path.exists(html_path):
            try:
                with open(html_path, "r") as f:
                    html_content = f.read()
                return HTMLResponse(content=html_content)
            except Exception as e:
                print(f"Error reading {html_path}: {e}")
                continue
    
    # Fallback: return a simple HTML page with API docs
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Code Review Agent</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
            .container { max-width: 800px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; }
            h1 { color: #333; }
            .endpoint { background: #f0f0f0; padding: 10px; margin: 10px 0; border-left: 4px solid #007bff; }
            a { color: #007bff; text-decoration: none; }
            a:hover { text-decoration: underline; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚀 Code Review Agent — OpenEnv</h1>
            <p>Interactive RL environment for Python code review.</p>
            
            <h2>API Endpoints</h2>
            <div class="endpoint">
                <strong>GET /health</strong> - Check if service is alive
            </div>
            <div class="endpoint">
                <strong>GET /tasks</strong> - List all available tasks
            </div>
            <div class="endpoint">
                <strong>POST /reset</strong> - Start a new episode
            </div>
            <div class="endpoint">
                <strong>POST /step</strong> - Submit an action
            </div>
            <div class="endpoint">
                <strong>GET /docs</strong> - <a href="/docs">View API documentation (Swagger UI)</a>
            </div>
            
            <h2>Quick Start</h2>
            <pre>
# 1. Reset to get initial observation
curl -X POST https://bughunter28-code-review-env.hf.space/reset \\
  -H "Content-Type: application/json" \\
  -d '{"task_name": "bug_identification"}'

# 2. Submit your response
curl -X POST https://bughunter28-code-review-env.hf.space/step \\
  -H "Content-Type: application/json" \\
  -d '{"response": "off-by-one error"}'
            </pre>
            
            <h2>About</h2>
            <p>
                This is a complete OpenEnv RL environment with 3 tasks:
                <ul>
                    <li><strong>Bug Identification (Easy)</strong> - Name the bug type</li>
                    <li><strong>Bug Fixing (Medium)</strong> - Fix the code</li>
                    <li><strong>Full Review (Hard)</strong> - Write complete JSON review</li>
                </ul>
            </p>
            <p>
                📖 Docs: <a href="https://github.com/Rajath2005/code-review-env">GitHub</a>
            </p>
        </div>
    </body>
    </html>
    """)


# ── Dev server ────────────────────────────────────────────────────────────────

def main():
    """Entry point for server.app:main"""
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)


if __name__ == "__main__":
    main()
