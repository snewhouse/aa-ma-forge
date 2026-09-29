"""measure(): run every §5a tool row against a target repo and write the work dir's measure.json.

Tools measure, the model judges, and this module never guesses. A tool that is not installed is
`absent`; one that fails, times out, or leaves no readable report is `unknown` (the report-based
rule of /sole-dev-merge Stage C) and its metrics stay None — never zero. Rows, argv and parse
shapes are the ones the 2.1 prototype confirmed on the forge (plan §5a, amended 2026-09-28).

Scanners never see the target itself: they run in a staging dir (a system temp dir, outside
any git work tree, so no `.gitignore` hides it) of hard links or copies of its tracked regular files, without the scanner config and ignore files the target ships (those are recorded,
not obeyed). So an untracked `.env` or `node_modules/` is never scanned, a tracked symlink is
never followed, and no file name can become a tool option. codemem always builds a fresh index in
the work dir, with cwd = the target; the target's own `.codemem/` is never read or written. Tools
run concurrently, each into its own context, merged in a fixed order so the output is
deterministic."""

from __future__ import annotations

import csv
import io
import json
import os
import re
import shutil
import stat
import tempfile
import time
from collections import Counter
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from .ids import anchor_for, assign_ids
from .models import (
    NETWORK_TOOLS,
    SCHEMA_VERSION,
    Confidence,
    Dimension,
    Finding,
    MeasureDoc,
    Origin,
    Refutation,
    Severity,
    Tier,
    ToolStatus,
)
from .run import spawn
from .secrets import gitleaks_args, secret_lines
from .stamp import (
    REPORTS_ROOT,
    build_stamp,
    check_git_config,
    ensure_self_ignoring,
    find_binary,
    read_regular,
    run_git,
    safe_dir,
    safe_env,
)

TOOL_TIMEOUT_S = 300
VERSION_TIMEOUT_S = 60
WORK_PREFIX = ".work-"
# The parsers below were confirmed against these major versions (2.1 prototype); another major
# is `unknown` rather than parsed into plausible-looking wrong values.
TOOL_MAJOR = {
    "lizard": 1,
    "jscpd": 5,
    "gitleaks": 8,
    "semgrep": 1,
    "osv-scanner": 2,
    "pip-audit": 2,
}
# Everything else answers --version.
VERSION_ARGS = {"gitleaks": ["version"]}
# Scanner config and ignore files a target can ship to quieten a tool: recorded, left out of the
# staging dir, so never obeyed.
TOOL_CONFIGS = {
    ".gitleaks.toml",
    ".gitleaksignore",
    ".semgrepignore",
    "osv-scanner.toml",
    "whitelizard.txt",
    ".jscpd.json",
}
# Also never staged: a tracked .gitignore hides force-added tracked files from the scanners that
# honour it. Silent: it is git's, not a scanner's.
UNSTAGED = TOOL_CONFIGS | {".gitignore"}
# jscpd also obeys a `jscpd` key in the root package.json: staged as a copy without it.
PACKAGE_JSON, JSCPD_KEY = "package.json", "jscpd"
STAGE_DIR, STAGE_PREFIX = "aa-ma", "stage-"
# A stage this old outlived its run (killed before cleanup): removed at the next start.
STALE_STAGE_S = 86400
# Inline markers that silence one finding; counted, since the staging dir cannot remove them.
# Only in a comment (after an introducer on the same line) of a non-prose file.
# ponytail: an introducer inside a string literal still counts; a tokenizer per language if it matters.
COMMENT = r"(?:#|//|/\*|<!--|--)"
SUPPRESSIONS = {
    tool: re.compile(rf"{COMMENT}.*?{marker}")
    for tool, marker in {
        "semgrep": r"nosemgrep",
        "gitleaks": r"gitleaks:allow",
        "lizard": r"lizard\s+forgives",
        "jscpd": r"jscpd:ignore-start",
    }.items()
}
PROSE_SUFFIXES = {".md", ".markdown", ".rst", ".txt", ".adoc"}
CCN_FLAG, CCN_HIGH = 15, 25
CHURN_DAYS = 90
SECONDS_PER_DAY = 86400
# Hot files whose co-changes are recorded.
CO_CHANGE_FILES = 3
# dead_code truncates at its default budget (2.1: 167 of 1500 symbols).
DEAD_CODE_BUDGET = 10**9
# ponytail: larger tracked files are skipped by the regex set (gitleaks still reads them).
SECRET_SCAN_MAX_BYTES = 5_000_000
# jscpd formats that are prose or data, not code (2.1: 201 of the forge's 263 clones).
PROSE_FORMATS = {
    "markdown",
    "text",
    "txt",
    "json",
    "yaml",
    "toml",
    "log",
    "markup",
    "mermaid",
    "dot",
}
# lizard --csv has no header row.
LIZARD_NLOC, LIZARD_CCN, LIZARD_FILE, LIZARD_FUNCTION, LIZARD_START = 0, 1, 6, 7, 9
# osv-scanner 2.x: no lockfile or manifest found (empty stdout).
OSV_NO_PACKAGES = 128
SEMGREP_SEVERITY = {
    "ERROR": Severity.HIGH, "CRITICAL": Severity.HIGH, "HIGH": Severity.HIGH,
    "WARNING": Severity.MEDIUM, "MEDIUM": Severity.MEDIUM,
    "INFO": Severity.LOW, "LOW": Severity.LOW,
}  # fmt: skip
CODEMEM_INPUTS = (
    "codemem.hot_spots",
    "codemem.co_changes",
    "codemem.owners",
    "codemem.layers",
    "codemem.dead_code",
)
LAYERS = ("core", "middle", "periphery")
COMPLEXITY_OVER = f"complexity.over_{CCN_FLAG}"
_VERSION = re.compile(r"\d+(?:\.\d+)+")
_INSERTED = re.compile(r"inserted (\d+) commits")


