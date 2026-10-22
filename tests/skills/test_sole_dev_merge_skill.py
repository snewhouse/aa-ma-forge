"""Shape of /sole-dev-merge's SKILL.md once it calls sdm.sh (sole-dev-merge-simplify 2.1).

The skill is prose that runs `sdm.sh check|ship|finish` as separate Bash calls; the code and
its exit table live in the script (`sdm.sh help`), so SKILL.md must not grow bash blocks or
copy the table back (L-062: copies drift).
"""

from __future__ import annotations

import re
import subprocess

from ._helpers import SKILLS_DIR, split_frontmatter

SKILL = SKILLS_DIR / "sole-dev-merge" / "SKILL.md"
SDM = SKILLS_DIR / "sole-dev-merge" / "scripts" / "sdm.sh"
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


def test_within_line_budget() -> None:
    assert len(_text().splitlines()) <= MAX_LINES


def test_runs_each_subcommand() -> None:
    text = _text()
    for sub in ("check", "ship", "finish"):
        assert re.search(rf"sdm\.sh {sub}\b", text), sub


def test_no_long_fenced_block() -> None:
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


# --- SKILL.md restates sdm.sh's output names; these tie the copies to the script (L-062) ---


def _sdm_help() -> str:
    return subprocess.run(
        ["bash", str(SDM), "help"], capture_output=True, text=True, check=True
    ).stdout


def _statuses(text: str) -> set[str]:
    return set(re.findall(r"STATUS: ([A-Z_]+)", text))


def test_status_names_match_sdm_help() -> None:
    """Every STATUS the script can print has a SKILL.md action, and SKILL.md names no other."""
    assert _statuses(_text()) == _statuses(_sdm_help())


def test_pr_body_reasons_match_sdm() -> None:
    sdm_reasons = set(
        re.findall(r'reason="?([a-z]+(?:-[a-z]+)+)', SDM.read_text("utf-8"))
    )
    rows = [ln for ln in _text().splitlines() if "PR_BODY_NOT_UPDATED" in ln]
    skill_reasons = {
        m
        for ln in rows
        for tok in re.findall(r"`([^`]+)`", ln)
        for m in re.findall(r"(?:^|reason=)([a-z]+(?:-[a-z]+)+)$", tok)
    }
    assert sdm_reasons and skill_reasons == sdm_reasons


def test_quoted_output_lines_exist_in_sdm() -> None:
    """A quoted result/ABORT line's literal prefix (up to its first placeholder) is in sdm.sh."""
    source = SDM.read_text("utf-8")
    quoted = re.findall(
        r"`((?:check OK|ABORT: |PR_NUM=|PR_URL=|CI_STATE=)[^`]*)`", _text()
    )
    assert quoted
    for q in quoted:
        prefix = re.split(r"<|…", q.removeprefix("ABORT: "), maxsplit=1)[0]
        assert prefix in source, q


def test_restates_no_script_default() -> None:
    """Defaults live in sdm.sh only; SKILL.md names the variables, never their values."""
    for var in re.findall(r"`(CI_[A-Z_]+)`", _text()):
        assert var in SDM.read_text("utf-8"), var
    assert not re.search(r"`CI_[A-Z_]+` \(\d", _text())


def test_notes_never_quote_a_secret() -> None:
    """The notes become the public PR body (security review, M2 §6.8)."""
    assert re.search(
        r"never quote[^\n]*(secret|token|credential)", _text(), re.IGNORECASE
    )


def test_bans_force_push() -> None:
    assert re.search(r"never force-push", _text(), re.IGNORECASE)
