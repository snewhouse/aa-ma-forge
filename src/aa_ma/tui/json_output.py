"""JSON output mode for aa-ma-tui.

Created in aa-ma-tui-tracker M2 T2.4 (2026-05-18).

Emits a stable JSON envelope:

    {
      "schema_version": 1,
      "tasks": [<Task.model_dump(mode='json') for each task>]
    }

The `schema_version` is bumped via CHANGELOG breaking-change (per M2
plan risk #2). Consumers should pin a major version and reject unknown
ones rather than parse fuzzy.

L-052 dual-formatter rule: this module imports `discover_tasks` from
`aa_ma.tui.parser` so all 4 CLI modes (board/tree/summary/json) share
the SAME function object. Verified by
`test_json_output_reuses_parser_discover_tasks`.
"""

from __future__ import annotations

import json

from aa_ma.tui.model import SCHEMA_VERSION, Task

# Re-export for L-052 dual-formatter rule.
from aa_ma.tui.parser import discover_tasks  # noqa: F401


def dump(tasks: list[Task]) -> str:
    """Serialise tasks to a JSON string.

    Uses Pydantic's `model_dump(mode='json')` so Path → str, datetime →
    ISO-8601, enums → their string values. Output is pretty-printed
    (`indent=2`) for human-friendly snapshots; consumers should parse
    via `json.loads`, not regex.
    """
    envelope = {
        "schema_version": SCHEMA_VERSION,
        "tasks": [task.model_dump(mode="json") for task in tasks],
    }
    return json.dumps(envelope, indent=2, sort_keys=True)
