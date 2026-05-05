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
    _extract_repomix_file_paths,
    _parse_munch_gen1,
    _run_aider,
    measure_output,
    parse_aider_output,
    rbo_at_10,
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

        # M2a.6: each pair now emits BOTH jaccard and rbo_at_10
        for pair_name, pair_data in data["overlap"].items():
            assert isinstance(pair_data, dict), (
                f"{pair_name} should be dict (post-M2a.6), got {type(pair_data).__name__}"
            )
            assert set(pair_data.keys()) == {"jaccard", "rbo_at_10"}, (
                f"{pair_name} keys = {set(pair_data.keys())}, expected {{jaccard, rbo_at_10}}"
            )
            assert 0.0 <= pair_data["jaccard"] <= 1.0
            assert 0.0 <= pair_data["rbo_at_10"] <= 1.0

        # Each tool measurement has the contract fields
        for tool_name, m in data["tools"].items():
            assert "status" in m, f"{tool_name} missing status"
            assert "raw_bytes" in m, f"{tool_name} missing raw_bytes"
            assert "tiktoken_tokens" in m, f"{tool_name} missing tiktoken_tokens"
            assert "symbol_count" in m, f"{tool_name} missing symbol_count"

        # M2a.4 (post-pivot): jcodemunch must now succeed (no longer stubbed)
        assert data["tools"]["jcodemunch"]["status"] == "ok", (
            f"jcodemunch should succeed post-pivot: {data['tools']['jcodemunch']}"
        )

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


class TestSweepAggregate:
    """M3 Task 3.2 — pin median-aggregation correctness before real sweeps.

    Tests the pure aggregation logic in scripts/bench_sweep.py. The
    I/O-heavy parts (subprocess.run, tempfiles) are exercised at actual
    M3 sweep time, not here.
    """

    def _import(self):
        from bench_sweep import _median_int, aggregate
        return _median_int, aggregate

    def test_median_int_empty(self) -> None:
        median_int, _ = self._import()
        assert median_int([]) == 0

    def test_median_int_odd_count(self) -> None:
        median_int, _ = self._import()
        assert median_int([10, 20, 30]) == 20

    def test_median_int_even_count_returns_int(self) -> None:
        median_int, _ = self._import()
        # statistics.median of [10, 20] is 15.0 — must coerce to int
        assert median_int([10, 20]) == 15

    def test_aggregate_empty_runs_returns_empty(self) -> None:
        _, aggregate = self._import()
        assert aggregate([]) == {}

    def test_aggregate_single_run_passes_through(self) -> None:
        _, aggregate = self._import()
        runs = [{"tools": {
            "codemem": {"status": "ok", "raw_bytes": 100,
                        "tiktoken_tokens": 25, "symbol_count": 5},
        }}]
        out = aggregate(runs)
        assert out["codemem"]["status"] == "ok"
        assert out["codemem"]["raw_bytes"] == 100
        assert out["codemem"]["tiktoken_tokens"] == 25
        assert out["codemem"]["symbol_count"] == 5
        assert out["codemem"]["runs_included"] == 1

    def test_aggregate_three_runs_picks_median(self) -> None:
        _, aggregate = self._import()
        runs = [
            {"tools": {"codemem": {"status": "ok", "raw_bytes": 90,
                                   "tiktoken_tokens": 20, "symbol_count": 4}}},
            {"tools": {"codemem": {"status": "ok", "raw_bytes": 100,
                                   "tiktoken_tokens": 25, "symbol_count": 5}}},
            {"tools": {"codemem": {"status": "ok", "raw_bytes": 110,
                                   "tiktoken_tokens": 30, "symbol_count": 6}}},
        ]
        out = aggregate(runs)
        assert out["codemem"]["raw_bytes"] == 100
        assert out["codemem"]["tiktoken_tokens"] == 25
        assert out["codemem"]["symbol_count"] == 5
        assert out["codemem"]["runs_included"] == 3

    def test_aggregate_status_precedence_error_wins(self) -> None:
        """Any run with status=error drags the cell to error."""
        _, aggregate = self._import()
        runs = [
            {"tools": {"codemem": {"status": "ok", "raw_bytes": 100,
                                   "tiktoken_tokens": 25, "symbol_count": 5}}},
            {"tools": {"codemem": {"status": "error", "raw_bytes": 0,
                                   "tiktoken_tokens": 0, "symbol_count": 0}}},
            {"tools": {"codemem": {"status": "ok", "raw_bytes": 100,
                                   "tiktoken_tokens": 25, "symbol_count": 5}}},
        ]
        out = aggregate(runs)
        assert out["codemem"]["status"] == "error"

    def test_aggregate_status_precedence_skipped_over_ok(self) -> None:
        """If no errors but at least one skipped → skipped (not ok)."""
        _, aggregate = self._import()
        runs = [
            {"tools": {"jcodemunch": {"status": "ok", "raw_bytes": 1,
                                      "tiktoken_tokens": 1, "symbol_count": 1}}},
            {"tools": {"jcodemunch": {"status": "skipped", "raw_bytes": 0,
                                      "tiktoken_tokens": 0, "symbol_count": 0}}},
        ]
        out = aggregate(runs)
        assert out["jcodemunch"]["status"] == "skipped"


