"""Tests for scripts/check_conventions.py — the touched-lines extractor (ADR-0018).

Each test builds a throwaway git repo, so the extractor is exercised against real
`git diff` output rather than a hand-written patch.
"""

from __future__ import annotations

import importlib.util
import os
import subprocess
from pathlib import Path

import pytest
import yaml

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "check_conventions.py"
_spec = importlib.util.spec_from_file_location("check_conventions", SCRIPT)
assert _spec is not None and _spec.loader is not None
cc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cc)

# A five-line file, so a rename with one changed line stays above git's 50% similarity cut.
FIVE = "".join(f"line {n}\n" for n in range(1, 6))


def git(repo: Path, *args: str) -> str:
    env = {
        **os.environ,
        "GIT_AUTHOR_NAME": "t",
        "GIT_AUTHOR_EMAIL": "t@example.invalid",
        "GIT_COMMITTER_NAME": "t",
        "GIT_COMMITTER_EMAIL": "t@example.invalid",
    }
    return subprocess.run(
        ["git", *args], cwd=repo, env=env, check=True, capture_output=True, text=True
    ).stdout


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    git(tmp_path, "init", "-q", "-b", "main")
    (tmp_path / "mod.py").write_text("a\nb\nc\n")
    (tmp_path / "old.py").write_text(FIVE)
    (tmp_path / "gone.py").write_text("x\n")
    git(tmp_path, "add", "-A")
    git(tmp_path, "commit", "-q", "-m", "base")
    return tmp_path


def make_change(repo: Path) -> None:
    """Modify, add, rename-with-edit and delete — one of each."""
    (repo / "mod.py").write_text("a\nB\nc\nd\n")
    (repo / "new.py").write_text("one\ntwo\n")
    git(repo, "mv", "old.py", "renamed.py")
    (repo / "renamed.py").write_text(FIVE.replace("line 3", "LINE 3"))
    (repo / "gone.py").unlink()
    git(repo, "add", "-A")


EXPECTED = {
    "mod.py": {2: "B", 4: "d"},
    "new.py": {1: "one", 2: "two"},
    "renamed.py": {3: "LINE 3"},
}


def test_staged_mode_returns_only_added_lines(repo: Path) -> None:
    make_change(repo)
    assert cc.added_lines(cc.resolve_range(None, None, cwd=repo), cwd=repo) == EXPECTED


def test_ref_mode_matches_staged_mode(repo: Path) -> None:
    make_change(repo)
    staged = cc.added_lines(cc.resolve_range(None, None, cwd=repo), cwd=repo)
    git(repo, "commit", "-q", "-m", "change")
    ranged = cc.added_lines(cc.resolve_range("HEAD~1", "HEAD", cwd=repo), cwd=repo)
    assert ranged == staged == EXPECTED


def test_file_arguments_filter_the_diff(repo: Path) -> None:
    make_change(repo)
    got = cc.added_lines(
        cc.resolve_range(None, None, cwd=repo), files=["new.py"], cwd=repo
    )
    assert got == {"new.py": EXPECTED["new.py"]}


def test_file_arguments_are_normalised(repo: Path) -> None:
    make_change(repo)
    got = cc.added_lines(
        cc.resolve_range(None, None, cwd=repo), files=["./new.py"], cwd=repo
    )
    assert got == {"new.py": EXPECTED["new.py"]}


