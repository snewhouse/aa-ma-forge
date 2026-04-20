#!/usr/bin/env python3
"""codemem vs Aider vs jCodeMunch token-budget benchmark harness (M2).

Invokes each tool at a requested budget, captures its output, and emits a
normalized JSON measurement record per the harness output contract
(reference.md §Harness JSON Output Contract).

Usage:
    uv run python scripts/bench_codemem_vs_aider.py \\
        --repo . --requested-budget 1024 --out /tmp/bench.json

jCodeMunch note: this tool is invoked via MCP protocol only; the real MCP
round-trip is exercised in Task 2.6's integration test. Here it is
stub-skipped with status='skipped'.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import tiktoken

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

# cl100k_base matches jCodeMunch's internal tokenizer (Phase-3 research).
# Cross-tool parity is the whole point of external normalization (AD-001).
_TIKTOKEN_ENCODING = "cl100k_base"


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
        if not line.startswith("│") and line.endswith(":") and line != ":":
            candidate = line[:-1]
            if "/" in candidate or _FILE_EXT_RE.search(candidate):
                current_file = candidate
                continue

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


def measure_output(text: str, symbol_count: int) -> dict[str, int]:
    """Normalize a tool's raw output into the harness measurement contract.

    Returns ``{raw_bytes, tiktoken_tokens, symbol_count}``:
    - ``raw_bytes``: UTF-8 byte count (NOT len(text), which is code points)
    - ``tiktoken_tokens``: count under ``cl100k_base`` (AD-001 parity axis)
    - ``symbol_count``: passthrough of caller-derived count (each tool has
      its own parser; this helper deliberately stays tokenizer-only)
    """
    enc = tiktoken.get_encoding(_TIKTOKEN_ENCODING)
    return {
        "raw_bytes": len(text.encode("utf-8")),
        "tiktoken_tokens": len(enc.encode(text)),
        "symbol_count": symbol_count,
    }


def jaccard(a: set[tuple[str, str]], b: set[tuple[str, str]]) -> float:
    """Jaccard similarity on (file, symbol_name) tuples. Empty-empty → 0.0."""
    if not a and not b:
        return 0.0
    return len(a & b) / len(a | b)


def _run_codemem(repo: Path, budget: int) -> dict:
    """Invoke `uv run codemem intel --budget=N --out=FILE` and collect output."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        out_path = Path(f.name)
    try:
        result = subprocess.run(
            ["uv", "run", "codemem", "intel",
             f"--budget={budget}", f"--out={out_path}"],
            cwd=repo, capture_output=True, text=True, timeout=60,
        )
        if result.returncode != 0:
            return {
                "status": "error",
                "error": f"codemem exit {result.returncode}: {result.stderr.strip()[:200]}",
                "raw_bytes": 0, "tiktoken_tokens": 0, "symbol_count": 0,
                "symbols": [],
            }
        text = out_path.read_text()
        data = json.loads(text)
        symbols = [(s["file"], s["name"]) for s in data.get("symbols", [])]
        m = measure_output(text, len(symbols))
        return {"status": "ok", **m, "symbols": symbols}
    except (subprocess.TimeoutExpired, json.JSONDecodeError, OSError) as e:
        return {
            "status": "error", "error": f"{type(e).__name__}: {e}",
            "raw_bytes": 0, "tiktoken_tokens": 0, "symbol_count": 0,
            "symbols": [],
        }
    finally:
        out_path.unlink(missing_ok=True)


def _run_aider(repo: Path, budget: int) -> dict:
    """Invoke `aider --show-repo-map --map-tokens N` and parse prose output."""
    try:
        result = subprocess.run(
            ["aider", "--show-repo-map", "--map-tokens", str(budget)],
            cwd=repo, capture_output=True, text=True, timeout=120,
        )
        if result.returncode != 0:
            return {
                "status": "error",
                "error": f"aider exit {result.returncode}: {result.stderr.strip()[:200]}",
                "raw_bytes": 0, "tiktoken_tokens": 0, "symbol_count": 0,
                "symbols": [],
            }
        text = result.stdout
        rows = parse_aider_output(text)
        symbols = [(r[0], r[1]) for r in rows]
        m = measure_output(text, len(symbols))
        return {"status": "ok", **m, "symbols": symbols}
    except (subprocess.TimeoutExpired, OSError) as e:
        return {
            "status": "error", "error": f"{type(e).__name__}: {e}",
            "raw_bytes": 0, "tiktoken_tokens": 0, "symbol_count": 0,
            "symbols": [],
        }


def _run_jcodemunch(repo: Path, budget: int) -> dict:
    """Stub: jCodeMunch is MCP-protocol only; real round-trip at Task 2.6."""
    return {
        "status": "skipped",
        "reason": (
            "jCodeMunch exposes get_ranked_context only via MCP protocol. "
            "Real MCP round-trip is exercised in Task 2.6 integration test."
        ),
        "raw_bytes": 0, "tiktoken_tokens": 0, "symbol_count": 0,
        "symbols": [],
    }


def _build_report(
    budget: int, repo: Path,
    codemem: dict, aider: dict, jcm: dict,
) -> dict:
    """Assemble the harness JSON report."""
    cm_syms = set(codemem.get("symbols", []))
    ai_syms = set(aider.get("symbols", []))
    jcm_syms = set(jcm.get("symbols", []))
    return {
        "requested_budget": budget,
        "repo": str(repo.resolve()),
        "tokenizer": _TIKTOKEN_ENCODING,
        "tools": {
            "codemem": {k: v for k, v in codemem.items() if k != "symbols"},
            "aider": {k: v for k, v in aider.items() if k != "symbols"},
            "jcodemunch": {k: v for k, v in jcm.items() if k != "symbols"},
        },
        "overlap": {
            "codemem_vs_aider": jaccard(cm_syms, ai_syms),
            "codemem_vs_jcodemunch": jaccard(cm_syms, jcm_syms),
            "aider_vs_jcodemunch": jaccard(ai_syms, jcm_syms),
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, add_help=True)
    parser.add_argument("--repo", type=Path, required=True,
                        help="Target repository root")
    parser.add_argument("--requested-budget", type=int, required=True,
                        help="Token budget for all 3 tools")
    parser.add_argument("--out", type=Path, required=True,
                        help="Output JSON path")
    args = parser.parse_args(argv)

    if not args.repo.is_dir():
        print(f"error: --repo {args.repo} is not a directory", file=sys.stderr)
        return 2

    codemem = _run_codemem(args.repo, args.requested_budget)
    aider = _run_aider(args.repo, args.requested_budget)
    jcm = _run_jcodemunch(args.repo, args.requested_budget)
    report = _build_report(args.requested_budget, args.repo, codemem, aider, jcm)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    print(f"wrote {args.out}  "
          f"(cm={codemem['status']}, ai={aider['status']}, jcm={jcm['status']})",
          file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
