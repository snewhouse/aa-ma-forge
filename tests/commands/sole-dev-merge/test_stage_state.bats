#!/usr/bin/env bats
# test_stage_state.bats — the stage state file (sole-dev-merge-fixes M2, forge L-055).
#
# Each stage block runs in its own Bash tool call, so shell variables do not
# carry from one block to the next. Stage A writes
#   "$(git rev-parse --absolute-git-dir)/sole-dev-merge.env"
# as KEY=<base64> lines; every later block loads it, and appends with sdm_save.
#
# Contract (plan §4 M2): a non-empty explicit env beats the file; the file beats
# defaults; required values fail loud; the last write of a key wins; a file left
# by another branch is ignored, with a message.
#
# Every block here runs through `fresh`: `env -i` with only PATH and HOME, which
# is what a new Bash tool call gives a block.

bats_require_minimum_version 1.5.0

load fixtures/helpers

# Every stage block in the skill, read from its markers, so a new block is
# checked without anyone remembering to list it. NO_STATE names the blocks
# that hold no state: the banner. (E1 left the list in sole-dev-merge-fixes M4,
# when it started saving its remote counts for E2.)
NO_STATE=" stage-banner "
mapfile -t BLOCKS < <(
    grep -rhoE '=== stage-[a-z0-9-]+ \(BEGIN\)' "${BATS_TEST_DIRNAME}/../../../claude-code/skills/sole-dev-merge" \
        | sed -E 's/^=== (stage-[a-z0-9-]+) .*/\1/' \
        | while read -r b; do [[ "$NO_STATE" == *" $b "* ]] || echo "$b"; done
)

setup() {
    REPO_ROOT="$(cd "${BATS_TEST_DIRNAME}/../../.." && pwd)"
    COMMAND_MD="${REPO_ROOT}/claude-code/skills/sole-dev-merge/SKILL.md"
    SKILL_DIR="${REPO_ROOT}/claude-code/skills/sole-dev-merge"
    EXTRACT="${REPO_ROOT}/tests/commands/sole-dev-merge/fixtures/extract_stage.sh"
    STUB_DIR="${REPO_ROOT}/tests/commands/sole-dev-merge/fixtures/bin"
    SCRIPT_DIR="$(tmp_script_dir)"
    BATS_TMP="$(mktemp -d)"
    CLI_LOG="${SCRIPT_DIR}/cli.log"; : > "$CLI_LOG"     # why: outside the repo, so Stage A sees a clean tree
    SCAN_LOG="${SCRIPT_DIR}/scan.log"; : > "$SCAN_LOG"
    export REPO_ROOT COMMAND_MD SKILL_DIR EXTRACT STUB_DIR SCRIPT_DIR BATS_TMP CLI_LOG SCAN_LOG

    for b in "${BLOCKS[@]}"; do
        bash "$EXTRACT" "$b" "$COMMAND_MD" > "${SCRIPT_DIR}/${b}.sh"
    done

    # Scanner stubs for Stage C: log the files they were given, report clean.
    for s in ruff shellcheck; do
        printf '#!/usr/bin/env bash\necho "%s $*" >> "%s"\necho "[]"\n' "$s" "$SCAN_LOG" > "${SCRIPT_DIR}/${s}-stub"
        chmod +x "${SCRIPT_DIR}/${s}-stub"
    done

    # Sandbox: main + feature (1 commit ahead, one .py and one .sh), bare origin.
    cd "$BATS_TMP"
    sandbox_init
    echo init > a.txt && git add a.txt && mkcommit "init"
    git init -q --bare "${BATS_TMP}.bare.git"
    git remote add origin "${BATS_TMP}.bare.git"
    git switch -q -c feature
    printf 'import os\n' > app.py
    printf '#!/usr/bin/env bash\necho hi\n' > run.sh
    git add app.py run.sh && mkcommit "feat: app"
    git push -q origin main feature
}

teardown() {
    rm -rf "$BATS_TMP" "${BATS_TMP}.bare.git" "$SCRIPT_DIR"
}

