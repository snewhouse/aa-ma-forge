# onboarding-team — the Deep-tier `TeamCreate` composition

Used by `Skill(understand-codebase)` Deep tier. Modelled on `Skill(agent-teams)` (7-phase
lifecycle). A REVIEW-flavoured team (parallel investigation → synthesis → QA), not an
implementation team — no debate mode needed; the "competing hypotheses" are just independent
dimension coverage.

> **Fallback:** if `TeamCreate` is unavailable or any step fails to spawn, abort the team, clean
> up whatever was created, and fall back to **enhanced Standard** (still run `/index`,
> `gsd-map-codebase` ×4, `/codebase-deep-dive`, the 3 onboarding worker agents directly, and the
> WebSearch/Context7 enrichment — just without the formal team/task-list). Note the downgrade in Provenance.

---

## Team identity
- Name: `understand-codebase-<repo-slug>` (slug = repo dir name, lowercased, non-alnum → `-`).
- Type: REVIEW (parallel investigation + synthesis + QA).
- Created with `TeamCreate({ team_name, ... })` → produces `~/.claude/teams/<name>/` and `~/.claude/tasks/<name>/`.

## Roles / teammates
| Name | `subagent_type` | Role | Writes |
|---|---|---|---|
| `orchestrator` | (you — the skill) | Create team, build task list, dispatch, collect confirmations only, run the `AskUserQuestion` AGENTS.md gate, shutdown+cleanup. Keep context lean — receive confirmations, not document bodies. | — |
| `mapper-tech` | `gsd-codebase-mapper` | focus `tech` | `.planning/codebase/STACK.md`, `INTEGRATIONS.md` |
| `mapper-arch` | `gsd-codebase-mapper` | focus `arch` | `.planning/codebase/ARCHITECTURE.md`, `STRUCTURE.md` |
| `mapper-quality` | `gsd-codebase-mapper` | focus `quality` | `.planning/codebase/CONVENTIONS.md`, `TESTING.md` |
| `mapper-concerns` | `gsd-codebase-mapper` | focus `concerns` | `.planning/codebase/CONCERNS.md` |
| `deep-dive` | (invoke `/codebase-deep-dive` directly, or `subagent_type=general-purpose` driving it) | quality / security / flow + Mermaid diagrams | `.claude/reports/codebase-deep-dive-<ts>/*` |
| `conventions` | `codebase-onboarding-conventions` | dims 9, 10, 11, 17 | `.claude/onboarding/06-conventions-versioning-git.md`, `07-rules-and-agent-instructions.md` |
| `runbook` | `codebase-onboarding-runbook` | dims 5, 6, 7, 8, 12-observability, 3-datamodel | `.claude/onboarding/04-build-run-debug.md`, `05-tests-ci.md`, `08-integrations-observability-security.md` |
| `health` | `codebase-onboarding-health` | dims 13, 14-evidence, 12-vuln, 2-currency | `.claude/onboarding/09-repo-health-and-verdict.md` (evidence part); adds "Version currency" to `01-stack.md` |
| `synthesizer` | `codebase-onboarding-synthesizer` | dims 1-4, 14-verdict, 15, 16, 17, 18, 19 | `ONBOARDING.md`, `.claude/onboarding/00-index.md`, `01-stack.md`, `02-architecture.md`, `03-structure.md`; + `AGENTS.md`/`AGENTS.review.md`/`AGENTS.draft.md` per `AGENTS-MD-TEMPLATE.md` (consent via orchestrator) |
| `reviewer` | `code-reviewer` (or `comprehensive-review:code-reviewer`) | QA: verify every claim against the codebase; flag boilerplate; run the secret-leak grep; check SKILL.md acceptance criteria | posts findings as task comments / `SendMessage` |

