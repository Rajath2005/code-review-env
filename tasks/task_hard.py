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
import logging
import re
from data.snippets import SNIPPETS

SEVERITY_ORDER = {"high": 0, "medium": 1, "low": 2}
SEVERITY_WEIGHT = {"high": 1.0, "medium": 0.7, "low": 0.4}
WEIGHTS = {"bugs": 0.40, "security_issues": 0.35, "style_violations": 0.15}
ORDERING_WEIGHT = 0.10
MISSING_CRITICAL_PENALTY = 0.05
HALLUCINATION_PENALTY = 0.03
MAX_PENALTY = 0.25

LOGGER = logging.getLogger(__name__)


def _clamp_score(score: float) -> float:
    """Clamp score to open interval (0, 1) - strictly between 0 and 1."""
    if score <= 0.0:
        return 0.01
    if score >= 1.0:
        return 0.99
    return round(score, 4)


def _finalize(score: float, feedback: str, done: bool) -> tuple[float, str, bool]:
    # Defensive clamp at the last possible moment.
    return _clamp_score(score), feedback, done


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
    Returns best match score strictly within (0.01, 0.99).
    """
    if not isinstance(agent_finding, dict):
        return 0.01

    agent_desc = str(agent_finding.get("description", "")).lower()
    agent_sev = _normalise_severity(agent_finding.get("severity", ""))
    agent_line = agent_finding.get("line")

    best = 0.01
    for exp in expected_findings:
        exp_desc = str(exp.get("description", "")).lower()
        exp_sev = exp.get("severity", "low")
        exp_line = exp.get("line")

        # Description keyword overlap
        agent_words = set(agent_desc.split())
        exp_words = set(exp_desc.split())
        stop = {"the", "a", "an", "is", "in", "on", "to", "of", "and", "or", "with", "—", "-"}
        overlap = (agent_words - stop) & (exp_words - stop)
        desc_score = min(0.99, len(overlap) / max(len(exp_words - stop), 1))
        desc_score = max(0.01, desc_score)  # Clamp to (0.01, 0.99)

        # Severity match (clamp to range, not exact 0/1)
        sev_score = 0.99 if agent_sev == exp_sev else 0.45

        # Line proximity (optional bonus) -- clamp away from exact 0/1
        line_score = 0.01
        if agent_line is not None and exp_line is not None:
            diff = abs(int(agent_line) - int(exp_line))
            line_score = 0.99 if diff == 0 else (0.45 if diff <= 1 else 0.01)

        # Composite score: desc matters most (will be between 0.01 and 0.99)
        score = 0.6 * desc_score + 0.25 * sev_score + 0.15 * line_score
        score = max(0.01, min(0.99, score))  # Final clamp

        if desc_score > 0.3:  # only count if description is at least somewhat relevant
            best = max(best, score)

    return best


def _severity_weight(severity: str) -> float:
    return SEVERITY_WEIGHT.get(_normalise_severity(severity), 0.4)


def _score_category(agent_items: list, expected_items: list) -> tuple[float, float, float, int, int]:
    """
    Score a category (bugs / security_issues / style_violations).
    Returns (f1, precision, recall, hallucinations, missing_critical).
    Note: These are internal metrics, but we clamp them to avoid exact 0/1.
    """
    if not expected_items:
        false_positives = len(agent_items)
        precision = max(0.01, 0.99 - 0.3 * false_positives)  # Avoid exact 0.0 or 1.0
        precision = min(precision, 0.99)  # Cap at 0.99
        recall = 0.99  # Avoid exact 1.0
        f1 = 0.01 if precision < 0.05 else 2 * precision * recall / (precision + recall)
        f1 = round(f1, 3)
        return f1, precision, recall, false_positives, 0

    if not agent_items:
        return 0.01, 0.01, 0.01, 0, len([e for e in expected_items if _normalise_severity(e.get("severity", "low")) == "high"])

    expected_weights = [_severity_weight(e.get("severity", "low")) for e in expected_items]
    expected_weight_total = max(sum(expected_weights), 1e-6)

    recall_scores = []
    missing_critical = 0
    for exp, weight in zip(expected_items, expected_weights):
        best = max((_match_finding(a, [exp]) for a in agent_items), default=0.01)
        recall_scores.append(best * weight)
        if _normalise_severity(exp.get("severity", "low")) == "high" and best < 0.5:
            missing_critical += 1
    recall = sum(recall_scores) / expected_weight_total
    recall = max(0.01, min(0.99, recall))  # Clamp to valid range

    agent_weights = [_severity_weight(a.get("severity", "low")) for a in agent_items if isinstance(a, dict)]
    agent_weight_total = max(sum(agent_weights), 1e-6)

    prec_scores = []
    hallucinations = 0
    for a, weight in zip(agent_items, agent_weights):
        best = _match_finding(a, expected_items)
        prec_scores.append(best * weight)
        if best < 0.3:
            hallucinations += 1
    precision = sum(prec_scores) / agent_weight_total
    precision = max(0.01, min(0.99, precision))  # Clamp to valid range

    if precision + recall == 0:
        f1 = 0.01  # Changed from 0.0 to avoid boundary score
    else:
        f1 = 2 * precision * recall / (precision + recall)
    
    # Final clamp: ensure all returned values are strictly between 0.01 and 0.99
    f1 = max(0.01, min(0.99, f1))

    return f1, precision, recall, hallucinations, missing_critical


def _score_ordering(agent_items: list) -> float:
    """
    Check that items within a category are ordered high → medium → low.
    Returns score strictly between 0.01 and 0.99 (never 0.0 or 1.0).
    """
    if len(agent_items) <= 1:
        return 0.99  # Perfect ordering for single/empty items

    severities = [SEVERITY_ORDER.get(_normalise_severity(a.get("severity", "low")), 2)
                  for a in agent_items if isinstance(a, dict)]

    violations = sum(
        1 for i in range(len(severities) - 1)
        if severities[i] > severities[i + 1]
    )
    
    # Calculate score: 0.99 for perfect, down to 0.01 for worst
    score = 1.0 - violations / max(1, len(severities))
    # Clamp strictly to (0.01, 0.99)
    score = max(0.01, min(0.99, round(score, 3)))
    return score


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
        score = _clamp_score(0.01)  # Minimum valid score
        return _finalize(score, (
            "Could not parse your response as JSON. "
            "Respond with: {\"bugs\": [...], \"security_issues\": [...], \"style_violations\": [...]}"
        ), True)

    # Validate required keys
    required_keys = {"bugs", "security_issues", "style_violations"}
    missing = required_keys - set(parsed.keys())
    if missing:
        score = _clamp_score(0.05)  # Minimum valid score for missing keys
        return _finalize(score, f"Response is missing required keys: {missing}. Score capped at 0.05.", True)

    # Score each category
    category_scores = {}
    precision_scores = {}
    recall_scores = {}
    hallucinations = 0
    missing_critical = 0
    for cat, weight in WEIGHTS.items():
        agent_items = parsed.get(cat, [])
        expected_items = expected.get(cat, [])
        if not isinstance(agent_items, list):
            agent_items = []
        score, precision, recall, hallucinated, missing = _score_category(agent_items, expected_items)
        category_scores[cat] = (score, weight)
        precision_scores[cat] = precision
        recall_scores[cat] = recall
        hallucinations += hallucinated
        if cat in {"bugs", "security_issues"}:
            missing_critical += missing

    # Score ordering within each category
    ordering_scores = []
    for cat in ["bugs", "security_issues", "style_violations"]:
        cat_items = [item for item in parsed.get(cat, []) if isinstance(item, dict)]
        ordering_scores.append(_score_ordering(cat_items))
    ordering_score = sum(ordering_scores) / len(ordering_scores)

    # Weighted total
    total = sum(score * weight for score, weight in category_scores.values())
    total += ordering_score * ORDERING_WEIGHT

    penalty = min(MAX_PENALTY, missing_critical * MISSING_CRITICAL_PENALTY + hallucinations * HALLUCINATION_PENALTY)
    total = total - penalty
    # Defensive multi-layer clamping to ensure no boundary scores
    total = round(total, 4)  # Round first
    total = _clamp_score(total)  # Clamp to open interval (0.01, 0.99)
    
    # Final verification: guarantee total is never exactly 0.0 or 1.0
    if total <= 0.0:
        total = 0.01
    if total >= 1.0:
        total = 0.99
    # Triple-check after all operations
    assert 0.01 <= total <= 0.99, f"Score {total} is outside valid range!"

    # Build feedback
    weighted_precision = sum(precision_scores[cat] * WEIGHTS[cat] for cat in WEIGHTS) / sum(WEIGHTS.values())
    weighted_recall = sum(recall_scores[cat] * WEIGHTS[cat] for cat in WEIGHTS) / sum(WEIGHTS.values())
    LOGGER.info(
        "hard_metrics precision=%.2f recall=%.2f missing_critical=%d hallucinations=%d",
        weighted_precision,
        weighted_recall,
        missing_critical,
        hallucinations,
    )

    feedback_parts = []
    for cat, (score, weight) in category_scores.items():
        pct = round(score * 100)
        feedback_parts.append(f"{cat}: {pct}% match")
    feedback_parts.append(f"severity ordering: {round(ordering_score * 100)}%")
    if penalty > 0:
        feedback_parts.append(f"penalty: -{round(penalty, 2)}")
    feedback = f"Score {total:.2f} — " + " | ".join(feedback_parts)

    return _finalize(total, feedback, True)
