# sole-dev-merge-pr-workflow Reference

Immutable facts and constants — load FIRST during execution.

_Last Updated: 2026-05-18_

## Identity

- **Task slug:** `sole-dev-merge-pr-workflow`
- **AA-MA marker slug:** `sole-dev-merge-ci-pr-20260518105415`
- **AA-MA Plan signature:** `[AA-MA Plan] sole-dev-merge-pr-workflow .claude/dev/active/sole-dev-merge-pr-workflow`
- **Plan version:** v2 (post-verification revision)

## Target paths

- **Repo root:** `/home/sjnewhouse/biorelate/projects/gitlab/github_private/aa-ma-forge`
- **New command file:** `claude-code/commands/sole-dev-merge.md`
- **Replaces (user-local, NOT in plugin git):** `~/.claude/commands/sole-dev-merge.md`
- **Tests directory:** `tests/commands/sole-dev-merge/`
- **ADR:** `docs/adr/0008-sole-dev-merge-pr-workflow.md`
- **Backup location (install.sh-created):** `~/.claude/backups/aa-ma-forge-<timestamp>/commands/sole-dev-merge.md`

## CLI versions (verified at plan time)

- `gh` v2.92.0 (2026-04-28) — `which gh` → `/usr/bin/gh`
- `glab` v1.80.4 (f4b518e9) — `which glab` → `/usr/bin/glab`

## Auth state (verified at plan time, snewhouse account)

- `gh auth status` → `Logged in to github.com account snewhouse`
- `glab auth status` → `Logged in to gitlab.com as stephen_newhouse`

## CLI command surface (verified syntax)

### GitHub (gh)

| Operation | Command |
|-----------|---------|
| Check existing PR | `gh pr view --json url 2>/dev/null` (idempotency pre-check) |
| Create PR | `gh pr create --title "$TITLE" --body-file "$BODY"` |
| Update PR body | `gh pr edit --body-file "$BODY"` |
| Poll CI checks | `gh pr checks <pr-num> --watch --interval 30 --fail-fast` (wrap in `timeout 900s`) |
| Get branch protection | `gh api "repos/{owner}/{repo}" --jq '.allow_rebase_merge'` |
| Merge (rebase) | `gh pr merge <pr-num> --rebase --delete-branch` |
| Merge (fallback) | `gh pr merge <pr-num> --merge --delete-branch` |
| Auto-merge (post-timeout recovery) | `gh pr merge <pr-num> --auto --rebase` |

