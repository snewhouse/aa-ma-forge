# Security

This document explains exactly what AA-MA Forge does to your system when you install it, what the hook does at runtime, and how to report vulnerabilities. Read it before running anything.

## What install.sh does

The installer (`scripts/install.sh`) places files into `~/.claude/` so Claude Code can find them. It makes no network calls, downloads nothing, requires no sudo, does not modify your PATH, and does not set or change environment variables.

**Symlinks created** (pointing from `~/.claude/` back into this repo):

- 6 command files: `~/.claude/commands/*.md` (aa-ma-plan, execute-aa-ma-milestone, execute-aa-ma-full, execute-aa-ma-step, verify-plan, archive-aa-ma)
- 1 skills directory: `~/.claude/skills/aa-ma-execution/`
- 2 agent files: `~/.claude/agents/aa-ma-scribe.md`, `~/.claude/agents/aa-ma-validator.md`
- 1 rules file: `~/.claude/rules/aa-ma.md`
- 1 hook: `~/.claude/hooks/lib/pre-compact-aa-ma.sh`

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
