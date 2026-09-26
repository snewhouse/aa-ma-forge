"""understand-codebase rewired onto codemem (diagram-generation M13, Tickets 9 + 19).

Named sets, not judgements (plan AC5): each string below was measured at 1d10771 and is
an instruction to RUN a command the plugin does not ship (`/codebase-deep-dive`,
`/index`) or a `.mmd` sidecar the living doc retires. Conditional "reuse its output if
it ran" references stay (Ticket 9 decision 3).
"""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / "claude-code/skills/understand-codebase"
REWIRED = [  # the Contract's files + the Deep tier's team template (Ste, 13.4)
    SKILL / "SKILL.md",
    *(SKILL / "references" / f for f in (
        "DIMENSIONS.md", "DEEPDIVE-TEMPLATES.md", "REUSE-MAP.md", "PLAYBOOK-CONTRIBUTE.md",
        "PROS-CONS-RUBRIC.md", "ONBOARDING-TEMPLATE.md", "AGENTS-MD-TEMPLATE.md")),
    SKILL / "templates/onboarding-team.md",
    ROOT / "claude-code/skills/impact-analysis/SKILL.md",
    ROOT / "claude-code/skills/system-mapping/SKILL.md",
    ROOT / "claude-code/agents/codebase-onboarding-synthesizer.md",
]

# AC5 — the 7 instructions to run /codebase-deep-dive (4 in the Contract + 3 in the template).
DEEP_DIVE_RUNS = [
    ("references/REUSE-MAP.md", "invoke `Skill(codebase-deep-dive)` / the `/codebase-deep-dive` command"),
    ("SKILL.md", "`/codebase-deep-dive` (`.claude/reports/` + Mermaid)"),
    ("SKILL.md", "(still invoke `gsd-map-codebase`, `/codebase-deep-dive`"),
    ("SKILL.md", "Also run `/codebase-deep-dive`"),
    ("templates/onboarding-team.md", "(invoke `/codebase-deep-dive` directly"),
    ("templates/onboarding-team.md", "— /codebase-deep-dive → .claude/reports/"),
    ("templates/onboarding-team.md", "OK to run `gsd-map-codebase` + `/codebase-deep-dive`"),
]
# Ticket 19 — every instruction to run /index.
INDEX_RUNS = [
    ("SKILL.md", "`/index` if no `PROJECT_INDEX.json`"),
    ("SKILL.md", "run `/index` (`~/.claude-code-project-index/scripts/project_index.py`) first"),
    ("SKILL.md", "*optionally* run `/index`"),
    ("SKILL.md", "(run `/index` if not)"),
    ("SKILL.md", "Ensure `/index` has run."),
    ("SKILL.md", "| `/index` unavailable or too slow |"),
    ("references/REUSE-MAP.md", "→ run /index."),
    ("references/REUSE-MAP.md", "### `/index` — structural index"),
    ("references/DIMENSIONS.md", "`/index` if\n  absent"),
    ("templates/onboarding-team.md", "(still run `/index`,"),
    ("templates/onboarding-team.md", "(run /index if not)"),
]
# A conditional reuse reference that must survive (Ticket 9: harmless, a real reuse path).
KEPT = [("references/DIMENSIONS.md", "`/codebase-deep-dive` `01-architecture-overview.md`")]


@pytest.mark.parametrize("rel, text", DEEP_DIVE_RUNS + INDEX_RUNS)
def test_no_instruction_to_run_an_unshipped_command(rel: str, text: str) -> None:
    assert text not in (SKILL / rel).read_text(encoding="utf-8")


@pytest.mark.parametrize("rel, text", KEPT)
def test_conditional_reuse_references_stay(rel: str, text: str) -> None:
    assert text in (SKILL / rel).read_text(encoding="utf-8")


def test_mmd_sidecars_are_retired() -> None:
    hits = [f"{p.relative_to(ROOT)}:{n}" for p in REWIRED
            for n, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1) if ".mmd" in line]
    assert hits == []


def test_every_project_index_reference_names_codemem() -> None:  # AC7
    bare = [f"{p.relative_to(ROOT)}:{n}" for p in REWIRED
            for n, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1)
            if "PROJECT_INDEX" in line and "codemem" not in line]
    assert bare == []


def test_provisioning_points_at_codemem_build() -> None:
    for rel in ("SKILL.md", "references/REUSE-MAP.md", "templates/onboarding-team.md"):
        assert "codemem build" in (SKILL / rel).read_text(encoding="utf-8"), rel


def test_rule_set_stays_at_two() -> None:  # AC6
    assert sorted(p.name for p in (ROOT / "claude-code/rules").iterdir()) == [
        "aa-ma.md", "engineering-standards.md"]


def test_write_footprint_is_declared_up_front() -> None:
    text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    bullet = text[text.index("**Read-only on the target's code.**"):]
    bullet = bullet[: bullet.index("\n- **")]
    for path in ("docs/architecture/", ".codemem/", ".gitignore"):
        assert path in bullet, path


def _living_doc_fence() -> str:
    text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    m = re.search(r"^#### Living architecture doc\b.*?^```bash\n(.*?)^```$", text, re.S | re.M)
    assert m, "SKILL.md must carry the Deep tier's `#### Living architecture doc` bash fence"
    return m.group(1)


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, text=True).stdout


def test_deep_tier_fence_writes_the_living_doc_and_ignores_the_index_once(tmp_path: Path) -> None:  # AC4
    repo = tmp_path / "target"
    (repo / "pkg").mkdir(parents=True)
    (repo / "pkg" / "a.py").write_text("from pkg import b\n\ndef f():\n    b.g()\n")
    (repo / "pkg" / "b.py").write_text("def g():\n    return 1\n")
    (repo / ".gitignore").write_text("*.pyc")  # no trailing newline: the append must not join lines
    _git(repo, "init", "-q")
    _git(repo, "add", ".")
    _git(repo, "-c", "user.email=t@t.dev", "-c", "user.name=t", "commit", "-q", "-m", "seed")
    env = {"AA_MA_ROOT": str(ROOT), "PATH": os.environ["PATH"], "HOME": os.environ["HOME"]}
    for _ in range(2):
        subprocess.run(["bash", "-c", _living_doc_fence()], cwd=repo, env=env, check=True,
                       capture_output=True, text=True, timeout=300)
    assert (repo / ".gitignore").read_text().splitlines() == ["*.pyc", ".codemem/"]
    assert (repo / "docs/architecture/component.md").is_file()
    status = _git(repo, "status", "--porcelain", "--untracked-files=all")
    assert ".codemem" not in status
    assert "docs/architecture/" in status
