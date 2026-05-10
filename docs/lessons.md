# Lessons Learned (aa-ma-forge)

Project-local pattern + prevention rules. Reviewed at session start.
Newest at top. See also: `~/.claude/rules/self-improvement-loop.md`.

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
