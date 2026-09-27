"""Tests for codemem.parser.ast_grep — Task 1.4 acceptance gate.

Covers: JSON stream parsing, per-language batching, SCIP ID construction
for classes/methods/functions with parent-by-line-range inference,
subprocess mocking, and real-sg integration for TypeScript.
"""

from __future__ import annotations

import errno
import json
import logging
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

@pytest.mark.skipif(ag.resolve_ast_grep_bin() is None, reason="ast-grep binary not found")
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


# ---------------------------------------------------------------------
# Binary resolution — a foreign ``sg`` must never index to a silent zero
# ---------------------------------------------------------------------

# On Ubuntu ``/usr/bin/sg`` is util-linux's ``newgrp``, not ast-grep. This
# stand-in answers ``--version`` the same way and rejects ``scan`` flags.
_FOREIGN_SG = """#!/bin/sh
if [ "$1" = "--version" ]; then echo "sg from util-linux 2.41.3"; exit 0; fi
echo "sg: invalid option -- 'r'" >&2
exit 1
"""


# ``--version`` like the ast-grep-cli wheel's ``sg``; scanning is never reached.
_AST_GREP_SG = """#!/bin/sh
echo "ast-grep 0.42.1"
"""

_REAL_AST_GREP = ag.resolve_ast_grep_bin()
_LOGGER = "codemem.parser.ast_grep"
_TS_SOURCE = "function greet(name: string): string {\n    return name;\n}\n"


def _script(bindir: Path, name: str, body: str) -> Path:
    bindir.mkdir(exist_ok=True)
    p = bindir / name
    p.write_text(body)
    p.chmod(0o755)
    return p


def _foreign_sg_dir(tmp_path: Path) -> Path:
    bindir = tmp_path / "foreign-bin"
    _script(bindir, "sg", _FOREIGN_SG)
    return bindir


def _no_interpreter_bindir(tmp_path: Path, monkeypatch) -> None:
    """Point sys.executable at a dir holding no ast-grep (the venv's bin has one)."""
    empty = tmp_path / "interp-bin"
    empty.mkdir()
    monkeypatch.setattr(ag.sys, "executable", str(empty / "python"))


