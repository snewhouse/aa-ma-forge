# post-impl-adversarial-review Tasks (HTP)

_Hierarchical Task Planning roadmap with dependencies and state tracking._

## Milestone 1: ADR-0005 + Spec Doc Update

- Status: PENDING
- **Dependencies:** None
- **Complexity:** 30%
- **Gate:** SOFT
- **Mode:** HITL
- **Audit-Profile:** docs-only
- **Critical-Path:** doc-count-drift
- **Baseline:** N/A — pure local code, no API exercised
- **Acceptance Criteria:**
  - `docs/adr/0005-post-impl-adversarial-review.md` exists, follows TEMPLATE.md structure, references ADR-0001 (engineering-standards-architecture)
  - `docs/adr/INDEX.md` lists ADR-0005
  - `docs/spec/aa-ma-specification.md` gains §6.8 Post-Impl Adversarial Review subsection with file:line references to where Phase 6.8 will live
  - Cutover rule documented: "Plans with `Created: < v0.8.0-release-date` are grandfathered; §6.8 does not fire"

### Step 1.1: Draft ADR-0005 from TEMPLATE.md
- Status: PENDING
- **Mode:** HITL
- **Dependencies:** None
- **Effort:** 1h
- **Complexity:** 30%
- **Acceptance:** ADR-0005 exists; covers Context, Decision, Consequences, Alternatives Considered (mirror ADR-0001 structure)
- **Artefacts:** `docs/adr/0005-post-impl-adversarial-review.md`
- **Result Log:**

### Step 1.2: Update INDEX.md
- Status: PENDING
- **Mode:** HITL
- **Dependencies:** Step 1.1
- **Effort:** 15min
- **Complexity:** 10%
- **Acceptance:** INDEX.md lists ADR-0005 with one-line summary
- **Artefacts:** `docs/adr/INDEX.md`
- **Result Log:**

### Step 1.3: Add §6.8 anatomy to aa-ma-specification.md
- Status: PENDING
- **Mode:** HITL
- **Dependencies:** Step 1.1
- **Effort:** 45min
- **Complexity:** 40%
- **Acceptance:** New `### 6.8 Post-Impl Adversarial Review` subsection documents trigger, 5 agents, severity matrix, override panel, escape valves
- **Artefacts:** `docs/spec/aa-ma-specification.md`
- **Result Log:**

---

## Milestone 2: `security-static-check.sh` Pre-Commit Hook (TDD-first)

- Status: PENDING
- **Dependencies:** Milestone 1
- **Complexity:** 60%
- **Gate:** HARD
- **Mode:** AFK
- **Audit-Profile:** code-only
- **Critical-Path:** hook-modification
- **Baseline:** N/A — pure local code, no API exercised
- **Acceptance Criteria:**
  - `claude-code/hooks/security-static-check.sh` exists, executable, shellcheck-clean
  - Detects 5 pattern classes: hardcoded secrets, shell-injection idioms, path-traversal, SQL string concatenation, unsafe binary deserialisation idioms (CWE-502)
  - Bypassable via `AA_MA_HOOKS_DISABLE=1` and `[security-bypass: reason]` marker (auditable)
  - Bats test suite covers: each pattern detected, each bypass mechanism, no-pattern → exit 0
  - `scripts/install.sh` adds the hook to symlink list (verified via `--dry-run` grep)

### Step 2.1: Write bats tests FIRST (red)
- Status: PENDING
- **Mode:** AFK
- **Dependencies:** None
- **Effort:** 1.5h
- **Complexity:** 50%
- **Acceptance:** Bats file with 10+ test cases, all currently failing (no hook exists)
- **Artefacts:** `tests/hooks/security_static_check.bats`
- **Result Log:**

### Step 2.2: Implement hook to pass each test (green)
- Status: PENDING
- **Mode:** AFK
- **Dependencies:** Step 2.1
- **Effort:** 2h
- **Complexity:** 60%
- **Acceptance:** All bats tests pass; shellcheck clean
- **Artefacts:** `claude-code/hooks/security-static-check.sh`
- **Result Log:**

