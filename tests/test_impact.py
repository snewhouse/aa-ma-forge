"""aa_ma.impact — gate-computed IMPACT_VERIFIED (code-conventions-impact 11.3, ticket T7).

Fixture repos are real git repos; co-change cases run the REAL codemem (the workspace
member) so the 5-shared / 50% boundary is codemem's own ``>=``, not a mock's. A stub
codemem (``CODEMEM_BIN``) injects the failures a real one will not produce on demand:
a skipped refresh, a failed refresh, a stale answer.
"""

from __future__ import annotations

import datetime as dt
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

from aa_ma import impact
from aa_ma.impact import (
    COCHANGE_MIN_RATIO,
    COCHANGE_MIN_SHARED,
    COCHANGE_WINDOW_COMMITS,
    IMPACT_CUTOVER,
    IMPACT_EXCLUDE,
    compute,
)

ROOT = Path(__file__).resolve().parents[1]
# why: fixture plan dates either side of every real cutover; the CLI runs in a subprocess, so no monkeypatch
GRANDFATHERED = "2020-01-01"
POST_CUTOVER = "2027-01-01"
TASK = ".claude/dev/active/t"
HEADING = "Milestone 1: Thing"

PLAN = """\
# t Plan
Created: {created}

### Milestone 1 — Thing
#### Contract
```
Files:
{rows}
```
"""

TASKS = """\
# t Tasks

## Milestone 1: Thing
- Status: ACTIVE
- Gate: HARD
{extra}
### Sub-step 1.1: Do it
- Status: PENDING
- Mode: AFK
"""


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=repo, check=True, capture_output=True, text=True
    ).stdout.strip()


def _write(repo: Path, rel: str, text: str) -> None:
    path = repo / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _commit(repo: Path, msg: str) -> str:
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", msg)
    return _git(repo, "rev-parse", "HEAD")


class Fixture:
    def __init__(
        self, tmp: Path, rows: str, *, reference: str = "", created: str = POST_CUTOVER
    ) -> None:
        self.repo = tmp / "repo"
        self.repo.mkdir()
        _git(self.repo, "init", "-q", "-b", "main")
        _git(self.repo, "config", "user.email", "t@example.com")
        _git(self.repo, "config", "user.name", "t")
        _write(self.repo, "src/a.py", "A = 1\n")
        _write(self.repo, "tests/test_a.py", "def test_a():\n    pass\n")
        _write(self.repo, "src/b.py", "B = 1\n")
        _write(self.repo, f"{TASK}/t-plan.md", PLAN.format(rows=rows, created=created))
        _write(self.repo, f"{TASK}/t-tasks.md", TASKS.format(extra=""))
        _write(self.repo, f"{TASK}/t-reference.md", f"# ref\n{reference}")
        _write(self.repo, f"{TASK}/t-context-log.md", "# log\n")
        _write(self.repo, f"{TASK}/t-provenance.log", "")
        self.base = _commit(self.repo, "base")

    @property
    def plan(self) -> Path:
        return self.repo / TASK / "t-plan.md"

    @property
    def tasks(self) -> Path:
        return self.repo / TASK / "t-tasks.md"

    def tasks_extra(self, extra: str) -> None:
        self.tasks.write_text(TASKS.format(extra=extra), encoding="utf-8")

    def append(self, name: str, text: str) -> None:
        path = self.repo / TASK / f"t-{name}"
        path.write_text(path.read_text(encoding="utf-8") + text, encoding="utf-8")

    def run(self, **kw):
        kw.setdefault("ignore_cutover", True)
        return compute(self.plan, self.tasks, 1, self.base, **kw)


ROWS = "  Modify  src/a.py\n  Test    tests/test_a.py"


@pytest.fixture
def db(tmp_path, monkeypatch) -> Path:
    path = tmp_path / "cm" / "index.db"
    monkeypatch.setenv("CODEMEM_DB", str(path))
    monkeypatch.delenv("CODEMEM_BIN", raising=False)
    return path


def _build(fx: Fixture) -> None:
    codemem = Path(sys.executable).with_name("codemem")
    subprocess.run(
        [str(codemem), "build", "--repo-root", str(fx.repo)],
        cwd=fx.repo,
        check=True,
        capture_output=True,
    )


@pytest.fixture
def fx(tmp_path, db) -> Fixture:
    f = Fixture(tmp_path, ROWS)
    _build(f)
    return f


# --- constants -----------------------------------------------------------------------------


def test_constants_are_the_t7_and_11_1_decisions() -> None:
    assert dt.date.fromisoformat(IMPACT_CUTOVER)
    assert (COCHANGE_MIN_SHARED, COCHANGE_MIN_RATIO) == (5, 0.5)
    assert COCHANGE_WINDOW_COMMITS == 500
    assert IMPACT_EXCLUDE == (
        ".claude/dev/**",
        "docs/architecture/**",
        "tests/golden/**",
        "uv.lock",
        "CHANGELOG.md",
    )


