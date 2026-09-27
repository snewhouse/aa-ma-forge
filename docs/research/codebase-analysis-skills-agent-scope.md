# Can this repo's audit agents run against a whole repository rather than a milestone diff?

**Created:** 2026-09-27
**Author:** aa-ma-researcher (Claude), for charting effort `codebase-analysis-skills` Ticket 3
**Reviewed-Through-Date:** 2026-09-27 (repo state at `d250ee3`, branch `main`)
**Valid-Through:** 2026-Q4 (edits to any of the 5 audit-agent contracts, `claude-code/skills/verify-impl/SKILL.md`, the 4 `codebase-onboarding-*` agents, or their pinning tests invalidate this)
**Sources:**
- `claude-code/skills/verify-impl/SKILL.md:25-30,52-96,121-125,155-180` — dispatcher inputs, base/head resolution, output file, CRITICAL panel
- `claude-code/agents/code-reviewer.md:14,18-24,34-39,65,73-75,90,124` — diff-only contract, scope-discipline CRITICAL
- `claude-code/agents/security-auditor.md:4,12,16-22,74,100` — inputs, hook-deferral
- `claude-code/agents/future-proofing-auditor.md:12,15-19,25-47,100-102` — "added lines only" contract
- `claude-code/agents/tdd-sequence-auditor.md:4,15-20,37-56` — git-log window forensics
- `claude-code/agents/context7-evidence-auditor.md:12,15-19,30-31,58-73` — new-dep detection via diff
- `claude-code/agents/codebase-onboarding-{conventions,health,runbook,synthesizer}.md` — repo-wide workers
- `claude-code/commands/execute-aa-ma-milestone.md:745-764,776-800,812-842` — §6.8 grandfathering, dispatch, override panel, defer sub-steps
- `claude-code/commands/sole-dev-merge.md:268-278,317-332` — existing non-milestone invocation of code-reviewer/security-auditor
- `claude-code/skills/understand-codebase/SKILL.md:200-217,267-289` — onboarding workers' dispatch + code-reviewer reused as docs QA
- `claude-code/hooks/security-static-check.sh:4,118,139` — mechanical layer scans the staged diff only
- `tests/skills/test_verify_impl_agents.py:22-189`, `tests/agents/test_codebase_onboarding_agents.py:26-70`, `tests/hooks/execute_aa_ma_milestone_phase_6_8.bats:42-58`, `tests/skills/test_understand_codebase_rewire.py:20-34` — contract pins
- `git diff --stat 4b825dc642cb6eb9a060e54bf8d69288fbee4904 HEAD` (run 2026-09-27) — whole-repo diff size

## Answer

Not through `Skill(verify-impl)`: its inputs are a task directory plus a milestone number and it aborts without them (`verify-impl/SKILL.md:27-30,73-81`), and it gives no way to pass in a base SHA (`SKILL.md:93-96`). The individual agents take a `<base>..<head>` pair, and the empty tree `4b825dc…` works as a git base on this repo (659 files, 122,334 insertions). But every agent is written around "what the diff added, not what already existed". Given the empty tree as base, the whole repo counts as "added". Scope-discipline then raises roughly one CRITICAL per file, each CRITICAL opens its own accept/dispute/defer panel, and the diff is about 7.7 MB. The 4 `codebase-onboarding-*` agents are the only ones that already work repo-wide, with no base or head input.

## Evidence

### (1) Required inputs per agent

| Agent | Required inputs (cite) |
|---|---|
| `verify-impl` skill | `<task-name>` (active dir under `.claude/dev/active/`), `<milestone-id>`; computes `<milestone-base-sha>`, `<milestone-head-sha>`, `<audit-profile>` (`SKILL.md:27-30`). The direct form is `--task <name> --milestone <id>` only (`SKILL.md:15`). The per-agent prompt carries task, milestone, base, head, reference.md + provenance.log paths, the milestone's `Required Artefacts`, and `AA_MA_AUDIT_BUDGET` (`SKILL.md:121-125`). |
| `code-reviewer` | task + milestone ids; base/head SHAs for `git diff <base>..<head>`; the milestone's `Required Artefacts` verbatim; `Audit-Profile`; the reference.md path (`code-reviewer.md:18-24`). Also reads `[task]-context-log.md` and prior `[task]-impl-review.md` disputes (`:92-93`). |
| `security-auditor` | task + milestone; base/head; `Required Artefacts`; reference.md; **mechanical-layer status** PASS / BLOCKED-at-commit / BYPASSED (`security-auditor.md:16-22`). |
| `future-proofing-auditor` | task + milestone; base/head; reference.md (`future-proofing-auditor.md:15-19`). |
| `tdd-sequence-auditor` | task + milestone; base/head window; the milestone's `TDD-Waiver:` from `[task]-tasks.md`; reference.md (`tdd-sequence-auditor.md:15-20`). |
| `context7-evidence-auditor` | task + milestone; base/head; the `provenance.log` + `reference.md` paths in the active task dir (`context7-evidence-auditor.md:15-19`). |
| `codebase-onboarding-conventions` / `-runbook` / `-health` | A `<repo>` target plus an optional `<required_reading>` block. They always read `~/.claude/skills/understand-codebase/references/*` (conventions file lines 19-25, runbook 20-23, health 21-25). There is no SHA, task or milestone input. |
| `codebase-onboarding-synthesizer` | The worker outputs `04-09-*.md` already on disk (synthesizer file line 30). An orchestrator-supplied `agents_md_action` (`:38,49-54`). |

