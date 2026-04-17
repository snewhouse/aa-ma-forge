# Security

This document explains exactly what AA-MA Forge does to your system when you install it, what the hook does at runtime, and how to report vulnerabilities. Read it before running anything.

## What install.sh does

The installer (`scripts/install.sh`) places files into `~/.claude/` so Claude Code can find them. It makes no network calls, downloads nothing, requires no sudo, does not modify your PATH, and does not set or change environment variables.

**Symlinks created** (pointing from `~/.claude/` back into this repo):

- 9 command files: `~/.claude/commands/*.md` (aa-ma-plan, execute-aa-ma-milestone, execute-aa-ma-full, execute-aa-ma-step, verify-plan, archive-aa-ma, grill-me, ops-mode, aa-ma-search)
- 13 skills directories: `~/.claude/skills/*/` (aa-ma-execution, aa-ma-plan-workflow, agent-teams, complexity-router, debugging-strategies, defense-in-depth, dispatching-parallel-agents, impact-analysis, operational-constraints, plan-verification, retro, system-mapping, token-compression)
- 2 agent files: `~/.claude/agents/aa-ma-scribe.md`, `~/.claude/agents/aa-ma-validator.md`
- 1 rules file: `~/.claude/rules/aa-ma.md`
- 2 hooks: `~/.claude/hooks/lib/pre-compact-aa-ma.sh`, `~/.claude/hooks/lib/aa-ma-session-start.sh`

**Files copied** (not symlinked, because `~/.claude/docs/` is a shared directory):

- 4 spec docs from `docs/spec/` into `~/.claude/docs/`: aa-ma-specification.md, aa-ma-quick-reference.md, aa-ma-team-guide.md, claude-code-foundations.md

**Safety features:**

- `--dry-run` previews every operation without touching the filesystem
- Before overwriting any existing (non-symlink) file, the installer backs it up to `~/.claude/backups/aa-ma-forge-YYYYMMDD-HHMMSS/` with the original directory structure preserved
- `--force` skips backups (intended for CI, not normal use)
- The installer refuses to run if the expected target directories don't exist -- it will not create `~/.claude/commands/`, `~/.claude/skills/`, etc. from scratch

**Clean removal:** `scripts/uninstall.sh` finds all symlinks pointing into this repo and removes them, deletes the copied spec docs, and optionally restores from the most recent backup (`--restore`). It also supports `--dry-run`.

## What the hook does

`pre-compact-aa-ma.sh` runs before Claude Code compacts its context window. It:

1. Checks whether any active AA-MA task directories exist under `~/.claude/dev/active/`
2. If they do, reads their task status, reference, context log, and provenance files
3. Writes a markdown snapshot to `~/.claude/hooks/cache/compaction-snapshots/`
4. Appends a one-line log entry to `~/.claude/hooks/cache/compaction.log`

It only reads and writes files under `~/.claude/`. It always exits 0, so it never blocks compaction. If there are no active tasks, it logs that fact and exits immediately.

## codemem (optional subsystem)

`codemem` is an optional code-intelligence subsystem shipped alongside AA-MA Forge. It parses your repo, indexes symbols and call edges into a local SQLite DB, and exposes 12 MCP tools to Claude Code. Installing it opts your repo into the additional behaviours below. If you haven't enabled the codemem MCP server in your `.mcp.json`, none of this applies.

### What codemem reads

On first MCP query against a repo without `.codemem/index.db`, codemem runs `git ls-files` and parses every tracked `.py`, `.ts`, `.tsx`, `.js`, `.go`, `.rs`, `.java`, `.rb`, and `.sh` file with either the Python stdlib `ast` module or the `ast-grep` binary. It reads full file contents into memory, computes SHA-256 hashes, and stores signatures plus intra- and cross-file call edges to `<repo>/.codemem/index.db` (SQLite).

codemem does **not** transmit anything off the machine. All parsing is local. Subprocess calls to `git` and `ast-grep` use `shell=False` and `--` separators; no shell interpolation.

