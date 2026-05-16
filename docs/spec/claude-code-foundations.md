# Claude Code foundations

What ships with Claude Code out of the box vs what AA-MA adds on top.

---

## Claude Code: what ships out of the box

### Built-in tools (26)

| Category | Tools |
|----------|-------|
| File and content | Read, Write, Edit, Glob, Grep |
| Execution | Bash, PowerShell, Agent |
| Code | LSP, ToolSearch |
| Web | WebSearch, WebFetch, ReadMcpResourceTool, ListMcpResourcesTool |
| User interaction | AskUserQuestion, SendMessage, TodoWrite |
| Plan mode | EnterPlanMode, ExitPlanMode |
| Task management | TaskCreate, TaskGet, TaskList, TaskUpdate, TaskStop, TaskOutput |
| Scheduling | CronCreate, CronDelete, CronList |
| Teams and worktree | TeamCreate, TeamDelete, ExitWorktree, EnterWorktree |
| Skills | Skill |

### Extension mechanisms

| Mechanism | Description |
|-----------|-------------|
| CLAUDE.md | Project-scoped instruction files at multiple levels (system, project, user, local) |
| Memory system | Persistent cross-session memory via MEMORY.md files, auto-managed by Claude |
| Rules | `.claude/rules/` directory, auto-loaded contextual instruction files |
| Hooks | Event-driven automation (25+ events including SessionStart, UserPromptSubmit, PreToolUse, PostToolUse, PreCompact, PostCompact, TaskCreated, TaskCompleted, SubagentStart, etc.) |
| Skills | Reusable prompt-based workflows invoked via the Skill() tool |
| Agents | Custom subagent definitions spawned via the Agent tool |
| Commands | Custom slash commands in `~/.claude/commands/` |
| MCP servers | External tool and resource integrations via Model Context Protocol |
| Plugins | Packaged extensions providing skills + agents + commands + hooks |

### Built-in features

- Auto-compaction with configurable threshold
- Git integration and worktree support
- Plan mode (design-before-implementation)
- Task tracking (6 tools)
- Permission system (allow/deny lists, tool-level control)
- Session management with hooks
- Web search and URL fetching

---

## AA-MA: what this project adds

### File taxonomy (5 standard + 2 optional)

| File | Purpose |
|------|---------|
| `[task]-plan.md` | Strategy, rationale, constraints |
| `[task]-reference.md` | Immutable facts (APIs, paths, constants) |
| `[task]-context-log.md` | Decision history, gate approvals |
| `[task]-tasks.md` | HTP execution roadmap, dependencies, state tracking |
| `[task]-provenance.log` | Execution telemetry, commit history |
| `[task]-verification.md` | Adversarial verification audit (optional) |
| `[task]-tests.yaml` | Machine-executable test definitions (optional) |

**Task directory structure:**

| Path | Contents |
|------|----------|
| `.claude/dev/active/[task-name]/` | Active tasks |
| `.claude/dev/completed/` | Archived completed tasks |

### Commands (10)

| Command | Purpose |
|---------|---------|
| `/aa-ma-plan` | Create detailed AA-MA plan with 12 mandatory outputs |
| `/execute-aa-ma-milestone` | Execute milestone with HITL/AFK mode dispatch and validation |
| `/execute-aa-ma-full` | Execute complete plan from current position |
| `/execute-aa-ma-step` | Execute single task with lightweight validation |
| `/verify-plan` | Adversarial 6-angle verification |
| `/grill-me` | Relentlessly interview about plans/designs until decisions are resolved |
| `/ops-mode` | Activate full operational constraints for disciplined execution |
| `/archive-aa-ma` | Archive completed tasks to `dev/completed/` |
| `/aa-ma-search` | Keyword search across active and completed AA-MA task files |
| `/understand-codebase` | Onboard to a new/inherited/shared codebase — produces `ONBOARDING.md` + `.claude/onboarding/` deep-dives (tiered Quick/Standard/Deep); optionally authors/reviews `AGENTS.md`. Thin wrapper around `Skill(understand-codebase)`; see ADR-0006 |

### Skills (19)

