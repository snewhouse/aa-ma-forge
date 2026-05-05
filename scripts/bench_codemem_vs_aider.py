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


def rbo_at_10(
    list_s: list, list_t: list, p: float = 0.9, k: int = 10
) -> float:
    """Rank-Biased Overlap, extrapolated form (Webber, Moffat, Zobel 2010).

    Top-heavy similarity in [0, 1] for two ranked lists. Identical rankings
    of length >= k → 1.0. Disjoint rankings → 0.0.

    Formula (Webber 2010 eq. 8, truncated to depth k):
        RBO_ext = (1-p) * Σ_{d=1..k} p^(d-1) * |S[:d] ∩ T[:d]| / d
                + p^k * |S[:k] ∩ T[:k]| / k

    The extrapolation tail (second term) assumes unobserved depths beyond k
    agree at the same rate as the observed depth-k agreement. ``p=0.9``
    weights the top of the list ~10x more than the bottom over a 10-deep
    window; this is the convention in the original paper.

    Args:
        list_s, list_t: Ranked sequences. Items must be hashable.
        p: Persistence parameter (top-heaviness). Default 0.9.
        k: Truncation depth. Default 10.

    Returns:
        Float in [0.0, 1.0].
    """
    if not list_s and not list_t:
        return 0.0

    s_set: set = set()
    t_set: set = set()
    summation = 0.0
    for d in range(1, k + 1):
        if d <= len(list_s):
            s_set.add(list_s[d - 1])
        if d <= len(list_t):
            t_set.add(list_t[d - 1])
        agreement_d = len(s_set & t_set) / d
        summation += (p ** (d - 1)) * agreement_d

    rbo_truncated = (1.0 - p) * summation
    agreement_k = len(s_set & t_set) / k
    rbo_extrapolated = rbo_truncated + (p ** k) * agreement_k
    return rbo_extrapolated


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


