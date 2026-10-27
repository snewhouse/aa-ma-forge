"""aa-ma-impact: gate-computed ``IMPACT_VERIFIED`` (§6.7 fence 4; ticket T7, ADR-0009 scope).

Compares what a milestone changed with what its plan Contract predicted, and with what
usually changes alongside it, then requires every difference to be explained:

- **unpredicted** — changed, but no Contract row names it (a directory row covers what is
  beneath it);
- **predicted-unchanged** — a Contract row whose path did not change;
- **co-change miss** — a file that shared >= ``COCHANGE_MIN_SHARED`` commits and >=
  ``COCHANGE_MIN_RATIO`` of a changed file's commits (codemem ``co_changes``, import/call-
  linked files excluded by codemem) but did not change itself.

Each needs an ``Impact-Explained: <path> — <reason>`` line in the milestone's tasks.md
block. Separately, every derived ``Critical-Path`` value
(:func:`aa_ma.plan_parsers.derive_critical_paths`) needs a ``CRITICAL_PATH_REVIEW`` line
for the milestone naming each triggering file, or the glob it matched.

Changed set = ``git diff <base>`` against the working tree (committed, staged and unstaged)
plus untracked, non-ignored files: §8.1 commits after the gate, so a pre-commit tree must
not hide anything. codemem runs as a separate program: ``aa_ma`` never imports it.

Exit codes: 0 pass · 1 unexplained / unreviewed / stale / no Contract rows · 2 usage,
unreadable input or git error · 3 codemem index unavailable or a refresh failed (fails
closed) · 5 not applicable (the plan predates ``IMPACT_CUTOVER``; prints why).
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import logging
import os
import re
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

from aa_ma import gitutil
from aa_ma.contract_rows import milestone_contract_lines, milestone_contract_rows
from aa_ma.enforce import (
    Unreadable,
    has_gate_approval,
    read_tasks_text,
    read_text_field_lines,
)
from aa_ma.grammar import split_milestones
from aa_ma.logsetup import configure_logging
from aa_ma.plan_parsers import CRITICAL_PATH_GLOBS, derive_critical_paths

log = logging.getLogger(__name__)

IMPACT_CUTOVER: str = "9999-12-31"  # sentinel until M14.1 sets the v0.18.0 release date
COCHANGE_MIN_SHARED: int = 5  # T7; 11.1 replay: 5 | 11 lines over 15 | 12 milestones
COCHANGE_MIN_RATIO: float = 0.5  # >= semantics (codemem co_changes)
COCHANGE_WINDOW_COMMITS: int = (
    500  # `refresh-commits --limit`; 2000 tripled stale pairs (11.1)
)
COCHANGE_MAX_SHARED, COCHANGE_MAX_RATIO = (
    20,
    0.9,
)  # bounds of a Cochange-Threshold override
IMPACT_EXCLUDE: tuple[str, ...] = (
    ".claude/dev/**",
    "docs/architecture/**",
    "tests/golden/**",
    "uv.lock",
    "CHANGELOG.md",
)
CODEMEM_TIMEOUT_S = 300.0  # one refresh can rebuild the index; ~1 s on this repo

# P6: the packages whose public API fence 4 diffs (griffe, static), and their search path.
API_PACKAGES: dict[str, str] = {"aa_ma": "src", "codemem": "packages/codemem-mcp/src"}

EXIT_PASS, EXIT_FAIL, EXIT_USAGE, EXIT_NO_INDEX, EXIT_NOT_APPLICABLE = 0, 1, 2, 3, 5

_CREATED_RE = re.compile(
    r"^(?:\*\*Created:\*\*|Created:)[ \t]*(\d{4}-\d{2}-\d{2})", re.M
)
_H2_RE = re.compile(r"^##(?:[ \t]|$)", re.M)
_THRESHOLD_RE = re.compile(
    r"^[ \t]*(?:-[ \t]+)?Cochange-Threshold:[ \t]*(\S+)[ \t]+(\S+)[ \t]*$", re.M
)
_API_BREAK_RE = re.compile(
    r"^(?:-[ \t]+)?API-Break:[ \t]*`?([A-Za-z_][\w.]*)`?[ \t]+[—–-]+[ \t]*\S"
)
_EXPLAINED_RE = re.compile(r"^`?([^`\s]+)`?(?:[ \t]+[—–-]+[ \t]*(.*))?$")


class _Stop(Exception):
    """Ends ``compute`` early with an exit code and the one line saying why."""

    def __init__(self, code: int, reason: str) -> None:
        super().__init__(reason)
        self.code, self.reason = code, reason


@dataclass
class ImpactReport:
    """What fence 4 decides on. ``exit_code`` and ``reason`` are always set."""

    exit_code: int
    reason: str = ""
    changed: list[str] = field(default_factory=list)
    predicted: list[str] = field(default_factory=list)
    unpredicted: list[str] = field(default_factory=list)
    predicted_unchanged: list[str] = field(default_factory=list)
    cochange_missing: dict[str, list[str]] = field(default_factory=dict)
    api_breaks_undeclared: list[str] = field(default_factory=list)
    api_diff: str = ""
    derived_critical_paths: dict[str, list[str]] = field(default_factory=dict)
    unreviewed_critical_paths: dict[str, list[str]] = field(default_factory=dict)
    explained: dict[str, str] = field(default_factory=dict)
    unexplained: list[str] = field(default_factory=list)

    def to_kv(self) -> str:
        """``key=value`` lines for fence 4; every value on one line (a path cannot forge a key)."""

        def kv(key: str, value: object) -> str:
            return f"{key}={str(value).replace(chr(10), ' ').replace(chr(13), ' ')}"

        derived = ";".join(
            f"{v}:{','.join(fs)}" for v, fs in self.derived_critical_paths.items()
        )
        lines = [
            kv("exit_code", self.exit_code),
            kv("reason", self.reason),
            kv("changed", len(self.changed)),
            kv("predicted", len(self.predicted)),
            kv("cochange", len(self.cochange_missing)),
            kv("unexplained", len(self.unexplained)),
            kv("api_breaks", len(self.api_breaks_undeclared)),
            kv("api_diff", self.api_diff),
            kv("derived_cp", derived),
        ]
        lines += [
            kv("unexplained_file", f"{self._kind(p)}:{p}") for p in self.unexplained
        ]
        lines += [kv("api_break", b) for b in self.api_breaks_undeclared]
        lines += [
            kv("unreviewed_cp", f"{v}:{f}")
            for v, fs in self.unreviewed_critical_paths.items()
            for f in fs
        ]
        return "\n".join(lines)

    def _kind(self, path: str) -> str:
        if path in self.unpredicted:
            return "unpredicted"
        if path in self.predicted_unchanged:
            return "predicted-unchanged"
        return "cochange"


def compute(  # why: the AC signature plus the 11.7 retro flag, all keyword-able
    plan_md: Path,
    tasks_md: Path,
    milestone: int,
    base: str | None,
    head: str = "HEAD",
    *,
    ignore_cutover: bool = False,
) -> ImpactReport:
    """Decide fence 4 for Milestone ``milestone``; never raises for an expected failure.

    ``head="HEAD"`` reads the working tree too; any other ref compares ``base..head`` only
    (a retro-check of merged history, 11.7).
    """
    report = ImpactReport(exit_code=EXIT_PASS)
    try:
        _compute(report, plan_md, tasks_md, str(milestone), base, head, ignore_cutover)
    except _Stop as stop:
        report.exit_code, report.reason = stop.code, stop.reason
    return report


def _compute(  # noqa: PLR0913  # why: one private step carrying compute's arguments
    report: ImpactReport,
    plan_md: Path,
    tasks_md: Path,
    milestone: str,
    base: str | None,
    head: str,
    ignore_cutover: bool,
) -> None:
    plan_text = _read(plan_md)
    if not ignore_cutover:
        _check_cutover(plan_text)
    if base is None:
        raise _Stop(
            EXIT_USAGE, "--base is required for a plan in force (no milestone window)"
        )
    repo = _toplevel(tasks_md.parent)
    try:
        gitutil.verify_ref(base, repo)
        if head != "HEAD":
            gitutil.verify_ref(head, repo)
    except gitutil.GitError as exc:
        raise _Stop(EXIT_USAGE, f"bad --base/head: {exc}") from exc
    heading, block = _milestone_block(tasks_md, milestone)
    rows = milestone_contract_rows(plan_text, milestone)
    if not rows:
        raise _Stop(EXIT_FAIL, f"no Contract Files for Milestone {milestone}")
    shared, ratio = _threshold(repo, tasks_md, base, heading)
    report.predicted = [p for _, p in rows if not _excluded(p)]
    report.changed = [p for p in _changed(repo, base, head) if not _excluded(p)]
    report.explained = _explanations(block)
    partners = _cochanges(repo, report.changed, shared, ratio)
    _classify(report, partners)
    declared = _declared_breaks(plan_text, milestone)
    report.api_diff, report.api_breaks_undeclared = _api_diff(
        repo, base, head, report.changed, declared
    )
    report.derived_critical_paths = derive_critical_paths(report.changed)
    report.unreviewed_critical_paths = _unreviewed(
        report.derived_critical_paths, tasks_md, heading
    )
    _verdict(report, milestone)


def _verdict(report: ImpactReport, milestone: str) -> None:
    problems = []
    if report.unexplained:
        problems.append(f"{len(report.unexplained)} unexplained file(s)")
    if report.api_breaks_undeclared:
        problems.append(
            f"{len(report.api_breaks_undeclared)} public API break(s) without API-Break:"
        )
    if report.unreviewed_critical_paths:
        problems.append(
            "derived Critical-Path without a CRITICAL_PATH_REVIEW naming its files: "
            + ", ".join(sorted(report.unreviewed_critical_paths))
        )
    report.exit_code = EXIT_FAIL if problems else EXIT_PASS
    report.reason = (
        "; ".join(problems)
        or f"Milestone {milestone}: every change predicted or explained"
    )


# --- inputs --------------------------------------------------------------------------------


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise _Stop(EXIT_USAGE, f"{path}: unreadable ({exc})") from exc


def _check_cutover(plan_text: str) -> None:
    first_h2 = _H2_RE.search(plan_text)
    m = _CREATED_RE.search(plan_text[: first_h2.start()] if first_h2 else plan_text)
    if m is None:
        raise _Stop(
            EXIT_NOT_APPLICABLE,
            "not applicable: the plan has no Created: date (grandfathered)",
        )
    if m.group(1) < IMPACT_CUTOVER:
        raise _Stop(
            EXIT_NOT_APPLICABLE,
            f"not applicable: plan Created: {m.group(1)} is before IMPACT_CUTOVER {IMPACT_CUTOVER} (grandfathered)",
        )


def _toplevel(start: Path) -> Path:
    try:
        return Path(
            gitutil.git(["rev-parse", "--show-toplevel"], start.resolve()).strip()
        )
    except gitutil.GitError as exc:
        raise _Stop(EXIT_USAGE, f"not in a git repository: {exc}") from exc


def _milestone_block(tasks_md: Path, milestone: str) -> tuple[str, str]:
    try:
        text = read_tasks_text(tasks_md)
    except Unreadable as exc:
        raise _Stop(EXIT_USAGE, str(exc)) from exc
    for block in split_milestones(text):
        if block.number == milestone:
            return f"Milestone {block.number}: {block.title}", block.text
    raise _Stop(EXIT_USAGE, f"{tasks_md}: no Milestone {milestone}")


def _threshold(
    repo: Path, tasks_md: Path, base: str, heading: str
) -> tuple[int, float]:
    """``Cochange-Threshold: <n> <ratio>`` from the merge-base reference.md, if approved."""
    reference = tasks_md.with_name(tasks_md.name.replace("-tasks.md", "-reference.md"))
    rel = reference.resolve().relative_to(repo).as_posix()
    try:
        text = gitutil.git(["show", f"{base}:{rel}"], repo)
    except gitutil.GitError:
        log.debug("no %s at %s; default co-change threshold", rel, base)
        return COCHANGE_MIN_SHARED, COCHANGE_MIN_RATIO
    m = _THRESHOLD_RE.search(text)
    if m is None:
        return COCHANGE_MIN_SHARED, COCHANGE_MIN_RATIO
    try:
        shared, ratio = int(m.group(1)), float(m.group(2))
    except ValueError as exc:
        raise _Stop(
            EXIT_USAGE, f"Cochange-Threshold unreadable: {m.group(0).strip()!r}"
        ) from exc
    if not (1 <= shared <= COCHANGE_MAX_SHARED and 0 < ratio <= COCHANGE_MAX_RATIO):
        raise _Stop(
            EXIT_USAGE,
            f"Cochange-Threshold {shared} {ratio} out of bounds (n <= {COCHANGE_MAX_SHARED}, ratio <= {COCHANGE_MAX_RATIO})",
        )
    title = f"Cochange-Threshold {m.group(1)} {m.group(2)} — {heading}"
    log_path = tasks_md.with_name(tasks_md.name.replace("-tasks.md", "-context-log.md"))
    if not log_path.is_file() or not has_gate_approval(_read(log_path), title):
        raise _Stop(
            EXIT_FAIL,
            f"Cochange-Threshold override needs `## [date] GATE APPROVAL: {title}`",
        )
    return shared, ratio


def _explanations(block: str) -> dict[str, str]:
    out = {}
    for value in read_text_field_lines(block, "Impact-Explained"):
        m = _EXPLAINED_RE.match(value)
        if m and m.group(2) and m.group(2).strip():
            out[m.group(1)] = m.group(2).strip()
        else:
            log.warning("Impact-Explained without a reason ignored: %r", value)
    return out


# --- the changed set -----------------------------------------------------------------------


def _changed(repo: Path, base: str, head: str) -> list[str]:
    try:
        if head == "HEAD":
            diff = gitutil.git(["diff", "--name-status", "-M", "-z", base], repo)
            untracked = gitutil.split_z(
                gitutil.git(["ls-files", "--others", "--exclude-standard", "-z"], repo)
            )
        else:
            diff = gitutil.git(["diff", "--name-status", "-M", "-z", base, head], repo)
            untracked = []
    except gitutil.GitError as exc:
        raise _Stop(EXIT_USAGE, f"git diff failed: {exc}") from exc
    return sorted({*_name_status_paths(gitutil.split_z(diff)), *untracked})


def _name_status_paths(fields: list[str]) -> list[str]:
    """Paths of a ``--name-status -z`` walk: R/C carry two (old and new), the rest one."""
    paths, i = [], 0
    while i < len(fields):
        status = fields[i]
        width = 2 if status[:1] in ("R", "C") else 1
        paths += fields[i + 1 : i + 1 + width]
        i += 1 + width
    return paths


def _excluded(path: str) -> bool:
    return any(fnmatch.fnmatchcase(path, glob) for glob in IMPACT_EXCLUDE)


# --- codemem (a separate program; aa_ma never imports it) ----------------------------------


def _codemem_bin() -> str:
    """``CODEMEM_BIN`` (no fallback), else this venv's codemem, else an absolute PATH hit."""
    if pinned := os.environ.get("CODEMEM_BIN"):
        return pinned
    beside = Path(sys.executable).with_name("codemem")
    if beside.is_file():
        return str(beside)
    found = shutil.which("codemem")
    if found and os.path.isabs(found):
        return found
    raise _Stop(
        EXIT_NO_INDEX,
        "codemem not installed — `uv sync` in the forge, then `codemem build`",
    )


