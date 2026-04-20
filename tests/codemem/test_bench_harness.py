"""Tests for bench_codemem_vs_aider — M2 Tasks 2.2, 2.4, 2.6.

Scope:
- TestParserSurface / TestParserBehavior / TestParserEdgeCases (Task 2.2/2.3):
  parser API contract against the aider golden fixture.
- TestMeasureOutput (Task 2.4/2.5): tiktoken normalization contract.
- TestHarnessIntegration (Task 2.6): end-to-end pytest-driven CLI run against
  aa-ma-forge. Marked @pytest.mark.slow (skipped by default; run with `-m slow`)
  because aider subprocess takes ~60-120s.

Fixtures:
- tests/codemem/fixtures/aider_repo_map_aa-ma-forge.txt
- tests/codemem/fixtures/codemem_intel_aa-ma-forge.json
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from bench_codemem_vs_aider import (  # noqa: E402
    measure_output,
    parse_aider_output,
)

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


# Project root — tests/codemem/test_bench_harness.py -> parents[2]
_PROJECT_ROOT = Path(__file__).resolve().parents[2]


class TestHarnessIntegration:
    """M2 Task 2.6 — end-to-end integration test.

    Runs the harness as a subprocess against aa-ma-forge itself and asserts
    the JSON output contract. Marked @pytest.mark.slow because aider takes
    60-120s; skipped in the default `pytest` run (pyproject `addopts` has
    `-m 'not perf and not slow'`). Run explicitly with `pytest -m slow`.

    AC#4 (plan): "Test handles known edge case: jCodeMunch may require
    remote fixture (log and skip if unavoidable)". We tolerate jcodemunch
    status ∈ {ok, skipped, error} rather than requiring 'ok' — matches
    AD-012 stub posture at Task 2.5.
    """

    @pytest.mark.slow
    def test_harness_e2e_against_aa_ma_forge(self, tmp_path: Path) -> None:
        out_path = tmp_path / "bench-integration.json"
        result = subprocess.run(
            [
                "uv", "run", "python",
                "scripts/bench_codemem_vs_aider.py",
                "--repo", str(_PROJECT_ROOT),
                "--requested-budget", "1024",
                "--out", str(out_path),
            ],
            cwd=_PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=300,
        )
        assert result.returncode == 0, (
            f"harness failed (exit {result.returncode}): "
            f"stderr={result.stderr[-500:]!r}"
        )
        assert out_path.exists(), f"harness produced no output file: {out_path}"

        data = json.loads(out_path.read_text())

        # AC#3: requested_budget present and correct
        assert data.get("requested_budget") == 1024

        # AC#2: all 3 tools present under tools key
        assert "tools" in data
        assert set(data["tools"].keys()) == {"codemem", "aider", "jcodemunch"}

        # AC#3: overlap key present with all 3 pairs
        assert "overlap" in data
        assert set(data["overlap"].keys()) == {
            "codemem_vs_aider",
            "codemem_vs_jcodemunch",
            "aider_vs_jcodemunch",
        }

        # Each tool measurement has the contract fields
        for tool_name, m in data["tools"].items():
            assert "status" in m, f"{tool_name} missing status"
            assert "raw_bytes" in m, f"{tool_name} missing raw_bytes"
            assert "tiktoken_tokens" in m, f"{tool_name} missing tiktoken_tokens"
            assert "symbol_count" in m, f"{tool_name} missing symbol_count"

        # AC#4: jcodemunch tolerated in ok/skipped/error (currently stub-skipped)
        assert data["tools"]["jcodemunch"]["status"] in {"ok", "skipped", "error"}

        # Sanity: codemem + aider should have produced non-empty output on
        # our own repo — if this fails, the harness itself is broken, not
        # jcodemunch's skip.
        assert data["tools"]["codemem"]["status"] == "ok", (
            f"codemem unexpectedly failed: {data['tools']['codemem']}"
        )
        assert data["tools"]["aider"]["status"] == "ok", (
            f"aider unexpectedly failed: {data['tools']['aider']}"
        )
        assert data["tools"]["codemem"]["symbol_count"] > 0
        assert data["tools"]["aider"]["symbol_count"] > 0
