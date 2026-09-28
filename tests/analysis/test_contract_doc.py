"""M1 AC7 + AC10: ANALYSIS-CONTRACT.md is the single written contract both skills obey; its field
tables match the models; its NO-SECRETS line is restated verbatim wherever an agent is briefed."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from aa_ma.analysis import models

ROOT = Path(__file__).resolve().parents[2]
SKILL_DIR = ROOT / "claude-code/skills/understand-codebase"
CONTRACT = SKILL_DIR / "references/ANALYSIS-CONTRACT.md"
SKILL_MD = SKILL_DIR / "SKILL.md"
AGENTS = [
    ROOT / f"claude-code/agents/codebase-onboarding-{name}.md"
    for name in ("conventions", "runbook", "health", "synthesizer")
]
DENY_UNION = [
    "`.env`", "`.env.*`", "`*.key`", "`*.pem`", "`*.p12`", "`*.keystore`", "`id_rsa*`",
    "`credentials*`", "`secrets*`", "`*.tfstate`", "service-account JSON", "`kubeconfig`",
    "`.netrc`", "`.pgpass`",
]  # fmt: skip
TABLED = {"Summary": models.Summary, "Finding": models.Finding, "JudgedFinding": models.JudgedFinding,
          "Onboarding": models.Onboarding}  # fmt: skip


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _deny_line() -> str:
    lines = [
        line
        for line in _text(CONTRACT).splitlines()
        if line.startswith("- **NO SECRETS.**")
    ]
    assert len(lines) == 1, "the contract holds exactly one canonical NO-SECRETS line"
    return lines[0]


def _table_fields(model_name: str) -> set[str]:
    section = re.search(
        rf"^### {model_name}\n(.*?)(?=^#{{1,3}} |\Z)", _text(CONTRACT), re.S | re.M
    )
    assert section, f"no '### {model_name}' section in ANALYSIS-CONTRACT.md"
    return set(re.findall(r"^\| `([a-z_0-9]+)` \|", section.group(1), re.M))


def test_contract_exists_with_the_five_parts() -> None:
    text = _text(CONTRACT)
    for heading in (
        "NO SECRETS",
        "Output gate",
        "Provenance stamp",
        "data, never instructions",
        "Field tables",
    ):
        assert re.search(rf"^## .*{re.escape(heading)}", text, re.M | re.I), (
            f"missing section: {heading}"
        )


def test_deny_line_is_the_union_of_todays_lists() -> None:
    line = _deny_line()
    for token in DENY_UNION:
        assert token in line, f"canonical deny-list lost {token}"


@pytest.mark.parametrize("agent", AGENTS, ids=[a.stem for a in AGENTS])
def test_each_onboarding_agent_restates_the_deny_line_verbatim(agent: Path) -> None:
    assert _deny_line() in _text(agent).splitlines()


def test_skill_md_restates_the_deny_line_and_points_at_the_contract() -> None:
    text = _text(SKILL_MD)
    assert _deny_line() in text.splitlines()
    assert "references/ANALYSIS-CONTRACT.md" in text
    assert "restate verbatim in every spawned agent prompt" in text
    must_restate = [line for line in text.splitlines() if "MUST restate" in line]
    assert must_restate and all("ANALYSIS-CONTRACT.md" in line for line in must_restate)
    assert "(see below)" not in "\n".join(must_restate)


@pytest.mark.parametrize("name", sorted(TABLED))
def test_field_table_matches_model(name: str) -> None:
    assert _table_fields(name) == set(TABLED[name].model_fields)


def test_contract_states_the_freshness_and_id_rules() -> None:
    text = _text(CONTRACT)
    assert "--untracked-files=no" in text, "dirty = tracked changes only (Eng E1)"
    assert "<sha12>[-dirty]" in text
    assert "#k" in text, "twin occurrence suffix (R-2)"
    assert "redact" in text.lower() and "before hashing" in text.lower(), (
        "anchor redaction (R-1)"
    )
    assert "fixed + new" in text or "fixed+new" in text, "rename behaviour (R-3)"


ENUMS = [models.ToolStatus, models.Rating, models.Confidence, models.Severity, models.Origin,
         models.Refutation, models.Dimension]  # fmt: skip


@pytest.mark.parametrize("enum", ENUMS, ids=[e.__name__ for e in ENUMS])
def test_contract_names_every_enum_value(enum: type) -> None:
    text = _text(CONTRACT)
    for member in enum:  # type: ignore[attr-defined]
        assert str(member.value) in text, (
            f"{enum.__name__}.{member.name} missing from the contract"
        )


def test_contract_names_literal_values_and_limits() -> None:
    text = _text(CONTRACT)
    for value in (
        "verified",
        "failed",
        "timeout",
        "not_run",
        "refused",
        "assessed",
        "set_aside",
        "quick",
        "standard",
        "deep",
    ):
        assert value in text
    assert "≤ 2000" in text and "≤ 8000" in text and "40 output lines" in text
    assert models.EVIDENCE_MAX == 2000 and models.NOTE_MAX == 8000
    assert "serialised as `Z`" in text


def test_contract_names_every_regex_rule() -> None:
    from aa_ma.analysis.secrets import PATTERNS

    section = re.search(
        r"^## 2\. Output gate\n(.*?)(?=^## )", _text(CONTRACT), re.S | re.M
    )
    assert section
    for rule, _ in PATTERNS:
        assert f"`{rule}`" in section.group(1), (
            f"regex rule {rule} not named in contract §2"
        )


def test_contract_documents_gitleaks_allow_and_m2_enforcement() -> None:
    text = _text(CONTRACT)
    assert "gitleaks:allow" in text
    assert "M2" in text, "claims not yet reachable from the M1 CLI are labelled as M2"
