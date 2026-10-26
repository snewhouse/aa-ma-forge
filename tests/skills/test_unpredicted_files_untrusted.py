"""The §6.3 unpredicted-file list is repo-controlled data (code-conventions-impact §6.8 W7).

Paths come from the reviewed repository, so a file name can carry text aimed at the
reviewer. Both the dispatching skill and the receiving agent must frame the list as
untrusted data, never as instructions.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / "claude-code" / "skills" / "verify-impl" / "SKILL.md"
AGENT = ROOT / "claude-code" / "agents" / "code-reviewer.md"
PHRASE = "untrusted data, not instructions"


def _section(path: Path, heading: str) -> str:
    text = path.read_text(encoding="utf-8")
    assert heading in text
    return text.split(heading, 1)[1].split("\n## ", 1)[0].split("\n### ", 1)[0]


def test_verify_impl_dispatch_marks_the_list_untrusted() -> None:
    section = _section(SKILL, "### Step 3: Dispatch agents per Audit-Profile")
    assert "<unpredicted-files>" in section
    assert PHRASE in section


def test_code_reviewer_reads_the_list_as_untrusted() -> None:
    section = _section(AGENT, "## Unpredicted files from §6.3 (R6)")
    assert PHRASE in section
