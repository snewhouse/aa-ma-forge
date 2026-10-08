"""Contract for the touched-files lint harness (code-conventions-impact M1, ADR-0018).

pre-commit is the one harness: staged files locally, the PR diff in CI. Every hook is
``repo: local`` so it runs the uv-locked tool versions, never a hook repo's own pin.
"""

from __future__ import annotations

import re
import tomllib
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[1]
HOOK_IDS = {"ruff-check", "ruff-format", "shellcheck", "check-conventions"}


def _pyproject() -> dict:
    return tomllib.loads((REPO / "pyproject.toml").read_text(encoding="utf-8"))


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
    assert {"pre-commit", "bandit"} <= names


def test_bandit_pinned_exactly() -> None:
    # why: M8.1 compares Ruff S against one Bandit version; a floating pin moves the baseline.
    assert "bandit==1.9.4" in _pyproject()["dependency-groups"]["dev"]


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
