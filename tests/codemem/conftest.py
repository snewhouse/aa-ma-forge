"""Codemem test-suite conftest — adds scripts/ to sys.path for harness imports.

Scoped to the tests/codemem/ tree. The bench harness lives in scripts/ per AD-005
(inline parser, no separate package). This conftest makes it importable during
pytest collection without converting scripts/ into a formal Python package.
"""

from __future__ import annotations

import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_SCRIPTS_DIR = _PROJECT_ROOT / "scripts"

if _SCRIPTS_DIR.is_dir() and str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))