def test_shell_twin_constants_match() -> None:
    """aa-ma-parse.sh `aa_ma_cochange_partners` (the pre-edit hook path) uses the same T7 pair."""
    sh = (ROOT / "claude-code/hooks/lib/aa-ma-parse.sh").read_text(encoding="utf-8")
    shared = re.search(r"AA_MA_COCHANGE_MIN_SHARED=(\S+)", sh)
    ratio = re.search(r"AA_MA_COCHANGE_MIN_RATIO=(\S+)", sh)
    assert shared and ratio
    assert int(shared.group(1).strip("\"'")) == COCHANGE_MIN_SHARED
    assert float(ratio.group(1).strip("\"'")) == COCHANGE_MIN_RATIO


# --- applicability -------------------------------------------------------------------------


def test_grandfathered_plan_is_not_applicable(fx, monkeypatch) -> None:
    # why: pinned — the fixture plan is dated POST_CUTOVER, so the live cutover cannot decide it
    monkeypatch.setattr(impact, "IMPACT_CUTOVER", "2028-01-01")
    r = fx.run(ignore_cutover=False)
    assert r.exit_code == 5
    assert f"Created: {POST_CUTOVER}" in r.reason and "2028-01-01" in r.reason


def test_cutover_is_release_date() -> None:
    """M14.1: fence 4 applies from the v0.18.0 release date (ADR-0027 P4), not the sentinel."""
    assert IMPACT_CUTOVER != "9999-12-31"
    assert POST_CUTOVER >= IMPACT_CUTOVER  # why: the fixtures rely on it to be in force
    assert dt.date.fromisoformat(IMPACT_CUTOVER)
    tag = subprocess.run(
        ["git", "-C", str(ROOT), "log", "-1", "--format=%cs", "v0.18.0", "--"],
        capture_output=True,
        text=True,
        check=False,
    )
    if tag.returncode != 0:
        # why: before 14.2 tags it, or in a clone without tags (CI checkout), only the sentinel check applies
        pytest.skip("tag v0.18.0 not present")
    assert tag.stdout.strip() == IMPACT_CUTOVER


def test_post_cutover_plan_is_checked(fx, monkeypatch) -> None:
    monkeypatch.setattr(impact, "IMPACT_CUTOVER", "2026-01-01")
    _write(fx.repo, "src/a.py", "A = 2\n")
    _write(fx.repo, "tests/test_a.py", "def test_a():\n    assert 1\n")
    assert fx.run(ignore_cutover=False).exit_code == 0


def test_plan_without_created_is_not_applicable(fx) -> None:
    fx.plan.write_text(fx.plan.read_text().replace(f"Created: {POST_CUTOVER}\n", ""))
    fx.base = _commit(
        fx.repo, "plan date at the base"
    )  # the merge-base copy dates the plan
    r = fx.run(ignore_cutover=False)
    assert r.exit_code == 5 and "no Created:" in r.reason


# --- the predicted / changed comparison ----------------------------------------------------


def test_predicted_and_changed_agree_passes(fx) -> None:
    _write(fx.repo, "src/a.py", "A = 2\n")
    _write(fx.repo, "tests/test_a.py", "def test_a():\n    assert 1\n")
    _commit(fx.repo, "m1")
    r = fx.run()
    assert (r.exit_code, r.unexplained) == (0, [])
    assert r.changed == ["src/a.py", "tests/test_a.py"]


def test_unpredicted_file_fails(fx) -> None:
    _write(fx.repo, "src/a.py", "A = 2\n")
    _write(fx.repo, "tests/test_a.py", "def test_a():\n    assert 1\n")
    _write(fx.repo, "src/b.py", "B = 2\n")
    r = fx.run()
    assert r.exit_code == 1
    assert r.unpredicted == ["src/b.py"] and r.unexplained == ["src/b.py"]


def test_predicted_unchanged_fails(fx) -> None:
    _write(fx.repo, "src/a.py", "A = 2\n")
    r = fx.run()
    assert r.exit_code == 1 and r.predicted_unchanged == ["tests/test_a.py"]


def test_explained_file_passes_and_a_bare_explanation_does_not(fx) -> None:
    _write(fx.repo, "src/a.py", "A = 2\n")
    _write(fx.repo, "tests/test_a.py", "def test_a():\n    assert 1\n")
    _write(fx.repo, "src/b.py", "B = 2\n")
    fx.tasks_extra("- Impact-Explained: `src/b.py`\n")
    assert fx.run().exit_code == 1
    fx.tasks_extra("- Impact-Explained: `src/b.py` — renamed constant, no caller\n")
    r = fx.run()
    assert r.exit_code == 0
    assert r.explained == {"src/b.py": "renamed constant, no caller"}


def test_working_tree_staged_unstaged_and_untracked_count(fx) -> None:
    _write(fx.repo, "src/a.py", "A = 2\n")  # unstaged
    _write(fx.repo, "tests/test_a.py", "def test_a():\n    assert 1\n")
    _git(fx.repo, "add", "tests/test_a.py")  # staged
    _write(fx.repo, "src/new.py", "N = 1\n")  # untracked
    r = fx.run()
    assert r.changed == ["src/a.py", "src/new.py", "tests/test_a.py"]
    assert r.unpredicted == ["src/new.py"]


