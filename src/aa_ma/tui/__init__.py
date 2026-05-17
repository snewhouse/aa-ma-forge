"""aa-ma-tui — terminal UI for tracking AA-MA tasks.

Created in aa-ma-tui-tracker M0 T0.4 (2026-05-17).

This sub-package exposes:
    - __version__ : re-exported from the parent aa_ma package so that
      `aa-ma-tui --version` and `aa-ma --version` always agree.

Scaffolding only at M0. Real modules land in:
    - M1: model.py, parser.py    (parser foundation)
    - M2: snapshot.py, json_output.py  (snapshot modes)
    - M3: app.py, screens/, widgets/, watcher.py, app.tcss  (interactive TUI)
"""

from aa_ma import __version__

__all__ = ["__version__"]
