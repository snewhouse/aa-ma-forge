"""Coverage of all 8 branches of scripts/grill-mode-resolver.sh.

Each test invokes the resolver as a subprocess from an isolated `tmp_path`
project root, mocking the project state with `mktemp -d`-equivalent fixtures.

Branches covered (M1.7a acceptance criteria):
    1. --grill-mode=auto + CONTEXT.md present                → with-docs / 0
    2. --grill-mode=auto + docs/adr/ present (readable)      → with-docs / 0
    3. --grill-mode=auto + docs/adr/ unreadable              → simple / 0 + WARN
    4. --grill-mode=auto + neither present (greenfield)      → simple / 0
    5. --grill-mode=with-docs (force, no project state)      → with-docs / 0
    6. --grill-mode=simple (force, no project state)         → simple / 0
    7. --grill-mode=skip                                     → skip / 0
    8. --grill-mode=INVALID (E1)                             → skip / 2 + ERROR

Additional coverage:
    9. AA_MA_GRILL_MODE env var honored (no CLI flag)
    10. CLI flag overrides AA_MA_GRILL_MODE env var
    11. --grill-mode <value> (space-separated, not equals)
"""

from __future__ import annotations

import os
import stat
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
RESOLVER = REPO_ROOT / "scripts" / "grill-mode-resolver.sh"


