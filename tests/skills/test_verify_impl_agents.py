"""Prototype-validation smoke tests for the 5 verify-impl audit agents.

Per ADR-0005 / Plan M4: agent prompts must satisfy structural invariants:
- Required YAML frontmatter fields (name, description, tools)
- Documented mandatory pattern checks
- Output format (SUMMARY: <N> CRITICAL, <M> WARNING, <P> INFO trailer)
- L-005 / L-006 / L-007 references in the agents that audit those classes
- Cross-agent consistency on severity vocabulary

These tests run at every commit (via the default pytest suite) to guard
against drift in agent prompts that would break the orchestrator's parsing.
"""
from __future__ import annotations

from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
AGENTS_DIR = PROJECT_ROOT / "claude-code" / "agents"

VERIFY_IMPL_AGENTS = [
    "code-reviewer",
    "security-auditor",
    "tdd-sequence-auditor",
    "context7-evidence-auditor",
    "future-proofing-auditor",
]


def _read_agent(name: str) -> str:
    return (AGENTS_DIR / f"{name}.md").read_text(encoding="utf-8")


@pytest.mark.parametrize("agent", VERIFY_IMPL_AGENTS)
def test_agent_file_exists(agent: str) -> None:
    path = AGENTS_DIR / f"{agent}.md"
    assert path.is_file(), f"Agent file missing: {path}"


@pytest.mark.parametrize("agent", VERIFY_IMPL_AGENTS)
def test_agent_has_required_frontmatter(agent: str) -> None:
    text = _read_agent(agent)
    assert text.startswith("---\n"), f"{agent}: missing YAML frontmatter opener"
    frontmatter_end = text.find("---\n", 4)
    assert frontmatter_end > 0, f"{agent}: missing YAML frontmatter closer"
    frontmatter = text[4:frontmatter_end]
    assert f"name: {agent}" in frontmatter, f"{agent}: frontmatter missing name field"
    assert "description:" in frontmatter, f"{agent}: frontmatter missing description"
    assert "tools:" in frontmatter, f"{agent}: frontmatter missing tools"


@pytest.mark.parametrize("agent", VERIFY_IMPL_AGENTS)
def test_agent_documents_output_summary_format(agent: str) -> None:
    """Every agent must specify the SUMMARY: <N> CRITICAL, <M> WARNING, <P> INFO trailer."""
    text = _read_agent(agent)
    assert "SUMMARY:" in text, f"{agent}: missing SUMMARY: output format"
    assert "CRITICAL" in text and "WARNING" in text and "INFO" in text, (
        f"{agent}: must mention all three severity levels"
    )


@pytest.mark.parametrize("agent", VERIFY_IMPL_AGENTS)
def test_agent_declares_grandfathering(agent: str) -> None:
    """Every agent must respect the pre-v0.8.0 grandfathering rule."""
    text_lower = _read_agent(agent).lower()
    # Either "pre-v0.8.0" or "grandfather" or "created:" — at least one must be cited
    has_grandfathering = any(
        marker in text_lower for marker in ["pre-v0.8.0", "grandfather", "created:"]
    )
    assert has_grandfathering, f"{agent}: missing grandfathering documentation"


@pytest.mark.parametrize("agent", VERIFY_IMPL_AGENTS)
def test_agent_declares_budget_modes(agent: str) -> None:
    """Every agent must document AA_MA_AUDIT_BUDGET behaviour."""
    text = _read_agent(agent)
    assert "AA_MA_AUDIT_BUDGET" in text, (
        f"{agent}: missing AA_MA_AUDIT_BUDGET documentation"
    )


