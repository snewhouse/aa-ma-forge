"""M1 AC6, AC9, AC10, AC11: provenance stamp, SHA freshness, self-ignoring report root, safe paths."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest

from aa_ma.analysis import cli, stamp
from aa_ma.analysis.models import Stamp

from .conftest import commit_file, git

REPORTS = Path(".claude/reports/assess-codebase")


def test_head_stamp_clean_repo(repo: Path) -> None:
    sha12, dirty, branch = stamp.head_stamp(repo)
    assert sha12 == git(repo, "rev-parse", "HEAD")[:12]
    assert dirty is False
    assert branch == git(repo, "rev-parse", "--abbrev-ref", "HEAD")


def test_untracked_file_is_not_dirty(repo: Path) -> None:
    """AC10 / Eng E1: writing ONBOARDING.md must not make the run it describes stale."""
    s = stamp.build_stamp(repo, "quick")
    (repo / "ONBOARDING.md").write_text("# new\n", encoding="utf-8")
    assert stamp.head_stamp(repo)[1] is False
    assert stamp.is_fresh(s, repo) is True


def test_tracked_edit_is_dirty_and_stale(repo: Path) -> None:
    s = stamp.build_stamp(repo, "quick")
    (repo / "src" / "app.py").write_text("print(2)\n", encoding="utf-8")
    assert stamp.head_stamp(repo)[1] is True
    assert stamp.is_fresh(s, repo) is False


def test_new_commit_makes_stamp_stale(repo: Path) -> None:
    s = stamp.build_stamp(repo, "standard")
    commit_file(repo, "src/new.py", "y = 2\n")
    assert stamp.is_fresh(s, repo) is False


def test_dirty_stamp_is_never_fresh(repo: Path) -> None:
    (repo / "src" / "app.py").write_text("print(2)\n", encoding="utf-8")
    s = stamp.build_stamp(repo, "quick")
    assert s.dirty is True
    assert stamp.is_fresh(s, repo) is False


def test_build_stamp_fields(repo: Path) -> None:
    s = stamp.build_stamp(repo, "deep")
    assert isinstance(s, Stamp)
    assert s.tier == "deep"
    assert (
        s.date_utc.utcoffset() is not None
        and s.date_utc.utcoffset().total_seconds() == 0
    )
    assert s.tools == {} and s.absorbed == [] and s.fresh_run == []


def test_report_dir_name(repo: Path) -> None:
    sha12 = git(repo, "rev-parse", "HEAD")[:12]
    assert stamp.report_dir(repo) == repo / REPORTS / sha12
    (repo / "README.md").write_text("# edited\n", encoding="utf-8")
    assert stamp.report_dir(repo) == repo / REPORTS / f"{sha12}-dirty"


def test_detached_head_branch(repo: Path) -> None:
    commit_file(repo, "src/two.py", "z = 3\n")
    git(repo, "checkout", "-q", "--detach", "HEAD~1")
    assert stamp.head_stamp(repo)[2] == "(detached)"


def test_shallow_clone_stamps_head(repo: Path, tmp_path: Path) -> None:
    clone = tmp_path / "shallow"
    subprocess.run(
        ["git", "clone", "-q", "--depth", "1", f"file://{repo}", str(clone)], check=True
    )
    assert stamp.head_stamp(clone)[0] == git(repo, "rev-parse", "HEAD")[:12]


def test_non_git_dir_exits_2(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert cli.main(["stamp", "--repo", str(tmp_path), "--tier", "quick"]) == 2
    assert "not a git repo with ≥1 commit" in capsys.readouterr().err


def test_zero_commit_repo_exits_2(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    git(tmp_path, "init", "-q")
    assert cli.main(["stamp", "--repo", str(tmp_path), "--tier", "quick"]) == 2
    assert "not a git repo with ≥1 commit" in capsys.readouterr().err


def test_stamp_cli_prints_valid_stamp(
    repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert cli.main(["stamp", "--repo", str(repo), "--tier", "standard"]) == 0
    s = Stamp.model_validate_json(capsys.readouterr().out)
    assert s.sha12 == git(repo, "rev-parse", "HEAD")[:12]


def test_stamp_cli_requires_tier(repo: Path) -> None:
    with pytest.raises(SystemExit) as exc:
        cli.main(["stamp", "--repo", str(repo)])
    assert exc.value.code == 2


def _write_summary_dir(repo: Path, s: Stamp) -> Path:
    fixture = (
        Path(__file__).resolve().parents[2]
        / "tests/fixtures/analysis/valid/summary.json"
    )
    doc = json.loads(fixture.read_text(encoding="utf-8"))
    doc["stamp"] = json.loads(s.model_dump_json())
    d = repo / REPORTS / s.sha12
    d.mkdir(parents=True)
    (d / "summary.json").write_text(json.dumps(doc), encoding="utf-8")
    return d


def test_fresh_cli(repo: Path) -> None:
    d = _write_summary_dir(repo, stamp.build_stamp(repo, "standard"))
    assert cli.main(["fresh", str(d), "--repo", str(repo)]) == 0
    commit_file(repo, "src/later.py", "w = 4\n")
    assert cli.main(["fresh", str(d), "--repo", str(repo)]) == 1


def test_fresh_cli_legacy_dir_is_unverified(
    repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    legacy = repo / ".claude/reports/codebase-deep-dive-2026-09-17"
    legacy.mkdir(parents=True)
    (legacy / "00-executive-summary.md").write_text("# old\n", encoding="utf-8")
    assert cli.main(["fresh", str(legacy), "--repo", str(repo)]) == 1
    assert "legacy, unverified" in capsys.readouterr().out


def test_fresh_cli_reads_onboarding_json(repo: Path) -> None:
    fixture = (
        Path(__file__).resolve().parents[2]
        / "tests/fixtures/analysis/valid/onboarding.json"
    )
    doc = json.loads(fixture.read_text(encoding="utf-8"))
    doc["stamp"] = json.loads(stamp.build_stamp(repo, "quick").model_dump_json())
    target = repo / ".claude/onboarding/onboarding.json"
    target.parent.mkdir(parents=True)
    target.write_text(json.dumps(doc), encoding="utf-8")
    assert cli.main(["fresh", str(target), "--repo", str(repo)]) == 0


# --- self-ignoring report root + safe paths (AC6) -------------------------------------------


def test_ensure_self_ignoring_hides_reports(repo: Path) -> None:
    root = stamp.safe_dir(repo, str(REPORTS))
    stamp.ensure_self_ignoring(root)
    (root / "abc").mkdir()
    (root / "abc" / "summary.json").write_text("{}", encoding="utf-8")
    assert (root / ".gitignore").read_text(encoding="utf-8") == "*\n"
    assert git(repo, "status", "--porcelain") == ""


def test_ensure_self_ignoring_refuses_symlinked_gitignore(
    repo: Path, tmp_path: Path
) -> None:
    root = stamp.safe_dir(repo, str(REPORTS))
    outside = tmp_path / "elsewhere"
    outside.write_text("keep\n", encoding="utf-8")
    (root / ".gitignore").symlink_to(outside)
    with pytest.raises(stamp.UnsafePath):
        stamp.ensure_self_ignoring(root)
    assert outside.read_text(encoding="utf-8") == "keep\n"


SYMLINKABLE = [
    ".claude",
    ".claude/reports",
    ".claude/reports/assess-codebase",
    ".claude/reports/assess-codebase/.work-0123456789ab",
    ".claude/onboarding",
]


@pytest.mark.parametrize("component", SYMLINKABLE)
def test_safe_dir_refuses_a_symlinked_component(
    repo: Path, tmp_path: Path, component: str
) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    link = repo / component
    link.parent.mkdir(parents=True, exist_ok=True)
    link.symlink_to(outside, target_is_directory=True)
    target = (
        component
        if component.endswith((".work-0123456789ab", "onboarding"))
        else f"{component}/x"
    )
    with pytest.raises(stamp.UnsafePath):
        stamp.safe_dir(repo, target)
    assert list(outside.iterdir()) == [], "nothing may be written through the symlink"


def test_safe_dir_refuses_escape(repo: Path) -> None:
    with pytest.raises(stamp.UnsafePath):
        stamp.safe_dir(repo, "../escaped")
    with pytest.raises(stamp.UnsafePath):
        stamp.safe_dir(repo, "/tmp/absolute")


def test_safe_dir_creates_and_returns(repo: Path) -> None:
    d = stamp.safe_dir(repo, ".claude/onboarding")
    assert d == repo / ".claude/onboarding" and d.is_dir() and not d.is_symlink()


# --- git option injection (AC11) -------------------------------------------------------------


def test_every_git_call_ends_options(
    repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[list[str]] = []
    real = subprocess.run

    def spy(argv, *a, **kw):  # type: ignore[no-untyped-def]
        if argv and os.path.basename(str(argv[0])) == "git":
            calls.append([str(x) for x in argv])
        return real(argv, *a, **kw)

    monkeypatch.setattr(stamp.subprocess, "run", spy)
    stamp.head_stamp(repo)
    stamp.is_fresh(stamp.build_stamp(repo, "quick"), repo)
    assert calls, "expected git subprocess calls"
    for argv in calls:
        assert "--end-of-options" in argv, argv
        after = argv[argv.index("--end-of-options") + 1 :]
        assert not any(a.startswith("-") for a in after), argv


# --- M2 2.9: one binary lookup, one safe reader, one naming pattern -------------------------------


def _exe(path: Path, body: str = "exit 0") -> Path:
    path.write_text("#!/bin/sh\n" + body + "\n", encoding="utf-8")
    path.chmod(0o755)
    return path


def test_find_binary_ignores_relative_path_entries(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Resolved after a chdir into the target, `.` or an empty entry finds a planted binary."""
    _exe(tmp_path / "toolx")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("PATH", f".{os.pathsep}{os.pathsep}/usr/bin{os.pathsep}/bin")
    monkeypatch.delenv("TOOLX_BIN", raising=False)
    assert stamp.find_binary("toolx") is None


