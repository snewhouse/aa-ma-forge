"""Angle 6 check 8 — every Contract path a milestone creates or modifies is drawn in §13
(diagram-generation M10).

Decisions (context-log 2026-09-25, Ste): the rule is executable (`aa_ma.render.coverage`,
opt-in `aa-ma-lint-views --coverage`) so the milestone gate, which never passes
`--coverage`, cannot reach it (ADR-0009). It reads `Create`/`Modify` rows and template-style
`# file: <path>` lines; `Test`/`Verify` rows, `tests/`, `docs/`, root docs and dependency
manifests/lockfiles are exempt; a directory node covers everything beneath it; a `(new)`
node covers its planned path. Planning-time only, for plans `Created:` >= 2026-09-11.
"""

from __future__ import annotations

import ast
import re
import subprocess
import textwrap
import time
from datetime import date, timedelta
from pathlib import Path

import pytest

from aa_ma.render import coverage
from aa_ma.render.cli import lint_main
from aa_ma.render.mermaid_lint import lint_plan

ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / "claude-code/skills/plan-verification/SKILL.md"
PLAN_CMD = ROOT / "claude-code/commands/aa-ma-plan.md"
SPEC = ROOT / "docs/spec/aa-ma-specification.md"
SEEDED = ROOT / "tests/fixtures/seeded-plan.md"


def _plan(contract: str, nodes: str = "", created: str | None = "2026-09-25") -> str:
    front = f"**Created:** {created}\n\n" if created else ""
    return (
        f"# p Plan\n\n{front}## Milestones\n\n### Milestone 1: x\n\n- Audit-Profile: code-only\n\n"
        f"#### Contract\n```\nFiles:\n{contract}\n```\n\n"
        f"## 13. Architecture View\n\n### Component view\n\n```mermaid\nflowchart LR\n{nodes}  Z[\"prose only\"]\n```\n"
    )


def _codes(text: str) -> list[str]:
    return [f.message.split(":")[0] for f in coverage.coverage_findings(text)]


THREE = "  Modify  src/a.py\n  Create  src/b.py\n  Modify  scripts/run.sh\n"


def test_three_undrawn_paths_give_three_findings():  # AC1
    findings = coverage.coverage_findings(_plan(THREE))
    assert [f.code for f in findings] == ["UNDRAWN_PATH"] * 3
    assert _codes(_plan(THREE)) == ["src/a.py", "src/b.py", "scripts/run.sh"]


def test_all_drawn_gives_none():  # AC2
    nodes = '  A["src/a.py"]\n  B["src/b.py (new)"]\n  R["scripts/run.sh"]\n'
    assert coverage.coverage_findings(_plan(THREE, nodes)) == []


@pytest.mark.parametrize(("created", "fires"), [("2026-09-10", False), (None, False), ("2026-09-11", True)])
def test_grandfathered_before_the_cutover(created, fires):  # AC3
    assert bool(coverage.coverage_findings(_plan(THREE, created=created))) is fires


def test_finding_points_at_the_contract_row():
    text = _plan(THREE)
    f = coverage.coverage_findings(text)[0]
    assert text.splitlines()[f.line - 1].strip() == "Modify  src/a.py"


@pytest.mark.parametrize(
    "row",
    [
        "  Test    src/a_test.py",
        "  Verify  src/a.py",
        "  Modify  tests/test_a.py",
        "  Modify  docs/spec/x.md",
        "  Modify  README.md",
        "  Modify  CHANGELOG.md",
        "  Modify  SECURITY.md",
        "  Modify  CONTEXT.md",
        "  Modify  packages/x/pyproject.toml",
        "  Modify  web/package.json",
        "  Modify  uv.lock",
        "  Modify  web/yarn.lock",
    ],
)
def test_exempt_rows(row):
    assert coverage.coverage_findings(_plan(row + "\n")) == []


def test_a_directory_node_covers_everything_beneath_it():
    rows = "  Modify  claude-code/skills/u/SKILL.md\n  Create  claude-code/skills/u/references/x.md\n"
    assert coverage.coverage_findings(_plan(rows, '  U["claude-code/skills/u/"]\n')) == []
    assert coverage.coverage_findings(_plan(rows, '  U["claude-code/skills/u"]\n')) == []
    # a prefix that is not a path component does not cover
    assert len(coverage.coverage_findings(_plan(rows, '  U["claude-code/skills/uu"]\n'))) == 2


