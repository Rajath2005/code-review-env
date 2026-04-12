# Configuring Hugging Face Space links and description

This document describes where Space metadata and links appear, and how to align them with the repository.

## Where links and copy appear

### 1. Space README (`README.md` at the Space root)

Primary visible description. Use [README_HF_SPACE.md](README_HF_SPACE.md) as the Space-facing README, or merge its frontmatter and body into the Space repository root `README.md`.

Example excerpt:

```markdown
# Code Review Agent — OpenEnv

**Live demo:** https://BugHunter28-code-review-env.hf.space

[Source](https://github.com/Rajath2005/code-review-env)
```

### 2. README YAML frontmatter (side panel)

Tags and card styling are often defined at the top of the Space `README.md`:

```yaml
---
title: Code Review Agent
colorFrom: blue
colorTo: green
sdk: docker
pinned: false
tags:
  - openenv
  - rl
  - code-review
---
```

Optional Hugging Face fields (for example `emoji`) may be added per [Hub documentation](https://huggingface.co/docs/hub/spaces-config-reference).

### 3. `app.yaml` (optional)

For advanced Space configuration, add `app.yaml` at the repository root:

```yaml
title: Code Review Agent — OpenEnv
description: Interactive RL environment for Python code review with a live demo.
sdk: docker
app_port: 7860
models:
  - url: https://BugHunter28-code-review-env.hf.space
    description: Live demo
```

## Space settings (web UI)

1. Open Space settings: https://huggingface.co/spaces/BugHunter28/code-review-env/settings
2. Under **About**, set a short description, for example:

```
Interactive RL environment for Python code review.

Live demo: https://BugHunter28-code-review-env.hf.space

Tasks: bug identification (easy), bug fixing (medium), full structured review (hard).

Deterministic grading on 32+ snippets; rewards in (0, 1).

GitHub: https://github.com/Rajath2005/code-review-env
```

## Page layout (conceptual)

| Area | Content source |
|------|----------------|
| Main column | Rendered README from the Space repository |
| Side panel | Tags, optional `models` from `app.yaml`, About text from settings |

## Recommended checklist

1. Push an updated Space `README.md` (frontmatter + body) from this repo’s [README_HF_SPACE.md](README_HF_SPACE.md) when appropriate.
2. Confirm the Space URL responds: https://BugHunter28-code-review-env.hf.space
3. Optionally sync the **About** field in Space settings with the template above.
4. Optionally add `app.yaml` if you need explicit `app_port` or **Models** entries.

## Verifying static assets and API

In the browser developer tools console:

```javascript
fetch('/health').then(r => r.json()).then(console.log)
```

Expected shape:

```json
{
  "status": "ok",
  "environment": "code-review-env",
  "tasks": ["bug_identification", "bug_fixing", "full_review"]
}
```

If the request fails, wait for the Space build to finish or inspect build logs on Hugging Face.

## Summary

- README (with YAML) drives the main Space page and side metadata.
- Space **About** is edited in the Hugging Face UI.
- `app.yaml` is optional for additional Hub configuration.
- Use `/health` to confirm the API is reachable after deployment.
