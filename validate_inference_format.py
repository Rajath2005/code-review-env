#!/usr/bin/env python3
"""
Runtime check: inference stdout matches Phase-2 log contract (sample inference script).
Run before submit: python validate_inference_format.py
"""
from __future__ import annotations

import io
import os
import re
import sys
from contextlib import redirect_stdout
from unittest.mock import patch

# Must be set before importing inference (OpenAI client init)
os.environ.setdefault("HF_TOKEN", "format-check-placeholder")


def _fake_post_json(path: str, payload: dict) -> dict:
    task = payload.get("task_name") or "bug_identification"
    base = {
        "task_name": task,
        "instructions": "test",
        "code_snippet": "pass",
        "feedback": None,
    }
    if path == "/reset":
        return {**base, "reward": 0.01, "done": False}
    # Single step then done; boundary reward to prove clamping in logs
    return {**base, "reward": 1.0, "done": True}


def _fake_call_llm(_obs: dict) -> str:
    return 'agent says "ok"'


def main() -> int:
    import inference as inf

    f = io.StringIO()
    with patch.object(inf, "post_json", side_effect=_fake_post_json), patch.object(
        inf, "call_llm", side_effect=_fake_call_llm
    ), redirect_stdout(f):
        score = inf.run_task("bug_identification")

    text = f.getvalue()
    lines = [ln for ln in text.splitlines() if ln.strip()]

    errs: list[str] = []
    if not any(ln.startswith("[START] ") for ln in lines):
        errs.append("missing [START] line")
    start = next((ln for ln in lines if ln.startswith("[START] ")), "")
    for key in ("task=", "env=", "model="):
        if key not in start:
            errs.append(f"[START] missing {key}")

    steps = [ln for ln in lines if ln.startswith("[STEP] ")]
    if not steps:
        errs.append("missing [STEP] line(s)")
    for s in steps:
        for key in ("step=", "action=", "reward=", "done=", "error="):
            if key not in s:
                errs.append(f"[STEP] missing {key}: {s[:120]}...")
        if "reward=0.0000" in s or "reward=1.0000" in s:
            errs.append(f"[STEP] boundary reward string: {s}")
        if "reward=0.00" in s or "reward=1.00" in s:
            errs.append(f"[STEP] disallowed .00 pattern: {s}")

    ends = [ln for ln in lines if ln.startswith("[END] ")]
    if len(ends) != 1:
        errs.append(f"expected exactly one [END] line, got {len(ends)}")
    else:
        end = ends[0]
        if "score=" not in end:
            errs.append("[END] missing score= (Phase-2 task validation often defaults to 0.0)")
        if "rewards=" not in end:
            errs.append("[END] missing rewards=")
        m = re.search(r"score=(\S+)", end)
        if m:
            try:
                sv = float(m.group(1).rstrip(","))
            except ValueError:
                errs.append(f"[END] non-float score: {m.group(1)}")
            else:
                if not (0.0 < sv < 1.0):
                    errs.append(f"[END] score not strictly in (0,1): {sv}")
        if "rewards=0.0000" in end or "rewards=1.0000" in end:
            errs.append(f"[END] boundary rewards string: {end}")
        if ",0.0000" in end or ",1.0000" in end or end.endswith("0.0000") or end.endswith("1.0000"):
            errs.append(f"[END] possible boundary token in rewards: {end}")

    if not (0.0 < float(score) < 1.0):
        errs.append(f"run_task return not in (0,1): {score}")

    if errs:
        print("validate_inference_format.py: FAIL", file=sys.stderr)
        for e in errs:
            print(f"  - {e}", file=sys.stderr)
        return 1

    print("validate_inference_format.py: PASS")
    print("  sample stdout tail:")
    for ln in lines[-4:]:
        print(f"    {ln}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
