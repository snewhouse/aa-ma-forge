"""Skills that read codemem record CODE_INTEL_STALE on a stale result (M15.3, report 03 X2)."""

from pathlib import Path

import pytest

from tests.skills._helpers import skill_text

SKILLS = Path(__file__).resolve().parents[2] / "claude-code" / "skills"


@pytest.mark.parametrize("skill", ["impact-analysis", "plan-verification"])
def test_skill_records_code_intel_stale(skill):
    text = skill_text(SKILLS / skill)
    assert "CODE_INTEL_STALE" in text
    assert "stale_reason" in text
    assert (
        "leads" in text
    )  # stale results are leads to confirm by reading, not evidence
