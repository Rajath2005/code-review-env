"""
Task: Bug Identification (Easy)
--------------------------------
Agent receives a buggy Python snippet.
Agent must respond with the bug TYPE - a short phrase describing what's wrong.

Scoring:
  1.0  - exact match, known alias, or synonym map hit
  0.7  - partial keyword overlap (agent got the gist)
  0.0  - completely wrong or empty
"""

import logging
import re
from data.snippets import SNIPPETS

SYNONYM_MAP = {
    "off by one error":              ["off by one", "fence post", "fencepost", "oboe", "index out of range", "range error", "array index error"],
    "division by zero":              ["zero division", "zerodivisionerror", "zero division error", "divide by zero", "missing zero check", "division error"],
    "wrong initial value":           ["wrong default", "incorrect initialisation", "incorrect initialization", "bad initial value", "initialisation error"],
    "command injection":             ["shell injection", "os injection", "code injection", "injection vulnerability", "arbitrary command"],
    "infinite recursion":            ["recursion error", "stack overflow", "missing base case", "wrong recursive call", "recursionerror"],
    "null pointer dereference":      ["none dereference", "nonetype error", "missing null check", "typeerror on none", "attributeerror on none"],
    "mutating list while iterating": ["list mutation during iteration", "concurrent modification", "modifying list in loop"],
    "case sensitivity error":        ["missing case normalisation", "missing case normalization", "case insensitive check missing", "missing lower"],
    "resource leak":                 ["file not closed", "missing file close", "unclosed file handle", "missing context manager"],
    "infinite loop":                 ["loop does not terminate", "low never advances", "loop never exits", "non terminating loop"],
    "wrong operator":                ["comparison instead of assignment", "assignment vs comparison", "== instead of =", "assignment error"],
    "wrong method call":             ["append instead of extend", "nested list not flattened", "wrong list method"],
    "insecure deserialization":      ["pickle vulnerability", "arbitrary code execution", "unsafe deserialization"],
    "hardcoded secret":              ["hardcoded credential", "secret in source code", "insecure default", "plaintext credential", "hardcoded password"],
    "sql injection":                 ["unsanitised sql", "unsanitized sql", "string formatting in sql", "parameterised query missing"],
    "incomplete merge":              ["missing tail elements", "remaining elements not appended"],
    "performance bug":               ["inefficient algorithm", "quadratic complexity", "should use sqrt", "slow implementation"],
    "mutable default argument":      ["shared mutable default", "default argument mutation", "mutable default"],
    "in place mutation":             ["modifies input list", "sorts in place", "unexpected side effect", "mutates argument"],
    "race condition":                ["thread safety issue", "data race", "missing lock", "unsynchronised access"],
    "missing input validation":      ["no error handling", "keyerror possible", "unvalidated input", "missing validation"],
    "syntax error":                  ["assignment in condition", "= instead of ==", "invalid syntax"],
    "hardcoded credential":          ["hardcoded password", "plaintext password", "smtp credentials hardcoded"],
    "eval misuse":                    ["eval injection", "unsafe eval", "code injection via eval"],
    "unsafe file handling":          ["path traversal", "unsafe path join", "unsafe delete", "missing path validation"],
    "incorrect loop bounds":         ["off by one", "inclusive range", "loop bound error"],
    "wrong variable used":           ["uses wrong variable", "wrong field referenced", "incorrect variable"],
    "memory leak":                   ["unbounded cache", "growing list", "no cache eviction"],
    "index out of range":            ["index error", "range error", "out of bounds"],
}

LOGGER = logging.getLogger(__name__)


def _get_snippet(snippet_id: int) -> dict:
    for s in SNIPPETS:
        if s["id"] == snippet_id:
            return s
    raise ValueError(f"Unknown snippet_id: {snippet_id}")


def _normalise(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[-_]", " ", text)
    text = re.sub(r"[^\w\s]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _check_synonym_map(response: str, expected: str) -> bool:
    for canonical, synonyms in SYNONYM_MAP.items():
        all_forms = [_normalise(canonical)] + [_normalise(s) for s in synonyms]
        if expected in all_forms:
            return response in all_forms
    return False


def _log_metrics(score: float) -> None:
    accuracy = 1.0 if score == 1.0 else 0.0
    precision = score
    recall = score
    LOGGER.info(
        "easy_metrics accuracy=%.2f precision=%.2f recall=%.2f score=%.2f",
        accuracy,
        precision,
        recall,
        score,
    )


def run_easy_task(agent_response: str, snippet_id: int) -> tuple[float, str, bool]:
    snippet = _get_snippet(snippet_id)
    expected = _normalise(snippet["bug_type"])
    aliases = [_normalise(a) for a in snippet["bug_type_aliases"]]
    response = _normalise(agent_response)

    # 1. Exact match
    if response == expected or response in aliases:
        _log_metrics(1.0)
        return 1.0, f"Correct! The bug is: {snippet['bug_type']}", True

    # 2. Synonym map
    if _check_synonym_map(response, expected):
        _log_metrics(1.0)
        return 1.0, f"Correct! The bug is: {snippet['bug_type']}", True

    # 3. Close match (keyword overlap)
    stop = {"the", "a", "an", "is", "in", "on", "to", "of", "and", "or", "with", "error", "bug", "issue"}
    exp_kws = set(expected.split()) - stop
    res_kws = set(response.split()) - stop

    overlap = exp_kws & res_kws
    alias_overlap = max(
        (len((set(_normalise(a).split()) - stop) & res_kws) for a in snippet["bug_type_aliases"]),
        default=0
    )
    best = max(len(overlap), alias_overlap)
    needed = max(1, len(exp_kws) // 2)

    if best >= needed and response:
        _log_metrics(0.7)
        return 0.7, (
            f"Partially correct. The exact bug type is: '{snippet['bug_type']}'"
        ), True

    # 4. Keyword match (weak signal)
    if response and best > 0:
        _log_metrics(0.4)
        return 0.4, (
            f"Somewhat related. The exact bug type is: '{snippet['bug_type']}'"
        ), True

    _log_metrics(0.0)
    return 0.0, (
        f"Incorrect. The bug type is: '{snippet['bug_type']}'. "
        f"Hint: look at control flow and data flow carefully."
    ), True
