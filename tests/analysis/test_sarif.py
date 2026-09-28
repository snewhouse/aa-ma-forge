"""M1 AC4: SARIF 2.1.0 validates against the vendored OASIS schema, plus the GitHub fields the
schema does not check (ruleId, repo-relative uri, string security-severity)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft4Validator

from aa_ma.analysis import sarif
from aa_ma.analysis.models import Finding

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = json.loads(
    (ROOT / "tests/fixtures/sarif/sarif-schema-2.1.0.json").read_text(encoding="utf-8")
)
FIXTURE = ROOT / "tests/fixtures/analysis/valid/finding.jsonl"
SEVERITY = {
    "critical": "9.0",
    "high": "7.0",
    "medium": "4.0",
    "low": "2.0",
    "info": "0.0",
}
LEVEL = {
    "critical": "error",
    "high": "error",
    "medium": "warning",
    "low": "note",
    "info": "note",
}


def _findings() -> list[Finding]:
    base = [
        Finding.model_validate_json(line)
        for line in FIXTURE.read_text(encoding="utf-8").splitlines()
    ]
    extra = []
    for i, sev in enumerate(["critical", "low", "info"]):
        extra.append(
            base[0].model_copy(
                update={"id": f"F-00000000000{i}", "severity": sev, "rule": f"r.{sev}"}
            )
        )
    return base + extra


def _results(log: dict) -> list[dict]:
    return log["runs"][0]["results"]


def test_validates_against_oasis_schema() -> None:
    log = sarif.to_sarif(_findings(), "0.17.0")
    Draft4Validator(SCHEMA).validate(log)


def test_empty_findings_still_valid() -> None:
    log = sarif.to_sarif([], "0.17.0")
    Draft4Validator(SCHEMA).validate(log)
    assert _results(log) == []


def test_top_level_fields() -> None:
    log = sarif.to_sarif(_findings(), "0.17.0")
    assert log["version"] == "2.1.0"
    assert log["$schema"].startswith("https://")
    driver = log["runs"][0]["tool"]["driver"]
    assert driver["name"] == "aa-ma-analysis" and driver["version"] == "0.17.0"


def test_every_rule_has_the_github_required_texts() -> None:
    log = sarif.to_sarif(_findings(), "0.17.0")
    rules = log["runs"][0]["tool"]["driver"]["rules"]
    assert {r["id"] for r in rules} == {f.rule for f in _findings()}
    for r in rules:
        for key in ("shortDescription", "fullDescription", "help"):
            assert r[key]["text"].strip()


def test_every_result_has_ruleid_uri_severity_and_fingerprint() -> None:
    findings = _findings()
    for f, res in zip(
        findings, _results(sarif.to_sarif(findings, "0.17.0")), strict=True
    ):
        assert res["ruleId"] == f.rule
        uri = res["locations"][0]["physicalLocation"]["artifactLocation"]["uri"]
        assert uri == f.path and not uri.startswith("/") and "://" not in uri
        sev = res["properties"]["security-severity"]
        assert isinstance(sev, str) and sev == SEVERITY[f.severity]
        assert res["level"] == LEVEL[f.severity]
        assert res["fingerprints"] == {"aaMaFindingId/v1": f.id}
        assert "partialFingerprints" not in res, "left to upload-sarif"
        assert res["message"]["text"] == f.title


def test_region_only_when_line_known() -> None:
    findings = _findings()
    res = _results(sarif.to_sarif(findings, "0.17.0"))
    for f, r in zip(findings, res, strict=True):
        region = r["locations"][0]["physicalLocation"].get("region")
        assert (region == {"startLine": f.line}) if f.line else region is None


@pytest.mark.parametrize(
    ("ours", "theirs"), [("new", "new"), ("persisting", "unchanged")]
)
def test_baseline_state_mapping(ours: str, theirs: str) -> None:
    findings = _findings()
    log = sarif.to_sarif(findings, "0.17.0", baseline={f.id: ours for f in findings})
    Draft4Validator(SCHEMA).validate(log)
    assert {r["baselineState"] for r in _results(log)} == {theirs}


def test_fixed_findings_are_emitted_as_absent() -> None:
    findings = _findings()
    log = sarif.to_sarif(
        findings[1:],
        "0.17.0",
        baseline={f.id: "persisting" for f in findings[1:]},
        fixed=findings[:1],
    )
    Draft4Validator(SCHEMA).validate(log)
    absent = [r for r in _results(log) if r["baselineState"] == "absent"]
    assert [r["fingerprints"]["aaMaFindingId/v1"] for r in absent] == [findings[0].id]


def test_no_baseline_means_no_baseline_state() -> None:
    assert all(
        "baselineState" not in r
        for r in _results(sarif.to_sarif(_findings(), "0.17.0"))
    )


def test_output_is_plain_json() -> None:
    log = sarif.to_sarif(_findings(), "0.17.0")
    assert json.loads(json.dumps(log)) == log
