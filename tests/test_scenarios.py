from pathlib import Path

import pytest

from review_benchmark import load_scenarios


def test_load_scenarios_returns_filename_ordered_examples():
    scenarios = load_scenarios(Path("examples"))
    assert [scenario.id for scenario in scenarios] == [
        "correctness-pagination-boundary",
        "security-sql-and-path",
    ]


def test_load_scenarios_requires_a_directory(tmp_path):
    with pytest.raises(NotADirectoryError):
        load_scenarios(tmp_path / "missing")