Output locations:
- **verify-impl:** one `[task]-impl-review.md` (`SKILL.md:155-157`, `execute-aa-ma-milestone.md:800`) plus a line in `[task]-provenance.log` (`SKILL.md:182-188`).
- **The 5 audit agents:** they write nothing. All 5 declare no Write tool (`code-reviewer.md:4`, `security-auditor.md:4`, `tdd-sequence-auditor.md:4` `tools: Bash, Read, Grep`). They return text that ends in `SUMMARY: <N> CRITICAL, <M> WARNING, <P> INFO`, which the dispatcher parses (`SKILL.md:142`, `code-reviewer.md:111-115`).
- **Onboarding workers:** they write fixed paths under `<repo>/.claude/onboarding/NN-*.md` (conventions:8-9, health:10-11, runbook:8-9). The synthesizer writes `<repo>/ONBOARDING.md` (synthesizer:48).

### (2) Is a whole-repo run possible within the current contract?

- **Sizing (run 2026-09-27):**
  - Diff: `git diff --stat 4b825dc…904 HEAD | tail -1` → `659 files changed, 122334 insertions(+)`. `git diff 4b825dc…904..HEAD | wc -c` → 7,673,064 bytes (126,248 lines).
  - Token estimate: about 1.9M tokens, using a ~4 bytes/token heuristic. No tokenizer was run. That is above the 1M-token context this report was written under.
  - Where the insertions sit: `tests/` 33,083, `.claude/` 30,238, `claude-code/` 23,104, `docs/` 14,893, `packages/` 7,407, `src/` 5,163, `uv.lock` 2,590.
- **Git accepts the empty tree as a base:** `git cat-file -t` → `tree`. The two-dot `git diff 4b825dc…..HEAD` works. `git log 4b825dc…..HEAD` exits 0 and lists all 731 commits (checked on git 2.53.0).
- **Through the dispatcher: no.**
  - Step 1 needs an active task dir and a tasks.md milestone that the gate resolves. Every non-zero gate exit is an `ABORT` (`SKILL.md:52,73-81`).
  - The base comes from a `git log --grep` heuristic, and the command has no parameter that overrides it (`SKILL.md:93-96`). §6.8 describes it the same way (`execute-aa-ma-milestone.md:780-783`).
  - §6.8 is skipped for plans whose `Created:` is before 2026-05-11 (`execute-aa-ma-milestone.md:748-764`).
- **Calling an agent directly with base = empty tree:** the text contract has room for it, because base/head are plain prompt inputs (e.g. `code-reviewer.md:21`). There is precedent for calling these agents outside verify-impl:
  - `sole-dev-merge` Stage C dispatches `code-reviewer` / `security-auditor` on `git diff ${BASE_REF}...HEAD`, with no task or milestone (`sole-dev-merge.md:268-278`).
  - `understand-codebase` Deep tier reuses `code-reviewer` to fact-check docs, with no diff at all (`understand-codebase/SKILL.md:213-216`).
  - In both cases the caller's prompt overrides the agent's own contract. Sole-dev-merge asks for a `[CRITICAL]|[HIGH]|[MEDIUM]|[LOW]` vocabulary (`sole-dev-merge.md:273-278`), while the agents emit `CRITICAL/WARNING/INFO` (`code-reviewer.md:103`). It also asks them to "Write output to /tmp/…" (`sole-dev-merge.md:275`), but the agents have no Write tool (`code-reviewer.md:4`). The aggregator falls back to tagging unparsed output `[HIGH]` (`sole-dev-merge.md:317-326`).

### (3) What breaks or misleads in whole-repo mode

- **Diff-only reasoning becomes vacuous:**
  - `code-reviewer`: "Look at what the diff added, not what already existed. Pre-existing patterns are out of scope" (`code-reviewer.md:14,90`).
  - `future-proofing-auditor`: "You do NOT re-scan the entire codebase" (`future-proofing-auditor.md:12`), and it must not flag "pre-existing magic numbers" (`:102`).
  - With the empty tree as base, nothing counts as pre-existing, so these exclusions filter nothing.
