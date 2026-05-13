# Lessons Learned (aa-ma-forge)

Project-local pattern + prevention rules. Reviewed at session start.
Newest at top. See also: `~/.claude/rules/self-improvement-loop.md`.

---

## L-008 (2026-05-13) — `cz bump --files-only` exits 16 when CHANGELOG.md has been manually promoted; chain "manual promote + cz files-only" is broken

**Pattern:** During v0.9.0 release prep (fix-drift-release-v0-9-0 M3.4),
chose the manual-CHANGELOG-promote path to preserve the rich
hand-written `## [Unreleased]` entry (per L-006's alternative-to-amend
guidance). Step 1: manually edited `## [Unreleased]` → `## v0.9.0 (2026-05-13)`
in CHANGELOG.md, keeping all the multi-paragraph Feat + Docs prose intact.
Step 2: ran `uv run cz bump --files-only --yes` expecting it to bump only
`pyproject.toml` (`version =`) + `VERSION` (`__version__ =`).

**Symptom:** cz correctly computed the bump (`bump: version 0.8.0 → 0.9.0;
tag to create: v0.9.0; increment detected: MINOR`) — but then exited
with code 16 and the message "No tag found to do an incremental
changelog". Version files were not modified. Despite the `--files-only`
flag, cz appears to still execute CHANGELOG operations when
`update_changelog_on_bump = true` is set in `[tool.commitizen]`, and
it dies on the already-promoted CHANGELOG state (the section it tries
to insert above already exists).

**Root cause (suspected):** `cz_conventional_commits` interaction between
`--files-only` semantics and `update_changelog_on_bump = true`. The flag
should disable CHANGELOG ops; the config setting overrides it. Either
order of operations works in isolation (cz bump with auto-regen, OR
manual-everything), but the chain `manual promote → cz --files-only`
doesn't.

**Workaround used:** Abandoned cz for this bump. Did the 2-line manual
edit directly:
- `pyproject.toml`: `version = "0.8.0"` → `"0.9.0"` (one Edit).
- `VERSION`: `__version__ = "0.8.0"` → `"0.9.0"` (one Edit).
Then `git commit -m "bump: version 0.8.0 → 0.9.0"` (cz-style subject)
+ `git tag -a v0.9.0 -m "..."` + push tag. End-state byte-identical
to what a successful `cz bump --files-only` would have produced.

**Rule:** For aa-ma-forge releases where you want to preserve a rich
hand-written `[Unreleased]` entry, pick ONE path — do NOT combine them:

(a) **Per L-003**: run `cz bump --increment minor --yes` (or
    `--increment patch`/`major`) end-to-end → cz regenerates CHANGELOG
    terse → amend the CHANGELOG entry per L-006 → re-tag with
    `git tag -f vX.Y.Z`. cz owns everything; you fix up at the end.

(b) **Skip cz entirely**: manually promote `## [Unreleased]` →
    `## vX.Y.Z (date)` + 2-line manual edit of `pyproject.toml` +
    `VERSION` + `git commit -m "bump: version X → Y"` (cz-style
    subject) + `git tag -a vX.Y.Z -m "..."`. Standard 8-tag cadence
    preserved; no cz invocation in this bump.

The chained "manually promote CHANGELOG + then `cz bump --files-only`"
path is broken and will exit 16.

**Cross-ref:** L-003 (cz bump owns CHANGELOG headings — never manually
edit), L-006 (cz strips rich `[Unreleased]` content; amend after bump),
`[tool.commitizen]` config in `pyproject.toml`, observed in commit
`ed077f7` of feature/understand-codebase-skill (the v0.9.0 release).
Global L-324 (the HARD-gate approval bootstrap problem encountered in
the same session — different bug class, same release).

## L-007 (2026-05-11) — `/sole-dev-merge` quality-check format pass may modify out-of-scope files

**Pattern:** During harden-aa-ma-plan M5 merge step, `/sole-dev-merge` Step 2
ran `uv run ruff format src/ tests/` which reformatted 29 pre-existing test
files in `tests/codemem/` and `tests/perf/` — none of which were touched by
the plan's work. The format step is a "with-fix" pass, meaning it mutates
working-tree files as part of the merge ceremony.

**Symptom:** After the format step, `git status --porcelain` listed 29
modified files outside the plan's known scope. The default sole-dev-merge
flow would have bundled them into the release merge, coupling the v0.7.0
release commit to wholesale format drift unrelated to its declared scope.

