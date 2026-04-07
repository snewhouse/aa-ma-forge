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

### Commands (8)

| Command | Purpose |
|---------|---------|
| `/aa-ma-plan` | Create detailed AA-MA plan with 11 mandatory outputs |
| `/execute-aa-ma-milestone` | Execute milestone with HITL/AFK mode dispatch and validation |
| `/execute-aa-ma-full` | Execute complete plan from current position |
| `/execute-aa-ma-step` | Execute single task with lightweight validation |
| `/verify-plan` | Adversarial 6-angle verification |
| `/grill-me` | Relentlessly interview about plans/designs until decisions are resolved |
| `/ops-mode` | Activate full operational constraints for disciplined execution |
| `/archive-aa-ma` | Archive completed tasks to `dev/completed/` |

### Skills (12)

| Skill | Purpose |
|-------|---------|
| `aa-ma-plan-workflow` | 5-phase planning workflow: context → brainstorm → research → plan → artifacts |
| `aa-ma-execution` | Orchestrates AA-MA execution, auto-detects active tasks, handles context injection |
| `plan-verification` | 6-angle adversarial plan verification (invoked by `/verify-plan` and `/aa-ma-plan`) |
| `impact-analysis` | Pre-commit dependency and blast-radius analysis at milestone boundaries |
| `system-mapping` | 5-point pre-flight check before modifying unfamiliar code |
| `operational-constraints` | Disciplined execution mode: token efficiency, parallel eval, tool hierarchy |
| `retro` | Weekly engineering retrospective (invoked by `/archive-aa-ma`) |
| `complexity-router` | Weighted complexity scoring that routes high-risk tasks to deeper review |
| `agent-teams` | Multi-agent team orchestration with roles, debate, and shutdown protocols |
| `defense-in-depth` | Four-layer validation pattern for making bugs structurally impossible |
| `dispatching-parallel-agents` | Pattern for concurrent independent agent investigations |
| `debugging-strategies` | Systematic debugging process with multi-language tooling |

### Agents (2)

| Agent | Purpose |
|-------|---------|
| `aa-ma-scribe` | Generates the 5-file artifact set from an approved plan |
| `aa-ma-validator` | Read-only validation of artifact completeness and cross-file consistency |

### Rules (1)

| Rule | Purpose |
|------|---------|
| `aa-ma.md` | Operational rules governing sync discipline, commit signatures, task modes, gate classification |

### Hooks (1)

| Hook | Purpose |
|------|---------|
| `pre-compact-aa-ma.sh` | Snapshots AA-MA state before auto-compaction to prevent context loss |

### Operational protocols

- **Sync discipline** -- mark complete, extract facts, document decisions, commit+push after every task
- **Planning standard** -- 11 mandatory outputs per plan
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
