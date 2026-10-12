"""The Ruff S canary (M8.2): proves the security rules fire, and that the canary is fenced off.

A scanner that reports nothing looks the same as one that never ran. The canary file
holds a known S602, so `ruff check --select S` on it must fail; the normal lint run
must skip it, through one exclusion that names one file.
"""

import re
import runpy
import subprocess
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CANARY = "tests/fixtures/canary/canary_shell.py"
AWS_KEY_ID = re.compile(r"(A3T[A-Z0-9]|AKIA|ASIA|ABIA|ACCA)[A-Z0-9]{16}")


def _ruff(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["uv", "run", "ruff", "check", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def test_ruff_s_flags_the_canary_when_scanned_explicitly() -> None:
    proc = _ruff("--isolated", "--select", "S", "--output-format", "concise", CANARY)
    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert "S602" in proc.stdout


def test_normal_lint_skips_the_canary_even_when_named() -> None:
    # pre-commit passes explicit paths; only --force-exclude makes ruff honour the exclusion.
    proc = _ruff("--force-exclude", CANARY)
    assert proc.returncode == 0, proc.stdout + proc.stderr


def test_the_canary_exclusion_names_one_file() -> None:
    cfg = tomllib.loads((ROOT / "pyproject.toml").read_text())
    excludes = cfg["tool"]["ruff"]["extend-exclude"]
    assert [e for e in excludes if "canary" in e] == [CANARY]


def test_precommit_ruff_hooks_force_exclude() -> None:
    text = (ROOT / ".pre-commit-config.yaml").read_text()
    assert "entry: uv run ruff check --force-exclude" in text
    assert "entry: uv run ruff format --check --force-exclude" in text


def test_the_fake_key_exists_only_at_runtime() -> None:
    source = (ROOT / CANARY).read_text()
    assert not AWS_KEY_ID.search(source)
    namespace = runpy.run_path(str(ROOT / CANARY))
    assert AWS_KEY_ID.fullmatch(namespace["FAKE_AWS_KEY_ID"])
