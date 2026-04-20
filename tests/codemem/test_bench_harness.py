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

# measure_output is Task 2.5 GREEN. During Task 2.4 RED, the import fails and
# the TestMeasureOutput class uses an autouse fixture to fail each test with a
# readable message, WITHOUT breaking collection for the 13 parser tests above.
try:
    from bench_codemem_vs_aider import measure_output  # type: ignore[attr-defined]
except ImportError:
    measure_output = None  # type: ignore[assignment]

FIXTURES_DIR = Path(__file__).parent / "fixtures"
GOLDEN_FIXTURE = FIXTURES_DIR / "aider_repo_map_aa-ma-forge.txt"
CODEMEM_INTEL_FIXTURE = FIXTURES_DIR / "codemem_intel_aa-ma-forge.json"

# Synthetic jCodeMunch MCP response — keeps this TDD RED iteration self-contained.
# Real jCodeMunch MCP round-trip exercised in Task 2.6 (integration test).
JCM_SYNTHETIC_MCP_TEXT = (
    '{"content": [{"type": "text", "text": "ranked context pack:\\n'
    "1. src/codemem/pagerank.py::pagerank_binary_search_budget "
    "(rank=0.142)\\n"
    "2. src/codemem/indexer.py::build_index (rank=0.089)\\n"
    "3. src/codemem/mcp_tools/aa_ma_context.py::aa_ma_context "
    '(rank=0.067)"}]}'
)


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


class TestMeasureOutput:
    """M2 Task 2.4 RED — tiktoken normalization contract.

    Pins the harness measurement helper:
        measure_output(text: str, symbol_count: int) -> dict

    Returned dict MUST populate all 3 keys of the harness output contract
    (reference.md §Harness JSON Output Contract): `raw_bytes`,
    `tiktoken_tokens`, `symbol_count`.

    Why 3 tool-shape tests exist: the AC requires that captured outputs from
    all 3 tools (aider prose, codemem JSON, jCodeMunch MCP) produce a
    comparable integer token count. These tests confirm tiktoken handles
    structurally different input types without error.
    """

    @pytest.fixture(autouse=True)
    def _require_measure_output(self) -> None:
        if measure_output is None:
            pytest.fail(
                "measure_output not yet implemented — Task 2.5 GREEN pending"
            )

    def test_returns_dict_with_three_contract_keys(self) -> None:
        m = measure_output("hello world", symbol_count=0)
        assert set(m.keys()) == {"raw_bytes", "tiktoken_tokens", "symbol_count"}

    def test_empty_text_yields_zero_bytes_zero_tokens(self) -> None:
        m = measure_output("", symbol_count=0)
        assert m["raw_bytes"] == 0
        assert m["tiktoken_tokens"] == 0
        assert m["symbol_count"] == 0

    def test_raw_bytes_equals_utf8_length(self) -> None:
        """raw_bytes must be UTF-8 byte count (not len(text) which is code points)."""
        text = "⋮"  # U+22EE: 3 bytes in UTF-8, 1 code point
        m = measure_output(text, symbol_count=0)
        assert m["raw_bytes"] == 3

    def test_tiktoken_tokens_is_positive_int_for_nonempty_text(self) -> None:
        m = measure_output("def foo(): pass", symbol_count=1)
        assert isinstance(m["tiktoken_tokens"], int)
        assert m["tiktoken_tokens"] > 0

    def test_symbol_count_passthrough(self) -> None:
        m = measure_output("irrelevant", symbol_count=42)
        assert m["symbol_count"] == 42

    def test_aider_prose_fixture_normalizes(self, golden_text: str) -> None:
        """Captured aider output (prose with ⋮ elision) tokenizes cleanly."""
        symbol_count = len(parse_aider_output(golden_text))
        m = measure_output(golden_text, symbol_count=symbol_count)
        assert m["raw_bytes"] == len(golden_text.encode("utf-8"))
        assert m["tiktoken_tokens"] > 0
        assert m["symbol_count"] == symbol_count

    def test_codemem_json_fixture_normalizes(self) -> None:
        """Captured codemem PROJECT_INTEL.json (structured JSON) tokenizes."""
        text = CODEMEM_INTEL_FIXTURE.read_text()
        m = measure_output(text, symbol_count=17)  # 17 = baseline from reference.md
        assert m["raw_bytes"] == len(text.encode("utf-8"))
        assert m["tiktoken_tokens"] > 0
        assert m["symbol_count"] == 17

    def test_jcodemunch_mcp_synthetic_normalizes(self) -> None:
        """Synthetic MCP-shaped JSON tokenizes (real MCP round-trip: Task 2.6)."""
        m = measure_output(JCM_SYNTHETIC_MCP_TEXT, symbol_count=3)
        assert m["raw_bytes"] > 0
        assert m["tiktoken_tokens"] > 0
        assert m["symbol_count"] == 3

    def test_comparable_integers_across_three_tool_shapes(
        self, golden_text: str
    ) -> None:
        """AC core: 3 structurally-different outputs → 3 comparable int token counts.

        Tests that `len(tiktoken.encode(...))` produces an integer regardless
        of input structure (prose/JSON/MCP-wrapper). No ordering assertion —
        just comparability via type + non-negativity.
        """
        aider_tokens = measure_output(golden_text, 0)["tiktoken_tokens"]
        codemem_tokens = measure_output(
            CODEMEM_INTEL_FIXTURE.read_text(), 0
        )["tiktoken_tokens"]
        jcm_tokens = measure_output(JCM_SYNTHETIC_MCP_TEXT, 0)["tiktoken_tokens"]
        for count in (aider_tokens, codemem_tokens, jcm_tokens):
            assert isinstance(count, int)
            assert count >= 0
        # Transitive comparability via int arithmetic
        assert aider_tokens + codemem_tokens + jcm_tokens == sum(
            [aider_tokens, codemem_tokens, jcm_tokens]
        )