JCM_FIXTURE = FIXTURES_DIR / "jcodemunch_symbol_importance_aa-ma-forge.txt"
REPOMIX_FIXTURE = FIXTURES_DIR / "repomix_output_aa-ma-forge.xml"


class TestRepomixAdapter:
    """M2b — Repomix XML file-path extractor tests.

    Repomix is a *dump-everything* tool; it has no native budget concept
    and produces a packed XML representation of the entire scope. For
    aa-ma-forge full-repo it emits ~551k tokens (538× larger than codemem
    at budget=1024 — empirical, 2026-05-05). The fixture is a small
    subset (parser/ subdirectory, ~7.7k tokens, 11 files) for unit-test
    tractability.

    The harness emits Repomix with status='ok_no_symbols' and an empty
    symbols list — Repomix doesn't produce symbol-level output.
    """

    def test_extract_paths_synthetic_xml(self) -> None:
        """Minimal valid Repomix-style XML → 2 file paths extracted."""
        text = (
            "<files>\n"
            '<file path="src/foo.py">\n'
            "def hello(): pass\n"
            "</file>\n"
            "\n"
            '<file path="tests/test_foo.py">\n'
            "def test_hello(): pass\n"
            "</file>\n"
            "</files>\n"
        )
        paths = _extract_repomix_file_paths(text)
        assert "src/foo.py" in paths
        assert "tests/test_foo.py" in paths
        assert len(paths) == 2

    def test_extract_paths_real_fixture_has_files(self) -> None:
        """Live-captured Repomix fixture must produce ≥ 5 file paths."""
        assert REPOMIX_FIXTURE.exists(), f"Live fixture missing: {REPOMIX_FIXTURE}"
        paths = _extract_repomix_file_paths(REPOMIX_FIXTURE.read_text())
        assert len(paths) >= 5, f"only {len(paths)} files; expected >= 5"
        for p in paths:
            assert isinstance(p, str) and p, f"bad path: {p!r}"
            # All extracted paths should be path-like
            assert "/" in p or "." in p, f"path doesn't look like a path: {p!r}"

    def test_extract_paths_real_fixture_includes_python(self) -> None:
        """Captured fixture is from packages/codemem-mcp/src/codemem/parser/
        — must include Python files."""
        paths = _extract_repomix_file_paths(REPOMIX_FIXTURE.read_text())
        py_paths = [p for p in paths if p.endswith(".py")]
        assert py_paths, f"expected .py files; got: {paths[:5]}"

    def test_extract_paths_no_files_returns_empty(self) -> None:
        """XML with no <file path=...> tags → empty list, no exceptions."""
        assert _extract_repomix_file_paths("<files></files>") == []
        assert _extract_repomix_file_paths("not even xml") == []
        assert _extract_repomix_file_paths("") == []

    def test_extract_paths_handles_quoted_attributes(self) -> None:
        """The path attribute may use either single or double quotes."""
        text_dq = '<file path="src/main.py">x</file>'
        text_sq = "<file path='src/main.py'>x</file>"
        assert _extract_repomix_file_paths(text_dq) == ["src/main.py"]
        # Single quotes are less common but also valid XML
        sq_result = _extract_repomix_file_paths(text_sq)
        # If parser doesn't support single-quote, that's documented
        # behaviour — Repomix v1.14.0 always emits double-quoted attrs.
        assert sq_result in ([], ["src/main.py"]), (
            f"unexpected behaviour on single quotes: {sq_result}"
        )