### Step 2.3: Register hook in `scripts/install.sh`
- Status: PENDING
- **Mode:** AFK
- **Dependencies:** Step 2.2
- **Effort:** 30min
- **Complexity:** 30%
- **Acceptance:** `scripts/install.sh --dry-run | grep security-static-check.sh` returns the new symlink line
- **Artefacts:** `scripts/install.sh`
- **Result Log:**

---

## Milestone 3: `Audit-Profile` + `TDD-Waiver` Parsers in plan-verification (TDD-first)

- Status: PENDING
- **Dependencies:** Milestone 1
- **Complexity:** 70%
- **Gate:** HARD
- **Mode:** AFK
- **Audit-Profile:** code-only
- **Baseline:** N/A — pure local code, no API exercised
- **Acceptance Criteria:**
  - plan-verification structural check fails when a v0.8.0-or-later plan milestone lacks `Audit-Profile:` field
  - plan-verification rejects non-canonical `TDD-Waiver:` values (e.g., `TDD-Waiver: idk`)
  - Grandfathering: plans with `Created:` < v0.8.0 release date pass without `Audit-Profile`
  - pytest cases cover: missing field, valid field, invalid field, grandfathered absence
  - `Skill(plan-verification)` SKILL.md Angle 6 documents the new checks

### Step 3.1: Write pytest cases FIRST (red)
- Status: PENDING
- **Mode:** AFK
- **Dependencies:** None
- **Effort:** 1.5h
- **Complexity:** 50%
- **Acceptance:** 15+ test cases across both parsers, all currently failing
- **Artefacts:** `tests/codemem/test_audit_profile_parser.py`, `tests/codemem/test_tdd_waiver_parser.py`
- **Result Log:**

### Step 3.2: Implement parsers (green)
- Status: PENDING
- **Mode:** AFK
- **Dependencies:** Step 3.1
- **Effort:** 2h
- **Complexity:** 70%
- **Acceptance:** All pytest cases pass; ruff clean
- **Artefacts:** `src/aa_ma/plan_parsers.py`
- **Result Log:**

### Step 3.3: Wire parsers into plan-verification Angle 6
- Status: PENDING
- **Mode:** AFK
- **Dependencies:** Step 3.2
- **Effort:** 1h
- **Complexity:** 50%
- **Acceptance:** `Skill(plan-verification)` Angle 6 SKILL.md documents the new structural checks; integration test verifies they fire on synthetic non-canonical inputs
- **Artefacts:** `claude-code/skills/plan-verification/SKILL.md`
- **Result Log:**

### Step 3.4: Corpus-test against existing completed plans
- Status: PENDING
- **Mode:** AFK
- **Dependencies:** Step 3.3
- **Effort:** 30min
- **Complexity:** 40%
- **Acceptance:** Running parser against every `.claude/dev/completed/*/*-tasks.md` produces zero false-positive failures (grandfathered)
- **Artefacts:** `tests/codemem/test_corpus_grandfathering.py`
- **Result Log:**

---

## Milestone 4: `/verify-impl` Skill + 5 Agent Prompts

- Status: PENDING
- **Dependencies:** Milestones 1, 3
- **Complexity:** 80% ⚠️ HIGH COMPLEXITY
- **Gate:** HARD
- **Mode:** HITL
- **Audit-Profile:** full
- **Prototype-Required:** YES
- **Critical-Path:** (none — agent prompts have no external API or version-pipeline impact)
- **Baseline:** N/A — pure local code, no API exercised
- **Acceptance Criteria:**
  - `claude-code/skills/verify-impl/SKILL.md` exists, follows Skill format, documents the 5-agent dispatch
  - 5 agent files exist in `claude-code/agents/`: `code-reviewer.md`, `security-auditor.md`, `tdd-sequence-auditor.md`, `context7-evidence-auditor.md`, `future-proofing-auditor.md`
  - Each agent prompt is documented with: trigger conditions, scope, severity classification rules, expected output schema (CRITICAL/WARNING/INFO with file:line + impact + fix)
  - Prototype validation: feed synthetic milestone diff to each agent in isolation; verify it catches L-005, L-006, L-007 historical examples
  - `[task]-impl-review.md` template exists in `docs/templates/`

