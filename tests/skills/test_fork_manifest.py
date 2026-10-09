"""Fork manifest tests — `claude-code/skills/FORKS.json` is the SSoT for every fork.

Milestone 1 Contract (mattpocock-trio-adoption). The classifier tests build
`fetched` dicts by hand: no plugin cache, no network, so they run in CI.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from aa_ma.forks import ForkEntry, _cli, classify_fork, load_manifest

from ._helpers import FORKS_MANIFEST as MANIFEST, SKILLS_DIR, assert_skill_frontmatter  # pyright: ignore[reportMissingImports]

# SKILL.md carries provenance as a YAML comment on line 2, inside the frontmatter
# (ADR-0011 amendment, 2026-10-05); companion files (LOGIC.md, ADR-FORMAT.md, …) have no
# frontmatter and keep it as an HTML comment on line 1.
YAML_PREFIXES = ("# Forked from ", "# Derived from ")
HTML_PREFIXES = ("<!-- Forked from ", "<!-- Derived from ")


def _provenance_region(text: str) -> list[str]:
    """Lines where provenance could sit: the `#` run after a line-1 `---`, else line 1 itself."""
    lines = text.split("\n")
    if lines[0] != "---":
        return lines[:1]
    region: list[str] = []
    for line in lines[1:]:
        if not line.startswith("#"):
            break
        region.append(line)
    return region


def _fork_dirs() -> set[str]:
    """Skill dirs whose SKILL.md carries a Forked/Derived provenance comment, wherever it sits.

    Scans the whole provenance region (not just line 2) so a fork placed anywhere — even
    the legacy line-1 form — is still checked against the manifest.
    """
    out: set[str] = set()
    for skill_md in SKILLS_DIR.glob("*/SKILL.md"):
        region = _provenance_region(skill_md.read_text(encoding="utf-8"))
        if any(line.startswith(YAML_PREFIXES + HTML_PREFIXES) for line in region):
            out.add(skill_md.parent.name)
    return out


def _local_md5(path: Path) -> str:
    """md5 of the file minus its provenance line — the manifest `files.<f>` recipe.

    Exactly one valid place per file kind: line 2 (YAML `#`) of SKILL.md, line 1 (HTML
    comment) of companion files. Dropping it yields the bytes the original `tail -n +2`
    recipe hashed, so FORKS.json is unchanged — and a SKILL.md that slips back to the
    line-1 form fails here as well as in tests/test_frontmatter_at_top.py.
    """
    idx, prefixes = (
        (1, YAML_PREFIXES) if path.name == "SKILL.md" else (0, HTML_PREFIXES)
    )
    lines = path.read_bytes().split(b"\n")
    assert len(lines) > idx and lines[idx].decode("utf-8").startswith(prefixes), (
        f"{path}: line {idx + 1} must be the provenance comment ({prefixes[0].strip()} …)"
    )
    body = b"\n".join(lines[:idx] + lines[idx + 1 :])
    return hashlib.md5(body, usedforsecurity=False).hexdigest()


def test_every_fork_dir_is_in_manifest() -> None:
    manifest = load_manifest(MANIFEST)
    missing = sorted(_fork_dirs() - manifest.keys())
    assert not missing, "MISSING_IN_MANIFEST: " + ", ".join(missing)


def test_manifest_entries_exist_on_disk() -> None:
    manifest = load_manifest(MANIFEST)
    for name, entry in manifest.items():
        assert (SKILLS_DIR / name).is_dir(), f"MISSING_ON_DISK: {name}"
        for fname in entry.files:
            assert (SKILLS_DIR / name / fname).is_file(), (
                f"MISSING_ON_DISK: {name}/{fname}"
            )


def test_local_md5_matches_manifest() -> None:
    """Hard fail: a local edit to a forked file without a manifest update."""
    manifest = load_manifest(MANIFEST)
    mismatches = [
        f"{name}/{fname}"
        for name, entry in manifest.items()
        for fname, md5 in entry.files.items()
        if _local_md5(SKILLS_DIR / name / fname) != md5
    ]
    assert not mismatches, "MD5_MISMATCH: " + ", ".join(mismatches)


def _entry(**upstream_md5: str | None) -> ForkEntry:
    return ForkEntry(
        name="x",
        upstream="skills/engineering/x",
        upstream_repo="mattpocock/skills",
        licence="MIT",
        upstream_sha="c55ee46073ed923f86ce59a5eb3b6d895095d1b7",
        forked_at="2026-05-10",
        adr="docs/adr/0000-x.md",
        state="current",
        files={k: "local" for k in upstream_md5},
        upstream_md5=upstream_md5,
    )


def test_classify_fork_same_drift_orphan() -> None:
    entry = _entry(**{"SKILL.md": "aaa", "LOGIC.md": "bbb"})
    assert classify_fork(entry, {"SKILL.md": "aaa", "LOGIC.md": "bbb"}) == "SAME"
    assert classify_fork(entry, {"SKILL.md": "aaa", "LOGIC.md": "zzz"}) == "DRIFT"
    assert classify_fork(entry, {"SKILL.md": None, "LOGIC.md": "zzz"}) == "ORPHAN"
    # A key missing from `fetched` counts as None → ORPHAN.
    assert classify_fork(entry, {"SKILL.md": "aaa"}) == "ORPHAN"
    # expected None (unknown upstream) → nothing to compare → SAME.
    assert (
        classify_fork(_entry(**{"SKILL.md": None}), {"SKILL.md": "anything"}) == "SAME"
    )


def test_load_manifest_names_missing_key(tmp_path: Path) -> None:
    bad = tmp_path / "FORKS.json"
    bad.write_text(json.dumps({"x": {"upstream": "skills/x"}}), encoding="utf-8")
    with pytest.raises(ValueError, match="upstream_sha"):
        load_manifest(bad)


def test_helper_resolves_upstream_from_manifest() -> None:
    """Step 1.3: `expected_upstream_path=None` derives the path from FORKS.json."""
    assert_skill_frontmatter("prototype", expected_upstream_path=None)


def test_cli_files_lists_manifest_rows(capsys: pytest.CaptureFixture[str]) -> None:
    assert _cli(["files", "--manifest", str(MANIFEST)]) == 0
    rows = [line.split("\t") for line in capsys.readouterr().out.splitlines()]
    assert [
        "prototype",
        "mattpocock/skills",
        "skills/engineering/prototype",
        "SKILL.md",
    ] in rows
    assert [
        "secrets-management",
        "wshobson/agents",
        "plugins/cicd-automation/skills/secrets-management",
        "SKILL.md",
    ] in rows
    assert all(len(r) == 4 for r in rows)


def test_cli_classify_all_reads_stdin(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    import io

    proto = load_manifest(MANIFEST)["prototype"]
    fetched = (
        "\n".join(f"prototype\t{f}\t{md5}" for f, md5 in proto.upstream_md5.items())
        + "\nwrite-a-skill\tSKILL.md\tnull\n"
    )
    monkeypatch.setattr("sys.stdin", io.StringIO(fetched))
    assert _cli(["classify-all", "--manifest", str(MANIFEST)]) == 0
    out = capsys.readouterr().out
    assert "prototype | * | | | SAME" in out
    assert "write-a-skill | * | | | ORPHAN" in out
    assert (
        "grill-with-docs | * | | | ORPHAN" in out
    )  # absent from stdin → every file None


def test_cli_usage_errors_exit_2(capsys: pytest.CaptureFixture[str]) -> None:
    assert _cli(["classify", "no-such-skill", "{}"]) == 2
    assert _cli(["classify", "prototype", "{}", "--manifest"]) == 2
    assert _cli(["bogus"]) == 2


def test_default_manifest_constant_is_shared() -> None:
    from aa_ma.forks import DEFAULT_MANIFEST

    assert DEFAULT_MANIFEST == MANIFEST


@pytest.mark.parametrize("name", sorted(load_manifest(MANIFEST)))
def test_every_fork_provenance_names_its_upstream(name: str) -> None:
    """Line-2 provenance names the row's own repo + path (not always mattpocock/skills)."""
    assert_skill_frontmatter(name, expected_upstream_path=None)


