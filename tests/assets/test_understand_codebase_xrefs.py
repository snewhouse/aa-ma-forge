"""Cross-reference integrity for the vendored ``understand-codebase`` skill.

Pins the dependency boundary:
  - the **in-repo** assets the skill composes (``agent-teams``, ``impact-analysis``,
    ``system-mapping``, ``/aa-ma-plan``, ``code-reviewer``) MUST exist;
  - the skill's own ``references/`` + ``templates/`` relative links MUST resolve within
    the skill directory (so a move/refactor that breaks them fails loudly).

The skill *also* names tools aa-ma-forge does **not** ship (``/index``, ``gsd-map-codebase``,
``/codebase-deep-dive``, ``code-intelligence``, ``doc-drift-detection``,
``improve-codebase-architecture``) — those are documented **soft-deps**; the skill degrades
gracefully when they're absent (see docs/adr/0006-understand-codebase-adoption.md), so they
are intentionally NOT asserted here.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SKILL_DIR = REPO_ROOT / "claude-code" / "skills" / "understand-codebase"


def test_in_repo_composed_assets_exist() -> None:
    """Every aa-ma-forge asset the understand-codebase skill composes is present in this repo."""
    must_exist = [
        REPO_ROOT / "claude-code" / "skills" / "agent-teams" / "SKILL.md",
        REPO_ROOT / "claude-code" / "skills" / "impact-analysis" / "SKILL.md",
        REPO_ROOT / "claude-code" / "skills" / "system-mapping" / "SKILL.md",
        REPO_ROOT / "claude-code" / "commands" / "aa-ma-plan.md",
        REPO_ROOT / "claude-code" / "agents" / "code-reviewer.md",
    ]
    for p in must_exist:
        assert p.exists(), f"understand-codebase composes {p.relative_to(REPO_ROOT)} but it is missing from this repo"


def test_skill_internal_relative_links_resolve() -> None:
    """Every ``references/<X>`` / ``templates/<X>`` path in SKILL.md resolves within the skill dir."""
    text = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
    rels = set(re.findall(r"\b((?:references|templates)/[A-Za-z0-9_.-]+\.[A-Za-z0-9]+)\b", text))
    assert rels, "expected SKILL.md to reference its companion files under references/ and templates/"
    for rel in sorted(rels):
        assert (SKILL_DIR / rel).exists(), f"SKILL.md links {rel!r} but it does not exist in the skill directory"
