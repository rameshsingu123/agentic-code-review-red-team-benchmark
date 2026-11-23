# Agentic Code Review Red-Team Benchmark

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Tests: pytest](https://img.shields.io/badge/tests-pytest-informational.svg)](https://pytest.org/)

A small, dependency-free Python toolkit for validating code-review benchmark data, loading labeled scenarios, and comparing review findings with expected issues. It is an independent portfolio project by [Ramesh Singu](https://github.com/rameshsingu123), intended to make review outcomes and misses easier to inspect—not to claim performance for any agent, model, or benchmark suite.

## What and why

Code-review evaluations can be difficult to compare when a finding is judged only by a narrative summary. This project provides a simple, transparent baseline: validate scenario and finding records, match detections against labeled issues, calculate precision/recall/F1, and list false positives and false negatives explicitly. The included examples cover SQL injection and path traversal as well as a pagination boundary error.

## Scoring

The scorer performs one-to-one issue-level matching. If a finding includes `expected_issue_id`, it matches only the issue with that exact ID. Otherwise, the finding must have the same file and a line inside the expected issue's inclusive `line`–`line_end` range (a missing `line_end` means the single `line`); if the finding supplies a category, that category must also match. Repeated findings cannot claim the same expected issue. Stable sorting makes the assignment and report reproducible.

Severity does not affect detection precision/recall/F1; a matched severity disagreement is listed separately. Findings require a severity (`critical`, `high`, `medium`, `low`, or `info`) and evidence-quality label (`strong`, `moderate`, `weak`, or `insufficient`). Evidence quality is validated and included in false-positive detail, but is not a weighted score.

- **Precision** = true positives / (true positives + false positives)
- **Recall** = true positives / (true positives + false negatives)
- **F1** = harmonic mean of precision and recall

When both expected issues and findings are empty, all three metrics are `1.0`. With expected issues but no findings, precision is `1.0` (there are no predicted positives), recall and F1 are `0.0`. With findings and no expected issues, recall is `1.0`, precision and F1 are `0.0`. These conventions are explicit so empty runs never divide by zero.

## Installation

Requires Python 3.10 or newer. Runtime code uses only the Python standard library.

```bash
python -m pip install -e ".[dev]"
```

The `dev` extra installs pytest. To use the package without installing it, run from the repository root with `PYTHONPATH=src`.

## Usage

`examples/findings_sample.json` contains a `findings` array. Load that array, validate it, score it against the security scenario, and print a text report:

```python
import json
from pathlib import Path

from review_benchmark import load_scenario, score_findings, text_report, validate_findings

scenario = load_scenario("examples/scenario_security.json")
payload = json.loads(Path("examples/findings_sample.json").read_text(encoding="utf-8"))
findings = validate_findings(payload["findings"])
result = score_findings(scenario.expected_issues, findings)
print(text_report(result), end="")
```

The above example produces:

```text
Code review benchmark
Expected issues: 2
Findings:        2
True positives:  1
False positives: 1
False negatives: 1
Precision: 0.500
Recall:    0.500
F1:        0.500
False-positive analysis:
  - F-002: Database access may fail under load (app.py:6)
False-negative analysis:
  - SEC-002: Path traversal in note reader (app.py:9)
Severity mismatches: none
```

Use `json_report(result)` for deterministic, indented JSON. `load_scenarios("examples")` loads all JSON scenarios in filename order. The public `validate_scenario`, `validate_finding`, and `validate_findings` functions raise `ValidationError` with a field-oriented message when input is malformed.

## Tests

From the repository root:

```bash
pytest
```

## Limitations

This is a compact, transparent evaluation utility, not a complete code-review platform. Matching depends on accurate file paths and line annotations (unless a caller supplies an expected-issue ID); it does not infer semantic equivalence, merge duplicate findings, or grade evidence quality. The included scenarios are examples, not a statistically representative benchmark, and no model or agent performance has been measured or implied. Review results still require human interpretation, especially when source locations shift or a finding spans several lines.

**Independent portfolio project - not a deployed enterprise or customer system**

**Independent portfolio project, public on GitHub. Not deployed enterprise or customer system.**
