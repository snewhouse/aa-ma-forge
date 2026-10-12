"""Contract for the touched-files lint harness (code-conventions-impact M1, ADR-0018).

pre-commit is the one harness: staged files locally, the PR diff in CI. Every lint hook is
``repo: local`` so it runs the uv-locked tool versions, never a hook repo's own pin. The one
remote repo, gitleaks (M8.3), supplies only a hook definition at a frozen SHA; its
``gitleaks-system`` hook runs the installed binary.
"""

from __future__ import annotations

import re
import subprocess
import tomllib
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[1]
HOOK_IDS = {"ruff-check", "ruff-format", "shellcheck", "check-conventions"}


def _pyproject() -> dict:
    return tomllib.loads((REPO / "pyproject.toml").read_text(encoding="utf-8"))


def _hook(hook_id: str) -> dict:
    config = yaml.safe_load(
        (REPO / ".pre-commit-config.yaml").read_text(encoding="utf-8")
    )
    return next(h for r in config["repos"] for h in r["hooks"] if h["id"] == hook_id)


def _dev_group_names() -> set[str]:
    names = set()
    for spec in _pyproject()["dependency-groups"]["dev"]:
        # why: strip the PEP 508 specifier, extras and markers to the bare name.
        names.add(re.split(r"[<>=!~\[ ;]", spec, maxsplit=1)[0].lower())
    return names


def test_no_deprecated_uv_dev_dependencies() -> None:
    assert "dev-dependencies" not in _pyproject().get("tool", {}).get("uv", {})


def test_harness_tools_in_dev_group() -> None:
    names = _dev_group_names()
    assert {"pre-commit"} <= names


def test_precommit_hooks_are_local_and_complete() -> None:
    config = yaml.safe_load(
        (REPO / ".pre-commit-config.yaml").read_text(encoding="utf-8")
    )
    found = {}
    for repo in config["repos"]:
        for hook in repo["hooks"]:
            found[hook["id"]] = repo["repo"]
    assert HOOK_IDS <= set(found)
    assert all(found[hook_id] == "local" for hook_id in HOOK_IDS)


def test_shellcheck_hook_skips_bats() -> None:
    # why: identify tags .bats as `shell`; bats syntax is not plain shell, and CI's
    # ShellCheck job has only ever covered *.sh (19 of 31 .bats files fail today).
    hook = _hook("shellcheck")
    assert "bats" in hook.get("exclude_types", [])


def test_shellcheck_hook_enables_set_e_suppressed_only(tmp_path: Path) -> None:
    # why: SC2310 (set -e silently off inside a condition) is opt-in and the hook
    # turns it on (T8). SC2312 was dropped after M6 (Ste, 2026-10-11): 116 of the
    # 124 findings due on touch, mostly the harmless `echo "$(cmd)"` form.
    hook = _hook("shellcheck")
    script = tmp_path / "s.sh"
    script.write_text(
        '#!/bin/bash\nset -e\nf() { false; }\nif f; then :; fi\necho "$(date)"\n'
    )
    proc = subprocess.run(
        [hook["entry"], *hook.get("args", []), "--format=gcc", str(script)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert "SC2310" in proc.stdout
    assert "SC2312" not in proc.stdout