**Exit codes:**
- `gh pr checks --watch`: `0` = green; `8` = pending (with `--watch`, shouldn't terminate); other = failure
- `timeout 900s`: returns `124` on SIGTERM (must translate to clean exit 0 + `STATUS: CI_TIMEOUT`)

### GitLab (glab)

| Operation | Command |
|-----------|---------|
| Check existing MR | `glab mr view 2>/dev/null` (idempotency pre-check) |
| Create MR | `glab mr create --title "$TITLE" --description "$(cat $BODY)"` |
| Update MR body | `glab mr update --description "$(cat $BODY)"` |
| Poll CI (JSON) | `glab api /projects/:id/merge_requests/<iid>` parsed via `--jq '.pipeline.status'` |
| Get merge method | `glab api "/projects/:id" --jq '.merge_method'` (expect `rebase_merge` or `merge` or `ff`) |
| Merge (rebase) | `glab mr merge <iid> --rebase --remove-source-branch --yes` |
| Merge (fallback) | `glab mr merge <iid> --remove-source-branch --yes` |

**WRONG SYNTAX TO NEVER USE (would fail at runtime):**
- ❌ `glab mr create --description-file "$BODY"` — flag does NOT exist
- ❌ `glab mr create --remove-source-branch=false` — boolean flag, no `=value`
- ❌ `glab ci status` for script-safe polling — TTY UI, no documented exit codes

**Pipeline status values from glab api:** `success` | `failed` | `canceled` | `running` | `pending` | `manual` | `skipped` | `created` | `preparing`

## Agent dispatch contract

### Code review agents (try in order, fall back if unavailable)

1. **Preferred:** `feature-dev:code-reviewer` (via Agent tool, `subagent_type: feature-dev:code-reviewer`)
2. **Fallback:** `code-reviewer` (via Agent tool, `subagent_type: code-reviewer`) — verified exists at `~/.claude/agents/code-reviewer.md`

### Security agent

- **Path:** `~/.claude/agents/security-auditor.md` (verified exists)
- **Dispatch:** Agent tool, `subagent_type: security-auditor`

### Severity output contract (passed in agent prompt)

Every dispatched review agent MUST be instructed to output findings in EXACTLY this format:

```
[CRITICAL] <one-line finding> — <path>:<line>
[HIGH]     <one-line finding> — <path>:<line>
[MEDIUM]   <one-line finding> — <path>:<line>
[LOW]      <one-line finding> — <path>:<line>
```

Parser regex: `^\[(CRITICAL|HIGH|MEDIUM|LOW)\]\s+(.+?)\s+—\s+(.+?):(\d+)$`

**Safe-default behaviour on parse failure:** classify ALL findings as `[HIGH]` (forces user review of everything; no auto-fix). Log parse failure to `provenance.log`.

### Output paths (absolute — required for `gh --body-file`)

- Code review (M2.1): `/tmp/sole-dev-merge-review-<slug>.md`
- Security agent (M2.2): `/tmp/sole-dev-merge-security-<slug>.md`
- Bandit JSON (M2.3): `/tmp/sole-dev-merge-bandit-<slug>.json`
- ShellCheck JSON (M2.4): `/tmp/sole-dev-merge-shellcheck-<slug>.json`
- Consolidated findings (M2.5): `/tmp/sole-dev-merge-findings-<slug>.md`
- AI PR/MR body (M3.3): `/tmp/sole-dev-merge-body-<slug>.md`
- AskUserQuestion args log (testing): `/tmp/sole-dev-merge-auq-<slug>.json`
- gh/glab call log (testing): `/tmp/sole-dev-merge-cli-calls-<slug>.log`

## Static analyzer severity mapping

### Bandit JSON → unified scheme

| Bandit `issue_severity` | Mapped to |
|------------------------|-----------|
| `HIGH` | `[CRITICAL]` |
| `MEDIUM` | `[HIGH]` |
| `LOW` | `[MEDIUM]` |
| (undefined) | `[LOW]` |

### ShellCheck JSON → unified scheme

| ShellCheck `level` | Mapped to |
|-------------------|-----------|
| `error` | `[CRITICAL]` |
| `warning` | `[HIGH]` |
| `info` | `[MEDIUM]` |
| `style` | `[LOW]` |

## Engineering Standards canonical values

### Critical-Path canonical values (from `claude-code/rules/engineering-standards.md`)

| Value | Used by milestone |
|-------|-------------------|
| `auth-flow` | (none in this plan) |
| `data-xform` | (none in this plan) |
| `external-api` | M3 |
| `version-pipeline` | M4 |
| `doc-count-drift` | M1, M5 |
| `hook-modification` | (none in this plan) |

### Audit-Profile canonical values (post-v0.8.0 requirement)

| Value | Used by milestone |
|-------|-------------------|
| `full` | M2, M3 |
| `code-only` | M1, M4 |
| `docs-only` | M5 |
| `infra` | (none in this plan) |
| `custom` | (none in this plan) |

## Test harness contracts (for falsifiability)

- **AskUserQuestion spy:** Each `AskUserQuestion` invocation MUST log to `$AUQ_LOG` (env var; defaults to `/tmp/sole-dev-merge-auq-<slug>.json`) as JSON line: `{"call": <n>, "n_options": <int>, "labels": [...], "default": "<label>"}`. Tests assert via `jq` over the file.
- **gh/glab call spy:** Tests use PATH-shadowed stubs at `tests/commands/sole-dev-merge/fixtures/bin/{gh,glab}` that `echo "$@" >> $CLI_LOG` then `exit 0`. Asserts via `grep -c` over the log.
- **Agent dispatch spy:** Tests use a `MOCK_AGENT_DISPATCH=1` env var; when set, the dispatch step writes the configured fixture file (e.g., `tests/commands/sole-dev-merge/fixtures/agent-output-bandit-critical.md`) to the expected `/tmp/...` output path and skips real Agent tool invocation.

## Critical doc-drift counts (must update atomically)

As of plan time (commit `c2bf40c`):

- `claude-code/commands/` count: **10** (becomes **11** with `sole-dev-merge.md`)
- `claude-code/skills/` count: **19** (stays **19** — no skill added)
- `claude-code/agents/` count: **11** (stays **11**)
- `claude-code/hooks/` count: **8** (stays **8**)
- `docs/spec/` templates count: **8** (stays **8**)

**Pre-existing drift to resolve in same commit (M5.4):**
- `CLAUDE.md:48-50` says "10 slash commands, 18 reusable procedures" — should be 10→11 (after add) and 18→19 (correcting pre-existing drift; SECURITY.md already says 19)
- `SECURITY.md:11-12` says "10 command files, 19 skills directories" — should be 10→11 (after add)

## Files touched by the plan (final list)

**CREATE (13):**
1. `claude-code/commands/sole-dev-merge.md`
2. `docs/adr/0008-sole-dev-merge-pr-workflow.md`
3. `tests/commands/sole-dev-merge/test_stage_a_preflight.bats`
4. `tests/commands/sole-dev-merge/test_stage_b_scope.bats`
5. `tests/commands/sole-dev-merge/test_stage_c_dispatch.bats`
6. `tests/commands/sole-dev-merge/test_stage_d_triage.bats`
7. `tests/commands/sole-dev-merge/test_stage_e_remote.bats`
8. `tests/commands/sole-dev-merge/test_stage_f_idempotent.bats`
9. `tests/commands/sole-dev-merge/test_stage_g_poll.bats`
10. `tests/commands/sole-dev-merge/test_stage_g_merge.bats`
11. `tests/commands/sole-dev-merge/test_smoke_e2e.bats`
12. `tests/commands/sole-dev-merge/fixtures/` (directory with planted-defect files + mock binaries)
13. (M5) `tests/commands/sole-dev-merge/fixtures/bin/{gh,glab}` (PATH-shadowing stubs)

**MODIFY (7):**
1. `README.md` (add `/sole-dev-merge` to command list)
2. `CHANGELOG.md` (`## Unreleased` header + entry)
3. `CLAUDE.md` (lines 48-50: counts to 11/19)
4. `SECURITY.md` (lines 11-12: counts to 11/19; name in inline list)
5. `docs/spec/aa-ma-quick-reference.md` (command row)
6. `docs/lessons.md` (annotate L-007 as resolved)
7. `.github/workflows/security.yml` (append bats step)

**DELETE / REPLACE (1):**
- `~/.claude/commands/sole-dev-merge.md` (auto-backed-up by install.sh)

**EXPLICITLY NOT MODIFIED (correcting v1):**
- `scripts/install.sh` — auto-discovery handles both new command and new skill (no edit required)
- `claude-code/skills/sole-dev-merge/` — entire directory dropped (no skill-with-lib pattern in repo precedent)