def _codemem(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    argv = [_codemem_bin(), *args]
    try:
        return subprocess.run(  # noqa: S603  # why: fixed argv, no shell; paths after `--`
            argv,
            cwd=repo,
            capture_output=True,
            text=True,
            timeout=CODEMEM_TIMEOUT_S,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise _Stop(EXIT_NO_INDEX, f"codemem {args[0]} could not run: {exc}") from exc


def _cochanges(
    repo: Path, changed: list[str], shared: int, ratio: float
) -> dict[str, list[str]]:
    """Partner -> the changed files it co-changes with, after refreshing index and commits."""
    root = ["--repo-root", str(repo)]
    if _codemem(repo, "status").returncode != 0:  # no --repo-root flag; cwd is the repo
        raise _Stop(
            EXIT_NO_INDEX,
            f"no codemem index for {repo} — run `codemem build --repo-root {repo}`",
        )
    p = _codemem(repo, "refresh", *root)
    if p.returncode != 0:
        raise _Stop(
            EXIT_NO_INDEX, f"codemem refresh failed (rc {p.returncode}): {_last(p)}"
        )
    p = _codemem(
        repo, "refresh-commits", "--limit", str(COCHANGE_WINDOW_COMMITS), *root
    )
    if p.returncode != 0 or "skipped" in p.stderr:
        raise _Stop(
            EXIT_NO_INDEX,
            f"codemem refresh-commits failed or skipped (rc {p.returncode}): {_last(p)}",
        )
    if not changed:
        return {}  # the index is still required: an unindexed repo never passes fence 4
    q = [
        "query",
        "co_changes",
        *root,
        "--threshold",
        str(shared),
        "--min-ratio",
        str(ratio),
    ]
    p = _codemem(repo, *q, "--", *changed)
    try:
        out = json.loads(p.stdout)
    except json.JSONDecodeError as exc:
        raise _Stop(
            EXIT_NO_INDEX,
            f"codemem co_changes printed no JSON (rc {p.returncode}): {_last(p)}",
        ) from exc
    results = {changed[0]: out} if len(changed) == 1 else out
    partners: dict[str, list[str]] = {}
    for path, result in results.items():
        if result.get("error"):
            raise _Stop(EXIT_NO_INDEX, f"codemem co_changes {path}: {result['error']}")
        if result.get("stale") is not False:
            raise _Stop(
                EXIT_FAIL,
                f"codemem index stale ({result.get('stale_reason') or 'stale: ' + str(result.get('stale'))}) "
                "— a stale answer never passes; refresh and re-run",
            )
        for entry in result.get("files", []):
            partners.setdefault(entry["path"], []).append(path)
    return partners


def _last(p: subprocess.CompletedProcess[str]) -> str:
    lines = (p.stderr or p.stdout).strip().splitlines()
    return lines[-1] if lines else "(no output)"


# --- public API (griffe, P6) ------------------------------------------------------------


def _declared_breaks(plan_text: str, milestone: str) -> list[str]:
    """Dotted paths the milestone's Contract declares with ``API-Break: <path> — <reason>``."""
    return [
        m.group(1)
        for line in milestone_contract_lines(plan_text, milestone)
        if (m := _API_BREAK_RE.match(line))
    ]


def _api_diff(
    repo: Path, base: str, head: str, changed: list[str], declared: list[str]
) -> tuple[str, list[str]]:
    """(``api_diff`` summary, undeclared breaks) for each API package the change touches.

    Static loads only (the code under review is never imported). Anything griffe cannot
    load is reported as ``skipped(<package>: <reason>)`` — never silent.
    """
    touched = [
        (name, root)
        for name, root in API_PACKAGES.items()
        if any(p.startswith(f"{root}/{name}/") for p in changed)
    ]
    if not touched:
        return f"skipped(no {' or '.join(API_PACKAGES)} file changed)", []
    try:
        import griffe  # lazy: a dev dependency; absent -> skipped(reason), never ImportError
    except ImportError:
        return "skipped(griffe not installed)", []
    done, skipped, breaks = [], [], []
    for name, root in touched:
        try:
            gitutil.git(["cat-file", "-e", f"{base}:{root}/{name}"], repo)
        except gitutil.GitError:
            skipped.append(f"{name}: absent at base")
            continue
        try:
            old = griffe.load_git(
                name, ref=base, repo=repo, search_paths=[root], allow_inspection=False
            )
            if head == "HEAD":
                new = griffe.load(
                    name,
                    search_paths=[repo / root],
                    allow_inspection=False,
                    try_relative_path=False,
                )
            else:
                new = griffe.load_git(
                    name,
                    ref=head,
                    repo=repo,
                    search_paths=[root],
                    allow_inspection=False,
                )
            found = [
                (b.obj.path, b.kind.value)
                for b in griffe.find_breaking_changes(old, new)
            ]
        except Exception as exc:  # noqa: BLE001  # why: griffe raises many types on code it cannot load; reported as skipped(reason)
            first = str(exc).splitlines()[0] if str(exc) else ""
            skipped.append(f"{name}: {type(exc).__name__}: {first}".rstrip(": "))
            log.warning("api diff of %s skipped: %s", name, skipped[-1])
            continue
        done.append(name)
        breaks += [
            f"{path}: {kind}"
            for path, kind in found
            if not any(path == d or path.startswith(d + ".") for d in declared)
        ]
    summary = ",".join(done)
    if skipped:
        summary += ("; " if summary else "") + f"skipped({'; '.join(skipped)})"
    return summary, sorted(dict.fromkeys(breaks))


# --- classification ------------------------------------------------------------------------


def _covers(row: str, path: str) -> bool:
    row = row.rstrip("/")
    return path == row or path.startswith(row + "/")


def _classify(report: ImpactReport, partners: dict[str, list[str]]) -> None:
    changed = set(report.changed)
    report.unpredicted = [
        p for p in report.changed if not any(_covers(r, p) for r in report.predicted)
    ]
    report.predicted_unchanged = [
        r
        for r in dict.fromkeys(report.predicted)
        if not any(_covers(r, p) for p in changed)
    ]
    report.cochange_missing = {
        g: sorted(fs)
        for g, fs in sorted(partners.items())
        if g not in changed and not _excluded(g)
    }
    need = [*report.unpredicted, *report.predicted_unchanged, *report.cochange_missing]
    report.unexplained = sorted(
        p for p in dict.fromkeys(need) if p not in report.explained
    )


def _unreviewed(
    derived: dict[str, list[str]], tasks_md: Path, heading: str
) -> dict[str, list[str]]:
    if not derived:
        return {}
    provenance = tasks_md.with_name(
        tasks_md.name.replace("-tasks.md", "-provenance.log")
    )
    text = provenance.read_text(encoding="utf-8") if provenance.is_file() else ""
    reviews = "\n".join(
        line
        for line in text.splitlines()
        if "CRITICAL_PATH_REVIEW" in line and heading in line
    )
    out = {}
    for value, files in derived.items():
        globs = [g for g in CRITICAL_PATH_GLOBS[value] if g in reviews]
        missing = [
            f
            for f in files
            if f not in reviews and not any(fnmatch.fnmatchcase(f, g) for g in globs)
        ]
        if missing:
            out[value] = missing
    return out


# --- CLI -----------------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    """``aa-ma-impact <plan.md> <tasks.md> --milestone N --base SHA [--format kv|json]``."""
    parser = argparse.ArgumentParser(
        prog="aa-ma-impact",
        description="Gate-computed IMPACT_VERIFIED: every change predicted or explained.",
    )
    parser.add_argument("plan", type=Path)
    parser.add_argument("tasks", type=Path)
    parser.add_argument("--milestone", type=int, required=True)
    parser.add_argument(
        "--base",
        help="the milestone's merge-base SHA; omitted, only the grandfather check runs",
    )
    parser.add_argument(
        "--head", default="HEAD", help="default HEAD: the working tree too"
    )
    parser.add_argument("--format", choices=("kv", "json"), default="kv")
    parser.add_argument(
        "--ignore-cutover",
        action="store_true",
        help="check a grandfathered plan (retro-check)",
    )
    parser.add_argument("-v", "--verbose", action="count", default=0)
    args = parser.parse_args(argv)  # usage errors exit 2 (argparse)
    configure_logging(args.verbose)
    report = compute(
        args.plan,
        args.tasks,
        args.milestone,
        args.base,
        args.head,
        ignore_cutover=args.ignore_cutover,
    )
    if args.format == "json":
        print(json.dumps(asdict(report), indent=2, sort_keys=True))
    else:
        print(report.to_kv())
    if report.exit_code != EXIT_PASS:
        print(f"aa-ma-impact: {report.reason}", file=sys.stderr)
    return report.exit_code


if __name__ == "__main__":
    sys.exit(main())
