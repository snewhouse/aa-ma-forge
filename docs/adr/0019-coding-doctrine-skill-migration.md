# 0019. Coding-doctrine skill migration: five global skills and the ruff hook move into the forge

**Status:** Proposed
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
| `secrets-management` (SKILL.md) | Fork | `wshobson/agents` @ `46891e7e60da0e52baf1050b7b6391b64e84c6d9`, `plugins/cicd-automation/skills/secrets-management/` | `f72110c6…` (= snapshot `5d65aa1` up to 3 blank lines) | `5273fb73…` | upstream since changed: examples no longer echo secrets, images pinned (`vault:1.17`) | MIT (`gh api …/license`: MIT; LICENSE md5 `0e1b4dd9…`) | **current**: copied byte-exact from upstream @ `46891e7` (Ste, 2026-10-09) |
| `bash-defensive-patterns` (SKILL.md, references/advanced-patterns.md) | Fork | `wshobson/agents` @ `5d65aa10638bcc1b390738e11f9bff213f61955a`, `plugins/shell-scripting/skills/bash-defensive-patterns/` | SKILL.md `b1930f17…` · advanced-patterns.md `376f1ab0…` | SKILL.md `8280da5a…`; advanced-patterns.md has no upstream | local edits: ERR trap to stderr, `work_dir` instead of `TMPDIR` in traps; advanced-patterns.md split out locally | MIT (same LICENSE) | **derived** @ `5d65aa1` (Ste, 2026-10-09). Upstream HEAD `46891e7` restructured to SKILL.md + references/details.md; rebasing onto it is out of scope. |
| `hooks/lib/ruff-format.sh` → `claude-code/hooks/ruff-format.sh` | Adoption | none: Ste-authored | `618d855b…` | — | — | repo licence | — |

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
  registration, and `--restore` cannot recreate them (they were never forge backups). Restore
  them from the `~/.claude/backups/cci-m2-<ts>.tgz` tarball.
- **Bad:** the live `secrets-management` changes content when `install.sh` relinks it (the
  upstream fixes above).

## References

- Plan: `.claude/dev/active/code-conventions-impact/` (Milestone 2)
- Map: Ticket 9 (logging-and-comments adoption), Ticket 12 (doctrine packaging)
- Fork pattern: ADR-0003 (`prototype`), commit `4049b43`
