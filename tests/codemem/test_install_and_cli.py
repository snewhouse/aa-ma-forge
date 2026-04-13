"""Tests for M1 Task 1.11 — install integration, CLI, import-linter, post-commit hook."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent.parent


# ---------------------------------------------------------------------
# import-linter contract — AC gate
# ---------------------------------------------------------------------

class TestImportLinterContract:
    def test_contracts_kept(self):
        """Run `lint-imports` against the .importlinter config. Must pass."""
        result = subprocess.run(
            ["uv", "run", "lint-imports"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, (
            f"import-linter failed:\n{result.stdout}\n{result.stderr}"
        )
        assert "Contracts: 2 kept, 0 broken." in result.stdout

    def test_config_file_exists(self):
        cfg = REPO_ROOT / ".importlinter"
        assert cfg.exists(), "import-linter config missing"
        text = cfg.read_text()
        assert "codemem-layers" in text
        assert "parser-is-pure" in text


# ---------------------------------------------------------------------
# Post-commit hook script
# ---------------------------------------------------------------------

class TestPostCommitHook:
    def test_hook_file_exists_and_executable(self):
        hook = REPO_ROOT / "claude-code" / "codemem" / "hooks" / "post-commit.sh"
        assert hook.exists()
        assert os.access(hook, os.X_OK), f"{hook} is not executable"

    def test_hook_exits_zero_on_rebase_action(self, tmp_path):
        """AC: skip during rebase/cherry-pick/merge — don't trigger
        refresh on non-user-initiated commits."""
        hook = REPO_ROOT / "claude-code" / "codemem" / "hooks" / "post-commit.sh"
        env = {**os.environ, "GIT_REFLOG_ACTION": "rebase (continue)"}
        result = subprocess.run(
            ["bash", str(hook)],
            cwd=tmp_path,
            env=env,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0

    def test_hook_exits_zero_outside_git_repo(self, tmp_path):
        """Hook must not crash when run from a non-git directory."""
        hook = REPO_ROOT / "claude-code" / "codemem" / "hooks" / "post-commit.sh"
        # Clear reflog action so we reach the git-rev-parse branch
        env = {k: v for k, v in os.environ.items() if k != "GIT_REFLOG_ACTION"}
        result = subprocess.run(
            ["bash", str(hook)],
            cwd=tmp_path,
            env=env,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0


# ---------------------------------------------------------------------
# install.sh --wire-git-hook
# ---------------------------------------------------------------------

class TestInstallScriptWiring:
    def test_dry_run_flag_accepts_wire_git_hook(self, tmp_path):
        # Accept the new flag without error (in dry-run so no side
        # effects land in ~/.claude/).
        result = subprocess.run(
            ["bash", str(REPO_ROOT / "scripts" / "install.sh"),
             "--dry-run", "--wire-git-hook"],
            capture_output=True,
            text=True,
            env={**os.environ, "HOME": str(tmp_path)},
        )
        # Exit code may be non-zero (Claude-home layout checks may fail
        # in a clean tmp HOME) but the flag parser must not reject
        # --wire-git-hook.
        assert "Unknown flag: --wire-git-hook" not in (result.stderr + result.stdout)


class TestCLI:
    """Smoke-tests for the argparse dispatch layer."""

    def test_help_exits_zero(self):
        result = subprocess.run(
            [sys.executable, "-m", "codemem.cli", "--help"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stderr
        out = result.stdout + result.stderr
        assert "build" in out
        assert "status" in out
        assert "query" in out
        assert "intel" in out

    def test_no_subcommand_errors(self):
        result = subprocess.run(
            [sys.executable, "-m", "codemem.cli"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
        # argparse prints usage and returns non-zero when required
        # subcommand is missing.
        assert result.returncode != 0

    def test_build_status_roundtrip(self, tmp_path):
        # Make a tiny repo and run build + status via the CLI.
        (tmp_path / ".gitignore").write_text(".codemem/\n")
        (tmp_path / "hello.py").write_text("def hello(): return 1\n")
        subprocess.run(["git", "init", "-q", "-b", "main", str(tmp_path)], check=True)
        subprocess.run(
            ["git", "-C", str(tmp_path), "config", "user.email", "t@x"], check=True
        )
        subprocess.run(
            ["git", "-C", str(tmp_path), "config", "user.name", "T"], check=True
        )
        subprocess.run(["git", "-C", str(tmp_path), "add", "-A"], check=True)
        subprocess.run(
            ["git", "-C", str(tmp_path), "commit", "-qm", "i", "--allow-empty"],
            check=True,
        )

        db_path = tmp_path / ".codemem" / "index.db"
        env = {**os.environ, "PYTHONPATH": str(REPO_ROOT / "packages" / "codemem-mcp" / "src")}

        # Build — --db is a global flag (before subcommand).
        r = subprocess.run(
            [sys.executable, "-m", "codemem.cli",
             "--db", str(db_path),
             "build",
             "--repo-root", str(tmp_path),
             "--package", "."],
            capture_output=True,
            text=True,
            env=env,
        )
        assert r.returncode == 0, r.stderr
        assert db_path.exists()

        # Status
        r = subprocess.run(
            [sys.executable, "-m", "codemem.cli", "--db", str(db_path), "status"],
            capture_output=True,
            text=True,
            env=env,
        )
        assert r.returncode == 0, r.stderr
        assert "hello" not in r.stdout  # status prints counts not names
        assert "files:" in r.stdout
        assert "symbols:" in r.stdout

    def test_refresh_is_no_op_m1_placeholder(self, tmp_path):
        r = subprocess.run(
            [sys.executable, "-m", "codemem.cli",
             "--db", str(tmp_path / "x.db"),
             "refresh"],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
        )
        assert r.returncode == 0
        assert "placeholder" in r.stdout.lower() or "m2" in r.stdout.lower()


# ---------------------------------------------------------------------
# Plugin-surface no-bypass (grep-based — supplements import-linter
# since claude-code/codemem/ isn't a Python package)
# ---------------------------------------------------------------------

class TestPluginSurfaceNoBypass:
    def test_mcp_server_only_imports_mcp_tools(self):
        server = REPO_ROOT / "claude-code" / "codemem" / "mcp" / "server.py"
        text = server.read_text()
        # Legal: `from codemem import mcp_tools`
        # Illegal: direct imports of internals
        for forbidden in (
            "from codemem.storage",
            "from codemem.parser",
            "from codemem.indexer",
            "from codemem.resolver",
            "from codemem.pagerank",
            "import codemem.storage",
            "import codemem.parser",
            "import codemem.indexer",
            "import codemem.resolver",
            "import codemem.pagerank",
        ):
            assert forbidden not in text, (
                f"claude-code/codemem/mcp/server.py imports '{forbidden}' "
                f"— must route through codemem.mcp_tools"
            )