@dataclass
class _Candidate:
    rule: str
    dimension: Dimension
    severity: Severity
    path: str
    line: int | None
    anchor: str
    title: str
    evidence: str = ""


Parsed = tuple[list[_Candidate], dict[str, int | float | None]]


@dataclass
class _Ctx:
    repo: Path
    work: Path
    stage: Path
    timeout: float
    sizes: dict[
        str, int
    ]  # tracked regular files inside the repo → size at listing time
    tools: dict[str, ToolStatus] = field(default_factory=dict)
    metrics: dict[str, int | float | None] = field(default_factory=dict)
    found: list[_Candidate] = field(default_factory=list)
    log: list[str] = field(default_factory=list)
    # Shared metrics a contributing run missed: unknown, never a partial count.
    partial: set[str] = field(default_factory=set)
    _lines: dict[str, list[str]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.files = list(self.sizes)
        self.fileset = set(self.sizes)

    def child(self) -> _Ctx:
        """A fresh context for one concurrent job; merged back in a fixed order."""
        return _Ctx(self.repo, self.work, self.stage, self.timeout, self.sizes)

    def merge(self, other: _Ctx) -> None:
        for name, status in other.tools.items():
            self._status(name, status)
        self.partial |= other.partial
        self.add(other.found, other.metrics)
        self.log += other.log

    def anchor(self, path: str, line: int, fallback: str) -> str:
        """The source line's text (redacted, whitespace-collapsed), or `fallback` if there is none."""
        if path not in self.fileset:
            return fallback
        if path not in self._lines:
            try:  # it was a regular file when listed; it must still be one
                self._lines[path] = read_regular(self.repo / path).splitlines()
            except (OSError, UnicodeDecodeError):
                self._lines[path] = []
        lines = self._lines[path]
        text = anchor_for(lines[line - 1]) if 1 <= line <= len(lines) else ""
        return text or fallback

    def _status(self, name: str, status: ToolStatus) -> None:
        # A tool run several times keeps its worst.
        if self.tools.get(name) != ToolStatus.UNKNOWN:
            self.tools[name] = status

    def record(
        self,
        name: str,
        argv: list[str],
        rc: int | None,
        secs: float,
        status: ToolStatus,
    ) -> None:
        self._status(name, status)
        self.trail(name, argv, rc, secs, status)

    def trail(
        self, name: str, argv: list[str], rc: int | None, secs: float, status: str
    ) -> None:
        """One run.log line: name, argv, rc, seconds, status — never any tool output."""
        fields = [
            name,
            " ".join(argv),
            "-" if rc is None else str(rc),
            f"{secs:.2f}",
            status,
        ]
        # A git path may hold a tab or newline; neither may break the one-line-per-call format.
        self.log.append(
            "\t".join(f.replace("\t", " ").replace("\n", " ") for f in fields)
        )

    def add(
        self, found: list[_Candidate], metrics: dict[str, int | float | None]
    ) -> None:
        self.found += [c for c in found if c.path in self.fileset]
        # The same count from several runs (osv-scanner + pip-audit) adds up.
        for key, value in metrics.items():
            old = self.metrics.get(key)
            self.metrics[key] = value if old is None or value is None else old + value
        for key in self.partial & metrics.keys():
            self.metrics[key] = None

    def miss(self, metric_keys: tuple[str, ...]) -> None:
        """A contributing run did not run: its shared metrics are unknown, never a partial count."""
        self.partial.update(metric_keys)
        self.metrics.update(dict.fromkeys(metric_keys))


def _exec(
    ctx: _Ctx, argv: list[str], *, cwd: Path | None = None, timeout: float | None = None
) -> tuple[int | None, bytes, float]:
    t0 = time.monotonic()
    try:
        rc, out = spawn(
            argv,
            cwd or ctx.stage,
            safe_env(),
            timeout or ctx.timeout,
            merge_stderr=False,
        )
    except OSError:
        rc, out = None, b""
    return rc, out, time.monotonic() - t0


def _version_ok(ctx: _Ctx, name: str, binary: str) -> bool:
    """Probe the tool's version; recorded in run.log; only the confirmed major is parsed."""
    argv = [binary, *VERSION_ARGS.get(name, ["--version"])]
    rc, out, secs = _exec(ctx, argv, timeout=VERSION_TIMEOUT_S)
    found = _VERSION.search(out.decode("utf-8", "replace")) if rc == 0 else None
    version = found.group(0) if found else None
    ctx.trail(f"{name}.version", argv, rc, secs, version or ToolStatus.UNKNOWN)
    return version is not None and int(version.split(".")[0]) == TOOL_MAJOR[name]


def _tool(
    ctx: _Ctx,
    name: str,
    args: list[str],
    parse: Callable[[bytes], Parsed],
    metric_keys: tuple[str, ...],
    *,
    report: Path | None = None,
    ok: tuple[int, ...] = (0, 1),
    empty_ok: tuple[int, ...] = (),
) -> bool:
    """Run one optional tool in the staging dir; its findings and metrics count only if its
    report parses."""
    ctx.metrics.update({k: ctx.metrics.get(k) for k in metric_keys})
    binary = find_binary(name)
    if binary is None:
        ctx.record(name, [name, *args], None, 0.0, ToolStatus.ABSENT)
        ctx.miss(metric_keys)
        return False
    if not _version_ok(ctx, name, binary):
        ctx.record(name, [binary, *args], None, 0.0, ToolStatus.UNKNOWN)
        ctx.miss(metric_keys)
        return False
    argv = [binary, *args]
    rc, out, secs = _exec(ctx, argv)
    body = out if report is None else (report.read_bytes() if report.is_file() else b"")
    status = ToolStatus.UNKNOWN
    if rc in ok and (body.strip() or rc in empty_ok):
        try:
            ctx.add(*parse(body))
            status = ToolStatus.RAN
        except (ValueError, KeyError, TypeError, IndexError, AttributeError):
            pass
    ctx.record(name, argv, rc, secs, status)
    if status != ToolStatus.RAN:
        ctx.miss(metric_keys)
    return status == ToolStatus.RAN


# --- parsers (2.1 shapes; paths are relative to the staging dir, i.e. repo-relative) -------------


def _rel(path: str) -> str:
    return os.path.normpath(path)


def _lizard(ctx: _Ctx) -> Callable[[bytes], Parsed]:
    def parse(body: bytes) -> Parsed:
        found, ccns = [], []
        for row in csv.reader(io.StringIO(body.decode("utf-8"))):
            nloc, ccn = int(row[LIZARD_NLOC]), int(row[LIZARD_CCN])
            path, function, start = (
                _rel(row[LIZARD_FILE]),
                row[LIZARD_FUNCTION],
                int(row[LIZARD_START]),
            )
            ccns.append(ccn)
            if ccn > CCN_FLAG:
                severity = Severity.HIGH if ccn > CCN_HIGH else Severity.MEDIUM
                found.append(_Candidate(
                    "maint.complexity", Dimension.MAINTAINABILITY, severity, path, start,
                    ctx.anchor(path, start, function), f"{function}: cyclomatic complexity {ccn}",
                    f"CCN {ccn}, NLOC {nloc}",
                ))  # fmt: skip
        over = sum(c > CCN_FLAG for c in ccns)
        return found, {
            "complexity.functions": len(ccns),
            "complexity.ccn_max": max(ccns, default=None),
            COMPLEXITY_OVER: over,
        }

    return parse


def _jscpd(ctx: _Ctx) -> Callable[[bytes], Parsed]:
    def parse(body: bytes) -> Parsed:
        doc, found = json.loads(body), []
        for dup in doc["duplicates"]:
            path, line = (
                _rel(dup["firstFile"]["name"].rsplit(":", 1)[0]),
                dup["firstFile"]["startLoc"]["line"],
            )
            # A code block inside markdown is named by basename only, so it is no tracked path.
            if dup["format"] in PROSE_FORMATS or path not in ctx.fileset:
                continue
            other = _rel(dup["secondFile"]["name"].rsplit(":", 1)[0])
            other_line = dup["secondFile"]["startLoc"]["line"]
            found.append(_Candidate(
                "maint.duplication", Dimension.MAINTAINABILITY, Severity.LOW, path, line,
                ctx.anchor(path, line, f"clone of {other}"),
                f"{dup['lines']} duplicated lines, also at {other}:{other_line}",
            ))  # fmt: skip
        code = [
            v for k, v in doc["statistics"]["formats"].items() if k not in PROSE_FORMATS
        ]
        lines = sum(v["lines"] for v in code)
        pct = 100.0 * sum(v["duplicatedLines"] for v in code) / lines if lines else None
        return found, {"duplication.pct": pct, "duplication.clones": len(found)}

    return parse


def _secret(path: str, line: int, rule: str) -> _Candidate:
    return _Candidate(
        "security.secret",
        Dimension.SECURITY,
        Severity.HIGH,
        path,
        line,
        rule,
        f"possible secret ({rule})",
    )


def _gitleaks(body: bytes) -> Parsed:
    return [
        _secret(_rel(leak["File"]), int(leak["StartLine"]), leak["RuleID"])
        for leak in json.loads(body)
    ], {}


def _semgrep(body: bytes) -> Parsed:
    # The title is the rule id: semgrep messages can quote source.
    found = [
        _Candidate(
            "security.sast",
            Dimension.SECURITY,
            SEMGREP_SEVERITY.get(str(r["extra"]["severity"]).upper(), Severity.MEDIUM),
            _rel(r["path"]),
            int(r["start"]["line"]),
            r["check_id"],
            r["check_id"],
        )  # fmt: skip
        for r in json.loads(body)["results"]
    ]
    return found, {"sast.findings": len(found)}


def _vuln(
    path: str, name: str, version: str, vuln_id: str, fixable: bool
) -> _Candidate:
    severity = Severity.HIGH if fixable else Severity.MEDIUM
    return _Candidate(
        "deps.vuln", Dimension.TESTS_DEPS, severity, path, None, f"{name}@{version}:{vuln_id}",
        f"{name} {version}: {vuln_id}{'' if fixable else ' (no fix released)'}",
    )  # fmt: skip


def _under(path: str, roots: tuple[Path, ...]) -> str:
    """osv-scanner reports absolute paths: make them relative to whichever root holds them."""
    resolved = Path(path).resolve()
    for root in roots:
        if resolved.is_relative_to(root.resolve()):
            return resolved.relative_to(root.resolve()).as_posix()
    raise ValueError("path outside the scanned tree")


def _osv(ctx: _Ctx) -> Callable[[bytes], Parsed]:
    def parse(body: bytes) -> Parsed:
        found = []
        for result in (json.loads(body) if body.strip() else {}).get("results") or []:
            source = _under(result["source"]["path"], (ctx.stage, ctx.repo))
            for pkg in result["packages"]:
                p = pkg["package"]
                for v in pkg.get("vulnerabilities") or []:
                    events = (
                        e
                        for a in v.get("affected", [])
                        for g in a.get("ranges", [])
                        for e in g.get("events", [])
                    )
                    found.append(
                        _vuln(
                            source,
                            p["name"],
                            p["version"],
                            v["id"],
                            any("fixed" in e for e in events),
                        )
                    )
        return found, {"deps.vulns": len(found)}

    return parse


def _pip_audit(requirements: str) -> Callable[[bytes], Parsed]:
    def parse(body: bytes) -> Parsed:
        found = [
            _vuln(
                requirements,
                dep["name"],
                dep["version"],
                v["id"],
                bool(v.get("fix_versions")),
            )
            for dep in json.loads(body)["dependencies"]
            for v in dep.get("vulns", [])
        ]
        return found, {"deps.vulns": len(found)}

    return parse


# --- the tree -------------------------------------------------------------------------------------


def _top(path: str) -> str:
    return path.split("/", 1)[0] if "/" in path else "."


def _tracked_regular_files(repo: Path) -> tuple[dict[str, int], int]:
    """{path: size} of tracked regular files still inside the repo, and how many escaped it.

    lstat and O_NOFOLLOW only guard the last component: a tracked `p/x` whose `p` was swapped
    for a symlink resolves outside the repo, so every path is checked against its real one."""
    listed = run_git(repo, "ls-files", "-z", "--end-of-options")
    root, files, escaping = os.path.realpath(repo), {}, 0
    for rel in filter(None, listed.stdout.split("\0")):
        try:
            st = os.lstat(repo / rel)
        except FileNotFoundError:  # deleted in the working tree
            continue
        if os.path.realpath(repo / rel) != os.path.join(root, rel):
            escaping += 1
        elif stat.S_ISREG(st.st_mode):
            files[rel] = st.st_size
    return files, escaping


def _stage_root(repo: Path) -> Path | None:
    """`$XDG_CACHE_HOME/aa-ma` (or ~/.cache/aa-ma) when it is ours, on the repo's filesystem (so
    staging hard-links rather than copies) and outside any git work tree (whose .gitignore the
    scanners would obey); else None. Stale stages from killed runs are removed from it."""
    base = os.environ.get("XDG_CACHE_HOME") or os.path.expanduser("~/.cache")
    root = Path(base) / STAGE_DIR
    try:
        root.mkdir(mode=0o700, parents=True, exist_ok=True)
        st = os.lstat(root)
        if (
            not stat.S_ISDIR(st.st_mode)
            or st.st_uid != os.getuid()
            or st.st_dev != os.stat(repo).st_dev
            or run_git(root, "rev-parse", "--is-inside-work-tree").returncode == 0
        ):
            return None
        cutoff = time.time() - STALE_STAGE_S
        for old in root.glob(f"{STAGE_PREFIX}*"):
            if os.lstat(old).st_mtime < cutoff:
                shutil.rmtree(old, ignore_errors=True)
    except OSError:
        return None
    return root


def _make_stage(repo: Path) -> Path:
    root = _stage_root(repo)
    if root is None:
        return Path(tempfile.mkdtemp(prefix=f"{STAGE_DIR}-{STAGE_PREFIX}"))
    return Path(tempfile.mkdtemp(prefix=STAGE_PREFIX, dir=root))


def _without_jscpd_key(src: Path) -> str | None:
    """package.json as JSON without its `jscpd` key, or None when it has none."""
    try:
        doc = json.loads(read_regular(src))
    except (OSError, ValueError):
        return None
    if not isinstance(doc, dict) or JSCPD_KEY not in doc:
        return None
    del doc[JSCPD_KEY]
    return json.dumps(doc, indent=2) + "\n"


def _stage(ctx: _Ctx) -> None:
    """Hard-link every tracked regular file (copy across filesystems) into the staging dir, minus
    the scanner configs the target ships, which are recorded as present and not obeyed. A file
    that changed or vanished since it was listed is skipped and counted."""
    t0, overrides, done = time.monotonic(), 0, Counter()
    for rel in ctx.files:
        name, src, dst = Path(rel).name, ctx.repo / rel, ctx.stage / rel
        if name in UNSTAGED:
            if name in TOOL_CONFIGS:
                overrides += 1
                ctx.trail(f"tool-config:{rel}", [], None, 0.0, "present, not obeyed")
            continue
        try:
            dst.parent.mkdir(parents=True, exist_ok=True)
            stripped = _without_jscpd_key(src) if rel == PACKAGE_JSON else None
            if stripped is not None:
                dst.write_text(stripped, encoding="utf-8")
                overrides += 1
                ctx.trail(
                    f"tool-config:{rel}#{JSCPD_KEY}",
                    [],
                    None,
                    0.0,
                    "present, not obeyed",
                )
                done["copied"] += 1
                continue
            try:
                os.link(src, dst, follow_symlinks=False)
                done["linked"] += 1
            except OSError:
                shutil.copyfile(src, dst, follow_symlinks=False)
                done["copied"] += 1
            if not stat.S_ISREG(
                os.lstat(dst).st_mode
            ):  # swapped for a symlink since listed
                raise OSError(rel)
        except OSError:  # shutil.SpecialFileError is one
            if os.path.lexists(dst):
                dst.unlink()
            done["skipped"] += 1
    counts = " ".join(f"{k}={done[k]}" for k in ("linked", "copied", "skipped"))
    ctx.trail("stage", [], None, time.monotonic() - t0, counts)
    ctx.metrics["tool_config.overrides"] = overrides
    ctx.metrics["files.unstaged"] = done["skipped"]


def _git_metrics(ctx: _Ctx) -> None:
    files, size = Counter(), Counter()
    for rel in ctx.files:
        files[_top(rel)] += 1
        size[_top(rel)] += ctx.sizes[rel]
    log = run_git(
        ctx.repo,
        "log",
        f"--since={CHURN_DAYS} days ago",
        "--numstat",
        "--no-renames",
        "--format=",
        "--end-of-options",
        "HEAD",
    )
    churn: Counter[str] | None = None
    if log.returncode == 0:
        churn = Counter()
        for line in log.stdout.splitlines():
            added, deleted, path = (line.split("\t") + ["", "", ""])[:3]
            if added.isdigit() and deleted.isdigit():
                churn[_top(path)] += int(added) + int(deleted)
    # Days before HEAD's commit, not before now: the same commit always gives the same value.
    head = run_git(
        ctx.repo, "log", "-1", "--format=%ct", "--end-of-options", "HEAD"
    ).stdout.strip()
    for top in files:
        ctx.metrics[f"size.files:{top}"] = files[top]
        ctx.metrics[f"size.bytes:{top}"] = size[top]
        ctx.metrics[f"churn.{CHURN_DAYS}d:{top}"] = (
            None if churn is None else churn[top]
        )
        if top != "." and head.isdigit():
            last = run_git(
                ctx.repo,
                "log",
                "-1",
                "--format=%ct",
                "--end-of-options",
                "HEAD",
                "--",
                top,
            ).stdout.strip()
            ctx.metrics[f"last_touch_days:{top}"] = (
                (int(head) - int(last)) // SECONDS_PER_DAY if last.isdigit() else None
            )


# --- jobs (each runs concurrently in its own context) --------------------------------------------


def _job_lizard(ctx: _Ctx) -> None:
    _tool(
        ctx,
        "lizard",
        ["--csv", "."],
        _lizard(ctx),
        ("complexity.functions", "complexity.ccn_max", COMPLEXITY_OVER),
    )


def _job_jscpd(ctx: _Ctx) -> None:
    out = ctx.work / "jscpd"
    try:
        args = ["--reporters", "json", "--output", str(out), "--silent", "."]
        _tool(
            ctx,
            "jscpd",
            args,
            _jscpd(ctx),
            ("duplication.pct", "duplication.clones"),
            report=out / "jscpd-report.json",
        )
    finally:
        shutil.rmtree(out, ignore_errors=True)


def _job_gitleaks(ctx: _Ctx) -> None:
    report = ctx.work / "gitleaks.json"
    try:
        _tool(
            ctx,
            "gitleaks",
            gitleaks_args(".", report),
            _gitleaks,
            (),
            report=report,
            ok=(0,),
        )
    finally:
        report.unlink(missing_ok=True)


def _job_semgrep(ctx: _Ctx) -> None:
    args = ["scan", "--config", "p/default", "--metrics=off", "--json", "--quiet", "."]
    _tool(ctx, "semgrep", args, _semgrep, ("sast.findings",))


def _job_deps(ctx: _Ctx) -> None:
    """osv-scanner and pip-audit share deps.vulns, so they run in one job, in order."""
    osv = ["scan", "source", "-r", "--format", "json", "."]
    _tool(
        ctx,
        "osv-scanner",
        osv,
        _osv(ctx),
        ("deps.vulns",),
        empty_ok=(OSV_NO_PACKAGES,),
        ok=(0, 1, OSV_NO_PACKAGES),
    )
    requirements = [
        f
        for f in ctx.files
        if Path(f).name.startswith("requirements") and f.endswith(".txt")
    ]
    if not requirements:
        ctx.record("pip-audit", ["pip-audit"], None, 0.0, ToolStatus.SKIPPED)
    for req in requirements:
        _tool(
            ctx,
            "pip-audit",
            ["-f", "json", "--no-deps", "--disable-pip", "-r", req],
            _pip_audit(req),
            ("deps.vulns",),
        )


def _is_test(path: str, name: str) -> bool:
    parts = path.split("/")
    return (
        bool({"tests", "test"} & set(parts[:-1]))
        or parts[-1].startswith("test_")
        or name.startswith("test_")
    )


class _Codemem:
    """Every call: `codemem --db <work>/codemem.db …` with cwd = the target (AC12). codemem ships
    with the forge, so a missing or failing one leaves its inputs `unknown`, never `absent`."""

    def __init__(self, ctx: _Ctx, binary: str) -> None:
        self.ctx, self.binary, self.db = ctx, binary, str(ctx.work / "codemem.db")

    def call(self, label: str, *args: str) -> bytes | None:
        argv = [self.binary, "--db", self.db, *args]
        rc, out, secs = _exec(self.ctx, argv, cwd=self.ctx.repo)
        self.ctx.trail(
            label, argv, rc, secs, ToolStatus.RAN if rc == 0 else ToolStatus.UNKNOWN
        )
        return out if rc == 0 else None

    def query(self, tool: str, *args: str) -> dict[str, Any] | None:
        out = self.call(f"codemem.{tool}", "query", tool, *args)
        try:
            doc = json.loads(out) if out else None
        except ValueError:
            return None
        return doc if isinstance(doc, dict) and not doc.get("error") else None

    def ran(
        self,
        tool: str,
        fill: Callable[[dict[str, Any]], dict[str, int | float | None]],
        *args: str,
    ) -> bool:
        """Query; `fill` turns the answer into metrics. Any malformed answer leaves it unknown."""
        doc = self.query(tool, *args)
        try:
            metrics = fill(doc) if doc is not None else None
        except (KeyError, TypeError, ValueError, IndexError):
            metrics = None
        if metrics is None:
            return False
        self.ctx.metrics.update(metrics)
        self.ctx.tools[f"codemem.{tool}"] = ToolStatus.RAN
        return True


def _dead_code(d: dict[str, Any]) -> dict[str, int | float | None]:
    if d["truncated"]:
        raise ValueError("truncated")
    return {
        "dead_code.candidates": sum(
            not _is_test(s["file"], s["name"]) for s in d["symbols"]
        )
    }


def _layers(d: dict[str, Any]) -> dict[str, int | float | None]:
    return {f"layers.{k}": len(d["layers"][k]) for k in LAYERS}


def _co_changes(
    target: str, doc: dict[str, Any] | None
) -> dict[str, int | float | None]:
    return {f"co_change:{target}|{f['path']}": f["count"] for f in doc["files"]}  # type: ignore[index]


def _job_codemem(ctx: _Ctx) -> None:
    ctx.tools.update(dict.fromkeys(CODEMEM_INPUTS, ToolStatus.UNKNOWN))
    ctx.metrics.update(
        dict.fromkeys([*(f"layers.{k}" for k in LAYERS), "dead_code.candidates"])
    )
    binary = find_binary("codemem")
    if not binary:
        ctx.trail("codemem.build", ["codemem"], None, 0.0, ToolStatus.UNKNOWN)
        return
    cm = _Codemem(ctx, binary)
    if cm.call("codemem.build", "build", "--repo-root", str(ctx.repo)) is None:
        return
    commits = cm.call(
        "codemem.refresh-commits", "refresh-commits", "--repo-root", str(ctx.repo)
    )
    cm.ran("dead_code", _dead_code, "--budget", str(DEAD_CODE_BUDGET))
    cm.ran("layers", _layers)
    inserted = _INSERTED.search(commits.decode("utf-8", "replace")) if commits else None
    if not inserted or int(inserted.group(1)) == 0:
        return  # no commit rows: the git-history inputs stay unknown, never zero

    hot: list[str] = []

    def hot_spots(d: dict[str, Any]) -> dict[str, int | float | None]:
        hot.extend(f["path"] for f in d["files"][:CO_CHANGE_FILES])
        return {f"hot_spot:{f['path']}": f["score"] for f in d["files"]}

    if cm.ran("hot_spots", hot_spots):
        pairs: dict[str, int | float | None] = {}
        for target in hot:
            doc = cm.query("co_changes", target)
            try:
                pairs.update(_co_changes(target, doc))
            except (KeyError, TypeError):
                break
        else:  # every hot file answered (also when there is none)
            ctx.metrics.update(pairs)
            ctx.tools["codemem.co_changes"] = ToolStatus.RAN

    owned: dict[str, int | float | None] = {}
    for top in sorted({_top(f) for f in ctx.files} - {"."}):
        # A directory needs its trailing /; counts and shares only — never an email.
        doc = cm.query("owners", f"{top}/", "--repo-root", str(ctx.repo))
        try:
            authors = doc["authors"]  # type: ignore[index]
            if authors:
                owned[f"owners.authors:{top}/"] = len(authors)
                owned[f"owners.top_pct:{top}/"] = round(
                    float(authors[0]["percentage"]), 1
                )
        except (KeyError, TypeError, ValueError, IndexError):
            return
    if owned:
        ctx.metrics.update(owned)
        ctx.tools["codemem.owners"] = ToolStatus.RAN


def _skip_network(ctx: _Ctx) -> None:
    for name in NETWORK_TOOLS:
        ctx.record(name, [name], None, 0.0, ToolStatus.SKIPPED)
    ctx.metrics.update({"sast.findings": None, "deps.vulns": None})


def _regex_pass(ctx: _Ctx) -> None:
    """The built-in secret patterns over every tracked file (after gitleaks, which wins a line),
    counting inline suppression markers on the way."""
    seen = {(c.path, c.line) for c in ctx.found if c.rule == "security.secret"}
    found, markers = [], Counter()
    for rel in ctx.files:
        if ctx.sizes[rel] > SECRET_SCAN_MAX_BYTES:
            continue
        try:
            text = read_regular(ctx.repo / rel)
        except (OSError, UnicodeDecodeError):
            continue
        if Path(rel).suffix.lower() not in PROSE_SUFFIXES:
            markers.update(
                {tool: len(rx.findall(text)) for tool, rx in SUPPRESSIONS.items()}
            )
        for rule, line in secret_lines(text):
            if (rel, line) not in seen:  # the first rule in PATTERNS order wins a line
                seen.add((rel, line))
                found.append(_secret(rel, line, rule))
    ctx.add(found, {})
    ctx.metrics["secrets.findings"] = sum(
        c.rule == "security.secret" for c in ctx.found
    )
    ctx.metrics.update({f"suppressions.{tool}": markers[tool] for tool in SUPPRESSIONS})


# --- entry ---------------------------------------------------------------------------------------


def _findings(ctx: _Ctx) -> list[Finding]:
    """Findings with ids; one whose path the model refuses (a hostile file name) is dropped and
    counted, never allowed to crash the run."""
    found = sorted(ctx.found, key=lambda c: (c.rule, c.path, c.line or 0, c.anchor))
    ids = assign_ids((c.dimension, c.rule, c.path, c.anchor) for c in found)
    out = []
    for c, fid in zip(found, ids, strict=True):
        try:
            out.append(_finding(c, fid))
        except ValidationError:
            continue
    ctx.metrics["findings.unreportable"] = len(found) - len(out)
    return out


def _finding(c: _Candidate, fid: str) -> Finding:
    return Finding(
        schema_version=SCHEMA_VERSION, id=fid, origin=Origin.MEASURED, redacted=False,
        dimension=c.dimension, severity=c.severity, confidence=Confidence.HIGH, rule=c.rule,
        title=c.title, path=c.path, line=c.line, anchor=c.anchor,
        refutation=Refutation.NOT_REQUIRED, evidence=c.evidence,
    )  # fmt: skip


def measure(repo: Path, tier: Tier, *, tool_timeout: float = TOOL_TIMEOUT_S) -> Path:
    """Measure `repo` at `tier`; returns the work dir holding measure.json and run.log."""
    repo = Path(repo).absolute()
    check_git_config(repo)
    stamp = build_stamp(repo, tier)
    root = safe_dir(repo, str(REPORTS_ROOT))
    ensure_self_ignoring(root)
    work_rel = str(REPORTS_ROOT / f"{WORK_PREFIX}{stamp.sha12}")
    if os.path.lexists(repo / work_rel):
        shutil.rmtree(safe_dir(repo, work_rel))
    work = safe_dir(repo, work_rel)

    stage = _make_stage(repo)
    try:
        sizes, escaping = _tracked_regular_files(repo)
        ctx = _Ctx(repo, work, stage, tool_timeout, sizes)
        ctx.metrics["files.escaping"] = escaping
        _stage(ctx)
        _git_metrics(ctx)
        jobs = [_job_lizard, _job_jscpd, _job_gitleaks, _job_codemem]
        jobs += [_job_semgrep, _job_deps] if tier == "deep" else [_skip_network]
        children = [ctx.child() for _ in jobs]
        with ThreadPoolExecutor(max_workers=len(jobs)) as pool:
            for future in [
                pool.submit(job, child)
                for job, child in zip(jobs, children, strict=True)
            ]:
                future.result()
        for child in children:  # fixed order: run.log and metric sums are deterministic
            ctx.merge(child)
        _regex_pass(ctx)
    finally:
        shutil.rmtree(stage, ignore_errors=True)

    doc = MeasureDoc(
        schema_version=SCHEMA_VERSION,
        stamp=stamp.model_copy(update={"tools": ctx.tools}),
        metrics=ctx.metrics,
        measured=_findings(ctx),
    )
    (work / "measure.json").write_text(
        doc.model_dump_json(indent=2) + "\n", encoding="utf-8"
    )
    (work / "run.log").write_text("\n".join(ctx.log) + "\n", encoding="utf-8")
    return work
