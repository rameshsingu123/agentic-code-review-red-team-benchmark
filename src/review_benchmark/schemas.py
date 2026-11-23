"""Typed data models and validation for code-review benchmark inputs."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping
import json

SEVERITIES = frozenset({"critical", "high", "medium", "low", "info"})
EVIDENCE_QUALITIES = frozenset({"strong", "moderate", "weak", "insufficient"})


class ValidationError(ValueError):
    """Raised when scenario or finding data violates the input contract."""


@dataclass(frozen=True)
class ExpectedIssue:
    id: str
    title: str
    description: str
    severity: str
    file: str
    line: int
    category: str
    line_end: int | None = None

    @property
    def effective_line_end(self) -> int:
        return self.line_end if self.line_end is not None else self.line


@dataclass(frozen=True)
class Scenario:
    id: str
    title: str
    description: str
    language: str
    code: str
    expected_issues: tuple[ExpectedIssue, ...]


@dataclass(frozen=True)
class Finding:
    id: str
    title: str
    description: str
    severity: str
    file: str
    line: int
    evidence: str
    evidence_quality: str
    category: str | None = None
    expected_issue_id: str | None = None


def _mapping(value: Any, where: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValidationError(f"{where} must be an object")
    return value


def _required_text(data: Mapping[str, Any], key: str, where: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValidationError(f"{where}.{key} must be a non-empty string")
    return value.strip()


def _optional_text(data: Mapping[str, Any], key: str, where: str) -> str | None:
    value = data.get(key)
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ValidationError(f"{where}.{key} must be a non-empty string when provided")
    return value.strip()


def _line(data: Mapping[str, Any], key: str, where: str, *, required: bool = True) -> int | None:
    value = data.get(key)
    if value is None and not required:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValidationError(f"{where}.{key} must be a positive integer")
    return value


def _severity(data: Mapping[str, Any], where: str) -> str:
    value = _required_text(data, "severity", where).lower()
    if value not in SEVERITIES:
        choices = ", ".join(sorted(SEVERITIES))
        raise ValidationError(f"{where}.severity must be one of: {choices}")
    return value


def validate_expected_issue(value: Any, where: str = "expected_issue") -> ExpectedIssue:
    data = _mapping(value, where)
    line = _line(data, "line", where)
    line_end = _line(data, "line_end", where, required=False)
    if line_end is not None and line_end < line:
        raise ValidationError(f"{where}.line_end must be greater than or equal to line")
    return ExpectedIssue(
        id=_required_text(data, "id", where),
        title=_required_text(data, "title", where),
        description=_required_text(data, "description", where),
        severity=_severity(data, where),
        file=_required_text(data, "file", where),
        line=line,
        category=_required_text(data, "category", where),
        line_end=line_end,
    )


def validate_scenario(value: Any) -> Scenario:
    """Validate a decoded scenario object and return an immutable model."""
    data = _mapping(value, "scenario")
    issues_value = data.get("expected_issues")
    if not isinstance(issues_value, list):
        raise ValidationError("scenario.expected_issues must be a list")
    issues = tuple(
        validate_expected_issue(issue, f"scenario.expected_issues[{index}]")
        for index, issue in enumerate(issues_value)
    )
    issue_ids = [issue.id for issue in issues]
    if len(issue_ids) != len(set(issue_ids)):
        raise ValidationError("scenario.expected_issues must have unique id values")
    code = data.get("code")
    if not isinstance(code, str):
        raise ValidationError("scenario.code must be a string")
    return Scenario(
        id=_required_text(data, "id", "scenario"),
        title=_required_text(data, "title", "scenario"),
        description=_required_text(data, "description", "scenario"),
        language=_required_text(data, "language", "scenario"),
        code=code,
        expected_issues=issues,
    )


def validate_finding(value: Any, where: str = "finding") -> Finding:
    """Validate one finding, including severity and evidence-quality labels."""
    data = _mapping(value, where)
    quality = _required_text(data, "evidence_quality", where).lower()
    if quality not in EVIDENCE_QUALITIES:
        choices = ", ".join(sorted(EVIDENCE_QUALITIES))
        raise ValidationError(f"{where}.evidence_quality must be one of: {choices}")
    return Finding(
        id=_required_text(data, "id", where),
        title=_required_text(data, "title", where),
        description=_required_text(data, "description", where),
        severity=_severity(data, where),
        file=_required_text(data, "file", where),
        line=_line(data, "line", where),
        evidence=_required_text(data, "evidence", where),
        evidence_quality=quality,
        category=_optional_text(data, "category", where),
        expected_issue_id=_optional_text(data, "expected_issue_id", where),
    )


def validate_findings(value: Any) -> list[Finding]:
    """Validate a list of findings and ensure finding IDs are unique."""
    if not isinstance(value, list):
        raise ValidationError("findings must be a list")
    findings = [validate_finding(item, f"findings[{index}]") for index, item in enumerate(value)]
    ids = [finding.id for finding in findings]
    if len(ids) != len(set(ids)):
        raise ValidationError("findings must have unique id values")
    return findings


def load_scenario(path: str | Path) -> Scenario:
    """Load and validate a scenario from a UTF-8 JSON file."""
    scenario_path = Path(path)
    try:
        with scenario_path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except json.JSONDecodeError as exc:
        raise ValidationError(f"invalid JSON in {scenario_path}: {exc.msg}") from exc
    return validate_scenario(payload)