# A fresh shell with an empty env, like a new Bash tool call.
fresh() { env -i PATH="${STUB_DIR}:${PATH}" HOME="$HOME" CLI_LOG="$CLI_LOG" "$@"; }
blk()   { printf '%s/%s.sh' "$SCRIPT_DIR" "$1"; }
state() { printf '%s/sole-dev-merge.env' "$(git rev-parse --absolute-git-dir)"; }
# get KEY — the last value of KEY in the state file, decoded.
get() { local l; l=$(grep "^$1=" "$(state)" | tail -n 1) || return 1; printf '%s' "${l#*=}" | base64 -d; }
# put KEY VALUE — append one line in sdm_save's format.
put() { printf '%s=%s\n' "$1" "$(printf '%s' "$2" | base64 | tr -d '\n')" >> "$(state)"; }
# probe — the loader as shipped in G1, then print each key in $SHOW as k=%q.
probe() {
    {
        echo 'set -euo pipefail'
        sed -n '/^SDM_STATE=/,/^sdm_save()/p' "$(blk stage-g1-protect)"
        echo 'for k in ${SHOW:-}; do printf "%s=%q\n" "$k" "${!k:-}"; done'
    } > "${SCRIPT_DIR}/probe.sh"
    # why: `p=$(probe)` runs without errexit (bash does not inherit it into $(…)),
    # so a missing loader must fail through the return code, not set -e.
    grep -q '^sdm_load()' "${SCRIPT_DIR}/probe.sh" || { echo "no sdm_load in G1" >&2; return 1; }
    printf '%s/probe.sh' "$SCRIPT_DIR"
}
# seed_g — the keys Stage F/G1/G2 would have saved, after a real Stage A.
seed_g() {
    fresh bash "$(blk stage-a-preflight)" >/dev/null
    put REMOTE_CHOICE github; put PR_NUM 42; put PR_URL "https://github.com/test/repo/pull/42"
    put MERGE_STRATEGY rebase; put CI_STATE green
}

# --- Stage A: the writer -----------------------------------------------------

@test "A writes ORIGINAL_BRANCH, BASE_REF, DEFAULT_BRANCH, SLUG and SDM_DIR" {
    run fresh bash "$(blk stage-a-preflight)"
    [ "$status" -eq 0 ]
    [ -f "$(state)" ]
    [ "$(get ORIGINAL_BRANCH)" = feature ]
    [ "$(get BASE_REF)" = main ]
    [ "$(get DEFAULT_BRANCH)" = main ]
    [ -n "$(get SLUG)" ]
    [ "$(get SDM_DIR)" = "$(git rev-parse --absolute-git-dir)/sdm-$(get SLUG)" ]
}

@test "A creates the state file 600 and SDM_DIR 700" {
    run fresh bash "$(blk stage-a-preflight)"
    [ "$status" -eq 0 ]
    [ "$(stat -c %a "$(state)")" = 600 ]
    [ "$(stat -c %a "$(get SDM_DIR)")" = 700 ]
}

@test "A truncates a stale state file from an earlier run" {
    put ORIGINAL_BRANCH feature; put PR_NUM 999
    run fresh bash "$(blk stage-a-preflight)"
    [ "$status" -eq 0 ]
    run grep -c '^PR_NUM=' "$(state)"
    [ "$output" = 0 ]
}

@test "an aborted A leaves no state file behind" {
    put ORIGINAL_BRANCH feature; put PR_NUM 999
    echo dirt > dirty.txt
    run fresh bash "$(blk stage-a-preflight)"
    [ "$status" -eq 1 ]
    [[ "$output" == *"ABORT: Uncommitted changes"* ]]
    [ ! -e "$(state)" ]
}

# --- Values carry between separate shells --------------------------------------

@test "B appends CHANGED_FILES, CHANGED_PY and CHANGED_SH" {
    fresh bash "$(blk stage-a-preflight)" >/dev/null
    run fresh bash "$(blk stage-b-scope)"
    [ "$status" -eq 0 ]
    [ "$(get CHANGED_PY)" = app.py ]
    [ "$(get CHANGED_SH)" = run.sh ]
    [ "$(get CHANGED_FILES)" = $'app.py\nrun.sh' ]
}

