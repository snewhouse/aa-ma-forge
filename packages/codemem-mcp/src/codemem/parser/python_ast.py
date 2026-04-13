"""Python parser via stdlib `ast` (M1 Task 1.3).

Ports ``extract_python_signatures`` from ``~/.claude-code-project-index/scripts/
index_utils.py`` into codemem's canonical shape:

* Emit one :class:`Symbol` per module-level function, module-level class,
  class-level method, and nested class — mirroring ``/index``'s scope.
* Each symbol carries a SCIP-shaped ID built per
  ``docs/codemem/symbol-id-grammar.md`` (v1).
* Intra-file call edges are resolved by name against the set of
  symbols emitted for this file. Cross-file resolution is Task 1.6.

Out of scope for v1: nested functions as named symbols, lambdas,
comprehensions, macros, MRO resolution, re-exports, tombstones.
"""

from __future__ import annotations

import ast
import hashlib
from dataclasses import dataclass, field
from typing import Iterable


__all__ = ["Symbol", "CallEdge", "ParseResult", "extract_python_signatures"]


# Builtins and common stdlib shims that would otherwise drown real edges.
# Matches ``/index``'s exclusion list verbatim.
_CALL_EXCLUDE: frozenset[str] = frozenset(
    {
        "print", "len", "str", "int", "float", "bool", "list", "dict",
        "set", "tuple", "type", "isinstance", "issubclass", "super",
        "range", "enumerate", "zip", "map", "filter", "sorted",
        "reversed", "open", "input", "eval",
    }
)


@dataclass(eq=True)
class Symbol:
    """One row of the ``symbols`` table, pre-DB.

    ``parent_scip_id`` is a string reference that the indexer driver
    (Task 1.5) resolves to an integer FK at insert time.
    """

    scip_id: str
    name: str
    kind: str
    line: int
    signature: str | None
    signature_hash: str | None
    docstring: str | None
    parent_scip_id: str | None


@dataclass(eq=True)
class CallEdge:
    """Intra-file directed edge. ``dst_scip_id`` is always set for edges
    produced by this parser; cross-file unresolved edges come from the
    cross-file resolver (Task 1.6).
    """

    src_scip_id: str
    dst_scip_id: str | None
    dst_unresolved: str | None
    kind: str = "call"


@dataclass
class ParseResult:
    symbols: list[Symbol]
    edges: list[CallEdge]
    # Module names imported at file-top (Task 1.6 cross-file resolver input).
    # For ``import a.b`` / ``from a.b import c`` both emit ``a.b``.
    imports: list[str] = field(default_factory=list)
    # Cross-file call candidates: edges whose target isn't a same-file symbol.
    # ``dst_unresolved`` is populated; ``dst_scip_id`` is ``None``. The
    # resolver (Task 1.6) consumes these and upgrades what it can match.
    unresolved_edges: list[CallEdge] = field(default_factory=list)


# ---------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------

