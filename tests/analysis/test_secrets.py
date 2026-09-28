"""M1 AC5: the output secret gate redacts every planted secret, never echoes a value, is idempotent,
and fails closed on files it cannot parse. Every fake secret is assembled at runtime from fragments
(plan §0: no literal secret in a committed file) and none uses an allowlisted `EXAMPLE` value."""

from __future__ import annotations

import dataclasses
import json
import shutil
import stat
import textwrap
from pathlib import Path

import pytest

from aa_ma.analysis import cli, secrets
from aa_ma.analysis.models import Finding

ROOT = Path(__file__).resolve().parents[2]

AWS = "AKIA" + "Q7ZXM3PL" + "K9WRT2VB"
GHP = "ghp_" + "a1B2c3D4e5F6g7H8i9J0" + "k1L2m3N4o5P6q7R8"
PEM_BODY = "MIIEpAIBAAKC" + "AQEA3Tz2mr7SZiAMfQyuvBjM2wq"
PEM = "-----BEGIN " + "RSA PRIVATE KEY-----\n" + PEM_BODY + "\nb3BlbnNzaC1rZXktdjEAAAAA\n-----END " + "RSA PRIVATE KEY-----"
PGP_BODY = "lQOYBGV" + "k2mMBCAC9xw7Tq1Zr"
PGP = "-----BEGIN PGP " + "PRIVATE KEY BLOCK-----\n\n" + PGP_BODY + "\n=Ab1c\n-----END PGP " + "PRIVATE KEY BLOCK-----"
JSON_PW = "S3cr3t" + "Passw0rd!x"
URL_PW = "Sup3r" + "S3cretPw"
ENV_PW = "Xy7pQ2" + "rT9wLmN4"
OPAQUE = "zzopaque" + "-value-7f3a9c21"  # only the stub gitleaks knows this one
BENIGN = "--mask-sk-lighthouse-skeleton"
PLANTED = [AWS, GHP, PEM_BODY, PGP_BODY, JSON_PW, URL_PW, ENV_PW]

STUB = textwrap.dedent(
    """\
    #!/usr/bin/env python3
    # Stub gitleaks 8.18: records argv; STUB_MODE=exit2 exits 2 with no report;
    # STUB_MODE=find reports every occurrence of the opaque token with gitleaks' own column
    # convention (measured 2026-09-28: StartColumn = index + 2, EndColumn = index + len + 1).
    import json, os, sys
    from pathlib import Path
    log = Path(os.environ["STUB_LOG"])
    log.write_text(log.read_text() + json.dumps(sys.argv[1:]) + "\\n" if log.exists() else json.dumps(sys.argv[1:]) + "\\n")
    if os.environ.get("STUB_MODE") == "exit2":
        sys.exit(2)
    args = sys.argv[1:]
    src, report = Path(args[args.index("-s") + 1]), Path(args[args.index("-r") + 1])
    token, out = os.environ["STUB_TOKEN"], []
    for f in sorted(p for p in src.rglob("*") if p.is_file()):
        for n, line in enumerate(f.read_text(errors="replace").splitlines(), 1):
            i = line.find(token)
            if i >= 0:
                out.append({"RuleID": "generic-api-key", "File": str(f), "StartLine": n, "EndLine": n,
                            "StartColumn": i + 2, "EndColumn": i + len(token) + 1,
                            "Match": "REDACTED", "Secret": "REDACTED"})
    report.write_text(json.dumps(out))
    """
)


def _finding_line() -> str:
    fixture = (ROOT / "tests/fixtures/analysis/valid/finding.jsonl").read_text(encoding="utf-8").splitlines()[1]
    doc = json.loads(fixture)
    doc["evidence"] = f'config has "password": "{JSON_PW}" and key {AWS}'
    return json.dumps(doc)