def test_find_binary_override_must_be_executable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("TOOLX_BIN", str(_exe(tmp_path / "ok")))
    assert stamp.find_binary("toolx") == str(tmp_path / "ok")
    (tmp_path / "noexec").write_text("x")
    monkeypatch.setenv("TOOLX_BIN", str(tmp_path / "noexec"))
    assert stamp.find_binary("toolx") is None


def test_git_is_never_taken_from_a_relative_path_entry(
    repo: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    marker = tmp_path / "planted-git-ran"
    bindir = tmp_path / "hostile"
    bindir.mkdir()
    _exe(bindir / "git", f"touch '{marker}'; exit 1")
    monkeypatch.chdir(bindir)
    monkeypatch.setenv("PATH", f".{os.pathsep}{os.environ['PATH']}")
    assert stamp.head_stamp(repo)[0]
    assert not marker.exists()


def test_read_regular_refuses_a_symlink_and_never_blocks_on_a_fifo(
    tmp_path: Path,
) -> None:
    import signal

    (tmp_path / "real").write_text("ok", encoding="utf-8")
    os.symlink(tmp_path / "real", tmp_path / "link")
    os.mkfifo(tmp_path / "fifo")
    assert stamp.read_regular(tmp_path / "real") == "ok"
    signal.alarm(5)  # a blocking open would hang here
    try:
        for name in ("link", "fifo"):
            with pytest.raises(OSError):
                stamp.read_regular(tmp_path / name)
    finally:
        signal.alarm(0)


def test_the_report_name_pattern_is_the_naming_rule() -> None:
    assert stamp.REPORT_NAME.fullmatch(stamp.report_name("0123456789ab", True))
    assert stamp.REPORT_NAME.fullmatch(stamp.report_name("0123456789ab", False))
    assert not stamp.REPORT_NAME.fullmatch(".work-0123456789ab")


# --- M2 2.10: the target's own .git/config never runs code for us -------------------------------


def test_git_calls_never_run_the_targets_fsmonitor(
    repo: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Defence in depth: the command-scope override alone stops it (the config check is off)."""
    monkeypatch.setattr(stamp, "check_git_config", lambda repo: None)
    marker = tmp_path / "fsmonitor-ran"
    git(repo, "config", "core.fsmonitor", f"touch '{marker}'; false")
    stamp.head_stamp(repo)
    assert not marker.exists()


@pytest.mark.parametrize(
    "key,value",
    [
        ("core.fsmonitor", "x"),
        ("filter.lfs.clean", "x"),
        ("diff.x.textconv", "x"),
        ("include.path", "x"),
        ("core.sshCommand", "x"),
        ("includeIf.gitdir:/x.path", "x"),
        ("diff.x.command", "x"),
        ("gpg.program", "x"),
        ("log.showSignature", "true"),
        ("core.pager", "x"),
        ("some.unknownkey", "x"),
        # A dotted subsection must not smuggle a key past a prefix match.
        ("remote.a.url.b.uploadpack", "x"),
        ("core.worktree", "/elsewhere"),  # allowed only in a submodule's own config
    ],
)
def test_a_git_config_that_can_run_commands_is_refused_by_name(
    repo: Path, key: str, value: str
) -> None:
    git(repo, "config", key, value)
    with pytest.raises(stamp.UnsafeRepo, match=key.lower()):
        stamp.check_git_config(repo)


def test_an_ordinary_git_config_passes(repo: Path) -> None:
    """What a fresh clone plus a user identity writes: every key is on the safe list."""
    for key, value in [
        ("user.name", "Someone"),
        ("user.email", "s@example.invalid"),
        ("remote.origin.url", "https://example.invalid/r.git"),
        ("remote.origin.fetch", "+refs/heads/*:refs/remotes/origin/*"),
        ("branch.main.remote", "origin"),
        ("branch.main.merge", "refs/heads/main"),
        ("core.autocrlf", "input"),
        (
            "branch.main.vscode-merge-base",
            "origin/main",
        ),  # VS Code: 11 of 17 local repos
    ]:
        git(repo, "config", key, value)
    stamp.check_git_config(repo)


def test_worktree_scoped_config_is_checked(repo: Path) -> None:
    git(repo, "config", "extensions.worktreeConfig", "true")
    git(repo, "config", "--worktree", "filter.x.clean", "cat")
    with pytest.raises(stamp.UnsafeRepo, match=r"filter\.x\.clean"):
        stamp.check_git_config(repo)


def test_a_submodule_config_is_checked(repo: Path) -> None:
    module = repo / ".git" / "modules" / "sub"
    module.mkdir(parents=True)
    git(repo, "config", "--file", str(module / "config"), "filter.x.clean", "cat")
    with pytest.raises(stamp.UnsafeRepo, match=r"filter\.x\.clean"):
        stamp.check_git_config(repo)


def test_an_unreadable_git_config_is_refused(repo: Path) -> None:
    (repo / ".git" / "config").write_text("[core\nbroken", encoding="utf-8")
    with pytest.raises(stamp.UnsafeRepo, match="cannot read"):
        stamp.check_git_config(repo)


def test_our_git_log_never_verifies_signatures(repo: Path, tmp_path: Path) -> None:
    """log.showSignature + gpg.program + one signed-looking commit ran the program (§6.8 r4)."""
    marker = tmp_path / "gpg-ran"
    gpg = tmp_path / "gpg"
    gpg.write_text(f"#!/bin/sh\ntouch '{marker}'\n", encoding="utf-8")
    gpg.chmod(0o755)
    body = git(repo, "cat-file", "commit", "HEAD")
    head, _, message = body.partition("\n\n")
    signed = f"{head}\ngpgsig -----BEGIN PGP SIGNATURE-----\n x\n -----END PGP SIGNATURE-----\n\n{message}"
    sha = subprocess.run(
        ["git", "hash-object", "-t", "commit", "-w", "--stdin"],
        cwd=repo, input=signed, capture_output=True, text=True, check=True,
    ).stdout.strip()  # fmt: skip
    git(repo, "update-ref", "HEAD", sha)
    git(repo, "config", "log.showSignature", "true")
    git(repo, "config", "gpg.program", str(gpg))
    assert stamp.run_git(repo, "log", "-1", "--format=%ct", "HEAD").returncode == 0
    assert not marker.exists()


def _add_submodule(repo: Path, tmp_path: Path) -> None:
    inner = tmp_path / "inner"
    inner.mkdir()
    git(inner, "init", "-q")
    commit_file(inner, "a.txt", "a\n")
    commit_file(inner, ".gitattributes", "*.txt filter=x\n")
    git(
        repo,
        "-c",
        "protocol.file.allow=always",
        "submodule",
        "add",
        "-q",
        str(inner),
        "sub",
    )
    git(repo, "commit", "-qm", "sub")


def test_a_repo_with_an_ordinary_submodule_passes(repo: Path, tmp_path: Path) -> None:
    """git writes core.worktree into every submodule's own config."""
    _add_submodule(repo, tmp_path)
    stamp.check_git_config(repo)


def test_status_never_enters_a_submodule(
    repo: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Defence in depth (config check off): a submodule's filter never runs under status."""
    monkeypatch.setattr(stamp, "check_git_config", lambda repo: None)
    _add_submodule(repo, tmp_path)
    marker = tmp_path / "filter-ran"
    module = repo / ".git" / "modules" / "sub" / "config"
    git(
        repo,
        "config",
        "--file",
        str(module),
        "filter.x.clean",
        f"touch '{marker}'; cat",
    )
    os.utime(repo / "sub" / "a.txt", (1, 1))
    stamp.head_stamp(repo)
    assert not marker.exists()


def test_a_relative_bin_override_is_made_absolute(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _exe(tmp_path / "tool")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("TOOLX_BIN", "tool")
    assert stamp.find_binary("toolx") == str(tmp_path / "tool")


# --- M2 2.12: §6.8 round 5 ----------------------------------------------------------------------


def _hostile_filter(repo: Path, marker: Path) -> None:
    """A filter in the target's own config, selected by its .gitattributes, on a stat-dirty file."""
    commit_file(repo, ".gitattributes", "*.py filter=x\n")
    git(repo, "config", "filter.x.clean", f"sh -c 'touch {marker}; cat'")
    for f in repo.rglob("*.py"):
        os.utime(f, (1, 1))


@pytest.mark.parametrize("command", ["stamp", "fresh"])
def test_every_cli_command_refuses_an_unsafe_git_config(
    command: str, repo: Path, tmp_path: Path
) -> None:
    """R5-1: stamp and fresh reached `git status` without the config check."""
    d = _write_summary_dir(repo, stamp.build_stamp(repo, "standard"))
    marker = tmp_path / "filter-ran"
    _hostile_filter(repo, marker)
    argv = (
        ["stamp", "--repo", str(repo), "--tier", "quick"]
        if command == "stamp"
        else ["fresh", str(d), "--repo", str(repo)]
    )
    assert cli.main(argv) == 2
    assert not marker.exists()


def test_a_git_dir_outside_the_repo_is_refused(repo: Path, tmp_path: Path) -> None:
    """A `.git` file naming another repo's git dir would mine that repo's history."""
    victim = tmp_path / "victim"
    victim.mkdir()
    git(victim, "init", "-q")
    commit_file(victim, "secret.txt", "x\n")
    target = tmp_path / "target"
    target.mkdir()
    (target / ".git").write_text(f"gitdir: {victim / '.git'}\n", encoding="utf-8")
    with pytest.raises(stamp.UnsafeRepo, match="outside"):
        stamp.head_stamp(target)


def test_a_commondir_outside_the_repo_is_refused(repo: Path, tmp_path: Path) -> None:
    victim = tmp_path / "victim"
    victim.mkdir()
    git(victim, "init", "-q")
    (repo / ".git" / "commondir").write_text(str(victim / ".git"), encoding="utf-8")
    with pytest.raises(stamp.UnsafeRepo, match="outside"):
        stamp.check_git_config(repo)


def test_a_linked_worktree_of_the_users_repo_is_accepted(
    repo: Path, tmp_path: Path
) -> None:
    wt = tmp_path / "wt"
    git(repo, "worktree", "add", "-q", "--detach", str(wt))
    assert stamp.head_stamp(wt)[0] == stamp.head_stamp(repo)[0]


def test_a_git_call_that_hangs_is_refused(
    repo: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """include.path at a FIFO blocked `git config --list` forever."""
    fifo = tmp_path / "fifo"
    os.mkfifo(fifo)
    git(repo, "config", "include.path", str(fifo))
    monkeypatch.setattr(stamp, "GIT_TIMEOUT_S", 2)
    with pytest.raises(stamp.UnsafeRepo, match="did not finish"):
        stamp.check_git_config(repo)


def test_the_users_global_filters_are_never_reached(
    repo: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A target .gitattributes `filter=lfs` selected the user's global git-lfs clean filter."""
    marker = tmp_path / "global-filter-ran"
    script = (
        tmp_path / "clean.sh"
    )  # a script: `;` would start a comment in a config file
    script.write_text(f"#!/bin/sh\ntouch '{marker}'\ncat\n", encoding="utf-8")
    script.chmod(0o755)
    cfg = tmp_path / "global.gitconfig"
    cfg.write_text(f'[filter "lfs"]\n\tclean = {script}\n', encoding="utf-8")
    commit_file(repo, ".gitattributes", "*.py filter=lfs\n")
    for f in repo.rglob("*.py"):
        os.utime(f, (1, 1))
    monkeypatch.setenv(
        "GIT_CONFIG_GLOBAL", str(cfg)
    )  # after setup: only our call can run it
    stamp.head_stamp(repo)
    assert not marker.exists()


def test_a_git_file_naming_another_repos_worktree_is_refused(
    repo: Path, tmp_path: Path
) -> None:
    """The worktree exception holds only when that git dir names *this* dir back."""
    wt = tmp_path / "their-wt"
    git(repo, "worktree", "add", "-q", "--detach", str(wt))
    [wt_git_dir] = (repo / ".git" / "worktrees").iterdir()
    target = tmp_path / "target"
    target.mkdir()
    (target / ".git").write_text(f"gitdir: {wt_git_dir}\n", encoding="utf-8")
    with pytest.raises(stamp.UnsafeRepo, match="outside"):
        stamp.head_stamp(target)


def test_a_relative_path_worktree_is_accepted(repo: Path, tmp_path: Path) -> None:
    """`git worktree add --relative-paths` writes a back-reference relative to the git dir."""
    wt = tmp_path / "rel-wt"
    git(repo, "worktree", "add", "-q", "--relative-paths", "--detach", str(wt))
    assert stamp.head_stamp(wt)[0] == stamp.head_stamp(repo)[0]


def test_a_subdir_of_a_hostile_clone_cannot_forge_the_worktree_exception(
    repo: Path,
) -> None:
    """The enclosing repo's own git dir is not a worktree git dir, whatever `gitdir` it holds."""
    sub = repo / "sub"
    sub.mkdir()
    (repo / ".git" / "gitdir").write_text(f"{sub / '.git'}\r\n  ", encoding="utf-8")
    with pytest.raises(stamp.UnsafeRepo, match="outside"):
        stamp.head_stamp(sub)
