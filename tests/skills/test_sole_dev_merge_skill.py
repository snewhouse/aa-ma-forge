"""Shape of /sole-dev-merge's SKILL.md once it calls sdm.sh (sole-dev-merge-simplify 2.1).

The skill is prose that runs `sdm.sh check|ship|finish` as separate Bash calls; the code and
its exit table live in the script (`sdm.sh help`), so SKILL.md must not grow bash blocks or
copy the table back (L-062: copies drift).
"""

from __future__ import annotations

import re

from ._helpers import SKILLS_DIR, split_frontmatter

SKILL = SKILLS_DIR / "sole-dev-merge" / "SKILL.md"
MAX_LINES = 150  # plan M2 budget; the 500-line hard limit is tests/test_prompt_size.py
MAX_FENCE_LINES = 3  # one sdm.sh call per fence, never a stage block


def _text() -> str:
    return SKILL.read_text(encoding="utf-8")


def _fenced_blocks(text: str) -> list[list[str]]:
    blocks: list[list[str]] = []
    current: list[str] | None = None
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            if current is None:
                current = []
            else:
                blocks.append(current)
                current = None
        elif current is not None:
            current.append(line)
    assert current is None, "unclosed fence"
    return blocks


def test_at_most_150_lines() -> None:
    assert len(_text().splitlines()) <= MAX_LINES


def test_runs_each_subcommand() -> None:
    text = _text()
    for sub in ("check", "ship", "finish"):
        assert re.search(rf"sdm\.sh {sub}\b", text), sub


def test_no_fenced_block_longer_than_3_lines() -> None:
    long_blocks = [b for b in _fenced_blocks(_text()) if len(b) > MAX_FENCE_LINES]
    assert not long_blocks, long_blocks[0][:5]


def test_model_may_not_invoke_it() -> None:
    assert split_frontmatter(_text())[1].get("disable-model-invocation") is True


def test_github_only() -> None:
    assert not re.search(r"glab|gitlab", _text(), re.IGNORECASE)


def test_points_at_sdm_help_instead_of_copying_the_exit_table() -> None:
    text = _text()
    assert "sdm.sh help" in text
    rows = re.findall(r"^(?:STATUS|ABORT): .* \| ", text, re.MULTILINE)
    assert not rows, rows[:3]


def test_says_which_calls_push_and_merge() -> None:
    """sdm.sh hides git push and gh pr merge from the permission prompt (plan §3)."""
    text = _text()
    assert re.search(r"`?ship`?[^\n]*\bpush", text)
    assert re.search(r"`?finish`?[^\n]*\bmerge", text)