def test_rename_counts_old_and_new(tmp_path, db) -> None:
    fx = Fixture(tmp_path, "  Move    src/a.py → src/c.py")
    _build(fx)
    _git(fx.repo, "mv", "src/a.py", "src/c.py")
    _commit(fx.repo, "mv")
    r = fx.run()
    assert r.changed == ["src/a.py", "src/c.py"] and r.exit_code == 0


def test_deleted_predicted_file_counts_as_changed(tmp_path, db) -> None:
    fx = Fixture(tmp_path, "  Delete  src/b.py")
    _build(fx)
    _git(fx.repo, "rm", "-q", "src/b.py")
    r = fx.run()
    assert r.changed == ["src/b.py"] and r.exit_code == 0


def test_directory_row_covers_what_is_beneath_it(tmp_path, db) -> None:
    fx = Fixture(tmp_path, "  Modify  src/")
    _build(fx)
    _write(fx.repo, "src/b.py", "B = 2\n")
    assert fx.run().exit_code == 0


def test_excluded_paths_are_never_unexplained(fx) -> None:
    _write(fx.repo, "src/a.py", "A = 2\n")
    _write(fx.repo, "tests/test_a.py", "def test_a():\n    assert 1\n")
    _write(fx.repo, "CHANGELOG.md", "x\n")
    _write(fx.repo, "docs/architecture/c.md", "x\n")
    fx.append("provenance.log", "x\n")
    r = fx.run()
    assert r.exit_code == 0 and "CHANGELOG.md" not in r.changed


def test_no_contract_rows_fails(tmp_path, db) -> None:
    fx = Fixture(tmp_path, "")
    _build(fx)
    r = fx.run()
    assert r.exit_code == 1 and r.reason == "no Contract Files for Milestone 1"


# --- co-change misses (real codemem) -------------------------------------------------------


def _cochange_history(fx: Fixture, shared: int, alone: int) -> None:
    """x.md and y.md change together `shared` times; x.md alone `alone` times."""
    for i in range(shared):
        _write(fx.repo, "notes/x.md", f"x{i}\n")
        _write(fx.repo, "notes/y.md", f"y{i}\n")
        _commit(fx.repo, f"both {i}")
    for i in range(alone):
        _write(fx.repo, "notes/x.md", f"x-alone{i}\n")
        _commit(fx.repo, f"x alone {i}")
    fx.plan.write_text(
        PLAN.format(rows="  Modify  notes/x.md", created=POST_CUTOVER), encoding="utf-8"
    )
    _commit(fx.repo, "plan")
    fx.base = _git(fx.repo, "rev-parse", "HEAD")
    _write(fx.repo, "notes/x.md", "milestone\n")


@pytest.mark.parametrize(
    ("shared", "alone", "missed"),
    [
        (5, 0, True),  # 5 shared of x's 5 commits (the milestone edit is uncommitted)
        (4, 0, False),  # 4 shared: under COCHANGE_MIN_SHARED
        (5, 5, True),  # 5 of x's 10 commits = 50%: at COCHANGE_MIN_RATIO (>=)
        (5, 6, False),  # 5 of 11 = 45%: under COCHANGE_MIN_RATIO
    ],
)
def test_cochange_boundary(tmp_path, db, shared, alone, missed) -> None:
    fx = Fixture(tmp_path, ROWS)
    _cochange_history(fx, shared, alone)
    _build(fx)
    r = fx.run()
    assert ("notes/y.md" in r.cochange_missing) is missed
    assert r.exit_code == (1 if missed else 0)


def test_explained_cochange_partner_passes(tmp_path, db) -> None:
    fx = Fixture(tmp_path, ROWS)
    _cochange_history(fx, 5, 0)
    _build(fx)
    fx.tasks_extra("- Impact-Explained: notes/y.md — y is the old copy, not touched\n")
    assert fx.run().exit_code == 0


# --- derived Critical-Path -----------------------------------------------------------------


def test_derived_critical_path_needs_a_review_naming_the_files(tmp_path, db) -> None:
    fx = Fixture(tmp_path, "  Modify  claude-code/hooks/x.sh")
    _build(fx)
    _write(fx.repo, "claude-code/hooks/x.sh", "#!/bin/sh\n")
    r = fx.run()
    assert r.exit_code == 1
    assert r.derived_critical_paths == {"hook-modification": ["claude-code/hooks/x.sh"]}
    assert r.unreviewed_critical_paths == {
        "hook-modification": ["claude-code/hooks/x.sh"]
    }
    fx.append(
        "provenance.log",
        f"[ts] CRITICAL_PATH_REVIEW — {HEADING} — hook-modification — claude-code/hooks/x.sh reviewed\n",
    )
    assert fx.run().exit_code == 0


