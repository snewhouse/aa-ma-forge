"""Every shipped skill, command and agent must open with its YAML frontmatter on line 1.

Claude Code only recognises frontmatter that starts at the top of the file. A line-1 HTML
comment silently dropped `name`/`description` (and `allowed-tools`) from six skills, which
then showed the comment as their description. Fork provenance now lives on line 2 as a
YAML `#` comment (ADR-0011 amendment, 2026-10-05). Each skill's `name` must also equal its
directory, since `name` sets the `/` command and callers use the directory slug.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
PLUGIN = REPO_ROOT / "claude-code"

# (glob, keys that must be non-empty strings). The forge's commands became skills
# (ADR-0020), so commands/ is no longer a surface.
SURFACES = {
    "skills/*/SKILL.md": ("name", "description"),
    "agents/*.md": ("name", "description"),
}

CASES = [
    pytest.param(path, keys, id=str(path.relative_to(PLUGIN)))
    for pattern, keys in SURFACES.items()
    for path in sorted(PLUGIN.glob(pattern))
]


def test_surfaces_are_not_empty() -> None:
    """Guard the guard: a moved directory must not turn this file into zero tests."""
    for pattern in SURFACES:
        assert list(PLUGIN.glob(pattern)), f"no files match claude-code/{pattern}"


def _frontmatter(path: Path) -> dict:
    lines = path.read_text(encoding="utf-8").split("\n")
    assert lines[0] == "---", f"line 1 must be '---', got: {lines[0][:80]!r}"
    assert "---" in lines[1:], "unterminated frontmatter: no closing '---'"
    close = lines.index("---", 1)
    fm = yaml.safe_load("\n".join(lines[1:close]))
    assert isinstance(fm, dict), f"frontmatter is not a mapping: {type(fm).__name__}"
    return fm


@pytest.mark.parametrize(("path", "keys"), CASES)
def test_frontmatter_starts_on_line_1(path: Path, keys: tuple[str, ...]) -> None:
    fm = _frontmatter(path)
    for key in keys:
        value = fm.get(key)
        assert isinstance(value, str) and value.strip(), f"missing or empty {key!r}"


@pytest.mark.parametrize(
    "path",
    [
        pytest.param(p, id=p.parent.name)
        for p in sorted(PLUGIN.glob("skills/*/SKILL.md"))
    ],
)
def test_skill_name_matches_directory(path: Path) -> None:
    """`name` sets the skill's `/` command; callers invoke skills by their directory slug."""
    name = _frontmatter(path).get("name")
    assert name == path.parent.name, (
        f"name {name!r} must match the directory {path.parent.name!r}"
    )


# --- Skill frontmatter schema (M4.1, map Ticket 15) ---------------------------------
#
# Sources, fetched 2026-10-09:
# - Claude Code skills docs, "Frontmatter reference"
#   (https://code.claude.com/docs/en/skills#frontmatter-reference): the field table below.
#   "Claude Code ignores a field it doesn't recognize without reporting an error", so an
#   unknown key is a silent no-op — this test is what makes it loud.
# - Agent Skills spec (https://agentskills.io/specification): `name` 1-64 chars of
#   [a-z0-9-], no leading/trailing/double hyphen; `description` 1-1024 chars.
# - The skills docs truncate `description` + `when_to_use` at 1,536 characters in the
#   skill listing. `<` is refused in descriptions because the listing is injected into
#   the system prompt, where a tag-like string reads as markup.

SKILL_KEYS = frozenset(
    {
        "name",
        "description",
        "when_to_use",
        "argument-hint",
        "arguments",
        "disable-model-invocation",
        "user-invocable",
        "allowed-tools",
        "disallowed-tools",
        "model",
        "effort",
        "context",
        "agent",
        "background",
        "hooks",
        "paths",
        "shell",
        "metadata",
        "license",
        "compatibility",
    }
)
NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
NAME_MAX = 64  # Agent Skills spec
DESCRIPTION_MAX = 1024  # Agent Skills spec
LISTING_MAX = 1536  # Claude Code: description + when_to_use, truncated beyond this
SECOND_PERSON_RE = re.compile(r"\b(you|your)\b", re.IGNORECASE)
QUOTED_RE = re.compile(r"\"[^\"]*\"|'[^']*'|“[^”]*”")
DYNAMIC_EXEC_RE = re.compile(r"(^|\s)!`|^```!", re.MULTILINE)
UNSCOPED_TOOLS = frozenset({"Bash", "Write", "Edit"})

# Skills that pre-approve an unscoped Bash/Write/Edit, and why. `allowed-tools` grants
# the tool without a prompt for the invoking turn, so an unscoped grant is any command
# or any file; each entry must say why that breadth is needed.
UNSCOPED_TOOLS_ALLOWLIST = {
    "assess-codebase": (
        "runs semgrep, gitleaks, osv-scanner, jscpd, lizard, pip-audit and codemem with "
        "tier-dependent argv, and writes its report tree under "
        ".claude/reports/assess-codebase/ (secret-gated before write)"
    ),
    "retro": (
        "runs git log/shortlog/diff over computed ranges and `mkdir -p ~/.gstack/sessions`, "
        "and writes its snapshot under .context/retros/"
    ),
}


def _skill_parts(path: Path) -> tuple[dict, str]:
    fm = _frontmatter(path)
    lines = path.read_text(encoding="utf-8").split("\n")
    return fm, "\n".join(lines[lines.index("---", 1) + 1 :])