### Step 4.1: Build minimal prototype of `verify-impl` skill (`Skill(prototype)` — LOGIC branch)
- Status: PENDING
- **Mode:** HITL
- **Dependencies:** None
- **Prototype-Required:** YES
- **Effort:** 1h
- **Complexity:** 60%
- **Acceptance:** Skeleton skill that dispatches a single test agent and returns structured output
- **Artefacts:** `claude-code/skills/verify-impl/SKILL.md` (initial draft)
- **Result Log:**

### Step 4.2: Prototype each agent prompt iteratively
- Status: PENDING
- **Mode:** HITL
- **Dependencies:** Step 4.1
- **Prototype-Required:** YES
- **Effort:** 3h
- **Complexity:** 80% ⚠️ HIGH COMPLEXITY
- **Acceptance:** Each of 5 agents catches its target lesson example (L-005, L-006, L-007); false-positive count documented in `[task]-context-log.md`
- **Artefacts:** 5 agent prompt files in `claude-code/agents/`
- **Result Log:**

### Step 4.3: Write impl-review template
- Status: PENDING
- **Mode:** HITL
- **Dependencies:** Step 4.2
- **Effort:** 1h
- **Complexity:** 40%
- **Acceptance:** Template covers all 5 agent output sections, severity table, override panel record
- **Artefacts:** `docs/templates/impl-review-template.md`
- **Result Log:**

### Step 4.4: Finalize skill SKILL.md with prototype findings
- Status: PENDING
- **Mode:** HITL
- **Dependencies:** Step 4.3
- **Effort:** 1h
- **Complexity:** 50%
- **Acceptance:** SKILL.md cites prototype evidence, documents budget modes, escape valves; provenance.log has `[ts] PROTOTYPE — verify-impl-skill — <verdict>`
- **Artefacts:** `claude-code/skills/verify-impl/SKILL.md`
- **Result Log:**

---

## Milestone 5: §6.8 Integration into `/execute-aa-ma-milestone` + Delegation in `/execute-aa-ma-full`

- Status: PENDING
- **Dependencies:** Milestones 2, 3, 4
- **Complexity:** 80% ⚠️ HIGH COMPLEXITY
- **Gate:** HARD
- **Mode:** HITL
- **Audit-Profile:** full
- **Critical-Path:** doc-count-drift
- **Baseline:** N/A — pure local code, no API exercised
- **Acceptance Criteria:**
  - `execute-aa-ma-milestone.md` gains §6.8 between current §6.7 (line 481) and §7.1 (line 559)
  - §6.8 invokes `/verify-impl` skill with the current milestone's `Audit-Profile`
  - CRITICAL findings from any agent surface via `AskUserQuestion` (accept/dispute/defer) BEFORE §7.3 user authorization
  - `execute-aa-ma-full.md` delegates §6.8 invocation to milestone command
  - `AA_MA_AUDIT_BUDGET={low,off}` env var honored
  - Grandfathering: plans with `Created:` < cutover skip §6.8 entirely (logged to provenance.log)
  - E2E bats test: synthetic milestone with `Audit-Profile: full` triggers §6.8; with `Audit-Profile: docs-only` triggers only future-proofing agent

### Step 5.1: Draft §6.8 section in `execute-aa-ma-milestone.md`
- Status: PENDING
- **Mode:** HITL
- **Dependencies:** None
- **Effort:** 2h
- **Complexity:** 70%
- **Acceptance:** §6.8 inserted between §6.7 and §7.1; references `/verify-impl` skill; documents Audit-Profile dispatch logic
- **Artefacts:** `claude-code/commands/execute-aa-ma-milestone.md`
- **Result Log:**

### Step 5.2: Wire CRITICAL override panel via `AskUserQuestion`
- Status: PENDING
- **Mode:** HITL
- **Dependencies:** Step 5.1
- **Effort:** 1.5h
- **Complexity:** 70%
- **Acceptance:** §6.8 documents accept/dispute/defer panel; defer creates new sub-task in `tasks.md`; dispute logged to `impl-review.md`
- **Artefacts:** `claude-code/commands/execute-aa-ma-milestone.md`
- **Result Log:**

