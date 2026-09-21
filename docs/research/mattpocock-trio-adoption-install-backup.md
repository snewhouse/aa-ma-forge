# Does `scripts/install.sh` back up a real directory before symlinking, and where?

**Created:** 2026-09-21
**Author:** aa-ma-researcher (Claude), for mattpocock-trio-adoption (M4 install step)
**Reviewed-Through-Date:** 2026-09-21 (scripts/install.sh at HEAD `ca0de90`; last touched in commit `55f0be0`, 2026-05-11)
**Valid-Through:** 2026-Q4 (any edit to the "Backup existing AA-MA files" block or `create_symlink` in scripts/install.sh invalidates this)
**Sources:**
- scripts/install.sh:112-190 — backup collection + copy logic (primary)
- scripts/install.sh:195-225 — `create_symlink` removes real files/dirs after backup
- scripts/install.sh:346-358 — separate one-shot `settings.json` backup
- scripts/uninstall.sh:151-206 — `--restore` reads the same backup tree (secondary, confirmed against install.sh)
- docs/runbooks/rollback-v0.5.0.md:84-86 — documents the backup path (secondary, matches install.sh:158)

## Answer
Yes. Before any symlink is created, `install.sh` copies every real (non-symlink) file or directory it is about to replace into a timestamped tree at `~/.claude/backups/aa-ma-forge-YYYYMMDD-HHMMSS/`, preserving the path relative to `~/.claude/` (e.g. a real `~/.claude/skills/aa-ma-research/` lands at `~/.claude/backups/aa-ma-forge-<ts>/skills/aa-ma-research/`). The backup is skipped entirely under `--force`, and it only covers the targets install.sh explicitly enumerates — real files at other hook paths under `~/.claude/hooks/lib/` are `rm -rf`'d without backup.

## Evidence

**What gets backed up (real files/dirs only).**
- `collect_backup_target` adds a path only if it exists and is *not* a symlink: `[ -e "${target}" ] && [ ! -L "${target}" ]` — scripts/install.sh:119-124. Existing symlinks are never backed up (they are simply replaced, see below).
- Enumerated targets: every `~/.claude/commands/<name>.md` matching a repo command (scripts/install.sh:127-130); every `~/.claude/skills/<dir>` matching a repo skill directory (scripts/install.sh:133-136) — this is the "real directory" case; every `~/.claude/agents/<name>.md` (scripts/install.sh:139-142); `~/.claude/rules/aa-ma.md` and `~/.claude/rules/engineering-standards.md` (scripts/install.sh:145-146); only one hook, `~/.claude/hooks/lib/pre-compact-aa-ma.sh` (scripts/install.sh:149); every `~/.claude/docs/<spec>.md` (scripts/install.sh:152-155).

**Where it goes.**
- `BACKUP_DIR="${CLAUDE_HOME}/backups/aa-ma-forge-$(date +%Y%m%d-%H%M%S)"` with `CLAUDE_HOME="${HOME}/.claude"` — scripts/install.sh:158, scripts/install.sh:43.
- Relative path preserved: `rel_path="${target#"${CLAUDE_HOME}"/}"; backup_dest="${BACKUP_DIR}/${rel_path}"` — scripts/install.sh:170-171. Parent created with `mkdir -p "$(dirname "${backup_dest}")"` (scripts/install.sh:176), then `cp -a "${target}" "${backup_dest}"` (scripts/install.sh:178 for dirs, :180 for files — the two branches are identical; `cp -a` on a directory to a non-existent dest recreates the directory with its contents and permissions).
- The backup directory is created with `mkdir -p` only when there is at least one target and `--force` is not set (scripts/install.sh:157, :164). If nothing needs backing up, the message "No existing files to back up." is printed and no directory is created (scripts/install.sh:188-189).

**Ordering: backup happens before any symlink.**
- The backup block (scripts/install.sh:112-190) runs before `create_symlink` is even defined (scripts/install.sh:195) and before the first link step "1. Symlink commands" (scripts/install.sh:256).
- `create_symlink` then removes the real file/dir with `rm -rf "${target}"`, relying on the comment "already backed up above" (scripts/install.sh:209-216), and creates the link with `ln -s` (scripts/install.sh:221).

**When backup does NOT happen.**
- `--force`: backup skipped with `warn "Skipping backup (--force flag set)"`; the subsequent `rm -rf` still runs — scripts/install.sh:12, :186-187, :214.
- `--dry-run`: only prints "Would backup: ..." and creates nothing — scripts/install.sh:161-162, :173-174. (`FILES_BACKED_UP` is incremented even in dry-run, scripts/install.sh:184, so the summary count is a would-be count.)
- Coverage gap: `create_symlink` is also called for `~/.claude/hooks/lib/aa-ma-parse.sh` (scripts/install.sh:333-336), `~/.claude/hooks/lib/aa-ma-plan-marker.sh` (scripts/install.sh:341-344), and every hook in `AA_MA_HOOKS` via `register_hook` (scripts/install.sh:314-323, :373). Of these, only `pre-compact-aa-ma.sh` is in the backup list (scripts/install.sh:149). A real (non-symlink) file at any of the other seven `hooks/lib/` paths would be `rm -rf`'d at scripts/install.sh:214 without a backup copy. Not observed in practice (these paths are normally symlinks created by a prior install), but it is a real hole in the "backed up above" assumption.
- Spec docs are copied, not symlinked (`copy_file`, scripts/install.sh:230-251); they *are* backed up first (scripts/install.sh:152-155) and then overwritten by `cp` (scripts/install.sh:247).

**Separate mechanism for settings.json.**
- `~/.claude/settings.json` is not part of the timestamped tree. It is copied once to `~/.claude/settings.json.bak` (sibling, no timestamp, overwritten on each install that mutates settings) immediately before the first hook registration, and only when `--force` is not set — scripts/install.sh:346-358, invoked at :396.

**Restore path (secondary, confirmed).**
- `scripts/uninstall.sh --restore` finds the lexically-latest `~/.claude/backups/aa-ma-forge-*` directory and `cp -a`s each file back to `~/.claude/<rel_path>` — scripts/uninstall.sh:156-206. It walks with `find -type f` (scripts/uninstall.sh:206), so directory backups are restored file-by-file; the `[ -d ]` branch at :198-199 is effectively dead. It does not restore `settings.json.bak`.
- docs/runbooks/rollback-v0.5.0.md:84-86 states the same path and restore command; matches scripts/install.sh:158.

## Not pursued
- Whether `uninstall.sh --restore` correctly restores when the target is currently a symlink (it may write through the link into the repo) — scripts/uninstall.sh:178-204 not traced in full; out of scope for the install question.
- Whether the hook tests under `tests/hooks/` (bats) exercise the backup path — not checked.
- Fixing the `hooks/lib/` backup coverage gap or the dead identical `if [ -d ]` branch at scripts/install.sh:177-181 — findings only, no edits per brief.
- Behaviour when `~/.claude/backups/` is not writable — script uses `set -euo pipefail` (scripts/install.sh:14) so `mkdir -p` failure aborts before any `rm -rf`, but not tested.