## Task list (create with `TaskCreate`, wire deps with `TaskUpdate addBlockedBy`)
```
T1  index            — ensure PROJECT_INDEX.json exists (run /index if not)            [no deps]
T2  map-tech         — mapper-tech writes STACK.md, INTEGRATIONS.md                      [blockedBy: T1]
T3  map-arch         — mapper-arch writes ARCHITECTURE.md, STRUCTURE.md                  [blockedBy: T1]
T4  map-quality      — mapper-quality writes CONVENTIONS.md, TESTING.md                  [blockedBy: T1]
T5  map-concerns     — mapper-concerns writes CONCERNS.md                                [blockedBy: T1]
T6  deep-dive        — /codebase-deep-dive → .claude/reports/... + diagrams              [blockedBy: T1]   (skip if a fresh one exists — absorb instead)
T7  conventions      — conventions agent writes 06-*, 07-*                               [blockedBy: T1]   (can read .planning/codebase/CONVENTIONS.md if T4 done, else derive)
T8  runbook          — runbook agent writes 04-*, 05-*, 08-*                             [blockedBy: T1]
T9  health           — health agent writes 09-* (evidence) + version-currency            [blockedBy: T1, (soft) T5, T6]
T10 enrich-currency  — WebSearch+Context7 version/EOL/CVE pass (folded into T9 or standalone) [blockedBy: T2]
T11 synthesize       — synthesizer writes ONBOARDING.md + 00-03 + verdict + playbooks    [blockedBy: T2,T3,T4,T5,T6,T7,T8,T9]
T12 agents-md-gate   — orchestrator AskUserQuestion (per AGENTS-MD-TEMPLATE SAFETY PROTOCOL); synthesizer writes AGENTS.md / AGENTS.review.md / AGENTS.draft.md accordingly [blockedBy: T11]
T13 review           — reviewer verifies everything; corrections applied                 [blockedBy: T11, T12]
T14 shutdown         — orchestrator: collect, summarise to chat, SendMessage teammates to stop, TeamDelete/cleanup [blockedBy: T13]
```
T2–T8 run in parallel once T1 is done. Spawn the mapper/worker agents with `Agent({ team_name, name, subagent_type, prompt, run_in_background: true })`.

## Dispatch notes
- **Every spawned agent prompt MUST include** (verbatim): the **NO-SECRETS** constraint; "evidence
  or it didn't happen"; the target path; a `<required_reading>` block listing `PROJECT_INDEX.json`
  (if present), the relevant `references/*.md` for its dimensions, and any absorbed `.planning/codebase/*`.
- **Agents write to disk, not back to the orchestrator** — they return a short confirmation +
  line counts. The orchestrator never holds the document bodies (token discipline — same as
  `gsd-map-codebase`).
- **Absorb-before-run:** before T2–T6, the orchestrator checks for fresh `.planning/codebase/*` /
  `.claude/reports/codebase-deep-dive-*/` / `PROJECT_INDEX.json` and *cancels* the corresponding
  task(s), recording "absorbed" in the Provenance scratchpad. (See `references/REUSE-MAP.md`.)
- **AGENTS.md gate (T12):** the **orchestrator** runs the `AskUserQuestion` (it's HITL — needs the
  human); the **synthesizer** does the writing. Never overwrite an existing `AGENTS.md` — sidecar
  only. Read `references/AGENTS-MD-TEMPLATE.md` first.
- **Reviewer brief (T13):** "Read `ONBOARDING.md` + `.claude/onboarding/**`. For each factual
  claim, verify against the codebase (file exists? command valid? git fact true?). Flag any
  boilerplate not grounded in THIS repo. Run `grep -rEi 'api[_-]?key\s*=\s*\S|BEGIN [A-Z ]*PRIVATE KEY|password\s*=\s*\S|secret\s*=\s*[\"\x27]\S' ONBOARDING.md .claude/onboarding/` — must be zero hits. Check the acceptance criteria in `understand-codebase/SKILL.md`. Return: PASS / FIX-LIST."
- **Shutdown (T14):** `SendMessage` each teammate "task complete — you may stop"; teammates going
  idle between turns is normal. Then `TeamDelete` (or leave the team dir if the user wants the audit
  trail — ask). Report to chat: which tools ran vs absorbed, the AGENTS.md action, the reviewer
  verdict, and "ONBOARDING.md is at `<repo>/ONBOARDING.md`; deep-dives in `.claude/onboarding/`".

## 7-phase mapping (for cross-reference with `Skill(agent-teams)`)
1. **ANALYZE** — Step 0 absorb; detect languages; size the repo; decide which heavy tools to run vs absorb.
2. **COMPOSE** — pick the roles above (drop `deep-dive`/some mappers if their output is being absorbed).
3. **APPROVE** — `AskUserQuestion`: confirm Deep tier, target path, "OK to run `gsd-map-codebase` + `/codebase-deep-dive` (writes to `.planning/` and `.claude/reports/`)?".
4. **SPAWN** — `TeamCreate` → `TaskCreate` ×14 + deps → `Agent(... run_in_background)` for T2–T9.
5. **COORDINATE** — poll `TaskList`; as tasks complete, unblock T11; run T10 enrichment; collect confirmations.
6. **SHUTDOWN** — T11 synth → T12 AGENTS.md gate → T13 review + fixes → final chat summary.
7. **CLEANUP** — `SendMessage` stop; `TeamDelete`; (optionally keep the team dir as audit trail if asked).