def _plant(d: Path) -> Path:
    d.mkdir(parents=True, exist_ok=True)
    (d / ".gitignore").write_text("*\n", encoding="utf-8")
    (d / "findings.jsonl").write_text(_finding_line() + "\n", encoding="utf-8")
    (d / "extra.json").write_text(
        json.dumps({GHP: "a token used as a key", "note": PEM, "db": f"postgres://admin:{URL_PW}@db.internal:5432/app",
                    "opaque": f"value {OPAQUE} here", "flag": BENIGN}),
        encoding="utf-8",
    )
    (d / "report.md").write_text(
        f"# Report\n\n```\n{PGP}\n```\n\nSet DB_PASSWORD={ENV_PW} in prod.\n\nAlso {OPAQUE} and {BENIGN}.\n",
        encoding="utf-8",
    )
    (d / "run.log").write_text(f"clone https://x:{URL_PW}@example.invalid/r.git\ntoken {GHP}\n", encoding="utf-8")
    return d


def _all_bytes(d: Path) -> str:
    return "\n".join(p.read_text(encoding="utf-8", errors="replace") for p in d.rglob("*") if p.is_file())


@pytest.fixture
def no_gitleaks(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GITLEAKS_BIN", "/nonexistent/gitleaks")


@pytest.fixture
def stub(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    bin_ = tmp_path / "bin" / "gitleaks"
    bin_.parent.mkdir()
    bin_.write_text(STUB, encoding="utf-8")
    bin_.chmod(bin_.stat().st_mode | stat.S_IEXEC)
    log = tmp_path / "stub.log"
    monkeypatch.setenv("GITLEAKS_BIN", str(bin_))
    monkeypatch.setenv("STUB_LOG", str(log))
    monkeypatch.setenv("STUB_TOKEN", OPAQUE)
    return log


def test_hit_type_has_no_value_field() -> None:
    names = {f.name for f in dataclasses.fields(secrets.Hit)}
    assert {"rule", "path", "start_line", "end_line", "start_col", "end_col"} <= names
    assert not names & {"value", "secret", "match", "text"}


def test_regex_path_finds_every_planted_secret(tmp_path: Path, no_gitleaks: None) -> None:
    d = _plant(tmp_path / "r")
    result = secrets.scan(d)
    assert result.tool_status == "absent"
    hit_files = {Path(h.path).name for h in result.hits}
    assert hit_files == {"findings.jsonl", "extra.json", "report.md", "run.log"}
    assert len(result.hits) >= 8
    rendered = repr(result.hits)
    for value in PLANTED:
        assert value not in rendered


def test_redact_removes_every_planted_secret(tmp_path: Path, no_gitleaks: None) -> None:
    d = _plant(tmp_path / "r")
    n = secrets.redact(d, secrets.scan(d).hits)
    assert n >= 8
    text = _all_bytes(d)
    for value in PLANTED:
        assert value not in text, "planted value survived redaction"
    assert "[REDACTED:" in text
    assert BENIGN in text, "a benign flag must not be treated as a secret"


def test_redaction_is_idempotent(tmp_path: Path, no_gitleaks: None) -> None:
    d = _plant(tmp_path / "r")
    secrets.redact(d, secrets.scan(d).hits)
    assert secrets.scan(d).hits == []
    assert secrets.redact(d, []) == 0


def test_json_is_rewritten_not_byte_patched(tmp_path: Path, no_gitleaks: None) -> None:
    d = _plant(tmp_path / "r")
    secrets.redact(d, secrets.scan(d).hits)
    extra = json.loads((d / "extra.json").read_text(encoding="utf-8"))  # still parses
    assert GHP not in "".join(extra)  # keys are scanned too
    assert extra["flag"] == BENIGN


def test_redacted_finding_is_flagged_and_still_valid(tmp_path: Path, no_gitleaks: None) -> None:
    d = _plant(tmp_path / "r")
    secrets.redact(d, secrets.scan(d).hits)
    finding = Finding.model_validate_json((d / "findings.jsonl").read_text(encoding="utf-8").strip())
    assert finding.redacted is True
    assert finding.id == json.loads(_finding_line())["id"]


def test_benign_flag_alone_is_not_a_hit(tmp_path: Path, no_gitleaks: None) -> None:
    d = tmp_path / "r"
    d.mkdir()
    (d / "a.md").write_text(f"run with {BENIGN}\n", encoding="utf-8")
    assert secrets.scan(d).hits == []


def test_gitleaks_error_is_unknown_and_regex_still_runs(tmp_path: Path, stub: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("STUB_MODE", "exit2")
    d = _plant(tmp_path / "r")
    result = secrets.scan(d)
    assert result.tool_status == "unknown"
    secrets.redact(d, result.hits)
    text = _all_bytes(d)
    for value in PLANTED:
        assert value not in text


def test_gitleaks_only_secret_is_redacted(tmp_path: Path, stub: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("STUB_MODE", "find")
    d = _plant(tmp_path / "r")
    result = secrets.scan(d)
    assert result.tool_status == "ran"
    secrets.redact(d, result.hits)
    text = _all_bytes(d)
    assert OPAQUE not in text, "a hit only gitleaks reports must still be redacted (md and json)"
    for value in PLANTED:
        assert value not in text


def test_gitleaks_invocation_and_report_location(tmp_path: Path, stub: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("STUB_MODE", "find")
    d = _plant(tmp_path / "r")
    secrets.scan(d)
    calls = [json.loads(line) for line in stub.read_text(encoding="utf-8").splitlines()]
    assert calls
    for argv in calls:
        assert argv[0] == "detect"
        for flag in ("--no-git", "--redact"):
            assert flag in argv
        assert argv[argv.index("--exit-code") + 1] == "0"
        report = Path(argv[argv.index("-r") + 1])
        assert d.resolve() not in report.resolve().parents, "report must be written outside the scanned dir"
        assert not report.exists(), "report must be deleted after parsing"


@pytest.mark.skipif(shutil.which("gitleaks") is None, reason="real gitleaks not installed")
def test_real_gitleaks_ran(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GITLEAKS_BIN", shutil.which("gitleaks") or "")
    d = _plant(tmp_path / "r")
    result = secrets.scan(d)
    assert result.tool_status == "ran"
    secrets.redact(d, result.hits)
    for value in PLANTED:
        assert value not in _all_bytes(d)


def test_unknown_extension_fails_closed(tmp_path: Path, no_gitleaks: None) -> None:
    d = _plant(tmp_path / "r")
    (d / "notes.csv").write_text(f"k,{AWS}\n", encoding="utf-8")
    with pytest.raises(secrets.UnsupportedFile):
        secrets.scan(d)


# --- CLI ---------------------------------------------------------------------------------------


def test_cli_reports_hits_without_values(tmp_path: Path, no_gitleaks: None, capsys: pytest.CaptureFixture[str]) -> None:
    d = _plant(tmp_path / "r")
    assert cli.main(["scan-secrets", str(d)]) == 1
    out = capsys.readouterr()
    for value in PLANTED:
        assert value not in out.out and value not in out.err
    assert "report.md" in out.out


def test_cli_redact_then_clean(tmp_path: Path, no_gitleaks: None, capsys: pytest.CaptureFixture[str]) -> None:
    d = _plant(tmp_path / "r")
    assert cli.main(["scan-secrets", str(d), "--redact"]) == 0
    assert cli.main(["scan-secrets", str(d)]) == 0
    out = capsys.readouterr()
    for value in PLANTED:
        assert value not in out.out and value not in out.err


def test_cli_unknown_extension_exit_1(tmp_path: Path, no_gitleaks: None, capsys: pytest.CaptureFixture[str]) -> None:
    d = _plant(tmp_path / "r")
    (d / "notes.csv").write_text("a,b\n", encoding="utf-8")
    assert cli.main(["scan-secrets", str(d), "--redact"]) == 1
    assert "notes.csv" in capsys.readouterr().err


def test_cli_missing_dir_exit_2(tmp_path: Path) -> None:
    assert cli.main(["scan-secrets", str(tmp_path / "nope")]) == 2