def _only_foreign_sg(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("PATH", str(_foreign_sg_dir(tmp_path)))
    _no_interpreter_bindir(tmp_path, monkeypatch)


def _ts_file(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir(exist_ok=True)
    f = repo / "a.ts"
    f.write_text(_TS_SOURCE)
    return f


def _warnings(caplog) -> list[str]:
    return [r.getMessage() for r in caplog.records
            if r.name == _LOGGER and r.levelno >= logging.WARNING]


@pytest.fixture(autouse=True)
def _fresh_resolver_cache():
    """The resolver is cached per process; each test sees its own PATH."""
    clear = getattr(ag.resolve_ast_grep_bin, "cache_clear", lambda: None)
    clear()
    yield
    clear()


class TestBinaryResolution:
    def test_foreign_sg_on_path_warns_instead_of_silent_zero(self, tmp_path, monkeypatch, caplog):
        _only_foreign_sg(tmp_path, monkeypatch)
        f = _ts_file(tmp_path)
        with caplog.at_level(logging.WARNING, logger=_LOGGER):
            results = extract_with_ast_grep([f], package=".", repo_root=f.parent)
        assert f not in results, "an unparsed file must not look like a parsed, empty one"
        msgs = _warnings(caplog)
        assert msgs, "a non-Python file indexed to zero symbols with no warning"
        assert any("ast-grep" in m for m in msgs)

    def test_foreign_sg_is_not_resolved(self, tmp_path, monkeypatch):
        _only_foreign_sg(tmp_path, monkeypatch)
        assert ag.resolve_ast_grep_bin() is None

    @pytest.mark.skipif(_REAL_AST_GREP is None, reason="ast-grep binary not found")
    def test_prefers_ast_grep_over_foreign_sg(self, tmp_path, monkeypatch, caplog):
        foreign = _foreign_sg_dir(tmp_path)
        real = tmp_path / "real-bin"
        real.mkdir()
        (real / "ast-grep").symlink_to(_REAL_AST_GREP)
        monkeypatch.setenv("PATH", f"{foreign}:{real}")  # foreign sg wins a bare `sg` lookup
        _no_interpreter_bindir(tmp_path, monkeypatch)
        f = _ts_file(tmp_path)
        with caplog.at_level(logging.WARNING, logger=_LOGGER):
            results = extract_with_ast_grep([f], package=".", repo_root=f.parent)
        assert {s.name for s in results[f].symbols} == {"greet"}
        assert _warnings(caplog) == []

    def test_finds_ast_grep_beside_the_interpreter_when_not_on_path(self, tmp_path, monkeypatch):
        # pipx / an absolute .venv/bin/codemem: the venv's bin dir is not on PATH.
        venv_bin = tmp_path / "venv-bin"
        adjacent = _script(venv_bin, "ast-grep", _AST_GREP_SG)
        monkeypatch.setenv("PATH", str(_foreign_sg_dir(tmp_path)))
        monkeypatch.setattr(ag.sys, "executable", str(venv_bin / "python"))
        assert ag.resolve_ast_grep_bin() == str(adjacent)

    def test_interpreter_adjacent_ast_grep_beats_one_on_path(self, tmp_path, monkeypatch):
        # Review finding 2: the pinned ast-grep-cli dependency sits beside the
        # interpreter; an unrelated ast-grep earlier on PATH must not win.
        venv_bin = tmp_path / "venv-bin"
        adjacent = _script(venv_bin, "ast-grep", _AST_GREP_SG)
        _script(tmp_path / "path-bin", "ast-grep", _AST_GREP_SG)
        monkeypatch.setenv("PATH", str(tmp_path / "path-bin"))
        monkeypatch.setattr(ag.sys, "executable", str(venv_bin / "python"))
        assert ag.resolve_ast_grep_bin() == str(adjacent)

    def test_sg_fallback_probes_every_sg_on_path(self, tmp_path, monkeypatch):
        # Review finding 7: newgrp's sg first on PATH must not hide ast-grep's sg.
        foreign = _foreign_sg_dir(tmp_path)
        good = _script(tmp_path / "good-bin", "sg", _AST_GREP_SG)
        monkeypatch.setenv("PATH", f"{foreign}:{good.parent}")
        _no_interpreter_bindir(tmp_path, monkeypatch)
        assert ag.resolve_ast_grep_bin() == str(good)

    def test_sg_fallback_probes_the_interpreter_adjacent_sg(self, tmp_path, monkeypatch):
        venv_bin = tmp_path / "venv-bin"
        good = _script(venv_bin, "sg", _AST_GREP_SG)
        monkeypatch.setenv("PATH", str(_foreign_sg_dir(tmp_path)))
        monkeypatch.setattr(ag.sys, "executable", str(venv_bin / "python"))
        assert ag.resolve_ast_grep_bin() == str(good)

    def test_resolution_is_cached_per_process(self, tmp_path, monkeypatch):
        # Review finding 5: no repeated which/--version probes per call.
        venv_bin = tmp_path / "venv-bin"
        adjacent = _script(venv_bin, "ast-grep", _AST_GREP_SG)
        monkeypatch.setenv("PATH", "")
        monkeypatch.setattr(ag.sys, "executable", str(venv_bin / "python"))
        assert ag.resolve_ast_grep_bin() == str(adjacent)
        adjacent.unlink()
        assert ag.resolve_ast_grep_bin() == str(adjacent)  # served from the cache
        ag.resolve_ast_grep_bin.cache_clear()
        assert ag.resolve_ast_grep_bin() is None

    def test_invoker_seam_does_not_change_binary_selection(self, tmp_path, monkeypatch):
        # Review finding 4: injecting _invoker must not fall back to a bare "sg".
        monkeypatch.setattr(ag, "resolve_ast_grep_bin", lambda: "/resolved/ast-grep")
        invoker = FakeInvoker({})
        f = _ts_file(tmp_path)
        extract_with_ast_grep([f], package=".", repo_root=f.parent, _invoker=invoker)
        assert [c["sg_bin"] for c in invoker.calls] == ["/resolved/ast-grep"]

    def test_failing_explicit_binary_is_logged_with_its_stderr(self, tmp_path, caplog):
        sg = _foreign_sg_dir(tmp_path) / "sg"
        f = _ts_file(tmp_path)
        with caplog.at_level(logging.WARNING, logger=_LOGGER):
            results = extract_with_ast_grep([f], package=".", repo_root=f.parent, sg_bin=str(sg))
        assert f not in results
        msgs = _warnings(caplog)
        assert any("exit 1" in m and "invalid option" in m for m in msgs)

    def test_missing_explicit_binary_warns_and_does_not_raise(self, tmp_path, caplog):
        f = _ts_file(tmp_path)
        with caplog.at_level(logging.WARNING, logger=_LOGGER):
            results = extract_with_ast_grep(
                [f], package=".", repo_root=f.parent, sg_bin=str(tmp_path / "no-such-ast-grep"),
            )
        assert f not in results
        assert _warnings(caplog)

    def test_unresolved_binary_never_reaches_the_invoker(self, tmp_path, monkeypatch, caplog):
        calls: list[object] = []
        monkeypatch.setattr(ag, "resolve_ast_grep_bin", lambda: None)
        monkeypatch.setattr(ag, "_invoke_sg", lambda *a, **kw: calls.append(kw) or "")
        f = _ts_file(tmp_path)
        with caplog.at_level(logging.WARNING, logger=_LOGGER):
            results = extract_with_ast_grep([f], package=".", repo_root=f.parent)
        assert calls == []
        assert f not in results
        assert any("no ast-grep binary found" in m for m in _warnings(caplog))

    def test_no_supported_files_never_looks_for_a_binary(self, tmp_path, monkeypatch, caplog):
        _only_foreign_sg(tmp_path, monkeypatch)
        py = tmp_path / "a.py"
        py.write_text("def f():\n    return 1\n")
        with caplog.at_level(logging.WARNING, logger=_LOGGER):
            assert extract_with_ast_grep([py], package=".", repo_root=tmp_path) == {}
        assert _warnings(caplog) == []

    def test_python_indexing_unaffected_when_ast_grep_missing(self, tmp_path, monkeypatch, caplog):
        from codemem.indexer import parse_files

        f = _ts_file(tmp_path)
        py = f.parent / "app.py"
        py.write_text("def greet(name):\n    return name\n")
        _only_foreign_sg(tmp_path, monkeypatch)
        with caplog.at_level(logging.WARNING, logger=_LOGGER):
            parses, py_errors = parse_files([py, f], repo_root=f.parent, package=".")
        by_lang = {p.lang: p for p in parses}
        assert py_errors == 0
        assert {s.name for s in by_lang["python"].result.symbols} == {"greet"}
        assert "typescript" not in by_lang, "unparsed file must be skipped, not stored empty"
        assert _warnings(caplog)


# ---------------------------------------------------------------------
# Batching — argv must stay bounded (review finding 3)
# ---------------------------------------------------------------------

class TestArgvBatching:
    def test_large_batch_is_chunked_under_the_argv_budget(self, tmp_path):
        long_dir = tmp_path / ("d" * 200)
        files = [long_dir / f"file_{i:05d}.ts" for i in range(2000)]  # ~0.5 MB of paths
        invoker = FakeInvoker({})
        results = extract_with_ast_grep(
            files, package=".", repo_root=tmp_path, sg_bin="sg", _invoker=invoker,
        )
        assert len(invoker.calls) > 1
        for call in invoker.calls:
            assert sum(len(p) + 1 for p in call["files"]) <= ag._ARGV_BUDGET
        assert [p for c in invoker.calls for p in c["files"]] == [str(f) for f in files]
        assert set(results) == set(files)

    def test_small_batch_is_one_invocation(self, tmp_path):
        files = [tmp_path / "a.ts", tmp_path / "b.ts"]
        invoker = FakeInvoker({})
        extract_with_ast_grep(files, package=".", repo_root=tmp_path, sg_bin="sg", _invoker=invoker)
        assert len(invoker.calls) == 1

    def test_e2big_is_reported_as_argv_too_long(self, tmp_path, monkeypatch, caplog):
        def _raise(*_a, **_kw):
            raise OSError(errno.E2BIG, "Argument list too long")

        monkeypatch.setattr(ag.subprocess, "run", _raise)
        f = _ts_file(tmp_path)
        with caplog.at_level(logging.WARNING, logger=_LOGGER):
            results = extract_with_ast_grep([f], package=".", repo_root=f.parent, sg_bin="sg")
        assert f not in results
        assert any("argument list too long" in m.lower() for m in _warnings(caplog))
