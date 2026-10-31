"""Every setup-uv step in CI pins one Python version.

An unpinned step takes the runner image's default Python. When the image moved to 3.14
(2026-10-31), watchfiles 0.24 had no wheel for it, its source build failed, and the
Ruff S and pre-commit jobs went red on main with no change in the repo.
"""

from pathlib import Path

import yaml

WORKFLOWS = Path(__file__).resolve().parents[2] / ".github" / "workflows"


def _setup_uv_steps() -> list[tuple[str, str, dict]]:
    steps = []
    for wf in sorted(WORKFLOWS.glob("*.yml")):
        for job_id, job in yaml.safe_load(wf.read_text())["jobs"].items():
            for step in job.get("steps", []):
                if "astral-sh/setup-uv@" in step.get("uses", ""):
                    steps.append((wf.name, job_id, step.get("with", {})))
    return steps


def test_every_setup_uv_step_pins_the_same_python() -> None:
    steps = _setup_uv_steps()
    assert steps
    unpinned = [f"{wf}:{job}" for wf, job, w in steps if "python-version" not in w]
    assert not unpinned, f"setup-uv without python-version: {unpinned}"
    assert len({str(w["python-version"]) for _, _, w in steps}) == 1