### Trusted-environment recommendation

Running codemem against a repo gives it read access to everything `git ls-files` returns. If your repo contains files you would not otherwise feed into a parser, audit before running. The general risk class is the one the LLM-tooling ecosystem learned from the litellm 2026 supply-chain incident: any tool that reads source into a process space inherits the source's blast radius. codemem is not immune.

Practical guidance:

- Don't run codemem against repos you don't trust enough to also `pip install -e .` from.
- If you're evaluating an unknown dependency, run codemem in a disposable environment (a fresh container, a throwaway user account, or a VM).
- codemem never executes code it indexes. But `ast-grep`'s parser runs on arbitrary input, and parsers have had CVEs before. Pin the `ast-grep-cli>=0.42,<0.43` range; review changelogs before bumping.

### Input sanitization contract

All 12 MCP tool arguments are sanitized before reaching SQL or `subprocess`:

- **Symbol / name arguments** must match the allow-list regex `^[A-Za-z0-9_./\-]{1,256}$`. Non-matching input returns a structured error dict. No SQL escape; no shell escape — rejection happens before either layer is reached.
- **File-path arguments** run the symbol check first, then resolve to an absolute path via `Path.resolve(strict=False)`, then verify the result is relative to the repo root. `../../etc/passwd`, `/etc/passwd`, and `foo/../../bar` all reject before any syscall.
- The adversarial test suite (`tests/codemem/test_mcp_tools.py`) exercises 11 injection vectors including `'; DROP TABLE`, 10 KB unicode, and regex metachars.

All MCP connections open SQLite via `file:...?mode=ro` URI — the tool surface is strictly non-mutating. The single writer is the indexer (`codemem build` / auto-build-on-first-query), gated by an `fcntl` / `msvcrt` lock at `<repo>/.codemem/db.lock`.

Import-linter contracts enforce that the plugin-surface handlers in `claude-code/codemem/mcp/server.py` cannot bypass the sanitization layer by importing codemem internals directly. CI fails on boundary violations.

### SQLite WAL file growth

codemem uses SQLite journal mode WAL for crash safety. The WAL file (`<repo>/.codemem/index.db-wal`) can grow during bulk inserts. On a cold `codemem build` of a ~70-file repo the WAL stays under 100 KB; on 10k-LOC repos it typically reaches a few MB before a checkpoint.

SQLite auto-checkpoints on connection close. If you kill the indexer mid-build the WAL can outlive its parent — re-running `codemem build` replays it cleanly. To flush manually: `sqlite3 .codemem/index.db "PRAGMA wal_checkpoint(TRUNCATE);"`.

codemem also maintains a second write-ahead log in JSONL form (`<repo>/.codemem/wal.jsonl`) used for crash-safe incremental refresh. It rotates at 10 MB with 3 compressed archives retained — unbounded growth is not possible.

## Prompt files trust model

The commands, skills, agents, and rules in this repo are declarative markdown files. They are not shell scripts or executables. Claude Code's runtime reads them as prompt instructions.

They run with whatever permissions your Claude Code session already has. Installing AA-MA Forge does not grant Claude Code any new capabilities or escalate privileges. If Claude Code can't do something before you install this, it still can't do it after.

Every file is plain text. You can read the lot in under an hour. I'd encourage you to do that before installing.

## Reporting vulnerabilities

If you find a security issue:

- **Preferred:** Use GitHub's [private vulnerability reporting](https://github.com/snewhouse/aa-ma-forge/security/advisories/new)
- **Email:** stephen.j.newhouse@gmail.com

Response time is best effort. This is a one-person project maintained in my own time.

## Verification

- All commits are by Stephen J Newhouse (stephen.j.newhouse@gmail.com)
- The repo uses conventional commits and semantic versioning
- Run `scripts/install.sh --dry-run` to see exactly what would happen before committing to an install
