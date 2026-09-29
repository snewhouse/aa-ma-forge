"""assess-codebase RATING.md names only metric keys measure really emits (M3 §6.8 CR-4).

Checked against a live measure() of the fixture target, not a grep of measure.py: keys are
built at runtime (``f"layers.{k}"``, ``COMPLEXITY_OVER``)."""

from __future__ import annotations

import json
import re
from pathlib import Path

from aa_ma.analysis.measure import measure

from .conftest import git

ROOT = Path(__file__).resolve().parents[2]
RATING = ROOT / "claude-code/skills/assess-codebase/references/RATING.md"


def test_every_metric_key_rating_md_names_is_emitted(target: Path, tools: Path) -> None:
    for n in range(3):  # co-change pairs are read for hot spots: files with functions, changed together
        (target / "a.py").write_text(f"def a():\n    return {n}\n")
        (target / "b.py").write_text(f"def b():\n    return {n}\n")
        git(target, "add", "a.py", "b.py")
        git(target, "commit", "-qm", f"pair {n}")
    keys = json.loads((measure(target, "standard") / "measure.json").read_text())["metrics"]
    named = [t for line in RATING.read_text(encoding="utf-8").splitlines() if line.startswith("Inputs:")
             for t in re.findall(r"`([^`]+)`", line)]  # fmt: skip
    assert len(named) >= 15
    for token in named:
        prefix = token.split("<", 1)[0]
        assert (token in keys) if prefix == token else any(k.startswith(prefix) for k in keys), token
