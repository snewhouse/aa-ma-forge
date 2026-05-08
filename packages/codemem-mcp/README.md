# codemem-mcp

Structured code-memory tier for AA-MA workflows. Ships as a Claude Code MCP server.

**Status: pre-alpha.** This is the standalone distribution of [aa-ma-forge](https://github.com/snewhouse/aa-ma-forge)'s `codemem` tool. Codemem's primary role is the data layer underneath AA-MA's memory architecture; the same SQLite index also answers structural code questions via 12 MCP tools, so it works as a drop-in code-intel server in repos that don't use AA-MA.

See [`docs/codemem/positioning.md`](../../docs/codemem/positioning.md) for the v2-empirical-driven positioning decision (2026-05-08): codemem is not competing with aider's repo-map for LLM prompt injection. The two tools serve different consumer profiles.

## What it is

Codemem is two things in one binary:

1. **The structured memory tier under AA-MA** (`aa_ma_context` plus the git-mining tools). This is the durable value. Deeply integrated with the memory architecture and not easily substituted.
2. **A general code-intelligence MCP server** (call-graph + symbol-search tools). This is the optional surface, useful in any repo, but consumers who only want LLM prompt injection should pair codemem with aider's repo-map rather than substitute one for the other.

The 12 tools:

- **Call graph:** `who_calls`, `blast_radius`, `dead_code`, `dependency_chain`
- **Symbol search:** `search_symbols`, `file_summary`
- **Git mining:** `hot_spots`, `co_changes`, `owners`, `symbol_history`, `layers`
- **AA-MA-native:** `aa_ma_context` (the headline integration; no-op unless aa-ma-forge is installed)

## Design principles

- Pure Python + stdlib (no NetworkX, no scipy, no embeddings)
- `ast-grep-cli` as the only external binary dep (via pip wheel)
- SQLite-canonical storage with PageRank-budgeted JSON projection (cl100k_base honest-budget enforcement post-M1, 2026-05-05)
- AA-MA coupling (`aa_ma_context`) is the durable moat. The git-mining tools are commoditisable per kill-criteria Signal 4 (next watch: 2026-08-06).

## Install (standalone)

```bash
pip install codemem-mcp
```

## Install (with aa-ma-forge integration)

See the parent [aa-ma-forge](https://github.com/snewhouse/aa-ma-forge) README.

## Docs

Full architecture, SCIP grammar, performance SLOs, kill criteria, and migration guide live in `docs/codemem/` of the parent repo.

## License

Apache-2.0
