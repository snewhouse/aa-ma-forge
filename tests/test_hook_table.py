"""One hook table (code-conventions-impact M3 §6.6): install.sh registers, uninstall.sh
deregisters and codemem's plugin-surface extractor reads the same AA_MA_HOOKS rows."""

from __future__ import annotations

from pathlib import Path

from codemem.draw.surface_allowlist import HOOK_TABLE

ROOT = Path(__file__).resolve().parents[1]
LIB = "scripts/lib/aa-ma-install-lib.sh"


def test_codemem_reads_the_shared_table() -> None:
    assert HOOK_TABLE == LIB
    assert "\nAA_MA_HOOKS=(\n" in (ROOT / LIB).read_text(encoding="utf-8")


def test_install_and_uninstall_source_it_and_keep_no_copy() -> None:
    for script in ("scripts/install.sh", "scripts/uninstall.sh"):
        text = (ROOT / script).read_text(encoding="utf-8")
        assert '. "${SCRIPT_DIR}/lib/aa-ma-install-lib.sh"' in text, script
        assert "AA_MA_HOOKS=(" not in text, script