**Root cause:** `/sole-dev-merge` was designed as a quality gate, not a
scope filter. It assumes the working tree is clean before invocation, but
its own format-fix step can dirty the tree with whole-tree changes that
weren't part of the feature branch's commits.

**Rule:** During `/sole-dev-merge`, after the format-with-fix step, check
`git status --porcelain` for modifications outside the plan's known scope.
Reset out-of-scope changes with `git checkout -- <paths>` before proceeding
to the merge. Whole-tree format passes should be their own dedicated
`chore(format)` commit on a separate prep PR — NOT slipped in via a release
merge ceremony. Failing to do this couples release scope to unrelated drift
and violates the atomic-commit-per-logical-change convention.

**Cross-ref:** sole-dev-merge skill (gstack) — the format-fix step is
deliberate but assumes clean-tree start; this lesson captures the gap when
the assumption breaks.

---

## L-006 (2026-05-11) — `cz bump` strips rich `## Unreleased` content to bare Feat/Fix — amend + retag to preserve prose

**Pattern:** During harden-aa-ma-plan M5.4, a `## Unreleased` section was
hand-authored with prose intro + Feat/Test/Docs/Chore subsections matching
the v0.6.0 / v0.5.0 entry styles. `uv run cz bump` replaced that section
with auto-generated bare Feat + Fix bullets only, losing the prose intro
and the entire Test + Docs + Plan-close subsections.

**Symptom:** v0.7.0 bump commit (00d6519, then amended to 480dd3f) landed
with a CHANGELOG entry far weaker than v0.6.0 and v0.5.0 — no prose intro,
no Test posture summary, no Docs additions list, no Plan close summary.
Discovered by reading the post-bump CHANGELOG before pushing.

**Root cause:** `cz_conventional_commits` default template emits only Feat
and Fix bullets extracted from commit subjects. Prior rich CHANGELOG
entries (v0.6.0, v0.5.0) were enriched manually post-bump — not generated
by cz. The hand-authored `## Unreleased` content does not survive cz's
section rewrite.

**Rule:** After `uv run cz bump`, immediately review the generated
CHANGELOG section. If it's missing prose intro + Test/Docs/Plan-close
sections needed to match prior entries, edit them in, then
`git commit --amend --no-edit && git tag -d vX.Y.Z && git tag vX.Y.Z` to
retag at the amended commit BEFORE pushing. This preserves L-003 (cz owns
the heading) while delivering substantive release notes. Do NOT push the
tag until the CHANGELOG is acceptable — local-only retagging is reversible;
pushed-tag retagging requires force-tag-push and breaks anyone who has
already fetched.

**Cross-ref:** L-003 (cz bump owns CHANGELOG headings — never manually
edit `## vX.Y.Z`). This is its operational corollary: cz owns the
heading, you own the contents under it.

---

## L-005 (2026-05-11) — `install.sh` symlinks only registered hook scripts — helpers invoked from slash-command bodies need explicit symlinks

**Pattern:** During harden-aa-ma-plan M4 first install attempt, the
`claude-code/hooks/aa-ma-plan-marker.sh` helper script was missing from
`~/.claude/hooks/lib/` after running `scripts/install.sh`. The helper is
invoked from the `/aa-ma-plan` command body as
`bash ~/.claude/hooks/lib/aa-ma-plan-marker.sh <slug> <phase> <status> ...`
but `register_hook` in `scripts/install.sh` only symlinks scripts that
appear in the `AA_MA_HOOKS` event-registration array. Helper scripts
(non-event, invoked-by-path) were silently skipped.

**Symptom:** After install completed without error, any `/aa-ma-plan`
invocation would hit
`bash: /home/.../aa-ma-plan-marker.sh: No such file or directory` for every
phase marker write. The event-registered hook script (aa-ma-plan-skip-warn.sh)
was correctly symlinked, but the helper it expects to coexist wasn't.

**Root cause:** `scripts/install.sh` has two distinct mechanisms for
deploying files under `~/.claude/hooks/lib/`:
(a) `register_hook` — auto-symlinks via the `AA_MA_HOOKS` array for
event-registered hooks;
(b) explicit `create_symlink` blocks — for helper libraries (precedent:
`aa-ma-parse.sh` at install.sh:332-335).
The harden-aa-ma-plan M2.4 task registered the event hook (path a) but
forgot the explicit symlink block (path b) for the helper.