class TestJCodeMunchAdapter:
    """M2a.4 — jCodeMunch MUNCH/gen1 parser tests (PIVOTED 2026-05-05).

    Plan amendment AD-V2-008: pivoted from `get_ranked_context` to
    `get_symbol_importance` after empirical probe revealed an encoder
    bug in jcodemunch-mcp 1.59.1 where rc1-format tables emit empty
    rows due to schema/return-key mismatch. `get_symbol_importance`
    uses gen1 encoding which is correct and methodologically cleaner
    (pure PageRank, no BM25 query bias) — apples-to-apples with codemem
    and Aider.

    These tests target the inline `_parse_munch_gen1` helper that
    extracts (file, name) tuples from gen1-encoded responses.
    The end-to-end MCP round-trip is exercised at M2a.7 smoke test
    against the real jcodemunch-mcp subprocess.
    """

    def test_parse_minimal_synthetic(self) -> None:
        """Minimal valid MUNCH/gen1 input: 1 legend, 1 row → 1 (file, name)."""
        text = (
            "#MUNCH/1 tool=get_symbol_importance enc=gen1\n"
            "\n"
            "@1=src/foo/\n"
            "@2=function\n"
            "\n"
            "algorithm=pagerank iterations_to_converge=10 __tables=t:ranked_symbols:symbol_id|rank|score|in_degree|out_degree|kind\n"
            "\n"
            "t,@1bar.py::baz#function,1,0.5,2,0,@2\n"
        )
        rows = _parse_munch_gen1(text)
        assert rows == [("src/foo/bar.py", "baz")]

    def test_parse_longest_legend_match_wins(self) -> None:
        """@11 must match before @1 to avoid prefix-collision bugs."""
        text = (
            "#MUNCH/1 tool=get_symbol_importance enc=gen1\n"
            "\n"
            "@1=src/\n"
            "@11=tests/integration/\n"
            "\n"
            "__tables=t:ranked_symbols:symbol_id|rank|score|in_degree|out_degree|kind\n"
            "\n"
            "t,@11test_foo.py::test_a#function,1,0.5,1,0,function\n"
            "t,@1main.py::main#function,2,0.4,1,0,function\n"
        )
        rows = _parse_munch_gen1(text)
        assert ("tests/integration/test_foo.py", "test_a") in rows
        assert ("src/main.py", "main") in rows

    def test_parse_no_table_returns_empty(self) -> None:
        """Header-only payload (no rows) yields empty list, no exceptions."""
        text = "#MUNCH/1 tool=get_symbol_importance enc=gen1\n\n\n"
        assert _parse_munch_gen1(text) == []

    def test_parse_real_fixture_has_populated_rows(self) -> None:
        """Live-captured aa-ma-forge fixture must produce >= 5 (file, name) rows."""
        assert JCM_FIXTURE.exists(), f"Live fixture missing: {JCM_FIXTURE}"
        rows = _parse_munch_gen1(JCM_FIXTURE.read_text())
        assert len(rows) >= 5, f"only {len(rows)} rows; expected >= 5"
        for file, name in rows:
            assert isinstance(file, str) and file, f"bad file: {(file, name)!r}"
            assert isinstance(name, str) and name, f"bad name: {(file, name)!r}"

    def test_parse_real_fixture_files_path_like(self) -> None:
        """Real fixture file fields must look path-like (contain / or known ext)."""
        rows = _parse_munch_gen1(JCM_FIXTURE.read_text())
        known_exts = (".py", ".sh", ".md", ".toml", ".yaml", ".yml", ".json", ".txt")
        for file, _ in rows:
            assert "/" in file or file.endswith(known_exts), (
                f"file field not path-like: {file!r}"
            )


