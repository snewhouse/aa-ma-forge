"""codemem.draw.plugin_surface — the commands->skills->agents->hooks graph (diagram-generation M4).

The golden is ONE regenerable snapshot of this repo's surface; no count is inlined
here. After an intended change to ``claude-code/`` regenerate it with::

    uv run python tests/codemem/test_plugin_surface.py

and review the diff — it is the surface change.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from codemem.draw.cut import Level, node_id
from codemem.draw.plugin_surface import RefClass, as_json, extract
from codemem.draw.surface_allowlist import EXTERNAL

REPO = Path(__file__).resolve().parents[2]
GOLDEN = REPO / "tests/golden/plugin-surface.json"


@pytest.fixture(scope="module")
def surface():
    return extract(REPO)


# ---------------------------------------------------------------------
# The real repo (AC1-AC4)
# ---------------------------------------------------------------------

def test_matches_golden(surface) -> None:
    assert as_json(surface) == json.loads(GOLDEN.read_text()), (
        "plugin surface drifted from tests/golden/plugin-surface.json — "
        "regenerate: uv run python tests/codemem/test_plugin_surface.py, then review the diff"
    )


def test_every_drawn_edge_resolves_on_disk_or_is_declared_external(surface) -> None:
    for e in surface.edges:
        if e.ref_class is RefClass.ON_DISK:
            kind, name = e.dst.split(":", 1)
            path = {
                "skill": REPO / "claude-code/skills" / name,
                "command": REPO / "claude-code/commands" / f"{name}.md",
                "agent": REPO / "claude-code/agents" / f"{name}.md",
                "hook": next((REPO / "claude-code/hooks").rglob(name), None),
            }[kind]
            assert path is not None and path.exists(), e
    drawn = {(a, b) for a, b, _ in surface.cut.edges}
    for e in surface.edges:
        pair = (node_id(e.src, Level.L2), node_id(e.dst, Level.L2))
        assert (pair in drawn) == (e.ref_class is not RefClass.DANGLING), e


def test_every_skill_target_has_exactly_one_class_and_dangling_is_named(surface) -> None:
    classes: dict[str, set[RefClass]] = {}
    for e in surface.edges:
        if e.kind == "skill":
            classes.setdefault(e.dst, set()).add(e.ref_class)
    assert all(len(c) == 1 for c in classes.values()), classes
    dangling = {d.split(":", 1)[1] for d, c in classes.items() if c == {RefClass.DANGLING}}
    assert dangling == {"aa-ma-plan", "codebase-deep-dive", "haiku-eval", "index"}
    # The target Ticket 4's regex could not see (':' in a plugin-namespaced name).
    assert classes["skill:feature-dev:feature-dev"] == {RefClass.DECLARED_EXTERNAL}


def test_orphans_are_the_named_set_and_no_errors(surface) -> None:
    # Orphans are `kind:stem` (a stem can be both a command and a skill); AC4 names bare stems.
    assert len(surface.orphans) == len(set(surface.orphans))
    assert {o.split(":", 1)[1] for o in surface.orphans} == {
        "aa-ma-search", "sole-dev-merge", "aa-ma-execution", "complexity-router",
        "debugging-strategies", "write-a-skill", "aa-ma-session-end-dirty.sh",
    }
    assert surface.errors == []


def test_codemem_subsurface_and_docs_are_out_of_the_graph(surface) -> None:
    assert not any("codemem" in n for e in surface.edges for n in (e.src, e.dst))


def test_every_allowlisted_external_is_still_referenced(surface) -> None:
    """The allowlist must not rot silently: an entry nobody references is stale."""
    used = {e.dst for e in surface.edges if e.ref_class is RefClass.DECLARED_EXTERNAL}
    stale = {f"{k}:{n}" for k, names in EXTERNAL.items() for n in names} - used
    assert stale == set(), "drop these from surface_allowlist.EXTERNAL"


def test_orphan_nodes_are_drawn(surface) -> None:
    drawn = set(surface.cut.nodes.values())
    assert set(surface.orphans) <= drawn


# ---------------------------------------------------------------------
# Fixture tree — behaviour, not counts (AC5)
# ---------------------------------------------------------------------

INSTALL = '''AA_MA_HOOKS=(
    "SessionStart||h-start.sh|5|"
    "PreToolUse|Bash|h-start.sh|5|"
)
'''


def _tree(root: Path, files: dict[str, str]) -> Path:
    for rel, text in {"scripts/install.sh": INSTALL, "claude-code/hooks/h-start.sh": "", **files}.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
    return root


BASE = {
    "claude-code/skills/alpha/SKILL.md": "<!-- fork provenance -->\n---\nname: Not Alpha\n---\n",
    "claude-code/skills/gamma/SKILL.md": "Use Skill(alpha) here.\n",
    "claude-code/commands/run.md": "Skill(alpha) then Skill(alpha) again; Skill(gamma).\n",
}


def _classes(s, cls: RefClass) -> list:
    return [e for e in s.edges if e.ref_class is cls]


def test_rename_skill_moves_exactly_its_references_to_dangling(tmp_path: Path) -> None:
    before = extract(_tree(tmp_path / "a", BASE))
    refs_to_alpha = sum(e.dst == "skill:alpha" for e in before.edges)
    assert refs_to_alpha == 2  # run.md's two mentions dedupe to one edge; gamma adds one

    renamed = dict(BASE)
    renamed["claude-code/skills/beta/SKILL.md"] = renamed.pop("claude-code/skills/alpha/SKILL.md")
    after = extract(_tree(tmp_path / "b", renamed))

    on_disk = len(_classes(before, RefClass.ON_DISK)) - len(_classes(after, RefClass.ON_DISK))
    assert on_disk == refs_to_alpha
    assert len(_classes(after, RefClass.DANGLING)) == refs_to_alpha
    assert not any(e.dst == "skill:beta" for e in after.edges)
    assert "skill:beta" in after.orphans


def test_rename_skill_and_its_references_keeps_the_graph(tmp_path: Path) -> None:
    before = extract(_tree(tmp_path / "a", BASE))
    renamed = {k.replace("alpha", "beta"): v.replace("alpha", "beta") for k, v in BASE.items()}
    after = extract(_tree(tmp_path / "b", renamed))
    assert len(after.edges) == len(before.edges)
    assert _classes(after, RefClass.DANGLING) == []


def test_node_identity_is_the_dir_stem_not_frontmatter(tmp_path: Path) -> None:
    s = extract(_tree(tmp_path, BASE))
    assert "skill:alpha" in {e.dst for e in s.edges}
    assert not any("Not Alpha" in n for n in s.cut.nodes.values())


def test_command_mentions_filter_on_disk_expand_globs_and_drop_self(tmp_path: Path) -> None:
    s = extract(_tree(tmp_path, {
        "claude-code/commands/go-one.md": "/go-one is me. See /goal, /tmp/go-two.log. Run /go-two.\n",
        "claude-code/commands/go-two.md": "",
        "claude-code/commands/go-three.md": "Any /go-* command.\n",
    }))
    got = {(e.src, e.dst) for e in s.edges}
    assert got == {
        ("command:go-one", "command:go-two"),
        ("command:go-three", "command:go-one"),
        ("command:go-three", "command:go-two"),
    }


def test_agents_hooks_and_externals_classify(tmp_path: Path) -> None:
    s = extract(_tree(tmp_path, {
        "claude-code/agents/checker.md": "",
        "claude-code/hooks/lib/aa-ma-helper.sh": "",
        "claude-code/hooks/plan-lint.sh": "",
        "claude-code/skills/s/SKILL.md": (
            'subagent_type: "checker"\nsubagent_type=Explore\nsubagent_type: ghost-agent\n'
            "source lib/aa-ma-helper.sh; aa-ma-missing.sh; test-aa-ma-fake.sh; plan-lint.sh\n"
            "Skill(browse) Skill(not-a-real-skill)\n"
        ),
    }))
    got = {(e.dst, e.kind, e.ref_class) for e in s.edges}
    assert got == {
        ("agent:checker", "agent", RefClass.ON_DISK),
        ("agent:Explore", "agent", RefClass.DECLARED_EXTERNAL),
        ("agent:ghost-agent", "agent", RefClass.DANGLING),
        ("hook:aa-ma-helper.sh", "hook", RefClass.ON_DISK),
        ("hook:aa-ma-missing.sh", "hook", RefClass.DANGLING),
        ("hook:plan-lint.sh", "hook", RefClass.ON_DISK),  # outside the naming prefix
        ("skill:browse", "skill", RefClass.DECLARED_EXTERNAL),
        ("skill:not-a-real-skill", "skill", RefClass.DANGLING),
    }


def test_hook_events_come_from_install_sh(tmp_path: Path) -> None:
    s = extract(_tree(tmp_path, {}))
    assert s.hook_events == {"h-start.sh": ["PreToolUse:Bash", "SessionStart"]}
    assert s.errors == []


def test_a_wired_hook_missing_on_disk_is_an_error(tmp_path: Path) -> None:
    root = _tree(tmp_path, {})
    (root / "claude-code/hooks/h-start.sh").unlink()
    assert any("h-start.sh" in e for e in extract(root).errors)


def test_missing_install_sh_is_an_error_not_silence(tmp_path: Path) -> None:
    root = _tree(tmp_path, {})
    (root / "scripts/install.sh").unlink()
    assert any("install.sh" in e for e in extract(root).errors)


def test_one_rule_decides_node_identity(tmp_path: Path) -> None:
    """A file that is not a node (hooks/README.md, a nested command) is never an edge source."""
    s = extract(_tree(tmp_path, {
        "claude-code/skills/alpha/SKILL.md": "",
        "claude-code/hooks/README.md": "Skill(alpha)\n",
        "claude-code/commands/sub/nested.md": "Skill(alpha)\n",
    }))
    assert s.edges == []
    assert "skill:alpha" in s.orphans


def test_symlinked_files_are_not_followed(tmp_path: Path) -> None:
    outside = tmp_path / "outside.md"
    outside.write_text("Skill(alpha)\n")
    root = _tree(tmp_path / "r", {"claude-code/skills/alpha/SKILL.md": ""})
    (root / "claude-code/skills/alpha/leak.md").symlink_to(outside)
    (root / "claude-code/commands").mkdir(parents=True, exist_ok=True)
    (root / "claude-code/commands/link.md").symlink_to(outside)
    assert extract(root).edges == []


def test_hook_regex_is_linear_on_hostile_input(tmp_path: Path) -> None:
    import time
    s0 = time.perf_counter()
    extract(_tree(tmp_path, {"claude-code/skills/s/SKILL.md": "aa-ma-" * 20000 + "\n"}))
    assert time.perf_counter() - s0 < 1.0


def test_install_table_matchers_and_unparsed_rows(tmp_path: Path) -> None:
    root = _tree(tmp_path, {"scripts/install.sh": """AA_MA_HOOKS=(
    "PreToolUse|Edit|Write|h-start.sh|5|"
    "PreToolUse|mcp__.*|h-start.sh|5|"
    "this row is not a hook row"
)
"""})
    s = extract(root)
    assert s.hook_events == {"h-start.sh": ["PreToolUse:Edit|Write", "PreToolUse:mcp__.*"]}
    assert len(s.errors) == 1 and "unparsed" in s.errors[0]


def test_non_utf8_install_sh_does_not_raise(tmp_path: Path) -> None:
    root = _tree(tmp_path, {})
    (root / "scripts/install.sh").write_bytes(INSTALL.encode() + b"# \xff\xfe\n")
    assert extract(root).hook_events == {"h-start.sh": ["PreToolUse:Bash", "SessionStart"]}


def test_missing_plugin_tree_is_an_error_not_an_empty_graph(tmp_path: Path) -> None:
    (tmp_path / "scripts").mkdir()
    (tmp_path / "scripts/install.sh").write_text(INSTALL)
    assert "claude-code/: not found" in extract(tmp_path).errors


if __name__ == "__main__":
    GOLDEN.write_text(json.dumps(as_json(extract(REPO)), indent=1, sort_keys=True) + "\n")
