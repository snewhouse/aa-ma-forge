# codemem-mcp

Lightweight codebase intelligence MCP tool for Claude Code.

**Status: pre-alpha.** This is the standalone distribution of [aa-ma-forge](https://github.com/snewhouse/aa-ma-forge)'s `codemem` tool. The full plan lives at `.claude/dev/active/codemem/codemem-plan.md` in the parent repository.

## What it is

A code-intelligence MCP server exposing 12 tools for structural queries over your codebase:

- **Call graph:** `who_calls`, `blast_radius`, `dead_code`, `dependency_chain`
- **Symbol search:** `search_symbols`, `file_summary`
- **Git intelligence:** `hot_spots`, `co_changes`, `owners`, `symbol_history`, `layers`
- **AA-MA-native:** `aa_ma_context` (no-op unless aa-ma-forge is installed)

## Design principles

- Pure Python + stdlib (no NetworkX, no scipy, no embeddings)
- `ast-grep-cli` as the only external binary dep (via pip wheel)
- SQLite-canonical storage with small PageRank-budgeted JSON projection
- Git-mining quintet is the differentiator — no competitor ships this combo

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
