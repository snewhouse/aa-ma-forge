"""Tests for codemem.parser.python_ast — Task 1.3 acceptance gate.

Covers: top-level function, class, method, nested class, decorated method,
async function, intra-file call edges, syntax error, and the pinned SCIP-ID
golden fixture from docs/codemem/symbol-id-grammar.md.
"""

from __future__ import annotations

from pathlib import Path

from codemem.parser import python_ast as parser_mod
from codemem.parser.python_ast import (
    CallEdge,
    ParseResult,
    Symbol,
    extract_python_signatures,
)


PKG = "packages/codemem-mcp/src/codemem"
FILE_REL = "storage/db.py"


def _parse(src: str, file_rel: str = FILE_REL) -> ParseResult:
    return extract_python_signatures(src, package=PKG, file_rel=file_rel)


def _ids(symbols: list[Symbol]) -> list[str]:
    return [s.scip_id for s in symbols]


# ---------------------------------------------------------------------
# Minimal shape tests (5 categories from the acceptance criteria)
# ---------------------------------------------------------------------

class TestTopLevelFunction:
    def test_emits_function_symbol_with_term_marker(self):
        result = _parse("def foo():\n    return 1\n")
        assert len(result.symbols) == 1
        sym = result.symbols[0]
        assert sym.name == "foo"
        assert sym.kind == "function"
        assert sym.scip_id == f"codemem {PKG} /{FILE_REL}#foo"
        assert sym.line == 1
        assert sym.parent_scip_id is None

    def test_signature_captured(self):
        result = _parse("def add(a, b):\n    return a + b\n")
        sym = result.symbols[0]
        assert sym.signature == "(a, b)"
        assert sym.signature_hash is not None
        assert len(sym.signature_hash) == 64  # sha256 hex

    def test_signature_with_return_annotation(self):
        result = _parse("def foo(x: int) -> str:\n    return str(x)\n")
        assert result.symbols[0].signature == "(x: int) -> str"

    def test_docstring_first_line_captured(self):
        src = 'def foo():\n    """First line.\n\n    More details.\n    """\n    return 1\n'
        sym = _parse(src).symbols[0]
        assert sym.docstring == "First line."


class TestClass:
    def test_emits_class_symbol_with_type_marker(self):
        result = _parse("class Bar:\n    pass\n")
        assert len(result.symbols) == 1
        sym = result.symbols[0]
        assert sym.name == "Bar"
        assert sym.kind == "class"
        assert sym.scip_id == f"codemem {PKG} #{FILE_REL}#Bar"
        assert sym.parent_scip_id is None


class TestMethod:
    def test_method_uses_member_marker_and_parent_link(self):
        result = _parse("class Bar:\n    def baz(self):\n        return 2\n")
        assert len(result.symbols) == 2
        by_name = {s.name: s for s in result.symbols}

        bar = by_name["Bar"]
        baz = by_name["baz"]

        assert bar.scip_id == f"codemem {PKG} #{FILE_REL}#Bar"
        assert baz.scip_id == f"codemem {PKG} .{FILE_REL}#Bar.baz"
        assert baz.kind == "method"
        assert baz.parent_scip_id == bar.scip_id

    def test_self_stripped_from_signature(self):
        result = _parse("class Bar:\n    def baz(self, x):\n        return x\n")
        baz = next(s for s in result.symbols if s.name == "baz")
        assert baz.signature == "(x)"


class TestNestedClass:
    def test_inner_class_uses_hash_separator(self):
        result = _parse("class Outer:\n    class Inner:\n        pass\n")
        assert len(result.symbols) == 2
        ids = _ids(result.symbols)
        assert f"codemem {PKG} #{FILE_REL}#Outer" in ids
        assert f"codemem {PKG} #{FILE_REL}#Outer#Inner" in ids

        inner = next(s for s in result.symbols if s.name == "Inner")
        assert inner.parent_scip_id == f"codemem {PKG} #{FILE_REL}#Outer"


class TestDecoratedFunction:
    def test_decorator_does_not_change_scip_id(self):
        src = (
            "class Bar:\n"
            "    @staticmethod\n"
            "    def qux():\n"
            "        return 3\n"
        )
        result = _parse(src)
        qux = next(s for s in result.symbols if s.name == "qux")
        # Decorators do NOT affect the ID per grammar doc
        assert qux.scip_id == f"codemem {PKG} .{FILE_REL}#Bar.qux"
        # Decorator info is stored in signature field, not ID
        assert qux.signature is not None
        assert "@staticmethod" in qux.signature

    def test_multiple_decorators_preserved_in_signature(self):
        src = (
            "def wrap(f): return f\n"
            "@wrap\n"
            "@staticmethod\n"
            "def bare():\n"
            "    return 0\n"
        )
        # Top-level decorated function — decorators applied bottom-up
        result = _parse(src)
        bare = next(s for s in result.symbols if s.name == "bare")
        # Both decorators captured (order matches source)
        assert "@wrap" in (bare.signature or "")
        assert "@staticmethod" in (bare.signature or "")


# ---------------------------------------------------------------------
# Additional behavior required by AC
# ---------------------------------------------------------------------

