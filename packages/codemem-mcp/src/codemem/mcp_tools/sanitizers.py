"""Input sanitization for MCP tools (M1 Task 1.7).

Every tool arg that becomes part of a SQL query or filesystem lookup
passes through a validator here FIRST. Rejection happens before any SQL
or path I/O — so adversarial inputs never reach the query layer.

Contract (per ``codemem-reference.md``):

* Path args → ``Path.resolve(strict=False)`` + ``is_relative_to(repo_root)``
  to catch canonicalized traversal (``foo/../../bar`` becomes absolute
  and is rejected when it escapes the repo).
* Symbol / file string args → allow-list regex
  ``^[A-Za-z0-9_./\\-]{1,256}$`` PLUS explicit rejection of ``..``
  substring. The explicit ``..`` check is defense-in-depth — the regex
  already rules it out, but a future widening of the allow-list won't
  silently re-introduce traversal.
"""

from __future__ import annotations

import re
from pathlib import Path


__all__ = ["ValidationError", "sanitize_path_arg", "sanitize_symbol_arg"]


_ALLOWED = re.compile(r"^[A-Za-z0-9_./\-]{1,256}$")


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
