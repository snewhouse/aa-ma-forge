"""The seven gate questions, answered from the Python SSoT.

`/execute-aa-ma-milestone` §6.7 / §7.1 and `verify-impl` used to answer these
with awk over `tasks.md`; ADR-0009 records why that stopped. This module
answers the same questions over :mod:`aa_ma.grammar` (heading structure),
:mod:`aa_ma.enforce` (field reads) and :mod:`aa_ma.plan_parsers` (canonical
sets) — nothing here recognises a heading or a field on its own.

The questions (reference.md "M5 enforcement contract"):

1. the exact heading text, consumed verbatim by §7.1's approval grep
2. which milestone is ACTIVE — refusing on 0 / 2+ / unreadable
3. how many sub-steps are ``Status: PENDING`` within it
4. ``Gate:`` → HARD/SOFT
5. ``Critical-Path:`` value, present or absent — the milestone's own, else the
   one its sub-steps agree on (disagreeing sub-steps refuse)
6. ``Prototype-Required:`` == YES, present or absent — on the milestone **or
   rolled up from any of its sub-steps** (AD-001: sub-step fields are read only
   for the milestone being answered, never file-wide)
7. a milestone block **by number** plus its ``Audit-Profile:`` (verify-impl)

Plus, for §5.2 dispatch, a sub-step's resolved ``Mode:`` (``--step``).

Exit codes are the contract's and fail closed: 0 one ACTIVE and every enforced
field readable · 1 no ACTIVE · 2 unreadable (missing file, unclosed fence,
any invalid field, orphaned sub-step) · 3 ambiguous (2+ ACTIVE, duplicate
title or number) · 4 requested number not found. If ANY milestone's own
fields are unreadable the answer is 2 even when another is cleanly ACTIVE:
we cannot know the unreadable one was not the intended subject.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass, replace
from pathlib import Path

from aa_ma.enforce import (
    GATES,
    MODES,
    PROTOTYPE_REQUIRED,
    FieldRead,
    Unreadable,
    read_enforced_field,
    read_milestone_status,
    read_step_status,
    read_tasks_text,
)
from aa_ma.grammar import (
    STEP_RE,
    Block,
    has_unterminated_fence,
    sanitize,
    split_milestones,
    split_steps,
)
from aa_ma.plan_parsers import CANONICAL_AUDIT_PROFILES, CANONICAL_CRITICAL_PATHS

EXIT_OK = 0
EXIT_NO_ACTIVE = 1
EXIT_UNREADABLE = 2
EXIT_AMBIGUOUS = 3
EXIT_NOT_FOUND = 4

MODE_SOURCES = frozenset({"step", "milestone", "default"})

JSON_SCHEMA_ID = "aa-ma-gate/1"

GATE_JSON_SCHEMA: dict = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "required": ["schema", "exit_code", "errors", "milestone", "step"],
    "additionalProperties": False,
    "properties": {
        "schema": {"const": JSON_SCHEMA_ID},
        "exit_code": {"type": "integer", "minimum": 0, "maximum": EXIT_NOT_FOUND},
        "errors": {"type": "array", "items": {"type": "string"}},
        "step": {
            "oneOf": [
                {"type": "null"},
                {
                    "type": "object",
                    "required": ["number", "heading", "status", "mode", "mode_source"],
                    "additionalProperties": False,
                    "properties": {
                        "number": {"type": "string"},
                        "heading": {"type": "string"},
                        "status": {"type": "string"},
                        "mode": {"enum": sorted(MODES)},
                        "mode_source": {"enum": sorted(MODE_SOURCES)},
                    },
                },
            ]
        },
        "milestone": {
            "oneOf": [
                {"type": "null"},
                {
                    "type": "object",
                    "required": [
                        "number",
                        "title",
                        "heading",
                        "status",
                        "gate",
                        "critical_path",
                        "prototype_required",
                        "audit_profile",
                        "pending_steps",
                    ],
                    "additionalProperties": False,
                    "properties": {
                        "number": {"type": "string"},
                        "title": {"type": "string"},
                        "heading": {"type": "string"},
                        "status": {"type": "string"},
                        "gate": {"enum": sorted(GATES)},
                        "critical_path": {"type": ["string", "null"]},
                        "prototype_required": {"type": "boolean"},
                        "audit_profile": {"type": ["string", "null"]},
                        "pending_steps": {"type": "integer", "minimum": 0},
                    },
                },
            ]
        },
    },
}


@dataclass(frozen=True)
class MilestoneRead:
    number: str
    title: str
    heading: str  # verbatim text after `## ` — what §7.1 greps for
    status: str
    gate: str
    critical_path: str | None
    prototype_required: bool
    audit_profile: str | None
    pending_steps: int


@dataclass(frozen=True)
class StepRead:
    """One sub-step, for §5.3 Mode dispatch. `mode` is resolved: the step's
    own, else its milestone's, else HITL — the documented rule. `Mode: TYPO`
    never reaches here; the file is refused first (contract row 13)."""

    number: str
    heading: str
    status: str
    mode: str
    mode_source: str  # step | milestone | default


@dataclass(frozen=True)
class GateAnswer:
    exit_code: int
    milestone: MilestoneRead | None
    errors: tuple[str, ...]
    step: StepRead | None = None

    def to_json(self) -> dict:
        return {
            "schema": JSON_SCHEMA_ID,
            "exit_code": self.exit_code,
            "errors": list(self.errors),
            "milestone": asdict(self.milestone) if self.milestone else None,
            "step": asdict(self.step) if self.step else None,
        }

    def to_kv(self) -> str:
        """`key=value` lines for the bash callers, which have no JSON parser.

        The value is everything after the first `=`, verbatim — a heading may
        itself contain `=`, `\\` or `"`, and this is how it reaches §7.1's
        approval grep byte-exact. Headings and field values are single lines
        by construction; error strings embed a *path* and an exception text,
        which are not, so every value has `\\n` escaped — one value, one line,
        or a crafted path could emit a forged `exit_code=` line. Booleans are
        YES/NO, null is empty.
        """

        def kv(key: str, value: object) -> str:
            if isinstance(value, bool):
                value = "YES" if value else "NO"
            text = "" if value is None else str(value)
            return f"{key}={text.replace(chr(10), chr(92) + 'n')}"

        lines = [kv("exit_code", self.exit_code)]
        if self.milestone:
            lines.extend(kv(k, v) for k, v in asdict(self.milestone).items())
        if self.step:
            lines.extend(kv(f"step_{k}", v) for k, v in asdict(self.step).items())
        lines.extend(kv("error", e) for e in self.errors)
        return "\n".join(lines) + "\n"


def _heading(block: Block) -> str:
    return block.text.split("\n", 1)[0].lstrip("#").strip()


def _own_text(block: Block) -> str:
    # Fields between the `##` heading and the first `###` are the milestone's
    # own; a sub-step's `Status:` must never stand in for the milestone's.
    steps = split_steps(block.text)
    return block.text if not steps else block.text[: block.text.index(steps[0].text)]


def _read_or_error(read: FieldRead, where: str, errors: list[str]) -> FieldRead:
    if not read.is_valid:
        errors.append(f"{where}: {read.error}")
    return read


def _read_milestone(block: Block, errors: list[str]) -> MilestoneRead:
    """Read one milestone's enforced fields; append every refusal to `errors`."""
    heading = _heading(block)
    own = _own_text(block)
    status = _read_or_error(read_milestone_status(own), heading, errors)
    if not status.present:
        errors.append(
            f"{heading}: no Status: field — a milestone the gate cannot read is not clean"
        )
    gate = _read_or_error(read_enforced_field(own, "Gate", GATES), heading, errors)
    _read_or_error(read_enforced_field(own, "Mode", MODES), heading, errors)
    critical = _read_or_error(
        read_enforced_field(own, "Critical-Path", CANONICAL_CRITICAL_PATHS),
        heading,
        errors,
    )
    proto = _read_or_error(
        read_enforced_field(own, "Prototype-Required", PROTOTYPE_REQUIRED),
        heading,
        errors,
    )
    audit = _read_or_error(
        read_enforced_field(own, "Audit-Profile", CANONICAL_AUDIT_PROFILES),
        heading,
        errors,
    )
    return MilestoneRead(
        number=block.number,
        title=block.title,
        heading=heading,
        status=status.value or "",
        gate=gate.value or "SOFT",  # documented default, claude-code/rules/aa-ma.md
        critical_path=critical.value,
        prototype_required=proto.value == "YES",
        audit_profile=audit.value,
        pending_steps=0,
    )


