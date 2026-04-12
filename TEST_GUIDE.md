# Code review environment — testing guide

## Low rewards versus incorrect responses

A **low reward** usually means the submitted response did not satisfy the grader for the selected task (wrong format, wrong content, or failed tests). It does not by itself indicate a broken UI or API.

**API note:** Rewards are clamped to a strict open interval `(0, 1)` (implementation uses bounds away from `0.0` and `1.0`; see `score_clamp.py`). The UI may display values such as `0.00` or `1.00` due to rounding; interpret them as **low** or **high** bands.

---

## Task-specific response formats

### Task 1: Bug identification (easy)

**Requirements**

- Read the snippet.
- Reply with **only** the bug type as a short phrase.
- No explanations, markdown, or extra text.

**Correct examples**

```
off-by-one error
division by zero
wrong initial value
infinite loop
command injection
null pointer dereference
```

**Incorrect examples**

```
There is an off-by-one error
off-by-one
The bug is off-by-one error
off by one error
```

The last form may score if it matches a synonym list, but prefer the canonical phrasing from the dataset when known.

**Scoring (conceptual)**

- High band: exact or alias match.
- Mid band: partial keyword overlap.
- Low band: wrong or empty (then clamped for API output).

**Snippet 0 (initial load example)**

```python
def sum_list(nums):
    total = 0
    for i in range(len(nums) + 1):  # bug: off-by-one iteration bound
        total += nums[i]
    return total
```

**Expected answer:** `off-by-one error`

---

### Task 2: Bug fixing (medium)

**Requirements**

- Reply with **only** the corrected Python for the requested function.
- No markdown fences, no prose before or after the code.
- The implementation must pass all snippet-specific unit tests in the grader.

**Correct shape**

```
def function_name(args):
    # body
    return value
```

**Incorrect patterns**

- Wrapping code in ` ```python ` fences.
- Explanatory text before or after the function.

**Scoring (conceptual)**

- High band: all tests pass.
- Mid band: proportional pass rate where supported.
- Low band: syntax errors, timeouts, or sandbox failures.

**Snippet 0 — test intent (illustrative)**

| Input | Expected output |
|--------|-----------------|
| `[1, 2, 3]` | `6` |
| `[10, 20]` | `30` |
| `[0]` | `0` |
| `[]` | `0` |

Resubmitting the buggy source unchanged yields a low score.

**Example fix**

```
def sum_list(nums):
    total = 0
    for i in range(len(nums)):
        total += nums[i]
    return total
```

---

### Task 3: Full code review (hard)

**Requirements**

- Reply with **only** a single JSON object.
- No markdown, no commentary.
- Top-level keys: `bugs`, `security_issues`, `style_violations` (each a list of findings).

**Finding object shape**

```json
{
  "line": 3,
  "severity": "high",
  "description": "Descriptive message about the issue"
}
```

**Incorrect patterns**

- JSON inside markdown code fences only (fences must not be sent as the response body if the grader expects raw JSON).
- Bulleted prose instead of structured lists.
- Lists of plain strings instead of objects with `line`, `severity`, `description`.

**Severity values**

- `"high"` — critical defect or security issue.
- `"medium"` — important but not catastrophic.
- `"low"` — style, maintainability, or minor issues.

**Category weights (hard task, high level)**

- Bugs: approximately 40%.
- Security issues: approximately 35%.
- Style violations: approximately 15%.
- Severity ordering: approximately 10%.

See `tasks/task_hard.py` for exact constants.

**Snippet 0 — reference-style JSON**

```json
{
  "bugs": [
    {
      "line": 3,
      "severity": "high",
      "description": "range(len(nums) + 1) causes IndexError on the last iteration"
    }
  ],
  "security_issues": [],
  "style_violations": [
    {
      "line": 3,
      "severity": "low",
      "description": "Use enumerate() or sum() instead of a manual index loop"
    }
  ]
}
```

---

## Manual test procedure

### Test 1: Easy task

1. Open the Space or local UI.
2. Select **Bug identification (easy)**.
3. Start an episode (**Start review** or equivalent).
4. Submit only the bug-type phrase.
5. Inspect feedback and reward: high band implies a match to expected labels; low band implies mismatch or formatting issues.

### Test 2: Medium task

1. Select **Bug fixing (medium)**.
2. Start an episode.
3. Paste a complete corrected function with no markdown wrappers.
4. Submit and inspect reward: proportional to tests passed; syntax errors map to the low band.

### Test 3: Hard task

1. Select **Full review (hard)**.
2. Start an episode.
3. Emit valid JSON with all three categories populated as required.
4. Submit and inspect reward: depends on overlap with gold lists, ordering, and validity constraints.

---

## Common issues

| Symptom | Likely cause | Mitigation |
|---------|--------------|------------|
| Persistently low reward | Wrong output shape for the task | Reread the format section for that task |
| Persistently low reward | Empty submission | Ensure non-empty input |
| Persistently low reward | Markdown fences on medium/hard | Send raw code or raw JSON only |
| Episode ends immediately with errors | Python syntax error on medium | Validate locally before submit |
| No response in UI | Network or server error | Browser devtools: Network tab and console |
| Cannot submit second answer | Episode already terminal | Use **Reset** to start a new episode |

---

## Browser debugging

Open developer tools (F12), **Console** and **Network** tabs:

- Confirm `POST` requests to `/step` return HTTP 200 and a JSON body containing `reward`.
- On failure, verify `API_BASE_URL` (if configurable) points at the intended host.

---

## UI regression checklist

After layout or CSS changes, confirm:

- [ ] Result panel text does not overlap other panels.
- [ ] Feedback wraps without clipping.
- [ ] Reward remains readable.
- [ ] Status indicator matches grader outcome.
- [ ] Long snippets scroll inside their container.

---

## Summary

Low rewards typically indicate **format or content mismatch** with the task grader. Use the examples above, align responses with `score_clamp.py` / API semantics, and validate medium-task code locally when possible.
