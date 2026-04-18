#!/usr/bin/env python3
"""codemem doc-drift check (M4 Task 4.6).

Narrow, codemem-scoped wrapper around the Tier 1 + Tier 2 logic defined
by ``Skill(doc-drift-detection)``. Use this from ``/commit-and-push``,
``/pre-commit-full``, CI, or standalone when you want a focused report
on codemem-specific documentation drift rather than the whole-project
pass.

Two checks:

* **Tier 1 — codemem version strings.** Reads the canonical codemem
  version from ``packages/codemem-mcp/pyproject.toml`` (the workspace
  member's own ``[project].version``), scans codemem-specific markdown
  (``claude-code/codemem/README.md``, ``docs/codemem/*.md``,
  ``docs/demo/codemem-*.md``) for PEP-440-shaped version strings that
  do not match the canonical and appear in a ``codemem``/``version``
  context window. Handles dotted (``1.2.3.dev0``), dashed
  (``1.2.3-dev``), and no-separator (``1.2.3a1``, ``1.2.3rc1``)
  suffix forms.
* **Tier 2 — codemem CHANGELOG completeness.** Walks conventional
  commits (``feat:``, ``fix:``, ``BREAKING CHANGE``) since the last tag
  that touched any codemem path; fails if the repo has notable commits
  and ``CHANGELOG.md`` lacks an ``Unreleased`` section.

Post-M4 follow-up: Tier-6-analog tool-count drift. Earlier draft
imported ``codemem.mcp.server`` which doesn't exist as a Python module
(the MCP server lives at ``claude-code/codemem/mcp/server.py``, outside
the package). Reinstating the check requires ``importlib.util`` to load
server.py by file path — filed as a post-M4 task rather than patched
mid-milestone.

Exits 0 on clean, 1 on any finding, 2 on malformed input.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path


CODEMEM_DOC_GLOB = (
    "claude-code/codemem/README.md",
    "docs/codemem/*.md",
    "docs/demo/codemem-*.md",
)
# Frozen design-phase artefacts — captures the plan at a point in time;
# retroactive drift updates would violate the "historical docs are frozen"
# rule in CLAUDE.md. Listed explicitly rather than inferred from naming so
# every exclusion requires deliberate intent.
CODEMEM_DOC_EXCLUDE = (
    "docs/codemem/design-scratchpad.md",
)
CODEMEM_PATH_PREFIXES = (
    "packages/codemem-mcp/",
    "claude-code/codemem/",
    "docs/codemem/",
    "docs/demo/codemem-",
    "tests/codemem/",
)
# PEP-440-compatible version matcher. Accepts:
#   1.2.3                     (plain)
#   1.2.3.dev0 / 1.2.3-dev    (dotted or dashed suffix separator)
#   1.2.3a1 / 1.2.3rc1        (no-separator alpha/beta/rc/post forms)
# Leading `\b` anchors the number; the two alternatives in the optional
# non-capturing group cover all three suffix styles. Regex-engine greed
# on the optional group handles the "prefix of longer version" concern
# (e.g. scanning `0.1.0-dev` matches the whole `0.1.0-dev` in one step
# rather than re-matching `0.1.0` as a standalone).
VERSION_RE = re.compile(
    r"\b\d+\.\d+\.\d+"
    r"(?:"
    r"[.\-][A-Za-z0-9]+"          # dotted or dashed suffix: .dev0 / -dev
    r"|"
    r"[A-Za-z]+\d*"                # no-separator PEP 440: a1 / rc1
    r")?"
)


@dataclass
class Finding:
    tier: str
    severity: str  # CRITICAL / WARNING / INFO
    file: str | None
    line: int | None
    message: str

    def format(self) -> str:
        loc = f"{self.file}:{self.line}" if self.file and self.line else self.file or "-"
        return f"[{self.severity}] {self.tier}\n  File: {loc}\n  Finding: {self.message}"


# ---------------------------------------------------------------------
# Tier 1
# ---------------------------------------------------------------------

def canonical_codemem_version(repo_root: Path) -> str | None:
    pj = repo_root / "packages" / "codemem-mcp" / "pyproject.toml"
    if not pj.exists():
        return None
    for line in pj.read_text().splitlines():
        m = re.match(r'^\s*version\s*=\s*"([^"]+)"', line)
        if m:
            return m.group(1)
    return None


def _iter_codemem_docs(repo_root: Path) -> list[Path]:
    excluded = {repo_root / rel for rel in CODEMEM_DOC_EXCLUDE}
    out: list[Path] = []
    for pattern in CODEMEM_DOC_GLOB:
        for p in repo_root.glob(pattern):
            if p.is_file() and p not in excluded:
                out.append(p)
    return out


def check_tier_1_version_strings(repo_root: Path) -> list[Finding]:
    canonical = canonical_codemem_version(repo_root)
    if canonical is None:
        return []
    findings: list[Finding] = []
    for doc in _iter_codemem_docs(repo_root):
        for lineno, line in enumerate(doc.read_text().splitlines(), start=1):
            # Skip obvious prose hits: dates (YYYY-MM-DD) and software version
            # pin references (>=0.42,<0.43) are not drift — drift is a bare
            # "0.1.0" or "0.1.0.dev0" that mismatches canonical.
            for m in VERSION_RE.finditer(line):
                candidate = m.group(0)
                if candidate == canonical:
                    continue
                # Exclude third-party versions pinned in documented form.
                # Heuristic: require the candidate to appear immediately
                # adjacent to "codemem" OR "version" within 40 chars.
                window = line[max(0, m.start() - 40):m.end() + 40].lower()
                if "codemem" not in window and "version" not in window:
                    continue
                findings.append(Finding(
                    tier="Tier 1: codemem Version String",
                    severity="WARNING",
                    file=str(doc.relative_to(repo_root)),
                    line=lineno,
                    message=(
                        f"'{candidate}' in context near codemem/version but "
                        f"canonical is '{canonical}'"
                    ),
                ))
    return findings


# ---------------------------------------------------------------------
# Tier 2
# ---------------------------------------------------------------------

def _git(args: list[str], cwd: Path) -> str:
    r = subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True, check=False,
    )
    return r.stdout if r.returncode == 0 else ""


def check_tier_2_changelog_completeness(repo_root: Path) -> list[Finding]:
    last_tag = _git(["describe", "--tags", "--abbrev=0"], repo_root).strip()
    if not last_tag:
        return []
    commits_log = _git(
        ["log", f"{last_tag}..HEAD", "--name-only", "--pretty=format:%H %s"],
        repo_root,
    )
    if not commits_log:
        return []

    notable_touching_codemem: list[tuple[str, str]] = []  # (sha, subject)
    current_sha: str | None = None
    current_subject: str | None = None
    current_files: list[str] = []

    def _flush() -> None:
        if current_sha is None:
            return
        # Check conventional commit type.
        if not re.match(r"^(feat|fix)(\([^)]*\))?:|BREAKING CHANGE", current_subject or "", re.I):
            return
        # Did this commit touch any codemem path?
        if any(
            f.startswith(CODEMEM_PATH_PREFIXES) for f in current_files
        ):
            notable_touching_codemem.append((current_sha, current_subject or ""))

    for line in commits_log.splitlines():
        if " " in line and len(line) >= 40 and re.match(r"^[0-9a-f]{7,40}\b", line):
            _flush()
            parts = line.split(" ", 1)
            current_sha = parts[0]
            current_subject = parts[1] if len(parts) > 1 else ""
            current_files = []
        elif line.strip():
            current_files.append(line.strip())
    _flush()

    if not notable_touching_codemem:
        return []

    changelog = repo_root / "CHANGELOG.md"
    has_unreleased = False
    if changelog.exists():
        text = changelog.read_text().lower()
        has_unreleased = "unreleased" in text or "upcoming" in text

    if has_unreleased:
        return []

    return [Finding(
        tier="Tier 2: codemem CHANGELOG Behind",
        severity="WARNING",
        file="CHANGELOG.md",
        line=None,
        message=(
            f"{len(notable_touching_codemem)} feat/fix commits touching codemem "
            f"paths since {last_tag} but CHANGELOG.md has no 'Unreleased' section"
        ),
    )]


# ---------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------

def run_checks(repo_root: Path) -> list[Finding]:
    return (
        check_tier_1_version_strings(repo_root)
        + check_tier_2_changelog_completeness(repo_root)
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="check_codemem_doc_drift")
    parser.add_argument(
        "--repo-root", default=os.getcwd(),
        help="Repo root (default: cwd)",
    )
    parser.add_argument(
        "--json", action="store_true",
        help="Emit findings as JSON (one object per finding)",
    )
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root).resolve()
    findings = run_checks(repo_root)

    if args.json:
        print(json.dumps(
            [
                {
                    "tier": f.tier,
                    "severity": f.severity,
                    "file": f.file,
                    "line": f.line,
                    "message": f.message,
                }
                for f in findings
            ],
            indent=2,
        ))
    else:
        if not findings:
            print("codemem doc-drift: no findings.")
        else:
            print(f"codemem doc-drift: {len(findings)} finding(s)")
            print()
            for f in findings:
                print(f.format())
                print()
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