def _run_aider(repo: Path, budget: int, *, tokeniser_equalise: bool = False) -> dict:
    """Invoke `aider --show-repo-map --map-tokens N` and parse prose output.

    When ``tokeniser_equalise=True`` (M2a.3, AD-V2-005), append
    ``--model gpt-3.5-turbo`` so litellm routes Aider through cl100k_base —
    the same tokeniser used by codemem (post-M1) and jCodeMunch. This makes
    the requested-budget comparable across all 3 tools.

    Verified live (M2a.2 probe): ``--show-repo-map --model gpt-3.5-turbo``
    works without OPENAI_API_KEY (warning-only) because `--show-repo-map`
    is a pure-local tokeniser operation; the API key is only needed for
    actual LLM completions.
    """
    args = ["aider", "--show-repo-map", "--map-tokens", str(budget)]
    if tokeniser_equalise:
        args += ["--model", "gpt-3.5-turbo"]
    try:
        result = subprocess.run(
            args,
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


def _parse_munch_gen1(text: str) -> list[tuple[str, str]]:
    """Parse jCodeMunch MUNCH/gen1 response into (file, symbol_name) tuples.

    The MUNCH on-wire format has 4 sections separated by blank lines:
    header, legends (@N=value lines), scalars (key=value), tables (CSV-style
    rows where the first field is a table tag).

    Legend tokens are *prefix substitution*: ``@1foo.py`` means
    ``<value-of-@1>`` concatenated with literal ``foo.py``. We must match
    the longest @N first to avoid `@1` shadowing `@11`.

    Returns ``[(file, name), ...]`` extracted from the ``ranked_symbols``
    table emitted by ``get_symbol_importance``. The ``symbol_id`` field
    has format ``<file>::<name>#<kind>`` per jcodemunch's contract.
    """
    sections = text.split("\n\n")
    if len(sections) < 2:
        return []

    # Build legend dict from any section that has @N=value lines.
    legends: dict[str, str] = {}
    for sec in sections:
        for line in sec.splitlines():
            line = line.strip()
            if line.startswith("@") and "=" in line:
                handle, _, value = line.partition("=")
                if handle[1:].isdigit():
                    legends[handle] = value

    # Sort handles longest-first for prefix-substitution
    sorted_handles = sorted(legends.keys(), key=lambda h: -len(h))

    def _decode(token: str) -> str:
        if not token.startswith("@"):
            return token
        for handle in sorted_handles:
            if token.startswith(handle):
                return legends[handle] + token[len(handle):]
        return token

    rows: list[tuple[str, str]] = []
    # Walk every line; rows are CSV starting with `t,`. Rows may live in
    # any section; in practice they're in the last section.
    import csv as _csv
    from io import StringIO as _StringIO

    for line in text.splitlines():
        if not line.startswith("t,"):
            continue
        reader = _csv.reader(_StringIO(line))
        for fields in reader:
            if len(fields) < 2:
                continue
            # fields[0] = "t" tag; fields[1] = symbol_id_token
            symbol_id = _decode(fields[1])
            # Format: <file>::<name>#<kind>
            if "::" not in symbol_id:
                continue
            file, _, name_kind = symbol_id.partition("::")
            name = name_kind.partition("#")[0] if "#" in name_kind else name_kind
            if file and name:
                rows.append((file, name))
    return rows


_JCM_TOKENS_PER_ROW = 25  # cl100k_base envelope per ranked_symbols row


def _run_jcodemunch(repo: Path, budget: int) -> dict:
    """Invoke jcodemunch-mcp via MCP stdio, call get_symbol_importance, parse.

    Pivoted 2026-05-05 (AD-V2-008) from `get_ranked_context` (encoder bug
    in jcodemunch-mcp 1.59.1's rc1 schema → empty data rows) to
    `get_symbol_importance` which uses gen1 encoding correctly. Pure
    PageRank, no BM25 — apples-to-apples with codemem's M1 fix.

    Budget mapping: jCodeMunch's natural interface is ``top_n`` (symbol
    count) not tokens. We map ``budget → top_n = max(10, budget // 25)``
    using an empirical 25 tokens-per-row envelope for the gen1 encoded
    ``ranked_symbols`` table. The harness re-tokenizes the response at
    the measurement boundary (``measure_output``) so the actual reported
    tiktoken count is honest regardless of slight over/under-shoot.
    """
    top_n = max(10, budget // _JCM_TOKENS_PER_ROW)
    import asyncio
    import json as _json

    async def _call() -> tuple[str, list[tuple[str, str]]]:
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client

        params = StdioServerParameters(
            command="jcodemunch-mcp",
            args=["serve", "--transport", "stdio"],
            env=None,
        )
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                idx = await session.call_tool(
                    "index_folder",
                    arguments={"path": str(repo)},
                )
                idx_data = _json.loads(idx.content[0].text)
                if not idx_data.get("success", True):
                    raise RuntimeError(f"index_folder failed: {idx_data}")
                repo_id = idx_data["repo"]
                result = await session.call_tool(
                    "get_symbol_importance",
                    arguments={
                        "repo": repo_id,
                        "top_n": top_n,
                        "algorithm": "pagerank",
                    },
                )
                response_text = result.content[0].text
                rows = _parse_munch_gen1(response_text)
                return response_text, rows

    try:
        text, rows = asyncio.run(asyncio.wait_for(_call(), timeout=120))
        m = measure_output(text, len(rows))
        return {"status": "ok", **m, "symbols": rows}
    except Exception as e:
        return {
            "status": "error",
            "error": f"{type(e).__name__}: {str(e)[:200]}",
            "raw_bytes": 0, "tiktoken_tokens": 0, "symbol_count": 0,
            "symbols": [],
        }


def _pair_overlap(
    list_a: list[tuple[str, str]],
    list_b: list[tuple[str, str]],
) -> dict[str, float]:
    """Both Jaccard (set similarity) and RBO@10 (rank-aware similarity)
    for a single tool-pair. Symmetric in arguments — Jaccard always is,
    and RBO is treated as such by averaging both directions to remove
    asymmetry-of-tail-extrapolation noise (Webber 2010 §4.2)."""
    set_a, set_b = set(list_a), set(list_b)
    rbo_ab = rbo_at_10(list_a, list_b, p=0.9, k=10)
    rbo_ba = rbo_at_10(list_b, list_a, p=0.9, k=10)
    return {
        "jaccard": jaccard(set_a, set_b),
        "rbo_at_10": (rbo_ab + rbo_ba) / 2.0,
    }


_REPOMIX_FILE_PATH_RE = re.compile(
    r"""<file\s+path\s*=\s*["']([^"']+)["']\s*>"""
)


def _extract_repomix_file_paths(text: str) -> list[str]:
    """Extract file paths from Repomix XML output.

    Repomix --style xml emits `<file path="<path>">...</file>` blocks.
    File paths are the smallest semantic unit Repomix surfaces — there is
    no symbol-level data. Returns the paths in document order.

    Returns ``[]`` for empty/non-XML input rather than raising.
    """
    return _REPOMIX_FILE_PATH_RE.findall(text)


def _run_repomix(repo: Path, budget: int) -> dict:
    """Invoke pinned Repomix CLI via npx, capture XML, re-tokenize.

    Pinned invocation (per reference.md):
        npx -y repomix@1.14.0 --style xml --output FILE \\
            --token-count-encoding cl100k_base <repo>

    Repomix is a *dump-everything* tool with no native budget concept.
    The harness reports the full output measurement honestly. The
    ``budget`` parameter is unused at invocation time but the response
    is re-tokenized with cl100k_base at measurement boundary for
    cross-tool parity. Empirically (2026-05-05): aa-ma-forge full repo
    produces ~551k cl100k_base tokens.

    Returns ``status="ok_no_symbols"`` per plan AC: Repomix doesn't
    produce symbol-level output; the empty symbols list is intentional.
    """
    with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False) as f:
        out_path = Path(f.name)
    try:
        result = subprocess.run(
            [
                "npx", "-y", "repomix@1.14.0",
                "--style", "xml",
                "--output", str(out_path),
                "--token-count-encoding", "cl100k_base",
                str(repo),
            ],
            cwd=repo, capture_output=True, text=True, timeout=300,
        )
        if result.returncode != 0:
            return {
                "status": "error",
                "error": f"repomix exit {result.returncode}: {result.stderr.strip()[-200:]}",
                "raw_bytes": 0, "tiktoken_tokens": 0, "symbol_count": 0,
                "symbols": [],
            }
        text = out_path.read_text()
        paths = _extract_repomix_file_paths(text)
        m = measure_output(text, symbol_count=0)
        m["file_count"] = len(paths)
        return {
            "status": "ok_no_symbols",
            **m,
            "symbols": [],
        }
    except (subprocess.TimeoutExpired, OSError) as e:
        return {
            "status": "error", "error": f"{type(e).__name__}: {e}",
            "raw_bytes": 0, "tiktoken_tokens": 0, "symbol_count": 0,
            "symbols": [],
        }
    finally:
        out_path.unlink(missing_ok=True)


def _build_report(
    budget: int, repo: Path,
    codemem: dict, aider: dict, jcm: dict, repomix: dict | None = None,
) -> dict:
    """Assemble the harness JSON report.

    M2a.6 (AD-V2-006): each overlap pair now emits both jaccard (set) and
    rbo_at_10 (rank-aware) similarity. Shape changed from scalar-per-pair
    to dict-per-pair.

    M2b: optional ``repomix`` argument adds a 4th tool to the tools dict.
    Repomix has no symbol-level output; ``status="ok_no_symbols"`` and
    an empty ``symbols`` list. Overlap stays 3-tool (codemem/aider/jcm)
    until M2c full 5-tool sweep adds Yek and switches to 10-pair overlap.
    """
    cm_list = list(codemem.get("symbols", []))
    ai_list = list(aider.get("symbols", []))
    jcm_list = list(jcm.get("symbols", []))
    tools = {
        "codemem": {k: v for k, v in codemem.items() if k != "symbols"},
        "aider": {k: v for k, v in aider.items() if k != "symbols"},
        "jcodemunch": {k: v for k, v in jcm.items() if k != "symbols"},
    }
    if repomix is not None:
        tools["repomix"] = {k: v for k, v in repomix.items() if k != "symbols"}
    return {
        "requested_budget": budget,
        "repo": str(repo.resolve()),
        "tokenizer": _TIKTOKEN_ENCODING,
        "tools": tools,
        "overlap": {
            "codemem_vs_aider": _pair_overlap(cm_list, ai_list),
            "codemem_vs_jcodemunch": _pair_overlap(cm_list, jcm_list),
            "aider_vs_jcodemunch": _pair_overlap(ai_list, jcm_list),
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
    parser.add_argument(
        "--aider-tokeniser-equalise", action="store_true",
        help=("Run Aider with --model gpt-3.5-turbo so litellm routes through "
              "cl100k_base, matching codemem (post-M1) and jCodeMunch. "
              "Verified live: works without OPENAI_API_KEY (warning-only)."),
    )
    parser.add_argument(
        "--include-repomix", action="store_true",
        help=("Add Repomix to the tools panel (M2b). Repomix is a "
              "dump-everything tool with no native budget; expect ~500k+ "
              "tokens on aa-ma-forge. Disabled by default to keep the "
              "default invocation fast."),
    )
    args = parser.parse_args(argv)

    if not args.repo.is_dir():
        print(f"error: --repo {args.repo} is not a directory", file=sys.stderr)
        return 2

    codemem = _run_codemem(args.repo, args.requested_budget)
    aider = _run_aider(
        args.repo, args.requested_budget,
        tokeniser_equalise=args.aider_tokeniser_equalise,
    )
    jcm = _run_jcodemunch(args.repo, args.requested_budget)
    repomix = _run_repomix(args.repo, args.requested_budget) if args.include_repomix else None
    report = _build_report(
        args.requested_budget, args.repo, codemem, aider, jcm, repomix=repomix
    )

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    statuses = (
        f"cm={codemem['status']}, ai={aider['status']}, jcm={jcm['status']}"
    )
    if repomix is not None:
        statuses += f", rpx={repomix['status']}"
    print(f"wrote {args.out}  ({statuses})", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