@test "C in a fresh empty shell scans B's files and writes findings under SDM_DIR" {
    fresh bash "$(blk stage-a-preflight)" >/dev/null
    fresh bash "$(blk stage-b-scope)" >/dev/null
    run fresh RUFF_BIN="${SCRIPT_DIR}/ruff-stub" SHELLCHECK_BIN="${SCRIPT_DIR}/shellcheck-stub" \
        bash "$(blk stage-c-aggregate)"
    [ "$status" -eq 0 ]
    grep -q '^ruff .*app\.py' "$SCAN_LOG"
    grep -q '^shellcheck .*run\.sh' "$SCAN_LOG"
    [[ "$output" == *"Stage C scanned: Ruff S 1 file(s), ShellCheck 1 file(s)"* ]]
    [ -f "$(get SDM_DIR)/findings.md" ]
}

@test "D uses A's SLUG: it triages C's findings and writes reviewer notes under SDM_DIR" {
    fresh bash "$(blk stage-a-preflight)" >/dev/null
    fresh bash "$(blk stage-b-scope)" >/dev/null
    fresh RUFF_BIN="${SCRIPT_DIR}/ruff-stub" SHELLCHECK_BIN="${SCRIPT_DIR}/shellcheck-stub" \
        bash "$(blk stage-c-aggregate)" >/dev/null
    echo "[LOW]      A low finding — app.py:1" >> "$(get SDM_DIR)/findings.md"
    run fresh bash "$(blk stage-d-triage)"
    [ "$status" -eq 0 ]
    [[ "$output" == *"Stage D triage:"* ]]
    [ -s "$(get SDM_DIR)/reviewer-notes.md" ]
}

@test "E3 writes the body under SDM_DIR and saves PR_BODY_FILE" {
    fresh bash "$(blk stage-a-preflight)" >/dev/null
    run fresh bash "$(blk stage-e3-body)"
    [ "$status" -eq 0 ]
    [ "$(get PR_BODY_FILE)" = "$(get SDM_DIR)/body.md" ]
    [ -s "$(get SDM_DIR)/body.md" ]
}

@test "G3 with no env reads PR_NUM from the file and saves MERGE_DISPATCHED=1" {
    seed_g
    run fresh bash "$(blk stage-g3-merge)"
    [ "$status" -eq 0 ]
    grep -q '^gh pr merge 42 ' "$CLI_LOG"
    [ "$(get MERGE_DISPATCHED)" = 1 ]
}

@test "G4 with no env reads ORIGINAL_BRANCH from the file" {
    seed_g; put MERGE_DISPATCHED 1
    run fresh bash "$(blk stage-g4-cleanup)"
    [ "$status" -eq 0 ]
    [[ "$output" != *"needs ORIGINAL_BRANCH"* ]]
    [[ "$output" == *"branch=feature"* ]]
}

@test "a key written twice gives the last value" {
    seed_g; put PR_NUM 7
    run fresh bash "$(blk stage-g3-merge)"
    [ "$status" -eq 0 ]
    grep -q '^gh pr merge 7 ' "$CLI_LOG"
}

# --- The loader: precedence, hostile input, refusals ---------------------------

@test "values with spaces, quotes, \$, backticks, newlines and a trailing = round-trip" {
    local p v
    p=$(probe)
    v=$'a b "q" \'s\' $HOME `id` $(id) ; | & < > \\ x\ty\nline2 trail='
    put ORIGINAL_BRANCH feature; put PR_URL "$v"
    run fresh SHOW=PR_URL bash "$p"
    [ "$status" -eq 0 ]
    [ "$output" = "PR_URL=$(printf '%q' "$v")" ]
}

@test "hand-written hostile lines execute nothing; bad values and unknown keys are reported" {
    local p
    p=$(probe)
    put ORIGINAL_BRANCH feature
    printf '%s\n' 'PR_URL=$(touch PWN)' 'CI_STATE=`touch PWN`' \
        "GIT_SSH_COMMAND=$(printf 'touch PWN' | base64)" "BASH_ENV=$(printf '/tmp/x' | base64)" >> "$(state)"
    run fresh SHOW="PR_URL CI_STATE" bash "$p"
    [ "$status" -eq 0 ]
    [ ! -e PWN ]
    [[ "$output" == *"Stage state: bad value for PR_URL"* ]]
    [[ "$output" == *"Stage state: bad value for CI_STATE"* ]]
    [[ "$output" == *"Stage state: ignoring unknown key 'GIT_SSH_COMMAND'"* ]]
    [[ "$output" == *"Stage state: ignoring unknown key 'BASH_ENV'"* ]]
}

