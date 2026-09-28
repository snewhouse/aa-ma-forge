"""measure(): tools measure, never guess. Absent → absent, failed → unknown, never a zero (M2 AC2,
AC10, AC12); rows, argv and parse shapes as confirmed by the 2.1 prototype (§5a, amended)."""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

import pytest

from aa_ma.analysis import cli
from aa_ma.analysis.measure import measure
from aa_ma.analysis.stamp import REPORTS_ROOT, UnsafePath

from .conftest import CODEMEM, FAKE_TOKEN, commit_file, git, stub_bin

NETWORK_TOOLS = ("semgrep", "osv-scanner", "pip-audit")
CODEMEM_INPUTS = (
    "codemem.hot_spots",
    "codemem.co_changes",
    "codemem.owners",
    "codemem.layers",
    "codemem.dead_code",
)


def lizard_row(
    fn: str, ccn: int, start: int, end: int, path: str = "src/calc.py"
) -> str:
    return f'2,{ccn},10,1,2,"{fn}@{start}-{end}@{path}","{path}","{fn}","{fn}( x )",{start},{end}\n'


def doc(work: Path) -> dict:
    return json.loads((work / "measure.json").read_text(encoding="utf-8"))


def by_rule(d: dict, rule: str) -> list[dict]:
    return [f for f in d["measured"] if f["rule"] == rule]


def lizard_stub(stubs: Path, monkeypatch: pytest.MonkeyPatch, csv: str) -> Path:
    report = stubs / "lizard.csv"
    report.write_text(csv, encoding="utf-8")
    monkeypatch.setenv("LIZARD_BIN", str(stub_bin(stubs, "lizard", f"cat '{report}'")))
    return report


# --- work dir -------------------------------------------------------------------------------------


def test_work_dir_sits_under_a_self_ignoring_reports_root(
    target: Path, tools: Path
) -> None:
    work = measure(target, "quick")
    assert (
        work == target / REPORTS_ROOT / f".work-{git(target, 'rev-parse', 'HEAD')[:12]}"
    )
    assert (target / REPORTS_ROOT / ".gitignore").read_text() == "*\n"
    assert git(target, "status", "--porcelain") == ""
    assert (work / "measure.json").is_file() and (work / "run.log").is_file()


def test_symlinked_reports_root_is_refused(
    target: Path, tools: Path, tmp_path: Path
) -> None:
    (tmp_path / "elsewhere").mkdir()
    (target / ".claude").mkdir()
    os.symlink(tmp_path / "elsewhere", target / ".claude" / "reports")
    with pytest.raises(UnsafePath):
        measure(target, "quick")
    assert list((tmp_path / "elsewhere").iterdir()) == []


