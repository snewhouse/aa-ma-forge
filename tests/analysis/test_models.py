"""M1 AC1 + AC2: the pydantic models are the schemas; goldens pin them; the CLI validates files."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from aa_ma.analysis import cli, models

ROOT = Path(__file__).resolve().parents[2]
FIX = ROOT / "tests" / "fixtures" / "analysis"
GOLDEN = ROOT / "tests" / "golden" / "analysis"
KIND_FILES = {
    "summary": "summary.json",
    "finding": "finding.jsonl",
    "judged_finding": "judged_finding.jsonl",
    "onboarding": "onboarding.json",
}
INVALID = sorted((FIX / "invalid").iterdir())


def _kind(path: Path) -> str:
    return path.name.split("-", 1)[0]


def test_exported_models_are_the_four_kinds() -> None:
    assert set(models.EXPORTED) == set(KIND_FILES)


@pytest.mark.parametrize("kind", sorted(KIND_FILES))
def test_valid_fixture_validates(kind: str) -> None:
    assert cli.main(["validate", kind, str(FIX / "valid" / KIND_FILES[kind])]) == 0


@pytest.mark.parametrize("path", INVALID, ids=[p.name for p in INVALID])
def test_negative_fixture_is_rejected(
    path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert cli.main(["validate", _kind(path), str(path)]) == 1
    assert capsys.readouterr().err.strip(), "a rejection must say why on stderr"


def test_negative_fixtures_cover_the_named_cases() -> None:
    names = {p.name for p in INVALID}
    for required in (
        "summary-extra-field.json",
        "summary-schema-version-2.json",
        "summary-schema-version-true.json",
        "summary-rating-bogus.json",
        "summary-metrics-nan.json",
        "summary-counts-bogus-key.json",
        "summary-sha12-not-hex.json",
        "finding-line-zero.jsonl",
        "finding-line-true.jsonl",
        "finding-missing-id.jsonl",
        "judged_finding-self-refuted.jsonl",  # M3 merge review: validate enforces the judge rules
        "judged_finding-prefix-mismatch.jsonl",
    ):
        assert required in names


def test_validate_usage_errors_exit_2(tmp_path: Path) -> None:
    assert (
        cli.main(["validate", "bogus-kind", str(FIX / "valid" / "summary.json")]) == 2
    )
    assert cli.main(["validate", "summary", str(tmp_path / "missing.json")]) == 2


def test_empty_jsonl_is_valid(tmp_path: Path) -> None:
    empty = tmp_path / "findings.jsonl"
    empty.write_text("", encoding="utf-8")
    assert cli.main(["validate", "finding", str(empty)]) == 0


@pytest.mark.parametrize("kind", sorted(KIND_FILES))
def test_golden_schema_equals_model_schema(kind: str) -> None:
    golden = json.loads((GOLDEN / f"{kind}.schema.json").read_text(encoding="utf-8"))
    assert golden == models.EXPORTED[kind].model_json_schema(), (
        f"regenerate: uv run python -m aa_ma.analysis.models --write-schemas {GOLDEN.relative_to(ROOT)}"
    )


def _documents(path: Path) -> list[object]:
    text = path.read_text(encoding="utf-8")
    if path.suffix == ".jsonl":
        return [json.loads(line) for line in text.splitlines() if line.strip()]
    return [json.loads(text)]


@pytest.mark.parametrize("kind", sorted(KIND_FILES))
def test_valid_fixture_passes_its_golden_schema(kind: str) -> None:
    schema = json.loads((GOLDEN / f"{kind}.schema.json").read_text(encoding="utf-8"))
    for doc in _documents(FIX / "valid" / KIND_FILES[kind]):
        Draft202012Validator(schema).validate(doc)


def test_schema_version_2_fails_the_golden_schema_too() -> None:
    """Draft-04 ignores `const`; 2020-12 must reject schema_version 2 like the model does."""
    schema = json.loads((GOLDEN / "summary.schema.json").read_text(encoding="utf-8"))
    doc = json.loads(
        (FIX / "invalid" / "summary-schema-version-2.json").read_text(encoding="utf-8")
    )
    assert not Draft202012Validator(schema).is_valid(doc)


def test_write_schemas_module_entry_point(tmp_path: Path) -> None:
    subprocess.run(
        [
            sys.executable,
            "-m",
            "aa_ma.analysis.models",
            "--write-schemas",
            str(tmp_path),
        ],
        check=True,
        cwd=ROOT,
    )
    assert sorted(p.name for p in tmp_path.iterdir()) == sorted(
        f"{k}.schema.json" for k in KIND_FILES
    )
    for kind in KIND_FILES:
        written = json.loads(
            (tmp_path / f"{kind}.schema.json").read_text(encoding="utf-8")
        )
        assert written == models.EXPORTED[kind].model_json_schema()


def test_sha12_rejects_option_like_value() -> None:
    """AC11: a stamp can never carry a value git would read as an option."""
    doc = json.loads((FIX / "valid" / "summary.json").read_text(encoding="utf-8"))
    doc["stamp"]["sha12"] = "--output=x"
    with pytest.raises(ValueError):
        models.Summary.model_validate_json(json.dumps(doc))


def test_console_script_is_declared() -> None:
    import tomllib

    scripts = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))[
        "project"
    ]["scripts"]
    assert scripts["aa-ma-analysis"] == "aa_ma.analysis.cli:main"