def _run(
    *args: str, cwd: Path, env: dict[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    """Invoke the resolver script with the given args from `cwd`."""
    final_env = os.environ.copy()
    if env is not None:
        final_env.update(env)
    return subprocess.run(
        ["bash", str(RESOLVER), *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        env=final_env,
        check=False,
    )


def test_resolver_script_exists_and_is_executable() -> None:
    assert RESOLVER.exists(), f"Resolver script missing at {RESOLVER}"
    assert os.access(RESOLVER, os.X_OK), f"Resolver script not executable: {RESOLVER}"


# ---------- 8 acceptance branches (one per criterion) -------------------------


def test_branch_1_auto_with_context_md_resolves_to_with_docs(tmp_path: Path) -> None:
    """Branch 1: --grill-mode=auto + CONTEXT.md present → with-docs."""
    (tmp_path / "CONTEXT.md").touch()
    result = _run("--grill-mode=auto", cwd=tmp_path)
    assert result.returncode == 0
    assert result.stdout.strip() == "with-docs"
    assert "GRILL-MODE: with-docs" in result.stderr
    assert "CONTEXT.md found" in result.stderr


def test_branch_2_auto_with_docs_adr_readable_resolves_to_with_docs(
    tmp_path: Path,
) -> None:
    """Branch 2: --grill-mode=auto + docs/adr/ readable → with-docs."""
    (tmp_path / "docs" / "adr").mkdir(parents=True)
    result = _run("--grill-mode=auto", cwd=tmp_path)
    assert result.returncode == 0
    assert result.stdout.strip() == "with-docs"
    assert "docs/adr/ found and readable" in result.stderr


def test_branch_3_auto_with_docs_adr_unreadable_falls_back_to_simple(
    tmp_path: Path,
) -> None:
    """Branch 3 (C3 fix): unreadable docs/adr/ → simple with stderr WARN."""
    adr = tmp_path / "docs" / "adr"
    adr.mkdir(parents=True)
    # Strip read+execute perms (root may bypass; if so, test is informational)
    adr.chmod(0)
    try:
        if os.geteuid() == 0:
            pytest.skip(
                "Running as root — chmod 000 cannot block access; branch 3 cannot be exercised"
            )
        result = _run("--grill-mode=auto", cwd=tmp_path)
        assert result.returncode == 0
        assert result.stdout.strip() == "simple"
        assert "WARN" in result.stderr
        assert "not readable" in result.stderr
    finally:
        # Restore perms so pytest can clean up tmp_path
        adr.chmod(stat.S_IRWXU)


def test_branch_4_auto_greenfield_resolves_to_simple(tmp_path: Path) -> None:
    """Branch 4: --grill-mode=auto + neither CONTEXT.md nor docs/adr/ → simple."""
    result = _run("--grill-mode=auto", cwd=tmp_path)
    assert result.returncode == 0
    assert result.stdout.strip() == "simple"
    assert "GRILL-MODE: simple" in result.stderr
    assert "no CONTEXT.md and no docs/adr/" in result.stderr


def test_branch_5_force_with_docs_ignores_project_state(tmp_path: Path) -> None:
    """Branch 5: --grill-mode=with-docs forced — no CONTEXT.md, still resolves with-docs."""
    result = _run("--grill-mode=with-docs", cwd=tmp_path)
    assert result.returncode == 0
    assert result.stdout.strip() == "with-docs"
    assert "forced via --grill-mode/AA_MA_GRILL_MODE" in result.stderr


def test_branch_6_force_simple_ignores_project_state(tmp_path: Path) -> None:
    """Branch 6: --grill-mode=simple forced even with CONTEXT.md present."""
    (tmp_path / "CONTEXT.md").touch()
    result = _run("--grill-mode=simple", cwd=tmp_path)
    assert result.returncode == 0
    assert result.stdout.strip() == "simple"
    assert "forced via --grill-mode/AA_MA_GRILL_MODE" in result.stderr


def test_branch_7_skip_bypasses_phase_1_3(tmp_path: Path) -> None:
    """Branch 7: --grill-mode=skip → skip / exit 0."""
    result = _run("--grill-mode=skip", cwd=tmp_path)
    assert result.returncode == 0
    assert result.stdout.strip() == "skip"
    assert "Phase 1.3 bypassed" in result.stderr


def test_branch_8_invalid_mode_emits_error_and_skip_default(tmp_path: Path) -> None:
    """Branch 8 (E1): invalid --grill-mode → exit 2, stderr ERROR, stdout safe-default 'skip'."""
    result = _run("--grill-mode=INVALID", cwd=tmp_path)
    assert result.returncode == 2
    assert result.stdout.strip() == "skip"
    assert "ERROR" in result.stderr
    assert "INVALID" in result.stderr
    assert "Treating as 'skip' for safety" in result.stderr


# ---------- Bonus precedence + parsing coverage ------------------------------


def test_env_var_honored_when_no_cli_flag(tmp_path: Path) -> None:
    """AA_MA_GRILL_MODE env var resolves correctly when --grill-mode is absent."""
    result = _run(cwd=tmp_path, env={"AA_MA_GRILL_MODE": "with-docs"})
    assert result.returncode == 0
    assert result.stdout.strip() == "with-docs"
    assert "forced via --grill-mode/AA_MA_GRILL_MODE" in result.stderr


def test_cli_flag_overrides_env_var(tmp_path: Path) -> None:
    """CLI flag has higher precedence than AA_MA_GRILL_MODE env var."""
    result = _run(
        "--grill-mode=skip", cwd=tmp_path, env={"AA_MA_GRILL_MODE": "with-docs"}
    )
    assert result.returncode == 0
    assert result.stdout.strip() == "skip"


def test_space_separated_flag_form_supported(tmp_path: Path) -> None:
    """--grill-mode <value> (space, not equals) is also accepted."""
    result = _run("--grill-mode", "skip", cwd=tmp_path)
    assert result.returncode == 0
    assert result.stdout.strip() == "skip"


def test_default_mode_when_no_flag_and_no_env_is_auto(tmp_path: Path) -> None:
    """No flag + no env var + greenfield project → resolves to 'simple' (auto default)."""
    # Strip AA_MA_GRILL_MODE if it leaks from the parent shell
    env = {k: v for k, v in os.environ.items() if k != "AA_MA_GRILL_MODE"}
    result = subprocess.run(
        ["bash", str(RESOLVER)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    assert result.returncode == 0
    assert result.stdout.strip() == "simple"
    assert "auto:" in result.stderr  # confirms we went through the auto branch