@pytest.mark.parametrize("name", sorted(load_manifest(MANIFEST)))
def test_every_fork_carries_upstream_licence(name: str) -> None:
    """An MIT fork ships the upstream LICENSE beside its files (MIT's notice condition)."""
    entry = load_manifest(MANIFEST)[name]
    assert entry.licence == "MIT", (
        f"{name}: licence {entry.licence!r} — review before forking"
    )
    licence = SKILLS_DIR / name / "LICENSE"
    assert licence.is_file(), f"MISSING_LICENSE: {name}/LICENSE"
    assert licence.read_text(encoding="utf-8").startswith("MIT License"), name


def test_wshobson_forks_recorded() -> None:
    manifest = load_manifest(MANIFEST)
    secrets, bash = manifest["secrets-management"], manifest["bash-defensive-patterns"]
    assert (secrets.upstream_repo, secrets.state) == ("wshobson/agents", "current")
    assert secrets.upstream_sha == "46891e7e60da0e52baf1050b7b6391b64e84c6d9"
    assert secrets.files == secrets.upstream_md5  # current = byte-exact upstream
    assert (bash.upstream_repo, bash.state) == ("wshobson/agents", "derived")
    assert bash.upstream_sha == "5d65aa10638bcc1b390738e11f9bff213f61955a"


def test_python_quality_gates_baseline_link_resolves() -> None:
    """The ruff baseline is linked relative to the skill, not via ~/.claude (works in-repo)."""
    skill = SKILLS_DIR / "python-quality-gates" / "SKILL.md"
    text = skill.read_text(encoding="utf-8")
    assert "~/.claude/skills/" not in text
    assert "../logging-and-comments/references/ruff-baseline.toml" in text
    assert (
        skill.parent / "../logging-and-comments/references/ruff-baseline.toml"
    ).is_file()
