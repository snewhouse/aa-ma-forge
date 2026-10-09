"""Every `../` markdown link in a shipped skill resolves (code-conventions-impact M3 §6.8).

Moving a file one directory deeper (commands/x.md -> skills/x/SKILL.md) silently breaks
its `../` links; the plugin-surface extractor does not read markdown links. Links that
stay inside the skill (`REFERENCE.md`, `./src/…`) are often illustrative — templates and
examples of output a skill writes elsewhere — so only links that climb out are checked.
"""

from __future__ import annotations

import re

import pytest

from ._helpers import SKILLS_DIR

LINK = re.compile(r"\]\(([^)#\s]+)(?:#[^)\s]*)?\)")
# *TEMPLATE*.md files hold the text a skill writes into another repo; their links are
# relative to where that output lands (e.g. .claude/onboarding/), not to the template.
FILES = sorted(p for p in SKILLS_DIR.rglob("*.md") if "TEMPLATE" not in p.name)


@pytest.mark.parametrize(
    "md", FILES, ids=[str(p.relative_to(SKILLS_DIR)) for p in FILES]
)
def test_relative_links_resolve(md) -> None:
    text = md.read_text(encoding="utf-8")
    dead = [
        h
        for h in LINK.findall(text)
        if h.startswith("../") and not (md.parent / h).exists()
    ]
    assert dead == []