**Rule:** When adding a helper script under `claude-code/hooks/` that is
invoked by absolute path from any slash-command body or other hook, add an
explicit `create_symlink` block in `scripts/install.sh` mirroring the
existing `aa-ma-parse.sh` pattern (install.sh:329-335). Helpers must be
reachable at `~/.claude/hooks/lib/<helper>.sh` regardless of which project
the user invokes the command from. Validate with
`scripts/install.sh --dry-run | grep <helper>` BEFORE running real install.

**Cross-ref:** sole-dev-merge dry-run gate (catches this if a new helper's
test asserts the symlink exists); future helpers should add a
`tests/hooks/install_dry_run.bats` assertion confirming their symlink is
announced.

---

## L-004 (2026-05-10) — Mid-flight Edit failures leave AA-MA artefacts in split-brain state

**Pattern:** During the M3.6 plan-close commit of skill-ecosystem-integration
v1.2, a sequence of three Edit calls was issued in parallel: (1) GATE
APPROVAL artifact append to `context-log.md`, (2) `## Milestone M3:
... Status: ACTIVE → COMPLETE`, (3) `### Task 3.6: ... Status: PENDING →
COMPLETE`. Edit (2) errored mid-flight with `claude-opus-4-7[1m] is
temporarily unavailable`. Edits (1) and (3) succeeded. The plan-close
commit (`2362903`) was created and pushed with the M3 milestone-line still
showing `Status: ACTIVE` while every sub-task underneath showed
`Status: COMPLETE` and the GATE APPROVAL artifact was present in
context-log.md — split-brain state.

**Symptom:** the next `/execute-aa-ma-milestone` invocation re-fired the
M3 close protocol because its milestone-line scan found `Status: ACTIVE`
(taking it as the next active milestone). User saw an unexpected re-run
of the close workflow instead of "all milestones complete — nothing to do."

**Root cause:** model-availability errors are not transactional across a
batch of independent Edit calls. The harness's parallel-tool execution
fans them out; partial failure silently leaves the artefact in an
inconsistent state. There is no rollback: succeeded edits are committed
to the working tree before the batch outcome is known.

**Rule:** when a milestone-close commit must update both a
milestone-level status field AND its closing sub-task's status field,
batch the two writes into a SINGLE Edit call (or use MultiEdit) so partial
failure leaves the artefact in a known state — either both edits land or
neither does. The same applies to any closing-protocol writes that must
either all succeed or all be retried together (e.g., milestone Status +
Task close + provenance append for the same milestone).

**How to apply:**
- In `/execute-aa-ma-milestone` Section 7.4 (Transparent Status Change),
  group the milestone-line and closing-task-line edits into one
  MultiEdit — DO NOT issue them as separate parallel Edit calls.
- Pre-flight: before the milestone-close commit, scan the artefact one
  last time and verify status fields are consistent. If they're not,
  HALT and remediate before commit.
- Post-flight: after every milestone-close commit, run
  `grep -B1 "^- Status:" tasks.md | grep -A1 "^## Milestone"` to
  detect drift between milestone-line status and sub-task status.

**Why this matters:** silent drift in plan artefacts undermines every
downstream consumer — `/execute-aa-ma-milestone` re-fires unnecessarily,
`/archive-aa-ma` may refuse to archive, the `aa-ma-validator` agent
flags as inconsistent. The cost of one extra MultiEdit on the close
commit is trivial; the cost of split-brain detection + corrective
commit later is at least one extra commit (the actual fix in this case
was `8d93879`).

**Cross-ref:** L-080–L-082 sub-step sync rule (which this complements —
L-080 ensures sub-step Result Logs are atomic; L-004 ensures
milestone-status edits are atomic).

---

## L-001 (2026-05-10) — External URL First Principle

**Pattern:** During `/aa-ma-plan` for skill-ecosystem-integration, a Phase 3
research agent was dispatched to audit "mattpocock/skills" without being
given the URL. The agent looked at locally-installed `anthropic-agent-skills`
plugin contents and concluded "this is Anthropic's catalog, not mattpocock".
The conclusion was wrong — `mattpocock/skills` is a real GitHub repo with
68k stars and 17 production skills, including the canonical `grill-with-docs`
and `grill-me`. The misattribution propagated into the AA-MA plan's
executive summary, M2 description, and Assumption A5. The user caught it
("did you read https://github.com/mattpocock/skills/tree/main in detail?")
and demanded re-work ("do not be lazy like this again").

