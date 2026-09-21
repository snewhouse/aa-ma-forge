"""The gate contract as tests — written before `aa_ma.gate` existed (M5 5.2).

Corpus: every fixture that broke bash across three §6.8 passes
(`tests/hooks/fixtures/gate-scans/`), the reference.md contract rows, and the
structural cases the contract names. Every expected value below is taken
from the reference "M5 enforcement contract", not invented here.
"""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest

from aa_ma import gate
from aa_ma.gate import (
    EXIT_AMBIGUOUS,
    EXIT_NO_ACTIVE,
    EXIT_NOT_FOUND,
    EXIT_OK,
    EXIT_UNREADABLE,
    GATE_JSON_SCHEMA,
    answer,
    main,
)

FIX = Path("tests/hooks/fixtures/gate-scans")
STYLES, ONE, TWO, NONE = (
    FIX / f"{n}-tasks.md" for n in ("styles", "one-active", "two-active", "no-active")
)
NBSP = "\u00a0"


def _write(tmp_path: Path, body: str, name: str = "t-tasks.md") -> Path:
    p = tmp_path / name
    p.write_bytes(body.encode("utf-8"))
    return p


# --- the shipped fixtures, exit codes 0/1/2/3 --------------------------------


def test_one_active_is_exit_0_with_the_exact_heading() -> None:
    a = answer(ONE)
    assert a.exit_code == EXIT_OK
    assert a.milestone is not None
    assert (
        a.milestone.heading == "Milestone 2: The one being gated"
    )  # Q1, verbatim for §7.1
    assert a.milestone.gate == "HARD"  # Q4
    assert (
        a.milestone.pending_steps == 0
    )  # Q3 — trailing `## Summary Counts` excluded (row 18)
    assert a.milestone.critical_path is None  # Q5 absent => valid, check skipped
    assert a.milestone.prototype_required is False  # Q6


def test_two_active_is_exit_3_naming_both() -> None:
    a = answer(TWO)
    assert a.exit_code == EXIT_AMBIGUOUS
    assert a.milestone is None
    joined = "\n".join(a.errors)
    assert "Milestone 2: Older milestone left ACTIVE" in joined
    assert "Milestone 4: The one actually being gated" in joined


def test_no_active_is_exit_1() -> None:
    a = answer(NONE)
    assert a.exit_code == EXIT_NO_ACTIVE
    assert a.milestone is None


def test_missing_file_is_exit_2() -> None:
    a = answer(Path("/nonexistent/x-tasks.md"))
    assert a.exit_code == EXIT_UNREADABLE
    assert any("missing" in e or "No such" in e for e in a.errors)


def test_styles_fixture_active_mode_is_ambiguous() -> None:
    """Seven ACTIVE milestones and a duplicate title: refuse, not pick one."""
    assert answer(STYLES).exit_code == EXIT_AMBIGUOUS


# --- Q7: by-number, on every heading style -----------------------------------


@pytest.mark.parametrize(
    ("number", "gate_", "pending", "critical_path", "prototype"),
    [
        ("1", "SOFT", 0, None, False),
        ("2", "HARD", 1, "data-xform", False),  # `## M2:`
        ("3", "SOFT", 1, None, True),  # `## Milestone M3:`
        ("4", "HARD", 2, "hook-modification", True),  # em-dash; 2 not 3 (row 18)
        ("5", "HARD", 1, "version-pipeline", False),  # bold field forms
        ("6", "SOFT", 1, None, False),  # ghost headings must not truncate
        ("7", "HARD", 0, None, False),  # `Gate: Hard` case-folded (row 11)
        ("8", "SOFT", 0, None, False),  # duplicate title, unique number
    ],
)
def test_by_number_reads_every_heading_style(
    number: str, gate_: str, pending: int, critical_path: str | None, prototype: bool
) -> None:
    a = answer(STYLES, number=number)
    assert a.exit_code == EXIT_OK, a.errors
    assert a.milestone is not None
    assert a.milestone.number == number
    assert a.milestone.gate == gate_
    assert a.milestone.pending_steps == pending
    assert a.milestone.critical_path == critical_path
    assert a.milestone.prototype_required is prototype