def test_a_review_naming_the_glob_covers_its_files(tmp_path, db) -> None:
    fx = Fixture(tmp_path, "  Modify  claude-code/hooks/x.sh")
    _build(fx)
    _write(fx.repo, "claude-code/hooks/x.sh", "#!/bin/sh\n")
    fx.append(
        "provenance.log",
        f"[ts] CRITICAL_PATH_REVIEW — {HEADING} — hook-modification — claude-code/hooks/** all read\n",
    )
    assert fx.run().exit_code == 0


def test_a_review_for_another_milestone_does_not_count(tmp_path, db) -> None:
    fx = Fixture(tmp_path, "  Modify  claude-code/hooks/x.sh")
    _build(fx)
    _write(fx.repo, "claude-code/hooks/x.sh", "#!/bin/sh\n")
    fx.append(
        "provenance.log",
        "[ts] CRITICAL_PATH_REVIEW — Milestone 2: Other — hook-modification — claude-code/hooks/x.sh\n",
    )
    assert fx.run().exit_code == 1


# --- usage and codemem failures ------------------------------------------------------------


def test_unknown_base_is_usage(fx) -> None:
    r = compute(fx.plan, fx.tasks, 1, "0" * 40, ignore_cutover=True)
    assert r.exit_code == 2


def test_absent_milestone_is_usage(fx) -> None:
    r = compute(fx.plan, fx.tasks, 7, fx.base, ignore_cutover=True)
    assert r.exit_code == 2 and "Milestone 7" in r.reason


def test_index_missing_is_3_with_the_build_instruction(tmp_path, db) -> None:
    fx = Fixture(tmp_path, ROWS)  # no codemem build
    r = fx.run()
    assert r.exit_code == 3 and "codemem build" in r.reason


STUB = r"""#!{python}
import json, os, sys
with open(os.environ["STUB_LOG"], "a") as f:
    f.write(json.dumps(sys.argv[1:]) + "\n")
cmd = sys.argv[1]
if cmd == "refresh":
    sys.exit(int(os.environ.get("STUB_REFRESH_RC", "0")))
if cmd == "refresh-commits":
    sys.stderr.write(os.environ.get("STUB_COMMITS_STDERR", ""))
    sys.exit(0)
if cmd == "query":
    paths = sys.argv[sys.argv.index("--") + 1:]
    if os.environ.get("STUB_DROP"):
        paths = paths[:-1]
    stale = json.loads(os.environ.get("STUB_STALE", "false"))
    out = {{p: {{"files": [], "target": p, "target_commits": 1, "error": None,
                 "stale": stale, "stale_reason": None if stale is False else "dirty"}} for p in paths}}
    print(json.dumps(out if len(paths) != 1 else out[paths[0]]))
sys.exit(0)
"""


@pytest.fixture
def stub(tmp_path, fx, monkeypatch) -> Path:
    path = tmp_path / "codemem-stub"
    path.write_text(STUB.format(python=sys.executable), encoding="utf-8")
    path.chmod(0o755)
    log = tmp_path / "stub.log"
    monkeypatch.setenv("CODEMEM_BIN", str(path))
    monkeypatch.setenv("STUB_LOG", str(log))
    _write(fx.repo, "src/a.py", "A = 2\n")
    _write(fx.repo, "tests/test_a.py", "def test_a():\n    assert 1\n")
    return log


def _calls(log: Path) -> list[list[str]]:
    return [json.loads(line) for line in log.read_text().splitlines()]


def test_window_and_threshold_reach_codemem(fx, stub) -> None:
    assert fx.run().exit_code == 0
    calls = _calls(stub)
    commits = next(c for c in calls if c[0] == "refresh-commits")
    assert commits[commits.index("--limit") + 1] == str(COCHANGE_WINDOW_COMMITS)
    query = next(c for c in calls if c[0] == "query")
    assert query[query.index("--threshold") + 1] == str(COCHANGE_MIN_SHARED)
    assert query[query.index("--min-ratio") + 1] == str(COCHANGE_MIN_RATIO)
    assert [c[0] for c in calls][:2] == ["status", "refresh"]


def test_refresh_failure_is_3(fx, stub, monkeypatch) -> None:
    monkeypatch.setenv("STUB_REFRESH_RC", "75")
    assert fx.run().exit_code == 3


def test_skipped_commit_refresh_is_3_although_codemem_exits_0(
    fx, stub, monkeypatch
) -> None:
    monkeypatch.setenv(
        "STUB_COMMITS_STDERR",
        "codemem refresh-commits: another writer holds /x/db.lock — skipped\n",
    )
    r = fx.run()
    assert r.exit_code == 3 and "skipped" in r.reason


@pytest.mark.parametrize("stale", ["true", '"unknown"'])
def test_stale_codemem_answer_never_passes(fx, stub, monkeypatch, stale) -> None:
    monkeypatch.setenv("STUB_STALE", stale)
    r = fx.run()
    assert r.exit_code == 1 and "stale" in r.reason


# --- Cochange-Threshold override -----------------------------------------------------------


