"""Tests for M1 Task 1.11 — install integration, CLI, import-linter, post-commit hook."""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest


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
        # Named contracts + "0 broken", never the total: a total breaks on every
        # unrelated contract added elsewhere (diagram-generation M2 did exactly that).
        assert re.search(r"\b0 broken", result.stdout), result.stdout
        for name in (
            "codemem layered architecture",
            "parser must not depend on public API",
            "aa_ma never imports codemem",  # diagram-generation M2, ADR-0014
        ):
            assert any(
                name in line and "KEPT" in line for line in result.stdout.splitlines()
            ), result.stdout

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

    def test_refresh_commits_populates_git_mining_cache(self, tmp_path):
        """RED → GREEN gate for L-254 fix: ``codemem refresh-commits``
        must populate ``commits`` + ``commit_files`` from ``git log``.

        The default ``codemem refresh`` is an M2 placeholder and does NOT
        populate the git-mining cache, so out of the box ``co_changes`` /
        ``hot_spots`` / cached portions of ``owners``+``symbol_history``
        return empty until a production code path runs
        ``GitMiner.refresh_commits_cache``. This test pins that path.
        """
        import sqlite3

        # Tiny git repo with two commits → ``git log`` returns rows.
        # Hermetic env: no host gitconfig leakage, no global/system hooks.
        hermetic = {
            **os.environ,
            "HOME": str(tmp_path),
            "GIT_CONFIG_GLOBAL": "/dev/null",
            "GIT_CONFIG_SYSTEM": "/dev/null",
        }
        (tmp_path / ".gitignore").write_text(".codemem/\n")
        (tmp_path / "a.py").write_text("def a(): return 1\n")
        subprocess.run(
            ["git", "init", "-q", "-b", "main", str(tmp_path)],
            check=True, env=hermetic,
        )
        subprocess.run(
            ["git", "-C", str(tmp_path), "config", "user.email", "t@x"],
            check=True, env=hermetic,
        )
        subprocess.run(
            ["git", "-C", str(tmp_path), "config", "user.name", "T"],
            check=True, env=hermetic,
        )
        subprocess.run(
            ["git", "-C", str(tmp_path), "add", "-A"], check=True, env=hermetic,
        )
        subprocess.run(
            ["git", "-C", str(tmp_path), "commit", "-qm", "first"],
            check=True, env=hermetic,
        )
        (tmp_path / "b.py").write_text("def b(): return 2\n")
        subprocess.run(
            ["git", "-C", str(tmp_path), "add", "-A"], check=True, env=hermetic,
        )
        subprocess.run(
            ["git", "-C", str(tmp_path), "commit", "-qm", "second"],
            check=True, env=hermetic,
        )

        db_path = tmp_path / ".codemem" / "index.db"
        env = {
            **hermetic,
            "PYTHONPATH": str(REPO_ROOT / "packages" / "codemem-mcp" / "src"),
        }

        # Build → DB exists at v2 but commits cache empty.
        r = subprocess.run(
            [sys.executable, "-m", "codemem.cli", "--db", str(db_path),
             "build", "--repo-root", str(tmp_path), "--package", "."],
            capture_output=True, text=True, env=env, cwd=tmp_path,
        )
        assert r.returncode == 0, r.stderr

        conn = sqlite3.connect(db_path)
        try:
            assert conn.execute("SELECT COUNT(*) FROM commits").fetchone()[0] == 0
            assert conn.execute(
                "SELECT COUNT(*) FROM commit_files"
            ).fetchone()[0] == 0
        finally:
            conn.close()

        # refresh-commits → cache populated.
        r = subprocess.run(
            [sys.executable, "-m", "codemem.cli", "--db", str(db_path),
             "refresh-commits", "--repo-root", str(tmp_path)],
            capture_output=True, text=True, env=env, cwd=tmp_path,
        )
        assert r.returncode == 0, r.stderr
        assert "inserted" in r.stdout.lower()

        conn = sqlite3.connect(db_path)
        try:
            n_commits = conn.execute("SELECT COUNT(*) FROM commits").fetchone()[0]
            n_files = conn.execute(
                "SELECT COUNT(*) FROM commit_files"
            ).fetchone()[0]
        finally:
            conn.close()
        assert n_commits == 2, f"expected 2 commits cached, got {n_commits}"
        assert n_files >= 2, f"expected >=2 commit_files rows, got {n_files}"


# ---------------------------------------------------------------------
# `codemem query` round-trips on a fixture index (codebase-analysis-skills M2 AC7)
# ---------------------------------------------------------------------

QUERY_TOOLS_PINNED = [
    "who_calls",
    "blast_radius",
    "dead_code",
    "dependency_chain",
    "search_symbols",
    "file_summary",
    "hot_spots",
    "co_changes",
    "owners",
    "layers",
]