def test_template_file_lines_braces_comments_and_suffixes():
    rows = (
        "# file: src/m.py   (append)\n"
        "  Modify  src/rules/{a,b}.yml   # two files\n"
        "  Modify  src/x.py, src/y.py\n"
    )
    assert _codes(_plan(rows)) == ["src/m.py", "src/rules/a.yml", "src/rules/b.yml", "src/x.py", "src/y.py"]


def test_a_contract_quoted_inside_an_example_fence_is_not_read():
    text = _plan("  Modify  src/a.py\n", '  A["src/a.py"]\n').replace(
        "## 13.", "- [ ] Add to the plan:\n\n````markdown\n#### Contract\n```\n# file: path/to/module.py\n```\n````\n\n## 13.", 1
    )
    assert coverage.coverage_findings(text) == []


def test_no_section_13_is_not_this_checks_business():
    text = _plan(THREE).split("## 13.")[0]
    assert coverage.coverage_findings(text) == []  # NO_SECTION is check 6's finding


def test_cli_coverage_is_opt_in(tmp_path: Path, capsys: pytest.CaptureFixture[str]):
    p = tmp_path / "x-plan.md"
    p.write_text(_plan(THREE))
    assert lint_main([str(p), "--repo-root", str(tmp_path)]) in (0, 1)
    assert "UNDRAWN_PATH" not in capsys.readouterr().out
    assert lint_main([str(p), "--repo-root", str(tmp_path), "--coverage"]) == 1
    assert capsys.readouterr().out.count(": UNDRAWN_PATH: ") == 3


def test_the_gate_never_computes_coverage():
    assert "UNDRAWN_PATH" not in {f.code for f in lint_plan(SEEDED, ROOT).findings}


# --- AC4 (proxy, labelled as such) and the shipped prose ----------------------------------


def test_check_8_never_names_the_gate():  # AC4 proxy, scoped to check 8 (Ste 2026-09-25)
    text = SKILL.read_text(encoding="utf-8")
    check_8 = text[text.index("8. **Contract paths drawn in §13"): text.index("Parsers for checks")]
    assert not re.search(r"aa-ma-gate|aa_ma[._]gate", check_8)


def test_coverage_module_never_imports_the_gate():
    tree = ast.parse((ROOT / "src/aa_ma/render/coverage.py").read_text(encoding="utf-8"))
    mods = {n.module or "" for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)}
    mods |= {a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names}
    assert not any(m == "aa_ma.gate" or m.endswith(".gate") for m in mods)


def test_skill_appends_check_8_without_renumbering():
    text = SKILL.read_text(encoding="utf-8")
    assert "6. **Architecture View present or validly waived" in text
    assert "7. **Contract block per code milestone" in text
    assert "8. **Contract paths drawn in §13" in text
    assert text.index("7. **Contract block") < text.index("8. **Contract paths drawn")
    assert "--coverage" in text and "UNDRAWN_PATH" in text


def test_plan_command_seeds_section_13_from_the_graph():
    text = PLAN_CMD.read_text(encoding="utf-8")
    seed = text[text.index("### Phase 4:"): text.index("### Phase 4.2:")]
    assert "codemem" in seed and "draw --level L2" in seed and "--scope" in seed
    assert "--direction both" in seed and "--hops 1" in seed
    assert "codemem build" in seed  # the no-index reason is printed, not an empty seed


def test_spec_item_13_names_the_coverage_rule():
    item = next(ln for ln in SPEC.read_text(encoding="utf-8").splitlines() if ln.startswith("13. **Architecture View**"))
    assert "--coverage" in item and "UNDRAWN_PATH" in item


def test_this_plan_passes_its_own_rule():
    plans = sorted(ROOT.glob(".claude/dev/*/diagram-generation/diagram-generation-plan.md"))
    assert plans, "diagram-generation plan not found"
    assert coverage.coverage_findings(plans[0].read_text(encoding="utf-8")) == []


# --- AC5: the seeded fixture ---------------------------------------------------------------


def _git(root: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True)


