"""Ruff S is the Python security gate (M8.2, DECISION ruff-only).

Pins the configuration the gate depends on: S selected, a fixed set of S ignores
for tests only, the CI job that runs it, and a clean scan of the gated paths.
"""

import subprocess
import tomllib
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
SECURITY_YML = ROOT / ".github" / "workflows" / "security.yml"
GATE_CMD = "uv run ruff check --isolated --select S src packages scripts"
# Approved by Ste (M8.2): tests run git/bash on purpose (S603/S607), write tmp
# fixtures (S108), assert (S101); S110 predates M8 (logging standard).
TESTS_S_IGNORES = {"S101", "S108", "S110", "S603", "S607"}


def _lint() -> dict:
    return tomllib.loads((ROOT / "pyproject.toml").read_text())["tool"]["ruff"]["lint"]


def test_s_is_selected() -> None:
    assert "S" in _lint()["extend-select"]


def test_only_tests_ignore_s_rules_and_only_the_approved_set() -> None:
    s_ignores = {
        pattern: {code for code in codes if code.startswith("S")}
        for pattern, codes in _lint()["per-file-ignores"].items()
    }
    assert {p: c for p, c in s_ignores.items() if c} == {"tests/**": TESTS_S_IGNORES}
    assert not [c for c in _lint().get("extend-ignore", []) if c.startswith("S")]


def _jobs() -> dict:
    return yaml.safe_load(SECURITY_YML.read_text())["jobs"]


def test_bandit_job_is_gone() -> None:
    assert "bandit" not in _jobs()


def test_ruff_security_job_runs_the_gate_and_cannot_swallow_failure() -> None:
    job = _jobs()["ruff-security"]
    runs = [step.get("run", "") for step in job["steps"]]
    assert GATE_CMD in runs
    assert not [r for r in runs if "|| true" in r]


def test_ruff_security_runs_on_push_to_main_and_weekly() -> None:
    on = yaml.safe_load(SECURITY_YML.read_text())[True]  # YAML 1.1 reads `on:` as True
    assert on["push"]["branches"] == ["main"]
    assert on["schedule"][0]["cron"]


def test_gated_paths_are_clean() -> None:
    proc = subprocess.run(
        GATE_CMD.split(), cwd=ROOT, capture_output=True, text=True, check=False
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
