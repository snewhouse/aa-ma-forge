<!-- ARCHIVED: 2026-05-11 22:20 -->
<!-- Plan: post-impl-adversarial-review - COMPLETE -->
<!-- Total Milestones: 6 (21 sub-tasks: 21 COMPLETE) | Duration: 2026-05-11 12:00 to 2026-05-11 22:10 (~10h) -->

# post-impl-adversarial-review Context Log

---

## [2026-05-11] Plan Approved

- Plan: post-impl-adversarial-review
- Approved by: Stephen Newhouse (via ExitPlanMode)
- Milestones: 6
- HARD gates: Milestones 2, 3, 4, 5, 6 (Milestone 1 is SOFT)

---

## [2026-05-11] Initial Context

**Feature Request (Phase 1):**

User invoked `/grill-with-docs` to stress-test aa-ma-forge's plan-execution discipline. Stated concerns: code review, security review, simplification, missing tests, TDD/KISS/DRY/SOLID/SOC adherence, Context7 usage, future-proofing. The grilling traversed a 7-question decision tree (Q1–Q7b) and surfaced one structural asymmetry: pre-execution rigor is high (6-angle plan-verification + 9 HARD gates at milestone close), but post-execution review is thin — only one SOFT, skippable simplification review. Project's own lesson history (L-005 KISS violation, L-006 CHANGELOG regression, L-007 out-of-scope drift) confirms the gap bites.

**Key Decisions (Phase 2 Brainstorming — 8 grilled decisions from Q1–Q7b):**

- **Decision AD-001 (Branch 1 — Asymmetry):** Add Phase 6.8 *Post-Impl Adversarial Review* to `/execute-aa-ma-milestone` + new `/verify-impl` skill that dispatches 5 parallel audit agents. CRITICAL findings block §7.3 user approval.
  - **Rationale:** Mirrors the proven 6-angle plan-verification pattern but post-implementation. Symmetry between plan and impl verification reduces post-ship surprises of the L-006 class.
  - **Alternatives Considered:** (a) Strengthen the existing SOFT simplification review to HARD — rejected, single-axis review cannot cover code/security/TDD/Context7/future-proofing concerns; (b) Defer post-impl review to a separate `/audit` command run manually — rejected, optional steps drift to "never run"; (c) Bake into commit hooks only — rejected, hooks cannot do semantic review of 5+ files in concert.
  - **Trade-offs:** Adds 100-200k tokens per milestone close (mitigated by `Audit-Profile` scoping and `AA_MA_AUDIT_BUDGET=low` sequential mode); 5 new agent files to maintain (mitigated by prototype validation in M4).

- **Decision AD-002 (Branch 2 — Trigger):** Plan-declared `Audit-Profile` per milestone, with canonical enum `full | code-only | docs-only | infra | custom`.
  - **Rationale:** Different milestone classes need different audit scopes. Plan-author declares the profile up front; no per-milestone runtime negotiation. Mirrors how `Critical-Path:` and `Mode:` are plan-declared.
  - **Alternatives Considered:** (a) Auto-detect profile from `git diff` file types — rejected, brittle and surprises users; (b) Always run `full` — rejected, prohibitively expensive on docs-only milestones; (c) Per-step instead of per-milestone — rejected, granularity mismatch with how `/execute-aa-ma-milestone` finalizes.
  - **Trade-offs:** Adds one mandatory field to v0.8.0-plus plans (mitigated by grandfathering in Branch 6); requires plan-verification parser update (M3).

- **Decision AD-003 (Branch 3 — TDD strictness):** Strict commit-ordering check: first `tests/` commit must precede first `src/` commit within milestone window. Canonical `TDD-Waiver` enum (`refactor | docs-only | prototype | hotfix-emergency | tooling-config`); new values require plan + ADR.
  - **Rationale:** Falsifiable, mechanical, observable from git log. Canonical enum prevents waiver-fatigue and matches the `Critical-Path:` enum pattern already shipping.
  - **Alternatives Considered:** (a) Coverage-percentage threshold instead of ordering — rejected, gameable; (b) No enforcement, just advisory — rejected, no behaviour change vs current state; (c) Free-form `TDD-Waiver:` strings — rejected, value drift undermines structural verification.
  - **Trade-offs:** Mis-attributes milestone-window if commits lack `[AA-MA Plan]` footer (mitigated by existing commit-signature hook); requires engineering-standards.md update to add TDD-Waiver enum next to Critical-Path.

- **Decision AD-004 (Branch 4 — False-positive tolerance):** Severity-gated user override panel. Each agent emits CRITICAL/WARNING/INFO. CRITICAL → `AskUserQuestion` panel with accept/dispute/defer. WARNING/INFO logged, do not block.
  - **Rationale:** Removes "all-or-nothing" trap. Disputes are logged to `impl-review.md` for audit; defer creates a new follow-up sub-task in `tasks.md`. Uses the proven §7.3 `AskUserQuestion` pattern.
  - **Alternatives Considered:** (a) Block on any finding — rejected, false-positives stall execution; (b) Advisory-only (never block) — rejected, defeats the point; (c) Numeric "confidence score" threshold — rejected, opaque and untunable.
  - **Trade-offs:** Adds a HITL step at milestone close (already HITL-friendly via Gate: HARD on M5); dispute records require persistent storage (handled by `impl-review.md` artefact).