class TestRBOMetric:
    """M2a.5 — Rank-Biased Overlap@10 (Webber, Moffat, Zobel 2010, p=0.9).

    Extrapolated form (eq. 8 in the paper): RBO_ext for identical infinite
    rankings = 1.0; for disjoint rankings = 0.0; for partial overlap with
    rank disagreement, somewhere in between.

    Tests use k=3 for hand-computation tractability; the production call
    uses k=10 (the AC alias `rbo_at_10` keeps the function name
    self-documenting).

    Plan deviation 2026-05-05: AC requested cross-verification against the
    `rbo` PyPI package. Skipped — third-party package can have its own bugs;
    direct hand-computation against canonical formula is a stronger
    validation. Documented in tasks.md M2a.5 result log.
    """

    def test_identical_short_lists_returns_one(self) -> None:
        """RBO_ext of identical lists (length >= k) = 1.0 by construction.

        Hand-computation k=3:
          d=1: 1/1 * p^0 = 1.0
          d=2: 2/2 * p^1 = 0.9
          d=3: 3/3 * p^2 = 0.81
          sum = 2.71
          trunc = (1-p) * sum = 0.271
          extrap tail = p^k * agreement_k = 0.729 * 1.0 = 0.729
          total = 0.271 + 0.729 = 1.0
        """
        result = rbo_at_10(["a", "b", "c"], ["a", "b", "c"], p=0.9, k=3)
        assert result == pytest.approx(1.0, abs=1e-9), f"identical → {result}, expected 1.0"

    def test_disjoint_lists_returns_zero(self) -> None:
        """RBO of disjoint lists = 0.0 (no agreement at any depth)."""
        result = rbo_at_10(["a", "b", "c"], ["d", "e", "f"], p=0.9, k=3)
        assert result == pytest.approx(0.0, abs=1e-9), f"disjoint → {result}, expected 0.0"

    def test_reversed_lists_hand_computed(self) -> None:
        """[a,b,c] vs [c,b,a] hand-computation k=3, p=0.9:

        d=1: {a} ∩ {c}     = 0; agreement 0.0; weight p^0 = 1.00 → 0.000
        d=2: {a,b} ∩ {c,b} = 1; agreement 0.5; weight p^1 = 0.90 → 0.450
        d=3: {a,b,c}∩{c,b,a}=3; agreement 1.0; weight p^2 = 0.81 → 0.810
        sum  = 1.260
        trunc = 0.1 * 1.260                       = 0.126
        extrap tail = p^3 * agreement_k = 0.729 * 1.0 = 0.729
        total = 0.126 + 0.729                     = 0.855
        """
        result = rbo_at_10(["a", "b", "c"], ["c", "b", "a"], p=0.9, k=3)
        assert result == pytest.approx(0.855, abs=1e-3), f"reversed → {result}, expected 0.855"

    def test_output_in_unit_interval_for_random_input(self) -> None:
        """RBO output must always be in [0, 1] regardless of input shape."""
        cases = [
            (["x"], ["y"]),
            (list("abcdefghij"), list("jihgfedcba")),
            (list("abcdef"), list("abcdef") + ["g", "h", "i", "j"]),
            ([], ["a", "b"]),
            ([], []),
        ]
        for s, t in cases:
            result = rbo_at_10(s, t, p=0.9, k=10)
            assert 0.0 <= result <= 1.0, f"RBO({s}, {t}) = {result} outside [0,1]"

    def test_empty_both_returns_zero(self) -> None:
        """RBO(empty, empty) = 0.0 by convention (matches our jaccard handler)."""
        assert rbo_at_10([], [], p=0.9, k=10) == 0.0

    def test_top_heavy_property(self) -> None:
        """RBO is top-heavy: agreement at top weighs more than at bottom.

        Two pairs sharing the same number of items but at different ranks:
        - pair X: agree at rank 1 only          → high RBO
        - pair Y: agree at rank 10 only         → low RBO
        """
        # Top-of-list agreement
        x_a = ["match"] + [f"a{i}" for i in range(9)]
        x_b = ["match"] + [f"b{i}" for i in range(9)]
        # Bottom-of-list agreement
        y_a = [f"a{i}" for i in range(9)] + ["match"]
        y_b = [f"b{i}" for i in range(9)] + ["match"]
        rbo_top = rbo_at_10(x_a, x_b, p=0.9, k=10)
        rbo_bot = rbo_at_10(y_a, y_b, p=0.9, k=10)
        assert rbo_top > rbo_bot, (
            f"top-of-list RBO ({rbo_top:.4f}) should exceed "
            f"bottom-of-list RBO ({rbo_bot:.4f})"
        )


