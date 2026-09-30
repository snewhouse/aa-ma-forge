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
    # TODOS follow-up (2026-09-27): the PROJECT_INDEX references M13 left outside its Contract.
    ROOT / "claude-code/commands/aa-ma-plan.md",
    ROOT / "claude-code/commands/execute-aa-ma-milestone.md",
    ROOT / "claude-code/agents/codebase-onboarding-runbook.md",
    ROOT / "claude-code/agents/codebase-onboarding-conventions.md",
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
# codebase-analysis-skills M4: the one legacy-absorb rule replaced DIMENSIONS.md's conditional line.
LEGACY_RULE = "`.claude/reports/codebase-deep-dive-*/` — **legacy deep-dive output**"
KEPT = [("SKILL.md", LEGACY_RULE)]


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


def test_write_footprint_is_declared_up_front() -> None:
    text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    bullet = text[text.index("**Read-only on the target's code.**"):]
    bullet = bullet[: bullet.index("\n- **")]
    for path in ("docs/architecture/", ".codemem/", ".gitignore", "hand-authored"):
        assert path in bullet, path


def _living_doc_fence() -> str:
    text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    m = re.search(r"^#### Living architecture doc\b.*?^```bash\n(.*?)^```$", text, re.S | re.M)
    assert m, "SKILL.md must carry the Deep tier's `#### Living architecture doc` bash fence"
    return m.group(1)


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, text=True).stdout


def _target(tmp_path: Path, gitignore: str = "*.pyc") -> Path:
    repo = tmp_path / "target"
    (repo / "pkg").mkdir(parents=True)
    (repo / "pkg" / "a.py").write_text("from pkg import b\n\ndef f():\n    b.g()\n")
    (repo / "pkg" / "b.py").write_text("def g():\n    return 1\n")
    (repo / ".gitignore").write_text(gitignore)  # no trailing newline: the append must not join lines
    _git(repo, "init", "-q")
    _git(repo, "add", ".")
    _git(repo, "-c", "user.email=t@t.dev", "-c", "user.name=t", "commit", "-q", "-m", "seed")
    return repo


def _run_fence(repo: Path, aa_ma_root: Path = ROOT) -> subprocess.CompletedProcess:
    env = {"AA_MA_ROOT": str(aa_ma_root), "PATH": os.environ["PATH"], "HOME": os.environ["HOME"]}
    return subprocess.run(["bash", "-c", _living_doc_fence()], cwd=repo, env=env,
                          capture_output=True, text=True, timeout=300)


def test_deep_tier_fence_writes_the_living_doc_and_ignores_the_index_once(tmp_path: Path) -> None:  # AC4
    repo = _target(tmp_path)
    for _ in range(2):
        assert _run_fence(repo).returncode == 0
    assert (repo / ".gitignore").read_text().splitlines() == ["*.pyc", ".codemem/"]
    assert (repo / "docs/architecture/component.md").is_file()
    status = _git(repo, "status", "--porcelain", "--untracked-files=all")
    assert ".codemem" not in status
    assert "docs/architecture/" in status


def test_fence_never_overwrites_a_hand_authored_architecture_doc(tmp_path: Path) -> None:
    """§6.8 CRITICAL: `draw --write` replaces docs/architecture/*.md whatever they hold."""
    repo = _target(tmp_path)
    own = repo / "docs/architecture/README.md"
    own.parent.mkdir(parents=True)
    own.write_text("# Our architecture\n\nWritten by the team.\n")
    r = _run_fence(repo)
    assert r.returncode == 0  # skipped, not failed: the tier notes it and carries on
    assert own.read_text() == "# Our architecture\n\nWritten by the team.\n"
    assert not (repo / "docs/architecture/component.md").exists()
    assert "hand-authored" in r.stderr + r.stdout


@pytest.mark.parametrize("link", [".gitignore", ".codemem"])
def test_fence_refuses_a_symlinked_gitignore_or_index_dir(tmp_path: Path, link: str) -> None:
    repo = _target(tmp_path)
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "victim").write_text("keep\n")
    (repo / link).unlink() if (repo / link).exists() else None
    (repo / link).symlink_to(outside / "victim" if link == ".gitignore" else outside)
    r = _run_fence(repo)
    assert r.returncode != 0 and "symlink" in r.stderr
    assert (outside / "victim").read_text() == "keep\n"
    assert sorted(p.name for p in outside.iterdir()) == ["victim"]


