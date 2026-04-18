"""Tests for M4 Task 4.6 — codemem doc-drift detection.

Exercises Tier 1 (version strings) and Tier 2 (CHANGELOG completeness) of
``Skill(doc-drift-detection)`` against codemem-shaped synthetic drift in
tmp git repos. Each test stages a known-bad scenario, runs
``scripts/check_codemem_doc_drift.py``, and asserts the finding fires
with the right severity + location.

These tests are the "test commit" half of the AC — they prove the hook
works without requiring users to audit the whole real-repo doc tree.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPT = REPO_ROOT / "scripts" / "check_codemem_doc_drift.py"


def _run_script(repo_path: Path) -> tuple[int, list[dict]]:
    """Invoke the script inside ``repo_path``; return (exit_code, findings)."""
    r = subprocess.run(
        [sys.executable, str(SCRIPT), "--repo-root", str(repo_path), "--json"],
        capture_output=True,
        text=True,
        check=False,
    )
    findings = json.loads(r.stdout) if r.stdout.strip() else []
    return r.returncode, findings


def _bootstrap_codemem_shaped_repo(tmp_path: Path, *, version: str = "0.1.0.dev0") -> Path:
    """Create a minimal codemem-shaped file tree inside ``tmp_path``.

    Ships just enough of the structure for the script to find:
      * ``packages/codemem-mcp/pyproject.toml`` (canonical version)
      * ``claude-code/codemem/README.md`` (Tier 1 scan target)
      * ``docs/codemem/`` (Tier 1 scan target)
      * ``CHANGELOG.md`` (Tier 2 target)
    """
    (tmp_path / "packages" / "codemem-mcp").mkdir(parents=True)
    (tmp_path / "packages" / "codemem-mcp" / "pyproject.toml").write_text(
        f'[project]\nname = "codemem-mcp"\nversion = "{version}"\n'
    )
    (tmp_path / "claude-code" / "codemem").mkdir(parents=True)
    (tmp_path / "claude-code" / "codemem" / "README.md").write_text(
        "# codemem\n\nStructural code intelligence.\n"
    )
    (tmp_path / "docs" / "codemem").mkdir(parents=True)
    (tmp_path / "docs" / "codemem" / "install-zero-config.md").write_text(
        "# install\n\nDrop `.mcp.json` and go.\n"
    )
    (tmp_path / "CHANGELOG.md").write_text("# Changelog\n\n## [0.0.1] - prehistory\n")
    # Minimal git repo so Tier 2's `git describe` works.
    subprocess.run(["git", "init", "-q", "-b", "main", str(tmp_path)], check=True)
    subprocess.run(
        ["git", "-C", str(tmp_path), "config", "user.email", "t@x"], check=True
    )
    subprocess.run(
        ["git", "-C", str(tmp_path), "config", "user.name", "T"], check=True
    )
    subprocess.run(["git", "-C", str(tmp_path), "add", "-A"], check=True)
    subprocess.run(
        ["git", "-C", str(tmp_path), "commit", "-qm", "chore: initial"], check=True
    )
    subprocess.run(
        ["git", "-C", str(tmp_path), "tag", "v0.0.1"], check=True
    )
    return tmp_path


# ---------------------------------------------------------------------
# Tier 1 — version string drift
# ---------------------------------------------------------------------

class TestTier1VersionDrift:
    def test_clean_state_no_findings(self, tmp_path):
        _bootstrap_codemem_shaped_repo(tmp_path)
        code, findings = _run_script(tmp_path)
        assert code == 0, findings
        assert findings == []

    def test_mismatched_version_in_codemem_readme_fires(self, tmp_path):
        _bootstrap_codemem_shaped_repo(tmp_path, version="0.2.0")
        readme = tmp_path / "claude-code" / "codemem" / "README.md"
        readme.write_text(
            readme.read_text()
            + "\n\nCurrent codemem version: 0.1.5.\n"
        )
        code, findings = _run_script(tmp_path)
        assert code == 1, findings
        assert len(findings) == 1
        f = findings[0]
        assert "Tier 1" in f["tier"]
        assert f["severity"] == "WARNING"
        assert f["file"] == "claude-code/codemem/README.md"
        assert "0.1.5" in f["message"]
        assert "0.2.0" in f["message"]

    def test_unrelated_version_in_prose_is_ignored(self, tmp_path):
        """A bare version number NOT near 'codemem' or 'version' must not fire."""
        _bootstrap_codemem_shaped_repo(tmp_path, version="0.2.0")
        (tmp_path / "docs" / "codemem" / "misc.md").write_text(
            "# misc\n\nPython 3.11 is required.\n"
            "The git binary must be 2.25.0 or newer.\n"
        )
        code, findings = _run_script(tmp_path)
        assert code == 0, findings
        assert findings == []

    def test_pep440_normalised_vs_dashed_fires(self, tmp_path):
        """Regression: previously '0.1.0' substring of '0.1.0-dev' slipped
        through the Tier 1 regex. Full PEP 440 pattern must match either
        dotted or dashed suffix forms as separate drift.
        """
        _bootstrap_codemem_shaped_repo(tmp_path, version="0.1.0.dev0")
        readme = tmp_path / "claude-code" / "codemem" / "README.md"
        readme.write_text(
            readme.read_text() + "\n\nThe codemem version is 0.1.0-dev (shipped).\n"
        )
        code, findings = _run_script(tmp_path)
        assert code == 1, findings
        assert any("0.1.0-dev" in f["message"] for f in findings), findings


# ---------------------------------------------------------------------
# Tier 2 — CHANGELOG completeness
# ---------------------------------------------------------------------

class TestTier2ChangelogCompleteness:
    def test_feat_commit_touching_codemem_without_unreleased_fires(self, tmp_path):
        _bootstrap_codemem_shaped_repo(tmp_path)
        # Write a new file under a codemem path and commit as feat:.
        new_file = tmp_path / "packages" / "codemem-mcp" / "src" / "codemem" / "x.py"
        new_file.parent.mkdir(parents=True)
        new_file.write_text("def x(): return 1\n")
        subprocess.run(["git", "-C", str(tmp_path), "add", "-A"], check=True)
        subprocess.run(
            ["git", "-C", str(tmp_path), "commit", "-qm", "feat(codemem): add x"],
            check=True,
        )
        code, findings = _run_script(tmp_path)
        assert code == 1, findings
        assert any(
            "Tier 2" in f["tier"] and "CHANGELOG" in f["tier"]
            for f in findings
        ), findings

    def test_feat_commit_with_unreleased_section_does_not_fire(self, tmp_path):
        _bootstrap_codemem_shaped_repo(tmp_path)
        changelog = tmp_path / "CHANGELOG.md"
        changelog.write_text(
            changelog.read_text()
            + "\n\n## [Unreleased]\n\n- codemem: add x\n"
        )
        new_file = tmp_path / "packages" / "codemem-mcp" / "src" / "codemem" / "x.py"
        new_file.parent.mkdir(parents=True)
        new_file.write_text("def x(): return 1\n")
        subprocess.run(["git", "-C", str(tmp_path), "add", "-A"], check=True)
        subprocess.run(
            ["git", "-C", str(tmp_path), "commit", "-qm", "feat(codemem): add x"],
            check=True,
        )
        code, findings = _run_script(tmp_path)
        # Tier 2 should NOT fire; other tiers may be silent too.
        tier_2 = [f for f in findings if "Tier 2" in f["tier"]]
        assert tier_2 == [], f"Tier 2 should be silent when Unreleased exists: {tier_2}"

    def test_feat_commit_NOT_touching_codemem_does_not_fire_tier_2(self, tmp_path):
        """A feat commit that only touches a non-codemem path must not trip the
        codemem-scoped Tier 2 check (this is the whole point of being
        codemem-specific rather than generic)."""
        _bootstrap_codemem_shaped_repo(tmp_path)
        (tmp_path / "unrelated").mkdir()
        (tmp_path / "unrelated" / "note.md").write_text("unrelated\n")
        subprocess.run(["git", "-C", str(tmp_path), "add", "-A"], check=True)
        subprocess.run(
            ["git", "-C", str(tmp_path), "commit", "-qm", "feat(unrelated): add note"],
            check=True,
        )
        _code, findings = _run_script(tmp_path)
        tier_2 = [f for f in findings if "Tier 2" in f["tier"]]
        assert tier_2 == [], f"Tier 2 must stay scoped to codemem paths: {tier_2}"


# ---------------------------------------------------------------------
# Historical-doc exclusion
# ---------------------------------------------------------------------

class TestHistoricalDocExclusion:
    def test_design_scratchpad_excluded_from_tier_1(self, tmp_path):
        """The script must not flag drift in frozen design-phase artefacts
        listed in CODEMEM_DOC_EXCLUDE — retroactive updates would violate
        CLAUDE.md's 'historical docs are frozen' rule."""
        _bootstrap_codemem_shaped_repo(tmp_path, version="0.2.0")
        (tmp_path / "docs" / "codemem" / "design-scratchpad.md").write_text(
            "# design scratchpad\n\ncodemem version plan at that time: 0.1.0.\n"
        )
        code, findings = _run_script(tmp_path)
        # design-scratchpad hit would fire Tier 1 without the exclude set.
        assert code == 0, findings
        assert findings == []


# ---------------------------------------------------------------------
# Live repo smoke (optional — proves the script is wired to the real tree)
# ---------------------------------------------------------------------

class TestLiveRepoSmoke:
    def test_live_repo_is_clean(self):
        """The aa-ma-forge repo itself must not carry codemem doc-drift at
        commit time. If this fires, someone landed a regression in the
        docs — run the script locally and fix.
        """
        code, findings = _run_script(REPO_ROOT)
        assert code == 0, (
            "codemem doc-drift in live repo:\n"
            + "\n".join(
                f"  [{f['severity']}] {f['tier']} — {f['file']}:{f['line']} — {f['message']}"
                for f in findings
            )
        )
