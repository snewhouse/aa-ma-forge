"""findings → SARIF 2.1.0 (stdlib json only). Validates against the OASIS schema; also carries the
fields GitHub code scanning wants that the schema does not check (docs/research/
codebase-analysis-skills-sarif.md). Our ID rides in `fingerprints`; `partialFingerprints` is left
to github/codeql-action/upload-sarif."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from typing import Any

from .models import Finding

SCHEMA_URI = "https://json.schemastore.org/sarif-2.1.0.json"
FINGERPRINT_KEY = "aaMaFindingId/v1"
LEVEL = {
    "critical": "error",
    "high": "error",
    "medium": "warning",
    "low": "note",
    "info": "note",
}
SECURITY_SEVERITY = {
    "critical": "9.0",
    "high": "7.0",
    "medium": "4.0",
    "low": "2.0",
    "info": "0.0",
}
BASELINE_STATE = {"new": "new", "persisting": "unchanged", "fixed": "absent"}


def _result(f: Finding, state: str | None) -> dict[str, Any]:
    location: dict[str, Any] = {"artifactLocation": {"uri": f.path}}
    if f.line:
        location["region"] = {"startLine": f.line}
    result: dict[str, Any] = {
        "ruleId": f.rule,
        "level": LEVEL[f.severity],
        "message": {"text": f.title},
        "locations": [{"physicalLocation": location}],
        "fingerprints": {FINGERPRINT_KEY: f.id},
        "properties": {"security-severity": SECURITY_SEVERITY[f.severity]},
    }
    if state is not None:
        result["baselineState"] = BASELINE_STATE[state]
    return result


def _rule(rule_id: str, example: Finding) -> dict[str, Any]:
    return {
        "id": rule_id,
        "shortDescription": {"text": rule_id},
        "fullDescription": {"text": f"{example.dimension}: {rule_id}"},
        "help": {
            "text": f"See ANALYSIS-CONTRACT.md in aa-ma-forge for rule {rule_id}."
        },
    }


def to_sarif(
    findings: Sequence[Finding],
    tool_version: str,
    baseline: Mapping[str, str] | None = None,
    fixed: Iterable[Finding] = (),
) -> dict[str, Any]:
    """`baseline` maps finding id → new|persisting; `fixed` findings are emitted with baselineState absent."""
    fixed = list(fixed)
    results = [
        _result(f, None if baseline is None else baseline.get(f.id, "new"))
        for f in findings
    ]
    results += [_result(f, "fixed") for f in fixed]
    examples: dict[str, Finding] = {}
    for f in [*findings, *fixed]:
        examples.setdefault(f.rule, f)
    return {
        "$schema": SCHEMA_URI,
        "version": "2.1.0",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "aa-ma-analysis",
                        "version": tool_version,
                        "rules": [_rule(r, f) for r, f in examples.items()],
                    }
                },
                "results": results,
            }
        ],
    }