def test_by_number_not_found_is_exit_4() -> None:
    assert answer(STYLES, number="99").exit_code == EXIT_NOT_FOUND


def test_by_number_survives_2a_and_3_5(tmp_path: Path) -> None:
    p = _write(
        tmp_path,
        "## Milestone 2a: A\n- Status: COMPLETE\n- Audit-Profile: infra\n## Milestone 3.5: B\n- Status: COMPLETE\n- Audit-Profile: full\n",
    )
    assert answer(p, number="2a").milestone.audit_profile == "infra"
    assert answer(p, number="3.5").milestone.audit_profile == "full"


def test_by_number_duplicate_number_is_ambiguous(tmp_path: Path) -> None:
    p = _write(
        tmp_path,
        "## Milestone 1: A\n- Status: COMPLETE\n## Milestone 1: B\n- Status: COMPLETE\n",
    )
    assert answer(p, number="1").exit_code == EXIT_AMBIGUOUS


# --- contract rows the field reads decide, seen through the gate -------------


def test_titles_with_backslashes_round_trip_byte_exact(tmp_path: Path) -> None:
    """The `awk -v` escape-decoding false PASS, closed by construction."""
    for title in (
        r"Fix \t handling in parser",
        r"Windows C:\dev\path",
        r"Escape \\ pair",
        r"Regex \d digit",
    ):
        p = _write(tmp_path, f"## Milestone 1: {title}\n- Status: ACTIVE\n")
        a = answer(p)
        assert a.exit_code == EXIT_OK
        assert a.milestone.heading == f"Milestone 1: {title}"


def test_crlf_is_normalised_and_the_heading_carries_no_cr(tmp_path: Path) -> None:
    p = _write(
        tmp_path,
        "## Milestone 1: T\r\n- Status: ACTIVE\r\n- Gate: HARD\r\n### Sub-step 1.1: S\r\n- Status: PENDING\r\n",
    )
    a = answer(p)
    assert a.exit_code == EXIT_OK
    assert a.milestone.heading == "Milestone 1: T"
    assert a.milestone.gate == "HARD" and a.milestone.pending_steps == 1


@pytest.mark.parametrize(
    "line",
    [
        "* Status: ACTIVE",  # row 9
        f"-{NBSP}Status: ACTIVE",  # row 10
        "- Status: TYPO",
        "- Status:",
    ],
)
def test_unreadable_milestone_status_is_exit_2_quoting_the_line(
    tmp_path: Path, line: str
) -> None:
    a = answer(_write(tmp_path, f"## Milestone 1: T\n{line}\n"))
    assert a.exit_code == EXIT_UNREADABLE
    assert any(repr(line.strip()) in e for e in a.errors), a.errors


def test_absent_milestone_status_is_refused_even_when_a_step_has_one(
    tmp_path: Path,
) -> None:
    """Only the milestone's *own* fields (before its first `###`) count — a
    sub-step's Status must never stand in for the milestone's. Mutation-found:
    reading the whole block passed every other case because own fields come
    first in every fixture."""
    a = answer(
        _write(
            tmp_path,
            "## Milestone 1: T\n- Gate: SOFT\n### Sub-step 1.1: s\n- Status: COMPLETE\n",
        )
    )
    assert a.exit_code == EXIT_UNREADABLE
    assert any("no Status" in e for e in a.errors)


def test_annotated_and_bold_values_read_their_intent(tmp_path: Path) -> None:
    """Rows 6-8: the 24 real corpus lines a Python-backed gate must not misread."""
    p = _write(
        tmp_path,
        "## Milestone 1: T\n- Status: **ACTIVE**\n- Gate: hard\n"
        "### Sub-step 1.1: a\n- Status: COMPLETE (2026-05-09, commit abc1234)\n"
        "### Sub-step 1.2: b\n- Status: PENDING\n",
    )
    a = answer(p)
    assert a.exit_code == EXIT_OK
    assert a.milestone.gate == "HARD" and a.milestone.pending_steps == 1


def test_gate_typo_is_exit_2_never_soft(tmp_path: Path) -> None:
    a = answer(_write(tmp_path, "## Milestone 1: T\n- Status: ACTIVE\n- Gate: TYPO\n"))
    assert a.exit_code == EXIT_UNREADABLE  # row 12