**Rule:** When a user explicitly names a specific external source — a GitHub
URL, an RFC number, a vendor doc URL, a paper DOI — the planning process
MUST fetch that source directly BEFORE any agent delegation. For GitHub:
use `gh api repos/<owner>/<repo>/contents` to enumerate and
`gh api .../SKILL.md --jq .content | base64 -d` for individual files. For
other URLs: WebFetch with a tight prompt.

Only dispatch research agents AFTER the canonical inventory is captured.
The agent's job is then synthesis/comparison against ground truth, not
discovery. The agent prompt must include the verified inventory as
ground-truth context to prevent hallucination on the source's identity.

**Why this matters:** Conflation between locally-installed skills and the
upstream they were sourced from is the silent default failure mode. Two
plugins with the same skill name can come from different repos; one repo
can be a subset/superset of another; aliases and curators (mattpocock,
anthropic-agent-skills) can muddy attribution. The only authoritative
answer is the URL the user named.

**How to apply:**
- Trigger keyword: any URL in the user message; any phrase like "the X repo"
  or "the X catalog" where X is a named external entity.
- First call after Phase 1.2 context-gathering: fetch the named URL.
- Embed the verified inventory in any subsequent agent prompt as
  ground-truth context.
- Save the inventory in the AA-MA `reference.md` so re-dispatches don't
  re-discover.

---

## L-002 (2026-05-10) — AA-MA `doc-count-drift` Critical-Path fires per milestone, not per plan

**Pattern:** Multi-milestone plans that add skills incrementally (e.g., M1: +1
skill, M2: +2 skills) must run the doc-count-drift grep sweep per milestone,
not once at plan close. v1.2 of the skill-ecosystem-integration plan had M1
change skill count 13 → 14 and M2 change 14 → 16. Each transition needs its
own `grep -rn "<old-count> skills" claude-code/ docs/ CLAUDE.md SECURITY.md
README.md` until clean. Combining into a single sweep at plan close would
leave M1's commits with stale "13 skills" prose for the duration of M2 work
— and any session opened against a half-shipped plan would see prose that
contradicts the actual skill directory count.

**Rule:** When a plan modifies hardcoded counts across multiple milestones,
declare `Critical-Path: doc-count-drift` ON EACH MILESTONE that changes the
count. Each milestone HARD gate runs its own `grep -rn` sweep targeting the
old count value being replaced. The plan must list per-milestone count
transitions explicitly (e.g., "M1.6: 13 → 14"; "M2.7: 14 → 16"). The Tier 6
detector in `rules/doc-drift-checks.md` is the canonical sweep mechanism;
invoke it per milestone close, not per plan close.

**Cross-ref:** Global L-304 (importer-count drift direction-check); the
canonical Critical-Path enum in `claude-code/rules/engineering-standards.md`.

---

## L-003 (2026-05-10) — aa-ma-forge CHANGELOG.md is managed by `cz bump`; never manually edit `## vX.Y.Z` headings

**Pattern:** `pyproject.toml` `[tool.commitizen]` has
`update_changelog_on_bump = true`. `cz bump` automatically inserts the
version heading and aggregates conventional commit messages from the bump
range. Plan v1.2 of skill-ecosystem-integration specified manually adding
`## v0.6.0 (2026-05-10)` to CHANGELOG.md during M3.5. C2 review caught this
during /double-check ultrathink: pre-inserting the heading would either
duplicate commitizen's auto-insertion, fail the bump, or cause commitizen to
skip auto-population of that section.

**Rule:** For aa-ma-forge releases, ALWAYS use `cz bump --increment
{major|minor|patch}`. Conventional commit bodies are the source of CHANGELOG
content; never write `## v...` version headings directly to CHANGELOG.md.
Manual release-narrative prose CAN appear above the next-released version
section (e.g., a top-of-section paragraph summarising the release theme),
but never inside or as a heading for an unreleased version. Verified
during /double-check ultrathink session 2026-05-10 by reading
`pyproject.toml` `[tool.commitizen]` and `[tool.semantic_release]` blocks.

**How to apply:**
- Plan acceptance criteria for any version bump: "Use `cz bump --increment
  X`; verify CHANGELOG.md auto-update"; do NOT include manual heading edits.
- If a release theme/narrative is needed, prepare it as a separate file or
  as the body of the release commit; commitizen will fold it in.
- If CHANGELOG.md ever shows duplicate `## vX.Y.Z` headings, the cause is
  manual heading + commitizen auto-insertion conflict — revert and let
  commitizen own the heading.

**Cross-ref:** Global L-303 (pip-audit findings can surface mid-session
from online DB refresh — adjacent release-pipeline gotcha).

---