def test_threshold_override_needs_approval_and_bounds(
    tmp_path, db, monkeypatch
) -> None:
    fx = Fixture(tmp_path, ROWS, reference="Cochange-Threshold: 3 0.4\n")
    _build(fx)
    _write(fx.repo, "src/a.py", "A = 2\n")
    _write(fx.repo, "tests/test_a.py", "def test_a():\n    assert 1\n")
    r = fx.run()
    assert r.exit_code == 1 and "GATE APPROVAL" in r.reason
    fx.append(
        "context-log.md",
        f"\n## [2027-01-02] GATE APPROVAL: Cochange-Threshold 3 0.4 — {HEADING}\n- Decision: APPROVED\n",
    )
    assert fx.run().exit_code == 0
    (tmp_path / "b").mkdir()
    big = Fixture(tmp_path / "b", ROWS, reference="Cochange-Threshold: 21 0.5\n")
    assert big.run().exit_code == 2


# --- CLI -----------------------------------------------------------------------------------


def _cli(fx: Fixture, *extra: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "aa_ma.impact",
            str(fx.plan),
            str(fx.tasks),
            "--milestone",
            "1",
            "--base",
            fx.base,
            *extra,
        ],
        cwd=fx.repo,
        capture_output=True,
        text=True,
    )


def test_cli_kv_keys_and_exit_code(fx) -> None:
    _write(fx.repo, "src/b.py", "B = 2\n")
    _write(fx.repo, "src/a.py", "A = 2\n")
    _write(fx.repo, "tests/test_a.py", "def test_a():\n    assert 1\n")
    p = _cli(fx, "--ignore-cutover")
    assert p.returncode == 1, p.stderr
    kv = dict(line.split("=", 1) for line in p.stdout.splitlines() if "=" in line)
    for key in (
        "changed",
        "predicted",
        "cochange",
        "unexplained",
        "api_breaks",
        "derived_cp",
    ):
        assert key in kv
    assert (kv["changed"], kv["unexplained"]) == ("3", "1")
    assert "unexplained_file=unpredicted:src/b.py" in p.stdout


def test_cli_json_and_grandfathered(tmp_path, db) -> None:
    fx = Fixture(tmp_path, ROWS, created=GRANDFATHERED)
    _build(fx)
    p = _cli(fx, "--format", "json")
    assert p.returncode == 5
    assert json.loads(p.stdout)["exit_code"] == 5


def test_cli_usage_is_2(fx) -> None:
    p = subprocess.run(
        [sys.executable, "-m", "aa_ma.impact", "--milestone", "x"],
        capture_output=True,
        text=True,
    )
    assert p.returncode == 2


def test_entrypoint_is_declared() -> None:
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'aa-ma-impact = "aa_ma.impact:main"' in text


def test_kv_puts_every_value_on_one_line() -> None:
    lines = (
        impact.ImpactReport(exit_code=2, reason="bad\nexit_code=0").to_kv().splitlines()
    )
    assert [ln for ln in lines if ln.startswith("exit_code=")] == ["exit_code=2"]


# --- API diff (griffe, 11.4) ---------------------------------------------------------------

PKG = "def keep():\n    return 1\n\n\ndef gone():\n    return 2\n\n\ndef _private():\n    return 3\n"


def _api_fixture(tmp_path: Path, extra_rows: str = "") -> Fixture:
    fx = Fixture(tmp_path, "  Modify  src/aa_ma/__init__.py" + extra_rows)
    _write(fx.repo, "src/aa_ma/__init__.py", PKG)
    fx.base = _commit(fx.repo, "pkg")
    _build(fx)
    return fx


def test_removing_a_public_function_without_api_break_fails(tmp_path, db) -> None:
    fx = _api_fixture(tmp_path)
    _write(
        fx.repo,
        "src/aa_ma/__init__.py",
        PKG.replace("def gone():\n    return 2\n\n\n", ""),
    )
    r = fx.run()
    assert r.exit_code == 1
    assert r.api_breaks_undeclared == ["aa_ma.gone: Public object was removed"]
    assert r.api_diff == "aa_ma"


def test_a_declared_api_break_passes(tmp_path, db) -> None:
    fx = _api_fixture(tmp_path, "\nAPI-Break: aa_ma.gone — no caller left (who_calls)")
    _write(
        fx.repo,
        "src/aa_ma/__init__.py",
        PKG.replace("def gone():\n    return 2\n\n\n", ""),
    )
    r = fx.run()
    assert (r.exit_code, r.api_breaks_undeclared) == (0, [])


def test_declaring_a_module_covers_its_members(tmp_path, db) -> None:
    fx = _api_fixture(tmp_path, "\nAPI-Break: aa_ma — package reshaped")
    _write(fx.repo, "src/aa_ma/__init__.py", "def keep():\n    return 1\n")
    assert fx.run().exit_code == 0


def test_private_changes_are_not_breaks(tmp_path, db) -> None:
    fx = _api_fixture(tmp_path)
    _write(
        fx.repo,
        "src/aa_ma/__init__.py",
        PKG.replace("def _private():\n    return 3\n", ""),
    )
    r = fx.run()
    assert (r.exit_code, r.api_breaks_undeclared, r.api_diff) == (0, [], "aa_ma")