| Skill | Purpose |
|-------|---------|
| `aa-ma-plan-workflow` | 5-phase planning workflow: context → brainstorm → research → plan → artifacts |
| `aa-ma-execution` | Orchestrates AA-MA execution, auto-detects active tasks, handles context injection |
| `plan-verification` | 6-angle adversarial plan verification (invoked by `/verify-plan` and `/aa-ma-plan`) |
| `impact-analysis` | Pre-commit dependency and blast-radius analysis at milestone boundaries |
| `system-mapping` | 5-point pre-flight check before modifying unfamiliar code |
| `operational-constraints` | Disciplined execution mode: token compression, parallel eval, tool hierarchy |
| `token-compression` | Output token reduction with HITL/AFK intensity mapping (lite/full/ultra) |
| `retro` | Weekly engineering retrospective (invoked by `/archive-aa-ma`) |
| `complexity-router` | Weighted complexity scoring that routes high-risk tasks to deeper review |
| `agent-teams` | Multi-agent team orchestration with roles, debate, and shutdown protocols |
| `defense-in-depth` | Four-layer validation pattern for making bugs structurally impossible |
| `dispatching-parallel-agents` | Pattern for concurrent independent agent investigations |
| `debugging-strategies` | Systematic debugging process with multi-language tooling |
| `grill-with-docs` | Glossary-aware grilling: challenges plans against `CONTEXT.md` / ADRs, sharpens terminology, updates docs inline (forked from mattpocock/skills, invoked by /aa-ma-plan Phase 1.3 when project state warrants) |
| `prototype` | Throwaway-prototype dispatcher: routes between LOGIC (terminal TUI for state/business-logic questions, cross-language) and UI (web-frontend variants on a single route, switchable via `?variant=`) branches based on the question (forked from mattpocock/skills; operationalises engineering-standards Theme 1 `Prototype-Required: YES` flag — see ADR-0003) |
| `write-a-skill` | Canonical skill-authoring procedure: gather requirements → draft SKILL.md → review with user; includes 1024-char description format, "Use when" trigger pattern, 100-line SKILL.md guidance, when-to-split-files heuristics (forked from mattpocock/skills — see ADR-0004) |
| `verify-impl` | Post-impl adversarial review symmetric to `/verify-plan`: dispatches up to 5 parallel audit agents per the milestone's plan-declared `Audit-Profile`; CRITICAL findings surface via an accept/dispute/defer panel before §7.3 authorization (invoked by Phase 6.8 of `/execute-aa-ma-milestone` — see ADR-0005) |
| `understand-codebase` | Tiered (Quick/Standard/Deep) codebase-onboarding workflow: reads/maps the repo, learns conventions/versioning/tests/stack/rules, produces a pros/cons verdict + "contribute safely" + "add a feature" playbooks → `ONBOARDING.md` + `.claude/onboarding/` deep-dives; Deep tier runs a `TeamCreate` agent-team; optionally authors/reviews `AGENTS.md` (see ADR-0006) |
| `goal-condition-synthesis` | Synthesize a Claude Code `/goal` condition (v2.1.139+) from AA-MA plan artifacts: produces a falsifiable condition referencing observable artifacts (`provenance.log`, `tasks.md` Status, git tags, test exit codes) with a turn-cap cost ceiling derived from plan effort. Consumed by `/execute-aa-ma-full` §2.5 and `/verify-plan --iterate`; rejects vague conditions at construction time |

### Agents (11)

| Agent | Purpose |
|-------|---------|
| `aa-ma-scribe` | Generates the 5-file artifact set from an approved plan |
| `aa-ma-validator` | Read-only validation of artifact completeness and cross-file consistency |
| `code-reviewer` | Read-only fresh-eyes review of the milestone-window diff (KISS/SOLID/SOC/DRY, scope discipline, mechanism duplication, schema-breaking output regressions, dead code, magic numbers); CRITICAL → blocks user approval. Spawned by Phase 6.8 via `verify-impl` |
| `security-auditor` | Read-only analytical security audit of the milestone diff — the reasoning layer complementing the mechanical `security-static-check.sh` hook. Spawned by Phase 6.8 via `verify-impl` |
| `tdd-sequence-auditor` | Verifies the red→green→refactor sequencing of the milestone's commits; emits PASS/FAIL/WAIVED verdicts (honours plan-declared `TDD-Waiver`). Spawned by Phase 6.8 via `verify-impl` |
| `context7-evidence-auditor` | Checks that external-library usage introduced/changed in the milestone is backed by current docs evidence (scoped to MAJOR version bumps; capped at WARNING severity). Spawned by Phase 6.8 via `verify-impl` |
| `future-proofing-auditor` | Flags forward-looking risks: hardcoded counts (Tier-6 doc-drift surface), TODO/FIXME debt, brittle assumptions, deprecation exposure. Spawned by Phase 6.8 via `verify-impl` |
| `codebase-onboarding-conventions` | Worker agent for `understand-codebase` (Deep tier; reusable standalone): code conventions validated against source, versioning/release/git workflow, all rules/agent-instruction files, domain glossary → writes `.claude/onboarding/06-conventions-versioning-git.md` + `07-rules-and-agent-instructions.md` |
| `codebase-onboarding-health` | Worker agent for `understand-codebase` (Deep tier; reusable standalone): repo-health snapshot + pros/cons evidence — churn hotspots, contributors/bus-factor, ownership, doc drift, TODO/FIXME backlog, dependency health, coverage gaps, "here be dragons", security-posture signal (optional WebSearch CVE/version-currency pass) → writes `.claude/onboarding/09-repo-health-and-verdict.md` |
| `codebase-onboarding-runbook` | Worker agent for `understand-codebase` (Deep tier; reusable standalone): how the repo is built/run/debugged/tested locally, CI gates, env & config (names only — no secrets), external integrations, observability, data model & migrations → writes `.claude/onboarding/04-build-run-debug.md`, `05-tests-ci.md`, `08-integrations-observability-security.md` |
| `codebase-onboarding-synthesizer` | Synthesis agent for `understand-codebase` (Deep tier; reusable standalone): reads every per-dimension deep-dive + absorbed prior artifacts → writes the root `ONBOARDING.md`, `00-index.md`, the structural deep-dives (01-stack/02-architecture/03-structure), the pros/cons verdict, both playbooks, glossary, Provenance; handles the `AGENTS.md` decision (consent-gated; never overwrites an existing `AGENTS.md` or `CLAUDE.md`) |

