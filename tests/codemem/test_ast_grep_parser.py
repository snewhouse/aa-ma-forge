"""Tests for codemem.parser.ast_grep — Task 1.4 acceptance gate.

Covers: JSON stream parsing, per-language batching, SCIP ID construction
for classes/methods/functions with parent-by-line-range inference,
subprocess mocking, and real-sg integration for TypeScript.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from codemem.parser import ast_grep as ag
from codemem.parser.ast_grep import (
    SUPPORTED_LANGUAGES,
    extract_with_ast_grep,
    language_from_path,
    parse_sg_output,
)
from codemem.parser.python_ast import ParseResult


REPO_ROOT = Path(__file__).resolve().parent.parent.parent
PKG = "tests/fixtures/codemem/sample_repo"  # synthetic package root


# ---------------------------------------------------------------------
# language_from_path
# ---------------------------------------------------------------------

class TestLanguageFromPath:
    @pytest.mark.parametrize(
        "filename, expected",
        [
            ("a.ts", "TypeScript"),
            ("a.tsx", "Tsx"),
            ("a.js", "JavaScript"),
            ("a.jsx", "JavaScript"),
            ("a.mjs", "JavaScript"),
            ("a.cjs", "JavaScript"),
            ("a.go", "Go"),
            ("a.rs", "Rust"),
            ("a.java", "Java"),
            ("a.rb", "Ruby"),
            ("a.sh", "Bash"),
            ("a.bash", "Bash"),
            ("a.py", None),        # Python handled by stdlib ast parser
            ("README.md", None),
        ],
    )
    def test_dispatch(self, filename, expected):
        assert language_from_path(Path(filename)) == expected

    def test_tsx_separate_from_typescript(self):
        # Required by AC: languageGlobs for .ts ↔ .tsx — we enforce this
        # by treating them as distinct ast-grep languages.
        assert ".ts" not in SUPPORTED_LANGUAGES["Tsx"]
        assert ".tsx" not in SUPPORTED_LANGUAGES["TypeScript"]


# ---------------------------------------------------------------------
# parse_sg_output — JSON stream parser
# ---------------------------------------------------------------------

def _sg_match(
    *, file: str, rule_id: str, name: str | None, start_line: int, end_line: int,
) -> str:
    """Build a minimal ast-grep JSON line matching its --json=stream format."""
    payload: dict = {
        "file": file,
        "ruleId": rule_id,
        "range": {
            "start": {"line": start_line, "column": 0},
            "end":   {"line": end_line,   "column": 0},
        },
        "text": "",
    }
    if name is not None:
        payload["metaVariables"] = {
            "single": {"NAME": {"text": name, "range": payload["range"]}},
        }
    return json.dumps(payload)


class TestParseSgOutput:
    def test_parses_single_match(self):
        stream = _sg_match(
            file="/repo/a.ts", rule_id="ts-function-def",
            name="greet", start_line=0, end_line=2,
        )
        matches = parse_sg_output(stream)
        assert len(matches) == 1
        m = matches[0]
        assert m.rule_id == "ts-function-def"
        assert m.name == "greet"
        assert m.line == 1         # 1-indexed (sg emits 0-indexed)
        assert m.end_line == 3

    def test_ignores_blank_lines(self):
        stream = "\n\n" + _sg_match(
            file="/repo/a.ts", rule_id="ts-function-def",
            name="x", start_line=0, end_line=0,
        ) + "\n\n"
        assert len(parse_sg_output(stream)) == 1

    def test_skips_invalid_json(self):
        stream = (
            "not valid json\n"
            + _sg_match(file="/a.ts", rule_id="ts-function-def", name="x",
                        start_line=0, end_line=0)
        )
        assert len(parse_sg_output(stream)) == 1

    def test_match_without_name_metavar_has_none_name(self):
        stream = _sg_match(
            file="/a.ts", rule_id="ts-call", name=None,
            start_line=5, end_line=5,
        )
        assert parse_sg_output(stream)[0].name is None


# ---------------------------------------------------------------------
# extract_with_ast_grep — end-to-end with mocked subprocess
# ---------------------------------------------------------------------

class FakeInvoker:
    """Captures sg invocations and returns canned JSON streams per language."""

    def __init__(self, streams_by_rule_file: dict[str, str]):
        self.streams = streams_by_rule_file
        self.calls: list[dict] = []

    def __call__(self, rule_file: Path, files: list[Path], *, sg_bin: str) -> str:
        self.calls.append(
            {"rule_file": rule_file.name, "files": [str(f) for f in files], "sg_bin": sg_bin}
        )
        return self.streams.get(rule_file.name, "")


class TestExtractWithAstGrep:
    def _run(self, files, streams):
        invoker = FakeInvoker(streams)
        results = extract_with_ast_grep(
            files,
            package=PKG,
            repo_root=REPO_ROOT,
            sg_bin="sg",
            _invoker=invoker,
        )
        return results, invoker

    def test_returns_per_file_parse_result(self):
        src_file = REPO_ROOT / PKG / "a.ts"
        stream = _sg_match(
            file=str(src_file), rule_id="ts-function-def",
            name="greet", start_line=0, end_line=2,
        )
        results, _ = self._run([src_file], {"typescript.yml": stream})
        assert src_file in results
        assert isinstance(results[src_file], ParseResult)

    def test_function_gets_term_marker_in_scip_id(self):
        src_file = REPO_ROOT / PKG / "a.ts"
        stream = _sg_match(
            file=str(src_file), rule_id="ts-function-def",
            name="greet", start_line=0, end_line=2,
        )
        results, _ = self._run([src_file], {"typescript.yml": stream})
        pr = results[src_file]
        assert len(pr.symbols) == 1
        sym = pr.symbols[0]
        assert sym.name == "greet"
        assert sym.kind == "function"
        assert sym.scip_id == f"codemem {PKG} /a.ts#greet"
        assert sym.line == 1
        assert sym.parent_scip_id is None

    def test_class_gets_type_marker(self):
        src_file = REPO_ROOT / PKG / "a.ts"
        stream = _sg_match(
            file=str(src_file), rule_id="ts-class-def",
            name="UserCard", start_line=3, end_line=10,
        )
        results, _ = self._run([src_file], {"typescript.yml": stream})
        sym = results[src_file].symbols[0]
        assert sym.kind == "class"
        assert sym.scip_id == f"codemem {PKG} #a.ts#UserCard"

    def test_method_infers_parent_from_line_range(self):
        src_file = REPO_ROOT / PKG / "a.ts"
        # Class spans lines 0-8; method on line 3 inside it.
        stream = (
            _sg_match(file=str(src_file), rule_id="ts-class-def",
                      name="UserCard", start_line=0, end_line=8)
            + "\n"
            + _sg_match(file=str(src_file), rule_id="ts-method-def",
                        name="render", start_line=3, end_line=5)
        )
        results, _ = self._run([src_file], {"typescript.yml": stream})
        syms = {s.name: s for s in results[src_file].symbols}
        assert syms["UserCard"].scip_id == f"codemem {PKG} #a.ts#UserCard"
        assert syms["render"].kind == "method"
        assert syms["render"].scip_id == f"codemem {PKG} .a.ts#UserCard.render"
        assert syms["render"].parent_scip_id == syms["UserCard"].scip_id

    def test_method_outside_any_class_is_skipped(self):
        # Defensive: if a method_def appears without an enclosing class
        # (e.g. object literal shorthand), skip rather than emit
        # an orphan .None.method id.
        src_file = REPO_ROOT / PKG / "a.ts"
        stream = _sg_match(
            file=str(src_file), rule_id="ts-method-def",
            name="render", start_line=5, end_line=7,
        )
        results, _ = self._run([src_file], {"typescript.yml": stream})
        assert results[src_file].symbols == []

    def test_per_language_batching_single_sg_invocation_per_lang(self):
        # AC: "Batches per language (single sg invocation across N files)".
        ts_a = REPO_ROOT / PKG / "a.ts"
        ts_b = REPO_ROOT / PKG / "b.ts"
        go_a = REPO_ROOT / PKG / "main.go"
        results, invoker = self._run(
            [ts_a, ts_b, go_a],
            {"typescript.yml": "", "go.yml": ""},
        )
        # One call per language, with ALL files of that language in one invocation
        rule_files_called = [c["rule_file"] for c in invoker.calls]
        assert sorted(rule_files_called) == ["go.yml", "typescript.yml"]

        ts_call = next(c for c in invoker.calls if c["rule_file"] == "typescript.yml")
        assert sorted(ts_call["files"]) == sorted([str(ts_a), str(ts_b)])

        go_call = next(c for c in invoker.calls if c["rule_file"] == "go.yml")
        assert go_call["files"] == [str(go_a)]

    def test_unsupported_file_extensions_skipped(self):
        py_file = REPO_ROOT / PKG / "a.py"  # Python — handled by python_ast, not here
        md_file = REPO_ROOT / PKG / "README.md"
        results, invoker = self._run([py_file, md_file], {})
        assert results == {}
        assert invoker.calls == []

    def test_tsx_and_ts_invoked_separately(self):
        # languageGlobs semantics — Tsx files go to tsx.yml, Ts to typescript.yml
        ts = REPO_ROOT / PKG / "a.ts"
        tsx = REPO_ROOT / PKG / "App.tsx"
        _, invoker = self._run(
            [ts, tsx],
            {"typescript.yml": "", "tsx.yml": ""},
        )
        rule_files = sorted(c["rule_file"] for c in invoker.calls)
        assert rule_files == ["tsx.yml", "typescript.yml"]


# ---------------------------------------------------------------------
# Rule-YAML file presence (deliverable completeness)
# ---------------------------------------------------------------------

class TestRuleFilesShipped:
    @pytest.mark.parametrize(
        "rule_file",
        [
            "typescript.yml", "tsx.yml", "javascript.yml",
            "go.yml", "rust.yml", "java.yml", "ruby.yml", "bash.yml",
        ],
    )
    def test_rule_file_exists(self, rule_file):
        f = Path(ag.__file__).parent / "rules" / rule_file
        assert f.exists(), f"missing rule file: {rule_file}"
        text = f.read_text()
        assert "language:" in text, f"{rule_file} has no language: line"
        assert "rule:" in text, f"{rule_file} has no rule: definition"


# ---------------------------------------------------------------------
# Integration test — real sg on a real TypeScript fixture
# ---------------------------------------------------------------------

@pytest.mark.skipif(shutil.which("sg") is None, reason="ast-grep binary not on PATH")
class TestIntegration:
    def test_real_sg_parses_typescript_file(self, tmp_path):
        ts_file = tmp_path / "sample.ts"
        ts_file.write_text(
            "function greet(name: string): string {\n"
            "    return `hello ${name}`;\n"
            "}\n"
            "\n"
            "class UserCard {\n"
            "    render() {\n"
            "        return greet('');\n"
            "    }\n"
            "}\n"
        )
        results = extract_with_ast_grep(
            [ts_file], package=str(tmp_path.relative_to(tmp_path.parent)),
            repo_root=tmp_path.parent,
        )
        assert ts_file in results
        syms = {s.name: s for s in results[ts_file].symbols}
        # All three kinds present
        assert "greet" in syms and syms["greet"].kind == "function"
        assert "UserCard" in syms and syms["UserCard"].kind == "class"
        assert "render" in syms and syms["render"].kind == "method"
        # Method parent correctly inferred
        assert syms["render"].parent_scip_id == syms["UserCard"].scip_id
