#!/usr/bin/env bats
# test_stage_e_remote.bats — Stage E1 (remote detection) + E2 (choice + AUQ bridge).
#
# Plan §3.6 acceptance: three fixtures (github-only, gitlab-only, dual) verify
# classification + AskUserQuestion mock invocation for the dual case.
# Plan §4.3.1 falsifiable AC (remote detection):
#   origin → github.com/foo/bar.git   → n_github=1, n_gitlab=0
#   origin → gitlab.com/x/y + github → github.com/a/b → n_github=1, n_gitlab=1
# Plan §4.3.2 falsifiable AC (dual-remote prompt):
#   n_github=1 AND n_gitlab=1 → AskUserQuestion args have options[0].label
#   matching ^GitLab and an option matching ^GitHub elsewhere.
#
# The Stage E2 bash cannot invoke AskUserQuestion (that's a Claude tool); it
# logs the would-be-AUQ args as JSON to "$AUQ_LOG" per the test harness
# contract in reference.md. The Claude executor in production reads the same
# log and dispatches the real AskUserQuestion. Tests assert the JSON shape.

load fixtures/helpers

setup() {
    REPO_ROOT="$(cd "${BATS_TEST_DIRNAME}/../../.." && pwd)"
    COMMAND_MD="${REPO_ROOT}/claude-code/commands/sole-dev-merge.md"
    EXTRACT="${REPO_ROOT}/tests/commands/sole-dev-merge/fixtures/extract_stage.sh"

    SCRIPT_DIR="$(tmp_script_dir)"
    BATS_TMP="$(mktemp -d)"
    AUQ_LOG="${BATS_TMP}/auq.json"
    export BATS_TMP SCRIPT_DIR REPO_ROOT COMMAND_MD EXTRACT AUQ_LOG

    [[ -f "$COMMAND_MD" ]] || { echo "Missing $COMMAND_MD" >&2; return 1; }
    [[ -x "$EXTRACT"   ]] || { echo "Missing or non-exec $EXTRACT" >&2; return 1; }

    E1_SCRIPT="${SCRIPT_DIR}/e1.sh"
    E2_SCRIPT="${SCRIPT_DIR}/e2.sh"
    bash "$EXTRACT" stage-e1-remote "$COMMAND_MD" > "$E1_SCRIPT"
    bash "$EXTRACT" stage-e2-choice "$COMMAND_MD" > "$E2_SCRIPT"
    chmod +x "$E1_SCRIPT" "$E2_SCRIPT"
    export E1_SCRIPT E2_SCRIPT
}

teardown() {
    rm -rf "$BATS_TMP" "$SCRIPT_DIR"
}

# ---------------------------------------------------------------------------
# Stage E1 — remote detection
# ---------------------------------------------------------------------------

@test "E1: github-only origin → n_github=1, n_gitlab=0 (AC §4.3.1)" {
    cd "$BATS_TMP"
    sandbox_init
    git remote add origin https://github.com/foo/bar.git

    run bash "$E1_SCRIPT"
    [ "$status" -eq 0 ]
    [[ "$output" == *"n_github=1"* ]]
    [[ "$output" == *"n_gitlab=0"* ]]
}

@test "E1: gitlab-only origin → n_github=0, n_gitlab=1 (AC §4.3.1)" {
    cd "$BATS_TMP"
    sandbox_init
    git remote add origin https://gitlab.com/x/y.git

    run bash "$E1_SCRIPT"
    [ "$status" -eq 0 ]
    [[ "$output" == *"n_github=0"* ]]
    [[ "$output" == *"n_gitlab=1"* ]]
}

@test "E1: dual remotes (gitlab origin + github named) → n_github=1, n_gitlab=1 (AC §4.3.1)" {
    cd "$BATS_TMP"
    sandbox_init
    git remote add origin https://gitlab.com/x/y.git
    git remote add github https://github.com/a/b.git

    run bash "$E1_SCRIPT"
    [ "$status" -eq 0 ]
    [[ "$output" == *"n_github=1"* ]]
    [[ "$output" == *"n_gitlab=1"* ]]
}