@test "a non-empty explicit env beats the file" {
    local p
    p=$(probe)
    put ORIGINAL_BRANCH feature; put PR_NUM 42
    run fresh PR_NUM=99 SHOW=PR_NUM bash "$p"
    [ "$output" = "PR_NUM=99" ]
}

@test "an empty exported var does not mask the file" {
    local p
    p=$(probe)
    put ORIGINAL_BRANCH feature; put PR_NUM 42
    run fresh PR_NUM= SHOW=PR_NUM bash "$p"
    [ "$output" = "PR_NUM=42" ]
}

@test "a file written on another branch is ignored, with the message" {
    local p
    p=$(probe)
    put ORIGINAL_BRANCH some-other-branch; put PR_NUM 42
    run fresh SHOW=PR_NUM bash "$p"
    [ "$status" -eq 0 ]
    [[ "$output" == *"Stage state: sole-dev-merge.env is not for this branch — ignored (run Stage A first)"* ]]
    [[ "$output" == *"PR_NUM=''"* ]]
}

@test "a bad line keeps the earlier good value; a bad ORIGINAL_BRANCH voids the file" {
    local p
    p=$(probe)
    put ORIGINAL_BRANCH feature; put PR_NUM 42
    printf 'PR_NUM=%%%%notbase64\n' >> "$(state)"
    run fresh SHOW=PR_NUM bash "$p"
    [[ "$output" == *"PR_NUM=42"* ]]
    : > "$(state)"
    printf 'ORIGINAL_BRANCH=%%%%notbase64\n' >> "$(state)"; put PR_NUM 42
    run fresh SHOW=PR_NUM bash "$p"
    [[ "$output" == *"not for this branch"* ]]
    [[ "$output" == *"PR_NUM=''"* ]]
}

@test "a value loses its trailing newline (documented: no key needs one)" {
    local p
    p=$(probe)
    put ORIGINAL_BRANCH feature; put CHANGED_FILES $'a.py\nb.sh\n'
    run fresh SHOW=CHANGED_FILES bash "$p"
    [ "$output" = "CHANGED_FILES=$(printf '%q' $'a.py\nb.sh')" ]
}

@test "a symlinked, group-writable or world-writable state file is refused" {
    local p st
    p=$(probe)
    put ORIGINAL_BRANCH feature; put PR_NUM 42
    st=$(state)
    chmod g+w "$st"
    run fresh SHOW=PR_NUM bash "$p"
    [[ "$output" == *"Stage state: refusing sole-dev-merge.env"* ]]
    [[ "$output" == *"PR_NUM=''"* ]]
    chmod g-w,o+w "$st"
    run fresh SHOW=PR_NUM bash "$p"
    [[ "$output" == *"Stage state: refusing sole-dev-merge.env"* ]]
    chmod o-w "$st"
    mv "$st" "${st}.real" && ln -s "${st}.real" "$st"
    run fresh SHOW=PR_NUM bash "$p"
    [[ "$output" == *"Stage state: refusing sole-dev-merge.env"* ]]
    [[ "$output" == *"PR_NUM=''"* ]]
    # A foreign owner needs root to set up; `! -O` covers it in the same branch.
}

# --- §6.8 remediation (code-reviewer, security-auditor, future-proofing) --------

@test "A outside a git repository prints an ABORT line and exits 1" {
    local nr
    nr=$(mktemp -d)
    run fresh bash -c 'cd "$1" && bash "$2"' _ "$nr" "$(blk stage-a-preflight)"
    rm -rf "$nr"
    [ "$status" -eq 1 ]
    [[ "$output" == *"ABORT: Not inside a git repository"* ]]
}

@test "A refuses a detached HEAD" {
    git switch -q --detach
    run fresh bash "$(blk stage-a-preflight)"
    [ "$status" -eq 1 ]
    [[ "$output" == *"ABORT: Detached HEAD"* ]]
}

