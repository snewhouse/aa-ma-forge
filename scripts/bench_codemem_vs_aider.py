#!/usr/bin/env python3
"""codemem vs Aider vs jCodeMunch token-budget benchmark harness (M2).

Currently contains: the Aider prose-output parser (Task 2.3 GREEN).

Future additions (later M2 tasks):
- Task 2.4: tiktoken normalization helpers
- Task 2.5: CLI entry point, tool invocation, overlap metrics
"""

from __future__ import annotations

import re

# Known file extensions — guards file-header detection against line-wrapped
# signature continuations (e.g., a standalone `dict:` line that is actually
# the return-type wrap from a preceding `│def foo(...) -> ` line).
_FILE_EXT_RE = re.compile(
    r"\.(py|sh|md|toml|yaml|yml|json|txt|rs|go|ts|tsx|"
    r"js|jsx|c|cpp|h|hpp|java|rb|php|swift|kt)$"
)

# Aider prefixes symbol lines with │ (U+2502). Whitespace after │ is Aider
# indentation reflecting Python nesting (e.g., methods inside a class body).
_DEF_RE = re.compile(r"^│\s*def\s+([A-Za-z_][A-Za-z0-9_]*)")
_CLASS_RE = re.compile(r"^│\s*class\s+([A-Za-z_][A-Za-z0-9_]*)")
_DECORATOR_RE = re.compile(r"^│\s*@([A-Za-z_][A-Za-z0-9_.]*)")


def parse_aider_output(text: str) -> list[tuple[str, str, str]]:
    """Parse Aider `--show-repo-map` prose into (file, symbol_name, kind) rows.

    Aider emits a hybrid prose format:
    - File headers: ``<path>:`` (no leading │, path-like, ends with `:`)
    - Top-level symbols: ``│def NAME(...``, ``│class NAME:``, ``│@NAME``
    - Nested symbols: ``│    def NAME(...`` (indentation after │ is preserved)
    - Elision: ``⋮`` — omitted lines, skipped
    - CLI preamble (lines 1-10 of ``aider ...`` stdout): skipped (no │, no
      path-like tail)

    Kinds emitted: ``"def"``, ``"class"``, ``"decorator"``. Decorators emit as
    their own rows (e.g., ``│@dataclass`` → ``(file, "dataclass", "decorator")``).

    Empty input returns an empty list.
    """
    rows: list[tuple[str, str, str]] = []
    current_file: str | None = None

    for line in text.splitlines():
        # File-header detection: non-│ line, ends with `:`, path-like tail.
        # Path-likeness (has `/` or known extension) guards against
        # wrapped-signature continuations like `dict:`.
        if not line.startswith("│") and line.endswith(":") and line != ":":
            candidate = line[:-1]
            if "/" in candidate or _FILE_EXT_RE.search(candidate):
                current_file = candidate
                continue

        # No file context yet = preamble or pre-map content; skip.
        if current_file is None:
            continue

        m = _DEF_RE.match(line)
        if m:
            rows.append((current_file, m.group(1), "def"))
            continue
        m = _CLASS_RE.match(line)
        if m:
            rows.append((current_file, m.group(1), "class"))
            continue
        m = _DECORATOR_RE.match(line)
        if m:
            rows.append((current_file, m.group(1), "decorator"))

    return rows