def test_fence_refuses_without_an_aa_ma_forge_checkout_and_touches_nothing(tmp_path: Path) -> None:
    repo = _target(tmp_path)
    r = _run_fence(repo, aa_ma_root=tmp_path / "nowhere")
    assert r.returncode != 0 and "aa-ma-forge" in r.stderr
    assert (repo / ".gitignore").read_text() == "*.pyc"
    assert not (repo / "docs").exists()


def test_system_mapping_does_not_call_layers_core_entry_points() -> None:
    """§6.8: `layers` ranks by incoming calls — its core is the most-depended-on code."""
    text = (ROOT / "claude-code/skills/system-mapping/SKILL.md").read_text(encoding="utf-8")
    assert "top entry points" not in text


# Double-check (2026-09-27): routing and related-tools lines that still sent readers to the
# unshipped commands — the verdict's four plus three siblings of the same shape.
ROUTES_TO_UNSHIPPED = [
    ("claude-code/skills/understand-codebase/SKILL.md", "Reuses /index, gsd-map-codebase, /codebase-deep-dive,"),
    ("claude-code/skills/understand-codebase/SKILL.md", "no onboarding deliverable → `/codebase-deep-dive`."),
    ("claude-code/skills/understand-codebase/SKILL.md", "structural index for tooling → `/index`."),
    ("claude-code/skills/understand-codebase/SKILL.md", "`/index` · `/codebase-deep-dive` ·"),
    ("claude-code/skills/system-mapping/SKILL.md", "| `/codebase-deep-dive` | Comprehensive audit |"),
    ("claude-code/skills/system-mapping/SKILL.md", "- `/codebase-deep-dive` - For comprehensive codebase audits"),
    ("claude-code/commands/understand-codebase.md", "no onboarding deliverable → `/codebase-deep-dive`; implementation"),
    ("claude-code/commands/understand-codebase.md", "just a structural index → `/index`;"),
    ("claude-code/commands/aa-ma-plan.md", "suggest /index for structural awareness"),
    # project-index's blast_radius is upstream, codemem's downstream: §6.3 must not ask for callers with it.
    ("claude-code/commands/execute-aa-ma-milestone.md", "call `blast_radius(symbol, depth=2)` via MCP or CLI"),
]


@pytest.mark.parametrize("rel, text", ROUTES_TO_UNSHIPPED)
def test_no_route_to_an_unshipped_command(rel: str, text: str) -> None:
    assert text not in (ROOT / rel).read_text(encoding="utf-8")


# --- codebase-analysis-skills M4: repoint onto /assess-codebase + residuals R1 R2 R5 R7 R8 N1 ----

CC = ROOT / "claude-code"
COMMAND = CC / "commands/understand-codebase.md"
CONTRACT_LEGACY = "no stamp — including a legacy `codebase-deep-dive-*` dir — is \"legacy, unverified\""


def _lines(needle: str) -> list[tuple[str, str]]:
    return [(str(p.relative_to(CC)), line) for p in sorted(CC.rglob("*.md"))
            for line in p.read_text(encoding="utf-8").splitlines() if needle in line]  # fmt: skip


def _section(text: str, heading: str) -> str:
    start = text.index(heading)
    nxt = re.search(r"^#{2,3} ", text[start + len(heading):], re.M)
    return text[start : start + len(heading) + (nxt.start() if nxt else len(text))]


def test_deep_dive_is_named_only_by_the_legacy_rule_and_the_contract() -> None:  # AC1 (Ste: 2 sites)
    hits = _lines("codebase-deep-dive")
    assert [f for f, _ in hits] == ["skills/understand-codebase/SKILL.md",
                                    "skills/understand-codebase/references/ANALYSIS-CONTRACT.md"], hits  # fmt: skip
    (_, rule), (_, contract) = hits
    assert LEGACY_RULE in rule and "legacy, unverified" in rule and "aa-ma-analysis fresh" in rule
    assert CONTRACT_LEGACY in (SKILL / "references/ANALYSIS-CONTRACT.md").read_text(encoding="utf-8").replace("\n  ", " ")
    assert contract


