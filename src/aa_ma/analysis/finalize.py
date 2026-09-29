"""finalize(): the work dir (measure.json + the judges' and main thread's files) → the report set.

judged.jsonl is untrusted model output: every line is validated, every path must stay inside the
repo, and a line that fails is refused by number without echoing it. The report is written to a
temp dir, passed through the secret gate, re-validated, and only then renamed over
`<sha12>[-dirty]`; a failure at any point leaves the previous report and the work dir as they were."""

from __future__ import annotations

import json
import os
import shutil
import tempfile
from collections import Counter
from datetime import UTC, datetime
from importlib import metadata
from pathlib import Path

from pydantic import TypeAdapter, ValidationError

from . import report_md, sarif, secrets
from .ids import anchor_for, assign_ids, compare
from .measure import WORK_PREFIX
from .models import (
    CORE_INPUTS,
    SCHEMA_VERSION,
    Baseline,
    Confidence,
    Counts,
    DimensionResult,
    Finding,
    JudgedFinding,
    LedgerEntry,
    MeasureDoc,
    Origin,
    Rating,
    Refutation,
    Severity,
    Summary,
    ToolStatus,
)
from .stamp import (
    REPORT_NAME,
    REPORTS_ROOT,
    contained,
    ensure_self_ignoring,
    head_stamp,
    read_regular,
    report_name,
    run_git,
)

# Test seam: fail after the gate, before the rename.
CRASH_SEAM = "AA_MA_FINALIZE_CRASH_BEFORE_RENAME"
REFUTE_REQUIRED = {Severity.CRITICAL, Severity.HIGH}
# Judged findings of these severities: confidence at most MED.
CONFIDENCE_CAPPED = {Severity.MEDIUM, Severity.LOW}
REPORT_FILES = (
    "summary.json",
    "findings.jsonl",
    "findings.sarif",
    "report.md",
    "run.log",
)


class FinalizeError(Exception):
    pass


def _read(work: Path, name: str) -> str:
    try:
        return read_regular(work / name)
    except (OSError, UnicodeDecodeError):
        raise FinalizeError(
            f"{work / name}: missing or unreadable (the work dir needs {name})"
        ) from None


def _describe(exc: Exception) -> str:
    """An error, never the input: pydantic's text quotes the value, which may hold a secret."""
    if isinstance(exc, ValidationError):
        kinds = sorted({e["type"] for e in exc.errors(include_input=False)})
        return f"{exc.error_count()} validation error(s) ({', '.join(kinds)})"
    return f"{exc.__class__.__name__}: {exc}"


def _load(work: Path, name: str, adapter: TypeAdapter) -> list:
    try:
        return adapter.validate_json(_read(work, name))
    except ValidationError as exc:
        raise FinalizeError(f"{name}: invalid: {_describe(exc)}") from None


def _judged(work: Path, repo: Path) -> list[JudgedFinding]:
    if not (work / "judged.jsonl").exists():
        return []  # Quick: no judge agents ran
    out = []
    for n, line in enumerate(_read(work, "judged.jsonl").split("\n"), 1):
        if not line.strip():
            continue
        try:
            judged = JudgedFinding.model_validate_json(line)
        except ValidationError as exc:
            raise FinalizeError(
                f"judged.jsonl:{n}: invalid judged finding: {_describe(exc)}"
            ) from None
        if not contained(repo, judged.path):
            raise FinalizeError(f"judged.jsonl:{n}: path resolves outside the repo")
        out.append(judged)
    return out


def _judged_fields(j: JudgedFinding) -> dict:
    capped = j.severity in CONFIDENCE_CAPPED and j.confidence == Confidence.HIGH
    return j.model_dump(mode="json") | {
        "origin": Origin.JUDGED.value,
        "redacted": False,
        "confidence": (Confidence.MED if capped else j.confidence).value,
        "anchor": anchor_for(j.anchor),  # redacted before hashing (R-1)
    }


