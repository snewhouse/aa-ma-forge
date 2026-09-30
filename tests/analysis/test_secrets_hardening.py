"""M1.7: regressions for the §6.8 impl-review findings on the secret gate and CLI
(codebase-analysis-skills-impl-review.md). Every one of these passed the gate before the fix."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from aa_ma.analysis import cli, secrets

from .test_secrets import AWS, GHP, OPAQUE, _plant, no_gitleaks, stub  # noqa: F401  (fixtures)

ROOT = Path(__file__).resolve().parents[2]


def _dir(tmp_path: Path) -> Path:
    d = tmp_path / "r"
    d.mkdir()
    return d


# --- CRITICAL 1: duplicate JSON keys ----------------------------------------------------------


def test_duplicate_json_key_is_refused(tmp_path: Path, no_gitleaks: None) -> None:
    d = _dir(tmp_path)
    (d / "dup.json").write_text('{"a": "' + AWS + '", "a": "benign"}', encoding="utf-8")
    with pytest.raises(secrets.UnsupportedFile):
        secrets.scan(d)
    assert cli.main(["scan-secrets", str(d), "--redact"]) == 1


def test_duplicate_key_in_jsonl_is_refused(tmp_path: Path, no_gitleaks: None) -> None:
    d = _dir(tmp_path)
    (d / "f.jsonl").write_text(
        '{"k": {"x": "' + AWS + '", "x": 1}}\n', encoding="utf-8"
    )
    with pytest.raises(secrets.UnsupportedFile):
        secrets.scan(d)


# --- CRITICAL 2: .gitignore skipped by name ------------------------------------------------------


def test_nested_gitignore_is_not_skipped(tmp_path: Path, no_gitleaks: None) -> None:
    d = _dir(tmp_path)
    (d / "sub").mkdir()
    (d / "sub" / ".gitignore").write_text(f"# {AWS}\n", encoding="utf-8")
    with pytest.raises(secrets.UnsupportedFile):
        secrets.scan(d)


def test_root_gitignore_other_than_star_is_not_skipped(
    tmp_path: Path, no_gitleaks: None
) -> None:
    d = _dir(tmp_path)
    (d / ".gitignore").write_text(f"*\n# {AWS}\n", encoding="utf-8")
    with pytest.raises(secrets.UnsupportedFile):
        secrets.scan(d)


def test_root_self_ignoring_gitignore_is_still_allowed(
    tmp_path: Path, no_gitleaks: None
) -> None:
    d = _dir(tmp_path)
    (d / ".gitignore").write_text("*\n", encoding="utf-8")
    assert secrets.scan(d).hits == []


# --- CRITICAL 3: gitleaks report that cannot be mapped back ---------------------------------------


def test_unmappable_gitleaks_entry_fails_closed(
    tmp_path: Path, stub: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("STUB_MODE", "find")
    monkeypatch.setenv("STUB_EXTRA", "nofile")
    d = _dir(tmp_path)
    (d / "a.md").write_text(f"x {OPAQUE} y\n", encoding="utf-8")
    with pytest.raises(secrets.GateError):
        secrets.scan(d)
    assert cli.main(["scan-secrets", str(d), "--redact"]) == 1


def test_bad_span_blanks_the_text_and_keeps_other_hits(
    tmp_path: Path, stub: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    other = "zzsecond" + "-opaque-4b1e"
    monkeypatch.setenv("STUB_MODE", "find")
    monkeypatch.setenv("STUB_EXTRA", "badspan")
    monkeypatch.setenv("STUB_BADSPAN_TOKEN", other)
    d = _dir(tmp_path)
    (d / "a.md").write_text(f"x {OPAQUE} y\n", encoding="utf-8")
    (d / "b.md").write_text(f"only gitleaks knows {other}\n", encoding="utf-8")
    result = secrets.scan(d)
    assert result.tool_status == "ran"
    secrets.redact(d, result.hits)
    assert OPAQUE not in (d / "a.md").read_text(encoding="utf-8"), (
        "the mapped hit must survive a bad sibling"
    )
    assert other not in (d / "b.md").read_text(encoding="utf-8"), (
        "unknown span → blank the whole text"
    )


# --- WARNING: dedup by span, not by rule ---------------------------------------------------------


def test_same_span_from_both_scanners_is_one_hit(
    tmp_path: Path, stub: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("STUB_MODE", "find")
    monkeypatch.setenv("STUB_TOKEN", AWS)
    d = _dir(tmp_path)
    (d / "a.md").write_text(f"first line\nkey {AWS} here\n", encoding="utf-8")
    hits = secrets.scan(d).hits
    assert len(hits) == 1, hits


# --- INFO: files the gate cannot handle cleanly ----------------------------------------------------


def test_redacted_flag_set_in_json_documents_too(
    tmp_path: Path, no_gitleaks: None
) -> None:
    d = _dir(tmp_path)
    (d / "measure.json").write_text(
        json.dumps(
            {
                "measured": [
                    {"evidence": f"key {AWS}", "redacted": False},
                    {"evidence": "clean", "redacted": False},
                ]
            }
        ),
        encoding="utf-8",
    )
    secrets.redact(d, secrets.scan(d).hits)
    measured = json.loads((d / "measure.json").read_text(encoding="utf-8"))["measured"]
    assert [m["redacted"] for m in measured] == [True, False]


def test_hardlinked_file_is_refused(tmp_path: Path, no_gitleaks: None) -> None:
    d = _dir(tmp_path)
    outside = tmp_path / "outside.md"
    outside.write_text(f"token {GHP}\n", encoding="utf-8")
    os.link(outside, d / "linked.md")
    with pytest.raises(secrets.UnsupportedFile):
        secrets.scan(d)
    assert GHP in outside.read_text(encoding="utf-8"), (
        "nothing outside the dir may be rewritten"
    )


def test_unencodable_string_is_refused_cleanly(
    tmp_path: Path, no_gitleaks: None
) -> None:
    d = _dir(tmp_path)
    (d / "s.json").write_text('{"a": "\\ud800"}', encoding="utf-8")
    with pytest.raises(secrets.UnsupportedFile):
        secrets.scan(d)
    assert cli.main(["scan-secrets", str(d)]) == 1


def test_secret_in_a_file_name_is_refused_without_echo(
    tmp_path: Path, no_gitleaks: None, capsys: pytest.CaptureFixture[str]
) -> None:
    d = _dir(tmp_path)
    (d / f"{AWS}.md").write_text("clean\n", encoding="utf-8")
    with pytest.raises(secrets.UnsupportedFile) as exc:
        secrets.scan(d)
    assert AWS not in str(exc.value)
    assert cli.main(["scan-secrets", str(d)]) == 1
    out = capsys.readouterr()
    assert AWS not in out.out and AWS not in out.err


def test_redaction_leaves_no_partial_file_on_failure(
    tmp_path: Path, no_gitleaks: None
) -> None:
    """Writes go to a temp file and are renamed into place, so the original is intact or fully replaced."""
    d = _plant(tmp_path / "r")
    before = {p.name for p in d.iterdir()}
    secrets.redact(d, secrets.scan(d).hits)
    assert {p.name for p in d.iterdir()} == before, "no temp files left behind"


# --- CLI ------------------------------------------------------------------------------------------


def test_validate_never_echoes_rejected_values(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    doc = json.loads(
        (ROOT / "tests/fixtures/analysis/valid/summary.json").read_text(
            encoding="utf-8"
        )
    )
    doc["grade"] = AWS
    doc["stamp"]["branch"] = 7  # a type error whose input would also be echoed
    bad = tmp_path / "s.json"
    bad.write_text(json.dumps(doc), encoding="utf-8")
    assert cli.main(["validate", "summary", str(bad)]) == 1
    err = capsys.readouterr().err
    assert AWS not in err
    assert "grade" in err, "the location is still reported"


def test_fresh_on_non_utf8_summary_is_unstamped(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    # M4 regression: a complete report set in its real location, so the decode branch is the one hit.
    from aa_ma.analysis.finalize import REPORT_FILES
    from aa_ma.analysis.stamp import REPORTS_ROOT

    d = tmp_path / REPORTS_ROOT / "000000000000"
    d.mkdir(parents=True)
    for name in REPORT_FILES:
        (d / name).write_text("", encoding="utf-8")
    (d / "summary.json").write_bytes(b"\xff\xfe{}")
    assert cli.main(["fresh", str(d), "--repo", str(tmp_path)]) == 1
    assert "unstamped" in capsys.readouterr().out


# --- §6.8 re-run (0ae6e8a..56f1cc6) -----------------------------------------------------------------


def test_json_key_context_reaches_the_contextual_rules(
    tmp_path: Path, no_gitleaks: None
) -> None:
    """{"password": "..."} in JSON must be caught like `password: "..."` in text."""
    d = _dir(tmp_path)
    value = "hunter2" + "hunter2hunter2"
    (d / "summary.json").write_text(
        json.dumps(
            {"password": value, "nested": {"api_key": "Zq8rT2vL" + "m9XwP4sK7nB3"}}
        ),
        encoding="utf-8",
    )
    result = secrets.scan(d)
    assert {h.rule for h in result.hits} >= {"generic-quoted"}
    secrets.redact(d, result.hits)
    doc = json.loads((d / "summary.json").read_text(encoding="utf-8"))
    assert value not in json.dumps(doc) and "Zq8rT2vLm9XwP4sK7nB3" not in json.dumps(
        doc
    )
    assert set(doc) == {"password", "nested"}, (
        "keys stay readable; only the values are redacted"
    )
    assert secrets.scan(d).hits == []


def test_validate_never_echoes_a_secret_key_name(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    doc = json.loads(
        (ROOT / "tests/fixtures/analysis/valid/summary.json").read_text(
            encoding="utf-8"
        )
    )
    doc[GHP] = 1
    bad = tmp_path / "s.json"
    bad.write_text(json.dumps(doc), encoding="utf-8")
    assert cli.main(["validate", "summary", str(bad)]) == 1
    assert GHP not in capsys.readouterr().err


def test_secret_split_across_path_components_is_not_echoed(
    tmp_path: Path, no_gitleaks: None, capsys: pytest.CaptureFixture[str]
) -> None:
    d = _dir(tmp_path)
    (d / AWS[:10]).mkdir()
    (d / AWS[:10] / f"{AWS[10:]}.bin").write_text("x", encoding="utf-8")
    assert cli.main(["scan-secrets", str(d)]) == 1
    err = capsys.readouterr().err
    assert AWS[10:] not in err and AWS[:10] not in err


def test_jsonl_is_split_on_newlines_only(tmp_path: Path, no_gitleaks: None) -> None:
    d = _dir(tmp_path)
    (d / "f.jsonl").write_text('{"a": 1}\x0c{"b": "x"}\n', encoding="utf-8")
    with pytest.raises(
        secrets.UnsupportedFile
    ):  # one line, which is not one JSON document
        secrets.scan(d)


def test_deep_nesting_is_refused_cleanly(tmp_path: Path, no_gitleaks: None) -> None:
    d = _dir(tmp_path)
    (d / "deep.json").write_text("[" * 5000 + "]" * 5000, encoding="utf-8")
    with pytest.raises(secrets.UnsupportedFile):
        secrets.scan(d)


def test_redaction_keeps_file_mode(tmp_path: Path, no_gitleaks: None) -> None:
    d = _dir(tmp_path)
    f = d / "a.md"
    f.write_text(f"token {GHP}\n", encoding="utf-8")
    f.chmod(0o644)
    secrets.redact(d, secrets.scan(d).hits)
    assert f.stat().st_mode & 0o777 == 0o644


def test_key_containing_the_separator_does_not_shift_the_value_span(
    tmp_path: Path, no_gitleaks: None
) -> None:
    """§6.6 quality review: a key that itself contains '": "' moved the value offset into the key,
    leaving part of the secret on disk after --redact."""
    d = _dir(tmp_path)
    value = "Sup3rS3cret" + "Value99"
    (d / "s.json").write_text(json.dumps({'x": "y password': value}), encoding="utf-8")
    secrets.redact(d, secrets.scan(d).hits)
    text = (d / "s.json").read_text(encoding="utf-8")
    assert value[:6] not in text and value[-6:] not in text
    assert secrets.scan(d).hits == []


def test_identical_texts_are_each_redacted(
    tmp_path: Path, stub: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Guard for scanning each distinct text once: every occurrence still gets its own hit."""
    monkeypatch.setenv("STUB_MODE", "find")
    d = _dir(tmp_path)
    lines = [
        json.dumps({"k": f"v {OPAQUE}", "n": i, "e": f"key {AWS}"}) for i in range(3)
    ]
    (d / "f.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (d / "a.md").write_text(f"v {OPAQUE}\n", encoding="utf-8")
    result = secrets.scan(d)
    assert (
        len({(h.path, h.pointer) for h in result.hits}) == 7
    )  # 3×k + 3×e + the md line
    secrets.redact(d, result.hits)
    text = (d / "f.jsonl").read_text(encoding="utf-8") + (d / "a.md").read_text(
        encoding="utf-8"
    )
    assert OPAQUE not in text and AWS not in text


# --- /sole-dev-merge Stage C (2026-09-28) ---------------------------------------------------------


def test_jsonl_redaction_keeps_the_line_framing(tmp_path: Path, no_gitleaks: None) -> None:
    d = _dir(tmp_path)
    (d / "f.jsonl").write_text(json.dumps({"e": f"k {AWS}"}) + "\n" + json.dumps({"e": "ok"}) + "\n", encoding="utf-8")
    for _ in range(2):
        secrets.redact(d, secrets.scan(d).hits)
    text = (d / "f.jsonl").read_text(encoding="utf-8")
    assert text.endswith("}\n") and text.count("\n") == 2, repr(text)


def test_list_items_get_their_key_as_context(tmp_path: Path, no_gitleaks: None) -> None:
    d = _dir(tmp_path)
    a, b = "Zx9Qw8Er" + "7Ty6Ui5Op4", "hunter2" + "hunter2"
    (d / "s.json").write_text(json.dumps({"api_key": [a], "cfg": {"password": [b, "x"]}}), encoding="utf-8")
    secrets.redact(d, secrets.scan(d).hits)
    text = (d / "s.json").read_text(encoding="utf-8")
    assert a not in text and b not in text
    assert json.loads(text)["cfg"]["password"][1] == "x"


def test_gitleaks_is_never_taken_from_a_relative_path_entry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """M2 2.9: the gate resolves gitleaks like measure does, on absolute PATH entries only."""
    marker = tmp_path / "planted-gitleaks-ran"
    hostile = tmp_path / "hostile"
    hostile.mkdir()
    fake = hostile / "gitleaks"
    fake.write_text(f"#!/bin/sh\ntouch '{marker}'\nexit 0\n", encoding="utf-8")
    fake.chmod(0o755)
    d = _dir(tmp_path)
    (d / "a.md").write_text("nothing here\n", encoding="utf-8")
    monkeypatch.delenv("GITLEAKS_BIN", raising=False)
    monkeypatch.chdir(hostile)
    monkeypatch.setenv("PATH", f".{os.pathsep}/usr/bin{os.pathsep}/bin")
    secrets.scan(d)
    assert not marker.exists()
