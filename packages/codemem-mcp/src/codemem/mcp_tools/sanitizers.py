r"""Input sanitization for MCP tools (M1 Task 1.7).

Every tool arg that becomes part of a SQL query or filesystem lookup
passes through a validator here FIRST. Rejection happens before any SQL
or path I/O — so adversarial inputs never reach the query layer.

Contract (per ``codemem-reference.md``):

* Path args → ``Path.resolve(strict=False)`` + ``is_relative_to(repo_root)``
  to catch canonicalized traversal (``foo/../../bar`` becomes absolute
  and is rejected when it escapes the repo).
* Symbol / file string args → allow-list regex
  ``^[A-Za-z0-9_./\-]{1,256}$`` PLUS explicit rejection of ``..``
  substring. The explicit ``..`` check is defense-in-depth — the regex
  already rules it out, but a future widening of the allow-list won't
  silently re-introduce traversal.

Output text is the other direction: :func:`sanitize_context_line` makes a
repo-controlled string (an indexed path, a node id) safe to hand the model
as one line of hook context (code-conventions-impact 10.6).
"""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path


__all__ = [
    "ValidationError",
    "sanitize_context_line",
    "sanitize_path_arg",
    "sanitize_symbol_arg",
]


_ALLOWED = re.compile(r"^[A-Za-z0-9_./\-]{1,256}$")


# Unicode categories never handed to the model: Cc (C0/C1 controls incl. CR, LF, ESC,
# DEL), Cf (format: zero-width, bidi controls, BOM, soft hyphen, tag characters that can
# smuggle hidden text), Co (private use), Cs (lone surrogates), Zl/Zp (line/paragraph
# separators). A category test, not a hand list: a list misses whatever it forgot.
_CONTEXT_UNSAFE_CATEGORIES = frozenset({"Cc", "Cf", "Co", "Cs", "Zl", "Zp"})
_ELLIPSIS = "\u2026"


class ValidationError(ValueError):
    """Raised when an input arg fails the sanitization contract."""


def sanitize_symbol_arg(value: object) -> str:
    """Validate a symbol/file string arg.

    Returns the value unchanged if it passes. Raises
    :class:`ValidationError` with a plain-English reason otherwise.
    """
    if not isinstance(value, str):
        raise ValidationError("must be a string")
    if not value:
        raise ValidationError("must be non-empty")
    if len(value) > 256:
        raise ValidationError("must be ≤ 256 characters")
    if ".." in value:
        raise ValidationError("must not contain '..' (path traversal)")
    if not _ALLOWED.match(value):
        raise ValidationError(
            "must match [A-Za-z0-9_./\\-]+ (no SQL/regex/shell metachars)"
        )
    return value


def sanitize_path_arg(value: object, repo_root: Path) -> Path:
    """Validate a filesystem path arg relative to ``repo_root``.

    Runs the symbol-arg allow-list first (so regex/SQL metacharacters
    can't slip through even in path-shaped inputs), then resolves and
    asserts the target stays inside the repo.
    """
    s = sanitize_symbol_arg(value)
    repo_root_abs = repo_root.resolve()
    # ``strict=False`` resolves even when the path doesn't exist yet —
    # we want the canonical form for the containment check, not
    # existence (that's the caller's concern).
    target = (repo_root_abs / s).resolve(strict=False)
    try:
        target.relative_to(repo_root_abs)
    except ValueError as exc:
        raise ValidationError("path escapes repository root") from exc
    return target


def sanitize_context_line(text: str, max_len: int = 200) -> str:
    """``text`` as one printable line of at most ``max_len`` characters; never raises.

    Every character in a Cc, Cf, Co, Cs, Zl or Zp Unicode category becomes a
    space, whitespace runs collapse to one space, and the ends are trimmed. A
    longer result is cut to ``max_len - 1`` characters plus ``…``;
    ``max_len <= 0`` gives ``""``. Shell syntax such as ``$(…)`` is kept: the
    result is data, never interpreted.
    """
    try:
        if max_len <= 0:
            return ""
        s = text if isinstance(text, str) else str(text)
        s = "".join(
            " " if unicodedata.category(ch) in _CONTEXT_UNSAFE_CATEGORIES else ch
            for ch in s
        )
        s = " ".join(s.split())
        if len(s) > max_len:
            s = s[: max_len - 1].rstrip() + _ELLIPSIS
        return s
    except Exception:  # noqa: BLE001  # why: the contract is "never raises"; a str() that raises yields ""
        return ""
