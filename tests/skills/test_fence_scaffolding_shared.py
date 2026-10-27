"""Fences 3 and 4 share their scaffolding; aa_ma_gate and aa_ma_impact share one launcher.

code-conventions-impact M11 §6.6 (reuse W): the two fence scripts carried ~35 identical lines
(slug check, symlink guard, library load, milestone read) and the two launchers were
line-for-line copies. A copy drifts; this pins the one shared source.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "claude-code/skills/execute-aa-ma-milestone/scripts"
LIB = ROOT / "claude-code/hooks/lib/aa-ma-parse.sh"


def test_both_fence_scripts_source_fence_common() -> None:
    for name in ("tests-verified.sh", "impact-verified.sh"):
        text = (SCRIPTS / name).read_text(encoding="utf-8")
        assert "fence-common.sh" in text, name
        assert "blocked() {" not in text, f"{name} redefines blocked()"


def test_gate_and_impact_launchers_are_wrappers_of_one_function() -> None:
    text = LIB.read_text(encoding="utf-8")
    for fn in ("aa_ma_gate", "aa_ma_impact"):
        body = re.search(rf"^{fn}\(\) \{{\n(.*?)^\}}", text, re.M | re.S)
        assert body, fn
        assert "_aa_ma_uv_kv_cli" in body.group(1), fn
        assert "uv run" not in body.group(1), f"{fn} still runs uv itself"
