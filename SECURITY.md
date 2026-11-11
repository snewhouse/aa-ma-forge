# Security

This document explains exactly what AA-MA Forge does to your system when you install it, what the hook does at runtime, and how to report vulnerabilities. Read it before running anything.

## What install.sh does

The installer (`scripts/install.sh`) places files into `~/.claude/` so Claude Code can find them. It makes no network calls, downloads nothing, requires no sudo, does not modify your PATH, and does not set or change environment variables.

**Symlinks created** (pointing from `~/.claude/` back into this repo):

- 40 skills directories: `~/.claude/skills/*/` (aa-ma-chart, aa-ma-execution, aa-ma-plan, aa-ma-plan-workflow, aa-ma-research, aa-ma-search, aa-ma-share, agent-teams, archive-aa-ma, assess-codebase, bash-defensive-patterns, complexity-router, debugging-strategies, defense-in-depth, dispatching-parallel-agents, execute-aa-ma-full, execute-aa-ma-milestone, execute-aa-ma-step, goal-condition-synthesis, grill-with-docs, grilling, impact-analysis, language-conventions, llm-output-safety, logging-and-comments, operational-constraints, ops-mode, plan-verification, prototype, python-quality-gates, retro, secops, secrets-management, sole-dev-merge, system-mapping, token-compression, understand-codebase, verify-impl, verify-plan, writing-for-agents)
- 13 agent files: `~/.claude/agents/*.md` (aa-ma-researcher, aa-ma-scribe, aa-ma-validator, code-reviewer, codebase-assessor, codebase-onboarding-conventions, codebase-onboarding-health, codebase-onboarding-runbook, codebase-onboarding-synthesizer, context7-evidence-auditor, future-proofing-auditor, security-auditor, tdd-sequence-auditor)
- 3 rules files: `~/.claude/rules/aa-ma.md`, `~/.claude/rules/engineering-standards.md`, `~/.claude/rules/coding-standards.md`
- 10 hooks: `~/.claude/hooks/lib/*.sh` (aa-ma-commit-drift, aa-ma-commit-signature, aa-ma-impact-preedit, aa-ma-plan-marker, aa-ma-plan-skip-warn, aa-ma-session-end-dirty, aa-ma-session-start, pre-compact-aa-ma, ruff-format, security-static-check)
- 2 library helpers in the same directory, not event hooks: `~/.claude/hooks/lib/aa-ma-parse.sh` (sourced by the hooks) and `~/.claude/hooks/lib/aa-ma-chart-guard.sh` (invoked from the `/aa-ma-chart` and `/aa-ma-plan --from-map` command bodies)

**Files copied** (not symlinked, because `~/.claude/docs/` is a shared directory):

- 5 spec docs from `docs/spec/` into `~/.claude/docs/`: aa-ma-specification.md, aa-ma-quick-reference.md, aa-ma-team-guide.md, claude-code-foundations.md, plan-marker-grammar.md

**Safety features:**

- `--dry-run` previews every operation without touching the filesystem
- Before overwriting any existing (non-symlink) file, the installer backs it up to `~/.claude/backups/aa-ma-forge-YYYYMMDD-HHMMSS/` with the original directory structure preserved
- `--force` skips backups (intended for CI, not normal use)
- The installer refuses to run if the expected target directories don't exist -- it will not create `~/.claude/skills/`, `~/.claude/agents/`, etc. from scratch

**Clean removal:** `scripts/uninstall.sh` finds all symlinks pointing into this repo and removes them, deletes the copied spec docs, and optionally restores from the most recent backup (`--restore`). It also supports `--dry-run`.

## What the hook does

`pre-compact-aa-ma.sh` runs before Claude Code compacts its context window. It:

1. Checks whether any active AA-MA task directories exist under `~/.claude/dev/active/`
2. If they do, reads their task status, reference, context log, and provenance files
3. Writes a markdown snapshot to `~/.claude/hooks/cache/compaction-snapshots/`
4. Appends a one-line log entry to `~/.claude/logs/hooks.log` (override with `CLAUDE_HOOK_LOG`)

It only reads and writes files under `~/.claude/`. It always exits 0, so it never blocks compaction. If there are no active tasks, it logs that fact and exits immediately.

## codemem (optional subsystem)