@dataclass(frozen=True)
class StepsRead:
    """What the answered milestone's sub-steps contribute: the PENDING count
    (Q3), whether any of them declares ``Prototype-Required: YES`` (Q6
    roll-up), and their ``Critical-Path`` value (Q5 roll-up — the milestone's
    own value wins; sub-steps that disagree with each other are a refusal,
    since the gate cannot know which review to demand). An invalid or empty
    token on any sub-step is a refusal, exactly as at milestone level — the
    blank ``- **Prototype-Required:**`` slot the old tasks-template emitted is
    ``empty value``, not ``NO``."""

    pending: int
    prototype_required: bool
    critical_path: str | None


def _read_steps(block: Block, heading: str, errors: list[str]) -> StepsRead:
    pending = 0
    prototype = False
    critical_paths: dict[str, str] = {}  # value -> first sub-step declaring it
    for step in split_steps(block.text):
        where = f"{heading} / {_heading(step)}"
        status = _read_or_error(read_step_status(step.text), where, errors)
        if not status.present:
            errors.append(
                f"{where}: no Status: field — its PENDING count is unknowable"
            )
        _read_or_error(read_enforced_field(step.text, "Mode", MODES), where, errors)
        proto = _read_or_error(
            read_enforced_field(step.text, "Prototype-Required", PROTOTYPE_REQUIRED),
            where,
            errors,
        )
        critical = _read_or_error(
            read_enforced_field(step.text, "Critical-Path", CANONICAL_CRITICAL_PATHS),
            where,
            errors,
        )
        pending += status.value == "PENDING"
        prototype |= proto.value == "YES"
        if critical.value is not None:
            critical_paths[critical.value] = where
    if len(critical_paths) > 1:
        errors.append(
            f"{heading}: conflicting sub-step Critical-Path values — "
            + "; ".join(f"{v} ({w})" for v, w in critical_paths.items())
        )
    return StepsRead(
        pending=pending,
        prototype_required=prototype,
        critical_path=next(iter(critical_paths), None),
    )