def _tool_names(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(v).strip() for v in value]
    # "Bash(git:*) Read, Write": split on commas/space outside parentheses.
    return [t for t in re.split(r"[,\s]+(?![^()]*\))", str(value or "")) if t]


def skill_schema_errors(
    name_dir: str, fm: dict, body: str, *, forked: bool = False
) -> list[str]:
    """Return every schema violation in one skill's frontmatter and body."""
    errors = [f"unknown key {k!r}" for k in sorted(set(fm) - SKILL_KEYS)]
    name = fm.get("name")
    if not (isinstance(name, str) and len(name) <= NAME_MAX and NAME_RE.match(name)):
        errors.append(f"name {name!r} must be 1-{NAME_MAX} chars of [a-z0-9-]")
    desc = fm.get("description")
    if not isinstance(desc, str) or not desc.strip():
        errors.append("description missing or empty")
        desc = ""
    if len(desc) > DESCRIPTION_MAX:
        errors.append(f"description is {len(desc)} chars (max {DESCRIPTION_MAX})")
    if "<" in desc:
        errors.append("description contains '<'")
    when = fm.get("when_to_use") or ""
    if not isinstance(when, str):
        errors.append("when_to_use must be a string")
        when = ""
    if len(desc) + len(when) > LISTING_MAX:
        errors.append(
            f"description + when_to_use is {len(desc) + len(when)} chars (max {LISTING_MAX})"
        )
    for field, text in (("description", desc), ("when_to_use", when)):
        hit = SECOND_PERSON_RE.search(QUOTED_RE.sub("", text))
        if hit:
            errors.append(
                f"{field} uses second person {hit.group(0)!r}; write in third person"
            )
    if "context" in fm and fm["context"] != "fork":
        errors.append(f"context must be 'fork' when present, got {fm['context']!r}")
    if "metadata" in fm and not isinstance(fm["metadata"], dict):
        errors.append("metadata must be a map")
    unscoped = sorted(UNSCOPED_TOOLS & set(_tool_names(fm.get("allowed-tools"))))
    if unscoped and name_dir not in UNSCOPED_TOOLS_ALLOWLIST:
        errors.append(
            f"allowed-tools pre-approves unscoped {unscoped} with no allowlist why"
        )
    if forked and DYNAMIC_EXEC_RE.search(body):
        errors.append("forked body contains a !`…` dynamic-exec line")
    return errors


FORKED = set(json.loads((PLUGIN / "skills" / "FORKS.json").read_text(encoding="utf-8")))


@pytest.mark.parametrize(
    "path",
    [
        pytest.param(p, id=p.parent.name)
        for p in sorted(PLUGIN.glob("skills/*/SKILL.md"))
    ],
)
def test_skill_frontmatter_schema(path: Path) -> None:
    fm, body = _skill_parts(path)
    errors = skill_schema_errors(
        path.parent.name, fm, body, forked=path.parent.name in FORKED
    )
    assert not errors, "\n".join(errors)


def test_allowlisted_skills_still_need_their_entry() -> None:
    """An allowlist entry whose skill no longer grants an unscoped tool is stale."""
    for skill in UNSCOPED_TOOLS_ALLOWLIST:
        fm, _ = _skill_parts(PLUGIN / "skills" / skill / "SKILL.md")
        assert UNSCOPED_TOOLS & set(_tool_names(fm.get("allowed-tools"))), skill


GOOD = {
    "name": "probe-skill",
    "description": "Checks a thing. Use when asked to check.",
}


@pytest.mark.parametrize(
    ("extra", "needle"),
    [
        ({"triggers": ["x"]}, "unknown key 'triggers'"),
        ({"version": "1.0"}, "unknown key 'version'"),
        ({"name": "Probe_Skill"}, "name"),
        ({"name": "x" * 65}, "name"),
        ({"description": "d" * 1025}, "max 1024"),
        ({"description": "Renders <b> tags."}, "'<'"),
        ({"when_to_use": "w" * 1500}, "max 1536"),
        ({"description": "Helps when your plan needs review."}, "second person"),
        ({"context": "AI-assisted development"}, "context must be 'fork'"),
        ({"metadata": "1.0"}, "metadata must be a map"),
        ({"allowed-tools": "Read Bash"}, "unscoped ['Bash']"),
        ({"allowed-tools": ["Read", "Write"]}, "unscoped ['Write']"),
    ],
)
def test_negative_controls_fail(extra: dict, needle: str) -> None:
    errors = skill_schema_errors("probe-skill", {**GOOD, **extra}, "")
    assert any(needle in e for e in errors), errors


def test_positive_controls_pass() -> None:
    fm = {
        **GOOD,
        "description": 'Grills a plan. Use when the user says "grill your plan".',
        "metadata": {"version": "1.0"},
        "allowed-tools": "Read Bash(git:*) Write(.claude/reports/**)",
        "context": "fork",
    }
    assert skill_schema_errors("probe-skill", fm, "") == []


def test_dynamic_exec_is_refused_only_in_forked_bodies() -> None:
    body = "Context:\n!`git status`\n"
    assert skill_schema_errors("probe-skill", GOOD, body) == []
    assert any(
        "dynamic-exec" in e
        for e in skill_schema_errors("probe-skill", GOOD, body, forked=True)
    )
