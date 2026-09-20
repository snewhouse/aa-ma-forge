# Matt Pocock's `wayfinder`, `prototype`, `research` — adoption research for aa-ma-forge

**Created:** 2026-09-20
**Author:** Stephen Newhouse, Claude (research session; three parallel read-only agents — local adoption audit, upstream web research, AA-MA seam map)
**Reviewed-Through-Date:** 2026-09-20 (upstream HEAD 2026-09-18; plugin cache 1.2.3 installed 2026-07-30)
**Valid-Through:** 2026-Q4 (re-fetch upstream if reviewing after this date; 12 unreleased changesets were pending on `main` at review time)
**Plan-Version:** none yet — feeds ADR-0011 / ADR-0012 / ADR-0013 (Proposed) and a follow-up `/aa-ma-plan mattpocock-trio-adoption`
**Sources:** https://github.com/mattpocock/skills @ c55ee46 (gh api, raw.githubusercontent.com) · X posts and Latent Space article linked inline · local plugin cache `~/.claude/plugins/cache/claude-plugins-official/mattpocock-skills/1.2.3` · this repo at `ecd4570` (path:line cites inline)
**Inventory-Files:**
- [`_inventories/mattpocock-inventory.json`](_inventories/mattpocock-inventory.json) — frozen 2026-05-10 snapshot (27 skills; predates all three subjects)
- [`_inventories/mattpocock-inventory-2026-09-20.json`](_inventories/mattpocock-inventory-2026-09-20.json) — partial delta snapshot for the three subjects + renames since May

---

## 1. Question