def _cap(result: DimensionResult, tools: dict[str, ToolStatus]) -> DimensionResult:
    ran = any(tools.get(t) == ToolStatus.RAN for t in CORE_INPUTS[result.dimension])
    if result.rating == Rating.STRONG and not ran:
        return result.model_copy(update={"rating": Rating.ADEQUATE, "capped": True})
    return result


def _previous(repo: Path, root: Path) -> list[Finding]:
    """Findings of the newest report this tool wrote, by its stamp — at the same commit, the one
    about to be replaced — or [] when there is none.

    The reports root sits inside the target, which may itself ship a report dir: one git tracks
    is the target's, not ours, and is never read. Nothing is read through a symlink, a stamp dated
    in the future is ignored, and an unreadable report is skipped without echoing it."""
    listed = run_git(
        repo, "ls-files", "-z", "--end-of-options", "--", str(REPORTS_ROOT)
    )
    if listed.returncode != 0:
        return []  # fail closed: without the tracked list a planted report could pass as ours
    tracked = {
        Path(p).relative_to(REPORTS_ROOT).parts[0]
        for p in listed.stdout.split("\0")
        if p
    }
    now, best = datetime.now(UTC), None
    for d in root.iterdir():
        if (
            not REPORT_NAME.fullmatch(d.name)
            or d.name in tracked
            or d.is_symlink()
            or not d.is_dir()
        ):
            continue
        try:
            when = Summary.model_validate_json(
                read_regular(d / "summary.json")
            ).stamp.date_utc
            findings = _findings_jsonl(read_regular(d / "findings.jsonl"))
        except (OSError, UnicodeDecodeError, ValidationError):
            continue
        if when <= now and (best is None or when > best[0]):
            best = (when, findings)
    return [] if best is None else best[1]


def _findings_jsonl(text: str) -> list[Finding]:
    return [
        Finding.model_validate_json(line) for line in text.splitlines() if line.strip()
    ]


def _tool_version() -> str:
    try:
        return metadata.version("aa-ma")
    except metadata.PackageNotFoundError:
        return "0+unknown"


def _write(
    tmp: Path, summary: Summary, findings: list[Finding], sarif_doc: dict, work: Path
) -> None:
    """Everything but report.md, which is rendered from the redacted outputs by _gate."""
    (tmp / "summary.json").write_text(
        summary.model_dump_json(indent=2) + "\n", encoding="utf-8"
    )
    (tmp / "findings.jsonl").write_text(
        "".join(f.model_dump_json() + "\n" for f in findings), encoding="utf-8"
    )
    (tmp / "findings.sarif").write_text(
        json.dumps(sarif_doc, indent=2) + "\n", encoding="utf-8"
    )
    shutil.copyfile(work / "run.log", tmp / "run.log")


def _gate(tmp: Path) -> None:
    """Secret gate; count what it redacted; render report.md from the redacted outputs; gate again;
    re-validate every output against the models and the SARIF invariants."""
    try:
        hits = secrets.scan(tmp).hits
        if hits:
            secrets.redact(tmp, hits)
        findings = _findings_jsonl((tmp / "findings.jsonl").read_text(encoding="utf-8"))
        summary = Summary.model_validate_json(
            (tmp / "summary.json").read_text(encoding="utf-8")
        )
        counts = summary.counts.model_copy(
            update={"redacted": sum(f.redacted for f in findings)}
        )
        summary = summary.model_copy(update={"counts": counts})
        (tmp / "summary.json").write_text(
            summary.model_dump_json(indent=2) + "\n", encoding="utf-8"
        )
        (tmp / "report.md").write_text(
            report_md.render(summary, findings), encoding="utf-8"
        )
        if secrets.scan(tmp).hits:
            raise FinalizeError("secret gate: hits remain after redaction")
        Summary.model_validate_json((tmp / "summary.json").read_text(encoding="utf-8"))
        sarif.verify(json.loads((tmp / "findings.sarif").read_text(encoding="utf-8")))
    except (secrets.GateError, ValidationError, ValueError) as exc:
        raise FinalizeError(
            f"output gate refused the report: {_describe(exc)}"
        ) from None