`codemem` is an optional code-intelligence subsystem shipped alongside AA-MA Forge. It parses your repo, indexes symbols and call edges into a local SQLite DB, and exposes 14 MCP tools to Claude Code. Installing it opts your repo into the additional behaviours below. If you haven't enabled the codemem MCP server in your `.mcp.json`, none of this applies.

### What codemem reads

On first MCP query against a repo without an index, codemem runs `git ls-files` and parses every tracked `.py`, `.ts`, `.tsx`, `.js`, `.go`, `.rs`, `.java`, `.rb`, and `.sh` file with either the Python stdlib `ast` module or the `ast-grep` binary. It reads full file contents into memory, computes SHA-256 hashes, and stores signatures plus intra- and cross-file call edges to `index.db` (SQLite) in the index dir: by default `${XDG_CACHE_HOME:-~/.cache}/codemem/<sha256(realpath repo root)>/`, outside the repo; `--db` or `CODEMEM_DB` overrides it.

codemem does **not** transmit anything off the machine. All parsing is local. Subprocess calls to `git` and `ast-grep` use `shell=False` and `--` separators; no shell interpolation.

### Trusted-environment recommendation

Running codemem against a repo gives it read access to everything `git ls-files` returns. If your repo contains files you would not otherwise feed into a parser, audit before running. The general risk class is the one the LLM-tooling ecosystem learned from the litellm 2026 supply-chain incident: any tool that reads source into a process space inherits the source's blast radius. codemem is not immune.

Practical guidance:

- Don't run codemem against repos you don't trust enough to also `pip install -e .` from.
- If you're evaluating an unknown dependency, run codemem in a disposable environment (a fresh container, a throwaway user account, or a VM).
- codemem never executes code it indexes. But `ast-grep`'s parser runs on arbitrary input, and parsers have had CVEs before. Pin the `ast-grep-cli>=0.42,<0.43` range; review changelogs before bumping.

### Input sanitization contract

All 14 MCP tool arguments are sanitized before reaching SQL or `subprocess`:

- **Symbol / name arguments** must match the allow-list regex `^[A-Za-z0-9_./\-]{1,256}$`. Non-matching input returns a structured error dict. No SQL escape; no shell escape — rejection happens before either layer is reached.
- **File-path arguments** run the symbol check first, then resolve to an absolute path via `Path.resolve(strict=False)`, then verify the result is relative to the repo root. `../../etc/passwd`, `/etc/passwd`, and `foo/../../bar` all reject before any syscall.
- **`diagram`** takes no symbol or path into SQL: `level` must be one of `L0`–`L3`, `hops` 0–10 (the neighbourhood walk loops that many times), and `scope` — a path prefix matched in Python only, spaces allowed — at most 1024 printable characters. Its labels are file and symbol names from the indexed repo: entity-escaped for mermaid, but still untrusted text for the agent that reads them.
- The adversarial test suite (`tests/codemem/test_mcp_tools.py`) exercises 11 injection vectors including `'; DROP TABLE`, 10 KB unicode, and regex metachars.

All MCP connections open SQLite via `file:...?mode=ro` URI — the tool surface is strictly non-mutating. The single writer is the indexer (`codemem build`, auto-build-on-first-query, and `codemem refresh` — run by the post-commit step, or as a subprocess capped at 5 s when a query finds the index stale), gated by an `fcntl` / `msvcrt` lock at `db.lock` in the index dir. The refresh never imports from the repo (`python -I`), pins `core.fsmonitor=false` / `core.hooksPath=/dev/null` on its git calls, and refuses to open, build, refresh or serve an index dir that is or holds a symlink or cannot be listed (`codemem.safety.check_db_path`, applied by `storage.db.connect` for every reader and writer; `stale_reason: unsafe_db_path`). A `CODEMEM_DB` can point into a repo, which can commit (or a zip can ship) a whole index whose rows do not match the code, so codemem serves only an index it built here: a DB file codemem creates is stamped with this user's random nonce for that directory, kept outside every repo in `$XDG_STATE_HOME/codemem/trust/` (mode 0600); a read-only open refuses an unstamped or foreign index, a refresh rebuilds it, and a query is never answered from it (`stale_reason: untrusted`). Git-based detection of a committed index was dropped after four bypasses (§6.8, M15). `aa_ma.render.graph` applies both rules before the §13 diagram fence reads the index. Known limits: `codemem replay --from-wal` trusts its journal (replay only a journal codemem wrote on this machine). The default index lives outside the repo (Milestone 16 of code-conventions-impact); a `CODEMEM_DB` pointed inside a repo is repo-controlled and keeps the M15 limits (a planted `index.db-wal` replayed or `index.db-journal` rolled back into a stamped index, and a committed stamped index publishing its stamp), though the trust token still refuses a foreign DB. A trust-store fault (an unreadable `$XDG_STATE_HOME`, a trust directory that is not private to this user, a record that is not a nonce) is reported as such (`stale_reason: trust_store`), never as a hostile index; records are read with `O_NOFOLLOW` and written whole (`fsync`, then `link`). The shell readers of `last_sha` and `graphify-out/.built_sha` refuse links the same way, and the post-commit worker skips graphify when `graphify-out/` holds a link. `aa_ma_context(write=True)` refuses a linked task path and appends with `O_NOFOLLOW`.

