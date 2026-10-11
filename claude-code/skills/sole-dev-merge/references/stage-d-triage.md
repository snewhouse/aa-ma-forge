# Stage D: findings triage — how findings are routed by severity: the B602 auto-fix, user panels for HIGH/MEDIUM, LOW to reviewer notes.

## Contents

  - [Stage D — Findings triage](#stage-d--findings-triage)

### Stage D — Findings triage

Consumes `/tmp/sole-dev-merge-findings-${SLUG}.md` produced by Stage C and
routes findings by severity:

- **CRITICAL** — deterministic auto-fix for known patterns (Bandit B602
  → `s/shell=True/shell=False/`); other CRITICALs (ShellCheck, agent-emitted)
  are tagged for user review. Auto-fix lands as a single commit:
  `fix(review): apply CRITICAL bandit findings`.
- **HIGH / MEDIUM** — Claude executor invokes `AskUserQuestion` panels
  (4-per-call max) with Apply / Dispute / Defer options. Bash logs only.
- **LOW** — appended to `/tmp/sole-dev-merge-reviewer-notes-${SLUG}.md`
  for inclusion in the PR/MR body's "Reviewer notes" section (advisory).

```bash
# === stage-d-triage (BEGIN) ===
set -euo pipefail

# Single source-of-truth for the AA-MA commit footer (shared with Stage B-commit).
_HELPER_PATH="${AA_MA_FOOTER_HELPER:-$(git rev-parse --show-toplevel)/claude-code/hooks/lib/aa-ma-footer.sh}"
source "$_HELPER_PATH"

SLUG="${SLUG:-$(date +%s)}"
FINDINGS="/tmp/sole-dev-merge-findings-${SLUG}.md"
BANDIT_OUT="/tmp/sole-dev-merge-bandit-${SLUG}.json"

if [[ ! -f "$FINDINGS" ]]; then
    echo "Stage D: no findings file at $FINDINGS — nothing to triage"
    exit 0
fi

N_CRITICAL=$(grep -cE '^\[CRITICAL\]' "$FINDINGS" || true)
N_HIGH=$(grep -cE '^\[HIGH\]' "$FINDINGS" || true)
N_MEDIUM=$(grep -cE '^\[MEDIUM\]' "$FINDINGS" || true)
N_LOW=$(grep -cE '^\[LOW\]' "$FINDINGS" || true)

echo "Stage D triage: $N_CRITICAL CRITICAL, $N_HIGH HIGH, $N_MEDIUM MEDIUM, $N_LOW LOW"

AUTO_FIXED=0

# === B602 AUTO-FIX (driven from $BANDIT_OUT JSON — trusted provenance) ===
# §6.8 audit fix (security HIGH 1-3 + future-proofing HIGH #4):
# Auto-fix the EXACT line Bandit reports, with test_id equality (not
# substring). Source of truth = Bandit's structured JSON output, NOT the
# stringified findings.md (which mixes agent-influenced text).
if [[ -s "$BANDIT_OUT" ]]; then
    while IFS=$'\t' read -r FILE LINE; do
        [[ -z "$FILE" || -z "$LINE" ]] && continue
        if [[ -f "$FILE" && "$LINE" =~ ^[0-9]+$ && "$LINE" -gt 0 ]]; then
            # Line-scoped sed: rewrite ONLY the exact line Bandit flagged.
            # Docstrings, comments, and unrelated occurrences SURVIVE.
            sed -i "${LINE}s/shell=True/shell=False/" "$FILE"
            echo "Stage D auto-fix: B602 at $FILE:$LINE"
            AUTO_FIXED=$((AUTO_FIXED + 1))
        fi
    done < <(python3 - "$BANDIT_OUT" <<'PY'
import json, sys
try:
    with open(sys.argv[1]) as f:
        data = json.load(f)
except (json.JSONDecodeError, FileNotFoundError):
    sys.exit(0)
for r in data.get("results", []):
    # Equality match on test_id + severity — no substring matching
    if r.get("test_id") == "B602" and r.get("issue_severity") == "HIGH":
        print(f"{r.get('filename', '')}\t{r.get('line_number', 0)}")
PY
    )
fi

# Tag non-auto-fixable CRITICALs (ShellCheck + agent-emitted) for user review.
# B602 lines are excluded — we've handled them via the JSON-driven path above.
TAGGED_FOR_REVIEW=()
if [[ "$N_CRITICAL" -gt 0 ]]; then
    while IFS= read -r line; do
        [[ "$line" == *"B602"* ]] && continue  # already auto-fixed
        TAGGED_FOR_REVIEW+=("$line")
    done < <(grep -E '^\[CRITICAL\]' "$FINDINGS")
fi

if [[ "${#TAGGED_FOR_REVIEW[@]}" -gt 0 ]]; then
    echo "Stage D: ${#TAGGED_FOR_REVIEW[@]} CRITICAL finding(s) tagged for user review (not auto-fixed):"
    printf '  %s\n' "${TAGGED_FOR_REVIEW[@]}"
fi

# LOW → reviewer notes (advisory; surfaced in PR/MR body by Stage E3)
if [[ "$N_LOW" -gt 0 ]]; then
    REVIEWER_NOTES="/tmp/sole-dev-merge-reviewer-notes-${SLUG}.md"
    grep -E '^\[LOW\]' "$FINDINGS" > "$REVIEWER_NOTES"
    echo "Stage D: $N_LOW LOW finding(s) → $REVIEWER_NOTES (advisory)"
fi

# Commit auto-fixes if any (footer from shared helper for drift-resistance)
if [[ "$AUTO_FIXED" -gt 0 ]]; then
    FOOTER=$(emit_aa_ma_footer)
    git add -A
    git commit -m "fix(review): apply CRITICAL bandit findings${FOOTER}"
    echo "Stage D: committed $AUTO_FIXED auto-fix(es) ($(git rev-parse --short HEAD))"
fi

# HIGH/MEDIUM — Claude executor handles via AskUserQuestion. Bash logs only.
if [[ "$N_HIGH" -gt 0 || "$N_MEDIUM" -gt 0 ]]; then
    echo "Stage D: $N_HIGH HIGH + $N_MEDIUM MEDIUM finding(s) require AskUserQuestion triage (HITL)"
fi
# === stage-d-triage (END) ===
```
