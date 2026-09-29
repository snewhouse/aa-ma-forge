"""Shared fixtures for aa_ma.analysis tests.

Git identity comes from env, never the runner's global config, and the default branch is never
assumed to be `main` (plan §0; precedent tests/codemem/test_owners.py).
"""

from __future__ import annotations

import os
import sys
import subprocess
from pathlib import Path

import pytest

GIT_ENV = {
    "GIT_AUTHOR_NAME": "Fixture",
    "GIT_AUTHOR_EMAIL": "fixture@example.invalid",
    "GIT_COMMITTER_NAME": "Fixture",
    "GIT_COMMITTER_EMAIL": "fixture@example.invalid",
}


def git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        env={**os.environ, **GIT_ENV},
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def commit_file(repo: Path, rel: str, text: str, msg: str = "c") -> str:
    path = repo / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    git(repo, "add", "--", rel)
    git(repo, "commit", "-q", "-m", msg)
    return git(repo, "rev-parse", "HEAD")


def make_repo(root: Path, files: dict[str, str]) -> Path:
    """A git repo at `root` with one commit of `files`."""
    root.mkdir()
    git(root, "init", "-q")
    for rel, text in files.items():
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        (root / rel).write_text(text, encoding="utf-8")
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", "init")
    return root


@pytest.fixture(autouse=True)
def cache(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """The stage root measure prefers: per test, on the same filesystem as the targets, outside
    any git work tree — never the real ~/.cache."""
    root = tmp_path / "cache"
    monkeypatch.setenv("XDG_CACHE_HOME", str(root))
    return root


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """A git repo with one commit of three tracked files."""
    return make_repo(
        tmp_path / "repo",
        {"src/app.py": "print(1)\n", "src/db.py": "x = 1\n", "README.md": "# toy\n"},
    )


# --- M2: fixture target repo + tool seams ------------------------------------------------------

# Assembled at runtime; matches the github-token rule.
FAKE_TOKEN = "gh" + "p_" + "Q7" * 18
CALC = "def f1(x):\n    return x\n\n\ndef f2(y):\n    return y\n"
OPTIONAL_TOOLS = ("LIZARD", "JSCPD", "GITLEAKS", "SEMGREP", "OSV_SCANNER", "PIP_AUDIT")
CODEMEM = Path(sys.executable).with_name("codemem")


# What each real tool prints for --version (gitleaks: `version`), as live-probed in 2.1.
TOOL_VERSIONS = {
    "lizard": "1.24.0",
    "jscpd": "5.3.3",
    "gitleaks": "8.18.0",
    "semgrep": "1.156.0",
    "osv-scanner": "osv-scanner version: 2.6.0",
    "pip-audit": "pip-audit 2.10.0",
}


def stub_bin(bindir: Path, name: str, body: str, version: str | None = None) -> Path:
    """A /bin/sh stub; a tool stub also answers its version probe (default: the 2.1 version)."""
    path = bindir / name
    version = version or TOOL_VERSIONS.get(name)
    probe = (
        f'case "$1" in --version|version) echo "{version}"; exit 0;; esac\n'
        if version
        else ""
    )
    path.write_text("#!/bin/sh\n" + probe + body + "\n", encoding="utf-8")
    path.chmod(0o755)
    return path


@pytest.fixture
def target(tmp_path: Path) -> Path:
    """The M2 fixture repo: two source files (one holding a fake secret) and a README, one commit."""
    files = {
        "src/calc.py": CALC,
        "src/config.py": f'TOKEN = "{FAKE_TOKEN}"\n',
        "README.md": "# fixture\n",
    }
    return make_repo(tmp_path / "target", files)


@pytest.fixture
def tools(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Every optional tool absent and the workspace codemem; returns an empty dir for stubs."""
    for name in OPTIONAL_TOOLS:
        monkeypatch.setenv(f"{name}_BIN", "/nonexistent")
    monkeypatch.setenv("CODEMEM_BIN", str(CODEMEM))
    stubs = tmp_path / "stubs"
    stubs.mkdir()
    return stubs


def lizard_row(
    fn: str, ccn: int, start: int, end: int, path: str = "src/calc.py"
) -> str:
    """One row of `lizard --csv` (headerless, 11 columns)."""
    return f'2,{ccn},10,1,2,"{fn}@{start}-{end}@{path}","{path}","{fn}","{fn}( x )",{start},{end}\n'


def lizard_stub(stubs: Path, monkeypatch: pytest.MonkeyPatch, csv: str) -> Path:
    """A lizard stub printing whatever the returned CSV file holds."""
    report = stubs / "lizard.csv"
    report.write_text(csv, encoding="utf-8")
    monkeypatch.setenv("LIZARD_BIN", str(stub_bin(stubs, "lizard", f"cat '{report}'")))
    return report
