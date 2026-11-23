from review_benchmark import score_findings, validate_findings


def issue(issue_id="I-1", line=10, severity="high"):
    return {
        "id": issue_id,
        "title": f"Expected {issue_id}",
        "description": "Expected behavior is violated.",
        "severity": severity,
        "file": "src/app.py",
        "line": line,
        "category": "security",
    }


def finding(finding_id="F-1", line=10, severity="high", **extra):
    value = {
        "id": finding_id,
        "title": f"Observed {finding_id}",
        "description": "A concrete problem was identified.",
        "severity": severity,
        "file": "src/app.py",
        "line": line,
        "evidence": "Relevant unsafe operation at this location.",
        "evidence_quality": "moderate",
    }
    value.update(extra)
    return value


def test_scores_match_false_positive_false_negative_and_severity_mismatch():
    result = score_findings(
        [issue("I-1", 10, "high"), issue("I-2", 20, "medium")],
        validate_findings([finding("F-1", 10, "low"), finding("F-2", 50)]),
    )
    assert (result.true_positive_count, result.false_positive_count, result.false_negative_count) == (1, 1, 1)
    assert result.precision == 0.5
    assert result.recall == 0.5
    assert result.f1 == 0.5
    assert result.false_positives[0]["finding_id"] == "F-2"
    assert result.false_negatives[0]["expected_issue_id"] == "I-2"
    assert result.severity_mismatches[0]["finding_id"] == "F-1"


def test_explicit_expected_issue_id_matches_even_when_location_differs():
    result = score_findings([issue()], [finding("F-1", 99, expected_issue_id="I-1")])
    assert result.true_positive_count == 1
    assert result.false_positive_count == 0


def test_explicit_unknown_expected_issue_id_does_not_fall_back_to_location():
    result = score_findings([issue()], [finding("F-1", 10, expected_issue_id="wrong")])
    assert result.true_positive_count == 0
    assert result.false_positive_count == 1
    assert result.false_negative_count == 1


def test_empty_empty_has_perfect_metrics():
    result = score_findings([], [])
    assert (result.precision, result.recall, result.f1) == (1.0, 1.0, 1.0)


def test_expected_without_findings_has_zero_recall():
    result = score_findings([issue()], [])
    assert (result.precision, result.recall, result.f1) == (1.0, 0.0, 0.0)


def test_findings_without_expected_issues_are_all_false_positives():
    result = score_findings([], [finding()])
    assert (result.precision, result.recall, result.f1) == (0.0, 1.0, 0.0)
    assert result.false_positive_count == 1
