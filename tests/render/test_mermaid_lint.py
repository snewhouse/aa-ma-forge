from pathlib import Path

import pytest

from aa_ma.render.mermaid_lint import lint_plan

REPO = Path(__file__).resolve().parents[2]
FIX = Path(__file__).parent / "fixtures"


def codes(name: str) -> set[str]:
    return {f.code for f in lint_plan(FIX / name, REPO).findings}


def test_ok_plan_has_no_findings() -> None:
    rep = lint_plan(FIX / "plan_ok.md", REPO)
    assert rep.findings == () and rep.render_status == "UNKNOWN"


@pytest.mark.parametrize(
    "name,code",
    [
        ("plan_no_section.md", "NO_SECTION"),
        ("plan_no_component.md", "NO_COMPONENT_VIEW"),
        ("plan_empty_fence.md", "EMPTY_FENCE"),
        ("plan_unknown_type.md", "UNKNOWN_TYPE"),
        ("plan_stale_path.md", "STALE_PATH"),
        ("plan_two_labels.md", "STALE_PATH"),
        ("plan_waiver_invalid.md", "WAIVER_INVALID"),
        ("plan_waiver_not_allowed.md", "WAIVER_NOT_ALLOWED"),
        ("plan_flow_required.md", "NO_FLOW_VIEW"),
        ("plan_two_fences.md", "UNKNOWN_TYPE"),
        ("plan_bad_audit.md", "AUDIT_PROFILE_INVALID"),
    ],
)
def test_finding_codes(name: str, code: str) -> None:
    assert code in codes(name)


@pytest.mark.parametrize(
    "name",
    [
        "plan_waived_docs_only.md",
        "plan_fenced_example.md",
        "plan_data_state.md",
        "plan_section_last.md",
        "plan_heading_nodot.md",
    ],
)
def test_clean_variants(name: str) -> None:
    assert codes(name) == set()


def test_stale_path_reports_line_number() -> None:
    f = [x for x in lint_plan(FIX / "plan_stale_path.md", REPO).findings if x.code == "STALE_PATH"][0]
    assert f.line > 0 and "src/aa_ma/nope.py" in f.message


def test_plan_h3_milestones_are_read_without_tasks() -> None:
    # Angle 6 runs before tasks.md exists; ### Milestone in plan.md must be enough.
    assert "NO_FLOW_VIEW" in codes("plan_flow_required.md")


def test_tasks_override_supplies_critical_path(tmp_path: Path) -> None:
    plan = tmp_path / "foo.md"
    plan.write_text((FIX / "plan_flow_required.md").read_text().split("### Milestone 1")[0])
    tasks = tmp_path / "t.md"
    tasks.write_text("## Milestone 1: X\n- Audit-Profile: code-only\n- **Critical-Path:** data-xform\n")
    assert "NO_FLOW_VIEW" in {f.code for f in lint_plan(plan, REPO, tasks_path=tasks).findings}