Can `wayfinder`, `prototype` and `research` from [mattpocock/skills](https://github.com/mattpocock/skills) be used or adapted inside AA-MA Forge's planning/execution workflow — and where exactly would they plug in? Ste's stated style (2026-09-20): "a big fan of prototyping and actually coding up solutions using trial and error."

## 2. Upstream state (verified 2026-09-20 via `gh api` + raw.githubusercontent.com)

- Repo: https://github.com/mattpocock/skills — default `main`, last push 2026-09-18. Latest release **v1.2.3** (2026-08-06); tags v1.0.0/1.0.1 (06-17), v1.1.0 (07-08), v1.2.0/1.2.2 (08-05). `plugin.json` version 1.2.3 lists 25 promoted skills (18 engineering + 7 productivity); `in-progress/` (9) and `misc/` (4) are excluded from the plugin.
- Organising invariant (added 2026-08-15, `.agents/invocation.md`): **user-invoked** skills orchestrate and are only reachable by typing; **model-invoked** skills are reusable discipline. A skill may only `Skill`-call model-invoked skills.
- Renames since our 2026-05-10 inventory: `diagnose`→`diagnosing-bugs`, `to-prd`→`to-spec`, `to-issues`+`to-plan`→`to-tickets`, `write-a-skill`→`writing-great-skills`→`writing-for-agents` (our `write-a-skill` fork is an orphan of a deleted upstream — [CHANGELOG 1.0.0](https://github.com/mattpocock/skills/blob/main/CHANGELOG.md)). New: `research` (07-01), `wayfinder` (07-06, from `in-progress/decision-mapping`), `implement`, `code-review`, `wizard`, `wait-what`, `grilling` (primitive), `domain-modeling`, `codebase-design`, `resolving-merge-conflicts`.
- README philosophy: "Approaches like GSD, BMAD, and Spec-Kit try to help by owning the process… These skills are designed to be small, easy to adapt, and composable." Matt on X 2026-07-16: "superpowers is an extremely useful skill set. It's just not for me." ([post](https://x.com/mattpocockuk/status/2077789970509463657))
- Main flow ([ask-matt SKILL.md](https://github.com/mattpocock/skills/blob/main/skills/engineering/ask-matt/SKILL.md)): `/grill-with-docs` → (detour `/prototype` in a fresh session via `/handoff`) → `/to-spec` → `/to-tickets` → `/implement` (+ `/tdd`, `/code-review`). On-ramps: `/triage`, `/diagnosing-bugs`, `/wayfinder`.

### 2.1 `research` — [skills/engineering/research/SKILL.md](https://raw.githubusercontent.com/mattpocock/skills/main/skills/engineering/research/SKILL.md)

- Model-invoked. 794 bytes; three rules, unchanged since creation (2026-07-01, PR #409; only em-dash purge 08-19 since):
  1. Spin up a **background agent**; investigate against **primary sources** (official docs, source, specs, first-party APIs) — "follow every claim back to the source that owns it".
  2. Write findings to **a single Markdown file**, citing each claim's source.
  3. **Save where the repo already keeps such notes**; match convention; otherwise somewhere sensible and say where.
- No gates, no stopping criterion, no source allowlist, no agent-type restriction.
- Matt's intent: X 2026-07-01 "Proposal: a /research skill… spins up a background agent to look at high-trust sources, and saves them in a markdown file" ([post](https://x.com/mattpocockuk/status/2072343173595029659)); docs: "Research is legwork you delegate, not thinking you outsource"; output "is something to take into the main flow at /grill-with-docs" ([docs/engineering/research.md](https://github.com/mattpocock/skills/blob/main/docs/engineering/research.md)).
- Documented failure modes (same docs page): **self-nesting** — the background agent is `general-purpose`, holds the Agent tool, re-spawns itself (issue #530: ~450k tokens across three overlapping runs; no shipped fix); the opposite failure when global rules forbid re-delegation (silently does nothing); no stopping criterion; "nothing auto-loads a past research file"; issue #576 research agents opening draft PRs from `research/<name>` branches.

### 2.2 `prototype` — [skills/engineering/prototype/](https://github.com/mattpocock/skills/tree/main/skills/engineering/prototype) (SKILL.md, LOGIC.md, UI.md, agents/openai.yaml)

- Model-invoked since 2026-06-29 (commit 850873c). "A prototype is throwaway code that answers a question. The question decides the shape."
- Branch gate: "Does this logic/state model feel right?" → LOGIC; "What should this look like?" → UI. Ambiguous + user unreachable → infer from surrounding code and state the assumption at the top of the prototype.
- Six shared rules: (1) throwaway from day one and clearly marked; (2) trivial to run — one task-runner command or a double-click HTML file; (3) no persistence by default; (4) no polish (no tests/error handling/abstractions); (5) surface the state after every action; (6) **capture when done** — fold the validated decision into real code, commit the prototype to a throwaway `prototype/<name>` branch off main, leave a context pointer on the implementation issue. "Throwaway is a constraint on how the code is written, not a promise to destroy it" ([docs/engineering/prototype.md](https://github.com/mattpocock/skills/blob/main/docs/engineering/prototype.md)).
- **LOGIC.md (rewritten 2026-07-17, commit 6bcbcb0, v1.2.0):** isolate the logic as a pure module in one `<script>`; build **one self-contained HTML file** (no framework/bundler/server) for a non-developer in domain language: title + one-line explanation → current-state panel → free-play buttons (one per action) → guided walkthroughs as tabs (happy path, tricky edge, illegal attempt) with reset. Replaced the terminal TUI.
- **UI.md:** variants on an existing route gated by `?variant=` (default 3, cap 5), radically different in structure not colour, floating bottom-centre switcher hidden when `NODE_ENV=production`; losers + switcher go to the throwaway branch. Unchanged mechanics since May.
- History since our fork (2026-05-10): model-invoked (06-29); "capture, don't dispose" (07-09/10, v1.2.0); HTML logic demo (07-17, v1.2.0); Codex yaml (07-13); em-dash purge (08-19). Docs FAQ notes agents recommending `/prototype` when `/implement` was right ("a naming problem") and full-app prototypes becoming production "by momentum". "Wayfinder is its largest consumer."

### 2.3 `wayfinder` — [skills/engineering/wayfinder/SKILL.md](https://raw.githubusercontent.com/mattpocock/skills/main/skills/engineering/wayfinder/SKILL.md) (11.9 KB)

- **User-invoked only** (`disable-model-invocation: true`). "Plan a huge chunk of work (more than one agent session can hold) as a shared map of decision tickets on your issue tracker, and resolve them one at a time until the way to the destination is clear." Premise: "Plan, don't do" — output is decisions, not deliverables; "refer by name, never bare #id".
- **The Map** = one tracker issue labelled `wayfinder:map`. Body: `## Destination` (1–2 lines) · `## Notes` (domain, skills to consult, standing preferences) · `## Decisions so far` (index — one line + link per closed ticket; "an index, not a store") · `## Not yet specified` (fog) · `## Out of scope`. Open tickets are not listed; found by query.
- **Decision tickets** = child issues; body is `## Question` only; sized to one ~100K-token session; label `wayfinder:<type>`:
  | Type | Mode | Resolved by |
  |---|---|---|
  | research | **AFK** | subagent calling `Skill("research")`; findings on throwaway `research/<name>` branch |
  | prototype | **HITL** | `Skill("prototype")`; artefact linked as asset |
  | grilling | **HITL (default)** | `Skill("grilling")` + `Skill("domain-modeling")` — "the agent never stands in for the human's side… a grilling agent that answers its own questions has broken this" |
  | task | HITL or AFK | manual unblocking work (provision access, move data) — "the one type that does rather than decides" |
- Claim = assign to self before any work. Blocking = tracker-native dependency. Frontier = open + unblocked + unclaimed. Fog test: "whether you can state the question precisely now, not whether you can answer it now." Out of scope never graduates.
- **Chart mode:** (1) name the destination via grilling + domain-modeling; (2) grill breadth-first for the frontier — if no fog surfaces, "you don't need a map", stop; (3) create the map; (4) create specifiable tickets, then wire blocking edges in a second pass; (5) fire one research subagent per research ticket in parallel; (6) stop — charting resolves nothing.
- **Work mode:** (1) load map low-res; (2) pick named or first-frontier ticket, **claim**; (3) resolve, zooming into related closed tickets; (4) resolution comment, close, append to Decisions so far; (5) add/graduate/rule-out tickets. **Never more than one non-research ticket per session.** When the map clears: hand off to `/to-spec #<map>` → `/to-tickets` → `/implement`; wayfinder never builds.
- Tracker wiring comes from `/setup-matt-pocock-skills` (writes `docs/agents/issue-tracker.md`; GitHub via `gh` sub-issues + `blocked_by`, GitLab via `glab`, or local markdown `.scratch/<effort>/map.md` + `issues/NN-<slug>.md` with `Type:/Status:/Blocked by:` lines). Local-markdown is "not recommended" upstream because of accidental persistence in the repo.
- Lineage: `in-progress/decision-mapping` (06-17) → `wayfinding`/`wayfinder` (07-01) → 36 commits in a week (map onto tracker 07-01; "planning by default, overridable via Notes" 07-06; "stop the agent grilling itself" 07-06) → graduated 07-06, v1.1.0 07-08 → "burn research tickets down with subagents" 07-13. Nothing substantive since 08-19.
- Matt's intent: X 07-02 "I think this replaces /grill-with-docs in my stack (as an orchestrator over the top of it)" ([post](https://x.com/mattpocockuk/status/2072599827540578664)); X ~07-02 "planning an entire course with it… closing in on 100 separate grilling/prototyping/research sessions all contributing back to a central map" ([post](https://x.com/mattpocockuk/status/2072716979195326905)); X 07-30 "give it a destination and it will: figure out the frontier of things that can be decided now; uncover the route ahead as you go; research, prototype, and discuss with you; maintain a map in an issue tracker" ([post](https://x.com/mattpocockuk/status/2082774006189449355)); Latent Space interview 2026-08-20 — Map / Ticket / Session as the three entities ([article](https://www.latent.space/p/wayfinder-skill)). **But** the v1.1 CHANGELOG (PR #464) settled it as "a situational on-ramp, not the new main entry flow — the grill-led idea → ship chain stays the front door (crowning wayfinder as the default spine is a v2-sized move)."
- Field-reported failure modes ([docs/engineering/wayfinder.md](https://github.com/mattpocock/skills/blob/main/docs/engineering/wayfinder.md); [Discussion #484](https://github.com/mattpocock/skills/discussions/484)): agent writes production code mid-map ("no hard in-skill stop"); 27-ticket maps whose later tickets go stale ("prototypemaxxing, not planmaxxing"); grilling verbosity / decision exhaustion; no guidance on reversing a closed decision; parallel prototype tickets where the agent picks the winner itself; users finding it "a lot more babysitting, and a lot more tokens" and asking for "a lite version".

### 2.4 Community comparisons (skimmed, not load-bearing)

- [jamilxt, dev.to 2026-07-18](https://dev.to/jamilxt/superpowers-vs-agent-skills-vs-pocock-three-philosophies-of-ai-coding-workflows-e6n): Pocock = requirements clarity + composability; Superpowers = autonomy pipeline.
- [Pulumi: Superpowers, GSD, gstack](https://www.pulumi.com/blog/claude-code-orchestration-frameworks/), [imaginex, dev.to](https://dev.to/imaginex/a-claude-code-skills-stack-how-to-combine-superpowers-gstack-and-gsd-without-the-chaos-44b3): "gstack thinks, GSD stabilizes, Superpowers executes" — Pocock not central.
- Unverified / not found: a YouTube video by Matt on any of the three; full X thread bodies (X returns 402); the aihero.dev v1.1 changelog post (404).

## 3. Local state (aa-ma-forge @ v0.12.0, 2026-09-20)

| Skill | Status | Evidence |
|---|---|---|
| `prototype` | Forked 2026-05-10 ([ADR-0003](../adr/0003-prototype-adoption.md)), `claude-code/skills/prototype/{SKILL,LOGIC,UI}.md`, symlinked from `~/.claude/skills/prototype` by `install.sh`. **Major drift:** fork LOGIC = terminal TUI, rule 6 = "delete or absorb"; upstream = HTML demo, "capture when done". `claude-code/rules/engineering-standards.md:21-31` still says "LOGIC (terminal TUI…)". | local-adoption audit; `diff` fork vs plugin cache 1.2.3 |
| `research` | Never forked; post-dates the 2026-05-10 inventory; no prior verdict. **Name collision:** `~/.claude/skills/research/SKILL.md` is an unrelated PAI-style skill whose body says "Execute the `/conduct-research` slash command" — no such file exists under `~/.claude` (dead pointer). | `find ~/.claude -name 'conduct-research*'` → none |
| `wayfinder` | Not in repo, inventory, or ADRs. Present only in `~/.claude/plugins/cache/claude-plugins-official/mattpocock-skills/1.2.3/skills/engineering/wayfinder/`. | `grep -ri wayfinder docs/ claude-code/ CHANGELOG.md` → 0 |
| `grill-with-docs` | Forked (ADR-0002), wired into `/aa-ma-plan` Phase 1.3. **Upstream is now a one-liner** delegating to `grilling` + `domain-modeling`; `CONTEXT-FORMAT.md`/`ADR-FORMAT.md` moved to `domain-modeling/`. Out of scope here; flagged. | plugin cache diff |
| `write-a-skill` | Forked (ADR-0004); **deleted upstream** (→ `writing-for-agents`). Orphan. Out of scope; flagged. | CHANGELOG 1.0.0, 1.2.0 |

Plugin cache note: `installed_plugins.json` records `gitCommitSha 2ab95809…` (2026-07-30) while the marketplace catalogue points at `959a8e9f…` — the cache itself may lag HEAD.

## 4. AA-MA seams (path:line as of v0.12.0)

### 4.1 Where research happens today — and doesn't land

- `claude-code/commands/aa-ma-plan.md` **Phase 3: Research & Documentation Gathering** (:373-426): 3.2 Context7 with retry-once → WebSearch fallback (:383-398); 3.3 parallel `Explore` agents on haiku (:400-412); 3.4 consolidate — **"save to memory, show brief on screen"** (:414-426). Marker `3 DONE context7_calls=<N> web_fetches=<N>` (:88). Detailed procedure `claude-code/skills/aa-ma-plan-workflow/references/PHASE_3_RESEARCH.md` (tool hierarchy :18-31; names `research-consolidation` at :14 and :201-207 — a skill that is **not shipped** in `claude-code/skills/`).
- Only durable landings: Step 5.4 context-log `**Research Findings:** [Summary from Phase 3]` (:729-730) and Step 5.3 reference.md fact extraction (:686-712). Spec `docs/spec/aa-ma-specification.md:283-289` has a `## [date] Research: [Title]` context-log entry type; no research/spike file type among the 8 (:16-41).
- **Existing convention that rule 3 would match:** `docs/research/` with `Created / Author / Reviewed-Through-Date / Valid-Through / Plan-Version / Inventory-Files` header (`docs/research/skill-ecosystem-audit.md:1-12`) and `_inventories/*.json` with `_meta.{source_url, fetched_at, verifier_method}`.
- Other research tooling: `understand-codebase` (ADR-0006) writes `ONBOARDING.md` + `.claude/onboarding/` — orientation, explicitly not per-plan (:65, :296); `~/.claude/skills/gsd-research-phase` writes `.planning/phases/*/RESEARCH.md` (GSD, not ours).

### 4.2 `Prototype-Required` end to end

- Rule: `claude-code/rules/engineering-standards.md:21-31` (Theme 1) — "When a task carries `Prototype-Required: YES`, invoke `Skill(prototype)`… Then write a `[ts] PROTOTYPE — <verdict>` entry to `provenance.log` before milestone COMPLETE"; checklist row :120; absent-field skip :125-127.
- Values: `src/aa_ma/enforce.py:48` `PROTOTYPE_REQUIRED = frozenset({"YES", "NO"})`, case-folded (:115). `TDD-Waiver: prototype` exists in `src/aa_ma/plan_parsers.py:47-59`.
- Gate: `src/aa_ma/gate.py:231-235` reads it in `_read_milestone`; `_own_text` (:202-206) truncates at the first `###`, so **sub-step flags are never read** — yet `docs/templates/tasks-template.md:111-113` offers a sub-step slot "same semantics as milestone". JSON schema `gate.py:99-121` (`additionalProperties: False`) exposes `prototype_required: bool`.
- Evidence: `claude-code/commands/execute-aa-ma-milestone.md:594-620` (§6.7 condition 5) — `grep -F "PROTOTYPE —" provenance.log | grep -qF "${MILESTONE_TITLE}"`; bypass `AA_MA_HOOKS_DISABLE=1` (:630-633). Step-level advisory `execute-aa-ma-step.md:242-246`.
- Verification: `claude-code/skills/plan-verification/SKILL.md:339, :351-387`. Tests: `tests/test_gate.py:57, :103-112, :397-412`; fixture `tests/hooks/fixtures/gate-scans/styles-tasks.md:28,:38`.
- **Planning never asks the question:** `aa-ma-plan.md` has zero occurrences of "Prototype"; only `docs/templates/engineering-standards-template.md:33-36` mentions it. Provenance grammar in the spec (:302-326) omits the `PROTOTYPE —` / `CRITICAL_PATH_REVIEW —` line formats.

### 4.3 Where a pre-plan map would sit

- `/aa-ma-plan` Phase 1.3 Grill Protocol (:133-209, modes auto|with-docs|simple|skip) and Phase 2 `superpowers:brainstorming` (:282) both assume the idea already fits one planning session. Nothing persists decisions made *before* `Phase 5` creates `.claude/dev/active/<task>/`.
- AA-MA vocabulary already matches wayfinder's: `Mode: HITL|AFK` (`enforce.py:47`; step→milestone→HITL resolution `gate.py:281-288`); `Status` enums (`enforce.py:34,39`); canonical heading grammar `src/aa_ma/grammar.py:74-82, :264-265`. `docs/spec/aa-ma-specification.md` file taxonomy :16-41 lists 8 file types; templates index `docs/templates/README.md:7-16`.
- Adding a gate-read field means editing `MilestoneRead`, the schema, `to_kv`, `tests/test_gate.py`; adding a planning-only enum means a `CANONICAL_*` frozenset + parser + Angle 6 item + rule table + template slot + ADR ("via plan + ADR", `engineering-standards.md:36-38`, `plan_parsers.py:86,:182-186`). `src/aa_ma/{gate,enforce,grammar,plan_parsers}.py` are `Critical-Path: hook-modification` surface (`engineering-standards.md:45`).

### 4.4 Adoption checklist (from ADR-0003's commits 6e2bc4c, 1d1b304, a796442, e5af1e0, b82e513, 0a342ba)

1. `claude-code/skills/<name>/` with line-1 `<!-- Forked from <URL> on <date> — aa-ma-forge vN.N.N -->`; MD5s recorded in the ADR.
2. `docs/adr/NNNN-<name>-adoption.md` + `docs/adr/INDEX.md` row.
3. `tests/skills/test_<name>_frontmatter.py` via `tests/skills/_helpers.py::assert_skill_frontmatter` (skips leading `<!--` lines).
4. Wiring in a rule or command.
5. Counts: `SECURITY.md:12`, `README.md`, `CHANGELOG.md ## Unreleased`, `docs/spec/claude-code-foundations.md`, `docs/spec/aa-ma-quick-reference.md`; credit in `docs/ATTRIBUTION.md:15-21`.
6. No `install.sh` change — `scripts/install.sh:263-268` auto-discovers `claude-code/skills/*/`.

## 5. Analysis (Socratic pass)

1. **Clarification.** The ask is "use or adapt", not "adopt". The problem beneath: AA-MA is strong on *execution* memory and weak on *discovery* memory and on *empirical validation before commitment*. Each of the three targets one of those.
2. **Assumptions challenged.**
   - *Adopt wayfinder verbatim* — rejected. It would stand up a second long-horizon memory (the tracker) beside `.claude/dev/active/`, and pull in `setup-matt-pocock-skills`, `grilling`, `domain-modeling`. Upstream itself demoted it to an on-ramp; users want a lite version. Upstream's objection to local-markdown (accidental repo persistence) **inverts** for AA-MA, where persistence in `.claude/dev/` is the point.
   - *`research` is too small to bother with* — rejected. Its rule 3 is precisely the missing Phase 3.4 contract, and the local `research` skill is broken.
   - *`prototype` is done* — rejected. Four months of drift, and upstream moved toward Ste's style (keep the prototype; shareable HTML). The larger miss is process: the flag is never asked for, and the gate ignores the per-task slot the template advertises.
3. **Evidence.** All claims above are from fetched source or `path:line` in this repo; nothing is inferred from memory.
4. **Alternatives** considered per skill: verbatim fork / adapt concept / document only. Verbatim for `research` and `prototype` (small, model-invoked, self-contained); adapt for `wayfinder` (user-invoked orchestrator with external deps).
5. **Implications.** Skill count changes touch five count locations; `research` name collides with a dead local dir (install.sh backup path must be verified); gate changes are `hook-modification` critical path; a 9th optional AA-MA file type touches the spec, templates and TUI parser tolerance.
6. **Meta.** Right problem — yes: discovery memory + empirical validation. Wrong problem to avoid: re-platforming AA-MA on wayfinder.

## 6. Decisions (Ste, 2026-09-20) → ADRs

| # | Decision | ADR |
|---|---|---|
| 1 | **`prototype`: re-sync to upstream 1.2.3; add an explicit Step 2.5 "Prototype decision" to `/aa-ma-plan`; gate aggregates milestone-or-any-sub-step `YES`; adopt `prototype/<name>` branch capture; add PROTOTYPE/CRITICAL_PATH_REVIEW line formats to the spec's provenance grammar.** | [ADR-0011](../adr/0011-prototype-resync-and-planning-gate.md) |
| 2 | **`research`: fork the 3-rule skill with two hardening lines (dispatch as `Explore`; stopping rule); wire Phase 3.3/3.4 to write `docs/research/<plan-slug>-<topic>.md`; marker gains `research_files=`; replace the dead `~/.claude/skills/research`.** | [ADR-0012](../adr/0012-research-skill-adoption.md) |
| 3 | **`wayfinder` → "charting" (wayfinder-lite): `/aa-ma-chart <effort>` + single-file map `.claude/dev/charting/<effort>/<effort>-map.md`; tickets typed research/prototype/grilling/task with AA-MA `Mode:`; no tracker; exit via `/aa-ma-plan --from-map`; map becomes optional 9th AA-MA file type. v1 = markdown + command only.** | [ADR-0013](../adr/0013-charting-wayfinder-lite.md) |
| 4 | Delivery: this document + three Proposed ADRs now; implementation via `/aa-ma-plan mattpocock-trio-adoption` (M1 prototype, M2 research, M3 charting). | — |

Out of scope, flagged for later ADRs: `grill-with-docs` drift; orphaned `write-a-skill`; `research-consolidation` (referenced, unshipped); `skill-ecosystem-audit.md` `Valid-Through: 2026-Q3` expiry.