def test_run_from_subdirectory_sees_the_whole_change(repo: Path) -> None:
    # A manual run from a subdirectory must not silently check nothing.
    (repo / "sub").mkdir()
    (repo / "sub" / "s.py").write_text("x\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "sub")
    (repo / "sub" / "s.py").write_text("x\ny\n")
    git(repo, "add", "-A")
    sub = repo / "sub"
    assert cc.added_lines(cc.resolve_range(None, None, cwd=sub), cwd=sub) == {
        "sub/s.py": {2: "y"}
    }


def test_textconv_driver_is_ignored(repo: Path) -> None:
    # A local textconv driver must neither shift line numbers nor run.
    conv = repo / "conv.sh"
    conv.write_text('#!/bin/sh\necho HDR\ncat "$1"\n')
    conv.chmod(0o755)
    git(repo, "config", "diff.hdr.textconv", str(conv))
    (repo / ".git" / "info" / "attributes").write_text("*.py diff=hdr\n")
    (repo / "mod.py").write_text("a\nB\nc\n")
    git(repo, "add", "mod.py")
    got = cc.added_lines(cc.resolve_range(None, None, cwd=repo), cwd=repo)
    assert got == {"mod.py": {2: "B"}}


def test_three_dot_diff_ignores_base_branch_progress(repo: Path) -> None:
    git(repo, "checkout", "-q", "-b", "feature")
    (repo / "new.py").write_text("feature\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "feature")
    git(repo, "checkout", "-q", "main")
    (repo / "mod.py").write_text("a\nb\nc\nmain-only\n")
    git(repo, "commit", "-q", "-am", "main moves on")
    got = cc.added_lines(cc.resolve_range("main", "feature", cwd=repo), cwd=repo)
    assert got == {"new.py": {1: "feature"}}


def test_added_line_that_looks_like_a_header(repo: Path) -> None:
    (repo / "mod.py").write_text("a\n++ not a header\nc\n")
    git(repo, "add", "-A")
    got = cc.added_lines(cc.resolve_range(None, None, cwd=repo), cwd=repo)
    assert got == {"mod.py": {2: "++ not a header"}}


def run_cli(
    repo: Path, *args: str, env: dict | None = None
) -> subprocess.CompletedProcess:
    clean = {k: v for k, v in os.environ.items() if not k.startswith("PRE_COMMIT_")}
    return subprocess.run(
        ["python3", str(SCRIPT), *args],
        cwd=repo,
        env={**clean, **(env or {})},
        capture_output=True,
        text=True,
        check=False,
    )


def test_cli_clean_reports_check_count(repo: Path) -> None:
    make_change(repo)
    proc = run_cli(repo)
    assert proc.returncode == 0, proc.stderr
    assert f"check_conventions: {len(cc.CHECKS)} checks enabled" in proc.stderr
    assert {c.__name__ for c in cc.CHECKS} == {"check_why", "check_todo"}
    assert proc.stdout == ""


def test_cli_no_diff_source_exits_2(repo: Path) -> None:
    proc = run_cli(repo)
    assert proc.returncode == 2
    assert "no diff source" in proc.stderr


@pytest.mark.parametrize("bad", ["no-such-ref", "--output={sink}", "HEAD:mod.py"])
def test_cli_rejects_unverifiable_refs(repo: Path, tmp_path: Path, bad: str) -> None:
    sink = tmp_path / "pwned"
    proc = run_cli(repo, "--from-ref", bad.format(sink=sink), "--to-ref", "HEAD")
    assert proc.returncode == 2
    assert not sink.exists()


def test_cli_one_ref_alone_is_usage_error(repo: Path) -> None:
    assert run_cli(repo, "--from-ref", "HEAD").returncode == 2


def test_cli_env_refs_beat_staged_mode(repo: Path) -> None:
    # Nothing staged: only the env refs can supply a diff source.
    proc = run_cli(
        repo, env={"PRE_COMMIT_FROM_REF": "HEAD", "PRE_COMMIT_TO_REF": "HEAD"}
    )
    assert proc.returncode == 0, proc.stderr


def test_cli_flags_beat_env_refs(repo: Path) -> None:
    proc = run_cli(
        repo,
        "--from-ref",
        "HEAD",
        "--to-ref",
        "HEAD",
        env={"PRE_COMMIT_FROM_REF": "no-such-ref", "PRE_COMMIT_TO_REF": "no-such-ref"},
    )
    assert proc.returncode == 0, proc.stderr


def test_findings_exit_1_with_path_line_code(repo: Path, monkeypatch, capsys) -> None:
    make_change(repo)
    monkeypatch.chdir(repo)
    monkeypatch.setattr(
        cc,
        "CHECKS",
        [lambda path, lines, text: [(path, n, "TST001", "seen") for n in lines]],
    )
    assert cc.main(["new.py"]) == 1
    assert capsys.readouterr().out.splitlines() == [
        "new.py:1: TST001 seen",
        "new.py:2: TST001 seen",
    ]


# --- WHY001 / TODO001 (M6, map T8) ---------------------------------------------------


def codes(path: str, text: str, lines: set[int] | None = None) -> list[tuple[int, str]]:
    """Run every check as if ``lines`` (default: all) were the added lines of ``text``."""
    numbered = dict(enumerate(text.splitlines(), start=1))
    added = {n: t for n, t in numbered.items() if lines is None or n in lines}
    return sorted(
        (n, code) for chk in cc.CHECKS for _, n, code, _ in chk(path, added, text)
    )


@pytest.mark.parametrize(
    ("path", "text", "expected"),
    [
        ("a.py", "import os  # noqa: F401\n", [(1, "WHY001")]),
        ("a.py", "x: int = y  # type: ignore[assignment]\n", [(1, "WHY001")]),
        ("a.py", "import os  # NOQA\n", [(1, "WHY001")]),
        ("a.sh", "rm -f x || true\n", [(1, "WHY001")]),
        ("a.sh", "cmd 2>/dev/null\n", [(1, "WHY001")]),
        ("a.sh", "cmd 2> /dev/null\n", [(1, "WHY001")]),
        ("hook", "#!/usr/bin/env bash\ncmd || true\n", [(2, "WHY001")]),
        # ${#var} and $# do not start a comment, so the || true is still code
        ("a.sh", "n=${#a[@]}; echo $# || true\n", [(1, "WHY001")]),
        # §6.6 review: forms the first scanner missed
        ("a.sh", 'x="$(git rev-parse HEAD 2>/dev/null || true)"\n', [(1, "WHY001")]),
        ("a.sh", 'x="`cmd 2>/dev/null`"\n', [(1, "WHY001")]),
        ("a.sh", "x=$((1<<N))\nfoo || true\n", [(2, "WHY001")]),
        ("a.sh", "cat <<END-X\nbody\nEND-X\nfoo || true\n", [(4, "WHY001")]),
        ("a.sh", "echo $'it\\'s'\nfoo || true\n", [(2, "WHY001")]),
        ("a.sh", "cmd &>/dev/null\n", [(1, "WHY001")]),
        ("a.sh", "cmd >/dev/null 2>&1\n", [(1, "WHY001")]),
        ("a.sh", "cmd || :\n", [(1, "WHY001")]),
        ("a.py", "# ruff: noqa: E501\n", [(1, "WHY001")]),
        ("a.py", "# flake8: noqa\n", [(1, "WHY001")]),
        ("a.py", "x = f()  # pyright: ignore\n", [(1, "WHY001")]),
        ("a.py", "import subprocess  # nosec\n", [(1, "WHY001")]),
        ("a.sh", "# why: x\n\nfoo || true\n", [(3, "WHY001")]),
        ("a.py", "# todo: tidy\n", [(1, "TODO001")]),
        ("a.py", "# TODO see #12abc\n", [(1, "TODO001")]),
        ("a.py", "# TODO: tidy\n", [(1, "TODO001")]),
        ("a.py", "x = 1  # FIXME later\n", [(1, "TODO001")]),
        ("a.sh", "# TODO(ste): later\n", [(1, "TODO001")]),
    ],
)
def test_finding(path: str, text: str, expected: list) -> None:
    assert codes(path, text) == expected


@pytest.mark.parametrize(
    ("path", "text"),
    [
        # why: on the same line, or in the comment block directly above
        ("a.py", "import os  # noqa: F401  # why: re-export\n"),
        ("a.py", "# why: re-export\nimport os  # noqa: F401\n"),
        ("a.py", "# why: re-export for the\n# public API.\nimport os  # noqa: F401\n"),
        ("a.sh", "rm -f x || true  # why: may not exist\n"),
        ("a.sh", "# why: may not exist\nrm -f x 2>/dev/null\n"),
        # never scanned: strings, docstrings, comments' prose, heredocs, markdown
        ("a.py", 'S = "import os  # noqa: F401"\n'),
        ("a.py", '"""Docstring.\n\n# noqa TODO: no\n"""\n'),
        ("a.py", "# the TODO001 rule mentions noqa in prose\n"),
        ("a.sh", "# see the TODO at the bottom of this file\n"),
        ("a.sh", "echo 'x || true'\n"),
        ("a.sh", 'echo "cmd 2>/dev/null"\n'),
        ("a.sh", "# a comment saying || true\n"),
        ("a.sh", "cat <<EOF\nx || true\nEOF\n"),
        ("a.sh", "cat <<-'END'\n\tcmd 2>/dev/null\n\tEND\ny=1\n"),
        ("a.sh", 'x="$(echo "a || true")"\n'),
        ("a.sh", "cat <<\\EOF\nfoo || true\nEOF\n"),
        ("a.sh", "cat <<'END-X'\nfoo || true\nEND-X\n"),
        ("a.sh", "echo $'it\\'s || true'\n"),
        ("a.sh", "x=$(cat <<EOF\nfoo || true\nEOF\n)\n"),
        ("README.md", "x || true\n# TODO: no\n"),
        ("t.bats", "run cmd || true\n"),
        # referenced TODOs pass TODO001
        ("a.py", "# TODO(ADR-0021): x\n"),
        ("a.py", "# TODO(#42): x\n"),
        ("a.sh", "# FIXME(#7): x\n"),
    ],
)
def test_no_finding(path: str, text: str) -> None:
    assert codes(path, text) == []


def test_heredoc_ends_and_scanning_resumes() -> None:
    text = "cat <<EOF\nx || true\nEOF\ncmd || true\n"
    assert codes("a.sh", text) == [(4, "WHY001")]


def test_only_added_lines_are_reported() -> None:
    text = "import os  # noqa: F401\nimport re  # noqa: F401\n"
    assert codes("a.py", text, lines={2}) == [(2, "WHY001")]


def test_existing_why_above_covers_an_added_suppression() -> None:
    text = "# why: re-export\nimport os  # noqa: F401\n"
    assert codes("a.py", text, lines={2}) == []


def test_untokenizable_python_is_reported_not_skipped(caplog) -> None:
    assert codes("a.py", "x = (\n") == []
    assert "a.py: not tokenizable" in caplog.text


def test_finding_names_the_suppression() -> None:
    added = {1: "x: int = y  # type:   ignore[assignment]"}
    (finding,) = cc.check_why("a.py", added, added[1] + "\n")
    assert "`# type: ignore`" in finding[3]


def test_unscannable_files_are_never_read(repo: Path, monkeypatch) -> None:
    (repo / "doc.md").write_text("x || true\n")
    (repo / "pic.png").write_bytes(b"\x89PNG")
    (repo / "mod.py").write_text("a\nB\nc\n")
    git(repo, "add", "-A")
    shown: list[str] = []
    real = cc.new_text
    monkeypatch.setattr(
        cc, "new_text", lambda r, p, top: shown.append(p) or real(r, p, top)
    )
    monkeypatch.chdir(repo)
    assert cc.main([]) == 0
    assert shown == ["mod.py"]


def test_cli_end_to_end_reads_the_new_side(repo: Path) -> None:
    # The why: comment is an unchanged line; only the suppression below it is added.
    (repo / "mod.py").write_text("# why: kept for callers\nimport os\n")
    git(repo, "commit", "-qam", "why")
    (repo / "mod.py").write_text(
        "# why: kept for callers\nimport os  # noqa: F401\nimport re  # noqa: F401\n"
    )
    (repo / "h.sh").write_text("#!/bin/bash\nrm x || true\n# TODO: later\n")
    (repo / "doc.md").write_text("rm x || true\n")
    git(repo, "add", "-A")
    proc = run_cli(repo)
    assert proc.returncode == 1, proc.stderr
    assert proc.stdout.splitlines() == [
        "h.sh:2: WHY001 suppression `|| true` without a `# why:` on this line or the comment above",
        "h.sh:3: TODO001 TODO/FIXME without a reference: write TODO(#N) or TODO(ADR-NNNN)",
        "mod.py:3: WHY001 suppression `# noqa` without a `# why:` on this line or the comment above",
    ]


def test_cli_ref_mode_reads_the_to_side(repo: Path) -> None:
    (repo / "mod.py").write_text("import os  # noqa: F401\n")
    git(repo, "commit", "-qam", "bad")
    (repo / "mod.py").write_text("clean = 1\n")  # working tree differs from HEAD
    proc = run_cli(repo, "--from-ref", "HEAD~1", "--to-ref", "HEAD")
    assert proc.returncode == 1
    assert proc.stdout.startswith("mod.py:1: WHY001")


def test_cli_escapes_control_characters_and_bad_utf8_in_paths(repo: Path) -> None:
    name = b"evil\x1b[2Jname\xff.py"
    with open(os.fsencode(repo) + b"/" + name, "wb") as fh:
        fh.write(b"# TODO: x\n")
    git(repo, "add", "-A")
    proc = subprocess.run(
        ["python3", str(SCRIPT)], cwd=repo, capture_output=True, check=False
    )
    assert proc.returncode == 1, proc.stderr
    assert b"\x1b" not in proc.stdout
    assert proc.stdout.startswith(b"evil\\x1b[2Jname\\udcff.py:1: TODO001")


# --- §6.8 security review --------------------------------------------------------------


def test_hook_passes_filenames_after_double_dash() -> None:
    config = yaml.safe_load((SCRIPT.parents[1] / ".pre-commit-config.yaml").read_text())
    hook = next(
        h for r in config["repos"] for h in r["hooks"] if h["id"] == "check-conventions"
    )
    assert hook.get("args") == ["--"]


def test_a_filename_cannot_override_the_range(repo: Path) -> None:
    # pre-commit runs `entry args FILE...`; a committed file named like a flag must
    # stay a file, never switch the diff to an empty range.
    head = git(repo, "rev-parse", "HEAD").strip()
    (repo / "bad.py").write_text("import os  # noqa: F401\n")
    git(repo, "add", "-A")
    proc = run_cli(repo, "--", "bad.py", f"--from-ref={head}", f"--to-ref={head}")
    assert proc.returncode == 1, proc.stderr
    assert proc.stdout.startswith("bad.py:1: WHY001")


def test_why_scan_is_linear_in_the_comment_block() -> None:
    import time

    text = "# noqa\n" * 20000
    start = time.monotonic()
    assert len(codes("a.py", text)) == 20000
    # why: the old walk-back was O(n²) — 8k lines took 6.5 s; linear is ~0.1 s here.
    assert time.monotonic() - start < 5


def test_log_lines_escape_control_characters(caplog) -> None:
    codes("evil\x1b[31m.py", "x = (\n")
    assert "\x1b" not in caplog.text
    assert "evil\\x1b[31m.py" in caplog.text


def test_unbalanced_shell_context_is_logged(caplog) -> None:
    codes("a.sh", 'echo "unclosed\nfoo || true\n')
    assert "a.sh: shell context unbalanced at end of file" in caplog.text


@pytest.mark.parametrize("name", ["::error title=x::y.py", " \t::warning::y.py"])
def test_workflow_command_paths_are_defused(repo: Path, name: str) -> None:
    # why: GitHub may read a workflow command after leading whitespace, so any line
    # whose first non-blank characters are `::` is defused.
    (repo / name).write_text("# TODO: x\n")
    git(repo, "add", "-A")
    proc = run_cli(repo)
    assert proc.returncode == 1
    assert proc.stdout.startswith("./")
    assert not proc.stdout.lstrip().startswith("::")


def test_staged_path_that_looks_like_a_stage_spec(repo: Path) -> None:
    (repo / "1:evil.py").write_text("# TODO: x\n")
    git(repo, "add", "-A")
    proc = run_cli(repo)
    assert proc.returncode == 1, proc.stderr
    assert proc.stdout.startswith("1:evil.py:1: TODO001")
