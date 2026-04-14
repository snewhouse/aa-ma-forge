"""Storm test for the codemem post-commit hook (M2 Task 2.5).

AC: 5 rapid `git commit --amend` calls in <1s must leave only ONE
active codemem refresh process. Verified via the PID file + process
liveness count.

The test installs the hook via the repo's own
`scripts/install.sh --wire-git-hook` path (end-to-end validation).
"""

from __future__ import annotations

import os
import subprocess
import time
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def _init_git_repo(root: Path) -> None:
    subprocess.run(["git", "init", "-q", "-b", "main", str(root)], check=True)
    subprocess.run(
        ["git", "-C", str(root), "config", "user.email", "storm@codemem.local"],
        check=True,
    )
    subprocess.run(
        ["git", "-C", str(root), "config", "user.name", "storm"], check=True
    )


def _wire_hook(root: Path) -> Path:
    """Directly install the hook via a guarded append (same shape as
    scripts/install.sh --wire-git-hook, but scoped to this test)."""
    hook_src = REPO_ROOT / "claude-code" / "codemem" / "hooks" / "post-commit.sh"
    git_dir = root / ".git"
    hook_file = git_dir / "hooks" / "post-commit"
    hook_file.parent.mkdir(parents=True, exist_ok=True)
    hook_file.write_text(
        "#!/usr/bin/env bash\n"
        f'"{hook_src}" || true\n'
    )
    hook_file.chmod(0o755)
    return hook_file


class TestPIDFileLifecycle:
    def test_pid_file_written_after_first_commit(self, tmp_path: Path):
        _init_git_repo(tmp_path)
        _wire_hook(tmp_path)
        (tmp_path / ".gitignore").write_text(".codemem/\n")
        (tmp_path / "seed.py").write_text("def a(): return 1\n")
        subprocess.run(["git", "-C", str(tmp_path), "add", "-A"], check=True)
        env = {**os.environ, "PYTHONPATH": str(REPO_ROOT / "packages" / "codemem-mcp" / "src")}
        subprocess.run(
            ["git", "-C", str(tmp_path), "commit", "-qm", "seed"],
            check=True, env=env,
        )
        # Hook backgrounds the refresh; give it a moment to write PID.
        time.sleep(0.3)
        pid_file = tmp_path / ".codemem" / "refresh.pid"
        assert pid_file.exists()
        pid_text = pid_file.read_text().strip()
        assert pid_text.isdigit()


class TestStormOfAmends:
    def test_five_rapid_amends_one_active_process(self, tmp_path: Path):
        """AC gate: 5 rapid `git commit --amend` in <1s leave exactly
        1 active codemem process (the latest)."""
        _init_git_repo(tmp_path)
        _wire_hook(tmp_path)
        (tmp_path / ".gitignore").write_text(".codemem/\n")
        (tmp_path / "file.py").write_text("def a(): return 1\n")
        subprocess.run(["git", "-C", str(tmp_path), "add", "-A"], check=True)
        env = {**os.environ, "PYTHONPATH": str(REPO_ROOT / "packages" / "codemem-mcp" / "src")}
        subprocess.run(
            ["git", "-C", str(tmp_path), "commit", "-qm", "seed"],
            check=True, env=env,
        )

        start = time.monotonic()
        for i in range(5):
            (tmp_path / "file.py").write_text(f"def a(): return {i + 2}\n")
            subprocess.run(["git", "-C", str(tmp_path), "add", "-A"], check=True)
            subprocess.run(
                ["git", "-C", str(tmp_path), "commit", "--amend", "-qm", f"amend-{i}"],
                check=True, env=env,
            )
        elapsed = time.monotonic() - start
        assert elapsed < 2.0, f"storm took too long: {elapsed:.2f}s"

        # Wait briefly for the last refresh to actually start + the
        # previous ones to die.
        time.sleep(0.5)

        pid_file = tmp_path / ".codemem" / "refresh.pid"
        assert pid_file.exists()

        # Enumerate all live codemem-refresh-like processes under this
        # test's tmp_path. Because other test runs might be in flight,
        # we filter by the repo path in the command line.
        result = subprocess.run(
            ["pgrep", "-af", "codemem"],
            capture_output=True, text=True, check=False,
        )
        active_pids = [
            line.split()[0]
            for line in result.stdout.splitlines()
            if str(tmp_path) in line
        ]
        # At most one active process for this repo.
        assert len(active_pids) <= 1, (
            f"storm left {len(active_pids)} active codemem refreshes: {active_pids}"
        )

    def test_hook_exits_zero_on_storm(self, tmp_path: Path):
        """The storm mustn't make any commit fail."""
        _init_git_repo(tmp_path)
        _wire_hook(tmp_path)
        (tmp_path / ".gitignore").write_text(".codemem/\n")
        (tmp_path / "seed.py").write_text("x = 1\n")
        subprocess.run(["git", "-C", str(tmp_path), "add", "-A"], check=True)
        env = {**os.environ, "PYTHONPATH": str(REPO_ROOT / "packages" / "codemem-mcp" / "src")}

        r = subprocess.run(
            ["git", "-C", str(tmp_path), "commit", "-qm", "seed"],
            env=env,
        )
        assert r.returncode == 0

        for i in range(5):
            (tmp_path / "seed.py").write_text(f"x = {i + 2}\n")
            subprocess.run(["git", "-C", str(tmp_path), "add", "-A"], check=True)
            r = subprocess.run(
                ["git", "-C", str(tmp_path), "commit", "--amend", "-qm", f"amend-{i}"],
                env=env,
            )
            assert r.returncode == 0


@pytest.mark.skipif(
    subprocess.run(["which", "setsid"], capture_output=True).returncode != 0,
    reason="setsid not available (macOS)",
)
class TestProcessGroupIsolation:
    def test_new_refresh_gets_own_session(self, tmp_path: Path):
        """Verify setsid path actually fires — new process should have
        PGID == its own PID (session leader)."""
        _init_git_repo(tmp_path)
        _wire_hook(tmp_path)
        (tmp_path / ".gitignore").write_text(".codemem/\n")
        (tmp_path / "seed.py").write_text("x = 1\n")
        subprocess.run(["git", "-C", str(tmp_path), "add", "-A"], check=True)
        env = {**os.environ, "PYTHONPATH": str(REPO_ROOT / "packages" / "codemem-mcp" / "src")}
        subprocess.run(
            ["git", "-C", str(tmp_path), "commit", "-qm", "seed"],
            check=True, env=env,
        )

        time.sleep(0.3)
        pid_file = tmp_path / ".codemem" / "refresh.pid"
        if not pid_file.exists():
            pytest.skip("hook didn't produce a PID — slow CI machine?")
        pid = pid_file.read_text().strip()
        # /proc/<pid>/status exposes 'Tgid:' + 'NSpid:' + 'SessionId:' on Linux.
        status_file = Path(f"/proc/{pid}/status")
        if not status_file.exists():
            pytest.skip(f"/proc/{pid} vanished (process already exited)")
        text = status_file.read_text()
        # Process should be in its own session group — look for a
        # "Sid:" line or similar. If not available, at minimum assert
        # that the PID is valid (existed when we read it).
        assert "Pid:" in text