@test "on a detached HEAD the loader ignores a file whose ORIGINAL_BRANCH is empty" {
    local p
    p=$(probe)
    put ORIGINAL_BRANCH ""; put PR_NUM 42
    git switch -q --detach
    run fresh SHOW=PR_NUM bash "$p"
    [[ "$output" == *"is not for this branch"* ]]
    [[ "$output" == *"PR_NUM=''"* ]]
}

@test "sdm_save refuses a symlinked state file and leaves the link's target alone" {
    local st target
    fresh bash "$(blk stage-a-preflight)" >/dev/null
    st=$(state); target="${SCRIPT_DIR}/victim"
    printf 'precious\n' > "$target"
    rm -f "$st" && ln -s "$target" "$st"
    run fresh bash "$(blk stage-b-scope)"
    [ "$status" -ne 0 ]
    [[ "$output" == *"Stage state: refusing to save"* ]]
    [ "$(cat "$target")" = precious ]
}

@test "sdm_save refuses a group-writable state file and leaves it unchanged" {
    local st before
    fresh bash "$(blk stage-a-preflight)" >/dev/null
    st=$(state); chmod g+w "$st"; before=$(cat "$st")
    run fresh bash "$(blk stage-b-scope)"
    [ "$status" -ne 0 ]
    [[ "$output" == *"Stage state: refusing to save"* ]]
    [ "$(cat "$st")" = "$before" ]
}

@test "sdm_save creates a missing state file as 600 whatever the caller's umask" {
    umask 022
    run fresh BASE_REF=main bash "$(blk stage-b-scope)"
    [ "$status" -eq 0 ]
    [ "$(stat -c %a "$(state)")" = 600 ]
}

@test "A removes earlier run dirs (a symlinked one as a link only) and starts a fresh 700 dir" {
    local gd outside
    gd=$(git rev-parse --absolute-git-dir); outside="${SCRIPT_DIR}/outside"
    mkdir -p "$gd/sdm-old" "$outside"
    echo "[LOW] stale" > "$gd/sdm-old/reviewer-notes.md"
    echo keep > "$outside/keep.txt"
    ln -s "$outside" "$gd/sdm-link"
    run fresh SLUG=old bash "$(blk stage-a-preflight)"
    [ "$status" -eq 0 ]
    [ ! -e "$gd/sdm-old/reviewer-notes.md" ]
    [ ! -L "$gd/sdm-link" ]
    [ "$(cat "$outside/keep.txt")" = keep ]
    [ "$(stat -c %a "$gd/sdm-old")" = 700 ]
}

@test "A refuses a SLUG that is not a plain name" {
    run fresh SLUG="../escape" bash "$(blk stage-a-preflight)"
    [ "$status" -eq 1 ]
    [[ "$output" == *"ABORT: SLUG"* ]]
    [ ! -e "$(git rev-parse --absolute-git-dir)/escape" ]
}

@test "G3 refuses a non-numeric PR_NUM before calling gh" {
    seed_g; put PR_NUM "--repo=evil/x"
    run fresh bash "$(blk stage-g3-merge)"
    [ "$status" -eq 1 ]
    [[ "$output" == *"ABORT: Stage G3: PR_NUM"* ]]
    run grep -c 'pr merge' "$CLI_LOG"
    [ "$output" = 0 ]
}

@test "G2 refuses a non-numeric PR_NUM" {
    seed_g; put PR_NUM "12a"
    run fresh bash "$(blk stage-g2-poll)"
    [ "$status" -eq 1 ]
    [[ "$output" == *"ABORT: Stage G2: PR_NUM"* ]]
}

@test "G4 stops when no successful merge was recorded" {
    seed_g
    run fresh bash "$(blk stage-g4-cleanup)"
    [ "$status" -eq 1 ]
    [[ "$output" == *"ABORT: Stage G4: no successful merge recorded"* ]]
    [ "$(git branch --show-current)" = feature ]
}

# --- Static contract over the skill text ---------------------------------------

@test "only sdm_save and Stage A's rm -f touch the state file" {
    local writes
    writes=$(grep -rnE '>>? *"?\$SDM_STATE' "$SKILL_DIR")
    [ -n "$writes" ]
    run grep -vc 'sdm_save()' <<<"$writes"
    [ "$output" = 0 ]
    run grep -rnE 'rm -f[^|;]*SDM_STATE' "$SKILL_DIR"
    [ "${#lines[@]}" -eq 1 ]
}