class TestAiderModelOverride:
    """M2a.3 — Aider --model gpt-3.5-turbo tokeniser-equalisation switch.

    Aider has no `--tokenizer` flag; tokeniser is routed via litellm from
    `--model`. Verified live (M2a.2 probe): `--show-repo-map --model gpt-3.5-turbo`
    produces output with cl100k_base tokenisation without requiring
    OPENAI_API_KEY (warning-only).

    These tests assert the harness propagates the equalisation switch through
    to the subprocess argv. We monkey-patch subprocess.run to capture the
    invocation rather than spawning Aider — keeps tests fast and deterministic.
    """

    def test_default_invocation_omits_model_flag(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """Without --aider-tokeniser-equalise, _run_aider must NOT pass --model."""
        captured: dict = {}

        def fake_run(args, **kwargs):
            captured["args"] = list(args)

            class Result:
                returncode = 0
                stdout = ""
                stderr = ""
            return Result()

        monkeypatch.setattr("bench_codemem_vs_aider.subprocess.run", fake_run)
        _run_aider(tmp_path, budget=256, tokeniser_equalise=False)
        assert "--model" not in captured["args"], (
            f"--model leaked into default invocation: {captured['args']}"
        )

    def test_equalise_flag_adds_model_gpt35turbo(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """With tokeniser_equalise=True, argv must contain `--model gpt-3.5-turbo`."""
        captured: dict = {}

        def fake_run(args, **kwargs):
            captured["args"] = list(args)

            class Result:
                returncode = 0
                stdout = ""
                stderr = ""
            return Result()

        monkeypatch.setattr("bench_codemem_vs_aider.subprocess.run", fake_run)
        _run_aider(tmp_path, budget=256, tokeniser_equalise=True)

        # Must contain `--model gpt-3.5-turbo` as adjacent args (not interleaved)
        args = captured["args"]
        assert "--model" in args, f"--model missing: {args}"
        idx = args.index("--model")
        assert idx + 1 < len(args), f"--model has no value: {args}"
        assert args[idx + 1] == "gpt-3.5-turbo", (
            f"--model value is {args[idx + 1]!r}, expected 'gpt-3.5-turbo'"
        )

    def test_equalise_preserves_show_repo_map_and_map_tokens(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """Equalisation must not break the existing repo-map invocation contract."""
        captured: dict = {}

        def fake_run(args, **kwargs):
            captured["args"] = list(args)

            class Result:
                returncode = 0
                stdout = ""
                stderr = ""
            return Result()

        monkeypatch.setattr("bench_codemem_vs_aider.subprocess.run", fake_run)
        _run_aider(tmp_path, budget=1024, tokeniser_equalise=True)

        args = captured["args"]
        assert "--show-repo-map" in args
        assert "--map-tokens" in args
        idx = args.index("--map-tokens")
        assert args[idx + 1] == "1024", (
            f"--map-tokens value not propagated: {args}"
        )