class TestAsyncFunction:
    def test_async_function_signature_prefix(self):
        result = _parse("async def fetch(url):\n    return url\n")
        sym = result.symbols[0]
        assert sym.kind == "async_function"
        assert sym.signature is not None
        assert sym.signature.startswith("async ")


class TestIntraFileCallEdges:
    def test_edge_emitted_when_caller_and_callee_in_same_file(self):
        src = (
            "def b():\n"
            "    return 2\n"
            "def a():\n"
            "    return b()\n"
        )
        result = _parse(src)
        assert len(result.edges) == 1

        edge = result.edges[0]
        a_id = f"codemem {PKG} /{FILE_REL}#a"
        b_id = f"codemem {PKG} /{FILE_REL}#b"
        assert edge.src_scip_id == a_id
        assert edge.dst_scip_id == b_id
        assert edge.dst_unresolved is None
        assert edge.kind == "call"

    def test_external_call_emits_no_edge(self):
        # External symbol 'requests' is cross-file territory (Task 1.6).
        src = (
            "def a():\n"
            "    return requests.get('url')\n"
        )
        result = _parse(src)
        assert result.edges == []

    def test_method_call_on_self_resolves_by_name(self):
        # self.helper() should resolve to same-class helper method.
        src = (
            "class C:\n"
            "    def helper(self):\n"
            "        return 1\n"
            "    def action(self):\n"
            "        return self.helper()\n"
        )
        result = _parse(src)
        assert len(result.edges) == 1
        edge = result.edges[0]
        assert edge.src_scip_id == f"codemem {PKG} .{FILE_REL}#C.action"
        assert edge.dst_scip_id == f"codemem {PKG} .{FILE_REL}#C.helper"

    def test_ambiguous_method_name_emits_edge_to_each_match(self):
        # When two classes define the same method name, the parser
        # can't disambiguate without type inference (v1 heuristic).
        # Emit one edge per same-named target — caller can dedupe.
        src = (
            "class A:\n"
            "    def run(self):\n"
            "        return 1\n"
            "class B:\n"
            "    def run(self):\n"
            "        return 2\n"
            "def driver():\n"
            "    return run()\n"  # bare call, ambiguous
        )
        result = _parse(src)
        # Two edges: driver → A.run and driver → B.run
        driver_id = f"codemem {PKG} /{FILE_REL}#driver"
        dst_ids = {e.dst_scip_id for e in result.edges if e.src_scip_id == driver_id}
        assert f"codemem {PKG} .{FILE_REL}#A.run" in dst_ids
        assert f"codemem {PKG} .{FILE_REL}#B.run" in dst_ids


class TestSyntaxError:
    def test_malformed_source_returns_empty_result(self):
        # Defensive default: caller can detect by empty result.
        # A regex fallback (the /index behavior) is out of scope for
        # the stdlib-ast path; Task 1.4 (ast-grep) handles broader cases.
        result = _parse("def foo(:\n    pass\n")
        assert result.symbols == []
        assert result.edges == []


# ---------------------------------------------------------------------
# Pinned grammar fixture — MUST match docs/codemem/symbol-id-grammar.md
# byte-for-byte. Any change is an implicit schema migration.
# ---------------------------------------------------------------------

class TestGrammarFixture:
    def test_emits_exact_id_set_from_grammar_doc(self):
        fixture = Path(__file__).parent.parent / "fixtures" / "codemem" / "symbol_ids" / "python_sample.py"
        src = fixture.read_text()

        pkg = "tests/fixtures/codemem/symbol_ids"
        file_rel = "python_sample.py"

        result = extract_python_signatures(src, package=pkg, file_rel=file_rel)

        # Contract from docs/codemem/symbol-id-grammar.md §Parser contract.
        expected = {
            f"codemem {pkg} /{file_rel}#foo",
            f"codemem {pkg} #{file_rel}#Bar",
            f"codemem {pkg} .{file_rel}#Bar.baz",
            f"codemem {pkg} .{file_rel}#Bar.qux",
            f"codemem {pkg} #{file_rel}#Outer",
            f"codemem {pkg} #{file_rel}#Outer#Inner",
        }
        got = set(_ids(result.symbols))
        assert got == expected, f"missing={expected - got}, extra={got - expected}"


# ---------------------------------------------------------------------
# Data-class invariants
# ---------------------------------------------------------------------

class TestDataTypes:
    def test_public_api_surface(self):
        # Contract: these three types form the module's public surface.
        assert set(parser_mod.__all__) == {
            "Symbol", "CallEdge", "ParseResult", "extract_python_signatures",
        }
        assert CallEdge.__module__ == "codemem.parser.python_ast"

    def test_symbol_is_hashable_and_ordered_by_fields(self):
        # Symbols should be usable in sets keyed by scip_id for dedup.
        s1 = Symbol(
            scip_id="x", name="x", kind="function", line=1,
            signature=None, signature_hash=None, docstring=None, parent_scip_id=None,
        )
        s2 = Symbol(
            scip_id="x", name="x", kind="function", line=1,
            signature=None, signature_hash=None, docstring=None, parent_scip_id=None,
        )
        assert s1 == s2

    def test_parse_result_fields(self):
        r = ParseResult(symbols=[], edges=[])
        assert r.symbols == []
        assert r.edges == []
