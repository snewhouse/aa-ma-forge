"""The advisory skill-eval suite (`evals/`, ADR-0021) has the agreed shape.

At least CASES_PER_SKILL cases for each skill in EVAL_SKILLS (code-conventions-impact M4.5). Each case loads the forge
plugin, starts from a scaffolded git repo with no remote, grants only read-only tools,
and carries a grader that proves the skill ran: a `tool_used: Skill` grader for a
model-invoked skill. A user-invoked skill (`disable-model-invocation: true`) is reached
by its slash name, which is expanded before the trace starts and is not a tool call, so
its cases grade the skill's behaviour instead.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from tests.skills._helpers import split_frontmatter
from tests.test_frontmatter_at_top import DYNAMIC_EXEC_RE

REPO_ROOT = Path(__file__).resolve().parents[1]
EVALS = REPO_ROOT / "evals"
SKILLS = REPO_ROOT / "claude-code" / "skills"
EVAL_SKILLS = {
    "execute-aa-ma-milestone",
    "execute-aa-ma-step",
    "execute-aa-ma-full",
    "aa-ma-plan",
    "plan-verification",
    "impact-analysis",
    "logging-and-comments",
    "writing-for-agents",
}
CASES_PER_SKILL = 3  # minimum per skill (ADR-0021 "at least 3")
# One turn budget for every case: Skill load + up to ~10 reads/greps + the answer.
MAX_TURNS = 12
READ_ONLY_TOOLS = {"Read", "Glob", "Grep", "Skill"}


def _cases() -> list[Path]:
    return sorted(EVALS.glob("*/*/case.yaml"))


def _frontmatter(path: Path) -> dict:
    return split_frontmatter(path.read_text(encoding="utf-8"))[1]


def _user_invoked(skill: str) -> bool:
    return bool(
        _frontmatter(SKILLS / skill / "SKILL.md").get("disable-model-invocation")
    )


def test_each_eval_skill_has_its_minimum_cases() -> None:
    counts: dict[str, int] = {}
    for case in _cases():
        counts[case.parent.parent.name] = counts.get(case.parent.parent.name, 0) + 1
    assert set(counts) == EVAL_SKILLS
    assert all(n >= CASES_PER_SKILL for n in counts.values()), counts


def test_no_loaded_skill_runs_dynamic_exec() -> None:
    """Evals load every forge skill; a `!`cmd`` line would run before any tool gate applies."""
    hits = [
        p.parent.name
        for p in sorted(SKILLS.glob("*/SKILL.md"))
        if DYNAMIC_EXEC_RE.search(p.read_text(encoding="utf-8"))
    ]
    assert hits == []


@pytest.mark.parametrize(
    "case", _cases(), ids=lambda p: f"{p.parent.parent.name}/{p.parent.name}"
)
def test_case_shape(case: Path) -> None:
    spec = yaml.safe_load(case.read_text(encoding="utf-8"))
    skill = case.parent.parent.name
    assert spec["schema_version"] == "1.1"
    assert spec["name"] == f"{skill}-{case.parent.name}"
    assert (case.parent / spec["plugins"][0]).resolve() == REPO_ROOT / "claude-code"
    ex = spec["execution"]
    assert ex["max_turns"] == MAX_TURNS
    assert set(ex["allowed_tools"]) <= READ_ONLY_TOOLS, "grant read-only tools only"
    assert ex["prompt"].strip()
    scaffold = case.parent / spec["context"]["scaffold_script"]
    assert scaffold.is_symlink() and scaffold.resolve().parent == EVALS / "_lib"

    graders = sorted((case.parent / "graders").glob("*.md"))
    assert len(graders) >= 2, "one grader on the steps, one on the result"
    kinds = [_frontmatter(g) for g in graders]
    if _user_invoked(skill):
        assert ex["prompt"].lstrip().startswith(f"/claude-code:{skill}")
        assert not any(k.get("tool") == "Skill" for k in kinds)
    else:
        skill_graders = [
            k
            for k in kinds
            if k.get("type") == "tool_used" and k.get("tool") == "Skill"
        ]
        assert skill_graders and skill in skill_graders[0]["input_match"]