class TestLessonReferences:
    """Specific agents must reference the lessons they're designed to catch."""

    def test_code_reviewer_references_l005(self) -> None:
        """code-reviewer mandatory pattern #2 (mechanism duplication) maps to L-005."""
        text = _read_agent("code-reviewer")
        assert "L-005" in text, "code-reviewer must reference L-005 (install.sh symlinks)"
        assert "mechanism duplication" in text.lower(), (
            "code-reviewer must document the mechanism-duplication pattern"
        )

    def test_code_reviewer_references_l006(self) -> None:
        """code-reviewer mandatory pattern #3 (schema-breaking output) maps to L-006."""
        text = _read_agent("code-reviewer")
        assert "L-006" in text, "code-reviewer must reference L-006 (cz bump CHANGELOG)"
        assert "schema-breaking output" in text.lower(), (
            "code-reviewer must document the schema-breaking output pattern"
        )

    def test_code_reviewer_references_l007(self) -> None:
        """code-reviewer mandatory pattern #1 (scope discipline) maps to L-007."""
        text = _read_agent("code-reviewer")
        assert "L-007" in text, "code-reviewer must reference L-007 (sole-dev-merge format pass)"
        assert "scope discipline" in text.lower(), (
            "code-reviewer must document the scope-discipline pattern"
        )

    def test_security_auditor_separation_from_mechanical(self) -> None:
        """security-auditor must NOT duplicate the mechanical hook layer."""
        text = _read_agent("security-auditor")
        assert "security-static-check.sh" in text, (
            "security-auditor must reference the mechanical hook"
        )
        assert "semantic" in text.lower(), "security-auditor scope is semantic"

    def test_context7_evidence_auditor_narrow_scope(self) -> None:
        """context7-evidence-auditor must skip patch/minor bumps (false-positive control)."""
        text = _read_agent("context7-evidence-auditor")
        assert "MAJOR" in text, "context7-evidence-auditor scope is MAJOR-bump only"
        # Must not emit CRITICAL — WARNING-only ceiling
        assert "WARNING-only" in text or "never CRITICAL" in text, (
            "context7-evidence-auditor severity ceiling must be WARNING"
        )

    def test_future_proofing_coordinates_with_tier6(self) -> None:
        """future-proofing-auditor must reference the existing Tier 6 detector."""
        text = _read_agent("future-proofing-auditor")
        assert "Tier 6" in text, (
            "future-proofing-auditor must reference Tier 6 doc-count-drift detector"
        )

    def test_tdd_sequence_auditor_three_state_verdict(self) -> None:
        """tdd-sequence-auditor must produce exactly PASS / FAIL / WAIVED."""
        text = _read_agent("tdd-sequence-auditor")
        for state in ("PASS", "FAIL", "WAIVED"):
            assert f"VERDICT: {state}" in text, (
                f"tdd-sequence-auditor must declare VERDICT: {state}"
            )


class TestSkillOrchestrator:
    """The /verify-impl skill must dispatch the right agents per Audit-Profile."""

    SKILL_PATH = PROJECT_ROOT / "claude-code" / "skills" / "verify-impl" / "SKILL.md"

    def test_skill_file_exists(self) -> None:
        assert self.SKILL_PATH.is_file()

    def test_skill_references_all_agents(self) -> None:
        text = self.SKILL_PATH.read_text(encoding="utf-8")
        for agent in VERIFY_IMPL_AGENTS:
            assert agent in text, f"SKILL.md must reference agent: {agent}"

    def test_skill_documents_audit_profile_dispatch(self) -> None:
        text = self.SKILL_PATH.read_text(encoding="utf-8")
        for profile in ("full", "code-only", "docs-only", "infra", "custom"):
            assert f"`{profile}`" in text, f"SKILL.md must document profile: {profile}"

    def test_skill_documents_bypass_mechanisms(self) -> None:
        text = self.SKILL_PATH.read_text(encoding="utf-8")
        for mechanism in (
            "AA_MA_HOOKS_DISABLE",
            "AA_MA_AUDIT_BUDGET",
            "TDD-Waiver",
            "security-bypass",
        ):
            assert mechanism in text, f"SKILL.md must document bypass: {mechanism}"


class TestImplReviewTemplate:
    """The impl-review template must mirror the verification template structure."""

    TEMPLATE_PATH = PROJECT_ROOT / "docs" / "templates" / "impl-review-template.md"

    def test_template_exists(self) -> None:
        assert self.TEMPLATE_PATH.is_file()

    def test_template_has_section_per_agent(self) -> None:
        text = self.TEMPLATE_PATH.read_text(encoding="utf-8")
        for label in ("Code Review", "Security", "TDD Sequence", "External Library Evidence", "Future-Proofing"):
            assert label in text, f"impl-review-template must have section: {label}"

    def test_template_has_user_override_section(self) -> None:
        text = self.TEMPLATE_PATH.read_text(encoding="utf-8")
        assert "User Override Decisions" in text
        for option in ("accept", "dispute", "defer"):
            assert option in text.lower(), f"override panel must mention: {option}"
