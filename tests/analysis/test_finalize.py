"""finalize(): work dir → the versioned report set (M2 AC1, AC3–AC5, AC8, AC9, AC11 + §5a rules).

Every test drives the real measure() on the fixture target with stub tools, then plays the main
thread / judge agents by writing ratings.json, ledger.json and judged.jsonl into the work dir."""

from __future__ import annotations

import json
import os
from collections import Counter
from pathlib import Path

import pytest
from jsonschema import Draft4Validator

from aa_ma.analysis import cli, finalize as finalize_mod
from aa_ma.analysis.finalize import FinalizeError, finalize
from aa_ma.analysis.ids import compare
from aa_ma.analysis.measure import measure
from aa_ma.analysis.models import Dimension, Finding, Summary
from aa_ma.analysis.stamp import REPORTS_ROOT

from .conftest import FAKE_TOKEN, commit_file, git, stub_bin

ROOT = Path(__file__).resolve().parents[2]
SARIF_SCHEMA = json.loads(
    (ROOT / "tests/fixtures/sarif/sarif-schema-2.1.0.json").read_text(encoding="utf-8")
)
F1 = '2,20,10,1,2,"f1@1-2@src/calc.py","src/calc.py","f1","f1( x )",1,2\n'
F2 = '2,30,10,1,2,"f2@5-6@src/calc.py","src/calc.py","f2","f2( y )",5,6\n'