@test "every stage block names the state file; the loader is identical in every block but A" {
    local b ref
    [[ " ${BLOCKS[*]} " == *" stage-a-preflight "* && " ${BLOCKS[*]} " == *" stage-g4-cleanup "* ]]
    for b in "${BLOCKS[@]}"; do
        grep -q 'sole-dev-merge.env' "$(blk "$b")" || { echo "no state file in $b"; return 1; }
    done
    run grep -c 'sdm_load' "$(blk stage-a-preflight)"
    [ "$output" = 0 ]
    ref=$(sed -n '/^SDM_STATE=/,/^sdm_save()/p' "$(blk stage-g1-protect)")
    [ -n "$ref" ]
    for b in "${BLOCKS[@]}"; do
        [[ "$b" == stage-a-preflight ]] && continue
        [ "$(sed -n '/^SDM_STATE=/,/^sdm_save()/p' "$(blk "$b")")" = "$ref" ] \
            || { echo "loader differs in $b"; return 1; }
    done
}

@test "Stage A's sdm_save is the loader's sdm_save" {
    [ "$(grep '^sdm_save()' "$(blk stage-a-preflight)")" = "$(grep '^sdm_save()' "$(blk stage-g1-protect)")" ]
}

@test "no masking defaults, /tmp run files or eval remain in the skill" {
    run grep -rnE 'SLUG.*date \+%s|PR_NUM:-0|ORIGINAL_BRANCH:-feature|SLUG:-NOSLUG' "$SKILL_DIR"
    [ "$status" -eq 1 ]
    run grep -rn '/tmp/sole-dev-merge' "$SKILL_DIR"
    [ "$status" -eq 1 ]
    run bash -c "grep -rn 'eval' '$SKILL_DIR' | grep sdm"
    [ "$status" -eq 1 ]
}

# --- sole-dev-merge-fixes M4: E1 → E2 counts, required REMOTE_CHOICE, per-run body ---

@test "E2 in a fresh empty shell reads E1's remote counts from the state file" {
    git remote add gh https://github.com/test/repo.git   # why: origin is a local bare repo (n_other)
    fresh bash "$(blk stage-a-preflight)" >/dev/null
    run fresh bash "$(blk stage-e1-remote)"
    [ "$status" -eq 0 ]
    [ "$(get n_github)" = 1 ]
    [ "$(get n_gitlab)" = 0 ]
    [ "$(get n_other)" = 1 ]
    run fresh bash "$(blk stage-e2-choice)"
    [ "$status" -eq 0 ]
    [ "$(get REMOTE_CHOICE)" = github ]
}

@test "E2 with no remote counts in env or file names Stage E1 instead of a misleading remote ABORT" {
    fresh bash "$(blk stage-a-preflight)" >/dev/null
    run fresh bash "$(blk stage-e2-choice)"
    [ "$status" -ne 0 ]
    [[ "$output" == *"Stage E1"* ]]
    [[ "$output" != *"only github.com and gitlab.com"* ]]
}

@test "E0, F, G1, G2 and G3 refuse to run with no REMOTE_CHOICE, before calling gh or glab" {
    # why: a defaulted github on a refused or missing state file would act on the wrong host (L-055)
    fresh bash "$(blk stage-a-preflight)" >/dev/null
    local body; body="$(get SDM_DIR)/body.md"
    echo "## Test plan" > "$body"
    put PR_BODY_FILE "$body"; put PR_NUM 42; put PR_URL "https://github.com/test/repo/pull/42"
    put MERGE_STRATEGY rebase; put CI_STATE green
    local b
    for b in stage-e0-auth stage-f-push stage-g1-protect stage-g2-poll stage-g3-merge; do
        : > "$CLI_LOG"
        run fresh bash "$(blk "$b")"
        echo "--- $b (status $status): $output"
        [ "$status" -ne 0 ]
        [[ "$output" == *"REMOTE_CHOICE"* ]]
        run grep -cE '^(gh|glab) ' "$CLI_LOG"
        [ "$output" = 0 ]
    done
}

