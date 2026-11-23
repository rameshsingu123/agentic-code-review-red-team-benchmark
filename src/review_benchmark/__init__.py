"""A small, dependency-free benchmark toolkit for code-review findings."""

from .report import json_report, text_report
from .scenarios import load_scenario, load_scenarios
from .schemas import (
    EVIDENCE_QUALITIES,
    SEVERITIES,
    ExpectedIssue,
    Finding,
    Scenario,
    ValidationError,
    validate_finding,
    validate_findings,
    validate_scenario,
)
from .scorer import ScoreResult, score_findings

__all__ = [
    "EVIDENCE_QUALITIES",
    "SEVERITIES",
    "ExpectedIssue",
    "Finding",
    "Scenario",
    "ScoreResult",
    "ValidationError",
    "json_report",
    "load_scenario",
    "load_scenarios",
    "score_findings",
    "text_report",
    "validate_finding",
    "validate_findings",
    "validate_scenario",
]
