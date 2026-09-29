"""The machine-readable outputs. These pydantic models ARE the schemas: the golden JSON Schemas in
tests/golden/analysis/ are generated from them (`python -m aa_ma.analysis.models --write-schemas`).

Validate files with `model_validate_json`: strict mode takes enum values from JSON strings but
would refuse plain strings from Python dicts."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from enum import StrEnum
from pathlib import Path
import re
from typing import Annotated, Literal

from pydantic import (
    AwareDatetime,
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    NonNegativeInt,
    PositiveInt,
    field_serializer,
    field_validator,
)

SCHEMA_VERSION = 1
HEX12 = 12  # hex digits in a stamp's sha12 and in a finding id's hash
EVIDENCE_MAX = 2000  # chars in a finding's evidence
NOTE_MAX = 8000  # chars in a CommandCheck note (the last 40 lines of output)
# A URI scheme — or a Windows drive letter, which looks like one — makes a path absolute to a viewer.
SCHEME = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")


def _not_bool(value: object) -> object:
    # pydantic 2.12 lets JSON `true` through Literal[1] even in strict mode (bool is an int).
    if isinstance(value, bool):
        raise ValueError("schema_version must be the integer 1, not a boolean")
    return value


SchemaVersion = Annotated[Literal[1], BeforeValidator(_not_bool)]


class ToolStatus(StrEnum):
    RAN = "ran"
    ABSENT = "absent"
    UNKNOWN = "unknown"
    SKIPPED = "skipped"  # not allowed at this tier


class Rating(StrEnum):
    STRONG = "strong"
    ADEQUATE = "adequate"
    WEAK = "weak"
    UNKNOWN = "unknown"


class Confidence(StrEnum):
    HIGH = "high"
    MED = "med"
    LOW = "low"


class Severity(StrEnum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class Origin(StrEnum):
    MEASURED = "measured"
    JUDGED = "judged"


class Refutation(StrEnum):
    SURVIVED = "survived"
    REFUTED = "refuted"
    NOT_REQUIRED = "not_required"
    PENDING = "pending"


class Dimension(StrEnum):
    ARCHITECTURE = "architecture"
    MAINTAINABILITY = "maintainability"
    SECURITY = "security"
    TESTS_DEPS = "tests_deps"


Tier = Literal["quick", "standard", "deep"]

# Rating policy (finalize caps; report_md explains; RATING.md mirrors it). A dimension whose core
# input did not run cannot rate Strong. The network tools run in Deep only (plan V4), so outside
# Deep security and tests_deps rate at most Adequate — intended.
NETWORK_TOOLS = ("semgrep", "osv-scanner", "pip-audit")
CORE_INPUTS = {
    Dimension.ARCHITECTURE: ("codemem.layers",),
    Dimension.MAINTAINABILITY: ("lizard",),
    Dimension.SECURITY: ("semgrep",),
    Dimension.TESTS_DEPS: ("osv-scanner", "pip-audit"),
}


class _Model(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, allow_inf_nan=False)


class Stamp(_Model):
    date_utc: AwareDatetime
    sha12: str = Field(pattern=rf"^[0-9a-f]{{{HEX12}}}$")
    dirty: bool
    branch: str
    tier: Tier
    tools: dict[str, ToolStatus]
    absorbed: list[str]
    fresh_run: list[str]

    @field_validator("date_utc")
    @classmethod
    def _utc_only(cls, value: datetime) -> datetime:
        offset = value.utcoffset()
        if offset is None or offset.total_seconds() != 0:
            raise ValueError("date_utc must be UTC (Z or +00:00)")
        return value

    @field_serializer("date_utc")
    def _iso_z(self, value: datetime) -> str:
        return value.isoformat().replace("+00:00", "Z")


class LedgerEntry(_Model):
    path: str
    status: Literal["assessed", "set_aside"]
    reason: str


class DimensionResult(_Model):
    dimension: Dimension
    rating: Rating
    confidence: Confidence
    inputs: list[str]
    capped: bool


class Counts(_Model):
    findings: NonNegativeInt = 0
    refuted: NonNegativeInt = 0
    redacted: NonNegativeInt = 0
    critical: NonNegativeInt = 0
    high: NonNegativeInt = 0
    medium: NonNegativeInt = 0
    low: NonNegativeInt = 0
    info: NonNegativeInt = 0


class Baseline(_Model):
    new: NonNegativeInt = 0
    persisting: NonNegativeInt = 0
    fixed: NonNegativeInt = 0


class Summary(_Model):
    schema_version: SchemaVersion
    stamp: Stamp
    dimensions: list[DimensionResult]
    ledger: list[LedgerEntry]
    metrics: dict[str, int | float | None]  # None = not measured
    counts: Counts
    baseline: Baseline

    @field_validator("dimensions")
    @classmethod
    def _one_per_dimension(cls, value: list[DimensionResult]) -> list[DimensionResult]:
        got = sorted(d.dimension for d in value)
        if got != sorted(Dimension):
            raise ValueError(
                f"need exactly one result per dimension {sorted(Dimension)}, got {got}"
            )
        return value


class _FindingFields(_Model):
    schema_version: SchemaVersion
    dimension: Dimension
    severity: Severity
    confidence: Confidence
    rule: str
    title: str
    path: str
    line: PositiveInt | None
    anchor: str  # whitespace-collapsed, secret-redacted source text or a per-rule anchor; never a line number
    refutation: Refutation
    evidence: str = Field(max_length=EVIDENCE_MAX)

    @field_validator("path")
    @classmethod
    def _repo_relative(cls, value: str) -> str:
        # Untrusted (judged) input flows into SARIF artifactLocation.uri: repo-relative only.
        parts = re.split(r"[\\/]", value)
        if (
            not value
            or value.startswith(("/", "\\"))
            or SCHEME.match(value)
            or ".." in parts
            or "%" in value
            or any(ord(ch) < 32 or ord(ch) == 127 for ch in value)
        ):
            raise ValueError(
                "path must be repo-relative: no leading slash, URI scheme or drive letter, "
                "'..', percent-encoding or control characters"
            )
        return value


class JudgedFinding(_FindingFields):
    """One judged.jsonl line, written by a judge agent; finalize assigns the id."""

    origin: Literal["judged"]


class Finding(_FindingFields):
    """One findings.jsonl line."""

    id: str = Field(pattern=rf"^F-[0-9a-f]{{{HEX12}}}$")
    origin: Origin
    redacted: bool
    refutation_reason: str | None = Field(
        default=None, max_length=EVIDENCE_MAX
    )  # the refuter's


class RefuterVerdict(_Model):
    """One verdicts.jsonl line: the refuter's call on a pending judged.jsonl line. Internal: no golden."""

    line: PositiveInt  # 1-based line number in judged.jsonl
    verdict: Literal["survived", "refuted"]
    reason: str = Field(min_length=1, max_length=EVIDENCE_MAX)