- **Scope-discipline flood:** every diff file that is not in `Required Artefacts` → CRITICAL (`code-reviewer.md:34-39`). A whole-repo run has no milestone and so no artefact list, which puts the cap at about 659 CRITICALs.
- **Override panel flood:** one `AskUserQuestion` per CRITICAL (`SKILL.md:161-174`, `execute-aa-ma-milestone.md:812-823`). Any `accept` → BLOCKED (`SKILL.md:178`). Each `defer` appends a `### Sub-step N.M: [DEFERRED …]` to the active tasks.md (`execute-aa-ma-milestone.md:829-839`). A whole-repo assessment has no milestone to hold those sub-steps.
- **Other counts inflate:**
  - Magic numbers: "3+ occurrences across the milestone" → WARNING (`code-reviewer.md:73-75`), and 5+ → CRITICAL (`future-proofing-auditor.md:60`). A repo-wide window turns every recurring literal into a hit.
  - Hardcoded counts: every prose count in the repo is "ADDED" (`future-proofing-auditor.md:25-47`). The only exclusions are HTML comments and changelogs (`:100-101`). The frozen `docs/plans/` and the 30,238 lines under `.claude/` (completed plans) are not excluded, even though repo policy freezes historical docs (CLAUDE.md "Historical docs are frozen").
- **TDD verdict is a guaranteed FAIL on this repo:**
  - With base = empty tree the window is the whole history.
  - The oldest `tests/` commit and the oldest `src/` commit are the same commit, `446e3a8` (ts 1775396649; it touches `src/aa_ma/__init__.py` and `tests/__init__.py`).
  - The rule `first_test_ts >= first_src_ts → FAIL` (`tdd-sequence-auditor.md:54-56`) therefore yields 1 CRITICAL that says nothing about test quality.
  - The agent audits commit order, not repo state, so "whole repo" means "whole history" for this agent.
- **context7-evidence-auditor:** every `pyproject.toml` dependency line looks newly added (`git diff … -- pyproject.toml | grep '^\+'`, `context7-evidence-auditor.md:31`). Evidence is searched only in one active task's provenance.log / reference.md (`:58-73`). So each dep with no note in that task → WARNING. The agent's ceiling is WARNING (`:12`), so this is noise, not a blocker.
- **The security split assumes a hook ran:**
  - `security-auditor` must not re-flag mechanical patterns "the hook catches" (`security-auditor.md:12,74`) and expects a mechanical-layer status input (`:22`).
  - The hook scans only the **staged** diff of `*.py` files (`security-static-check.sh:4,118,139`). In whole-repo mode no hook ran over most of the code, so mechanical issues fall between the two layers.
- **The inputs assume an active task:** reference.md, provenance.log, context-log.md and prior impl-review.md disputes are all task-scoped (`code-reviewer.md:24,92-93`; `context7-evidence-auditor.md:19,58-73`). With no plan, none of them exist.
- **Token budget:**
  - The full diff is about 7.7 MB.
  - `AA_MA_AUDIT_BUDGET=low` gives a diff-only context with no full-file reads (`SKILL.md:108-111`, `code-reviewer.md:124`, `security-auditor.md:100`). That reduces file reads but still feeds the whole diff to each agent.
  - Nothing in the contract chunks or samples the diff.
  - Parallel dispatch sends up to 5 agents at once (`SKILL.md:127-136`).
- **Output location:** the only output file is `[task]-impl-review.md` inside `.claude/dev/active/<task>/` (`SKILL.md:155`). A whole-repo run has no task dir to put it in.

### (4) What a whole-repo variant would minimally need (options, no recommendation)

- **Option A: a mode flag in the existing agents plus verify-impl.**
  - The agents would take a `scope: repo` input that swaps "added lines" for "all tracked files".
  - It would drop scope-discipline and TDD-sequence in repo mode.
  - It would redefine "pre-existing".
  - Contract lines touched:
    - `code-reviewer.md:14,18-24,34-39,73-75,90,119-126`
    - `security-auditor.md:12,16-22,74,100`
    - `future-proofing-auditor.md:12,15-19,51,102,129-136`
    - `tdd-sequence-auditor.md:15-20` (or exclude it from repo mode)
    - `context7-evidence-auditor.md:15-19,30-31`
    - `verify-impl/SKILL.md:15,25-30,52-96,155,161-180`
  - The dispatch matrix `SKILL.md:34-42` also needs a row. That row would be pinned by `test_skill_documents_audit_profile_dispatch` (`tests/skills/test_verify_impl_agents.py:156-159`) only if it became a new `Audit-Profile` value. Doing that would also touch `src/aa_ma/plan_parsers.py:33-34` (`CANONICAL_AUDIT_PROFILES`).
  - The current tests are substring checks (frontmatter, `SUMMARY:`, `AA_MA_AUDIT_BUDGET`, lesson IDs; `test_verify_impl_agents.py:35-140`). A flag leaves them green as long as that text stays.
