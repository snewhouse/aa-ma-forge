# 0020. Commands become skills: the forge ships no slash commands

**Status:** Proposed
**Date:** 2026-10-09
**Deciders:** Stephen Newhouse (sole maintainer)
**Tags:** `skills`, `commands`, `install`, `conventions`

## Context and Problem Statement

The forge shipped 14 slash commands (`claude-code/commands/*.md`) beside 27 skills. Claude Code
now resolves `/name` to a skill as well as to a command, so the two surfaces overlap. The overlap
cost three things (code-conventions-impact map, Ticket 15):

- **Two copies of one entry point.** `assess-codebase` and `understand-codebase` each had a thin
  command wrapper beside the skill. The wrapper's routing text and the skill's drifted apart, and
  tests pinned both.
- **Two conventions for one kind of file.** Commands had no `name:` rule (2 of 14 had none), a
  frontmatter test of their own, and their own install loop and count sites in five documents.
- **The executor cannot be invoked as a skill.** `/execute-aa-ma-full` delegates to
  `/execute-aa-ma-milestone`. When that is a command, the model cannot reach it through `Skill()`.

**Should the forge keep shipping commands, and if not, how do existing installs move?**

## Decision Drivers

- **One surface, one convention.** Prompt-as-code checks (frontmatter schema, 500-line cap, evals)
  are written once, for skills.
- **Existing installs must not be left broken.** `~/.claude/commands/<x>.md` links into the repo
  dangle the moment the source moves.
- **Nothing that belongs to someone else is lost.** A symlink the installer replaces may point at
  another tool's install.
- **Outward actions stay explicit.** Merging to main and publishing a link must not start because
  the model decided a request matched.

## Considered Options

1. **Keep commands; delete the two wrappers only.** Fixes the drift but keeps two conventions and
   leaves the executor unreachable through `Skill()`.
2. **Commands become skills (chosen).** 11 commands move by `git mv` to
   `claude-code/skills/<name>/SKILL.md`; the 2 wrappers merge into their skills; `grill-me` retires
   (D4: the user-level mattpocock skill covers it).
3. **Commands become skills, all with `disable-model-invocation`.** Behaves most like the old
   commands, but the executor still cannot delegate to the milestone skill (D9, superseded).

## Decision Outcome

Chosen option: **2**, prototyped on `prototype/cmd-to-skill` (M3.1). The prototype installed,
uninstalled and reinstalled one converted command into a fake `HOME`, and an isolated
`claude -p` probe showed `/aa-ma-search` resolving and running as a skill.

- **Move.** `git mv` keeps history. Each moved skill has `name:` equal to its directory and a
  description that names the explicit request.
- **Invocation (D9 revised).** Only `sole-dev-merge` and `aa-ma-share` carry
  `disable-model-invocation: true`. Every other moved skill stays model-invocable.
  `tests/skills/test_model_invocation_list.py` pins the set.
- **Merge.** `argument-hint`, `$ARGUMENTS` parsing and the use/don't-use routing move from the two
  wrappers into the SKILL.md bodies, not into `references/`.
- **No collisions.** `tests/skills/test_no_command_skill_collision.py` asserts that no stem is
  both a command and a skill, and that `claude-code/commands/` is absent or empty.
- **Install hygiene.**
  - `install.sh` removes `~/.claude/commands/*.md` links that resolve under
    `<repo>/claude-code/` and whose source is gone.
  - Before replacing a symlink that points outside the repo, it records `<link>\t<destination>`
    in `backups/aa-ma-forge-<ts>/foreign-symlinks.tsv`. It does this under `--force` too.
  - `uninstall.sh --restore` puts recorded links back.
  - `uninstall.sh` takes its deregistration list from `install.sh`'s `AA_MA_HOOKS` table, with
    or without `--restore`.
- **Plugin surface.** `/x-*` globs expand over skills as well as commands.
- **`/grill-me`** is declared external in `surface_allowlist.py`.

### Upgrade note

Existing installs must **re-run `scripts/install.sh`** from the updated checkout. Until then:

- the old `~/.claude/commands/<x>.md` links dangle;
- the new skill links do not exist.

The re-run removes the dangling links, links the 11 new skill directories, and leaves anything
foreign recorded and restorable.

## Consequences

**Positive**

- One convention for every `/name`. Commands no longer need their own count sites, install loop
  or frontmatter rule.
- `/execute-aa-ma-full` can delegate through `Skill(execute-aa-ma-milestone)`.
- `uninstall.sh` no longer lags the hook table. Before this change it missed
  `security-static-check` and `aa-ma-plan-skip-warn`.

**Negative**

- Eleven skills that used to run only when typed may now be started by the model.
  - Mitigation: each description names the explicit request.
  - Re-evaluate `aa-ma-plan` after two weeks of use (plan risk 3).
- A symlink into a different forge checkout counts as foreign and is recorded, for example a link
  into `main` while installing from a worktree. This is harmless, but it is noise in the manifest.

**Neutral**

- `plugin_surface.py` keeps `commands` in `_DIRS`, so a plugin that still ships commands is still
  read.
- `tests/commands/` keeps its name. It holds tests of the former commands, which are now skills.

## References

- code-conventions-impact plan, Milestone 3; map Ticket 15; decisions D4, D7 and D9 (revised).
- Prototype: branch `prototype/cmd-to-skill`; provenance `PROTOTYPE — Milestone 3 …`.
- `scripts/install.sh`, `scripts/uninstall.sh`, `tests/hooks/install_dry_run.bats`.
- ADR-0008 (`/sole-dev-merge`), ADR-0010 (`/aa-ma-share`), ADR-0019 (previous skill migration).