def test_mode_typo_on_a_step_or_milestone_is_exit_2(tmp_path: Path) -> None:
    """Row 13: `Mode: TYPO` must never dispatch as AFK — the gate refuses the file."""
    for body in (
        "## Milestone 1: T\n- Status: ACTIVE\n- Mode: TYPO\n",
        "## Milestone 1: T\n- Status: ACTIVE\n### Sub-step 1.1: s\n- Status: PENDING\n- Mode: TYPO\n",
    ):
        assert answer(_write(tmp_path, body)).exit_code == EXIT_UNREADABLE


def test_file_level_rule_an_unreadable_sibling_refuses_the_clean_active_one(
    tmp_path: Path,
) -> None:
    """We cannot know the unreadable milestone was not the intended subject."""
    p = _write(
        tmp_path,
        "## Milestone 1: A\n- Status: ACTIVE\n## Milestone 2: B\n- Status: DONE\n",
    )
    a = answer(p)
    assert a.exit_code == EXIT_UNREADABLE
    assert any("Milestone 2: B" in e for e in a.errors)


def test_step_status_is_scoped_to_the_answered_milestone(tmp_path: Path) -> None:
    """A step in a *completed* milestone with no Status cannot change which
    milestone is active, so it does not refuse; the same gap in the ACTIVE
    milestone makes its PENDING count unknowable and does."""
    ok = _write(
        tmp_path,
        "## Milestone 1: A\n- Status: COMPLETE\n### Sub-step 1.1: s\n## Milestone 2: B\n- Status: ACTIVE\n### Sub-step 2.1: t\n- Status: COMPLETE\n",
        "ok-tasks.md",
    )
    assert answer(ok).exit_code == EXIT_OK
    bad = _write(
        tmp_path,
        "## Milestone 2: B\n- Status: ACTIVE\n### Sub-step 2.1: t\n",
        "bad-tasks.md",
    )
    assert answer(bad).exit_code == EXIT_UNREADABLE


def test_step_active_is_refused_because_steps_have_no_active(tmp_path: Path) -> None:
    p = _write(
        tmp_path,
        "## Milestone 1: T\n- Status: ACTIVE\n### Sub-step 1.1: s\n- Status: ACTIVE\n",
    )
    assert answer(p).exit_code == EXIT_UNREADABLE


def test_skipped_and_deferred_steps_are_readable_and_not_pending(
    tmp_path: Path,
) -> None:
    p = _write(
        tmp_path,
        "## Milestone 1: T\n- Status: ACTIVE\n### Sub-step 1.1: s\n- Status: SKIPPED — User skipped at HITL gate\n### Sub-step 1.2: d\n- Status: DEFERRED — later\n",
    )
    a = answer(p)
    assert a.exit_code == EXIT_OK and a.milestone.pending_steps == 0


# --- structure rows 15-17 ----------------------------------------------------


def test_unclosed_fence_is_exit_2(tmp_path: Path) -> None:
    """Row 15: measured to hide a PENDING sub-step — a false PASS."""
    p = _write(
        tmp_path,
        "## Milestone 1: T\n- Status: ACTIVE\n```python\n### Sub-step 1.1: hidden\n- Status: PENDING\n",
    )
    a = answer(p)
    assert a.exit_code == EXIT_UNREADABLE
    assert any("fence" in e for e in a.errors)


def test_bare_h2_closes_the_block_and_orphaned_steps_refuse(tmp_path: Path) -> None:
    """Row 16: a bare `##` closes the block. Steps after it belong to no
    milestone; a sub-step the gate cannot attribute is unreadable (exit 2),
    which is what turns 'closes block' from a false PASS into a refusal."""
    p = _write(
        tmp_path,
        "## Milestone 1: T\n- Status: ACTIVE\n##\n### Sub-step 1.1: orphan\n- Status: PENDING\n",
    )
    a = answer(p)
    assert a.exit_code == EXIT_UNREADABLE
    assert any("orphan" in e for e in a.errors)


def test_tab_separated_h2_parses(tmp_path: Path) -> None:
    """Row 17: `##<TAB>Milestone 2:` is a milestone heading."""
    p = _write(
        tmp_path,
        "## Milestone 1: A\n- Status: COMPLETE\n##\tMilestone 2: B\n- Status: ACTIVE\n",
    )
    a = answer(p)
    assert a.exit_code == EXIT_OK and a.milestone.heading == "Milestone 2: B"


