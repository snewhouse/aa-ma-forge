"""Pure parser: AA-MA task directory → Task model.

Created in aa-ma-tui-tracker M1 (2026-05-17).

Grammar tolerated (per reference.md `tasks.md grammar`):
    - Milestone line: `^## Milestone (\\d+): (.+)$`
    - Step line:      `^### Step (\\d+\\.\\d+): (.+)$`
    - Status:         `^[- ]*(\\*\\*)?Status:?(\\*\\*)?\\s*VALUE`  (covers
                      plain, bold-pair, split-bold forms)
    - Mode/Gate:      same shape as Status
    - Complexity:     `^[- ]*(\\*\\*)?Complexity:(\\*\\*)?\\s*\\d+%?$`
    - Result Log:     `^- Result Log:\\s*(.*)$`

Tolerance contract (per L-052):
    - Missing Status on a milestone or step → treated as PENDING (default).
    - Missing Mode → AFK (default).
    - Missing Gate → SOFT (default).
    - `Status: ACTIVE` on a step → coerced to `IN_PROGRESS` (steps don't
      have an ACTIVE state per spec).

Failure modes:
    - No `{name}-tasks.md` in the directory → ParseError.
    - tasks.md file present but contains zero `## Milestone N:` headers
      → ParseError. discover_tasks() catches and attaches `parse_error`.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path

from aa_ma.tui.model import (
    AggregateStatus,
    Gate,
    Milestone,
    MilestoneStatus,
    Mode,
    ParseError,
    Step,
    StepStatus,
    Task,
)

# -----------------------------------------------------------------------------
# Regex grammar
# -----------------------------------------------------------------------------

_MILESTONE_RE = re.compile(r"^## Milestone (\d+):\s*(.+?)\s*$", re.MULTILINE)
_STEP_RE = re.compile(r"^### Step (\d+\.\d+):\s*(.+?)\s*$", re.MULTILINE)


def _field_pattern(field_name: str) -> re.Pattern[str]:
    """Build a tolerant regex for a `- Field: VALUE` line.

    Tolerates leading list bullet, bold-pair `**Field:**`, split-bold
    `**Field**:`, and variable whitespace.
    """
    return re.compile(
        rf"^[ \t]*-?[ \t]*\*{{0,2}}{re.escape(field_name)}\*{{0,2}}:\*{{0,2}}[ \t]*(\S.*?)\s*$",
        re.MULTILINE,
    )


_STATUS_RE = _field_pattern("Status")
_MODE_RE = _field_pattern("Mode")
_GATE_RE = _field_pattern("Gate")
_COMPLEXITY_RE = _field_pattern("Complexity")
_RESULT_LOG_RE = re.compile(
    r"^-[ \t]*Result Log:[ \t]*(.*?)\s*$",
    re.MULTILINE,
)


# -----------------------------------------------------------------------------
# Field extractors
# -----------------------------------------------------------------------------


def _extract_milestone_status(block: str) -> MilestoneStatus:
    """Read Status field from a milestone block; default PENDING if absent."""
    match = _STATUS_RE.search(block)
    if match is None:
        return MilestoneStatus.PENDING
    value = match.group(1).strip()
    try:
        return MilestoneStatus(value)
    except ValueError:
        return MilestoneStatus.PENDING


def _extract_step_status(block: str) -> StepStatus:
    """Read Status field from a step block; default PENDING.

    Coerces `ACTIVE` → `IN_PROGRESS` (semantic equivalence per spec).
    """
    match = _STATUS_RE.search(block)
    if match is None:
        return StepStatus.PENDING
    value = match.group(1).strip()
    if value == "ACTIVE":
        return StepStatus.IN_PROGRESS
    try:
        return StepStatus(value)
    except ValueError:
        return StepStatus.PENDING


def _extract_mode(block: str) -> Mode:
    """Read Mode field; default AFK."""
    match = _MODE_RE.search(block)
    if match is None:
        return Mode.AFK
    value = match.group(1).strip()
    try:
        return Mode(value)
    except ValueError:
        return Mode.AFK


def _extract_gate(block: str) -> Gate:
    """Read Gate field; default SOFT."""
    match = _GATE_RE.search(block)
    if match is None:
        return Gate.SOFT
    value = match.group(1).strip()
    try:
        return Gate(value)
    except ValueError:
        return Gate.SOFT


def _extract_complexity(block: str) -> int | None:
    """Read Complexity field as int; None if absent or unparseable."""
    match = _COMPLEXITY_RE.search(block)
    if match is None:
        return None
    raw = match.group(1).strip().rstrip("%")
    try:
        return int(raw)
    except ValueError:
        return None


def _extract_result_log(block: str) -> str | None:
    """Read Result Log field; None if absent or blank."""
    match = _RESULT_LOG_RE.search(block)
    if match is None:
        return None
    value = match.group(1).strip()
    return value if value else None


# -----------------------------------------------------------------------------
# Block splitting
# -----------------------------------------------------------------------------


def _split_milestone_blocks(text: str) -> list[tuple[int, str, str]]:
    """Yield (number, title, block_text) for each ## Milestone N: heading.

    Block text spans from the milestone header through to the next
    milestone header (or EOF).
    """
    matches = list(_MILESTONE_RE.finditer(text))
    if not matches:
        return []
    blocks: list[tuple[int, str, str]] = []
    for i, m in enumerate(matches):
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        number = int(m.group(1))
        title = m.group(2).strip()
        blocks.append((number, title, text[start:end]))
    return blocks


def _split_step_blocks(milestone_block: str) -> list[tuple[str, str, str]]:
    """Yield (number, title, block_text) for each ### Step N.M: heading
    inside a milestone block."""
    matches = list(_STEP_RE.finditer(milestone_block))
    if not matches:
        return []
    blocks: list[tuple[str, str, str]] = []
    for i, m in enumerate(matches):
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(milestone_block)
        number = m.group(1)
        title = m.group(2).strip()
        blocks.append((number, title, milestone_block[start:end]))
    return blocks


# -----------------------------------------------------------------------------
# File helpers (T1.8 + T1.9)
# -----------------------------------------------------------------------------


_PROVENANCE_TAIL_DEFAULT = 5

# Canonical 5-file AA-MA name suffixes, used by _max_mtime to scan the dir.
_AA_MA_FILE_SUFFIXES = (
    "-tasks.md",
    "-plan.md",
    "-reference.md",
    "-context-log.md",
    "-provenance.log",
)


def _provenance_tail(
    path: Path, name: str, n: int = _PROVENANCE_TAIL_DEFAULT
) -> list[str]:
    """Return the last `n` non-blank lines of `{name}-provenance.log`.

    Returns [] if the log file is absent. Lines are stripped of trailing
    whitespace; blank lines are dropped (per task UX — blanks are noise).
    """
    log = path / f"{name}-provenance.log"
    if not log.is_file():
        return []
    lines = [
        ln.rstrip() for ln in log.read_text(encoding="utf-8").splitlines() if ln.strip()
    ]
    return lines[-n:] if lines else []


def _max_mtime(path: Path, name: str) -> datetime | None:
    """Return the most-recent mtime across the 5 standard AA-MA files in `path`.

    Returns None if NONE of the files exist (caller's tasks.md presence
    check should prevent that case).
    """
    mtimes: list[float] = []
    for suffix in _AA_MA_FILE_SUFFIXES:
        f = path / f"{name}{suffix}"
        if f.is_file():
            mtimes.append(f.stat().st_mtime)
    if not mtimes:
        return None
    return datetime.fromtimestamp(max(mtimes), tz=timezone.utc)


# -----------------------------------------------------------------------------
# Public API
# -----------------------------------------------------------------------------


def parse_task_dir(path: Path) -> Task:
    """Parse a single AA-MA task directory into a Task model.

    Args:
        path: Directory containing `{name}-tasks.md` (and the other 4
              standard AA-MA files; only tasks.md is required for parsing).

    Returns:
        Task with name, root, parsed milestones/steps.

    Raises:
        ParseError: tasks.md missing, or has zero `## Milestone N:` headers.
    """
    name = path.name
    tasks_file = path / f"{name}-tasks.md"
    if not tasks_file.is_file():
        raise ParseError(f"missing tasks file: {tasks_file}")

    text = tasks_file.read_text(encoding="utf-8")
    milestone_blocks = _split_milestone_blocks(text)
    if not milestone_blocks:
        raise ParseError(f"no `## Milestone N:` headers found in {tasks_file}")

    milestones: list[Milestone] = []
    for number, title, block in milestone_blocks:
        steps: list[Step] = []
        for s_number, s_title, s_block in _split_step_blocks(block):
            steps.append(
                Step(
                    number=s_number,
                    title=s_title,
                    status=_extract_step_status(s_block),
                    result_log=_extract_result_log(s_block),
                )
            )
        milestones.append(
            Milestone(
                number=number,
                title=title,
                status=_extract_milestone_status(block),
                gate=_extract_gate(block),
                mode=_extract_mode(block),
                complexity=_extract_complexity(block),
                steps=steps,
            )
        )

    return Task(
        name=name,
        root=path,
        milestones=milestones,
        last_modified=_max_mtime(path, name),
        provenance_tail=_provenance_tail(path, name),
    )


def discover_tasks(roots: list[Path]) -> list[Task]:
    """Scan root directories for AA-MA task subdirectories.

    A "task directory" is any sub-directory of a root that contains a
    `{name}-tasks.md` file (matching the directory's own name).

    Per-task parse failures DO NOT raise — the failing directory is
    represented as a Task with `aggregate_status=ERROR` and `parse_error`
    populated, so the UI can render a PARSE_ERROR badge without the whole
    discovery pipeline collapsing.

    Args:
        roots: Directories to scan (e.g. `~/.claude/dev/active/`).
               Non-existent roots are silently skipped.

    Returns:
        List of Task objects (one per discovered sub-directory),
        deduplicated by absolute root path (later roots win on duplicates).
    """
    seen: dict[Path, Task] = {}
    for root in roots:
        if not root.is_dir():
            continue
        for child in sorted(root.iterdir()):
            if not child.is_dir():
                continue
            try:
                task = parse_task_dir(child)
            except ParseError as exc:
                task = Task(
                    name=child.name,
                    root=child,
                    aggregate_status=AggregateStatus.ERROR,
                    parse_error=str(exc),
                )
            seen[child.resolve()] = task
    return list(seen.values())