def _read_step(
    block: Block, step: str, read: MilestoneRead, errors: list[str]
) -> StepRead | None:
    hits = [s for s in split_steps(block.text) if s.number == step]
    if not hits:
        errors.append(f"{read.heading}: no sub-step numbered {step!r}")
        return None
    if len(hits) > 1:
        errors.append(
            f"{read.heading}: {len(hits)} sub-steps numbered {step!r}: "
            + "; ".join(_heading(h) for h in hits)
        )
        return None
    own = read_enforced_field(hits[0].text, "Mode", MODES)
    parent = read_enforced_field(_own_text(block), "Mode", MODES)
    if own.present:
        mode, source = own.value, "step"
    elif parent.present:
        mode, source = parent.value, "milestone"
    else:
        mode, source = "HITL", "default"
    return StepRead(
        number=hits[0].number,
        heading=_heading(hits[0]),
        status=read_step_status(hits[0].text).value or "",
        mode=mode,
        mode_source=source,
    )


def answer(
    path: Path, number: str | None = None, step: str | None = None
) -> GateAnswer:
    """Answer the gate questions for the ACTIVE milestone, or by `number`.

    With `step` (requires `number`) also resolve that sub-step's Mode for
    §5.2 dispatch.
    """
    if step is not None and number is None:
        raise ValueError("--step requires --milestone")
    errors: list[str] = []
    try:
        text = read_tasks_text(path)
    except Unreadable as exc:
        return GateAnswer(EXIT_UNREADABLE, None, (str(exc),))
    if has_unterminated_fence(text):
        return GateAnswer(
            EXIT_UNREADABLE,
            None,
            (f"{path}: unclosed code fence hides everything after it",),
        )
    blocks = split_milestones(text)
    if not blocks:
        return GateAnswer(
            EXIT_UNREADABLE, None, (f"{path}: no milestone heading recognised",)
        )

    # A sub-step outside every milestone block belongs to no milestone. Row 16
    # says a bare `##` closes the block; without this rule that would hide the
    # sub-steps after it, and hiding a PENDING sub-step is a false PASS.
    inside = sum(len(split_steps(b.text)) for b in blocks)
    total = len(STEP_RE.findall(sanitize(text)))
    if total != inside:
        errors.append(
            f"{path}: {total - inside} orphan sub-step heading(s) outside any milestone block"
        )

    reads = [_read_milestone(b, errors) for b in blocks]

    if number is not None:
        hits = [(b, r) for b, r in zip(blocks, reads) if r.number == number]
        if not hits:
            return GateAnswer(
                EXIT_NOT_FOUND, None, (*errors, f"no milestone numbered {number!r}")
            )
        if len(hits) > 1:
            return GateAnswer(
                EXIT_AMBIGUOUS,
                None,
                (*errors, f"{len(hits)} milestones numbered {number!r}"),
            )
        block, read = hits[0]
    else:
        headings = [r.heading for r in reads]
        numbers = [r.number for r in reads]
        dupes = sorted({h for h in headings if headings.count(h) > 1})
        # Duplicate NUMBERS too: `Milestone 1: Foo` and `Milestone 1: Foo bar`
        # have distinct headings, but §7.1's approval grep and §6.7's evidence
        # grep are prefix matches, so one milestone's lines satisfied the other.
        dupes += sorted({f"number {n!r}" for n in numbers if numbers.count(n) > 1})
        if dupes:
            errors.append(
                "duplicate milestone heading(s)/number(s): " + "; ".join(dupes)
            )
        active = [(b, r) for b, r in zip(blocks, reads) if r.status == "ACTIVE"]
        if errors:
            return GateAnswer(
                EXIT_UNREADABLE if not dupes else EXIT_AMBIGUOUS, None, tuple(errors)
            )
        if not active:
            return GateAnswer(EXIT_NO_ACTIVE, None, ("no milestone is ACTIVE",))
        if len(active) > 1:
            return GateAnswer(
                EXIT_AMBIGUOUS,
                None,
                tuple(
                    f"more than one milestone is ACTIVE: {r.heading}" for _, r in active
                ),
            )
        block, read = active[0]

    steps = _read_steps(block, read.heading, errors)
    if errors:
        return GateAnswer(EXIT_UNREADABLE, None, tuple(errors))
    milestone = replace(
        read,
        pending_steps=steps.pending,
        prototype_required=read.prototype_required or steps.prototype_required,
        critical_path=read.critical_path or steps.critical_path,
    )
    step_read = None
    if step is not None:
        step_read = _read_step(block, step, read, errors)
        if step_read is None:
            code = (
                EXIT_AMBIGUOUS
                if any("sub-steps numbered" in e for e in errors)
                else EXIT_NOT_FOUND
            )
            return GateAnswer(code, None, tuple(errors))
    return GateAnswer(EXIT_OK, milestone, (), step_read)