def test_zero_milestone_headings_is_exit_2(tmp_path: Path) -> None:
    assert (
        answer(_write(tmp_path, "# Just a title\n\nno milestones here\n")).exit_code
        == EXIT_UNREADABLE
    )


def test_audit_profile_is_read_with_the_same_normalisation(tmp_path: Path) -> None:
    p = _write(
        tmp_path, "## Milestone 1: T\n- Status: ACTIVE\n- Audit-Profile: infra\n"
    )
    assert answer(p).milestone.audit_profile == "infra"
    p2 = _write(
        tmp_path,
        "## Milestone 1: T\n- Status: ACTIVE\n- Audit-Profile: bogus\n",
        "b-tasks.md",
    )
    assert answer(p2).exit_code == EXIT_UNREADABLE


# --- the live plan -----------------------------------------------------------


def test_this_plans_own_tasks_file_is_gateable() -> None:
    """Dogfood on the plan that built the gate. By number, not ACTIVE mode:
    the first version asserted M5 was ACTIVE and broke the day it completed
    — a self-invalidating test. Finds the plan in active/ or completed/."""
    name = "milestone-grammar-ssot"
    candidates = [
        Path(f".claude/dev/{where}/{name}/{name}-tasks.md")
        for where in ("active", "completed")
    ]
    path = next((c for c in candidates if c.is_file()), None)
    assert path is not None, "plan not found in active/ or completed/"
    a = answer(path, number="5")
    assert a.exit_code == EXIT_OK, a.errors
    assert a.milestone is not None
    assert a.milestone.heading.startswith("Milestone 5:")
    assert a.milestone.status in {"ACTIVE", "COMPLETE"}
    assert a.milestone.gate == "HARD"
    assert a.milestone.critical_path == "hook-modification"
    assert a.milestone.audit_profile == "infra"
    assert a.milestone.pending_steps == 0


# --- CLI ---------------------------------------------------------------------


def test_cli_json_validates_against_the_declared_schema(
    capsys: pytest.CaptureFixture[str],
) -> None:
    for argv, code in (
        ([str(ONE)], 0),
        ([str(TWO)], 3),
        ([str(NONE)], 1),
        (["/nonexistent"], 2),
        ([str(STYLES), "--milestone", "99"], 4),
        ([str(STYLES), "--milestone", "4"], 0),
    ):
        assert main(argv) == code, argv
        doc = json.loads(capsys.readouterr().out)
        jsonschema.validate(doc, GATE_JSON_SCHEMA)
        assert doc["exit_code"] == code


