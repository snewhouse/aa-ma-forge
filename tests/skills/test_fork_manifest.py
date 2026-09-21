"""Fork manifest tests — `claude-code/skills/FORKS.json` is the SSoT for every fork.

Milestone 1 Contract (mattpocock-trio-adoption). The classifier tests build
`fetched` dicts by hand: no plugin cache, no network, so they run in CI.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from aa_ma.forks import ForkEntry, classify_fork, load_manifest

from ._helpers import SKILLS_DIR, assert_skill_frontmatter  # pyright: ignore[reportMissingImports]

MANIFEST = SKILLS_DIR / "FORKS.json"
FORK_LINE_PREFIXES = ("<!-- Forked from ", "<!-- Derived from ")


def _fork_dirs() -> set[str]:
    """Skill dirs whose SKILL.md line 1 is a Forked/Derived provenance comment."""
    out: set[str] = set()
    for skill_md in SKILLS_DIR.glob("*/SKILL.md"):
        with skill_md.open(encoding="utf-8") as fh:
            first = fh.readline()
        if first.startswith(FORK_LINE_PREFIXES):
            out.add(skill_md.parent.name)
    return out


def _local_md5(path: Path) -> str:
    """md5 of `tail -n +2 <file>` — the manifest `files.<f>` recipe."""
    body = path.read_bytes().split(b"\n", 1)[1] if b"\n" in path.read_bytes() else b""
    return hashlib.md5(body).hexdigest()  # noqa: S324 — integrity check, not security


def test_every_fork_dir_is_in_manifest() -> None:
    manifest = load_manifest(MANIFEST)
    missing = sorted(_fork_dirs() - manifest.keys())
    assert not missing, "MISSING_IN_MANIFEST: " + ", ".join(missing)


def test_manifest_entries_exist_on_disk() -> None:
    manifest = load_manifest(MANIFEST)
    for name, entry in manifest.items():
        assert (SKILLS_DIR / name).is_dir(), f"MISSING_ON_DISK: {name}"
        for fname in entry.files:
            assert (SKILLS_DIR / name / fname).is_file(), f"MISSING_ON_DISK: {name}/{fname}"


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
    assert classify_fork(_entry(**{"SKILL.md": None}), {"SKILL.md": "anything"}) == "SAME"


def test_load_manifest_names_missing_key(tmp_path: Path) -> None:
    bad = tmp_path / "FORKS.json"
    bad.write_text(json.dumps({"x": {"upstream": "skills/x"}}), encoding="utf-8")
    with pytest.raises(ValueError, match="upstream_sha"):
        load_manifest(bad)


def test_helper_resolves_upstream_from_manifest() -> None:
    """Step 1.3: `expected_upstream_path=None` derives the path from FORKS.json."""
    assert_skill_frontmatter("prototype", expected_upstream_path=None)
