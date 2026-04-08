"""
Batch evaluation for regression checks.
Scores gold responses across all snippets for easy/medium/hard tasks.
"""

from __future__ import annotations

import argparse
import json
from typing import Any

from data.snippets import SNIPPETS
from tasks.task_easy import run_easy_task
from tasks.task_hard import run_hard_task
from tasks.task_medium import run_medium_task


def _summarize(scores: list[float]) -> dict[str, float]:
    if not scores:
        return {"avg": 0.0, "min": 0.0, "max": 0.0}
    return {
        "avg": round(sum(scores) / len(scores), 3),
        "min": round(min(scores), 3),
        "max": round(max(scores), 3),
    }


def _evaluate_easy() -> list[dict[str, Any]]:
    results = []
    for snippet in SNIPPETS:
        score, _, _ = run_easy_task(snippet["bug_type"], snippet["id"])
        results.append({"id": snippet["id"], "score": score})
    return results


def _evaluate_medium() -> list[dict[str, Any]]:
    results = []
    for snippet in SNIPPETS:
        score, _, _ = run_medium_task(snippet["fixed_code"], snippet["id"])
        results.append({
            "id": snippet["id"],
            "score": score,
            "has_tests": bool(snippet.get("test_cases")),
        })
    return results


def _evaluate_hard() -> list[dict[str, Any]]:
    results = []
    for snippet in SNIPPETS:
        response = json.dumps(snippet["review"])
        score, _, _ = run_hard_task(response, snippet["id"])
        results.append({"id": snippet["id"], "score": score})
    return results


def _print_summary(label: str, results: list[dict[str, Any]]) -> None:
    scores = [r["score"] for r in results]
    summary = _summarize(scores)
    print(f"{label}: avg={summary['avg']} min={summary['min']} max={summary['max']}")


def _print_detail(label: str, results: list[dict[str, Any]]) -> None:
    print(f"{label} per snippet:")
    for item in results:
        extra = ""
        if "has_tests" in item:
            extra = " (tests)" if item["has_tests"] else " (no-tests)"
        print(f"  id={item['id']}: score={item['score']}{extra}")


def _check_threshold(name: str, avg: float, threshold: float | None) -> bool:
    if threshold is None:
        return True
    if avg < threshold:
        print(f"FAIL: {name} avg {avg} < threshold {threshold}")
        return False
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Batch-score all snippets for regression checks")
    parser.add_argument("--json", action="store_true", help="Emit JSON summary only")
    parser.add_argument("--detail", action="store_true", help="Print per-snippet scores")
    parser.add_argument("--fail-threshold-easy", type=float, default=None)
    parser.add_argument("--fail-threshold-medium", type=float, default=None)
    parser.add_argument("--fail-threshold-medium-tested", type=float, default=None)
    parser.add_argument("--fail-threshold-hard", type=float, default=None)
    args = parser.parse_args()

    easy = _evaluate_easy()
    medium = _evaluate_medium()
    hard = _evaluate_hard()

    easy_summary = _summarize([r["score"] for r in easy])
    medium_summary = _summarize([r["score"] for r in medium])
    hard_summary = _summarize([r["score"] for r in hard])

    medium_tested = [r["score"] for r in medium if r["has_tests"]]
    medium_tested_summary = _summarize(medium_tested)

    if args.json:
        payload = {
            "easy": easy_summary,
            "medium": medium_summary,
            "medium_tested": medium_tested_summary,
            "hard": hard_summary,
        }
        print(json.dumps(payload, indent=2))
    else:
        _print_summary("easy", easy)
        _print_summary("medium", medium)
        print(
            f"medium_tested: avg={medium_tested_summary['avg']} "
            f"min={medium_tested_summary['min']} max={medium_tested_summary['max']}"
        )
        _print_summary("hard", hard)

        if args.detail:
            _print_detail("easy", easy)
            _print_detail("medium", medium)
            _print_detail("hard", hard)

    ok = True
    ok &= _check_threshold("easy", easy_summary["avg"], args.fail_threshold_easy)
    ok &= _check_threshold("medium", medium_summary["avg"], args.fail_threshold_medium)
    ok &= _check_threshold(
        "medium_tested", medium_tested_summary["avg"], args.fail_threshold_medium_tested
    )
    ok &= _check_threshold("hard", hard_summary["avg"], args.fail_threshold_hard)

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
