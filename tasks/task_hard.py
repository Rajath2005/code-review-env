"""
Task: Full Code Review (Hard)
------------------------------
Agent must produce a structured JSON review covering:
  - bugs
  - security_issues
  - style_violations

Each item needs: line (int), severity ('high'/'medium'/'low'), description (str)
Items must be ordered by severity (high → medium → low) within each category.

Scoring breakdown (total 1.0):
  0.40 — bugs found (precision + recall)
  0.35 — security_issues found
  0.15 — style_violations found
  0.10 — correct severity ordering within each category

Partial credit: each matched finding adds to the score proportionally.
"""

import json
import re
from data.snippets import SNIPPETS

SEVERITY_ORDER = {"high": 0, "medium": 1, "low": 2}
WEIGHTS = {"bugs": 0.40, "security_issues": 0.35, "style_violations": 0.15}
ORDERING_WEIGHT = 0.10


def _get_snippet(snippet_id: int) -> dict:
    for s in SNIPPETS:
        if s["id"] == snippet_id:
            return s
    raise ValueError(f"Unknown snippet_id: {snippet_id}")


def _extract_json(response: str) -> dict | None:
    """
    Try to extract JSON from agent response.
    Handles raw JSON, markdown fences, and partial wrapping.
    """
    # Strip markdown fences
    cleaned = re.sub(r"```(?:json)?", "", response).replace("```", "").strip()

    # Try direct parse
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # Try to find JSON object in response
    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    return None


def _normalise_severity(s: str) -> str:
    s = str(s).lower().strip()
    if s in SEVERITY_ORDER:
        return s
    if "high" in s or "critical" in s:
        return "high"
    if "med" in s:
        return "medium"
    return "low"


def _match_finding(agent_finding: dict, expected_findings: list[dict]) -> float:
    """
    Score one agent finding against expected findings.
    Returns best match score (0.0 – 1.0).
    """
    if not isinstance(agent_finding, dict):
        return 0.0

    agent_desc = str(agent_finding.get("description", "")).lower()
    agent_sev = _normalise_severity(agent_finding.get("severity", ""))
    agent_line = agent_finding.get("line")

    best = 0.0
    for exp in expected_findings:
        exp_desc = str(exp.get("description", "")).lower()
        exp_sev = exp.get("severity", "low")
        exp_line = exp.get("line")

        # Description keyword overlap
        agent_words = set(agent_desc.split())
        exp_words = set(exp_desc.split())
        stop = {"the", "a", "an", "is", "in", "on", "to", "of", "and", "or", "with", "—", "-"}
        overlap = (agent_words - stop) & (exp_words - stop)
        desc_score = min(1.0, len(overlap) / max(len(exp_words - stop), 1))

        # Severity match
        sev_score = 1.0 if agent_sev == exp_sev else 0.5

        # Line proximity (optional bonus)
        line_score = 0.0
        if agent_line is not None and exp_line is not None:
            diff = abs(int(agent_line) - int(exp_line))
            line_score = 1.0 if diff == 0 else (0.5 if diff <= 1 else 0.0)

        # Composite score: desc matters most
        score = 0.6 * desc_score + 0.25 * sev_score + 0.15 * line_score

        if desc_score > 0.3:  # only count if description is at least somewhat relevant
            best = max(best, score)

    return best


def _score_category(agent_items: list, expected_items: list) -> float:
    """
    Score a category (bugs / security_issues / style_violations).
    Uses precision + recall averaged (F1-style).
    """
    if not expected_items:
        # No expected findings — only penalise false positives
        false_positives = len(agent_items)
        return max(0.0, 1.0 - 0.3 * false_positives)

    if not agent_items:
        return 0.0

    # Recall: how many expected did the agent find?
    recall_scores = []
    for exp in expected_items:
        best = max((_match_finding(a, [exp]) for a in agent_items), default=0.0)
        recall_scores.append(best)
    recall = sum(recall_scores) / len(recall_scores)

    # Precision: how many agent findings are correct?
    prec_scores = []
    for a in agent_items:
        best = _match_finding(a, expected_items)
        prec_scores.append(best)
    precision = sum(prec_scores) / len(prec_scores)

    # F1
    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)


def _score_ordering(agent_items: list) -> float:
    """
    Check that items within a category are ordered high → medium → low.
    Returns 1.0 if correctly ordered, partial otherwise.
    """
    if len(agent_items) <= 1:
        return 1.0

    severities = [SEVERITY_ORDER.get(_normalise_severity(a.get("severity", "low")), 2)
                  for a in agent_items if isinstance(a, dict)]

    violations = sum(
        1 for i in range(len(severities) - 1)
        if severities[i] > severities[i + 1]
    )
    return max(0.0, 1.0 - violations / len(severities))


def run_hard_task(agent_response: str, snippet_id: int) -> tuple[float, str, bool]:
    """
    Grade the agent's full code review.

    Returns:
        reward (float): 0.0 – 1.0
        feedback (str): detailed breakdown
        done (bool): True once graded
    """
    snippet = _get_snippet(snippet_id)
    expected = snippet["review"]

    # Parse JSON
    parsed = _extract_json(agent_response)
    if parsed is None:
        return 0.0, (
            "Could not parse your response as JSON. "
            "Respond with: {\"bugs\": [...], \"security_issues\": [...], \"style_violations\": [...]}"
        ), True

    # Validate required keys
    required_keys = {"bugs", "security_issues", "style_violations"}
    missing = required_keys - set(parsed.keys())
    if missing:
        return 0.1, f"Response is missing required keys: {missing}. Score capped at 0.1.", True

    # Score each category
    category_scores = {}
    for cat, weight in WEIGHTS.items():
        agent_items = parsed.get(cat, [])
        expected_items = expected.get(cat, [])
        if not isinstance(agent_items, list):
            agent_items = []
        score = _score_category(agent_items, expected_items)
        category_scores[cat] = (score, weight)

    # Score ordering across all categories
    all_agent_items = [
        item
        for cat in ["bugs", "security_issues", "style_violations"]
        for item in parsed.get(cat, [])
        if isinstance(item, dict)
    ]
    ordering_score = _score_ordering(all_agent_items)

    # Weighted total
    total = sum(score * weight for score, weight in category_scores.values())
    total += ordering_score * ORDERING_WEIGHT
    total = round(min(1.0, total), 3)

    # Build feedback
    feedback_parts = []
    for cat, (score, weight) in category_scores.items():
        pct = round(score * 100)
        feedback_parts.append(f"{cat}: {pct}% match")
    feedback_parts.append(f"severity ordering: {round(ordering_score * 100)}%")
    feedback = f"Score {total:.2f} — " + " | ".join(feedback_parts)

    return total, feedback, True
