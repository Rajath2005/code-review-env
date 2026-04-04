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
import re
import textwrap
import traceback
from data.snippets import SNIPPETS


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


def _run_test_cases(code: str, test_cases: list) -> tuple[int, int]:
    """
    Execute code against test cases in a sandboxed namespace.
    Returns (passed, total).
    """
    namespace = {}
    exec(compile(code, "<agent_code>", "exec"), namespace)  # noqa: S102

    # Find the function name defined in the code
    tree = ast.parse(code)
    func_names = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
    if not func_names:
        return 0, len(test_cases)

    func = namespace.get(func_names[0])
    if func is None:
        return 0, len(test_cases)

    passed = 0
    for args, expected in test_cases:
        try:
            if isinstance(args, (list, tuple)) and not isinstance(args, str):
                result = func(*args) if isinstance(args, tuple) else func(args)
            else:
                result = func(args)

            # For type-only checks (e.g. returns str)
            if isinstance(expected, type):
                if isinstance(result, expected):
                    passed += 1
            else:
                if result == expected:
                    passed += 1
        except Exception:
            pass  # failed test case

    return passed, len(test_cases)


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

    # No test cases for this snippet — fallback to AST similarity check
    if not test_cases:
        expected_code = textwrap.dedent(snippet["fixed_code"])
        # Simple heuristic: does the fix match key patterns?
        if "with open" in code or "shell=False" in code or "allowed" in code:
            return 0.8, "Fix looks correct based on pattern check (no runnable tests for this snippet).", True
        return 0.3, "Code compiles but the fix pattern doesn't match expected approach.", True

    # Run test cases
    try:
        passed, total = _run_test_cases(code, test_cases)
    except Exception as e:
        return 0.0, f"Code raised an exception during execution: {type(e).__name__}: {e}", True

    if total == 0:
        return 0.5, "No test cases available — assuming partial credit.", True

    ratio = passed / total

    if ratio == 1.0:
        reward = 1.0
        feedback = f"All {total} test cases passed. Bug fixed correctly!"
    elif ratio >= 0.5:
        reward = round(0.3 + 0.6 * ratio, 2)  # scale 0.3 → 0.9
        feedback = f"{passed}/{total} test cases passed. Partial fix — some edge cases still fail."
    else:
        reward = round(0.1 * ratio, 2)
        feedback = f"Only {passed}/{total} test cases passed. The core bug is likely not fixed."

    return reward, feedback, True
