"""Scenario-loading helpers."""

from pathlib import Path

from .schemas import Scenario, load_scenario, validate_scenario


def load_scenarios(directory: str | Path) -> list[Scenario]:
    """Load all ``scenario_*.json`` files in filename order."""
    root = Path(directory)
    if not root.is_dir():
        raise NotADirectoryError(f"scenario directory does not exist: {root}")
    return [load_scenario(path) for path in sorted(root.glob("scenario_*.json"))]


__all__ = ["Scenario", "load_scenario", "load_scenarios", "validate_scenario"]