- **Option B: new repo-scope agent(s) or skill, with the existing contracts untouched.**
  - Nothing in the 5 agent files or `verify-impl` changes.
  - It adds to the plugin surface: the agent count in `CLAUDE.md` ("12 specialized agents") and the other hardcoded-count docs listed in `CLAUDE.md` "Hardcoded counts go stale".
  - It also needs regenerating `tests/golden/plugin-surface.json`, which is maintained by `scripts/regen-generated.sh`.
  - A new agent would need its own pinning test, like `tests/agents/test_codebase_onboarding_agents.py:38-56`.
- **Option C: a prompt-level override from a new caller, with no contract edits (the sole-dev-merge / understand-codebase pattern).**
  - No agent file changes.
  - The caller's prompt contradicts the agent's own rules: diff-only (`code-reviewer.md:14`), read-only (`:11`), and the severity vocabulary (`:103`).
  - The caller also needs a parse-failure fallback like `sole-dev-merge.md:317-326`.
- **Option D: path-chunked windows under the existing diff contract.**
  - Base = empty tree, restricted to one directory at a time, so each call stays inside the token budget.
  - The current contract has no pathspec input. It would be added at `code-reviewer.md:21`, `security-auditor.md:19` and `future-proofing-auditor.md:18`.
  - This does not remove the pre-existing-exclusion or scope-discipline problems in (3).

### Onboarding agents already repo-wide, and reusable by an assessment skill

- All 4 run over the whole target with no diff:
  - conventions: dimensions 9/10/11/17 (conventions file lines 34-39)
  - runbook: build/tests/CI/env/integrations/data model (runbook:31-38)
  - health: churn, bus-factor, doc drift, TODO backlog, dragons, security-posture signal, verdict draft (health:34-44)
  - synthesizer: weaves the workers' outputs together (synthesizer:17-18)
- Each is described as "reusable standalone" or "invoked directly" (conventions:4,16; health:4,18; runbook:4,17; synthesizer:5,20).
- Limits on reusing them:
  - Output paths are fixed to `.claude/onboarding/NN-*.md` (see (1)).
  - They depend on the `understand-codebase/references/*` templates. These ship in the repo at `claude-code/skills/understand-codebase/references/`, 9 files.
  - `health` is explicitly "Describe, don't audit … not running a pentest" (health:32). It produces an axis verdict, not the `SUMMARY:` severity trailer.
  - `synthesizer` needs `agents_md_action` and writes repo-root `ONBOARDING.md` (synthesizer:38,48). An assessment skill would therefore reuse the 3 workers more naturally than the synthesizer.
- Tests pin only this:
  - name = filename stem, a non-empty description, and `tools` ⊇ {Read, Write} (`tests/agents/test_codebase_onboarding_agents.py:43-56`)
  - the fact that `understand-codebase` SKILL.md and `templates/onboarding-team.md` name all 4 agents (`:59-70`)
  - codemem rewiring text in synthesizer/runbook/conventions (`tests/skills/test_understand_codebase_rewire.py:28-33`)

## Not pursued

- `verify-impl/SKILL.md:93-95` base-SHA fallback: `git log … || git rev-parse HEAD~10`. `git log` exits 0 even when it finds nothing, so the `HEAD~10` fallback looks unreachable. Not verified: it is outside this question.
- Mismatch between `plan_parsers.py:40` ("code-only: All agents except docs-specific lints") and `verify-impl/SKILL.md:39,44` ("both run all 5"). Outside this question.
- §6.8 step 2 says the base comes from the `[AA-MA Plan] <task>` footer (`execute-aa-ma-milestone.md:780-783`), but the skill greps `M<N-1> COMPLETE|chore(aa-ma)` (`SKILL.md:93`). The two methods differ; not reconciled.
- Tokenizer-accurate size of the whole-repo diff: not measured (tiktoken is a dev dep but was not run; ~4 bytes/token heuristic used).
- `docs/adr/0005-post-impl-adversarial-review.md` and `docs/adr/0006-understand-codebase-adoption.md`: not read. The agent contracts were treated as the source of truth, as `SKILL.md:230` says they are.
- `feature-dev:code-reviewer`, `comprehensive-review:code-reviewer`, `gsd-codebase-mapper`: external agents, not in this repo. Not inspected.
- `/codebase-deep-dive`, which the health agent absorbs as an input (health:25): deliberately not read (clean-room constraint).
- `claude-code/skills/agent-teams/*` references to `code-reviewer` / `security-auditor` as team roles: not examined for contract overrides.