### Step 5.3: Delegate from `execute-aa-ma-full.md`
- Status: PENDING
- **Mode:** HITL
- **Dependencies:** Step 5.2
- **Effort:** 30min
- **Complexity:** 40%
- **Acceptance:** Full command's per-milestone loop invokes §6.8 via delegation; no logic duplication
- **Artefacts:** `claude-code/commands/execute-aa-ma-full.md`
- **Result Log:**

### Step 5.4: E2E bats tests
- Status: PENDING
- **Mode:** HITL
- **Dependencies:** Step 5.3
- **Critical-Path:** doc-count-drift
- **Effort:** 2h
- **Complexity:** 70%
- **Acceptance:** All 4 trigger scenarios pass (full, docs-only, grandfathered, budget=off)
- **Artefacts:** `tests/hooks/execute_aa_ma_milestone_phase_6_8.bats`
- **Result Log:**

---

## Milestone 6: Version Bump v0.7.0 → v0.8.0 + README/CHANGELOG Sweep

- Status: PENDING
- **Dependencies:** Milestones 1, 2, 3, 4, 5
- **Complexity:** 50%
- **Gate:** HARD
- **Mode:** HITL
- **Audit-Profile:** infra
- **Critical-Path:** version-pipeline, doc-count-drift
- **Baseline:** N/A — pure local code, no API exercised
- **Acceptance Criteria:**
  - `pyproject.toml` version 0.7.0 → 0.8.0 via `cz bump` (NOT manual edit per L-003)
  - CHANGELOG.md regenerated by `cz bump`; post-bump manual read per L-006 confirms prose preserved (amend if not)
  - README.md skill count updated; doc-count-drift sweep across `docs/spec/claude-code-foundations.md`, `docs/spec/aa-ma-quick-reference.md`, `SECURITY.md` confirms no stale counts
  - `scripts/install.sh --dry-run | grep security-static-check.sh` returns the new symlink line
  - Git tag `v0.8.0` pushed; release notes include §6.8 anatomy reference
  - L-006 post-bump verification protocol followed: read CHANGELOG before `git push --tags`

### Step 6.1: Hardcoded-count sweep across docs
- Status: PENDING
- **Mode:** HITL
- **Dependencies:** None
- **Critical-Path:** doc-count-drift
- **Effort:** 45min
- **Complexity:** 40%
- **Acceptance:** All stale counts replaced; verified via grep for old counts
- **Artefacts:** README.md, foundations.md, quick-reference.md, SECURITY.md
- **Result Log:**

### Step 6.2: Run `cz bump`
- Status: PENDING
- **Mode:** HITL
- **Dependencies:** Step 6.1
- **Critical-Path:** version-pipeline
- **Effort:** 30min
- **Complexity:** 40%
- **Acceptance:** version 0.8.0; new git tag; CHANGELOG entry generated
- **Artefacts:** pyproject.toml, CHANGELOG.md, .git/refs/tags/v0.8.0
- **Result Log:**

### Step 6.3: Post-bump CHANGELOG verification (L-006 protocol)
- Status: PENDING
- **Mode:** HITL
- **Dependencies:** Step 6.2
- **Critical-Path:** version-pipeline
- **Effort:** 30min
- **Complexity:** 50%
- **Acceptance:** CHANGELOG v0.8.0 entry has prose; if stripped, amend + retag BEFORE pushing
- **Artefacts:** CHANGELOG.md (amended if needed)
- **Result Log:**

### Step 6.4: Install dry-run verification
- Status: PENDING
- **Mode:** HITL
- **Dependencies:** Step 6.3
- **Effort:** 15min
- **Complexity:** 20%
- **Acceptance:** `--dry-run` output shows symlinks for security-static-check.sh, verify-impl/, all 5 agents, impl-review-template.md
- **Artefacts:** (verification only)
- **Result Log:**

### Step 6.5: Push tag + release notes
- Status: PENDING
- **Mode:** HITL
- **Dependencies:** Step 6.4
- **Critical-Path:** version-pipeline
- **Effort:** 30min
- **Complexity:** 30%
- **Acceptance:** `git push origin v0.8.0` succeeds; GitHub/GitLab release notes link to ADR-0005
- **Artefacts:** (release-only; no file changes)
- **Result Log:**
