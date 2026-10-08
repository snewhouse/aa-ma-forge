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


def test_cli_clean_reports_zero_checks(repo: Path) -> None:
    make_change(repo)
    proc = run_cli(repo)
    assert proc.returncode == 0, proc.stderr
    assert "check_conventions: 0 checks enabled" in proc.stderr
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
        cc, "CHECKS", [lambda path, lines: [(path, n, "TST001", "seen") for n in lines]]
    )
    assert cc.main(["new.py"]) == 1
    assert capsys.readouterr().out.splitlines() == [
        "new.py:1: TST001 seen",
        "new.py:2: TST001 seen",
    ]
