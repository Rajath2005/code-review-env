"""
Task: Bug Fixing (Medium)
--------------------------
Agent receives a buggy Python snippet.
Agent must respond with the CORRECTED complete function.
Grader executes the fixed code against test cases.

Scoring (partial credit):
  1.0  — all test cases pass
  0.6–0.9 — majority of test cases pass (proportional)
  0.3  — code runs without error but fails all test cases
  0.0  — code raises an exception / doesn't compile
"""

import ast
import logging
import re
import threading
from typing import Any
from data.snippets import SNIPPETS

LOGGER = logging.getLogger(__name__)

TIMEOUT_SECONDS = 5.0
ALLOWED_MODULES = {
    "math",
    "re",
    "json",
    "datetime",
    "collections",
    "itertools",
    "statistics",
    "functools",
    "operator",
    "decimal",
}
SAFE_BUILTINS = {
    "abs": abs,
    "all": all,
    "any": any,
    "bool": bool,
    "dict": dict,
    "enumerate": enumerate,
    "float": float,
    "int": int,
    "len": len,
    "list": list,
    "max": max,
    "min": min,
    "range": range,
    "set": set,
    "sorted": sorted,
    "str": str,
    "sum": sum,
    "tuple": tuple,
    "zip": zip,
    "ValueError": ValueError,
    "TypeError": TypeError,
    "Exception": Exception,
}


def _get_snippet(snippet_id: int) -> dict:
    for s in SNIPPETS:
        if s["id"] == snippet_id:
            return s
    raise ValueError(f"Unknown snippet_id: {snippet_id}")


def _extract_code(agent_response: str) -> str:
    """
    Strip markdown fences if agent wrapped in ```python ... ```.
    Returns raw Python code string.
    """
    text = agent_response.strip()
    # Remove opening fence (```python or ```)
    text = re.sub(r"^```[a-zA-Z]*\s*\n?", "", text)
    # Remove closing fence
    text = re.sub(r"\n?```\s*$", "", text)
    return text.strip()


def _parse_safe(code: str) -> bool:
    """Return True if code is valid Python syntax."""
    try:
        ast.parse(code)
        return True
    except SyntaxError:
        return False


def _safe_import(name: str, globals: dict | None = None, locals: dict | None = None,
                 fromlist: tuple | list = (), level: int = 0) -> Any:
    base = name.split(".")[0]
    if base in ALLOWED_MODULES:
        return __import__(name, globals, locals, fromlist, level)
    raise ImportError(f"Import blocked: {name}")


def _execute_tests_inner(code: str, test_cases: list) -> dict:
    try:
        ast.parse(code)
        safe_globals = {"__builtins__": dict(SAFE_BUILTINS)}
        safe_globals["__builtins__"]["__import__"] = _safe_import

        exec(compile(code, "<agent_code>", "exec"), safe_globals)  # noqa: S102

        tree = ast.parse(code)
        func_names = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
        if not func_names:
            return {"status": "no_function", "passed": 0, "total": len(test_cases), "error": "No function found"}

        func = safe_globals.get(func_names[0])
        if func is None:
            return {"status": "no_function", "passed": 0, "total": len(test_cases), "error": "Function not in globals"}

        passed = 0
        for args, expected in test_cases:
            try:
                if isinstance(args, (list, tuple)) and not isinstance(args, str):
                    result = func(*args) if isinstance(args, tuple) else func(args)
                else:
                    result = func(args)

                if isinstance(expected, type):
                    if isinstance(result, expected):
                        passed += 1
                else:
                    if result == expected:
                        passed += 1
            except Exception:
                pass

        return {"status": "ok", "passed": passed, "total": len(test_cases), "error": ""}
    except SyntaxError as exc:
        return {"status": "syntax_error", "passed": 0, "total": len(test_cases), "error": str(exc)}
    except Exception as exc:
        return {"status": "exec_error", "passed": 0, "total": len(test_cases), "error": f"{type(exc).__name__}: {exc}"}


def _run_test_cases_safely(code: str, test_cases: list) -> dict:
    result_holder = {}

    def runner():
        result_holder["result"] = _execute_tests_inner(code, test_cases)

    thread = threading.Thread(target=runner, daemon=True)
    thread.start()
    thread.join(TIMEOUT_SECONDS)

    if thread.is_alive():
        return {"status": "timeout", "passed": 0, "total": len(test_cases), "error": "Execution timed out"}

    return result_holder.get("result", {"status": "exec_error", "passed": 0, "total": len(test_cases), "error": "No result returned"})


def _clamp_score(score: float) -> float:
    """Clamp score to open interval (0, 1) - strictly between 0 and 1."""
    if score <= 0.0:
        return 0.01
    elif score >= 1.0:
        return 0.99
    else:
        return round(score, 3)


def _log_metrics(passed: int, total: int, score: float) -> None:
    accuracy = 1.0 if total > 0 and passed == total else 0.0
    precision = score
    recall = score
    LOGGER.info(
        "medium_metrics accuracy=%.2f precision=%.2f recall=%.2f passed=%d total=%d",
        accuracy,
        precision,
        recall,
        passed,
        total,
    )


def run_medium_task(agent_response: str, snippet_id: int) -> tuple[float, str, bool]:
    """
    Grade the agent's bug fix.

    Returns:
        reward (float): 0.01 – 0.99 (strictly within open interval)
        feedback (str): explanation
        done (bool): True once graded
    """
    snippet = _get_snippet(snippet_id)
    test_cases = snippet.get("test_cases", [])

    # Strip markdown fences
    code = _extract_code(agent_response)

    # Syntax check
    if not _parse_safe(code):
        score = _clamp_score(0.0)
        return score, "Your code has a syntax error and could not be parsed.", True

    # No test cases for this snippet — provide partial credit for valid code
    if not test_cases:
        score = _clamp_score(0.4)
        _log_metrics(0, 0, score)
        return score, "No runnable tests for this snippet. Awarding partial credit for valid code.", True

    result = _run_test_cases_safely(code, test_cases)
    status = result["status"]
    passed = result["passed"]
    total = result["total"]

    if status == "syntax_error":
        score = _clamp_score(0.0)
        _log_metrics(0, total, score)
        return score, "Your code has a syntax error and could not be parsed.", True
    if status == "timeout":
        score = _clamp_score(0.0)
        _log_metrics(0, total, score)
        return score, "Code execution timed out. Make sure it terminates quickly.", True
    if status in {"exec_error", "no_function"}:
        score = _clamp_score(0.0)
        _log_metrics(0, total, score)
        return score, f"Code could not be executed safely: {result['error']}", True

    if total == 0:
        score = _clamp_score(0.4)
        _log_metrics(0, 0, score)
        return score, "No test cases available — partial credit awarded.", True

    ratio = passed / total
    reward = _clamp_score(round(ratio, 3))
    _log_metrics(passed, total, reward)

    if reward >= 0.98:
        feedback = f"All {total} test cases passed. Bug fixed correctly!"
    else:
        feedback = f"{passed}/{total} test cases passed. Partial fix — some cases still fail."

    return reward, feedback, True