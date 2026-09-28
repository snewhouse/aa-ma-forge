"""measure(): run every §5a tool row against a target repo and write the work dir's measure.json.

Tools measure, the model judges, and this module never guesses. A tool that is not installed is
`absent`; one that fails, times out, or leaves no readable report is `unknown` (the report-based
rule of /sole-dev-merge Stage C) and its metrics stay None — never zero. Rows, argv and parse
shapes are the ones the 2.1 prototype confirmed on the forge (plan §5a, amended 2026-09-28).

Only tracked regular files are read or handed to a tool, and a finding on any other path is
dropped: a tracked symlink may point at a key outside the repo, and an untracked `.env` is not the
repo's code. codemem always builds a fresh index in the work dir; the target's own `.codemem/` is
never read or written."""

from __future__ import annotations

import csv
import io
import json
import os
import re
import shutil
import stat
import time
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from .ids import anchor_for, assign_ids
from .models import (
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
from .run import absolute_path, spawn
from .secrets import secret_lines
from .stamp import REPORTS_ROOT, build_stamp, ensure_self_ignoring, run_git, safe_dir

TOOL_TIMEOUT_S = 300
VERSION_TIMEOUT_S = 60
WORK_PREFIX = ".work-"
NETWORK_TOOLS = ("semgrep", "osv-scanner", "pip-audit")  # Deep only (plan V4)
# A dimension whose core input did not run cannot rate Strong (finalize; mirrored in RATING.md).
CORE_INPUTS = {
    Dimension.ARCHITECTURE: ("codemem.layers",),
    Dimension.MAINTAINABILITY: ("lizard",),
    Dimension.SECURITY: ("semgrep",),
    Dimension.TESTS_DEPS: ("osv-scanner", "pip-audit"),
}
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
VERSION_ARGS = {"gitleaks": ["version"]}  # everything else answers --version
# Config and ignore files a target can ship to quieten a scanner: recorded, never obeyed silently.
TOOL_CONFIGS = {
    ".gitleaks.toml",
    ".gitleaksignore",
    ".semgrepignore",
    "osv-scanner.toml",
    "whitelizard.txt",
    ".jscpd.json",
}
CCN_FLAG, CCN_HIGH = 15, 25
CHURN_DAYS = 90
CO_CHANGE_FILES = 3  # hot files whose co-changes are recorded
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
LIZARD_NLOC, LIZARD_CCN, LIZARD_FILE, LIZARD_FUNCTION, LIZARD_START = (
    0,
    1,
    6,
    7,
    9,
)  # headerless CSV
OSV_NO_PACKAGES = 128  # osv-scanner 2.x: no lockfile or manifest found (empty stdout)
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
    timeout: float
    files: list[str]
    tools: dict[str, ToolStatus] = field(default_factory=dict)
    metrics: dict[str, int | float | None] = field(default_factory=dict)
    found: list[_Candidate] = field(default_factory=list)
    log: list[str] = field(default_factory=list)
    partial: set[str] = field(
        default_factory=set
    )  # shared metrics a contributing run missed
    versions: dict[str, str | None] = field(default_factory=dict)
    _lines: dict[str, list[str]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.fileset = set(self.files)

    def anchor(self, path: str, line: int, fallback: str) -> str:
        """The source line's text (redacted, whitespace-collapsed), or `fallback` if there is none."""
        if path not in self.fileset:
            return fallback
        if path not in self._lines:
            self._lines[path] = (
                (self.repo / path)
                .read_text(encoding="utf-8", errors="replace")
                .splitlines()
            )
        lines = self._lines[path]
        text = anchor_for(lines[line - 1]) if 1 <= line <= len(lines) else ""
        return text or fallback

    def record(
        self,
        name: str,
        argv: list[str],
        rc: int | None,
        secs: float,
        status: ToolStatus,
    ) -> None:
        if (
            self.tools.get(name) != ToolStatus.UNKNOWN
        ):  # a tool run several times keeps its worst
            self.tools[name] = status
        self.trail(name, argv, rc, secs, status)

    def trail(
        self, name: str, argv: list[str], rc: int | None, secs: float, status: str
    ) -> None:
        """One run.log line: name, argv, rc, seconds, status — never any tool output."""
        shown = [a for a in argv if a not in self.fileset]
        if len(shown) < len(argv):
            shown.append(f"<{len(argv) - len(shown)} tracked files>")
        fields = [
            name,
            " ".join(shown),
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
        for key, value in metrics.items():  # the same metric from several runs adds up
            old = self.metrics.get(key)
            self.metrics[key] = value if old is None or value is None else old + value
        for key in self.partial & metrics.keys():
            self.metrics[key] = None

    def miss(self, metric_keys: tuple[str, ...]) -> None:
        """A contributing run did not run: its shared metrics are unknown, never a partial count."""
        self.partial.update(metric_keys)
        self.metrics.update(dict.fromkeys(metric_keys))


def _binary(name: str) -> str | None:
    override = os.environ.get(f"{name.upper().replace('-', '_')}_BIN")
    if override is not None:
        return (
            override
            if os.path.isfile(override) and os.access(override, os.X_OK)
            else None
        )
    return shutil.which(name, path=absolute_path(os.environ.get("PATH", "")))


def _env() -> dict[str, str]:
    return dict(os.environ) | {"PATH": absolute_path(os.environ.get("PATH", ""))}


def _exec(
    ctx: _Ctx, argv: list[str], timeout: float | None = None
) -> tuple[int | None, bytes, float]:
    t0 = time.monotonic()
    try:
        rc, out = spawn(
            argv, ctx.repo, _env(), timeout or ctx.timeout, merge_stderr=False
        )
    except OSError:
        rc, out = None, b""
    return rc, out, time.monotonic() - t0


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
    """Run one optional tool; its findings and metrics count only if its report parses."""
    ctx.metrics.update({k: ctx.metrics.get(k) for k in metric_keys})
    binary = _binary(name)
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


def _version_ok(ctx: _Ctx, name: str, binary: str) -> bool:
    """Probe the tool's version once; recorded in run.log; only the confirmed major is parsed."""
    if name not in ctx.versions:
        argv = [binary, *VERSION_ARGS.get(name, ["--version"])]
        rc, out, secs = _exec(ctx, argv, VERSION_TIMEOUT_S)
        found = _VERSION.search(out.decode("utf-8", "replace")) if rc == 0 else None
        ctx.versions[name] = found.group(0) if found else None
        ctx.trail(
            f"{name}.version", argv, rc, secs, ctx.versions[name] or ToolStatus.UNKNOWN
        )
    version = ctx.versions[name]
    return version is not None and int(version.split(".")[0]) == TOOL_MAJOR[name]


# --- parsers (2.1 shapes) --------------------------------------------------------------------------


def _lizard(ctx: _Ctx) -> Callable[[bytes], Parsed]:
    def parse(body: bytes) -> Parsed:
        found, ccns = [], []
        for row in csv.reader(io.StringIO(body.decode("utf-8"))):
            nloc, ccn = int(row[LIZARD_NLOC]), int(row[LIZARD_CCN])
            path, function, start = (
                row[LIZARD_FILE],
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
        return found, {
            "complexity.functions": len(ccns),
            "complexity.ccn_max": max(ccns, default=None),
            COMPLEXITY_OVER: sum(c > CCN_FLAG for c in ccns),
        }

    return parse


def _jscpd(ctx: _Ctx) -> Callable[[bytes], Parsed]:
    def parse(body: bytes) -> Parsed:
        doc, found = json.loads(body), []
        for dup in doc["duplicates"]:
            path, line = (
                dup["firstFile"]["name"].rsplit(":", 1)[0],
                dup["firstFile"]["startLoc"]["line"],
            )
            # A code block inside markdown is named by basename only, so it is no tracked path.
            if dup["format"] in PROSE_FORMATS or path not in ctx.fileset:
                continue
            other, other_line = (
                dup["secondFile"]["name"].rsplit(":", 1)[0],
                dup["secondFile"]["startLoc"]["line"],
            )
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
        _secret(os.path.normpath(leak["File"]), int(leak["StartLine"]), leak["RuleID"])
        for leak in json.loads(body)
    ], {}


def _semgrep(body: bytes) -> Parsed:
    found = [
        _Candidate(
            "security.sast",
            Dimension.SECURITY,
            SEMGREP_SEVERITY.get(str(r["extra"]["severity"]).upper(), Severity.MEDIUM),
            os.path.normpath(r["path"]),
            int(r["start"]["line"]),
            r["check_id"],
            r["check_id"],
        )  # fmt: skip — the title is the rule id: semgrep messages can quote source
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


def _osv(ctx: _Ctx) -> Callable[[bytes], Parsed]:
    def parse(body: bytes) -> Parsed:
        found = []
        for result in (json.loads(body) if body.strip() else {}).get("results") or []:
            source = (
                Path(result["source"]["path"])
                .resolve()
                .relative_to(ctx.repo.resolve())
                .as_posix()
            )
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


# --- rows ----------------------------------------------------------------------------------------


def _top(path: str) -> str:
    return path.split("/", 1)[0] if "/" in path else "."


def _tracked_regular_files(repo: Path) -> list[str]:
    listed = run_git(repo, "ls-files", "-z", "--end-of-options")
    out = []
    for rel in listed.stdout.split("\0"):
        try:
            if rel and stat.S_ISREG(os.lstat(repo / rel).st_mode):
                out.append(rel)
        except FileNotFoundError:  # deleted in the working tree
            continue
    return out


def _git_metrics(ctx: _Ctx) -> None:
    files, size = Counter(), Counter()
    for rel in ctx.files:
        files[_top(rel)] += 1
        size[_top(rel)] += os.lstat(ctx.repo / rel).st_size
    log = run_git(
        ctx.repo,
        "log",
        f"--since={CHURN_DAYS} days ago",
        "--numstat",
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
    now = time.time()
    for top in files:
        ctx.metrics[f"size.files:{top}"] = files[top]
        ctx.metrics[f"size.bytes:{top}"] = size[top]
        ctx.metrics[f"churn.{CHURN_DAYS}d:{top}"] = (
            None if churn is None else churn[top]
        )
        if top != ".":
            last = run_git(
                ctx.repo,
                "log",
                "-1",
                "--format=%ct",
                "--end-of-options",
                "HEAD",
                "--",
                top,
            )
            stamp = last.stdout.strip()
            ctx.metrics[f"last_touch_days:{top}"] = (
                int((now - int(stamp)) // 86400) if stamp.isdigit() else None
            )


def _tool_configs(ctx: _Ctx) -> None:
    """Record every scanner config/ignore file the target ships (they can quieten a tool)."""
    found = [rel for rel in ctx.files if Path(rel).name in TOOL_CONFIGS]
    for rel in found:
        ctx.trail(f"tool-config:{rel}", [], None, 0.0, "present")
    ctx.metrics["tool_config.overrides"] = len(found)


def _secrets(ctx: _Ctx) -> None:
    report = ctx.work / "gitleaks.json"
    args = [
        "detect",
        "--no-git",
        "--redact",
        "-s",
        ".",
        "-f",
        "json",
        "-r",
        str(report),
        "--exit-code",
        "0",
    ]
    try:
        _tool(ctx, "gitleaks", args, _gitleaks, (), report=report, ok=(0,))
    finally:
        report.unlink(missing_ok=True)
    seen = {(c.path, c.line) for c in ctx.found if c.rule == "security.secret"}
    regex = []
    for rel in ctx.files:
        if os.lstat(ctx.repo / rel).st_size > SECRET_SCAN_MAX_BYTES:
            continue
        try:
            text = (ctx.repo / rel).read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for rule, line in secret_lines(text):
            if (
                rel,
                line,
            ) not in seen:  # gitleaks first, then the first rule in PATTERNS order
                seen.add((rel, line))
                regex.append(_secret(rel, line, rule))
    ctx.add(regex, {})
    ctx.metrics["secrets.findings"] = sum(
        c.rule == "security.secret" for c in ctx.found
    )


def _network(ctx: _Ctx, tier: Tier) -> None:
    if tier != "deep":
        for name in NETWORK_TOOLS:
            ctx.record(name, [name], None, 0.0, ToolStatus.SKIPPED)
        ctx.metrics.update({"sast.findings": None, "deps.vulns": None})
        return
    semgrep = [
        "scan",
        "--config",
        "p/default",
        "--metrics=off",
        "--json",
        "--quiet",
        ".",
    ]
    _tool(ctx, "semgrep", semgrep, _semgrep, ("sast.findings",))
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
        pip_audit = ["-f", "json", "--no-deps", "--disable-pip", "-r", req]
        _tool(ctx, "pip-audit", pip_audit, _pip_audit(req), ("deps.vulns",))


def _is_test(path: str, name: str) -> bool:
    parts = path.split("/")
    return (
        bool({"tests", "test"} & set(parts[:-1]))
        or parts[-1].startswith("test_")
        or name.startswith("test_")
    )


def _codemem(ctx: _Ctx) -> None:
    """Every call: `codemem --db <work>/codemem.db …` with cwd = the target. Failure → unknown."""
    ctx.tools.update(dict.fromkeys(CODEMEM_INPUTS, ToolStatus.UNKNOWN))
    ctx.metrics.update(
        dict.fromkeys([*(f"layers.{k}" for k in LAYERS), "dead_code.candidates"])
    )
    # Not _binary(): codemem ships with the forge, so a missing one is `unknown`, never `absent` (AC12).
    binary = os.environ.get("CODEMEM_BIN") or shutil.which(
        "codemem", path=absolute_path(os.environ.get("PATH", ""))
    )
    if not binary:
        ctx.trail("codemem.build", ["codemem"], None, 0.0, ToolStatus.UNKNOWN)
        return
    db = str(ctx.work / "codemem.db")

    def call(label: str, *args: str) -> bytes | None:
        argv = [binary, "--db", db, *args]
        rc, out, secs = _exec(ctx, argv)
        ctx.trail(
            label, argv, rc, secs, ToolStatus.RAN if rc == 0 else ToolStatus.UNKNOWN
        )
        return out if rc == 0 else None

    def query(tool: str, *args: str) -> dict[str, Any] | None:
        out = call(f"codemem.{tool}", "query", tool, *args)
        try:
            doc = json.loads(out) if out else None
        except ValueError:
            return None
        return doc if isinstance(doc, dict) and not doc.get("error") else None

    def ran(
        tool: str, fill: Callable[[dict[str, Any]], None], doc: dict[str, Any] | None
    ) -> bool:
        if doc is None:
            return False
        try:
            fill(doc)
        except (KeyError, TypeError, ValueError):
            return False
        ctx.tools[f"codemem.{tool}"] = ToolStatus.RAN
        return True

    if call("codemem.build", "build", "--repo-root", str(ctx.repo)) is None:
        return
    commits = call(
        "codemem.refresh-commits", "refresh-commits", "--repo-root", str(ctx.repo)
    )
    inserted = _INSERTED.search(commits.decode("utf-8", "replace")) if commits else None

    def dead_code(d: dict[str, Any]) -> None:
        if d["truncated"]:
            raise ValueError("truncated")
        ctx.metrics["dead_code.candidates"] = sum(
            not _is_test(s["file"], s["name"]) for s in d["symbols"]
        )

    def layers(d: dict[str, Any]) -> None:
        ctx.metrics.update({f"layers.{k}": len(d["layers"][k]) for k in LAYERS})

    ran("dead_code", dead_code, query("dead_code", "--budget", str(DEAD_CODE_BUDGET)))
    ran("layers", layers, query("layers"))
    if not inserted or int(inserted.group(1)) == 0:
        return  # no commit rows: the git-history inputs stay unknown, never zero

    hot: list[str] = []

    def hot_spots(d: dict[str, Any]) -> None:
        ctx.metrics.update({f"hot_spot:{f['path']}": f["score"] for f in d["files"]})
        hot.extend(f["path"] for f in d["files"][:CO_CHANGE_FILES])

    if ran("hot_spots", hot_spots, query("hot_spots")):
        pairs: dict[str, int | float | None] = {}

        def co_changes(target: str) -> Callable[[dict[str, Any]], None]:
            return lambda d: pairs.update(
                {f"co_change:{target}|{f['path']}": f["count"] for f in d["files"]}
            )

        if all(ran("co_changes", co_changes(t), query("co_changes", t)) for t in hot):
            ctx.metrics.update(pairs)
            ctx.tools["codemem.co_changes"] = (
                ToolStatus.RAN
            )  # also when there is no hot file
        else:
            ctx.tools["codemem.co_changes"] = ToolStatus.UNKNOWN

    owned: dict[str, int | float | None] = {}
    for top in sorted({_top(f) for f in ctx.files} - {"."}):
        doc = query(
            "owners", f"{top}/", "--repo-root", str(ctx.repo)
        )  # a dir needs its trailing /
        if doc is None:
            return
        if doc.get("authors"):  # counts and shares only — never an email
            owned[f"owners.authors:{top}/"] = len(doc["authors"])
            owned[f"owners.top_pct:{top}/"] = round(
                float(doc["authors"][0]["percentage"]), 1
            )
    if owned:
        ctx.metrics.update(owned)
        ctx.tools["codemem.owners"] = ToolStatus.RAN


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
            schema_version=SCHEMA_VERSION,
            id=fid,
            origin=Origin.MEASURED,
            redacted=False,
            dimension=c.dimension,
            severity=c.severity,
            confidence=Confidence.HIGH,
            rule=c.rule,
            title=c.title,
            path=c.path,
            line=c.line,
            anchor=c.anchor,
            refutation=Refutation.NOT_REQUIRED,
            evidence=c.evidence,
        )  # fmt: skip


def measure(repo: Path, tier: Tier, *, tool_timeout: float = TOOL_TIMEOUT_S) -> Path:
    """Measure `repo` at `tier`; returns the work dir holding measure.json and run.log."""
    repo = Path(repo).absolute()
    stamp = build_stamp(repo, tier)
    root = safe_dir(repo, str(REPORTS_ROOT))
    ensure_self_ignoring(root)
    work_rel = str(REPORTS_ROOT / f"{WORK_PREFIX}{stamp.sha12}")
    if os.path.lexists(repo / work_rel):
        shutil.rmtree(safe_dir(repo, work_rel))
    work = safe_dir(repo, work_rel)

    ctx = _Ctx(repo, work, tool_timeout, _tracked_regular_files(repo))
    _git_metrics(ctx)
    _tool_configs(ctx)
    _tool(
        ctx,
        "lizard",
        ["--csv", *ctx.files],
        _lizard(ctx),
        ("complexity.functions", "complexity.ccn_max", COMPLEXITY_OVER),
    )
    jscpd_out = work / "jscpd"
    jscpd = ["--reporters", "json", "--output", str(jscpd_out), "--silent", *ctx.files]
    _tool(
        ctx,
        "jscpd",
        jscpd,
        _jscpd(ctx),
        ("duplication.pct", "duplication.clones"),
        report=jscpd_out / "jscpd-report.json",
    )
    shutil.rmtree(jscpd_out, ignore_errors=True)
    _secrets(ctx)
    _network(ctx, tier)
    _codemem(ctx)

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