@pytest.fixture
def lizard(tools: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A lizard stub reporting whatever the returned CSV file holds (f1 and f2 by default)."""
    report = tools / "lizard.csv"
    report.write_text(F1 + F2, encoding="utf-8")
    monkeypatch.setenv("LIZARD_BIN", str(stub_bin(tools, "lizard", f"cat '{report}'")))
    return report


def judged(**overrides: object) -> dict:
    base = {
        "schema_version": 1,
        "origin": "judged",
        "dimension": "architecture",
        "severity": "medium",
        "confidence": "med",
        "rule": "arch.layering",
        "title": "calc reaches into config",
        "path": "src/calc.py",
        "line": 1,
        "anchor": "def f1(x):",
        "refutation": "not_required",
        "evidence": "src/calc.py:1",
    }
    return base | overrides


def ratings(**by_dim: str) -> list[dict]:
    return [
        {
            "dimension": d.value,
            "rating": by_dim.get(d.value, "adequate"),
            "confidence": "med",
            "inputs": [],
            "capped": False,
        }
        for d in Dimension
    ]


def prepare(
    target: Path,
    *,
    judged_lines: list[str] | None = None,
    rate: list[dict] | None = None,
) -> Path:
    work = measure(target, "quick")
    (work / "ratings.json").write_text(json.dumps(rate or ratings()))
    (work / "ledger.json").write_text(
        json.dumps([{"path": "src", "status": "assessed", "reason": "source"}])
    )
    (work / "judged.jsonl").write_text(
        "".join(line + "\n" for line in (judged_lines or []))
    )
    return work


def run(target: Path, **kw) -> Path:
    return finalize(target, prepare(target, **kw))


def findings(report: Path) -> list[Finding]:
    return [
        Finding.model_validate_json(line)
        for line in (report / "findings.jsonl").read_text().splitlines()
    ]


def summary(report: Path) -> Summary:
    return Summary.model_validate_json((report / "summary.json").read_text())


def sarif(report: Path) -> dict:
    return json.loads((report / "findings.sarif").read_text())


# --- AC1: deterministic measured IDs; every output validates --------------------------------------


def test_two_runs_at_one_commit_give_identical_measured_ids_and_valid_outputs(
    target: Path, lizard: Path
) -> None:
    first = {f.id for f in findings(run(target)) if f.origin == "measured"}
    report = run(target)
    second = {f.id for f in findings(report) if f.origin == "measured"}
    assert first == second and len(first) == 3  # f1, f2, the config secret
    summary(report)
    Draft4Validator(SARIF_SCHEMA).validate(sarif(report))
    assert {
        r["fingerprints"]["aaMaFindingId/v1"]
        for r in sarif(report)["runs"][0]["results"]
    } == second
    assert (report / "report.md").is_file() and (report / "run.log").is_file()
    assert all(d.value in (report / "report.md").read_text() for d in Dimension)


# --- AC3: report dir naming -----------------------------------------------------------------------


def test_report_dir_is_sha12_clean_and_dirty_with_an_edit_and_is_replaced(
    target: Path, lizard: Path
) -> None:
    sha12 = git(target, "rev-parse", "HEAD")[:12]
    root = target / REPORTS_ROOT
    report = run(target)
    assert report == root / sha12
    (report / "stale-marker.md").write_text("old run\n")
    assert run(target) == report and not (report / "stale-marker.md").exists()
    (target / "src/calc.py").write_text("def f1(x):\n    return 2\n")
    assert run(target) == root / f"{sha12}-dirty"
    assert (root / ".gitignore").read_text() == "*\n"
    assert git(target, "status", "--porcelain") == "M src/calc.py"


# --- AC4: a quoted secret never reaches an output file --------------------------------------------


def test_secret_quoted_by_a_judged_finding_never_reaches_any_output(
    target: Path, lizard: Path
) -> None:
    line = json.dumps(
        judged(
            path="src/config.py",
            anchor=f'TOKEN = "{FAKE_TOKEN}"',
            evidence=f"leaks {FAKE_TOKEN}",
        )
    )
    report = run(target, judged_lines=[line])
    for f in report.rglob("*"):
        if f.is_file():
            assert FAKE_TOKEN not in f.read_text(errors="replace"), f
    [j] = [f for f in findings(report) if f.origin == "judged"]
    assert j.redacted is True
    n = summary(report).counts.redacted
    assert n >= 1
    assert (
        f"{n} redacted" in (report / "report.md").read_text()
    )  # rendered after the gate


# --- AC5: baseline --------------------------------------------------------------------------------


def test_deleting_a_flagged_function_makes_its_finding_fixed(
    target: Path, lizard: Path
) -> None:
    previous = [f.id for f in findings(run(target))]
    commit_file(target, "src/calc.py", "def f1(x):\n    return x\n", "drop f2")
    lizard.write_text(F1)
    report = run(target)
    current = [f.id for f in findings(report)]
    expected = {"new": 0, "persisting": 0, "fixed": 0} | Counter(
        compare(previous, current).values()
    )
    assert (
        summary(report).baseline.model_dump()
        == expected
        == {"new": 0, "persisting": 2, "fixed": 1}
    )
    states = Counter(
        r.get("baselineState") for r in sarif(report)["runs"][0]["results"]
    )
    assert states == {"unchanged": expected["persisting"], "absent": expected["fixed"]}


def test_rerun_at_the_same_commit_compares_against_the_report_it_replaces(
    target: Path, lizard: Path
) -> None:
    run(target)
    report = run(target)
    assert summary(report).baseline.model_dump() == {
        "new": 0,
        "persisting": 3,
        "fixed": 0,
    }


# --- §5a rules: refutation, confidence cap, rating cap --------------------------------------------


def test_refuted_findings_are_dropped_and_counted(target: Path, lizard: Path) -> None:
    lines = [
        json.dumps(judged(severity="high", refutation="refuted")),
        json.dumps(judged(title="kept", anchor="def f2(y):")),
    ]
    report = run(target, judged_lines=lines)
    assert [f.title for f in findings(report) if f.origin == "judged"] == ["kept"]
    assert summary(report).counts.refuted == 1


def test_judged_medium_and_low_confidence_is_capped_at_med(
    target: Path, lizard: Path
) -> None:
    lines = [
        json.dumps(judged(severity="low", confidence="high")),
        json.dumps(
            judged(
                severity="high",
                confidence="high",
                refutation="survived",
                anchor="def f2(y):",
            )
        ),
    ]
    got = {
        f.severity: f.confidence
        for f in findings(run(target, judged_lines=lines))
        if f.origin == "judged"
    }
    assert got == {"low": "med", "high": "high"}


def test_a_dimension_whose_core_input_did_not_run_cannot_be_strong(
    target: Path, tools: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    report = run(
        target, rate=ratings(maintainability="strong", architecture="strong")
    )  # lizard absent
    dims = {d.dimension: d for d in summary(report).dimensions}
    assert (dims["maintainability"].rating, dims["maintainability"].capped) == (
        "adequate",
        True,
    )
    assert (dims["architecture"].rating, dims["architecture"].capped) == (
        "strong",
        False,
    )  # codemem ran


# --- AC8: pending refutation blocks ---------------------------------------------------------------


def test_pending_high_finding_blocks_finalize_naming_its_id(
    target: Path, lizard: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    work = prepare(
        target,
        judged_lines=[json.dumps(judged(severity="critical", refutation="pending"))],
    )
    assert cli.main(["finalize", "--repo", str(target), "--work", str(work)]) == 1
    err = capsys.readouterr().err
    assert "F-" in err and "pending" in err and str(work) in err


# --- AC9: untrusted judged input ------------------------------------------------------------------


@pytest.mark.parametrize("bad_path", ["/etc/passwd", "../../etc/x", "escape/x"])
def test_judged_path_outside_the_repo_is_rejected_naming_the_line(
    target: Path, lizard: Path, tmp_path: Path, bad_path: str
) -> None:
    work = prepare(
        target, judged_lines=[json.dumps(judged()), json.dumps(judged(path=bad_path))]
    )
    os.symlink(
        tmp_path, target / "escape"
    )  # after measure; untracked, so the tree stays clean
    with pytest.raises(FinalizeError, match=r"judged\.jsonl:2"):
        finalize(target, work)


def test_malformed_judged_line_is_rejected_naming_the_line(
    target: Path, lizard: Path
) -> None:
    with pytest.raises(FinalizeError, match=r"judged\.jsonl:3"):
        finalize(
            target,
            prepare(
                target,
                judged_lines=[
                    json.dumps(judged()),
                    json.dumps(judged(anchor="x")),
                    "{not json",
                ],
            ),
        )


def test_missing_ratings_is_refused(target: Path, lizard: Path) -> None:
    work = prepare(target)
    (work / "ratings.json").unlink()
    with pytest.raises(FinalizeError, match="ratings.json"):
        finalize(target, work)


def test_work_dir_outside_the_reports_root_is_refused(
    target: Path, tmp_path: Path
) -> None:
    with pytest.raises(FinalizeError):
        finalize(target, tmp_path)


# --- AC11: the work dir lifecycle -----------------------------------------------------------------


def test_success_removes_the_work_dir_and_failure_keeps_it(
    target: Path, lizard: Path
) -> None:
    work = prepare(target)
    finalize(target, work)
    assert not work.exists()
    work = prepare(target, judged_lines=["{bad"])
    with pytest.raises(FinalizeError):
        finalize(target, work)
    assert (work / "measure.json").is_file()


def test_crash_before_rename_leaves_no_report_and_keeps_the_work_dir(
    target: Path, lizard: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    previous = run(target)
    before = {p.name: p.read_bytes() for p in previous.iterdir()}
    commit_file(target, "src/calc.py", "def f1(x):\n    return x\n", "drop f2")
    work = prepare(target)
    monkeypatch.setenv("AA_MA_FINALIZE_CRASH_BEFORE_RENAME", "1")
    with pytest.raises(FinalizeError):
        finalize(target, work)
    assert not (target / REPORTS_ROOT / git(target, "rev-parse", "HEAD")[:12]).exists()
    assert {p.name: p.read_bytes() for p in previous.iterdir()} == before
    assert work.is_dir()
    assert sorted(p.name for p in (target / REPORTS_ROOT).iterdir()) == sorted(
        [".gitignore", previous.name, work.name]
    )


def test_cli_finalize_prints_the_report_dir(
    target: Path, lizard: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    work = prepare(target)
    assert cli.main(["finalize", "--repo", str(target), "--work", str(work)]) == 0
    assert (
        Path(capsys.readouterr().out.strip())
        == target / REPORTS_ROOT / git(target, "rev-parse", "HEAD")[:12]
    )


# --- §6.8 remediation (sub-step 2.8) ----------------------------------------------------------------


def _hostile_report(
    root: Path,
    name: str,
    findings_target: Path | None,
    when: str = "2099-01-01T00:00:00Z",
) -> Path:
    """A report dir a hostile target can plant: far-future stamp, findings.jsonl maybe a symlink."""
    d = root / name
    d.mkdir(parents=True)
    stamp = {
        "date_utc": when,
        "sha12": "0" * 12,
        "dirty": False,
        "branch": "x",
        "tier": "quick",
        "tools": {},
        "absorbed": [],
        "fresh_run": [],
    }
    doc = {
        "schema_version": 1,
        "stamp": stamp,
        "dimensions": ratings(),
        "ledger": [],
        "metrics": {},
        "counts": {},
        "baseline": {},
    }
    (d / "summary.json").write_text(json.dumps(doc))
    if findings_target is None:
        fake = judged(title="planted fixed finding") | {
            "id": "F-" + "a" * 12,
            "origin": "judged",
            "redacted": False,
        }
        (d / "findings.jsonl").write_text(json.dumps(fake) + "\n")
    else:
        os.symlink(findings_target, d / "findings.jsonl")
    return d


@pytest.mark.parametrize("committed", [True, False])
def test_a_symlinked_previous_report_is_never_read_or_echoed(
    target: Path,
    lizard: Path,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    committed: bool,
) -> None:
    outside = tmp_path / "outside.txt"
    outside.write_text("OUTSIDE-TEXT-" + "Z" * 40 + "\n")
    _hostile_report(target / REPORTS_ROOT, "0123456789ab", outside)
    if committed:
        git(target, "add", "-f", "-A")
        git(target, "commit", "-q", "-m", "planted report")
    work = prepare(target)
    assert cli.main(["finalize", "--repo", str(target), "--work", str(work)]) == 0
    out = capsys.readouterr()
    assert "OUTSIDE-TEXT" not in out.out + out.err
    report = Path(out.out.strip())
    assert summary(report).baseline.persisting == 0


def test_a_committed_report_dir_is_not_a_baseline(target: Path, lizard: Path) -> None:
    """A far-future planted report would otherwise win the newest-report pick and fake 'fixed'."""
    _hostile_report(target / REPORTS_ROOT, "0123456789ab", None)
    git(target, "add", "-f", "-A")
    git(target, "commit", "-q", "-m", "planted report")
    report = run(target)
    assert summary(report).baseline.fixed == 0
    assert "planted fixed finding" not in (report / "findings.sarif").read_text()


def test_a_future_dated_previous_report_is_ignored(target: Path, lizard: Path) -> None:
    _hostile_report(
        target / REPORTS_ROOT, "0123456789ab", None
    )  # untracked, stamp in 2099
    assert summary(run(target)).baseline.fixed == 0


def test_a_corrupt_previous_report_is_skipped(target: Path, lizard: Path) -> None:
    first = run(target)
    (first / "findings.jsonl").write_text("{not json\n")
    commit_file(target, "src/other.py", "x = 1\n", "next")
    assert summary(run(target)).baseline.model_dump() == {
        "new": 3,
        "persisting": 0,
        "fixed": 0,
    }


def test_a_failed_rename_restores_the_previous_report(
    target: Path, lizard: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    previous = run(target)
    before = {p.name: p.read_bytes() for p in previous.iterdir()}
    real_rename = os.rename

    def failing(
        src, dst
    ):  # the new report's rename fails after the old one moved aside
        if Path(src).name.startswith(".tmp-"):
            raise OSError("disk full")
        return real_rename(src, dst)

    monkeypatch.setattr(finalize_mod.os, "rename", failing)
    with pytest.raises(FinalizeError):
        finalize(target, prepare(target))
    assert {p.name: p.read_bytes() for p in previous.iterdir()} == before
    assert not [
        p
        for p in (target / REPORTS_ROOT).iterdir()
        if p.name.startswith((".old-", ".tmp-"))
    ]


def test_a_gate_error_never_echoes_report_text(
    target: Path, lizard: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def corrupt(
        root: Path, hits
    ) -> int:  # a redaction that breaks a line, leaving a secret in it
        (root / "findings.jsonl").write_text(json.dumps({"x": FAKE_TOKEN}) + "\n")
        return 1

    monkeypatch.setattr(finalize_mod.secrets, "redact", corrupt)
    with pytest.raises(FinalizeError) as exc:
        quoted = json.dumps(
            judged(evidence=f"leaks {FAKE_TOKEN}")
        )  # gives the gate a hit
        finalize(target, prepare(target, judged_lines=[quoted]))
    assert FAKE_TOKEN not in str(exc.value)


def test_the_report_dir_holds_exactly_the_report_files(
    target: Path, lizard: Path
) -> None:
    assert sorted(p.name for p in run(target).iterdir()) == sorted(
        finalize_mod.REPORT_FILES
    )


def test_a_colon_inside_a_path_is_a_valid_sarif_uri(target: Path, lizard: Path) -> None:
    commit_file(target, "src/a:b.py", "x = 1\n")
    report = run(target, judged_lines=[json.dumps(judged(path="src/a:b.py"))])
    assert "src/a:b.py" in (report / "findings.sarif").read_text()


def test_report_name_is_the_one_naming_rule() -> None:
    from aa_ma.analysis.stamp import report_name

    assert (report_name("0123456789ab", False), report_name("0123456789ab", True)) == (
        "0123456789ab",
        "0123456789ab-dirty",
    )


def test_a_committed_report_dir_with_a_past_stamp_is_not_a_baseline(
    target: Path, lizard: Path
) -> None:
    """Isolates the tracked-dir rule: no future stamp, no symlink — only 'git tracks it'."""
    _hostile_report(
        target / REPORTS_ROOT, "0123456789ab", None, when="2000-01-01T00:00:00Z"
    )
    git(target, "add", "-f", "-A")
    git(target, "commit", "-q", "-m", "planted report")
    assert summary(run(target)).baseline.fixed == 0


def test_a_symlink_to_a_valid_report_outside_is_not_followed(
    target: Path, lizard: Path, tmp_path: Path
) -> None:
    """Isolates O_NOFOLLOW: the outside file parses, so only refusing the symlink keeps it out."""
    outside = tmp_path / "planted.jsonl"
    fake = judged(title="planted fixed finding") | {
        "id": "F-" + "b" * 12,
        "origin": "judged",
        "redacted": False,
    }
    outside.write_text(json.dumps(fake) + "\n")
    _hostile_report(
        target / REPORTS_ROOT, "0123456789ab", outside, when="2000-01-01T00:00:00Z"
    )
    assert summary(run(target)).baseline.fixed == 0


def test_report_md_says_what_the_target_did_to_its_scanners(
    target: Path, lizard: Path
) -> None:
    commit_file(target, ".gitleaks.toml", "[allowlist]\n")
    commit_file(target, "src/s.py", "x = 1  # nosemgrep\n")
    text = (run(target) / "report.md").read_text()
    assert "1 scanner config file" in text and "not obeyed" in text
    assert "semgrep 1" in text


def test_a_failed_restore_keeps_the_previous_report(
    target: Path, lizard: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    previous = run(target)
    before = {p.name: p.read_bytes() for p in previous.iterdir()}

    def rename(src, dst):
        raise OSError("disk full")

    real_replace = os.replace

    def replace(src, dst):  # moving the old report aside works; moving it back does not
        if Path(dst) == previous:  # the restore, not the move aside
            raise OSError("disk full")
        return real_replace(src, dst)

    monkeypatch.setattr(finalize_mod.os, "rename", rename)
    monkeypatch.setattr(finalize_mod.os, "replace", replace)
    with pytest.raises(FinalizeError, match=r"\.old-"):
        finalize(target, prepare(target))
    [kept] = [
        p for p in (target / REPORTS_ROOT).iterdir() if p.name.startswith(".old-")
    ]
    assert {p.name: p.read_bytes() for p in (kept / previous.name).iterdir()} == before
