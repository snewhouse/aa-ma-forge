"""Tests for codemem.mcp_tools.aa_ma_context (M3 Task 3.7 — the moat).

AC: validates task against .claude/dev/active/; assembles Markdown
context from filtered hot_spots, owners() of mentioned files,
blast_radius() of mentioned symbols. Extraction rules pinned in
codemem-reference.md §aa_ma_context Extraction Rule.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from codemem.storage import apply_schema, connect, migrate, transaction


FIXTURES = Path(__file__).resolve().parent.parent / "fixtures" / "aa_ma_context"


def _stage_task_dir(repo_root: Path, task_name: str) -> Path:
    """Copy the sample task fixture into a synthetic repo at
    ``<repo>/.claude/dev/active/<task>/`` using the target task name."""
    src_dir = FIXTURES / "sample-task"
    dst_dir = repo_root / ".claude" / "dev" / "active" / task_name
    dst_dir.mkdir(parents=True, exist_ok=True)
    for src_file in src_dir.iterdir():
        # Retarget filenames from sample-task-*.md to <task_name>-*.md
        rel = src_file.name.replace("sample-task", task_name)
        shutil.copy(src_file, dst_dir / rel)
    return dst_dir


@pytest.fixture
def repo_with_task(tmp_path: Path) -> tuple[Path, Path]:
    """A synthetic repo layout with the sample task artifacts staged AND
    the files mentioned in those artifacts actually present on disk so the
    extractor's existence filter passes. Returns (repo_root, db_path)."""
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    _stage_task_dir(repo_root, "sample-task")

    # Files referenced in the fixture must exist for the existence filter.
    (repo_root / "packages" / "sample" / "src").mkdir(parents=True)
    (repo_root / "packages" / "sample" / "src" / "config.py").write_text(
        "def load_config(): pass\n"
    )
    (repo_root / "packages" / "sample" / "src" / "loader.py").write_text(
        "def parse_yaml(text): return None\n"
    )
    # Note: `non-existent.py` and `not_real_path.py` MUST remain absent to
    # prove the existence filter works.

    # DB: index the symbols that appear in reference.md so the symbol-name
    # filter has something to match.
    db_path = tmp_path / "ctx.db"
    conn = connect(db_path)
    apply_schema(conn)
    migrate(conn)
    with transaction(conn):
        conn.execute(
            "INSERT INTO files (path, lang, last_indexed) VALUES ('packages/sample/src/config.py', 'python', 0)"
        )
        conn.execute(
            "INSERT INTO files (path, lang, last_indexed) VALUES ('packages/sample/src/loader.py', 'python', 0)"
        )
        # load_config in config.py, parse_yaml in loader.py
        conn.execute(
            "INSERT INTO symbols (file_id, scip_id, name, kind, line) "
            "VALUES (1, 'scip-config', 'load_config', 'function', 1)"
        )
        conn.execute(
            "INSERT INTO symbols (file_id, scip_id, name, kind, line) "
            "VALUES (2, 'scip-loader', 'parse_yaml', 'function', 1)"
        )
    conn.close()
    return repo_root, db_path


class TestFunctionSurface:
    def test_importable(self) -> None:
        from codemem.mcp_tools import aa_ma_context  # noqa: F401

    def test_callable(self) -> None:
        from codemem.mcp_tools import aa_ma_context

        assert callable(aa_ma_context)


class TestExtraction:
    def test_unknown_task_returns_error(self, tmp_path: Path) -> None:
        from codemem.mcp_tools import aa_ma_context

        repo_root = tmp_path / "r"
        (repo_root / ".claude" / "dev" / "active").mkdir(parents=True)
        db_path = tmp_path / "x.db"
        conn = connect(db_path)
        apply_schema(conn)
        migrate(conn)
        conn.close()
        result = aa_ma_context(db_path, "does-not-exist", repo_root=repo_root)
        assert result["error"] is not None
        assert "not found" in result["error"].lower()

    def test_file_existence_filter(self, repo_with_task) -> None:
        """`non-existent.py` / `not_real_path.py` are in the fixture but
        MUST be filtered out because they don't exist on disk."""
        from codemem.mcp_tools import aa_ma_context

        repo_root, db_path = repo_with_task
        result = aa_ma_context(db_path, "sample-task", repo_root=repo_root)
        mentioned = set(result["files"])
        assert "packages/sample/src/config.py" in mentioned
        assert "packages/sample/src/loader.py" in mentioned
        # These backticked strings appear in the fixture but aren't real files.
        assert "non-existent.py" not in mentioned
        assert "not_real_path.py" not in mentioned

    def test_symbol_name_filter(self, repo_with_task) -> None:
        """`load_config` / `parse_yaml` are in DB so they surface;
        bare words `True`, `None`, `string` must NOT appear as symbols."""
        from codemem.mcp_tools import aa_ma_context

        repo_root, db_path = repo_with_task
        result = aa_ma_context(db_path, "sample-task", repo_root=repo_root)
        syms = set(result["symbols"])
        assert "load_config" in syms
        assert "parse_yaml" in syms
        assert "True" not in syms
        assert "None" not in syms
        assert "string" not in syms


