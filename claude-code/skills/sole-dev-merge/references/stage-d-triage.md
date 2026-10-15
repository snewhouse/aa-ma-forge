# Stage D: findings triage — how findings are routed by severity: the S602 auto-fix, user panels for HIGH/MEDIUM, LOW to reviewer notes.

## Contents

  - [Stage D — Findings triage](#stage-d--findings-triage)

### Stage D — Findings triage

Consumes `/tmp/sole-dev-merge-findings-${SLUG}.md` produced by Stage C and
routes findings by severity:

- **CRITICAL** — deterministic auto-fix for known patterns (non-literal Ruff S602
  → `s/shell=True/shell=False/`); other CRITICALs (ShellCheck, agent-emitted)
  are tagged for user review. Auto-fix lands as a single commit:
  `fix(review): apply CRITICAL ruff findings`.
- **HIGH / MEDIUM** — Claude executor invokes `AskUserQuestion` panels
  (4-per-call max) with Apply / Dispute / Defer options. Bash logs only.
- **LOW** — appended to `/tmp/sole-dev-merge-reviewer-notes-${SLUG}.md`
  for inclusion in the PR/MR body's "Reviewer notes" section (advisory).

```bash
# === stage-d-triage (BEGIN) ===
set -euo pipefail

# Single source-of-truth for the AA-MA commit footer (shared with Stage B-commit).
# footer-resolve:begin
# Resolve the footer helper: an explicit AA_MA_FOOTER_HELPER, then this repo's
# copy (aa-ma-forge), then the link install.sh puts under ~/.claude. Outside
# aa-ma-forge only the link exists. None found → an [ad-hoc] footer, said aloud.
_HELPER_PATH=""
for _cand in "${AA_MA_FOOTER_HELPER:-}" \
    "$(git rev-parse --show-toplevel)/claude-code/hooks/lib/aa-ma-footer.sh" \
    "${CLAUDE_HOME:-$HOME/.claude}/hooks/lib/aa-ma-footer.sh"; do
    if [[ -n "$_cand" && -f "$_cand" ]]; then _HELPER_PATH="$_cand"; break; fi
done
if [[ -n "$_HELPER_PATH" ]]; then
    # shellcheck source=/dev/null
    source "$_HELPER_PATH"
else
    echo "footer-resolve: aa-ma-footer.sh not found — using the [ad-hoc] footer"
    emit_aa_ma_footer() { printf '\n\n[ad-hoc]'; }
fi
# footer-resolve:end

SLUG="${SLUG:-$(date +%s)}"
FINDINGS="/tmp/sole-dev-merge-findings-${SLUG}.md"
RUFF_OUT="/tmp/sole-dev-merge-ruff-${SLUG}.json"

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
FIXED_KEYS=()    # "<file>:<row>" of each applied fix, so the review tagging skips exactly these
FIXED_FILES=()   # what the auto-fix commit stages — never `git add -A`

# === S602 AUTO-FIX (driven from $RUFF_OUT JSON — trusted provenance) ===
# §6.8 audit fix (security HIGH 1-3 + future-proofing HIGH #4):
# Auto-fix the EXACT row Ruff reports, with rule-code equality (not
# substring). Source of truth = Ruff's structured JSON report written by
# Stage C3, NOT the stringified findings.md (which mixes agent-influenced text).
if [[ -s "$RUFF_OUT" ]]; then
    while IFS=$'\t' read -r FILE LINE; do
        [[ -z "$FILE" || -z "$LINE" ]] && continue
        if [[ -f "$FILE" && "$LINE" =~ ^[0-9]+$ && "$LINE" -gt 0 ]]; then
            # Line-scoped sed: rewrite ONLY the exact line Ruff flagged.
            # Docstrings, comments, and unrelated occurrences SURVIVE.
            sed -i "${LINE}s/shell=True/shell=False/" "$FILE"
            # Ruff anchors a multi-line call on its first row, which may not hold
            # `shell=True`: a sed that changed nothing is not a fix (tagged below).
            if sed -n "${LINE}p" "$FILE" | grep -qF 'shell=False'; then
                echo "Stage D auto-fix: S602 at $FILE:$LINE"
                AUTO_FIXED=$((AUTO_FIXED + 1))
                FIXED_KEYS+=("$FILE:$LINE")
                FIXED_FILES+=("$FILE")
            else
                echo "Stage D: S602 at $FILE:$LINE not auto-fixed (shell=True is not on that row)"
            fi
        fi
    done < <(python3 - "$RUFF_OUT" <<'PY'
import json, sys
try:
    with open(sys.argv[1]) as f:
        data = json.load(f)
except (json.JSONDecodeError, FileNotFoundError):
    sys.exit(0)
if not isinstance(data, list):
    sys.exit(0)  # not a Ruff report; Stage C already recorded it UNPARSEABLE
for r in data:
    # Exact equality on the rule code — no substring matching. Only the
    # non-literal form ("identified, security issue") is auto-fixed: Ruff also
    # reports S602 for a literal command ("seems safe, ..."), which may need the
    # shell (a pipe), so shell=False would break it. Bandit's HIGH-severity filter
    # excluded that form; this message test is its Ruff equivalent.
    if r.get("code") == "S602" and "identified, security issue" in (r.get("message") or ""):
        print(f"{r.get('filename', '')}\t{(r.get('location') or {}).get('row', 0)}")
PY
    )
fi

# Tag non-auto-fixable CRITICALs (ShellCheck + agent-emitted) for user review.
# Only the S602 rows actually fixed above are excluded (their line ends "— <file>:<row>").
TAGGED_FOR_REVIEW=()
if [[ "$N_CRITICAL" -gt 0 ]]; then
    while IFS= read -r line; do
        fixed=0
        for key in "${FIXED_KEYS[@]}"; do
            [[ "$line" == *"— ${key}" ]] && fixed=1 && break
        done
        [[ "$fixed" -eq 1 ]] && continue  # auto-fixed above
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
    git add -- "${FIXED_FILES[@]}"   # only what was edited: never sweep in untracked files
    git commit -m "fix(review): apply CRITICAL ruff findings${FOOTER}"
    echo "Stage D: committed $AUTO_FIXED auto-fix(es) ($(git rev-parse --short HEAD))"
fi

# HIGH/MEDIUM — Claude executor handles via AskUserQuestion. Bash logs only.
if [[ "$N_HIGH" -gt 0 || "$N_MEDIUM" -gt 0 ]]; then
    echo "Stage D: $N_HIGH HIGH + $N_MEDIUM MEDIUM finding(s) require AskUserQuestion triage (HITL)"
fi
# === stage-d-triage (END) ===
```