### Rules (2)

| Rule | Purpose |
|------|---------|
| `aa-ma.md` | Operational rules governing sync discipline, commit signatures, task modes, gate classification |
| `engineering-standards.md` | 6-theme engineering doctrine (Verification & Truth, Development Principles, Reasoning & Planning, Safety & Continuity, Execution Checklist, Sync & Commit Discipline) — auto-loaded; defines `Critical-Path:` canonical enum |

### Hooks (8)

| Hook | Purpose |
|------|---------|
| `pre-compact-aa-ma.sh` | Snapshots AA-MA state before auto-compaction and writes compaction entries to task provenance.log and context-log.md |
| `aa-ma-session-start.sh` | Auto-detects active AA-MA tasks on session start and emits hidden context (task name, milestone, step) |
| `aa-ma-session-end-dirty.sh` | SessionEnd — warns when the session ends with uncommitted changes while an AA-MA plan is active |
| `aa-ma-commit-signature.sh` | PreToolUse(Bash) — when an AA-MA plan is active, requires every `git commit` to carry the `[AA-MA Plan] {task} .claude/dev/active/{task}` footer (or an `[ad-hoc]` bypass marker); **BLOCKING** |
| `aa-ma-commit-drift.sh` | post-commit — advisory; flags commits that land without touching any `tasks.md`/`provenance.log` in an active task dir (`[no-sync-check]` overrides). Always exits 0 |
| `aa-ma-plan-skip-warn.sh` | PreToolUse(ExitPlanMode) + SessionEnd — advisory; checks the `/aa-ma-plan` runtime log for skipped phase markers. Never blocks |
| `aa-ma-plan-marker.sh` | Library helper invoked by the `/aa-ma-plan` workflow to append phase markers to `~/.claude/runtime/aa-ma-plan-<slug>.log` (not a standalone event hook) |
| `security-static-check.sh` | PreToolUse — mechanical, zero-token commit-time security checks (bandit / shellcheck class), mirroring the `aa-ma-commit-drift.sh` / `aa-ma-validator` mechanical-vs-analytical split; introduced v0.8.0 per ADR-0005; **BLOCKING** on findings |

### Operational protocols

- **Sync discipline** -- mark complete, extract facts, document decisions, commit+push after every task
- **Planning standard** -- 12 mandatory outputs per plan
- **Commit signatures** -- `[AA-MA Plan] {task-name} .claude/dev/active/{task-name}`
- **HITL/AFK task execution modes** -- human-in-the-loop vs autonomous dispatch per task
- **HARD/SOFT milestone gate classification** -- artifact-enforced vs convention-based approval gates
- **Session checkpoints** -- recovery snapshots written to provenance.log before compaction or session end
- **Sub-step Result Log requirement** -- mandatory evidence logging after each sub-step regardless of executor

---

## How they fit together

Claude Code provides the building blocks: file operations, shell execution, subagent dispatch, hook events, skill invocation, and session management. These are general-purpose tools with no opinion about how work is organized.

AA-MA uses those building blocks to impose a structured memory architecture for long-horizon tasks. It defines what files exist, what goes in them, when they get updated, and how progress is tracked across sessions. The commands, skill, agents, rules, and hooks are all implemented on top of Claude Code's native extension mechanisms.

| Layer | Provides | Example |
|-------|----------|---------|
| Claude Code | Tools, extension points, runtime | Bash, Agent, Skill(), hooks, CLAUDE.md |
| AA-MA | Architecture, discipline, memory | 5-file taxonomy, sync discipline, planning standard, gate enforcement |
