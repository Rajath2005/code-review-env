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
import multiprocessing as mp
import re
from typing import Any
from data.snippets import SNIPPETS

LOGGER = logging.getLogger(__name__)

TIMEOUT_SECONDS = 2.5
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


def _execute_tests(code: str, test_cases: list, queue: mp.Queue) -> None:
    try:
        ast.parse(code)
        safe_globals = {"__builtins__": dict(SAFE_BUILTINS)}
        safe_globals["__builtins__"]["__import__"] = _safe_import

        exec(compile(code, "<agent_code>", "exec"), safe_globals)  # noqa: S102

        tree = ast.parse(code)
        func_names = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
        if not func_names:
            queue.put({"status": "no_function", "passed": 0, "total": len(test_cases), "error": "No function found"})
            return

        func = safe_globals.get(func_names[0])
        if func is None:
            queue.put({"status": "no_function", "passed": 0, "total": len(test_cases), "error": "Function not in globals"})
            return

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

        queue.put({"status": "ok", "passed": passed, "total": len(test_cases), "error": ""})
    except SyntaxError as exc:
        queue.put({"status": "syntax_error", "passed": 0, "total": len(test_cases), "error": str(exc)})
    except Exception as exc:
        queue.put({"status": "exec_error", "passed": 0, "total": len(test_cases), "error": f"{type(exc).__name__}: {exc}"})


def _run_test_cases_safely(code: str, test_cases: list) -> dict:
    queue: mp.Queue = mp.Queue()
    process = mp.Process(target=_execute_tests, args=(code, test_cases, queue))
    process.start()
    process.join(TIMEOUT_SECONDS)

    if process.is_alive():
        process.terminate()
        process.join(0.2)
        return {"status": "timeout", "passed": 0, "total": len(test_cases), "error": "Execution timed out"}

    if queue.empty():
        return {"status": "exec_error", "passed": 0, "total": len(test_cases), "error": "No result returned"}

    return queue.get()


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
        reward (float): 0.0 – 1.0
        feedback (str): explanation
        done (bool): True once graded
    """
    snippet = _get_snippet(snippet_id)
    test_cases = snippet.get("test_cases", [])

    # Strip markdown fences
    code = _extract_code(agent_response)

    # Syntax check
    if not _parse_safe(code):
        return 0.0, "Your code has a syntax error and could not be parsed.", True

    # No test cases for this snippet — provide partial credit for valid code
    if not test_cases:
        _log_metrics(0, 0, 0.4)
        return 0.4, "No runnable tests for this snippet. Awarding partial credit for valid code.", True

    result = _run_test_cases_safely(code, test_cases)
    status = result["status"]
    passed = result["passed"]
    total = result["total"]

    if status == "syntax_error":
        _log_metrics(0, total, 0.0)
        return 0.0, "Your code has a syntax error and could not be parsed.", True
    if status == "timeout":
        _log_metrics(0, total, 0.0)
        return 0.0, "Code execution timed out. Make sure it terminates quickly.", True
    if status in {"exec_error", "no_function"}:
        _log_metrics(0, total, 0.0)
        return 0.0, f"Code could not be executed safely: {result['error']}", True

    if total == 0:
        _log_metrics(0, 0, 0.4)
        return 0.4, "No test cases available — partial credit awarded.", True

    ratio = passed / total
    reward = round(ratio, 3)
    _log_metrics(passed, total, reward)

    if ratio == 1.0:
        feedback = f"All {total} test cases passed. Bug fixed correctly!"
    else:
        feedback = f"{passed}/{total} test cases passed. Partial fix — some cases still fail."

    return reward, feedback, True
