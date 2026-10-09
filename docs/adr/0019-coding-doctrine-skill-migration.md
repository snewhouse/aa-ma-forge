# 0019. Coding-doctrine skill migration: five global skills and the ruff hook move into the forge

**Status:** Accepted
**Date:** 2026-10-09
**Deciders:** Stephen Newhouse (sole maintainer)
**Tags:** `skills`, `forks`, `install`, `conventions`

## Context and Problem Statement

The coding doctrine is stated in five skills that live only in `~/.claude/skills/`
(`logging-and-comments`, `python-quality-gates`, `llm-output-safety`, `secrets-management`,
`bash-defensive-patterns`) and is enforced at edit time by `~/.claude/hooks/lib/ruff-format.sh`.
None of them is versioned, tested or shipped, and forge content already invokes some of them,
so to the plugin-surface extractor they are declared-external or dangling
(engineering-standards §1).

**Where should the coding doctrine live, and how is each piece's origin recorded?**

## Decision Drivers

- **Forge is canonical** (code-conventions-impact map, Ticket 12): doctrine ships from this repo.
- **Origin must be evidenced, not remembered.** A fork records upstream repo, SHA, licence and
  md5 so `scripts/fork-drift.sh` can report drift.
- **Licence compliance.** A fork of MIT code carries the upstream `LICENSE`.
- **Reversible.** Outside-repo state is backed up and count-verified before any change (L-1300).

## Considered Options

1. Move all five skills and the hook into the forge: Adoption for Ste-authored skills, Fork for
   upstream ones.
2. Declare them external and leave them in `~/.claude/skills/`.
3. Rewrite them as one consolidated doctrine skill.

## Decision Outcome

**Option 1.** Each piece's origin, as verified on 2026-10-09:

| Skill / file | Kind | Upstream (repo @ SHA, path) | Local md5 (`~/.claude`) | Upstream md5 | `diff -wB` local vs upstream | Licence | Fork state |
|---|---|---|---|---|---|---|---|
| `logging-and-comments` (SKILL.md, references/{bash,python}.md, references/ruff-baseline.toml) | Adoption | none: Ste-authored (no copy in 19 plugin marketplaces or `_archive/`) | SKILL.md `0f7bde15…` · bash.md `679d4194…` · python.md `e587f717…` · ruff-baseline.toml `cc860803…` | — | — | repo licence | — |
| `python-quality-gates` (SKILL.md) | Adoption | none: Ste-authored | `ed0ff4e4…` | — | — | repo licence | — |
| `llm-output-safety` (SKILL.md) | Adoption | none: Ste-authored (from lessons L-050–L-052) | `891ef7e5…` | — | — | repo licence | — |
| `secrets-management` (SKILL.md) | Fork | `wshobson/agents` @ `46891e7e60da0e52baf1050b7b6391b64e84c6d9`, `plugins/cicd-automation/skills/secrets-management/` | `f72110c6…` (= snapshot `5d65aa1` up to 3 blank lines) | `5273fb73…` | upstream since changed: examples no longer echo secrets, images pinned (`vault:1.17`) | MIT (`gh api …/license`: MIT; LICENSE md5 `0e1b4dd9…`) | **derived** @ `46891e7`: copied byte-exact from upstream (Ste, 2026-10-09), then patched after the §6.8 security review — the GitLab example no longer echoes `$API_KEY`/`$DATABASE_URL`, and both trufflehog calls pass `--fail` (without it findings exit 0, so the gates could never fail) |
| `bash-defensive-patterns` (SKILL.md, references/advanced-patterns.md) | Fork | `wshobson/agents` @ `5d65aa10638bcc1b390738e11f9bff213f61955a`, `plugins/shell-scripting/skills/bash-defensive-patterns/` | SKILL.md `b1930f17…` · advanced-patterns.md `376f1ab0…` | SKILL.md `8280da5a…`; advanced-patterns.md has no upstream | local edits: ERR trap to stderr, `work_dir` instead of `TMPDIR` in traps; advanced-patterns.md split out locally | MIT (same LICENSE) | **derived** @ `5d65aa1` (Ste, 2026-10-09). Upstream HEAD `46891e7` restructured to SKILL.md + references/details.md; rebasing onto it is out of scope. |
| `hooks/lib/ruff-format.sh` → `claude-code/hooks/ruff-format.sh` | Adoption, adapted | none: Ste-authored | `618d855b…` | — | — | repo licence | — (adds `AA_MA_HOOKS_DISABLE`, `CLAUDE_HOOK_LOG`, `--` before the path) |

Upstream SHAs come from `gh api repos/wshobson/agents/commits/HEAD` (`46891e7`) and from the
local marketplace clone `git -C ~/.claude/plugins/marketplaces/claude-code-workflows rev-parse HEAD`
(`5d65aa1`). Upstream md5s come from `gh api …/contents/<path>?ref=<sha>` raw fetches, never
the plugin cache.

`deslop-shared-libs` and `ponytail` stay **declared-external**: they are third-party plugins
with their own release cycle. `senior-secops` is handled in M8 of the code-conventions-impact
plan (the secops plan).

## Consequences

- **Good:** doctrine is versioned, tested (`tests/skills`, `tests/hooks/ruff-format.bats`) and
  shipped by `install.sh`; `skill:secrets-management` resolves on disk.
- **Good:** both forks are tracked in `claude-code/skills/FORKS.json` and checked by `fork-drift.sh`,
  which now reads the upstream repo per row instead of assuming `mattpocock/skills`.
- **Bad:** after M2, `scripts/uninstall.sh` removes the five migrated skills and the ruff hook
  registration. `--restore` now walks every `aa-ma-forge-*` backup newest-first and restores each
  path from its newest copy, so the install-time backups of the five real skill dirs come back;
  before, it read only the newest dir, which a later re-run (backing up just the copied spec docs)
  could hide. `settings.json` backups are sibling files (`backups/settings-aa-ma-forge-<ts>.json`).
  The `~/.claude/backups/cci-m2-<ts>.tgz` tarball stays the fallback
  (M2: `cci-m2-20261009T073602Z.tgz`, 11 files, count-verified).
- **Neutral:** `ruff-format.sh` is adapted, not verbatim: it honours `AA_MA_HOOKS_DISABLE` and
  `CLAUDE_HOOK_LOG` (the logging-and-comments contract) like every AA-MA hook.
- **Neutral:** every fork dir ships its upstream MIT `LICENSE`, including the five pre-existing
  mattpocock forks; the new every-fork test found that gap.
- **Neutral:** `python-quality-gates` named five user-local commands (`commit-and-push`,
  `pre-commit-full`, `release-prep`, `doc-sync`, `doc-fix`) as `/x`. Shipped content may not
  invoke local-only commands (`surface_allowlist.py`), so the text now names them as user-local
  commands this plugin does not ship. `llm-output-safety` and `bash-defensive-patterns` are
  orphans (nothing in the forge invokes them) until the planned `coding-standards.md` rule.
- **Neutral:** a fork's local-only file (`bash-defensive-patterns/references/advanced-patterns.md`)
  is kept out of `FORKS.json` `files`, since fork-drift would report it ORPHAN; it carries a
  line-1 `Derived from` comment instead.
- **Bad:** the live `secrets-management` changes content when `install.sh` relinks it (the
  upstream fixes above).

## References

- Plan: `.claude/dev/active/code-conventions-impact/` (Milestone 2)
- Map: Ticket 9 (logging-and-comments adoption), Ticket 12 (doctrine packaging)
- Fork pattern: ADR-0003 (`prototype`), commit `4049b43`
