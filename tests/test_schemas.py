import pytest

from review_benchmark import (
    ValidationError,
    load_scenario,
    validate_finding,
    validate_findings,
    validate_scenario,
)


def valid_scenario():
    return {
        "id": "demo",
        "title": "Demo",
        "description": "A test scenario.",
        "language": "python",
        "code": "print('hello')\n",
        "expected_issues": [
            {
                "id": "ISSUE-1",
                "title": "Example issue",
                "description": "A labeled issue.",
                "severity": "medium",
                "file": "main.py",
                "line": 1,
                "category": "example",
            }
        ],
    }


def valid_finding():
    return {
        "id": "F-1",
        "title": "Observed issue",
        "description": "A concrete finding.",
        "severity": "high",
        "file": "main.py",
        "line": 1,
        "evidence": "The unsafe expression is on this line.",
        "evidence_quality": "strong",
    }


def test_scenario_validation_builds_immutable_models():
    scenario = validate_scenario(valid_scenario())
    assert scenario.id == "demo"
    assert scenario.expected_issues[0].effective_line_end == 1


def test_scenario_rejects_invalid_severity():
    data = valid_scenario()
    data["expected_issues"][0]["severity"] = "urgent"
    with pytest.raises(ValidationError, match="severity"):
        validate_scenario(data)


def test_scenario_requires_unique_expected_issue_ids():
    data = valid_scenario()
    data["expected_issues"].append(dict(data["expected_issues"][0]))
    with pytest.raises(ValidationError, match="unique"):
        validate_scenario(data)


def test_scenario_rejects_inverted_line_range():
    data = valid_scenario()
    data["expected_issues"][0]["line_end"] = 0
    with pytest.raises(ValidationError, match="line_end"):
        validate_scenario(data)


def test_finding_validates_severity_and_evidence_quality():
    finding = validate_finding(valid_finding())
    assert finding.evidence_quality == "strong"
    bad = valid_finding()
    bad["evidence_quality"] = "guess"
    with pytest.raises(ValidationError, match="evidence_quality"):
        validate_finding(bad)
    bad = valid_finding()
    bad["severity"] = "blocker"
    with pytest.raises(ValidationError, match="severity"):
        validate_finding(bad)


def test_findings_reject_duplicate_ids():
    finding = valid_finding()
    with pytest.raises(ValidationError, match="unique"):
        validate_findings([finding, dict(finding)])


def test_example_scenario_loads():
    scenario = load_scenario("examples/scenario_security.json")
    assert scenario.id == "security-sql-and-path"
    assert len(scenario.expected_issues) == 2