def test_cli_help_documents_every_exit_code(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc:
        main(["--help"])
    assert exc.value.code == 0
    out = capsys.readouterr().out
    for code in range(5):
        assert f"{code} " in out or f"{code}:" in out or f"{code}\t" in out, out


def test_console_script_is_declared() -> None:
    assert 'aa-ma-gate = "aa_ma.gate:main"' in Path("pyproject.toml").read_text()


def test_gate_module_exposes_no_second_grammar() -> None:
    """Behavioural no-second-parser guard lives in 5.3's parity test; this is
    the cheap structural half: gate.py imports its recognisers rather than
    compiling heading or field regexes of its own."""
    src = Path(gate.__file__).read_text()
    assert "re.compile" not in src and "re.match" not in src and "re.search" not in src


def test_kv_format_is_line_per_key_and_values_are_verbatim(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The shell callers read `sed -n 's/^heading=//p'`: everything after the
    first `=` must be the value byte-for-byte, `=` and backslashes included."""
    title = r"a=b \t C:\dev\path"
    p = _write(
        tmp_path,
        f"## Milestone 1: {title}\n- Status: ACTIVE\n- **Prototype-Required:** YES\n",
    )
    assert main([str(p), "--format", "kv"]) == 0
    out = capsys.readouterr().out
    lines = dict(line.split("=", 1) for line in out.splitlines())
    assert lines["heading"] == f"Milestone 1: {title}"
    assert lines["exit_code"] == "0" and lines["prototype_required"] == "YES"
    assert lines["critical_path"] == "" and lines["gate"] == "SOFT"
    assert main([str(TWO), "--format", "kv"]) == 3
    out = capsys.readouterr().out
    assert out.count("error=") == 2 and "heading=" not in out


# --- §5.3 Mode dispatch (M5 5.6): the HITL bypass ---------------------------


MODE_DOC = (
    "## Milestone 1: T\n- Status: ACTIVE\n- Mode: HITL\n"
    "### Sub-step 1.1: own mode\n- Status: PENDING\n- Mode: AFK\n"
    "### Sub-step 1.2: inherits\n- Status: PENDING\n"
    "## Milestone 2: U\n- Status: COMPLETE\n"
    "### Sub-step 2.1: defaults\n- Status: COMPLETE\n"
)


def test_step_mode_resolves_own_then_parent_then_hitl(tmp_path: Path) -> None:
    p = _write(tmp_path, MODE_DOC)
    own = answer(p, number="1", step="1.1")
    assert own.exit_code == EXIT_OK and own.step is not None
    assert (own.step.mode, own.step.mode_source) == ("AFK", "step")
    inherited = answer(p, number="1", step="1.2")
    assert (inherited.step.mode, inherited.step.mode_source) == ("HITL", "milestone")
    default = answer(p, number="2", step="2.1")
    assert (default.step.mode, default.step.mode_source) == ("HITL", "default")
    assert default.step.heading == "Sub-step 2.1: defaults"


def test_step_mode_typo_never_dispatches(tmp_path: Path) -> None:
    """Row 13, at the dispatch site: TYPO must halt quoting the text, not run as AFK."""
    p = _write(
        tmp_path,
        "## Milestone 1: T\n- Status: ACTIVE\n### Sub-step 1.1: s\n- Status: PENDING\n- Mode: TYPO\n",
    )
    a = answer(p, number="1", step="1.1")
    assert a.exit_code == EXIT_UNREADABLE and a.step is None
    assert any("TYPO" in e for e in a.errors)


def test_step_not_found_is_exit_4(tmp_path: Path) -> None:
    assert (
        answer(_write(tmp_path, MODE_DOC), number="1", step="1.9").exit_code
        == EXIT_NOT_FOUND
    )


def test_step_requires_milestone_number_at_the_api(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        answer(_write(tmp_path, MODE_DOC), step="1.1")


def test_step_kv_and_json_carry_the_step(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    p = _write(tmp_path, MODE_DOC)
    assert main([str(p), "--milestone", "1", "--step", "1.2", "--format", "kv"]) == 0
    out = capsys.readouterr().out
    assert "step_mode=HITL\n" in out and "step_mode_source=milestone\n" in out
    assert main([str(p), "--milestone", "1", "--step", "1.2"]) == 0
    doc = json.loads(capsys.readouterr().out)
    jsonschema.validate(doc, GATE_JSON_SCHEMA)
    assert doc["step"]["mode"] == "HITL"


# --- §6.8 review of M5 (2026-09-11): every false PASS found, as a test ------


def test_fence_closed_only_inside_an_html_comment_is_still_unterminated(
    tmp_path: Path,
) -> None:
    """code-reviewer C1: the unterminated check ran on raw text while stripping
    ran on comment-stripped text, so a ``` inside `<!-- -->` satisfied one and
    was removed before the other. One scanner now; measured false PASS before."""
    p = _write(
        tmp_path,
        "## Milestone 1: T\n- Status: ACTIVE\n```python\n<!--\n```\n-->\n### Sub-step 1.1: s\n- Status: PENDING\n",
    )
    a = answer(p)
    assert a.exit_code == EXIT_UNREADABLE and any("fence" in e for e in a.errors)


@pytest.mark.parametrize("sep", ["\x0c", "\x0b", "\x85", " ", "\x1c"])
def test_invisible_line_separators_are_refused_not_scanned(
    tmp_path: Path, sep: str
) -> None:
    """security CRITICAL / code-reviewer C2: `str.splitlines()` breaks on these,
    regexes and renderers do not, so `- Status: ACTIVE<FF>``` opened a fence
    the reader never saw and hid a PENDING sub-step. Refuse, quoting the line."""
    p = _write(
        tmp_path,
        f"## Milestone 1: T\n- Status: ACTIVE{sep}```\n### Sub-step 1.1: hidden\n- Status: PENDING\n```\n",
    )
    a = answer(p)
    assert a.exit_code == EXIT_UNREADABLE
    assert any("line 2" in e and "control character" in e for e in a.errors), a.errors


def test_duplicate_milestone_numbers_are_ambiguous_in_active_mode(
    tmp_path: Path,
) -> None:
    """security WARNING: `Milestone 1: Foo` and `Milestone 1: Foo bar` have
    distinct headings, but §7.1's `grep -F "GATE APPROVAL: Milestone 1: Foo"`
    is satisfied by the other milestone's approval line by prefix."""
    p = _write(
        tmp_path,
        "## Milestone 1: Foo bar\n- Status: COMPLETE\n## Milestone 1: Foo\n- Status: ACTIVE\n",
    )
    a = answer(p)
    assert a.exit_code == EXIT_AMBIGUOUS and any("number '1'" in e for e in a.errors)


def test_duplicate_step_numbers_are_ambiguous(tmp_path: Path) -> None:
    p = _write(
        tmp_path,
        "## Milestone 1: T\n- Status: ACTIVE\n### Sub-step 1.1: a\n- Status: COMPLETE\n- Mode: AFK\n### Sub-step 1.1: b\n- Status: COMPLETE\n- Mode: HITL\n",
    )
    a = answer(p, number="1", step="1.1")
    assert a.exit_code == EXIT_AMBIGUOUS and a.step is None


def test_non_utf8_and_oversized_files_are_exit_2_with_an_envelope(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    bad = tmp_path / "bin-tasks.md"
    bad.write_bytes(b"\xff\xfe## Milestone 1: T\n")
    assert answer(bad).exit_code == EXIT_UNREADABLE
    big = tmp_path / "big-tasks.md"
    big.write_bytes(b"## Milestone 1: T\n- Status: ACTIVE\n" + b"x" * (1 << 20))
    assert answer(big).exit_code == EXIT_UNREADABLE
    assert main([str(bad), "--format", "kv"]) == 2
    assert capsys.readouterr().out.startswith("exit_code=2\n")


def test_kv_values_never_contain_a_raw_newline(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """code-reviewer W3: error strings embed the path; a path with a newline
    forged `exit_code=0` / `heading=` lines."""
    weird = tmp_path / "x\nexit_code=0\nheading=Injected"
    assert main([str(weird), "--format", "kv"]) == 2
    out = capsys.readouterr().out
    lines = out.splitlines()
    assert sum(ln.startswith("exit_code=") for ln in lines) == 1
    assert not any(ln.startswith("heading=") for ln in lines)
    assert "\\n" in out  # escaped, not dropped


def test_step_without_milestone_is_a_usage_error(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as exc:
        main([str(ONE), "--step", "1.1"])
    assert exc.value.code == 2


# --- sub-step Prototype-Required rolls up to the selected milestone (M3, AD-001)


ROLLUP = FIX / "prototype-rollup-tasks.md"


def test_substep_prototype_required_rolls_up_to_the_milestone() -> None:
    a = answer(ROLLUP, number="1")
    assert a.exit_code == EXIT_OK, a.errors
    assert a.milestone.prototype_required is True  # M1 has no own field; 1.2 says YES


def test_rollup_no_flags_anywhere_is_no() -> None:
    a = answer(ROLLUP, number="2")
    assert a.exit_code == EXIT_OK, a.errors
    assert a.milestone.prototype_required is False


def test_invalid_substep_prototype_token_is_exit_2() -> None:
    a = answer(ROLLUP, number="3")
    assert a.exit_code == EXIT_UNREADABLE
    assert any("Prototype-Required" in e and "maybe" in e for e in a.errors), a.errors


def test_empty_substep_prototype_slot_exits_2() -> None:
    # `- **Prototype-Required:**` is what tasks-template.md emitted; a blank
    # value is a refusal, not "NO" — the template fix in M3 exists for this.
    a = answer(ROLLUP, number="4")
    assert a.exit_code == EXIT_UNREADABLE
    assert any("empty value" in e for e in a.errors), a.errors
