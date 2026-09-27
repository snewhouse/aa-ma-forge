"""Hardcoded asset counts in the docs equal the shipped surface (diagram-generation M14, AC4).

Replaces the generic doc-drift Tier 6 scan for this repo (Ste, 2026-09-27): with a
`doc-counts.sh` it flags ~130 lines of frozen history; without one it silently skips.
This reads only the living files CLAUDE.md names plus codemem's own docs, and compares
every count claim with the filesystem or the MCP registry.
"""

from __future__ import annotations

import importlib.util
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
CC = ROOT / "claude-code"
PLUGIN_DOCS = ["README.md", "SECURITY.md", "docs/spec/claude-code-foundations.md", "docs/spec/aa-ma-quick-reference.md"]
CODEMEM_DOCS = ["SECURITY.md", "claude-code/codemem/README.md", "packages/codemem-mcp/README.md",
                "packages/codemem-mcp/pyproject.toml", "docs/codemem/install-zero-config.md"]


def _mcp_tool_count() -> int:
    spec = importlib.util.spec_from_file_location("srv", CC / "codemem/mcp/server.py")
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return len(mod.CANONICAL_TOOL_NAMES)


TRUTH = {
    "commands": len(list((CC / "commands").glob("*.md"))),
    "skills": len(list((CC / "skills").glob("*/SKILL.md"))),
    "agents": len(list((CC / "agents").glob("*.md"))),
    "rules": len(list((CC / "rules").glob("*.md"))),
    "hooks": len(list((CC / "hooks").glob("*.sh"))),  # event hooks; lib/ helpers are not counted
}
PLUGIN_PATTERNS = {
    "commands": [r"\b(\d+) (?:slash )?command(?: file)?s\b", r"\bCommands \((\d+)\)"],
    "skills": [r"\b(\d+) skills?(?: directories)?\b", r"\bSkills \((\d+)\)"],
    "agents": [r"\b(\d+) agent(?: file)?s\b", r"\bAgents \((\d+)\)"],
    "rules": [r"\b(\d+) (?:operational )?rule(?:s| files|sets)\b", r"\bRules \((\d+)\)"],
    "hooks": [r"\b(\d+) hooks\b", r"\bHooks \((\d+)\)"],
}
MCP_PATTERNS = [r"\b(\d+) (?:codemem )?MCP tools?\b", r"\bThe (\d+) (?:MCP )?tools\b"]


def _claims(files: list[str], patterns: list[str]) -> list[tuple[str, int, int]]:
    out = []
    for rel in files:
        for n, line in enumerate((ROOT / rel).read_text(encoding="utf-8").splitlines(), 1):
            if "MemPalace" in line:  # an external project's tool count, not ours
                continue
            out += [(rel, n, int(m)) for p in patterns for m in re.findall(p, line)]
    return out


@pytest.mark.parametrize("kind", sorted(PLUGIN_PATTERNS))
def test_plugin_asset_counts_match_the_tree(kind: str) -> None:
    claims = _claims(PLUGIN_DOCS, PLUGIN_PATTERNS[kind])
    assert claims, f"no {kind} count found — the guard would pass vacuously"
    assert [c for c in claims if c[2] != TRUTH[kind]] == [], f"truth: {TRUTH[kind]} {kind}"


def test_mcp_tool_counts_match_the_registry() -> None:
    claims = _claims(CODEMEM_DOCS, MCP_PATTERNS)
    assert len(claims) >= 5, claims
    want = _mcp_tool_count()
    assert [c for c in claims if c[2] != want] == [], f"truth: {want} MCP tools"
