"""Tests for bench_codemem_vs_aider Aider prose parser — M2 Task 2.2 (TDD RED).

AC (per codemem-token-benchmarks-tasks.md M2.2):
- Parser extracts (file, symbol_name, kind) rows from Aider `--show-repo-map` prose.
- Golden fixture: tests/codemem/fixtures/aider_repo_map_aa-ma-forge.txt
  (captured 2026-04-20 @ aa-ma-forge HEAD af10ec6 via aider 0.86.2
   `aider --show-repo-map --map-tokens 1024`).
- Kinds present in fixture: def, class, @ (decorator).
- Aider preamble (lines 1-10) is CLI metadata and must be skipped.

Expected RED: ModuleNotFoundError on `bench_codemem_vs_aider` until Task 2.3 GREEN
implements scripts/bench_codemem_vs_aider.py with parse_aider_output.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from bench_codemem_vs_aider import parse_aider_output  # noqa: E402

FIXTURES_DIR = Path(__file__).parent / "fixtures"
GOLDEN_FIXTURE = FIXTURES_DIR / "aider_repo_map_aa-ma-forge.txt"


@pytest.fixture(scope="module")
def golden_text() -> str:
    assert GOLDEN_FIXTURE.exists(), f"Golden fixture missing: {GOLDEN_FIXTURE}"
    return GOLDEN_FIXTURE.read_text()


class TestParserSurface:
    """Minimal contract: callable, returns list, handles empty input."""

    def test_empty_input_returns_empty_list(self) -> None:
        assert parse_aider_output("") == []

    def test_returns_list_type(self) -> None:
        assert isinstance(parse_aider_output(""), list)


class TestParserBehavior:
    """AC: extract (file, symbol_name, kind) from golden fixture."""

    def test_extracts_at_least_one_row(self, golden_text: str) -> None:
        """Fixture has 59 │def/│class/│@ lines — parser must find ≥1."""
        assert len(parse_aider_output(golden_text)) >= 1

    def test_row_shape_is_3_tuple(self, golden_text: str) -> None:
        for row in parse_aider_output(golden_text):
            assert len(row) == 3, f"expected (file, name, kind), got {row!r}"

    def test_all_fields_are_nonempty_strings(self, golden_text: str) -> None:
        for row in parse_aider_output(golden_text):
            file, name, kind = row
            assert isinstance(file, str) and file, f"bad file: {row!r}"
            assert isinstance(name, str) and name, f"bad name: {row!r}"
            assert isinstance(kind, str) and kind, f"bad kind: {row!r}"

    def test_extracts_def_kind(self, golden_text: str) -> None:
        """Fixture contains `│def` markers — parser must emit ≥1 'def' row."""
        defs = [r for r in parse_aider_output(golden_text) if r[2] == "def"]
        assert defs, "expected ≥1 'def' row from golden fixture"

    def test_extracts_class_kind(self, golden_text: str) -> None:
        """Fixture contains `│class` markers — parser must emit ≥1 'class' row."""
        classes = [r for r in parse_aider_output(golden_text) if r[2] == "class"]
        assert classes, "expected ≥1 'class' row from golden fixture"

    def test_elision_marker_absent_from_names(self, golden_text: str) -> None:
        """The ⋮ marker signals elision; it must NEVER appear in a symbol name."""
        for _, name, _ in parse_aider_output(golden_text):
            assert "⋮" not in name, f"elision leaked into name: {name!r}"

    def test_file_fields_look_path_like(self, golden_text: str) -> None:
        """Guards against wrapped-signature continuations being mistaken for headers.

        Fixture line 18 `dict:` is a continuation of a line-wrapped `│def` signature.
        A naive `line ends with :` header regex would produce rows with file='dict'.
        """
        known_exts = (".py", ".sh", ".md", ".toml", ".yaml", ".yml", ".json", ".txt")
        for file, _, _ in parse_aider_output(golden_text):
            assert file.endswith(known_exts) or "/" in file, (
                f"file field not path-like: {file!r}"
            )

    def test_no_preamble_leakage(self, golden_text: str) -> None:
        """Aider preamble (v0.86.2, Model, Git repo, Repo-map, etc.) is not symbols."""
        names = {name for _, name, _ in parse_aider_output(golden_text)}
        forbidden = {"Aider", "Model", "Repo-map", "Git", "Using"}
        leaked = names & forbidden
        assert not leaked, f"preamble leaked into rows: {leaked}"


class TestParserEdgeCases:
    """Targeted single-behaviour tests against synthetic minimal inputs."""

    def test_minimal_single_def(self) -> None:
        text = "foo.py:\n⋮\n│def bar():\n⋮\n"
        assert ("foo.py", "bar", "def") in parse_aider_output(text)

    def test_minimal_single_class(self) -> None:
        text = "foo.py:\n⋮\n│class Bar:\n⋮\n"
        assert ("foo.py", "Bar", "class") in parse_aider_output(text)

    def test_only_elision_yields_no_rows(self) -> None:
        """File header + elision alone (no │def/│class/│@) produces no rows."""
        assert parse_aider_output("foo.py:\n⋮\n") == []
