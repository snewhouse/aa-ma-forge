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
from typing import Annotated, Literal

from pydantic import (
    AwareDatetime,
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    PositiveInt,
    field_serializer,
    field_validator,
)

SCHEMA_VERSION = 1


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


class _Model(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, allow_inf_nan=False)


class Stamp(_Model):
    date_utc: AwareDatetime
    sha12: str = Field(pattern=r"^[0-9a-f]{12}$")
    dirty: bool
    branch: str
    tier: Literal["quick", "standard", "deep"]
    tools: dict[str, ToolStatus]
    absorbed: list[str]
    fresh_run: list[str]

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
    findings: int = 0
    refuted: int = 0
    redacted: int = 0
    critical: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0
    info: int = 0


class Baseline(_Model):
    new: int = 0
    persisting: int = 0
    fixed: int = 0


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
    evidence: str = Field(max_length=2000)


class JudgedFinding(_FindingFields):
    """One judged.jsonl line, written by a judge agent; finalize assigns the id."""

    origin: Literal["judged"]


class Finding(_FindingFields):
    """One findings.jsonl line."""

    id: str = Field(pattern=r"^F-[0-9a-f]{12}$")
    origin: Origin
    redacted: bool


class CommandCheck(_Model):
    command: str
    status: Literal["verified", "failed", "timeout", "not_run", "refused"]
    note: str = Field(max_length=8000)  # last 40 output lines, secret-redacted


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
