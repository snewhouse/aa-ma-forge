#!/usr/bin/env bash
# aa-ma-footer.sh — emit the canonical AA-MA commit footer.
#
# Sourced by stage-b-commit and stage-d-triage in
# `claude-code/commands/sole-dev-merge.md`. Single source-of-truth for the
# footer format used in plan-active commits; eliminates the drift risk
# flagged by the M2 §6.8 future-proofing-auditor (HIGH finding: "AA-MA
# footer convention duplicated inline").
#
# Usage:
#     source claude-code/hooks/lib/aa-ma-footer.sh
#     FOOTER=$(emit_aa_ma_footer)
#     git commit -m "subject${FOOTER}"
#
# Behaviour:
# - If an active AA-MA plan exists (i.e., a directory under
#   `<repo-root>/.claude/dev/active/`), emit:
#       \n\n[AA-MA Plan] <plan-name> .claude/dev/active/<plan-name>
# - Otherwise emit `\n\n[ad-hoc]`.
#
# This matches the footer format the `aa-ma-commit-signature.sh` PreToolUse
# hook validates. When the canonical footer format evolves, update this
# helper AND the hook validator together.

emit_aa_ma_footer() {
    local repo_root plan_dir plan_name
    repo_root="$(git rev-parse --show-toplevel 2>/dev/null || echo .)"
    # `find -maxdepth` is preferred over `ls` per SC2012 — handles non-alphanumeric
    # filenames safely. We only need the first match for the active plan.
    plan_dir=$(find "${repo_root}/.claude/dev/active" -mindepth 1 -maxdepth 1 -type d 2>/dev/null | head -1 || true)
    if [[ -n "${plan_dir}" ]]; then
        plan_name=$(basename "${plan_dir}")
        printf '\n\n[AA-MA Plan] %s .claude/dev/active/%s' "${plan_name}" "${plan_name}"
    else
        printf '\n\n[ad-hoc]'
    fi
}
