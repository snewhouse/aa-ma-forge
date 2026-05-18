"""Pydantic v2 models + enums for the aa-ma-tui parser.

Created in aa-ma-tui-tracker M1 T1.1 (2026-05-17).

The model layer is **pure data**: no I/O, no rendering. Parser feeds it,
snapshot/json/textual layers consume it.

## State Machine Justification (per L-065)

`AggregateStatus` is the per-Task derived state surfaced to the UI. Every
value must have at least one incoming transition AND at least one outgoing
transition, OR be a documented terminal state.

```
PENDING     ←─ initial state when discovered (no milestone has any
              non-PENDING step). Outgoing: → IN_PROGRESS (first step
              starts), → BLOCKED (something blocks), → ERROR (parse fail).
IN_PROGRESS ←─ at least one milestone has a non-PENDING + non-COMPLETE
              step. Outgoing: → COMPLETE (all milestones done), → BLOCKED
              (any step/milestone blocks), → ERROR (parse fail on re-read).
BLOCKED     ←─ any milestone or step Status: BLOCKED. Outgoing: → PENDING
              (block resolved), → IN_PROGRESS (work resumes),
              → COMPLETE (block resolved AND remaining work done).
COMPLETE    ←─ TERMINAL. All milestones COMPLETE. Reaching this state ends
              the task lifecycle from the UI's perspective. No outgoing
              transitions — task moves to completed/ archive externally.
ERROR       ←─ TERMINAL. Entered exclusively via try/except in
              discover_tasks when parse_task_dir raises. No outgoing —
              the task stays ERROR until the parse error is fixed and
              the task is re-discovered as PENDING/IN_PROGRESS/COMPLETE.
```

Terminal-state justification: COMPLETE and ERROR are documented terminal
nodes per L-065. Both have at least one incoming transition; both have
zero outgoing transitions by design.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, model_validator


# -----------------------------------------------------------------------------
# Enums
# -----------------------------------------------------------------------------


class MilestoneStatus(str, Enum):
    """Lifecycle states for a milestone (## header in tasks.md).

    Values:
        PENDING:     Not yet started — initial state.
        ACTIVE:      Currently being executed (set when first sub-step starts).
        IN_PROGRESS: Synonym for ACTIVE seen in some plan styles.
                     (We keep both because the regex grammar in
                     `reference.md` permits both, and we don't want the
                     parser to drop legitimate plan content.)
        COMPLETE:    All sub-steps COMPLETE, finalization protocol passed.
        BLOCKED:     Halted pending external resolution.
    """

    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETE = "COMPLETE"
    BLOCKED = "BLOCKED"


class StepStatus(str, Enum):
    """Lifecycle states for a step (### header in tasks.md).

    Values:
        PENDING:     Not yet started.
        IN_PROGRESS: Currently being executed.
        COMPLETE:    Result Log populated, work done.
        BLOCKED:     Halted; needs intervention.

    Note: per spec, steps do not have an `ACTIVE` state — only milestones
    do. Real-world `Status: ACTIVE` on a step is coerced to `IN_PROGRESS`
    by the parser (semantic equivalence; see plan_parsers.py L-052
    precedent of variant-tolerance).
    """

    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETE = "COMPLETE"
    BLOCKED = "BLOCKED"


class Mode(str, Enum):
    """Execution mode controlling HITL pause behaviour.

    Values:
        HITL: Human-in-the-loop — pauses for user input before executing.
        AFK:  Auto-dispatched — executes without user interaction.
    """

    HITL = "HITL"
    AFK = "AFK"


class Gate(str, Enum):
    """Milestone finalization gate strictness.

    Values:
        SOFT: Convention-based approval — orchestrator prompts but does not enforce.
        HARD: Refuses milestone COMPLETE without signed approval artifact
              in context-log.md.
    """

    SOFT = "SOFT"
    HARD = "HARD"


class AggregateStatus(str, Enum):
    """Per-task derived state for UI display (see module docstring for state machine).

    Values:
        PENDING:     No milestone has any non-PENDING step.
        IN_PROGRESS: At least one milestone has work underway.
        BLOCKED:     Any milestone or step is BLOCKED.
        COMPLETE:    All milestones COMPLETE — terminal.
        ERROR:       Parse failed — terminal until fixed.
    """

    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    BLOCKED = "BLOCKED"
    COMPLETE = "COMPLETE"
    ERROR = "ERROR"


# -----------------------------------------------------------------------------
# JSON output contract version (M2 T2.4)
# -----------------------------------------------------------------------------

SCHEMA_VERSION: int = 1
"""JSON output schema version. Bump on any breaking change to the shape
emitted by `aa-ma-tui --json`. Consumers should pin to a major and reject
unknown versions. Documented in `aa_ma.tui.json_output.dump()`."""


# -----------------------------------------------------------------------------
# Errors
# -----------------------------------------------------------------------------


class ParseError(Exception):
    """Raised by parse_task_dir on malformed input.

    discover_tasks() catches this and attaches the error message to the
    Task as `parse_error: str`, so the TUI can render a PARSE_ERROR badge
    without the whole discovery pipeline collapsing.
    """


# -----------------------------------------------------------------------------
# Models
# -----------------------------------------------------------------------------


class Step(BaseModel):
    """A single ### step inside a milestone block.

    Fields are deliberately minimal — the TUI only needs status + title +
    last-result snippet for rendering. Mode/Gate live on the milestone.
    """

    model_config = ConfigDict(frozen=True)

    number: str  # dotted form, e.g. "1.2"
    title: str
    status: StepStatus
    result_log: str | None = None


class Milestone(BaseModel):
    """A ## milestone block from tasks.md.

    Defaults match the spec's "absent field = default" rule (per
    reference.md L-052 tolerance pattern).
    """

    model_config = ConfigDict(frozen=True)

    number: int
    title: str
    status: MilestoneStatus
    gate: Gate = Gate.SOFT
    mode: Mode = Mode.AFK
    complexity: int | None = None
    dependencies: str | None = None
    acceptance_criteria: str | None = None
    steps: list[Step] = Field(default_factory=list)


class Task(BaseModel):
    """A single AA-MA task directory parsed into model form.

    The TUI groups tasks into 4 columns by aggregate_status (PENDING /
    IN_PROGRESS / BLOCKED / COMPLETE); ERROR is rendered with a separate
    PARSE_ERROR badge.

    aggregate_status is **derived** from milestones + parse_error via the
    after-validator. Setting it explicitly is honoured only when no
    milestones are present (e.g. discover_tasks setting ERROR for tasks
    that couldn't be parsed). When milestones ARE present, the derivation
    takes precedence — single source of truth (per L-005).

    Task is **frozen after construction** (logically immutable; the only
    "mutation" is the model_validator setting aggregate_status, which
    bypasses the freeze via `object.__setattr__`). This makes the model
    safe to share across the read-only TUI without defensive copies.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True, frozen=True)

    name: str
    root: Path
    milestones: list[Milestone] = Field(default_factory=list)
    aggregate_status: AggregateStatus = AggregateStatus.PENDING
    last_modified: datetime | None = None
    provenance_tail: list[str] = Field(default_factory=list)
    parse_error: str | None = None

    @model_validator(mode="after")
    def _derive_aggregate_status(self) -> Task:
        """Derive aggregate_status from milestones + parse_error.

        Precedence (matches state machine in module docstring):
            1. parse_error set         → ERROR     (terminal)
            2. any BLOCKED step/m'tone → BLOCKED
            3. all m'tones COMPLETE    → COMPLETE  (terminal)
            4. any in-flight step/m'tone → IN_PROGRESS
            5. otherwise               → PENDING

        Empty milestones + no parse_error → caller's explicit value is
        kept (allows discover_tasks to set ERROR for missing-tasks-file
        cases where milestones list is empty).
        """
        if self.parse_error is not None:
            object.__setattr__(self, "aggregate_status", AggregateStatus.ERROR)
            return self

        if not self.milestones:
            # Honour caller's explicit value (e.g. ERROR set by discover_tasks)
            return self

        # Collect all statuses (milestones + steps) for one-pass scan.
        has_blocked = any(m.status == MilestoneStatus.BLOCKED for m in self.milestones)
        has_blocked = has_blocked or any(
            s.status == StepStatus.BLOCKED for m in self.milestones for s in m.steps
        )
        if has_blocked:
            object.__setattr__(self, "aggregate_status", AggregateStatus.BLOCKED)
            return self

        if all(m.status == MilestoneStatus.COMPLETE for m in self.milestones):
            object.__setattr__(self, "aggregate_status", AggregateStatus.COMPLETE)
            return self

        # Any in-flight signal?
        in_flight_milestone = any(
            m.status in (MilestoneStatus.ACTIVE, MilestoneStatus.IN_PROGRESS)
            for m in self.milestones
        )
        in_flight_step = any(
            s.status in (StepStatus.IN_PROGRESS, StepStatus.COMPLETE)
            for m in self.milestones
            for s in m.steps
            # A COMPLETE step in an otherwise-PENDING milestone means work
            # has started → IN_PROGRESS at aggregate level.
        )
        if in_flight_milestone or in_flight_step:
            object.__setattr__(self, "aggregate_status", AggregateStatus.IN_PROGRESS)
            return self

        object.__setattr__(self, "aggregate_status", AggregateStatus.PENDING)
        return self
