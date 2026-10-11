# Post-impl adversarial review (§6.8) — when §6.8 fires, how Skill(verify-impl) dispatches the five audit agents (ADR-0005), verdicts, the CRITICAL override panel and bypasses.

## Contents

  - [6.8 Post-Impl Adversarial Review (NEW in v0.8.0)](#68-post-impl-adversarial-review-new-in-v080)

### 6.8 Post-Impl Adversarial Review (NEW in v0.8.0)

Reference: ADR-0005 ([`docs/adr/0005-post-impl-adversarial-review.md`](../../../../docs/adr/0005-post-impl-adversarial-review.md)) and Skill: `verify-impl`.

Symmetric to plan-verification (which runs adversarially BEFORE execution),
§6.8 dispatches up to 5 audit agents AFTER the milestone's implementation has
landed and §6.7 has passed. Goal: close the asymmetry where pre-execution rigor
was high (6-angle plan-verification + 9 HARD gates) but post-execution rigor
was thin (only SOFT §6.6 simplification review).

**Grandfathering — when §6.8 does NOT fire:**

```bash
# Read plan's Created: front-matter
PLAN_CREATED=$(grep -m1 "^\*\*Created:\*\*\|^Created:" \
  "${TASK_DIR}/${TASK_NAME}-plan.md" | grep -oE '[0-9]{4}-[0-9]{2}-[0-9]{2}')

# v0.8.0 release tag commit date (cutover for §6.8)
# Tag v0.8.0 → commit 695f7b7, authored 2026-05-11 17:05:15 +0100.
# Strict less-than: plans Created: < 2026-05-11 are grandfathered.
# The post-impl-adversarial-review meta-plan (Created: 2026-05-11) sits at
# the boundary — see ADR-0005 self-bootstrap note. Future plans will be
# Created: 2026-05-12 or later and thus subject to §6.8.
V080_CUTOVER="2026-05-11"

if [[ -z "${PLAN_CREATED}" ]] || [[ "${PLAN_CREATED}" < "${V080_CUTOVER}" ]]; then
  echo "[$(date -Iseconds)] §6.8 SKIPPED — pre-v0.8.0 plan (grandfathered)" \
    >> "${TASK_DIR}/${TASK_NAME}-provenance.log"
  exit 0  # exit this section, continue to §7
fi

# AA_MA_AUDIT_BUDGET=off explicit skip (auditable bypass)
if [[ "${AA_MA_AUDIT_BUDGET:-normal}" == "off" ]]; then
  echo "[$(date -Iseconds)] AUDIT_BUDGET=off — bypassed §6.8" \
    >> "${TASK_DIR}/${TASK_NAME}-provenance.log"
  exit 0
fi
```

**Dispatch logic:**

1. Read `Audit-Profile:` from the current milestone block using
   `src/aa_ma/plan_parsers.py::parse_audit_profile`. If missing → emit a
   CRITICAL finding from the structural check (plan-verification Angle 6 #4
   should have caught this earlier; defensive double-check here).
2. Resolve the milestone's commit window (`<base_sha>..<head_sha>`) — use the
   first commit with `[AA-MA Plan] <task-name>` footer touching this milestone's
   tasks.md block, OR fall back to `git rev-parse HEAD~N` heuristic if commit
   markers are missing.
3. Invoke the `verify-impl` skill: `Skill(verify-impl)` with parameters
   `--task <task-name> --milestone <milestone-id>`. The skill orchestrator
   handles per-Audit-Profile agent dispatch (full/code-only/docs-only/infra/
   custom) per the matrix in `claude-code/skills/verify-impl/SKILL.md`. The
   5 audit agents are:
   - **code-reviewer** — KISS/SOLID/SOC/DRY + 5 mandatory patterns
     (scope discipline → L-007, mechanism duplication → L-005,
     schema-breaking output → L-006, dead code, magic numbers)
   - **security-auditor** — semantic OWASP review (mechanical handled
     upstream by `security-static-check.sh` PreToolUse hook)
   - **tdd-sequence-auditor** — git-log forensics, PASS/FAIL/WAIVED verdict
     (waivable via canonical `TDD-Waiver` enum)
   - **context7-evidence-auditor** — new PyPI deps + MAJOR-version bumps
     only; WARNING-only ceiling
   - **future-proofing-auditor** — hardcoded counts (proactive Tier 6+),
     magic numbers, version pins, premature abstractions
4. Skill returns an aggregated verdict and writes `[task]-impl-review.md`.

**Verdict outcomes:**

| Verdict | Behaviour |
|---|---|
| `PASS` | Continue to §7.1 |
| `PASS_WITH_WARNINGS` | Continue to §7.1; warnings logged in impl-review.md |
| `BLOCKED` | At least one CRITICAL finding was `accept`-ed via override panel. Halt §6.8; surface remediation guidance to user; do NOT proceed to §7.1 until accepted CRITICALs are fixed and §6.8 re-runs clean. |

**CRITICAL findings — override panel:**

For each CRITICAL finding emitted by any of the 5 dispatched agents, the
orchestrator surfaces an `AskUserQuestion` panel before continuing:

```
[CRITICAL] <pattern>: <file:line> — impact: "<X>" — suggested fix: "<Y>"

Options:
  - accept   → block until fixed (BLOCKED verdict)
  - dispute  → false-positive; logged for next-run "convention learned"
  - defer    → create new sub-task in tasks.md; continue (with warning)
```

User decisions are recorded in `[task]-impl-review.md` under "User Override
Decisions". If ANY decision is `accept`, the verdict is BLOCKED and §6.8 halts
the milestone. Disputes accumulate across runs and are fed back to agent
prompts as "conventions learned for this project" — over time, false-positive
rate drops.

**Defer creates a new sub-task** in the current milestone (or a follow-up
milestone if specified):

```markdown
### Sub-step N.M: [DEFERRED from §6.8 impl review] <pattern> <file:line>
- Status: PENDING
- Mode: AFK
- Acceptance: Address the deferred CRITICAL finding from impl-review.md
- Source: [task]-impl-review.md User Override Decisions table row N
```

**Provenance entry (always emitted on completion):**

```
[<ISO>] §6.8 POST_IMPL_REVIEW — Audit-Profile: <profile> — \
        agents: <slate> — verdict: <PASS|BLOCKED|PASS_WITH_WARNINGS> — \
        findings: <N> CRITICAL / <M> WARNING / <P> INFO
```

**Bypass mechanisms (auditable):**

| Mechanism | Effect | Logged where |
|---|---|---|
| `AA_MA_HOOKS_DISABLE=1` | Master kill switch — skips ALL aa-ma gates incl. §6.8 | n/a (existing) |
| `AA_MA_AUDIT_BUDGET=off` | Skips §6.8 specifically | provenance.log: `AUDIT_BUDGET=off — bypassed §6.8` |
| `AA_MA_AUDIT_BUDGET=low` | Runs §6.8 in sequential/diff-only mode | provenance.log: `§6.8 invoked under AUDIT_BUDGET=low` |
| `TDD-Waiver: <canonical>` per milestone | Bypasses tdd-sequence-auditor only | impl-review.md (WAIVED verdict) |
| `[security-bypass: <reason>]` in commit msg | Bypasses upstream security-static-check.sh hook; semantic security-auditor agent still runs | commit message footer |
| `Created: < v0.8.0` cutover | Grandfathered — §6.8 does not fire at all | provenance.log: `§6.8 SKIPPED — pre-v0.8.0 plan` |