class CommandCheck(_Model):
    command: str
    status: Literal["verified", "failed", "timeout", "not_run", "refused"]
    note: str = Field(max_length=NOTE_MAX)  # last 40 output lines, secret-redacted


class Onboarding(_Model):
    schema_version: SchemaVersion
    stamp: Stamp
    commands: list[CommandCheck]
    entry_points: list[str]
    key_modules: list[str]
    rules_files: list[str]
    ledger: list[LedgerEntry]
    sections: dict[
        str, list[str]
    ]  # onboarding section → source paths it was written from


class MeasureDoc(_Model):
    """The work dir's measure.json, measure → finalize. Internal: not exported, no golden schema."""

    schema_version: SchemaVersion
    stamp: Stamp
    metrics: dict[str, int | float | None]
    measured: list[Finding]


EXPORTED: dict[str, type[_Model]] = {
    "summary": Summary,
    "finding": Finding,
    "judged_finding": JudgedFinding,
    "onboarding": Onboarding,
}


def write_schemas(out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for kind, model in EXPORTED.items():
        text = json.dumps(model.model_json_schema(), indent=2, sort_keys=True) + "\n"
        (out_dir / f"{kind}.schema.json").write_text(text, encoding="utf-8")


def _main() -> None:
    parser = argparse.ArgumentParser(prog="python -m aa_ma.analysis.models")
    parser.add_argument("--write-schemas", type=Path, required=True, metavar="DIR")
    write_schemas(parser.parse_args().write_schemas)


if __name__ == "__main__":
    _main()