class TestMarkdownAssembly:
    def test_markdown_contains_file_and_symbol_sections(self, repo_with_task) -> None:
        from codemem.mcp_tools import aa_ma_context

        repo_root, db_path = repo_with_task
        result = aa_ma_context(db_path, "sample-task", repo_root=repo_root)
        md = result["markdown"]
        assert "## Files mentioned" in md
        assert "## Symbols mentioned" in md
        assert "packages/sample/src/config.py" in md
        assert "load_config" in md

    def test_owners_and_blast_radius_called_for_entries(self, repo_with_task) -> None:
        """Every mentioned file should have an ``owners`` entry in the payload
        (may be empty if no cached ownership), and every symbol should have a
        ``blast_radius`` entry. The payload is the source-of-truth; markdown
        is a rendering of it."""
        from codemem.mcp_tools import aa_ma_context

        repo_root, db_path = repo_with_task
        result = aa_ma_context(db_path, "sample-task", repo_root=repo_root)
        assert set(result["owners_by_file"].keys()) == set(result["files"])
        assert set(result["blast_radius_by_symbol"].keys()) == set(result["symbols"])


class TestWriteMode:
    def test_write_appends_to_reference(self, repo_with_task) -> None:
        from codemem.mcp_tools import aa_ma_context

        repo_root, db_path = repo_with_task
        ref_path = (
            repo_root
            / ".claude"
            / "dev"
            / "active"
            / "sample-task"
            / "sample-task-reference.md"
        )
        before = ref_path.read_text()
        aa_ma_context(db_path, "sample-task", repo_root=repo_root, write=True)
        after = ref_path.read_text()
        assert after.startswith(before)
        assert "## aa_ma_context snapshot" in after


class TestLinkedTaskFiles:
    """§6.8 re-run 1: a committed link in the task path must not be read or appended to."""

    def test_a_linked_reference_md_is_never_appended_to(
        self, repo_with_task, tmp_path
    ) -> None:
        from codemem.mcp_tools import aa_ma_context

        repo_root, db_path = repo_with_task
        victim = tmp_path / "victim-rc"
        victim.write_text("precious\n")
        ref = repo_root / ".claude/dev/active/sample-task/sample-task-reference.md"
        ref.unlink()
        ref.symlink_to(victim)
        r = aa_ma_context(db_path, "sample-task", repo_root=repo_root, write=True)
        assert r["error"] and "symlink" in r["error"]
        assert victim.read_text() == "precious\n"

    def test_a_linked_task_dir_is_refused(self, repo_with_task, tmp_path) -> None:
        from codemem.mcp_tools import aa_ma_context

        repo_root, db_path = repo_with_task
        active = repo_root / ".claude/dev/active"
        elsewhere = tmp_path / "elsewhere"
        (active / "sample-task").rename(elsewhere)
        (active / "sample-task").symlink_to(elsewhere)
        before = (elsewhere / "sample-task-reference.md").read_text()
        r = aa_ma_context(db_path, "sample-task", repo_root=repo_root, write=True)
        assert r["error"] and "symlink" in r["error"]
        assert (elsewhere / "sample-task-reference.md").read_text() == before

    def test_file_mentions_never_leave_the_repo(self, repo_with_task, tmp_path) -> None:
        """§6.8 re-run 1 (background review): mentions are repo text; no `..`, absolute or escaping link."""
        from codemem.mcp_tools import aa_ma_context

        repo_root, db_path = repo_with_task
        (tmp_path / "outside.py").write_text("x = 1\n")
        (repo_root / "escape.py").symlink_to(tmp_path / "outside.py")
        ref = repo_root / ".claude/dev/active/sample-task/sample-task-reference.md"
        with ref.open("a") as fh:
            fh.write(f"\n`../outside.py` `{tmp_path}/outside.py` `escape.py`\n")
        files = aa_ma_context(db_path, "sample-task", repo_root=repo_root)["files"]
        assert not [f for f in files if "outside" in f or f == "escape.py"]


class TestCalleeCount:
    """Carried defect 1 (M10.2): the per-symbol count read ``callees`` from a
    ``blast_radius`` payload keyed ``downstream``, so it was always 0."""

    def test_callee_count_is_non_zero_for_a_symbol_with_callees(
        self, repo_with_task
    ) -> None:
        from codemem.mcp_tools import aa_ma_context

        repo_root, db_path = repo_with_task
        conn = connect(db_path)
        with transaction(conn):
            # load_config (symbol 1) calls parse_yaml (symbol 2).
            conn.execute(
                "INSERT INTO edges (src_symbol_id, dst_symbol_id, kind) "
                "VALUES (1, 2, 'call')"
            )
        conn.close()

        result = aa_ma_context(db_path, "sample-task", repo_root=repo_root)
        assert "`load_config` (blast-radius: 1 downstream)" in result["markdown"]
        entry = result["blast_radius_by_symbol"]["load_config"]
        assert [c["name"] for c in entry["callees"]] == ["parse_yaml"]
