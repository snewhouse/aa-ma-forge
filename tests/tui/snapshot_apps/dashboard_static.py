"""Snapshot fixture: AAMAApp seeded with deterministic static_tasks.

snap_compare runs this module and captures SVG of the resulting screen.
Test press=["enter"] drills into TaskDetailScreen for the first task.
"""

from __future__ import annotations

from aa_ma.tui.app import AAMAApp
from tests.tui._static_tasks import make_static_tasks

app = AAMAApp(initial_tasks=make_static_tasks())

if __name__ == "__main__":  # pragma: no cover  (manual sanity smoke)
    app.run()
