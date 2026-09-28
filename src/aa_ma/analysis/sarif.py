"""findings → SARIF 2.1.0 (stdlib json only). Validates against the OASIS schema; also carries the
fields GitHub code scanning wants that the schema does not check (docs/research/
codebase-analysis-skills-sarif.md). Our ID rides in `fingerprints`; `partialFingerprints` is left
to github/codeql-action/upload-sarif."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from typing import Any, Literal

from .models import SCHEME, Finding

SCHEMA_URI = "https://json.schemastore.org/sarif-2.1.0.json"
FINGERPRINT_KEY = "aaMaFindingId/v1"
LEVEL = {
    "critical": "error",
    "high": "error",
    "medium": "warning",
    "low": "note",
    "info": "note",
}
# GitHub reads a string in (0.0, 10.0] and buckets > 9.0 as critical; the property also turns a result
# into a *security* result, so only security findings above info carry it
# (docs/research/codebase-analysis-skills-sarif.md:78).
SECURITY_SEVERITY = {"critical": "9.5", "high": "7.0", "medium": "4.0", "low": "2.0"}
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
    }
    if f.dimension == "security" and f.severity in SECURITY_SEVERITY:
        result["properties"] = {"security-severity": SECURITY_SEVERITY[f.severity]}
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
    baseline: Mapping[str, Literal["new", "persisting"]] | None = None,
    fixed: Iterable[Finding] = (),
) -> dict[str, Any]:
    """`baseline` maps finding id → new|persisting; `fixed` findings are emitted with baselineState absent."""
    if baseline is not None and "fixed" in baseline.values():
        raise ValueError(
            "a current finding cannot be 'fixed'; pass fixed findings via `fixed=`"
        )
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


def verify(doc: Mapping[str, Any]) -> None:
    """Re-check the writer's invariants after the secret gate rewrote the file; raises ValueError.
    Full schema validation lives in the tests (jsonschema is a dev dependency only)."""
    try:
        [run] = doc["runs"]
        if doc["version"] != "2.1.0" or doc["$schema"] != SCHEMA_URI:
            raise ValueError("not a SARIF 2.1.0 document")
        rules = {r["id"] for r in run["tool"]["driver"]["rules"]}
        for result in run["results"]:
            uris = [
                loc["physicalLocation"]["artifactLocation"]["uri"]
                for loc in result["locations"]
            ]
            if (
                result["ruleId"] not in rules
                or result["level"] not in LEVEL.values()
                or not result["fingerprints"].get(FINGERPRINT_KEY, "").startswith("F-")
                or any(u.startswith("/") or SCHEME.match(u) for u in uris)
            ):
                raise ValueError(
                    f"result for rule {result['ruleId']!r} breaks a writer invariant"
                )
    except (KeyError, TypeError) as exc:
        raise ValueError(f"malformed SARIF: {exc!r}") from None
