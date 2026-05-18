"""Tests for aa_ma.tui.json_output — JSON serialiser.

Created in aa-ma-tui-tracker M2 T2.4 (2026-05-18).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest


def _check_or_bootstrap_golden_json(actual: str, golden_path: Path) -> None:
    """Compare actual JSON string to golden file; bootstrap if missing.

    Compares **parsed** dicts so key ordering and whitespace differences
    don't cause spurious failures.
    """
    if not golden_path.exists():
        golden_path.parent.mkdir(parents=True, exist_ok=True)
        golden_path.write_text(actual, encoding="utf-8")
        pytest.fail(
            f"BOOTSTRAPPED golden file at {golden_path}; re-run test to verify."
        )
    expected = json.loads(golden_path.read_text(encoding="utf-8"))
    assert json.loads(actual) == expected


# =============================================================================
# T2.4: json_output.dump (schema-validated)
# =============================================================================


def test_schema_version_constant() -> None:
    """aa_ma.tui.model.SCHEMA_VERSION is exposed and == 1."""
    from aa_ma.tui.model import SCHEMA_VERSION

    assert SCHEMA_VERSION == 1


def test_json_output_dump_returns_string(static_tasks: list) -> None:
    """dump(tasks) returns a JSON string that parses to a dict."""
    from aa_ma.tui.json_output import dump

    result = dump(static_tasks)
    assert isinstance(result, str)
    parsed = json.loads(result)
    assert isinstance(parsed, dict)


def test_json_output_includes_schema_version(static_tasks: list) -> None:
    """Top-level JSON object carries `schema_version: 1`."""
    from aa_ma.tui.json_output import dump
    from aa_ma.tui.model import SCHEMA_VERSION

    parsed = json.loads(dump(static_tasks))
    assert parsed["schema_version"] == SCHEMA_VERSION


def test_json_output_includes_all_task_names(static_tasks: list) -> None:
    """All input task names appear in the output `tasks` array."""
    from aa_ma.tui.json_output import dump

    parsed = json.loads(dump(static_tasks))
    names = [t["name"] for t in parsed["tasks"]]
    assert set(names) == {"alpha-task", "beta-task", "gamma-task"}


def test_json_output_validates_against_task_schema(static_tasks: list) -> None:
    """Each emitted task object validates against Task.model_json_schema()."""
    import jsonschema

    from aa_ma.tui.json_output import dump
    from aa_ma.tui.model import Task

    parsed = json.loads(dump(static_tasks))
    schema = Task.model_json_schema()
    for task_obj in parsed["tasks"]:
        jsonschema.validate(instance=task_obj, schema=schema)


def test_json_output_matches_golden(static_tasks: list, snapshots_dir: Path) -> None:
    """End-to-end golden equality (semantic JSON equality)."""
    from aa_ma.tui.json_output import dump

    output = dump(static_tasks)
    _check_or_bootstrap_golden_json(output, snapshots_dir / "data.json")


def test_json_output_reuses_parser_discover_tasks() -> None:
    """json_output module imports the SAME discover_tasks as parser (L-052)."""
    import aa_ma.tui.json_output as json_output
    import aa_ma.tui.parser as parser

    assert json_output.discover_tasks is parser.discover_tasks
