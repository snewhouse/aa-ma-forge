# Migrating from `/index` to codemem

If you already use Eric Buess's `/index` ([claude-code-project-index](https://github.com/ericbuess/claude-code-project-index)), switching to codemem takes under five minutes. This document walks the switch, lists what changes, and explains what doesn't.

Both tools live side by side. You can install both and use whichever answers the question in front of you. Nothing in codemem removes, replaces, or rewrites `/index`'s files.

## Who this is for

- You use `/index` today and want to evaluate codemem against your own repo.
- You've read codemem's README and want to understand the concrete deltas from `/index` before committing.
- You've hit a case where `/index` runs out of headroom (very large repos, no git-history signals, no AA-MA coupling) and want to see whether codemem fills that gap.

If you don't use `/index`, skip this doc — install codemem directly per the README.

## Install in three commands

This assumes `/index` is already installed at `~/.claude-code-project-index/`. codemem doesn't care if it is.

```bash
# 1. Install codemem plugin dir (symlinks into ~/.claude/; no network calls).
bash /path/to/aa-ma-forge/scripts/install.sh

# 2. Drop the project-scope MCP config into your target repo.
#    This is the same pattern Claude Code uses for any other MCP server.
cat > <your-repo>/.mcp.json <<'EOF'
{
  "mcpServers": {
    "codemem": {
      "command": "uv",
      "args": ["--directory", "${PWD}", "run", "python",
               "/path/to/aa-ma-forge/claude-code/codemem/mcp/server.py"],
      "env": {
        "CODEMEM_REPO_ROOT": "${PWD}",
        "CODEMEM_DB": "${PWD}/.codemem/index.db"
      }
    }
  }
}
EOF

# 3. Open a fresh Claude Code session in that repo; approve when prompted.
#    The first MCP tool call triggers an auto-build (< 5s on ~70-file repos).
```

Alternative (user-scope install, no per-repo `.mcp.json`):

```bash
claude mcp add --scope user codemem uv --directory /path/to/aa-ma-forge \
  run python claude-code/codemem/mcp/server.py
```

After this, `/mcp` inside a fresh Claude Code session lists `codemem` as connected, alongside `project-index` if you have it installed. You can keep both.

## The six ported tools: signatures and behaviour

codemem ports `/index`'s six MCP tools with the same names. Signatures differ in small but important ways. Defaults and parameter names have shifted; one tool (`dependency_chain`) changed semantics.

| Tool | `/index` signature | codemem signature | What changed |
|------|--------------------|-------------------|--------------|
| `who_calls` | `(symbol, depth=1)` | `(name, max_depth=3, budget=8000)` | Param `symbol` → `name`. Default depth 1 → 3. Adds `budget`. |
| `blast_radius` | `(symbol, max_depth=3)` | `(name, max_depth=3, budget=8000)` | Param rename only. Same default depth. |
| `dead_code` | `()` | `(budget=8000)` | Adds `budget`. |
| `dependency_chain` | `(file_path, max_depth=5)` | `(source, target, max_depth=5, budget=8000)` | **Different purpose.** `/index` traces the import chain of a single file. codemem finds the shortest call-graph path from `source` to `target` (two symbols, not one file). |
| `search_symbols` | `(pattern, max_results=50)` — regex | `(query, budget=8000)` — substring, ranked | `/index` matches a **regex**; codemem matches a **substring** and ranks exact > prefix > contains. If you were using regex features (`.*`, `\b`, alternation), they won't work in codemem — use the plain substring. |
| `file_summary` | `(file_path)` | `(path, budget=8000)` | Adds `budget`. |

Everywhere `budget` appears: it's a token cap on the response (default 8000, ~32 KB of JSON). codemem truncates with a `truncated: true` flag rather than streaming an unbounded payload back into the context window.

### The `dependency_chain` change is the only real footgun

If you call `dependency_chain("src/auth/jwt.py")` expecting codemem to return that file's transitive imports, you'll get an error — codemem wants two symbol names, not a path. This is intentional (the two tools answer different questions) but it's the one swap where your existing prompts may silently do the wrong thing. Grep your habits for `dependency_chain` and rewrite before switching.