@pytest.fixture
def seed_repo(tmp_path: Path) -> Path:
    root = tmp_path / "seed"
    files = {
        "src/__init__.py": "",
        "src/app/__init__.py": "",
        "src/app/a.py": "from src.app import b\n\n\ndef run():\n    return b.helper()\n",
        "src/app/b.py": "def helper():\n    return 1\n",
        "src/app/cli.py": "from src.app import a\n\n\ndef main():\n    return a.run()\n",
    }
    for rel, text in files.items():
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        (root / rel).write_text(text)
    _git(root, "init", "-q")
    _git(root, "add", ".")
    _git(root, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "init")
    from codemem.indexer import build_index

    build_index(root, root / ".codemem/index.db", package=".")
    return root


def test_fixture_seed_is_byte_identical_to_the_command(seed_repo: Path, monkeypatch, capsys):  # AC5
    from codemem.cli import main as codemem_main

    monkeypatch.chdir(seed_repo)
    assert codemem_main(["draw", "--level", "L2", "--scope", "src/app/a.py", "--hops", "1", "--direction", "both"]) == 0
    seed = capsys.readouterr().out
    assert seed.count('-->|"@import"|') >= 1
    assert seed in SEEDED.read_text(encoding="utf-8")


def test_seeded_fixture_has_no_phantom_edges_and_every_claim_is_evaluated(seed_repo: Path):  # AC5
    rep = lint_plan(SEEDED, seed_repo)
    assert [f for f in rep.findings if f.code == "PHANTOM_EDGE"] == []
    assert [u for u in rep.unknowns if "@" in u.message] == []  # evaluated, not skipped
    assert coverage.coverage_findings(SEEDED.read_text(encoding="utf-8")) == []


# --- §6.8 follow-ups (fail closed, bounded, prose tied to code) ----------------------------


@pytest.mark.parametrize(
    ("row", "path"),
    [
        ("  Modify  .importlinter", ".importlinter"),
        ("  Modify  Makefile", "Makefile"),
        ("  Modify  docker/Dockerfile", "docker/Dockerfile"),
        ("  Modify  `src/x.py`", "src/x.py"),
        ("  Modify  src/x.py:12-40", "src/x.py"),
        ("  Modify  src/x.py (append)", "src/x.py"),
        ("  - Modify src/x.py", "src/x.py"),
        ("  | Modify | src/x.py |", "src/x.py"),
        ("  Create: src/x.py", "src/x.py"),
    ],
)
def test_every_contract_token_is_a_path(row, path):  # fail closed: a dropped path passes silently
    assert _codes(_plan(row + "\n")) == [path]


def test_brace_expansion_is_bounded():
    wide = "# file: src/" + "{a,b}" * 25 + ".py\n"  # 2**25 paths if expanded
    deep = "# file: src/" + "{" * 3000 + "a" + "}" * 3000 + ".py\n"  # recursion depth 3000
    start = time.perf_counter()
    assert len(coverage.coverage_findings(_plan(wide))) == 1
    assert len(coverage.coverage_findings(_plan(deep))) == 1
    assert time.perf_counter() - start < 1.0


def test_small_brace_lists_still_expand():
    assert _codes(_plan("  Modify  src/{a,b}/{c,d}.py\n")) == ["src/a/c.py", "src/a/d.py", "src/b/c.py", "src/b/d.py"]


def test_a_lone_slash_in_a_label_draws_nothing():
    text = _plan("# file: /etc/x.conf\n", '  S["a / b"]\n')
    assert _codes(text) == ["/etc/x.conf"]


def test_cli_crash_is_unknown_not_findings(tmp_path, monkeypatch, capsys):
    p = tmp_path / "x-plan.md"
    p.write_text(_plan(THREE))

    def boom(_):
        raise RecursionError("hostile plan")

    monkeypatch.setattr("aa_ma.render.cli.coverage_findings", boom)
    assert lint_main([str(p), "--repo-root", str(tmp_path), "--coverage"]) == 2
    assert "UNKNOWN: coverage could not run" in capsys.readouterr().out


def test_skill_names_every_exemption_the_code_applies():
    text = SKILL.read_text(encoding="utf-8")
    check_8 = text[text.index("8. **Contract paths drawn in §13"): text.index("Parsers for checks")]
    for name in (*coverage.EXEMPT_DIRS, *sorted(coverage.ROOT_DOCS), *sorted(coverage.MANIFESTS), "*.lock"):
        assert name.removesuffix(".md") in check_8, name