def _swap(root: Path, tmp: Path, target: Path) -> None:
    """Rename tmp over target; if that fails after the old report moved aside, move it back."""
    if not os.path.lexists(target):
        os.rename(tmp, target)
        return
    if target.is_symlink() or not target.is_dir():
        raise FinalizeError(f"{target}: refusing to replace a symlink or non-directory")
    old = Path(tempfile.mkdtemp(prefix=".old-", dir=root))
    try:
        os.replace(target, old / target.name)
    except OSError:
        old.rmdir()
        raise
    try:
        os.rename(tmp, target)
    except OSError:
        try:
            os.replace(old / target.name, target)
        except OSError:
            # Never delete the only copy: leave it where it is and say so.
            raise FinalizeError(
                f"could not install the report, and the previous one is kept in {old}"
            ) from None
        shutil.rmtree(old, ignore_errors=True)
        raise
    shutil.rmtree(old, ignore_errors=True)


def finalize(repo: Path, workdir: Path) -> Path:
    """Build `<sha12>[-dirty]` from the work dir; returns it. The work dir is removed on success."""
    repo, work = Path(repo).absolute(), Path(workdir).absolute()
    root = repo / REPORTS_ROOT
    if (
        work.parent != root
        or not work.name.startswith(WORK_PREFIX)
        or work.is_symlink()
        or not work.is_dir()
    ):
        raise FinalizeError(f"{work}: not a work dir under {root}")
    try:
        measured = MeasureDoc.model_validate_json(_read(work, "measure.json"))
    except ValidationError as exc:
        raise FinalizeError(f"measure.json: invalid: {_describe(exc)}") from None
    stamp = measured.stamp
    if head_stamp(repo)[:2] != (stamp.sha12, stamp.dirty):
        raise FinalizeError(
            f"HEAD moved since measure (stamped {stamp.sha12}) — re-run measure"
        )
    judged = _judged(work, repo)
    ratings = _load(work, "ratings.json", TypeAdapter(list[DimensionResult]))
    ledger = _load(work, "ledger.json", TypeAdapter(list[LedgerEntry]))

    kept = [_judged_fields(j) for j in judged if j.refutation != Refutation.REFUTED]
    fields = [*(f.model_dump(mode="json") for f in measured.measured), *kept]
    ids = assign_ids(
        (f["dimension"], f["rule"], f["path"], f["anchor"]) for f in fields
    )
    current = [
        Finding.model_validate_json(json.dumps(f | {"id": i}))
        for f, i in zip(fields, ids, strict=True)
    ]
    pending = [
        f.id
        for f in current
        if f.severity in REFUTE_REQUIRED and f.refutation == Refutation.PENDING
    ]
    if pending:
        raise FinalizeError(
            f"refutation pending for {', '.join(pending)} — run the refuter first"
        )

    previous = _previous(repo, root)
    states = compare([f.id for f in previous], [f.id for f in current])
    by_severity = Counter(f.severity.value for f in current)
    summary = Summary(
        schema_version=SCHEMA_VERSION,
        stamp=stamp,
        dimensions=[_cap(r, stamp.tools) for r in ratings],
        ledger=ledger,
        metrics=measured.metrics,
        counts=Counts(
            findings=len(current), refuted=len(judged) - len(kept), **by_severity
        ),
        baseline=Baseline(**Counter(states.values())),
    )
    fixed = [f for f in previous if states.get(f.id) == "fixed"]
    baseline = {i: s for i, s in states.items() if s != "fixed"}
    sarif_doc = sarif.to_sarif(current, _tool_version(), baseline, fixed)

    ensure_self_ignoring(root)
    tmp = Path(tempfile.mkdtemp(prefix=".tmp-", dir=root))
    try:
        _write(tmp, summary, current, sarif_doc, work)
        _gate(tmp)
        if os.environ.get(CRASH_SEAM) == "1":
            raise FinalizeError(f"{CRASH_SEAM}=1: stopped before the rename")
        target = root / report_name(stamp.sha12, stamp.dirty)
        try:
            _swap(root, tmp, target)
        except OSError as exc:
            raise FinalizeError(
                f"could not install the report: {exc.strerror or exc}"
            ) from None
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    shutil.rmtree(work)
    return target