_EPILOG = """\
exit codes:
  0  exactly one ACTIVE milestone; every enforced field read cleanly
  1  no ACTIVE milestone
  2  unreadable: file missing, unclosed fence, any invalid field, orphan sub-step
  3  ambiguous: 2+ ACTIVE, or duplicate milestone heading / number
  4  --milestone N not found
JSON is always written to stdout, including on refusal; `errors` says why.
"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="aa-ma-gate",
        description="Answer the /execute-aa-ma-milestone gate questions from tasks.md.",
        epilog=_EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("tasks_md", help="path to [task]-tasks.md")
    parser.add_argument(
        "--milestone", metavar="N", help="read milestone N instead of the ACTIVE one"
    )
    parser.add_argument(
        "--step",
        metavar="N.M",
        help="with --milestone: also resolve this sub-step's Mode",
    )
    parser.add_argument(
        "--format",
        choices=("json", "kv"),
        default="json",
        help="json (default) or kv: one key=value per line for shell callers",
    )
    args = parser.parse_args(argv)
    if args.step is not None and args.milestone is None:
        parser.error("--step requires --milestone")
    try:
        result = answer(Path(args.tasks_md), args.milestone, args.step)
    except Exception as exc:  # last resort: the envelope contract holds even here
        result = GateAnswer(EXIT_UNREADABLE, None, (f"internal error: {exc!r}",))
    if args.format == "kv":
        sys.stdout.write(result.to_kv())
    else:
        json.dump(result.to_json(), sys.stdout, indent=2)
        sys.stdout.write("\n")
    return result.exit_code


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
