"""Storm test for the codemem post-commit step (M2 Task 2.5; flock design M15.4).

Five rapid ``git commit --amend`` calls: every commit exits 0 in under two
seconds, the queued workers drain, and both sidecars end at the final HEAD.
Serialisation and the start-SHA race are pinned in
``tests/hooks/codemem-post-commit.bats``; graphify is a stub here.
"""

from __future__ import annotations

import os
import subprocess
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
HOOK = REPO_ROOT / "claude-code" / "codemem" / "hooks" / "post-commit.sh"


def _git(
    root: Path, *args: str, env: dict | None = None
) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", str(root), *args],
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )


def _repo(tmp_path: Path) -> tuple[Path, dict]:
    root = tmp_path / "repo"
    root.mkdir()
    stubs = tmp_path / "stubs"
    stubs.mkdir()
    graphify = stubs / "graphify"
    graphify.write_text(
        "#!/usr/bin/env bash\nmkdir -p graphify-out\ngit rev-parse HEAD > graphify-out/graph.json\n"
    )
    graphify.chmod(0o755)
    env = {**os.environ, "PATH": f"{stubs}:/usr/local/bin:/usr/bin:/bin"}
    _git(root, "init", "-q", "-b", "main")
    _git(root, "config", "user.email", "storm@codemem.local")
    _git(root, "config", "user.name", "storm")
    _git(root, "config", "commit.gpgsign", "false")
    (root / ".gitignore").write_text(".codemem/\ngraphify-out/\n")
    (root / "file.py").write_text("def a():\n    return 1\n")
    hook = root / ".git" / "hooks" / "post-commit"
    hook.parent.mkdir(parents=True, exist_ok=True)
    hook.write_text(f'#!/usr/bin/env bash\n"{HOOK}" || true\n')
    hook.chmod(0o755)
    return root, env


def _drained(root: Path, timeout: float = 60.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        r = subprocess.run(
            ["pgrep", "-f", f"post-commit.sh --worker [0-9a-f]* {root}"],
            capture_output=True,
            check=False,
        )
        if r.returncode != 0:
            return True
        time.sleep(0.1)
    return False


def test_five_rapid_amends_exit_zero_fast_and_end_at_head(tmp_path: Path):
    root, env = _repo(tmp_path)
    _git(root, "add", "-A", env=env)
    assert _git(root, "commit", "-qm", "seed", env=env).returncode == 0

    start = time.monotonic()
    for i in range(5):
        (root / "file.py").write_text(f"def a():\n    return {i + 2}\n")
        _git(root, "add", "-A", env=env)
        r = _git(root, "commit", "--amend", "-qm", f"amend-{i}", env=env)
        assert r.returncode == 0, r.stderr
    elapsed = time.monotonic() - start
    assert elapsed < 2.0, f"storm took too long: {elapsed:.2f}s"

    assert _drained(root), "post-commit workers did not drain"
    head = _git(root, "rev-parse", "HEAD").stdout.strip()
    assert (root / ".codemem" / "last_sha").read_text().strip() == head
    assert (root / "graphify-out" / ".built_sha").read_text().strip() == head