@test "E1: deduplicates fetch+push rows for one remote" {
    # git remote -v shows two lines per remote (fetch + push). E1 must NOT
    # double-count. Verified by single-remote case yielding count=1, not 2.
    cd "$BATS_TMP"
    sandbox_init
    git remote add origin https://github.com/foo/bar.git
    # Confirm git-remote-v emits both rows (canary for the regression):
    [ "$(git remote -v | wc -l)" -eq 2 ]

    run bash "$E1_SCRIPT"
    [ "$status" -eq 0 ]
    [[ "$output" == *"n_github=1"* ]]
    [[ "$output" != *"n_github=2"* ]]
}

# ---------------------------------------------------------------------------
# Stage E2 — dual-remote choice + AUQ bridge
# ---------------------------------------------------------------------------

@test "E2: dual remotes → AUQ_LOG JSON has options[0].label ^GitLab, includes GitHub (AC §4.3.2)" {
    cd "$BATS_TMP"
    sandbox_init
    git remote add origin https://gitlab.com/x/y.git
    git remote add github https://github.com/a/b.git

    # E2 depends on E1's exports (n_github, n_gitlab). Source rather than run
    # to inherit env, then run E2 in the same shell.
    run bash -c "source '$E1_SCRIPT' >/dev/null; export AUQ_LOG='$AUQ_LOG'; bash '$E2_SCRIPT'"
    [ "$status" -eq 0 ]
    [[ "$output" == *"DUAL_REMOTE_PROMPT"* ]]

    [ -f "$AUQ_LOG" ]
    # Default label is GitLab (Biorelate convention).
    grep -qE '"default"\s*:\s*"GitLab[^"]*"' "$AUQ_LOG"
    # options[0].label matches ^GitLab — single source-of-truth: the labels
    # array order. Using jq if present, fall back to grep.
    if command -v jq >/dev/null 2>&1; then
        first_label="$(jq -r '.labels[0]' "$AUQ_LOG")"
        [[ "$first_label" == GitLab* ]]
        # Some option (any index) matches ^GitHub
        jq -e '.labels | any(. | startswith("GitHub"))' "$AUQ_LOG" >/dev/null
    else
        # Fallback: order-preserving grep on the labels array literal
        head -c 1000 "$AUQ_LOG" | grep -qE '"labels"\s*:\s*\[\s*"GitLab[^"]*"'
        grep -qE '"GitHub[^"]*"' "$AUQ_LOG"
    fi
}

@test "E2: single github remote → no AUQ_DISPATCH, REMOTE_CHOICE=github" {
    cd "$BATS_TMP"
    sandbox_init
    git remote add origin https://github.com/foo/bar.git

    run bash -c "source '$E1_SCRIPT' >/dev/null; export AUQ_LOG='$AUQ_LOG'; bash '$E2_SCRIPT'"
    [ "$status" -eq 0 ]
    [[ "$output" != *"DUAL_REMOTE_PROMPT"* ]]
    [[ "$output" == *"REMOTE_CHOICE=github"* ]]
    # Single-remote path must NOT touch AUQ_LOG.
    [ ! -f "$AUQ_LOG" ]
}

@test "E2: single gitlab remote → no AUQ_DISPATCH, REMOTE_CHOICE=gitlab" {
    cd "$BATS_TMP"
    sandbox_init
    git remote add origin https://gitlab.com/x/y.git

    run bash -c "source '$E1_SCRIPT' >/dev/null; export AUQ_LOG='$AUQ_LOG'; bash '$E2_SCRIPT'"
    [ "$status" -eq 0 ]
    [[ "$output" != *"DUAL_REMOTE_PROMPT"* ]]
    [[ "$output" == *"REMOTE_CHOICE=gitlab"* ]]
    [ ! -f "$AUQ_LOG" ]
}

@test "E2: zero github+gitlab remotes → abort with actionable error" {
    cd "$BATS_TMP"
    sandbox_init
    git remote add origin https://bitbucket.org/x/y.git

    run bash -c "source '$E1_SCRIPT' >/dev/null; export AUQ_LOG='$AUQ_LOG'; bash '$E2_SCRIPT'"
    [ "$status" -ne 0 ]
    [[ "$output" == *"only github.com and gitlab.com remotes supported"* ]]
}