def extract_python_signatures(
    source: str,
    *,
    package: str,
    file_rel: str,
) -> ParseResult:
    """Parse ``source`` into codemem Symbols and intra-file CallEdges.

    Args:
        source: UTF-8 decoded Python source text.
        package: Repo-relative package directory (SCIP ``<package>``).
        file_rel: File path relative to ``package`` (SCIP ``<file>``).

    Returns:
        A :class:`ParseResult`. On SyntaxError the result is empty —
        the ast-grep wrapper in Task 1.4 handles best-effort parsing
        of partial/invalid source.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return ParseResult(symbols=[], edges=[])

    # Extract imports from the module top-level. ``import a.b`` and
    # ``from a.b import c`` both contribute the dotted module ``a.b``.
    imports: list[str] = []
    for node in tree.body:
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append(node.module)

    symbols: list[Symbol] = []
    # Preserve the original FunctionDef/AsyncFunctionDef AST node alongside
    # its SCIP ID so we can extract calls from its body in one pass.
    function_nodes: list[tuple[ast.FunctionDef | ast.AsyncFunctionDef, str]] = []

    def _emit_function(
        node: ast.FunctionDef | ast.AsyncFunctionDef,
        parent_path: str | None,
        parent_scip_id: str | None,
    ) -> None:
        is_method = parent_path is not None
        symbol_path = f"{parent_path}.{node.name}" if parent_path else node.name
        marker = "." if is_method else "/"
        scip_id = f"codemem {package} {marker}{file_rel}#{symbol_path}"
        base_kind = "method" if is_method else "function"
        kind = f"async_{base_kind}" if isinstance(node, ast.AsyncFunctionDef) else base_kind

        signature = _build_signature(node)
        signature_hash = (
            hashlib.sha256(signature.encode("utf-8")).hexdigest()
            if signature
            else None
        )

        raw_doc = ast.get_docstring(node)
        docstring = raw_doc.split("\n", 1)[0].strip() if raw_doc else None

        symbols.append(
            Symbol(
                scip_id=scip_id,
                name=node.name,
                kind=kind,
                line=node.lineno,
                signature=signature,
                signature_hash=signature_hash,
                docstring=docstring,
                parent_scip_id=parent_scip_id,
            )
        )
        function_nodes.append((node, scip_id))

    def _emit_class(
        node: ast.ClassDef,
        parent_path: str | None,
        parent_scip_id: str | None,
    ) -> None:
        symbol_path = f"{parent_path}#{node.name}" if parent_path else node.name
        scip_id = f"codemem {package} #{file_rel}#{symbol_path}"

        raw_doc = ast.get_docstring(node)
        docstring = raw_doc.split("\n", 1)[0].strip() if raw_doc else None

        symbols.append(
            Symbol(
                scip_id=scip_id,
                name=node.name,
                kind="class",
                line=node.lineno,
                signature=None,
                signature_hash=None,
                docstring=docstring,
                parent_scip_id=parent_scip_id,
            )
        )

        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                _emit_function(item, symbol_path, scip_id)
            elif isinstance(item, ast.ClassDef):
                _emit_class(item, symbol_path, scip_id)

    for top in tree.body:
        if isinstance(top, (ast.FunctionDef, ast.AsyncFunctionDef)):
            _emit_function(top, None, None)
        elif isinstance(top, ast.ClassDef):
            _emit_class(top, None, None)

    # --- Intra-file call edge resolution ---------------------------------
    # Build name → list[scip_id]. Same-named methods across sibling classes
    # collide here by design — v1 over-emits edges rather than guess (see
    # test_ambiguous_method_name_emits_edge_to_each_match). Disambiguation
    # by type inference is deferred past v1.
    name_to_ids: dict[str, list[str]] = {}
    _callable_kinds = {"function", "async_function", "method", "async_method"}
    for sym in symbols:
        if sym.kind in _callable_kinds:
            name_to_ids.setdefault(sym.name, []).append(sym.scip_id)

    resolvable = set(name_to_ids)
    edges: list[CallEdge] = []
    unresolved_edges: list[CallEdge] = []
    for func_node, src_scip_id in function_nodes:
        intra, extra = _extract_call_names(func_node.body, resolvable)
        for callee_name in intra:
            for dst_scip_id in name_to_ids[callee_name]:
                edges.append(
                    CallEdge(
                        src_scip_id=src_scip_id,
                        dst_scip_id=dst_scip_id,
                        dst_unresolved=None,
                        kind="call",
                    )
                )
        for callee_name in extra:
            unresolved_edges.append(
                CallEdge(
                    src_scip_id=src_scip_id,
                    dst_scip_id=None,
                    dst_unresolved=callee_name,
                    kind="call",
                )
            )

    return ParseResult(
        symbols=symbols,
        edges=edges,
        imports=imports,
        unresolved_edges=unresolved_edges,
    )


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------

def _unparse(node: ast.AST) -> str:
    """Best-effort ast.unparse; empty string on any failure."""
    try:
        return ast.unparse(node)
    except Exception:
        return ""


def _decorator_name(dec: ast.AST) -> str:
    """Return a display string for a decorator node (no leading '@')."""
    if isinstance(dec, ast.Name):
        return dec.id
    if isinstance(dec, ast.Attribute):
        return _unparse(dec)
    if isinstance(dec, ast.Call):
        if isinstance(dec.func, ast.Name):
            return dec.func.id
        if isinstance(dec.func, ast.Attribute):
            return _unparse(dec.func)
    return _unparse(dec)


def _build_signature(node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    """Canonicalized signature for display + M2 diff hashing.

    Format::

        @decorator_1
        @decorator_2
        (params) -> return_annotation        # 'async ' prefix on AsyncFunctionDef

    ``self`` and ``cls`` are stripped from param lists (per ``/index``).
    Decorators appear in source order.
    """
    lines: list[str] = []

    for dec in node.decorator_list:
        name = _decorator_name(dec)
        if name:
            lines.append("@" + name)

    params: list[str] = []
    args = node.args

    num_positional = len(args.args)
    num_defaults = len(args.defaults)
    default_offset = num_positional - num_defaults

    for idx, arg in enumerate(args.args):
        if arg.arg in ("self", "cls"):
            continue
        piece = arg.arg
        if arg.annotation:
            piece += ": " + _unparse(arg.annotation)
        default_idx = idx - default_offset
        if 0 <= default_idx < len(args.defaults):
            piece += " = " + _unparse(args.defaults[default_idx])
        params.append(piece)

    if args.vararg:
        piece = "*" + args.vararg.arg
        if args.vararg.annotation:
            piece += ": " + _unparse(args.vararg.annotation)
        params.append(piece)

    for idx, arg in enumerate(args.kwonlyargs):
        piece = arg.arg
        if arg.annotation:
            piece += ": " + _unparse(arg.annotation)
        if idx < len(args.kw_defaults):
            kw_default = args.kw_defaults[idx]
            if kw_default is not None:
                piece += " = " + _unparse(kw_default)
        params.append(piece)

    if args.kwarg:
        piece = "**" + args.kwarg.arg
        if args.kwarg.annotation:
            piece += ": " + _unparse(args.kwarg.annotation)
        params.append(piece)

    base = "(" + ", ".join(params) + ")"
    if node.returns:
        base += " -> " + _unparse(node.returns)
    if isinstance(node, ast.AsyncFunctionDef):
        base = "async " + base

    lines.append(base)
    return "\n".join(lines)


def _extract_call_names(
    body: Iterable[ast.stmt],
    resolvable: set[str],
) -> tuple[set[str], set[str]]:
    """Return ``(intra, extra)`` unique callee names from ``body``.

    * ``intra``: bare or attribute calls whose name matches a same-file
      symbol. These become resolved intra-file edges.
    * ``extra``: bare-name calls NOT in ``resolvable`` and NOT in the
      built-in exclusion list. Attribute calls whose attr doesn't match
      a same-file symbol are recorded ONLY when the receiver is a plain
      Name (cross-module-attribute pattern like ``mod.func()``); unknown
      method chains (``self.foo().bar()``) are not emitted because their
      receiver type is ambiguous at parse time.

    Both return sets filter out the ``_CALL_EXCLUDE`` built-ins for
    bare-name calls — those are never emitted at either layer.
    """
    intra: set[str] = set()
    extra: set[str] = set()
    for node in ast.walk(ast.Module(body=list(body), type_ignores=[])):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if isinstance(func, ast.Name):
            n = func.id
            if n in _CALL_EXCLUDE:
                continue
            if n in resolvable:
                intra.add(n)
            else:
                extra.add(n)
        elif isinstance(func, ast.Attribute):
            n = func.attr
            if n in resolvable:
                intra.add(n)
            elif isinstance(func.value, ast.Name):
                # ``module.func()`` — receiver is a plain name. The
                # resolver can try to match against imported modules.
                extra.add(n)
    return intra, extra