- **Decision AD-005 (Branch 5 — Budget):** `Audit-Profile` IS the budget — narrower profiles dispatch fewer agents. Global escape valve `AA_MA_AUDIT_BUDGET={low,off}`: `low` forces sequential dispatch (reduces peak tokens), `off` skips §6.8 entirely with bypass logged to `provenance.log`.
  - **Rationale:** Two-tier control: per-milestone (via plan) and global (via env var). Existing `AA_MA_HOOKS_DISABLE=1` master switch already covers emergencies.
  - **Alternatives Considered:** (a) Hard token cap per agent — rejected, breaks long agent outputs mid-stream; (b) Adaptive sampling — rejected, complexity not justified; (c) No budget controls — rejected, blocks adoption in token-constrained sessions.
  - **Trade-offs:** `AA_MA_AUDIT_BUDGET=off` is bypassable and could be abused (mitigated by always logging the bypass to provenance.log, auditable).

- **Decision AD-006 (Branch 6 — Backwards compat):** Grandfather by `Created:` date in plan front-matter. Plans authored before v0.8.0 release date skip §6.8 entirely.
  - **Rationale:** Mirrors the v0.5.0 precedent for Engineering Standards element #12 (plan-verification Angle 6 already implements this exact pattern). Non-breaking by construction — in-flight plans (this one included, `Created: 2026-05-11`) continue under v0.7.0 rules.
  - **Alternatives Considered:** (a) Cutover by plugin version number alone — rejected, conflates plan author intent with plugin version; (b) Cutover by tag commit — close, but cite "v0.8.0 release tag commit" in ADR for symmetry; (c) Opt-in via plan flag — rejected, defeats default-on safety.
  - **Trade-offs:** Plans without `Created:` front-matter (pre-v0.5.0) fall back to "absent → grandfathered" rule, still safe.

- **Decision AD-007 (Branch 7a — Security split):** Two-layer security. Mechanical patterns → `security-static-check.sh` pre-commit hook (commit-time, free, zero tokens). Semantic security review → `security-auditor` agent (milestone close).
  - **Rationale:** Separation of Concerns — mechanical patterns (hardcoded secrets, shell injection, path traversal, SQL concat, unsafe deserialisation) are cheap regex-class checks; semantic review (auth flow correctness, privilege escalation paths) needs LLM context. KISS: don't make the agent do regex-class work.
  - **Alternatives Considered:** (a) One agent does everything — rejected, mixes cheap and expensive checks; (b) Hook only — rejected, no semantic coverage; (c) Agent only — rejected, expensive on every commit; (d) `bandit`-style external tool — rejected, drags Python tooling into shell-script-heavy plugin.
  - **Trade-offs:** Hook adds one more file to `claude-code/hooks/`; need bypass marker `[security-bypass: <reason>]` for legitimate exceptions (auditable).

- **Decision AD-008 (Branch 7b — Context7 scope):** `context7-evidence-auditor` scope narrowed to NEW dependencies + MAJOR version bumps only. Minor/patch bumps skipped.
  - **Rationale:** uv.lock churn under minor/patch bumps is high-volume and low-signal. Context7 evidence pays off where breaking changes are plausible. Aligns with L-001 (external URL first principle for named external libraries).
  - **Alternatives Considered:** (a) Check every dependency change — rejected, uv.lock noise dominates; (b) Check only on `pyproject.toml` `dependencies` edits — close, but misses uv.lock-only major bumps; (c) Never check — rejected, defeats the auditor's purpose.
  - **Trade-offs:** Misses occasional regression in minor bumps (mitigated by general code-reviewer's "schema-breaking output" check + L-006 post-bump verification).

**Research Findings (Phase 3 — pre-flight verification from grilling session):**

- Current version is 0.7.0 (`grep ^version pyproject.toml`)
- Next ADR number is 0005 (`ls docs/adr/` shows 0001-0004)
- `verify-impl` skill name available (no existing `*verify*impl*` files)
- `security-static-check.sh` hook name available (no existing `*security*` hook files)
- Phase numbering §6.8 is free: `execute-aa-ma-milestone.md` §6.7 ends at line 481, §7.1 starts at line 559
- All 8 templates exist in `docs/templates/` (plan, tasks, reference, context-log, provenance, verification, tests, engineering-standards)
- `Created:` front-matter pattern confirmed in `.claude/dev/completed/harden-aa-ma-plan/harden-aa-ma-plan-plan.md`
- L-001 through L-007 all present in `docs/lessons.md`
- `.claude/dev/active/` was empty (no active-task conflicts)
- Existing agents in `claude-code/agents/`: only `aa-ma-scribe` and `aa-ma-validator`

**Remaining Questions / Unresolved Issues:**

None. All 8 branches grilled and resolved. Plan is execution-ready upon approval.

---

## [2026-05-11] Plan Approval Confirmation

Plan approved via ExitPlanMode 2026-05-11; aa-ma-scribe dispatched to populate 5 artifact files. Implementation may proceed against Milestone 1 (ADR-0005 + Spec Doc Update).
