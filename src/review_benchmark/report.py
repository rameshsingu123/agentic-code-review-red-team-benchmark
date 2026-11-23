"""Deterministic JSON and plain-text report formatting."""

from __future__ import annotations

import json

from .scorer import ScoreResult


def json_report(result: ScoreResult) -> str:
    """Serialize a score result as stable, indented JSON with a final newline."""
    return json.dumps(result.to_dict(), indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def text_report(result: ScoreResult) -> str:
    """Format metrics and explicit false-positive/false-negative analysis."""
    lines = [
        "Code review benchmark",
        f"Expected issues: {result.expected_count}",
        f"Findings:        {result.finding_count}",
        f"True positives:  {result.true_positive_count}",
        f"False positives: {result.false_positive_count}",
        f"False negatives: {result.false_negative_count}",
        f"Precision: {result.precision:.3f}",
        f"Recall:    {result.recall:.3f}",
        f"F1:        {result.f1:.3f}",
    ]
    if result.false_positives:
        lines.append("False-positive analysis:")
        for item in result.false_positives:
            lines.append(f"  - {item['finding_id']}: {item['title']} ({item['file']}:{item['line']})")
    else:
        lines.append("False-positive analysis: none")
    if result.false_negatives:
        lines.append("False-negative analysis:")
        for item in result.false_negatives:
            lines.append(f"  - {item['expected_issue_id']}: {item['title']} ({item['file']}:{item['line']})")
    else:
        lines.append("False-negative analysis: none")
    if result.severity_mismatches:
        lines.append("Severity mismatches:")
        for item in result.severity_mismatches:
            lines.append(
                f"  - {item['finding_id']} / {item['expected_issue_id']}: "
                f"expected {item['expected_severity']}, found {item['finding_severity']}"
            )
    else:
        lines.append("Severity mismatches: none")
    return "\n".join(lines) + "\n"
