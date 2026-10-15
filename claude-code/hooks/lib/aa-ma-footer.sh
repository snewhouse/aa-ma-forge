#!/usr/bin/env bash
# aa-ma-footer.sh — emit the canonical AA-MA commit footer.
#
# Sourced by stage-b-commit (`claude-code/skills/sole-dev-merge/SKILL.md`) and
# stage-d-triage (`claude-code/skills/sole-dev-merge/references/stage-d-triage.md`). Single source-of-truth for the
# footer format used in plan-active commits; eliminates the drift risk
# flagged by the M2 §6.8 future-proofing-auditor (HIGH finding: "AA-MA
# footer convention duplicated inline").
#
# Usage:
#     source claude-code/hooks/lib/aa-ma-footer.sh
#     FOOTER=$(emit_aa_ma_footer)
#     git commit -m "subject${FOOTER}"
#
# Behaviour (spec §VI, forge L-054):
# - No active plan (no directory under `<repo-root>/.claude/dev/active/`)
#   → `\n\n[ad-hoc]`.
# - Exactly one active plan → `\n\n[AA-MA Plan] <plan> .claude/dev/active/<plan>`.
# - Several → the one plan the branch changed: a tracked difference against
#   the merge-base with origin/HEAD (origin/main when unset), committed or not,
#   or an untracked plan dir. None or more than one → `[ad-hoc]` plus a
#   `WARN: aa-ma-footer` line on stderr. It never guesses.
# Works with or without the caller's `set -o pipefail` / `set -e`.
#
# This matches the footer format the `aa-ma-commit-signature.sh` PreToolUse
# hook validates. When the canonical footer format evolves, update this
# helper AND the hook validator together.

emit_aa_ma_footer() {
    local root ref base d
    local -a plans=() touched=()
    # why: outside a repo, use cwd; the plan scan then finds nothing, so [ad-hoc]
    root="$(git rev-parse --show-toplevel 2>/dev/null || echo .)"
    for d in "$root"/.claude/dev/active/*/; do
        [[ -d "$d" ]] && plans+=("$(basename "$d")")
    done
    if (( ${#plans[@]} == 1 )); then
        touched=("${plans[0]}")
    elif (( ${#plans[@]} > 1 )); then
        # With parallel plans, a branch's own plan is the one it changed
        # (milestone branches carry their plan's AA-MA files). No pipeline
        # here, so the fallbacks work without the caller's pipefail.
        ref=$(git symbolic-ref -q --short refs/remotes/origin/HEAD) || ref=origin/main
        # why: no merge-base (detached orphan, no remote) → nothing touched → [ad-hoc] + WARN
        base=$(git merge-base HEAD "$ref" 2>/dev/null) || base=""
        for d in "${plans[@]}"; do
            # `git diff <base>` sees committed and uncommitted tracked edits;
            # ls-files adds a plan dir not yet in git.
            if [[ -n "$base" ]] && [[ -n "$(git diff --name-only "$base" -- "$root/.claude/dev/active/$d")$(git ls-files --others --exclude-standard -- "$root/.claude/dev/active/$d")" ]]; then
                touched+=("$d")
            fi
        done
        if (( ${#touched[@]} != 1 )); then
            echo "WARN: aa-ma-footer: ${#plans[@]} active plans, ${#touched[@]} touched on this branch — using [ad-hoc]" >&2
        fi
    fi
    if (( ${#touched[@]} == 1 )); then
        printf '\n\n[AA-MA Plan] %s .claude/dev/active/%s' "${touched[0]}" "${touched[0]}"
    else
        printf '\n\n[ad-hoc]'
    fi
}
