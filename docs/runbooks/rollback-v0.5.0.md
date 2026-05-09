# Rollback Runbook: v0.5.0

**Affected release:** v0.5.0 (`feat`: engineering-standards doctrine + Planning
Standard 11→12 elements, soft-breaking auto-loaded rule).

**Origin:** AA-MA plan `aa-ma-engineering-standards` M4.8 (per ceo-review CEO-6).

**When to use:**

- The auto-loaded `engineering-standards.md` rule causes session friction in
  consumer projects.
- The new Planning Standard element #12 conflicts with established workflows.
- The Engineering Standards HARD gate (Section 6.7 of `/execute-aa-ma-milestone`)
  blocks legitimate work.
- A regression introduced by v0.5.0 needs reverting while investigation
  continues.

**When NOT to use:**

- Pre-v0.5.0 plans are already grandfathered (per CEO-4) — `Skill(plan-verification)`
  Angle 6 only flags missing element #12 for plans `Created:` on-or-after the
  v0.5.0 release date. If your friction is solely with old plans being flagged,
  you do not need to roll back; verify the `Created:` field of the affected
  plan first.

---

## Rollback Procedure

### Option A — Soft revert (most common)

Bypass the new gates and rule without removing the v0.5.0 commits or tag:

```bash
# Master kill switch — disables ALL AA-MA hooks and engineering-standards gate
export AA_MA_HOOKS_DISABLE=1

# Optional: also remove the auto-loaded rule symlink
rm -f ~/.claude/rules/engineering-standards.md
```

Persists for the current shell. Add to `~/.bashrc`/`~/.zshrc` to make permanent.
This is the fastest unblock and preserves the v0.5.0 changeset for forensics.

### Option B — Full revert from git

Roll the working copy back to v0.4.0 for the affected directories:

```bash
# 1. Revert the doctrine, spec, ADR, and template changes from v0.5.0
git checkout v0.4.0 -- claude-code/rules/ docs/spec/ docs/adr/ docs/templates/

# 2. Re-run the installer to re-symlink the v0.4.0 state
scripts/install.sh

# 3. Verify the engineering-standards.md symlink is gone
test ! -e ~/.claude/rules/engineering-standards.md && echo "Removed: OK"

# 4. (Optional) emergency override for any in-flight session still seeing
#    issues (e.g. stale rule cached in active context)
export AA_MA_HOOKS_DISABLE=1
```

### Option C — Clean uninstall + reinstall

If the install was corrupted by a partial v0.5.0 ship:

```bash
# 1. Full uninstall
scripts/uninstall.sh

# 2. Check out v0.4.0
git checkout v0.4.0

# 3. Reinstall from v0.4.0 state
scripts/install.sh
```

Note: `uninstall.sh` removes ALL aa-ma-forge symlinks under `~/.claude/`. The
backup directory at `~/.claude/backups/aa-ma-forge-YYYYMMDD-HHMMSS/` from the
original install can be restored via `scripts/uninstall.sh --restore` if needed.

---

## Verification After Rollback

```bash
# 1. engineering-standards.md symlink absent (Option B/C)
test ! -e ~/.claude/rules/engineering-standards.md && echo "PASS: rule removed"

# 2. AA_MA_HOOKS_DISABLE active (Option A)
[ "$AA_MA_HOOKS_DISABLE" = "1" ] && echo "PASS: kill switch active"

# 3. /aa-ma-plan no longer prompts for "Engineering Standards Declaration"
#    (Phase 2 Step 2.4 gated by rule presence)

# 4. /execute-aa-ma-milestone Section 6.7 gate either skipped (kill switch)
#    or absent (rule removed)
```

---

## Pre-v0.5.0 Plan Compatibility

Pre-v0.5.0 plans (those without `Created: YYYY-MM-DD` on-or-after the v0.5.0
release date) are **automatically grandfathered** by the engineering-standards
structural check. They remain valid and continue to execute under the prior
11-output Planning Standard. No rollback action needed for old plans.

After rollback (Option A/B/C), all plans — old and new — execute under the
v0.4.0 standard.

---

## Element #12 Reversibility

Reverting also reverts element #12 ("Engineering Standards Declaration") of the
Planning Standard. New plans created post-rollback need not include element #12.
Existing plans authored under v0.5.0 with element #12 declared will continue to
parse fine — the section becomes informational rather than required.

---

## CHANGELOG cross-reference

The v0.5.0 [`Behavior change (soft-breaking)`](../../CHANGELOG.md) and
[`Rollback`](../../CHANGELOG.md) subsections summarize this procedure inline.
This runbook is the canonical detailed reference.

---

## Reporting

If the rollback was needed because of a regression, please open an issue at
https://github.com/snewhouse/aa-ma-forge/issues with:

- Which option (A/B/C) was used
- Symptom that triggered the rollback
- Expected vs. actual behavior
- (Optional) `~/.claude/hooks/cache/compaction-snapshots/*.md` and recent
  `provenance.log` excerpts from affected sessions

---

**Last updated:** 2026-05-09 — initial authoring (M4.8 of aa-ma-engineering-standards plan).