def test_no_api_package_touched_is_skipped_with_a_reason(fx) -> None:
    _write(fx.repo, "src/a.py", "A = 2\n")
    _write(fx.repo, "tests/test_a.py", "def test_a():\n    assert 1\n")
    r = fx.run()
    assert r.api_diff == "skipped(no aa_ma or codemem file changed)"


def test_unloadable_package_is_skipped_never_silent(tmp_path, db) -> None:
    fx = _api_fixture(tmp_path)
    _write(fx.repo, "src/aa_ma/__init__.py", "def keep(:\n")  # not parseable
    r = fx.run()
    assert r.api_diff.startswith("skipped(aa_ma: ") and r.api_breaks_undeclared == []


def test_package_new_at_head_has_nothing_to_break(tmp_path, db) -> None:
    fx = Fixture(tmp_path, "  Create  src/aa_ma/__init__.py")
    _build(fx)
    _write(fx.repo, "src/aa_ma/__init__.py", PKG)
    r = fx.run()
    assert r.exit_code == 0 and r.api_diff == "skipped(aa_ma: absent at base)"


def test_cli_lists_each_undeclared_break(tmp_path, db) -> None:
    fx = _api_fixture(tmp_path)
    _write(
        fx.repo,
        "src/aa_ma/__init__.py",
        PKG.replace("def gone():\n    return 2\n\n\n", ""),
    )
    p = _cli(fx, "--ignore-cutover")
    assert p.returncode == 1
    assert "api_break=aa_ma.gone: Public object was removed" in p.stdout
    assert "api_breaks=1" in p.stdout


def test_cli_without_base_still_answers_grandfathered_first(tmp_path, db) -> None:
    """Fence 4 on the default branch has no milestone window; a grandfathered plan is still 5."""
    fx = Fixture(tmp_path, ROWS, created=GRANDFATHERED)
    _build(fx)
    p = subprocess.run(
        [
            sys.executable,
            "-m",
            "aa_ma.impact",
            str(fx.plan),
            str(fx.tasks),
            "--milestone",
            "1",
        ],
        cwd=fx.repo,
        capture_output=True,
        text=True,
    )
    assert p.returncode == 5
    q = subprocess.run(
        [
            sys.executable,
            "-m",
            "aa_ma.impact",
            str(fx.plan),
            str(fx.tasks),
            "--milestone",
            "1",
            "--ignore-cutover",
        ],
        cwd=fx.repo,
        capture_output=True,
        text=True,
    )
    assert q.returncode == 2 and "--base" in q.stdout


# --- §6.6 fixes (M11 boundary) -------------------------------------------------------------


def test_lettered_milestone_number_is_read(tmp_path, db) -> None:
    """The grammar admits `2a`; --milestone must not be an int (quality W1)."""
    fx = Fixture(tmp_path, ROWS)
    fx.plan.write_text(
        PLAN.format(rows=ROWS, created=POST_CUTOVER).replace(
            "Milestone 1 — Thing", "Milestone 1a — Thing"
        )
    )
    fx.tasks.write_text(
        TASKS.format(extra="").replace(
            "## Milestone 1: Thing", "## Milestone 1a: Thing"
        )
    )
    _commit(fx.repo, "lettered")
    fx.base = _git(fx.repo, "rev-parse", "HEAD")
    _build(fx)
    _write(fx.repo, "src/a.py", "A = 2\n")
    _write(fx.repo, "tests/test_a.py", "def test_a():\n    assert 1\n")
    assert compute(fx.plan, fx.tasks, "1a", fx.base, ignore_cutover=True).exit_code == 0
    p = subprocess.run(
        [
            sys.executable,
            "-m",
            "aa_ma.impact",
            str(fx.plan),
            str(fx.tasks),
            "--milestone",
            "1a",
            "--base",
            fx.base,
            "--ignore-cutover",
        ],
        cwd=fx.repo,
        capture_output=True,
        text=True,
    )
    assert p.returncode == 0, p.stdout + p.stderr


def _hook_fixture(tmp_path: Path) -> Fixture:
    fx = Fixture(tmp_path, "  Modify  claude-code/hooks/x.sh")
    _build(fx)
    _write(fx.repo, "claude-code/hooks/x.sh", "#!/bin/sh\n")
    return fx


def test_review_is_matched_on_the_verbatim_heading(tmp_path, db) -> None:
    """A non-canonical `## M1 — Thing` heading is what the gate prints and the review names (W2)."""
    fx = _hook_fixture(tmp_path)
    fx.tasks.write_text(
        TASKS.format(extra="").replace("## Milestone 1: Thing", "## M1 — Thing")
    )
    fx.append(
        "provenance.log",
        "[ts] CRITICAL_PATH_REVIEW — M1 — Thing — hook-modification — claude-code/hooks/x.sh\n",
    )
    assert fx.run().exit_code == 0


def test_a_review_for_a_longer_heading_does_not_count(tmp_path, db) -> None:
    fx = _hook_fixture(tmp_path)
    fx.append(
        "provenance.log",
        f"[ts] CRITICAL_PATH_REVIEW — {HEADING} extra — hook-modification — claude-code/hooks/x.sh\n",
    )
    assert fx.run().exit_code == 1