For the "what does this file import?" question that `/index`'s `dependency_chain` answers, codemem exposes `file_summary(path)` — the output includes import edges for that file. Not identical, but the same question.

## The six new tools (no `/index` counterpart)

codemem adds six git-mining + AA-MA-native tools that `/index` doesn't have. These are the reason to switch, not the ports.

- `hot_spots(window_days=90, top_n=10)` — files ranked by `(commits in last N days) × (function_count)`.
- `co_changes(file_path, threshold=3)` — files that change in the same commits as `file_path` AND **have no import edge to it**. Surfaces hidden coupling.
- `owners(path, refresh=False)` — per-author line-count percentages from `git blame`. Works on files or directories.
- `symbol_history(name, file_path=None)` — `git log -L:<name>:<file>` summary: first-seen commit, last-touched commit, authors, change count.
- `layers()` — three-tier ASCII onion (core / middle / periphery) based on in-degree bucketing.
- `aa_ma_context(task_name)` — surfaces codemem context for an AA-MA task: hot-spots filtered to files the task mentions, owners of those files, blast-radius for named symbols.

Two aliases are also registered for tool-search discoverability: `find_references` → `who_calls`, `find_dead_code` → `dead_code`.

## Data-model differences

### `/index` produces

A single JSON file at `PROJECT_INDEX.json` in the project root. Top-level keys (dense format): `at`, `root`, `tree`, `stats`, `f` (files), `g` (call graph edges), `d` (docs), `deps` (imports), `dir_purposes`, `staleness`, `_meta`.

Minified, ~100 KB on aa-ma-forge; auto-compressed if it exceeds a target size.

### codemem produces

- `<repo>/.codemem/index.db` — SQLite database with seven tables: `files`, `symbols`, `edges` (v1 schema), plus `commits`, `commit_files`, `ownership`, `co_change_pairs` (v2, added with the git-mining tools). `user_version = 2`.
- `<repo>/.codemem/wal.jsonl` — write-ahead log for crash-safe incremental refresh. Rotates at 10 MB with 3 compressed archives retained.
- `<repo>/.codemem/last_sha` — HEAD commit SHA at last refresh (used for `git log $last..HEAD` on incremental refresh).
- `<repo>/PROJECT_INTEL.json` (optional) — a PageRank-ranked 1024-token symbol index suitable for `@`-loading as model context.

`.codemem/` is git-ignored by default. `PROJECT_INTEL.json` is committable if you want it to be.

The two data models don't interoperate. codemem cannot read `PROJECT_INDEX.json`; `/index` can't read SQLite. You can run both and maintain two indexes, or pick one — there's no converter.

## Hook-switchover steps

`/index` uses two hooks in `~/.claude/settings.json`:

- `UserPromptSubmit` hook pointing at `i_flag_hook.py` (activates the `-i` flag behaviour).
- `Stop` hook pointing at `stop_hook.py` (regenerates `PROJECT_INDEX.json` after each session if the repo's files-hash changed).

codemem uses one hook, opt-in:

- `.git/hooks/post-commit` (per-repo, not global) appends a line that runs `codemem refresh` in the background after every commit. Wired by running `bash scripts/install.sh --wire-git-hook` from aa-ma-forge; skipped by default because it modifies git-internals in a repo that isn't aa-ma-forge's.

### Running both at once is fine

`/index`'s hooks and codemem's hook don't conflict — they run in different places (`~/.claude/settings.json` vs `<repo>/.git/hooks/post-commit`) and touch different files (`PROJECT_INDEX.json` vs `.codemem/index.db`). Neither tool reads the other's output.

### Disabling `/index` later

If you decide to turn off `/index` once you've migrated, Eric's uninstaller is `bash ~/.claude-code-project-index/uninstall.sh`. It removes the hooks, deletes the MCP registration, and leaves your `PROJECT_INDEX.json` in place so you can decide whether to commit, archive, or delete it.

## There is no `codemem import-from-index` command

The plan that bootstrapped this project had a placeholder for a `codemem import-from-index` command that would read `PROJECT_INDEX.json` and materialise it into `.codemem/index.db`. We didn't build it. Reason:

On aa-ma-forge, a cold `codemem build` takes **0.172 seconds** versus `/index`'s 0.235 seconds (measured, five trials, median — see [`docs/benchmarks/codemem-vs-index.md`](../benchmarks/codemem-vs-index.md)). Even on a 10k-LOC Python repo it's well under 10 seconds. A format-converter would be more code to write, more code to maintain, and — because the two schemas don't line up 1:1 (codemem stores git-mining data that isn't in PROJECT_INDEX.json) — a partial import would produce a degraded codemem DB that the git-mining tools would silently return empty results against.