def test_no_deep_analysis_and_no_skill_aa_ma_plan() -> None:  # AC3
    assert _lines("deep-analysis") == [] and _lines("Skill(aa-ma-plan)") == []


def test_r1_degradation_row_drops_the_deep_dive() -> None:
    text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    assert "| `gsd-codebase-mapper` unavailable | Deep → enhanced-Standard. Note. |" in text


def test_r2_command_names_codemem_as_the_index_and_keeps_assess_output() -> None:
    (line,) = [x for x in COMMAND.read_text(encoding="utf-8").splitlines() if x.startswith("3. Follow the skill exactly")]
    assert "codemem" in line and "/assess-codebase" in line and "/index" not in line


def test_r5_quick_links_a_real_assess_report() -> None:
    quick = _section((SKILL / "SKILL.md").read_text(encoding="utf-8"), "### Quick")
    assert ".claude/reports/assess-codebase/<sha12>/report.md" in quick


def test_r7_deep_flag_no_longer_claims_unshipped_commands() -> None:
    (line,) = [x for x in COMMAND.read_text(encoding="utf-8").splitlines() if x.startswith("- a **tier flag**")]
    assert "/codebase-deep-dive" not in line and "/index" not in line and "/assess-codebase" in line


def test_r8_whole_repo_audit_routes_to_assess_codebase() -> None:
    for text in ((SKILL / "SKILL.md").read_text(encoding="utf-8"), COMMAND.read_text(encoding="utf-8")):
        assert "ships no whole-repo audit" not in text and "no whole-repo audit ships here" not in text
        assert re.search(r"audit[^\n]*→ `/assess-codebase`", text)


def test_n1_follow_on_planning_is_the_aa_ma_plan_command() -> None:
    related = _section((SKILL / "SKILL.md").read_text(encoding="utf-8"), "## Related skills / commands")
    assert "`/aa-ma-plan` (follow-on, when you go to change it)" in related


def test_step_0_judges_assess_and_legacy_freshness_by_sha() -> None:  # AC4 (narrowed, Ste)
    text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    step0 = _section(text, "## Step 0")
    assert "aa-ma-analysis fresh" in step0
    (gsd,) = [x for x in step0.splitlines() if x.startswith("| `.planning/codebase/*.md`")]
    assert "git log -1 --format=%cd" in gsd  # gsd output has no SHA stamp: its date rule stays
    reuse = (SKILL / "references/REUSE-MAP.md").read_text(encoding="utf-8")
    stale = reuse[reuse.index("2. **Only run a heavy tool"): reuse.index("3. **Record what was absorbed")]
    assert "aa-ma-analysis fresh" in stale and "git log -1 --format=%cd" not in stale.split("gsd")[0]
    # Dimension-13 liveness checks are not report freshness: they stay.
    assert "`git log -1 --format=%cd` (is the repo alive?)" in (SKILL / "references/DIMENSIONS.md").read_text(encoding="utf-8")
    assert "`git log -1 --format=%cd` (alive?)" in (CC / "agents/codebase-onboarding-health.md").read_text(encoding="utf-8")


def test_step_0_absorbs_a_fresh_assess_report_and_drops_refuted_findings() -> None:
    for rel in ("SKILL.md", "references/REUSE-MAP.md"):
        text = (SKILL / rel).read_text(encoding="utf-8")
        (row,) = [x for x in text.splitlines() if "`.claude/reports/assess-codebase/<sha12>" in x and "summary.json" in x]
        assert "findings.jsonl" in row and "refuted" in row and "aa-ma-analysis fresh" in row, rel


def test_deep_asks_once_to_run_assess_first() -> None:
    deep = _section((SKILL / "SKILL.md").read_text(encoding="utf-8"), "### Deep")
    assert "/assess-codebase" in deep and "ask once" in deep