def test_a_review_naming_a_longer_path_does_not_cover_the_file(tmp_path, db) -> None:
    fx = _hook_fixture(tmp_path)
    fx.append(
        "provenance.log",
        f"[ts] CRITICAL_PATH_REVIEW — {HEADING} — hook-modification — claude-code/hooks/x.sh.orig\n",
    )
    assert fx.run().exit_code == 1


def test_unreadable_provenance_is_usage_not_a_traceback(tmp_path, db) -> None:
    fx = _hook_fixture(tmp_path)
    (fx.repo / TASK / "t-provenance.log").write_bytes(b"\xff\xfe not utf-8")
    r = fx.run()
    assert r.exit_code == 2 and "provenance" in r.reason


def test_a_codemem_answer_missing_a_path_is_3(fx, stub, monkeypatch) -> None:
    monkeypatch.setenv("STUB_DROP", "1")
    r = fx.run()
    assert r.exit_code == 3 and "tests/test_a.py" in r.reason


def test_a_task_dir_linked_outside_the_repo_is_usage(tmp_path, db) -> None:
    fx = Fixture(tmp_path, ROWS, reference="x\n")
    outside = tmp_path / "elsewhere"
    (fx.repo / TASK).rename(outside)
    (fx.repo / TASK).symlink_to(outside)
    r = compute(
        fx.repo / TASK / "t-plan.md",
        fx.repo / TASK / "t-tasks.md",
        1,
        fx.base,
        ignore_cutover=True,
    )
    assert r.exit_code == 2


def test_a_directory_row_is_satisfied_by_an_excluded_change_beneath_it(
    tmp_path, db
) -> None:
    fx = Fixture(tmp_path, "  Modify  docs/")
    _build(fx)
    _write(fx.repo, "docs/architecture/c.md", "x\n")
    r = fx.run()
    assert (r.exit_code, r.predicted_unchanged) == (0, [])


def test_created_inside_a_fence_is_not_the_plan_date(fx) -> None:
    fx.plan.write_text(
        fx.plan.read_text().replace(
            f"Created: {POST_CUTOVER}\n", f"```\nCreated: {POST_CUTOVER}\n```\n"
        )
    )
    fx.base = _commit(
        fx.repo, "plan date at the base"
    )  # the merge-base copy dates the plan
    r = fx.run(ignore_cutover=False)
    assert r.exit_code == 5 and "no Created:" in r.reason


def test_a_non_executable_codemem_bin_is_3(fx, tmp_path, monkeypatch) -> None:
    bad = tmp_path / "codemem-not-x"
    bad.write_text("#!/bin/sh\n")
    monkeypatch.setenv("CODEMEM_BIN", str(bad))
    r = fx.run()
    assert r.exit_code == 3 and "CODEMEM_BIN" in r.reason
    sh = subprocess.run(
        [
            "bash",
            "-c",
            '. "$1"; aa_ma_codemem_bin "$2"',
            "_",
            str(ROOT / "claude-code/hooks/lib/aa-ma-parse.sh"),
            str(ROOT),
        ],
        capture_output=True,
        text=True,
        env={**__import__("os").environ, "CODEMEM_BIN": str(bad)},
    )
    assert sh.returncode != 0  # the shell twin refuses it too


def test_api_diff_leaves_no_worktree_or_branch_behind(tmp_path, db) -> None:
    fx = _api_fixture(tmp_path)
    before = (
        _git(fx.repo, "worktree", "list"),
        _git(fx.repo, "branch", "--list", "--all"),
    )
    _write(
        fx.repo,
        "src/aa_ma/__init__.py",
        PKG.replace("def gone():\n    return 2\n\n\n", ""),
    )
    assert fx.run().api_diff == "aa_ma"
    assert (
        _git(fx.repo, "worktree", "list"),
        _git(fx.repo, "branch", "--list", "--all"),
    ) == before


def test_kv_has_one_line_per_derived_critical_path_file(tmp_path, db) -> None:
    fx = _hook_fixture(tmp_path)
    kv = fx.run().to_kv().splitlines()
    assert "derived_cp_file=hook-modification:claude-code/hooks/x.sh" in kv


# --- §6.8 fixes (M11 boundary) -------------------------------------------------------------


def test_created_is_read_from_the_merge_base_plan(fx, monkeypatch) -> None:
    """A branch cannot back-date its own plan to skip fence 4 (security A04)."""
    monkeypatch.setattr(impact, "IMPACT_CUTOVER", "2026-01-01")
    fx.plan.write_text(
        fx.plan.read_text().replace(
            f"Created: {POST_CUTOVER}", f"Created: {GRANDFATHERED}"
        )
    )
    _write(fx.repo, "src/a.py", "A = 2\n")
    r = fx.run(ignore_cutover=False)
    assert r.exit_code != 5, r.reason