Running `codemem build` from scratch is the simpler path. It reads the same files `/index` reads, parses them fresh, and lands an index that every codemem tool can query. No drift risk between two different serialization formats; no converter to maintain.

If your repo is large enough that `codemem build` doesn't feel fast, file an issue — the threshold for "build an importer" is empirical and we'd rather fix the build path than add a second code path to maintain.

## FAQ

**Q: Will codemem modify or read my `PROJECT_INDEX.json`?**

No. codemem ignores `PROJECT_INDEX.json` entirely. It reads source files via `git ls-files` and writes only under `<repo>/.codemem/`.

**Q: Can I disable the git post-commit hook after installing?**

Yes. Open `<repo>/.git/hooks/post-commit` and delete the line containing `codemem` (look for the sentinel comment `# codemem-post-commit-installed`). Or just don't install it in the first place — it's opt-in via `scripts/install.sh --wire-git-hook`.

**Q: Does codemem work on non-Python codebases?**

Yes. It parses `.py` via the stdlib `ast` module and `.ts`, `.tsx`, `.js`, `.go`, `.rs`, `.java`, `.rb`, `.sh` via the `ast-grep` binary (shipped in the wheel, version pinned `>=0.42,<0.43`). Each language gets a dedicated rule file; the coverage is function, class, method, import, call edges per language.

**Q: Can I migrate my `/index` shell habits — `python cli.py query who-calls foo --depth 2`?**

codemem has a CLI too. Equivalent: `codemem query who_calls foo --max-depth 2`. The CLI sub-commands mirror the six M1 tools — `build`, `status`, `refresh`, `query <tool> [args...]`, `intel`. See `codemem --help`.

**Q: I use the `-i` flag trick to auto-invoke `/index`. Does codemem have one?**

No. codemem doesn't hook `UserPromptSubmit`. Once the MCP server is registered, Claude Code has the tools available continuously — it decides when to use them based on the task. Auto-build on first query handles the cold-start case.

**Q: What if I want both tools' output available to Claude at once?**

That's the default state after migrating. Both MCP servers can be connected simultaneously and Claude will route to whichever tool is named. `/mcp` will list both; `project-index` keeps answering queries against `PROJECT_INDEX.json` and `codemem` answers against `.codemem/index.db`.

**Q: Are the kill-criteria and benchmarks actually public?**

Yes. Kill criteria at [`docs/codemem/kill-criteria.md`](kill-criteria.md) *(forthcoming in M4 Task 4.10)*. Benchmarks at [`docs/benchmarks/codemem-vs-index.md`](../benchmarks/codemem-vs-index.md) (small-repo measurements present; medium + large pending).

## What this doc doesn't cover

- The full codemem MCP tool API — see [`claude-code/codemem/README.md`](../../claude-code/codemem/README.md) *(forthcoming in M4 Task 4.4)* and [`codemem-reference.md`](../../.claude/dev/active/codemem/codemem-reference.md) §MCP Tools Public Surface.
- codemem's architecture (SQLite schema, WAL semantics, layering contract) — see [`docs/codemem/ARCHITECTURE.md`](ARCHITECTURE.md).
- `/index`'s own internals — Eric Buess's [repo README](https://github.com/ericbuess/claude-code-project-index) is authoritative.

If you hit a friction point during migration that this doc didn't anticipate, file an issue with the exact command that failed and what you expected. This doc gets updated from real migration friction, not predicted friction.
