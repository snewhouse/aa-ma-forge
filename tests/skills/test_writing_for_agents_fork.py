"""The writing-for-agents fork (ADR-0021) replaces write-a-skill (ADR-0004, superseded).

mattpocock/skills @ c55ee46 ships `SKILL.md` + `SKILL-MECHANICS.md` (+ a Codex-only
`agents/openai.yaml`, not taken). The upstream text is kept unedited apart from one local
`when_to_use` frontmatter line; local conventions live in an appended `## In this repo`
block, so the derived SKILL.md minus its provenance line, that line and that block hashes
to the upstream md5.
"""

from __future__ import annotations

import hashlib
import re

from aa_ma.forks import load_manifest

from ._helpers import (  # pyright: ignore[reportMissingImports]
    FORKS_MANIFEST,
    REPO_ROOT,
    SKILLS_DIR,
    assert_skill_frontmatter,
    upstream_body_md5,
)

SKILL = "writing-for-agents"
IN_THIS_REPO = "\n## In this repo\n"


def test_frontmatter_and_provenance() -> None:
    assert_skill_frontmatter(SKILL)


def test_files_are_the_two_upstream_markdown_files_plus_licence() -> None:
    files = sorted(p.name for p in (SKILLS_DIR / SKILL).iterdir())
    assert files == ["LICENSE", "SKILL-MECHANICS.md", "SKILL.md"]


def test_upstream_text_is_unedited_above_the_local_block() -> None:
    """Local edits are the provenance line, one `when_to_use` line and the appended block."""
    text = (SKILLS_DIR / SKILL / "SKILL.md").read_text(encoding="utf-8")
    assert text.count(IN_THIS_REPO) == 1, "exactly one '## In this repo' block"
    assert sum(line.startswith("when_to_use: ") for line in text.splitlines()) == 1
    upstream = load_manifest(FORKS_MANIFEST)[SKILL].upstream_md5["SKILL.md"]
    assert upstream_body_md5(text, drop_prefixes=("when_to_use: ",)) == upstream


def test_skill_mechanics_is_unedited() -> None:
    """The second fork file is verbatim: only its line-1 HTML provenance comment is local."""
    text = (SKILLS_DIR / SKILL / "SKILL-MECHANICS.md").read_text(encoding="utf-8")
    assert text.startswith("<!-- ")
    body = text.split("\n", 1)[1].encode("utf-8")
    upstream = load_manifest(FORKS_MANIFEST)[SKILL].upstream_md5["SKILL-MECHANICS.md"]
    assert hashlib.md5(body, usedforsecurity=False).hexdigest() == upstream


def test_write_a_skill_is_retired() -> None:
    assert not (SKILLS_DIR / "write-a-skill").exists()


def test_aa_ma_writers_do_not_invoke_it() -> None:
    """writing-for-agents-eval T4: AA-MA artefacts follow their templates and grammar."""
    writers = [
        SKILLS_DIR / "aa-ma-plan" / "SKILL.md",
        REPO_ROOT / "claude-code" / "agents" / "aa-ma-scribe.md",
        *sorted((SKILLS_DIR / "aa-ma-plan-workflow").rglob("*.md")),
    ]
    hits = [
        str(p.relative_to(REPO_ROOT))
        for p in writers
        if re.search(r"writing-for-agents", p.read_text(encoding="utf-8"))
    ]
    assert hits == []