def test_cli_prints_the_work_dir(
    target: Path, tools: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert cli.main(["measure", "--repo", str(target), "--tier", "quick"]) == 0
    assert Path(capsys.readouterr().out.strip()) == measure(target, "quick")


def test_cli_outside_a_git_repo_is_a_precondition_error(
    tmp_path: Path, tools: Path
) -> None:
    assert cli.main(["measure", "--repo", str(tmp_path), "--tier", "quick"]) == 2


def test_quick_and_standard_skip_network_tools(target: Path, tools: Path) -> None:
    for tier in ("quick", "standard"):
        status = doc(measure(target, tier))["stamp"]["tools"]
        assert {status[t] for t in NETWORK_TOOLS} == {"skipped"}


def test_git_size_metrics_per_top_level_dir(target: Path, tools: Path) -> None:
    metrics = doc(measure(target, "quick"))["metrics"]
    assert metrics["size.files:src"] == 2
    assert metrics["size.files:."] == 1
    assert metrics["size.bytes:src"] > 0
    assert metrics["churn.90d:src"] > 0


# --- AC2: absent / unknown / ran, never a zero ----------------------------------------------------


def _complexity(metrics: dict) -> dict:
    return {k: v for k, v in metrics.items() if k.startswith("complexity.")}


def test_absent_lizard_is_absent_and_measures_nothing(
    target: Path, tools: Path
) -> None:
    d = doc(measure(target, "quick"))
    assert d["stamp"]["tools"]["lizard"] == "absent"
    assert _complexity(d["metrics"]) and set(_complexity(d["metrics"]).values()) == {
        None
    }
    assert by_rule(d, "maint.complexity") == []


def test_lizard_failing_without_a_report_is_unknown(
    target: Path, tools: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("LIZARD_BIN", str(stub_bin(tools, "lizard", "exit 3")))
    d = doc(measure(target, "quick"))
    assert d["stamp"]["tools"]["lizard"] == "unknown"
    assert set(_complexity(d["metrics"]).values()) == {None}


def test_lizard_with_a_valid_report_ran(
    target: Path, tools: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    lizard_stub(
        tools,
        monkeypatch,
        lizard_row("f1", 20, 1, 2)
        + lizard_row("f2", 30, 5, 6)
        + lizard_row("g", 5, 1, 1, "README.md"),
    )
    d = doc(measure(target, "quick"))
    assert d["stamp"]["tools"]["lizard"] == "ran"
    found = sorted(
        (f["line"], f["severity"], f["anchor"], f["origin"])
        for f in by_rule(d, "maint.complexity")
    )
    assert found == [
        (1, "medium", "def f1(x):", "measured"),
        (5, "high", "def f2(y):", "measured"),
    ]
    assert d["metrics"]["complexity.over_15"] == 2
    assert d["metrics"]["complexity.ccn_max"] == 30
    assert all(f["id"].startswith("F-") for f in d["measured"])


# --- jscpd ----------------------------------------------------------------------------------------


def test_jscpd_reports_code_clones_only_and_never_copies_the_fragment(
    target: Path, tools: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    clone = {
        "format": "python",
        "fragment": "FRAGMENT-TEXT-MUST-NOT-LEAK",
        "lines": 2,
        "tokens": 10,
        "firstFile": {"name": "src/calc.py:python", "startLoc": {"line": 5}},
        "secondFile": {"name": "src/calc.py:python", "startLoc": {"line": 1}},
    }
    prose = {
        **clone,
        "format": "markdown",
        "firstFile": {"name": "README.md:markdown", "startLoc": {"line": 1}},
    }
    report = tools / "jscpd.json"
    report.write_text(
        json.dumps(
            {"duplicates": [clone, prose], "statistics": {"total": {"percentage": 3.5}}}
        )
    )
    body = f'while [ $# -gt 0 ]; do [ "$1" = --output ] && out=$2; shift; done\nmkdir -p "$out"\ncp \'{report}\' "$out/jscpd-report.json"'
    monkeypatch.setenv("JSCPD_BIN", str(stub_bin(tools, "jscpd", body)))
    work = measure(target, "quick")
    d = doc(work)
    assert d["stamp"]["tools"]["jscpd"] == "ran"
    assert [
        (f["path"], f["line"], f["severity"], f["anchor"])
        for f in by_rule(d, "maint.duplication")
    ] == [("src/calc.py", 5, "low", "def f2(y):")]
    assert d["metrics"]["duplication.pct"] == 3.5
    assert "FRAGMENT-TEXT-MUST-NOT-LEAK" not in (work / "measure.json").read_text()


# --- secrets --------------------------------------------------------------------------------------


def test_regex_secret_finding_never_carries_the_secret(
    target: Path, tools: Path
) -> None:
    work = measure(target, "quick")
    [f] = by_rule(doc(work), "security.secret")
    assert (f["path"], f["line"], f["severity"], f["anchor"]) == (
        "src/config.py",
        1,
        "high",
        "github-token",
    )
    assert FAKE_TOKEN not in (work / "measure.json").read_text()


def _gitleaks_stub(tools: Path, leaks: list[dict], rc: int = 0) -> Path:
    report = tools / "gl.json"
    report.write_text(json.dumps(leaks))
    body = f'while [ $# -gt 0 ]; do [ "$1" = -r ] && out=$2; shift; done\ncp \'{report}\' "$out"\nexit {rc}'
    return stub_bin(tools, "gitleaks", body)


def test_gitleaks_hit_wins_over_the_regex_hit_on_the_same_line(
    target: Path, tools: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    leak = {
        "File": "src/config.py",
        "StartLine": 1,
        "RuleID": "github-pat",
        "Secret": "REDACTED",
        "Match": "REDACTED",
    }
    monkeypatch.setenv("GITLEAKS_BIN", str(_gitleaks_stub(tools, [leak])))
    d = doc(measure(target, "quick"))
    assert d["stamp"]["tools"]["gitleaks"] == "ran"
    assert [(f["path"], f["anchor"]) for f in by_rule(d, "security.secret")] == [
        ("src/config.py", "github-pat")
    ]


def test_gitleaks_nonzero_exit_is_unknown(
    target: Path, tools: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("GITLEAKS_BIN", str(_gitleaks_stub(tools, [], rc=1)))
    d = doc(measure(target, "quick"))
    assert d["stamp"]["tools"]["gitleaks"] == "unknown"
    assert len(by_rule(d, "security.secret")) == 1  # the built-in regex set always runs


# --- Deep: network tools --------------------------------------------------------------------------


def test_semgrep_severity_map_covers_both_scales(
    target: Path, tools: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    results = [
        {
            "check_id": f"r.{sev}",
            "path": "src/calc.py",
            "start": {"line": 1},
            "extra": {"severity": sev, "lines": "x"},
        }
        for sev in ("ERROR", "CRITICAL", "HIGH", "WARNING", "MEDIUM", "INFO", "LOW")
    ]
    report = tools / "sg.json"
    report.write_text(json.dumps({"results": results, "errors": [{"level": "warn"}]}))
    monkeypatch.setenv(
        "SEMGREP_BIN", str(stub_bin(tools, "semgrep", f"cat '{report}'"))
    )
    d = doc(measure(target, "deep"))
    assert d["stamp"]["tools"]["semgrep"] == "ran"
    got = {f["anchor"]: f["severity"] for f in by_rule(d, "security.sast")}
    assert got == {
        "r.ERROR": "high",
        "r.CRITICAL": "high",
        "r.HIGH": "high",
        "r.WARNING": "medium",
        "r.MEDIUM": "medium",
        "r.INFO": "low",
        "r.LOW": "low",
    }


def _osv_report(target: Path) -> dict:
    def vuln(vid: str, fixed: bool) -> dict:
        events = [{"introduced": "0"}] + ([{"fixed": "9.9"}] if fixed else [])
        return {
            "id": vid,
            "affected": [{"ranges": [{"type": "ECOSYSTEM", "events": events}]}],
        }

    return {
        "results": [
            {
                "source": {"path": str(target / "uv.lock"), "type": "lockfile"},
                "packages": [
                    {
                        "package": {
                            "name": "anyio",
                            "version": "4.0",
                            "ecosystem": "PyPI",
                        },
                        "vulnerabilities": [
                            vuln("GHSA-1", True),
                            vuln("GHSA-2", False),
                        ],
                    }
                ],
            }
        ]
    }


def test_osv_vulns_found_exit_1_is_ran_with_relative_paths(
    target: Path, tools: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    report = tools / "osv.json"
    report.write_text(json.dumps(_osv_report(target)))
    monkeypatch.setenv(
        "OSV_SCANNER_BIN",
        str(stub_bin(tools, "osv-scanner", f"cat '{report}'\nexit 1")),
    )
    d = doc(measure(target, "deep"))
    assert d["stamp"]["tools"]["osv-scanner"] == "ran"
    got = sorted(
        (f["path"], f["anchor"], f["severity"], f["dimension"])
        for f in by_rule(d, "deps.vuln")
    )
    assert got == [
        ("uv.lock", "anyio@4.0:GHSA-1", "high", "tests_deps"),
        ("uv.lock", "anyio@4.0:GHSA-2", "medium", "tests_deps"),
    ]


def test_osv_no_packages_exit_128_is_ran_with_zero(
    target: Path, tools: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv(
        "OSV_SCANNER_BIN", str(stub_bin(tools, "osv-scanner", "exit 128"))
    )
    d = doc(measure(target, "deep"))
    assert d["stamp"]["tools"]["osv-scanner"] == "ran"
    assert d["metrics"]["deps.vulns"] == 0


def test_pip_audit_runs_no_deps_per_requirements_file(
    target: Path, tools: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    commit_file(target, "requirements.txt", "jinja2==3.1.2\n")
    argv_log = tools / "pa.argv"
    report = {
        "dependencies": [
            {
                "name": "jinja2",
                "version": "3.1.2",
                "vulns": [{"id": "PYSEC-1", "fix_versions": ["3.1.3"], "aliases": []}],
            }
        ],
        "fixes": [],
    }
    (tools / "pa.json").write_text(json.dumps(report))
    body = f"echo \"$@\" > '{argv_log}'\ncat '{tools / 'pa.json'}'\nexit 1"
    monkeypatch.setenv("PIP_AUDIT_BIN", str(stub_bin(tools, "pip-audit", body)))
    d = doc(measure(target, "deep"))
    assert d["stamp"]["tools"]["pip-audit"] == "ran"
    assert argv_log.read_text().split() == [
        "-f",
        "json",
        "--no-deps",
        "--disable-pip",
        "-r",
        "requirements.txt",
    ]
    assert [
        (f["path"], f["anchor"], f["severity"]) for f in by_rule(d, "deps.vuln")
    ] == [("requirements.txt", "jinja2@3.1.2:PYSEC-1", "high")]


def test_pip_audit_without_requirements_is_skipped(
    target: Path, tools: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("PIP_AUDIT_BIN", str(stub_bin(tools, "pip-audit", "exit 0")))
    assert doc(measure(target, "deep"))["stamp"]["tools"]["pip-audit"] == "skipped"


# --- AC10: bounded runtime + trail ----------------------------------------------------------------


def test_tool_timeout_marks_only_that_input_unknown_and_run_log_holds_no_output(
    target: Path, tools: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv(
        "LIZARD_BIN", str(stub_bin(tools, "lizard", f"echo {FAKE_TOKEN}\nsleep 30"))
    )
    t0 = time.monotonic()
    work = measure(target, "quick", tool_timeout=1)
    assert time.monotonic() - t0 < 15
    status = doc(work)["stamp"]["tools"]
    assert status["lizard"] == "unknown"
    assert status["jscpd"] == "absent"
    log = (work / "run.log").read_text()
    assert FAKE_TOKEN not in log
    names = [line.split("\t")[0] for line in log.splitlines()]
    assert set(status) <= set(names)
    assert all(
        len(line.split("\t")) == 5 for line in log.splitlines()
    )  # name, argv, rc, secs, status


# --- AC12: the codemem seam -----------------------------------------------------------------------


EMPTY_TOOL_JSON = json.dumps(
    {
        "files": [],
        "symbols": [],
        "authors": [],
        "layers": {"core": [], "middle": [], "periphery": []},
        "truncated": False,
        "error": None,
    }
)


def test_every_codemem_call_uses_the_work_db_and_the_target_cwd(
    target: Path, tools: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls = tools / "codemem.calls"
    body = (
        f"echo \"$PWD|$*\" >> '{calls}'\n"
        'case "$*" in *refresh-commits*) echo "codemem refresh-commits: inserted 0 commits";; '
        f"*query*) echo '{EMPTY_TOOL_JSON}';; *) echo built;; esac"
    )
    monkeypatch.setenv("CODEMEM_BIN", str(stub_bin(tools, "codemem", body)))
    work = measure(target, "quick")
    lines = calls.read_text().splitlines()
    assert lines
    for line in lines:
        cwd, args = line.split("|", 1)
        assert Path(cwd).resolve() == target.resolve()
        assert args.split()[:2] == ["--db", str(work / "codemem.db")]
    status = doc(work)["stamp"]["tools"]
    # zero commit rows → the git-history inputs are unknown, never zero
    assert {
        status[t] for t in ("codemem.hot_spots", "codemem.co_changes", "codemem.owners")
    } == {"unknown"}


def test_absent_codemem_makes_every_codemem_input_unknown(
    target: Path, tools: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("CODEMEM_BIN", "/nonexistent")
    d = doc(measure(target, "quick"))
    assert {d["stamp"]["tools"][t] for t in CODEMEM_INPUTS} == {"unknown"}
    assert d["metrics"]["dead_code.candidates"] is None


def test_real_codemem_run_measures_and_never_touches_a_committed_index(
    target: Path, tools: Path
) -> None:
    fake = target / ".codemem" / "index.db"
    fake.parent.mkdir()
    fake.write_bytes(b"PLANTED - not a database")
    git(target, "add", "-A")
    git(target, "commit", "-q", "-m", "planted index")
    before = (fake.read_bytes(), fake.stat().st_mtime_ns)
    work = measure(target, "quick")
    assert (fake.read_bytes(), fake.stat().st_mtime_ns) == before
    d = doc(work)
    assert {d["stamp"]["tools"][t] for t in CODEMEM_INPUTS} == {"ran"}
    m = d["metrics"]
    assert isinstance(m["layers.core"], int) and isinstance(
        m["dead_code.candidates"], int
    )
    assert m["owners.authors:src/"] == 1
    assert any(k.startswith("hot_spot:") for k in m)
    assert "fixture@example.invalid" not in (work / "measure.json").read_text()
    assert CODEMEM.exists()
