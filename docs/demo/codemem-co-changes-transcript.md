# `co_changes` demo: editorial coupling in aa-ma-forge

Real transcript of `mcp__codemem__co_changes` against `README.md` in this repo. Captured 2026-04-18 against commit `ebda2f4` (the kill-criteria doc commit).

The point of `co_changes` is to surface coupling that the AST cannot see: files that are routinely committed together but never import each other. For source code the typical hits are pairs like `service.py` ↔ `test_service.py`. For markdown — the case below — the hits are **editorial coupling**: docs that are kept in sync by discipline rather than by code.

## Reproduce this yourself

Assuming codemem is installed (see [`install-zero-config.md`](../codemem/install-zero-config.md)):

```bash
cd /path/to/aa-ma-forge

# One-off: populate the git-mining cache.
uv run codemem refresh-commits
# → codemem refresh-commits: inserted 128 commits (cap=500) — .codemem/index.db

# Run the query (here via the Python tool function; the agent uses the
# MCP tool of the same name).
uv run python -c "
from pathlib import Path
from codemem.mcp_tools import co_changes
import json
out = co_changes(Path('.codemem/index.db'), 'README.md', threshold=2, top_n=10)
print(json.dumps(out, indent=2))
"
```

In a Claude Code session the agent does this directly:

```
agent invokes: mcp__codemem__co_changes(file_path="README.md", threshold=2, top_n=10)
```

## The output (verbatim)

```json
{
  "files": [
    {
      "path": "docs/spec/claude-code-foundations.md",
      "count": 5
    },
    {
      "path": "SECURITY.md",
      "count": 4
    },
    {
      "path": "docs/spec/aa-ma-quick-reference.md",
      "count": 3
    },
    {
      "path": "claude-code/agents/aa-ma-scribe.md",
      "count": 2
    },
    {
      "path": "claude-code/commands/verify-plan.md",
      "count": 2
    },
    {
      "path": "claude-code/skills/llm-evaluation/SKILL.md",
      "count": 2
    },
    {
      "path": "docs/narrative/how-we-got-here.md",
      "count": 2
    },
    {
      "path": "docs/plans/2026-04-05-aa-ma-forge-implementation.md",
      "count": 2
    },
    {
      "path": "docs/spec/aa-ma-specification.md",
      "count": 2
    },
    {
      "path": "docs/spec/aa-ma-team-guide.md",
      "count": 2
    }
  ],
  "target": "README.md",
  "threshold": 2,
  "error": null,
  "truncated": false
}
```

`count` is the number of distinct commits in which both `README.md` and the listed file appeared together. `threshold=2` means we filter out single-commit coincidences. `top_n=10` caps the result.

## What this shows

None of the ten files import or reference `README.md` — there's no symbol edge between any of them. They appear here purely because of human editorial discipline. The pattern that falls out:

- **`docs/spec/claude-code-foundations.md`, `docs/spec/aa-ma-quick-reference.md`, `docs/spec/aa-ma-specification.md`, `docs/spec/aa-ma-team-guide.md`** — every time the README adds or removes a feature, the matching spec and quick-reference docs need updating. The CLAUDE.md project file explicitly warns about this: *"Hardcoded counts go stale. When adding/removing assets, update counts in: README.md, … `docs/spec/claude-code-foundations.md`, `docs/spec/aa-ma-quick-reference.md`."* This output is that warning made measurable.
- **`SECURITY.md`** — when a new component ships in the README it usually adds a security surface that needs documenting.
- **`claude-code/agents/aa-ma-scribe.md`, `claude-code/commands/verify-plan.md`, `claude-code/skills/llm-evaluation/SKILL.md`** — README updates that announce new agents/commands/skills always touch the corresponding asset file. Three different examples in this snapshot.
- **`docs/narrative/how-we-got-here.md`, `docs/plans/2026-04-05-aa-ma-forge-implementation.md`** — long-form context docs that get refreshed alongside the README at major version moments.

The signal an agent gets from this output: *"if you're about to edit README.md, you probably also need to think about these ten files — and a doc-drift check should be aware of the relationship."* No import-graph analyzer can see any of this.

## Why this matters

Most code-intelligence tools operate on the AST: imports, calls, types. That's correct for source code but blind to documentation, configuration, and any system where coupling is editorial rather than syntactic. `co_changes` makes those couplings inspectable using the same git history every dev already has on disk — no embeddings, no graph database, no cloud round-trip.

For source files (try `co_changes("packages/codemem-mcp/src/codemem/storage/db.py")` against this repo) the same technique surfaces test-file coupling, refactoring co-touches, and migration sequences. The mechanism is identical; the interpretation shifts based on what kind of file you query.

## Limits

- The result depends on git history. Files added in a single commit that have never co-changed since will not appear at any threshold.
- The default `_DEFAULT_CO_CHANGES_EXCLUDE` filters `CHANGELOG.md` and `README.md` from results because they're touched alongside almost everything. Pass `exclude=()` to disable, or `exclude=("docs/foo.md",)` to add custom exclusions.
- The cache caps at 500 commits by default (`--limit N` on `codemem refresh-commits` to override). Older history is not consulted until you raise the cap or trim the cache.

## Cross-refs

- Install + first-query walkthrough: [`install-zero-config.md`](../codemem/install-zero-config.md)
- Full tool reference: [`claude-code/codemem/README.md`](../../claude-code/codemem/README.md)
- What would make us drop this tool: [`kill-criteria.md`](../codemem/kill-criteria.md) — see signal #3 (M3 headline-tool kill).