def _plan_new_on_branch(tmp_path: Path, created: str, base_date: str | None) -> Fixture:
    """A fixture whose plan is absent at the base commit (dated ``base_date``) and untracked."""
    fx = Fixture(tmp_path, ROWS)
    _git(fx.repo, "rm", "-q", "--cached", f"{TASK}/t-plan.md")
    env = {**__import__("os").environ}
    if base_date:
        env["GIT_COMMITTER_DATE"] = f"{base_date}T12:00:00Z"
    subprocess.run(  # no `add -A`: the plan stays untracked
        ["git", "commit", "-q", "-m", "plan not at base"],
        cwd=fx.repo,
        check=True,
        env=env,
    )
    fx.base = _git(fx.repo, "rev-parse", "HEAD")
    _build(fx)
    fx.plan.write_text(
        fx.plan.read_text().replace(f"Created: {POST_CUTOVER}", f"Created: {created}")
    )
    return fx


@pytest.mark.parametrize(
    ("created", "base_date", "applicable"),
    [
        (POST_CUTOVER, "2020-06-01", True),  # the working copy dates a new plan
        ("2020-01-01", "2020-06-01", False),  # before the cutover, at or after the base
        (
            "2020-01-01",
            None,
            True,
        ),  # back-dated before its base commit: base date counts
    ],
)
def test_a_plan_new_on_the_branch_is_dated_no_earlier_than_its_base(
    tmp_path, db, monkeypatch, created, base_date, applicable
) -> None:
    """A renamed task dir or a new plan cannot back-date itself past its base (§6.8 r2)."""
    monkeypatch.setattr(impact, "IMPACT_CUTOVER", "2026-01-01")
    fx = _plan_new_on_branch(tmp_path, created, base_date)
    assert (fx.run(ignore_cutover=False).exit_code != 5) is applicable


def test_a_plan_new_on_the_branch_without_created_is_dated_by_its_base(
    tmp_path, db, monkeypatch
) -> None:
    monkeypatch.setattr(impact, "IMPACT_CUTOVER", "2026-01-01")
    fx = _plan_new_on_branch(tmp_path, POST_CUTOVER, None)
    fx.plan.write_text(fx.plan.read_text().replace(f"Created: {POST_CUTOVER}\n", ""))
    assert fx.run(ignore_cutover=False).exit_code != 5


def test_a_git_failure_reading_the_base_plan_is_usage(fx, monkeypatch) -> None:
    """Only "absent at the base" falls back to the working copy; any other error stops."""
    real = impact.gitutil.git

    def failing_show(args, repo, *a, **kw):
        if args[0] == "show":
            raise impact.gitutil.GitError("boom", args, 128, "boom")
        return real(args, repo, *a, **kw)

    monkeypatch.setattr(impact.gitutil, "git", failing_show)
    r = fx.run(ignore_cutover=False)
    assert r.exit_code == 2 and "boom" in r.reason


def test_a_skipped_api_diff_logs_its_reason_sanitised(tmp_path, caplog) -> None:
    class Griffe:
        @staticmethod
        def load(*_a, **_kw):
            raise ValueError("bad \x1b[31mname\u202e here")

    with caplog.at_level("WARNING", logger="aa_ma.impact"):
        reason = impact._breaks(Griffe, "aa_ma", tmp_path, tmp_path)
    assert "\x1b" in reason  # the kv value is sanitised by its consumer, not here
    assert "\x1b" not in caplog.text and "\u202e" not in caplog.text
    assert "bad ?[31mname? here" in caplog.text


def test_a_review_marker_quoted_mid_line_does_not_count(tmp_path, db) -> None:
    fx = _hook_fixture(tmp_path)
    fx.append(
        "provenance.log",
        f"note: see [ts] CRITICAL_PATH_REVIEW — {HEADING} — hook-modification — claude-code/hooks/x.sh\n",
    )
    assert fx.run().exit_code == 1


def test_tarfile_without_the_data_filter_is_skipped_not_a_crash(
    tmp_path, db, monkeypatch
) -> None:
    """Python 3.11.0–3.11.3 has no extractall(filter=): TypeError → skipped(reason)."""
    fx = _api_fixture(tmp_path)
    _write(
        fx.repo,
        "src/aa_ma/__init__.py",
        PKG.replace("def gone():\n    return 2\n\n\n", ""),
    )

    def old_extractall(self, path=".", members=None, *, numeric_owner=False):
        raise TypeError("extractall() got an unexpected keyword argument 'filter'")

    monkeypatch.setattr(impact.tarfile.TarFile, "extractall", old_extractall)
    r = fx.run()
    assert r.api_diff.startswith("skipped(") and "TypeError" in r.api_diff


def test_api_packages_are_the_workspace_packages() -> None:
    """A new workspace member must not silently escape the public-API diff (P6)."""
    import tomllib

    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    want = {"aa_ma": "src"}
    for member in project["tool"]["uv"]["workspace"]["members"]:
        src = ROOT / member / "src"
        want |= {
            p.name: f"{member}/src"
            for p in src.iterdir()
            if (p / "__init__.py").is_file()
        }
    assert impact.API_PACKAGES == want