Import-linter contracts enforce that the plugin-surface handlers in `claude-code/codemem/mcp/server.py` cannot bypass the sanitization layer by importing codemem internals directly. CI fails on boundary violations.

### Generated architecture docs

`codemem draw --write` writes only under `docs/architecture/`: every target is resolved and checked before any file is written, the authored captions sidecar (`docs/architecture.captions.json`) can never be a target, and an existing file without codemem's generated stamp on line 1 — a team's own architecture doc — is never overwritten (the whole write is refused). Caption prose is escaped into one inert markdown line; mermaid labels entity-escape `" # < > % { }` and backtick, so a file name cannot inject a `%%{init}%%` directive. `codemem draw --check` is read-only.

### SQLite WAL file growth

codemem uses SQLite journal mode WAL for crash safety. The WAL file (`index.db-wal` in the index dir) can grow during bulk inserts. On a cold `codemem build` of a ~70-file repo the WAL stays under 100 KB; on 10k-LOC repos it typically reaches a few MB before a checkpoint.

SQLite auto-checkpoints on connection close. If you kill the indexer mid-build the WAL can outlive its parent — re-running `codemem build` replays it cleanly. To flush manually: `sqlite3 <index dir>/index.db "PRAGMA wal_checkpoint(TRUNCATE);"` (`codemem status` prints the DB path).

codemem can also keep a second write-ahead log in JSONL form (`wal.jsonl` in the index dir), replayable with `codemem replay --from-wal`; it is written only when a caller passes `build_index(wal_path=…)` from Python; `codemem build` and `codemem refresh` do not write it (checked 2026-10-14). It rotates at 10 MB with 3 compressed archives retained — unbounded growth is not possible.

## Prompt files trust model

The skills, agents, and rules in this repo are declarative markdown files. They are not shell scripts or executables. Claude Code's runtime reads them as prompt instructions.

They run with whatever permissions your Claude Code session already has. Installing AA-MA Forge does not grant Claude Code any new capabilities or escalate privileges. If Claude Code can't do something before you install this, it still can't do it after.

Every file is plain text. You can read the lot in under an hour. I'd encourage you to do that before installing.

## Security scanning

- **Commit time (Claude Code sessions only):** `security-static-check.sh` (PreToolUse, blocking) runs the forge-pinned Ruff S on each whole `.py` file the commit can contain (staged, or modified for `-a`), plus two regex classes on added lines. A plain `git commit` in a terminal is not screened. It is a best-effort guardrail; CI is the enforcement (ADR-0022).
- **CI (`.github/workflows/security.yml`):** `ruff-security` (Ruff S over `src/`, `packages/`, `scripts/`), `gitleaks` (full history; `.gitleaksignore` holds fingerprints only), `deps` (pip-audit over the hashed `uv export`; `.pip-audit-ignore` entries expire), ShellCheck, and a weekly scheduled run. Dependabot updates actions and uv weekly.
- A missing scanner is never silent: a CI job fails, `/sole-dev-merge` reports it as UNKNOWN, and at commit time a missing ruff prints a warning (the commit still goes through; CI still runs Ruff S).

## Reporting vulnerabilities

If you find a security issue:

- **Preferred:** Use GitHub's [private vulnerability reporting](https://github.com/snewhouse/aa-ma-forge/security/advisories/new)
- **Email:** stephen.j.newhouse@gmail.com

Response time is best effort. This is a one-person project maintained in my own time.

## Verification

- All commits are by Stephen J Newhouse (stephen.j.newhouse@gmail.com)
- The repo uses conventional commits and semantic versioning
- Run `scripts/install.sh --dry-run` to see exactly what would happen before committing to an install