@test "no REMOTE_CHOICE default remains outside E2's dual-remote prompt" {
    # why: E2's prompt default is the operator's pre-answer; anywhere else a default masks a refused state file (L-055)
    [ "$(grep -rho 'REMOTE_CHOICE:-' "$SKILL_DIR" | wc -l)" -eq 1 ]
    [ "$(grep -c 'REMOTE_CHOICE:-github' "$(blk stage-e2-choice)")" -eq 1 ]
}

@test "F posts this run's body (PR_BODY_FILE), never a stale body.md from another run's dir" {
    fresh bash "$(blk stage-a-preflight)" >/dev/null
    local stale; stale="$(git rev-parse --absolute-git-dir)/sdm-stale"
    mkdir -m 700 "$stale" && echo STALE > "$stale/body.md"
    fresh bash "$(blk stage-e3-body)" >/dev/null
    put REMOTE_CHOICE github
    run fresh GH_PR_EXISTS=1 bash "$(blk stage-f-push)"
    [ "$status" -eq 0 ]
    [ "$(get PR_BODY_FILE)" = "$(get SDM_DIR)/body.md" ]
    cmp "$(get PR_BODY_FILE)" "${CLI_LOG}.body"
    run grep -c STALE "${CLI_LOG}.body"
    [ "$output" = 0 ]
}

@test "E2 refuses a remote count that is not a number and never evaluates it (state file or env)" {
    # why: (( n_github == 0 )) re-evaluates the value; BASH_VERSINFO[$(cmd)0] ran cmd (§6.8 SEC-1 probe)
    fresh bash "$(blk stage-a-preflight)" >/dev/null
    local pwned="${SCRIPT_DIR}/pwned" payload
    payload="BASH_VERSINFO[\$(touch ${SCRIPT_DIR}/pwned)0]"
    put n_github "$payload"; put n_gitlab 0; put n_other 0
    run fresh bash "$(blk stage-e2-choice)"
    [ "$status" -ne 0 ]
    [[ "$output" == *"ABORT: Stage E2: n_github"*"is not a count"* ]]
    [ ! -e "$pwned" ]
    run fresh n_github="$payload" n_gitlab=0 bash "$(blk stage-e2-choice)"
    [ "$status" -ne 0 ]
    [ ! -e "$pwned" ]
}

@test "the exit-status table names every STATUS/ABORT token the skill prints" {
    # why: the table drifted by ~10 rows before M4 (§6.8 FP-1)
    local table missing
    table=$(awk '/^## Exit-status contract/,/^Non-zero exits/' "$COMMAND_MD" | grep '^|')
    [ -n "$table" ]
    # why: ABORT messages are mixed case; one or two leading words name each (live run 1 C1 MEDIUM)
    local tok='STATUS: [A-Z_]+|ABORT: [A-Za-z_.]+( [A-Za-z0-9-]+)?'
    missing=$(comm -23 <(grep -rhoE "$tok" "$SKILL_DIR" | sort -u) \
                       <(grep -oE "$tok" <<<"$table" | sort -u))
    echo "missing from the table: ${missing:-none}"
    [ -z "$missing" ]
}

@test "ADR-0008's stage table names exactly the skill's block markers" {
    local adr="${REPO_ROOT}/docs/adr/0008-sole-dev-merge-pr-workflow.md"
    run diff <(sed -n '/^| Stage | Block/,/^$/p' "$adr" | grep -oE '`stage-[a-z0-9-]+`' | tr -d '`' | sort -u) \
             <(grep -rhoE '=== stage-[a-z0-9-]+ \(BEGIN\)' "$SKILL_DIR" | sed -E 's/^=== (stage-[a-z0-9-]+) .*/\1/' | sort -u)
    echo "$output"
    [ "$status" -eq 0 ]
}

@test "E1 without Stage A stops and writes no state file" {
    # why: live run 1 C1 LOW — E1 alone created a branchless state file that E2 then ignored
    run fresh bash "$(blk stage-e1-remote)"
    [ "$status" -ne 0 ]
    [[ "$output" == *"Stage E1 needs SDM_DIR from Stage A"* ]]
    [ ! -e "$(state)" ]
}