def test_cutover_prose_matches_the_constant():
    assert coverage.COVERAGE_CUTOVER in SKILL.read_text(encoding="utf-8")
    assert coverage.COVERAGE_CUTOVER in SPEC.read_text(encoding="utf-8")
    before = (date.fromisoformat(coverage.COVERAGE_CUTOVER) - timedelta(days=1)).isoformat()
    assert coverage.coverage_findings(_plan(THREE, created=before)) == []
    assert coverage.coverage_findings(_plan(THREE, created=coverage.COVERAGE_CUTOVER))


def test_every_check_list_names_check_8():
    rule = (ROOT / "claude-code/rules/aa-ma.md").read_text(encoding="utf-8")
    assert "#8" in rule.split("Grandfathering (v0.12.0", 1)[1].split("\n\n", 1)[0]
    routing = next(ln for ln in SKILL.read_text(encoding="utf-8").splitlines() if "Engineering Standards Auditor |" in ln)
    assert "check #8" in routing


# --- the shipped fences, executed ----------------------------------------------------------------


def _fence(md: Path, anchor: str) -> str:
    """The first ```bash fence after ``anchor``, dedented, up to its own closer line."""
    lines = md.read_text(encoding="utf-8")[md.read_text(encoding="utf-8").index(anchor):].splitlines()
    start = next(i for i, ln in enumerate(lines) if ln.strip() == "```bash")
    end = next(i for i in range(start + 1, len(lines)) if lines[i].strip() == "```")
    return textwrap.dedent("\n".join(lines[start + 1 : end])) + "\n"


@pytest.fixture
def home(tmp_path: Path) -> Path:
    """A ~/.claude that symlinks this checkout, as scripts/install.sh would."""
    h = tmp_path / "home"
    for rel in ("commands/aa-ma-plan.md", "skills/plan-verification/SKILL.md"):
        (h / ".claude" / rel).parent.mkdir(parents=True, exist_ok=True)
        (h / ".claude" / rel).symlink_to(ROOT / "claude-code" / rel)
    return h


def _stub_uv(tmp_path: Path, rc: int) -> Path:
    bin_ = tmp_path / "bin"
    bin_.mkdir(exist_ok=True)
    (bin_ / "uv").write_text(f'#!/bin/sh\nfor a in "$@"; do printf "%s\\n" "$a"; done > "{tmp_path}/uv-args"\nexit {rc}\n')
    (bin_ / "uv").chmod(0o755)
    return bin_


def _run(script: str, home: Path, bin_: Path, cwd: Path) -> str:
    env = {"HOME": str(home), "PATH": f"{bin_}:/usr/bin:/bin"}
    return subprocess.run(["bash", "-c", script], cwd=cwd, env=env, capture_output=True, text=True).stdout


def test_seed_fence_skips_the_cut_with_no_existing_paths(tmp_path, home):
    bin_ = _stub_uv(tmp_path, 0)
    script = _fence(PLAN_CMD, "**Step 4.2b").replace("<one existing path per line>\n", "")
    out = _run(script, home, bin_, tmp_path)
    assert "seed skipped" in out
    assert not (tmp_path / "uv-args").exists()


def test_seed_fence_passes_each_path_as_one_scope(tmp_path, home):
    bin_ = _stub_uv(tmp_path, 0)
    script = _fence(PLAN_CMD, "**Step 4.2b").replace("<one existing path per line>", "src/a b.py\nsrc/$(touch pwned).py\nsrc/*.py")
    _run(script, home, bin_, tmp_path)
    args = (tmp_path / "uv-args").read_text().splitlines()
    assert [args[i + 1] for i, a in enumerate(args) if a == "--scope"] == ["src/a b.py", "src/$(touch pwned).py", "src/*.py"]
    assert not (tmp_path / "pwned").exists()


def test_check_8_fence_never_reads_a_failed_run_as_clean(tmp_path, home):
    bin_ = _stub_uv(tmp_path, 127)
    script = _fence(SKILL, "8. **Contract paths drawn in §13").replace("<plan.md>", "p.md").replace("<project-root>", ".")
    assert "CRITICAL: check 8 could not run" in _run(script, home, bin_, tmp_path)