def _cli(*args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    env = {
        **os.environ,
        "PYTHONPATH": str(REPO_ROOT / "packages" / "codemem-mcp" / "src"),
    }
    return subprocess.run(
        [sys.executable, "-m", "codemem.cli", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        env=env,
    )


@pytest.fixture(scope="module")
def indexed_repo(tmp_path_factory) -> tuple[Path, Path]:
    """a.py calls b.helper; a.py and notes.md change together 3 times (no import edge between them)."""
    repo = tmp_path_factory.mktemp("q") / "repo"
    repo.mkdir()
    genv = {
        **os.environ,
        "GIT_AUTHOR_NAME": "F",
        "GIT_AUTHOR_EMAIL": "f@example.invalid",
        "GIT_COMMITTER_NAME": "F",
        "GIT_COMMITTER_EMAIL": "f@example.invalid",
    }

    def git(*a: str) -> None:
        subprocess.run(
            ["git", "-C", str(repo), *a], check=True, capture_output=True, env=genv
        )

    git("init", "-q")
    (repo / "b.py").write_text("def helper():\n    return 1\n")
    for i in range(3):
        (repo / "a.py").write_text(
            f"from b import helper\n\ndef main():\n    return helper() + {i}\n"
        )
        (repo / "notes.md").write_text(f"v{i}\n")
        git("add", "-A")
        git("commit", "-q", "-m", f"c{i}")
    db = repo.parent / "index.db"
    for step in (
        ("build", "--repo-root", str(repo)),
        ("refresh-commits", "--repo-root", str(repo)),
    ):
        r = _cli("--db", str(db), *step, cwd=repo)
        assert r.returncode == 0, r.stderr
    return repo, db


class TestQueryRoundTrips:
    def test_who_calls(self, indexed_repo):
        repo, db = indexed_repo
        r = _cli("--db", str(db), "query", "who_calls", "helper", cwd=repo)
        assert r.returncode == 0, r.stderr
        assert "main" in json.dumps(json.loads(r.stdout))

    def test_hot_spots(self, indexed_repo):
        repo, db = indexed_repo
        r = _cli("--db", str(db), "query", "hot_spots", cwd=repo)
        assert r.returncode == 0, r.stderr
        assert "a.py" in {f["path"] for f in json.loads(r.stdout)["files"]}

    def test_co_changes(self, indexed_repo):
        repo, db = indexed_repo
        r = _cli("--db", str(db), "query", "co_changes", "a.py", cwd=repo)
        assert r.returncode == 0, r.stderr
        assert "notes.md" in {f["path"] for f in json.loads(r.stdout)["files"]}

    def test_owners_with_repo_root_computes_blame(self, indexed_repo):
        repo, db = indexed_repo
        r = _cli(
            "--db",
            str(db),
            "query",
            "owners",
            "a.py",
            "--repo-root",
            str(repo),
            cwd=repo,
        )
        assert r.returncode == 0, r.stderr
        assert [a["line_count"] for a in json.loads(r.stdout)["authors"]] == [4]

    def test_layers(self, indexed_repo):
        repo, db = indexed_repo
        r = _cli("--db", str(db), "query", "layers", cwd=repo)
        assert r.returncode == 0, r.stderr
        assert set(json.loads(r.stdout)["layers"]) == {"core", "middle", "periphery"}

    def test_query_exposes_exactly_ten_tools(self, indexed_repo):
        repo, _ = indexed_repo
        r = _cli("query", "--help", cwd=repo)
        assert r.returncode == 0
        assert re.search(r"\{([a-z_,]+)\}", r.stdout).group(1).split(",") == QUERY_TOOLS_PINNED
        assert "10 MCP tools" in _cli("--help", cwd=repo).stdout


QUERY_DOCS = [
    "claude-code/codemem/README.md",
    "claude-code/codemem/commands/codemem.md",
    "docs/codemem/migration-from-index.md",
    "packages/codemem-mcp/src/codemem/cli.py",
]


def test_query_tool_counts_in_docs_match_the_cli() -> None:
    """Every "N of the MCP tools" / "one of N MCP tools" claim equals the CLI's query choices."""
    from codemem.cli import QUERY_TOOLS

    claims = [
        (rel, int(n))
        for rel in QUERY_DOCS
        for n in re.findall(
            r"\b(\d+) of the MCP tools\b|\bone of (\d+) MCP tools\b",
            (REPO_ROOT / rel).read_text(encoding="utf-8"),
        )
        for n in n
        if n
    ]
    assert {rel for rel, _ in claims} == set(QUERY_DOCS), claims
    assert [c for c in claims if c[1] != len(QUERY_TOOLS)] == []
    assert list(QUERY_TOOLS) == QUERY_TOOLS_PINNED


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
