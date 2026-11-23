"""Deterministic issue-level scoring and error analysis."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .schemas import ExpectedIssue, Finding, validate_expected_issue, validate_finding


@dataclass(frozen=True)
class ScoreResult:
    expected_count: int
    finding_count: int
    true_positive_count: int
    false_positive_count: int
    false_negative_count: int
    precision: float
    recall: float
    f1: float
    matched: tuple[dict[str, str], ...]
    false_positives: tuple[dict[str, object], ...]
    false_negatives: tuple[dict[str, object], ...]
    severity_mismatches: tuple[dict[str, str], ...]

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-serializable report with stable key/list ordering."""
        return {
            "counts": {
                "expected": self.expected_count,
                "findings": self.finding_count,
                "true_positives": self.true_positive_count,
                "false_positives": self.false_positive_count,
                "false_negatives": self.false_negative_count,
            },
            "metrics": {
                "precision": self.precision,
                "recall": self.recall,
                "f1": self.f1,
            },
            "matched": [dict(item) for item in self.matched],
            "false_positives": [dict(item) for item in self.false_positives],
            "false_negatives": [dict(item) for item in self.false_negatives],
            "severity_mismatches": [dict(item) for item in self.severity_mismatches],
        }


def _as_expected(items: Iterable[ExpectedIssue | dict[str, object]]) -> list[ExpectedIssue]:
    return [item if isinstance(item, ExpectedIssue) else validate_expected_issue(item) for item in items]


def _as_findings(items: Iterable[Finding | dict[str, object]]) -> list[Finding]:
    return [item if isinstance(item, Finding) else validate_finding(item, f"findings[{i}]") for i, item in enumerate(items)]


def _finding_record(finding: Finding) -> dict[str, object]:
    return {
        "finding_id": finding.id,
        "title": finding.title,
        "severity": finding.severity,
        "file": finding.file,
        "line": finding.line,
        "category": finding.category,
        "evidence_quality": finding.evidence_quality,
    }


def _expected_record(issue: ExpectedIssue) -> dict[str, object]:
    return {
        "expected_issue_id": issue.id,
        "title": issue.title,
        "severity": issue.severity,
        "file": issue.file,
        "line": issue.line,
        "line_end": issue.effective_line_end,
        "category": issue.category,
    }


def _matches(issue: ExpectedIssue, finding: Finding) -> bool:
    if finding.expected_issue_id is not None:
        return finding.expected_issue_id == issue.id
    if finding.file != issue.file or not (issue.line <= finding.line <= issue.effective_line_end):
        return False
    return finding.category is None or finding.category == issue.category


def score_findings(
    expected_issues: Iterable[ExpectedIssue | dict[str, object]],
    findings: Iterable[Finding | dict[str, object]],
) -> ScoreResult:
    """Score findings against expected issues using one-to-one deterministic matching.

    A finding with ``expected_issue_id`` matches only that expected issue.
    Otherwise, its file and line must fall in the expected issue's inclusive
    line range; a supplied finding category must also equal the expected category.
    Severity does not affect detection counts and is reported separately.

    Empty-empty is scored as precision=recall=F1=1.0 (no misses or noise).
    When only one side is empty, the absent side's metric is 1.0 and the
    metric for the side with errors is 0.0.
    """
    expected = _as_expected(expected_issues)
    observed = _as_findings(findings)
    expected_ids = [issue.id for issue in expected]
    finding_ids = [finding.id for finding in observed]
    if len(expected_ids) != len(set(expected_ids)):
        raise ValueError("expected issue IDs must be unique")
    if len(finding_ids) != len(set(finding_ids)):
        raise ValueError("finding IDs must be unique")

    # Stable ordering makes assignments and reports independent of input order.
    expected = sorted(expected, key=lambda item: (item.id, item.file, item.line))
    observed = sorted(observed, key=lambda item: (item.id, item.file, item.line))
    unmatched_expected = {item.id: item for item in expected}
    matched: list[dict[str, str]] = []
    mismatches: list[dict[str, str]] = []
    false_positives: list[dict[str, object]] = []

    for finding in observed:
        candidates = [issue for issue in expected if issue.id in unmatched_expected and _matches(issue, finding)]
        if not candidates:
            false_positives.append(_finding_record(finding))
            continue
        issue = candidates[0]
        unmatched_expected.pop(issue.id)
        matched.append({"expected_issue_id": issue.id, "finding_id": finding.id})
        if issue.severity != finding.severity:
            mismatches.append({
                "expected_issue_id": issue.id,
                "finding_id": finding.id,
                "expected_severity": issue.severity,
                "finding_severity": finding.severity,
            })

    false_negatives = [_expected_record(issue) for issue in expected if issue.id in unmatched_expected]
    tp = len(matched)
    fp = len(false_positives)
    fn = len(false_negatives)
    precision = tp / (tp + fp) if tp + fp else 1.0
    recall = tp / (tp + fn) if tp + fn else 1.0
    f1 = (2 * precision * recall / (precision + recall)) if precision + recall else 0.0
    return ScoreResult(
        expected_count=len(expected),
        finding_count=len(observed),
        true_positive_count=tp,
        false_positive_count=fp,
        false_negative_count=fn,
        precision=precision,
        recall=recall,
        f1=f1,
        matched=tuple(matched),
        false_positives=tuple(false_positives),
        false_negatives=tuple(false_negatives),
        severity_mismatches=tuple(mismatches),
    )
