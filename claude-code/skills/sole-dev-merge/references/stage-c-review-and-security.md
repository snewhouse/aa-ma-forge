# Stage C: code review and 3-source security pass — the parallel code-reviewer and security-auditor dispatch, Ruff S and ShellCheck, and the findings aggregation.

## Contents

  - [Stage C — Code review + 3-source security pass](#stage-c--code-review--3-source-security-pass)

### Stage C — Code review + 3-source security pass

Four parallel sources, all writing severity-tagged findings to
`$SDM_DIR/{review,security}.md` and `$SDM_DIR/{ruff,shellcheck}.json`
following the explicit `[CRITICAL]|[HIGH]|[MEDIUM]|[LOW]` contract from
reference.md. `SDM_DIR` is this run's private directory (mode 700), made by
Stage A and printed on its `Stage state:` line.

**Step 1 — Dispatch in parallel (instructions to Claude executor):**

1. Take `SDM_DIR` from Stage A's `Stage state: … (run dir <SDM_DIR>)` line.
   The aggregator below reads it from the stage state file itself.
2. Dispatch **C1** and **C2** in a SINGLE message with two `Agent` tool calls:
   - **C1** — `feature-dev:code-reviewer` agent (fallback: `code-reviewer`).
     Prompt: review `git diff ${BASE_REF}...HEAD`. Emit findings using
     EXACTLY the severity-prefix contract:
     `[CRITICAL]|[HIGH]|[MEDIUM]|[LOW] <one-line> — <path>:<line>`. Write
     output to `$SDM_DIR/review.md`.
   - **C2** — `security-auditor` agent (`~/.claude/agents/security-auditor.md`).
     Same severity contract; output to `$SDM_DIR/security.md`.
     Focus: input validation, auth/secrets, command injection, path traversal,
     hardcoded creds, OWASP top-10.

**Step 2 — C3 (Ruff S) + C4 (ShellCheck) + aggregation (single bash block):**

```bash
# === stage-c-aggregate (BEGIN) ===
set -euo pipefail

# Stage state: load what earlier stages saved (SKILL.md "State between stages").
SDM_STATE="$(git rev-parse --absolute-git-dir)/sole-dev-merge.env"   # why: absolute, so a later cd can't break sdm_save
SDM_KEYS=" ORIGINAL_BRANCH BASE_REF DEFAULT_BRANCH SLUG SDM_DIR CHANGED_FILES CHANGED_PY CHANGED_SH REMOTE_CHOICE PR_BODY_FILE PR_NUM PR_URL MERGE_STRATEGY CI_STATE MERGE_DISPATCHED n_github n_gitlab n_other "
sdm_load() {
    # why: a planted or shared file must never be read: symlink, other owner, or group/world-writable → refuse
    if [[ -L "$SDM_STATE" || ! -O "$SDM_STATE" || -n "$(find "$SDM_STATE" \( -perm -g+w -o -perm -o+w \) -print)" ]]; then
        echo "Stage state: refusing ${SDM_STATE##*/} (symlink, not owned by you, or writable by others)"; return 0
    fi
    local line k v dv
    declare -A _sdm=()
    while IFS= read -r line; do
        k=${line%%=*}; v=${line#*=}
        [[ "$SDM_KEYS" == *" $k "* ]] || { echo "Stage state: ignoring unknown key '$k'"; continue; }   # why: allowlist, never a free-form name
        # why: decode into a temp first, so a bad line never overwrites an earlier good value
        dv=$(printf '%s' "$v" | base64 -d 2>/dev/null) || { echo "Stage state: bad value for $k — ignored"; continue; }
        _sdm[$k]=$dv                                   # why: last good write wins
    done < "$SDM_STATE"
    # why: a missing or empty ORIGINAL_BRANCH counts as foreign (on a detached HEAD '' would equal '')
    if [[ -z "${_sdm[ORIGINAL_BRANCH]:-}" || "${_sdm[ORIGINAL_BRANCH]}" != "$(git branch --show-current)" ]]; then
        echo "Stage state: ${SDM_STATE##*/} is not for this branch — ignored (run Stage A first)"; return 0
    fi
    for k in "${!_sdm[@]}"; do
        [[ -n "${!k:-}" ]] || printf -v "$k" '%s' "${_sdm[$k]}"   # why: a non-empty explicit env wins; a value is assigned, never executed
    done
}
[[ -f "$SDM_STATE" ]] && sdm_load
sdm_save() { if [[ -L "$SDM_STATE" ]] || { [[ -e "$SDM_STATE" ]] && { [[ ! -O "$SDM_STATE" ]] || [[ -n "$(find "$SDM_STATE" \( -perm -g+w -o -perm -o+w \) -print)" ]]; }; }; then echo "Stage state: refusing to save $1 (${SDM_STATE##*/} is a symlink, not yours, or writable by others)"; return 1; fi; (umask 077; printf '%s=%s\n' "$1" "$(printf '%s' "$2" | base64 | tr -d '\n')" >> "$SDM_STATE"); }   # why: refuse exactly what the loader refuses, and create the file 600; base64 has no shell metacharacters, tr keeps one line

: "${SDM_DIR:?Stage C needs SDM_DIR from Stage A}"
REVIEW_OUT="$SDM_DIR/review.md"
SECURITY_OUT="$SDM_DIR/security.md"
RUFF_OUT="$SDM_DIR/ruff.json"
SHELLCHECK_OUT="$SDM_DIR/shellcheck.json"
FINDINGS="$SDM_DIR/findings.md"

: > "$FINDINGS"  # truncate / create

# The file counts the scanners below receive, so a reader can tell "scanned,
# clean" from "nothing to scan" (sole-dev-merge-fixes 2.3 live check).
N_PY=$(grep -c . <<<"${CHANGED_PY:-}" || true)
N_SH=$(grep -c . <<<"${CHANGED_SH:-}" || true)
echo "Stage C scanned: Ruff S ${N_PY} file(s), ShellCheck ${N_SH} file(s)"

# === CANONICAL severity-mapping tables (single source-of-truth) ===
# These JSON literals are the AUTHORITATIVE mapping for unifying Ruff S and
# ShellCheck findings into the [CRITICAL]/[HIGH]/[MEDIUM]/[LOW] contract.
# The table below this block mirrors them for human consumption; the runtime
# source is HERE. When Ruff adds an S rule or ShellCheck a severity tier,
# update these two literals AND the mirrored table in the SAME commit.
#
# Ruff reports no per-rule severity, so RUFF_SEV_JSON maps each S code to the
# tier its legacy counterpart check (Snnn <-> Bnnn, the scanner retired by the
# M8 ruff-only decision) carried by default under the old mapping:
# HIGH -> CRITICAL, MEDIUM -> HIGH, LOW -> MEDIUM.
# A code absent from the map is reported [HIGH]: an unknown rule fails
# conservative, never quietly LOW.
export RUFF_SEV_JSON='{
  "S201": "CRITICAL", "S202": "CRITICAL", "S324": "CRITICAL", "S413": "CRITICAL",
  "S501": "CRITICAL", "S502": "CRITICAL", "S507": "CRITICAL", "S602": "CRITICAL",
  "S605": "CRITICAL", "S609": "CRITICAL", "S701": "CRITICAL",
  "S102": "HIGH", "S103": "HIGH", "S104": "HIGH", "S108": "HIGH", "S113": "HIGH",
  "S301": "HIGH", "S302": "HIGH", "S303": "HIGH", "S304": "HIGH", "S305": "HIGH",
  "S306": "HIGH", "S307": "HIGH", "S308": "HIGH", "S310": "HIGH", "S312": "HIGH",
  "S313": "HIGH", "S314": "HIGH", "S315": "HIGH", "S316": "HIGH", "S317": "HIGH",
  "S318": "HIGH", "S319": "HIGH", "S320": "HIGH", "S321": "HIGH", "S323": "HIGH",
  "S503": "HIGH", "S505": "HIGH", "S506": "HIGH", "S508": "HIGH", "S509": "HIGH",
  "S601": "HIGH", "S604": "HIGH", "S608": "HIGH", "S610": "HIGH", "S611": "HIGH",
  "S612": "HIGH", "S702": "HIGH", "S704": "HIGH",
  "S101": "MEDIUM", "S105": "MEDIUM", "S106": "MEDIUM", "S107": "MEDIUM",
  "S110": "MEDIUM", "S112": "MEDIUM", "S311": "MEDIUM", "S401": "MEDIUM",
  "S402": "MEDIUM", "S403": "MEDIUM", "S404": "MEDIUM", "S405": "MEDIUM",
  "S406": "MEDIUM", "S407": "MEDIUM", "S408": "MEDIUM", "S409": "MEDIUM",
  "S411": "MEDIUM", "S412": "MEDIUM", "S415": "MEDIUM", "S504": "MEDIUM",
  "S603": "MEDIUM", "S606": "MEDIUM", "S607": "MEDIUM"
}'
export SHELLCHECK_SEV_JSON='{"error": "CRITICAL", "warning": "HIGH", "info": "MEDIUM", "style": "LOW"}'
# === END canonical severity-mapping tables ===

SEVERITY_RE='^\[(CRITICAL|HIGH|MEDIUM|LOW)\][[:space:]]+'

# parse_agent_file: append contract-conforming lines from agent output.
# Safe-default per plan §M2 risk #1: if file has content but ZERO lines match
# the contract, classify ALL content as [HIGH] (forces user review) and log
# the parse failure to stdout.
parse_agent_file() {
    local file="$1" source_name="$2"
    [[ ! -s "$file" ]] && return 0
    if grep -qE "$SEVERITY_RE" "$file"; then
        grep -E "$SEVERITY_RE" "$file" >> "$FINDINGS"
    else
        echo "Stage C: parse failure on $source_name — applying safe-default [HIGH]"
        while IFS= read -r line; do
            [[ -z "$line" ]] && continue
            echo "[HIGH]     ${line} — (parse-failure: $source_name)" >> "$FINDINGS"
        done < "$file"
    fi
}

# C1 — code-reviewer agent output
parse_agent_file "$REVIEW_OUT" "code-reviewer"

# C2 — security-auditor agent output
parse_agent_file "$SECURITY_OUT" "security-auditor"

# C3 — Ruff S (security rules) on changed Python (only if any)
#
# Same contract as C4 below, and if anything this one matters more: $RUFF_OUT
# is the trusted input driving Stage D's S602 auto-remediation, so a missing
# scanner would silently disable detection AND fixing. Not --isolated: the
# repo's per-file-ignores and `# noqa` apply here as for any lint run.
# Ruff exits 0 (clean) or 1 (findings); 2 or above, or an empty report, means
# it did not run. A clean run still writes `[]`, so `-s` means "report exists".
# RUFF_BIN is a seam for testing that degraded path.
RUFF_BIN="${RUFF_BIN:-ruff}"
if [[ -n "${CHANGED_PY:-}" ]]; then
    RUFF_RC=0
    mapfile -t PY_FILES <<< "$CHANGED_PY"
    # why: one argument per name, after '--', so '-x.py' or 'a b.py' is a file, never a flag or two words
    "$RUFF_BIN" check --select S --output-format json -- "${PY_FILES[@]}" > "$RUFF_OUT" 2>/dev/null || RUFF_RC=$?
    if [[ "$RUFF_RC" -gt 1 || ! -s "$RUFF_OUT" ]]; then
        echo "Stage C: WARNING — '${RUFF_BIN}' produced no report" \
             "(rc=${RUFF_RC}); Python findings are UNKNOWN, not zero."
        echo "[HIGH]     C3 NOT RUN — '${RUFF_BIN}' unavailable or produced no report (rc=${RUFF_RC}); Python findings UNKNOWN — (scanner-unavailable)" >> "$FINDINGS"
    else
        # Severity mapping loaded from $RUFF_SEV_JSON (canonical above).
        python3 - "$RUFF_OUT" >> "$FINDINGS" <<'PY' || true
import json, os, sys
try:
    with open(sys.argv[1]) as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError("Ruff JSON report is not a list")
except (json.JSONDecodeError, FileNotFoundError, ValueError):
    # stdout is appended to $FINDINGS — see the matching note in C4.
    print("[HIGH]     C3 REPORT UNPARSEABLE — scanner output was not valid JSON;"
          " Python findings UNKNOWN — (scanner-output-unparseable)")
    sys.exit(0)
sev_map = json.loads(os.environ["RUFF_SEV_JSON"])
for r in data:
    code = r.get("code") or "?"
    sev = sev_map.get(code, "HIGH")  # unmapped rule: fail conservative
    msg = r.get("message", "(no msg)")
    path = r.get("filename", "?")
    line = (r.get("location") or {}).get("row", 0)
    print(f"[{sev}]     {code} {msg} — {path}:{line}")
PY
    fi
fi

# C4 — ShellCheck on changed shell (only if any)
#
# A scanner that did not run must never be reported as a scanner that found
# nothing: the second is a clean bill of health on shell nobody reviewed.
#
# Test the REPORT, not the binary. `command -v` answers "is something on PATH",
# which is a different question — `true`, `:` and a present-but-broken install
# all resolve and all leave an empty report. ShellCheck exits 0 (clean) or 1
# (findings); anything above 1, or an empty report, means it did not run.
#
# SHELLCHECK_BIN is a seam for testing that degraded path without uninstalling
# anything.
SHELLCHECK_BIN="${SHELLCHECK_BIN:-shellcheck}"
if [[ -n "${CHANGED_SH:-}" ]]; then
    SHELLCHECK_RC=0
    mapfile -t SH_FILES <<< "$CHANGED_SH"
    # why: one argument per name, after '--' (probed: shellcheck keeps the name unprefixed in its report)
    "$SHELLCHECK_BIN" -f json -- "${SH_FILES[@]}" > "$SHELLCHECK_OUT" 2>/dev/null \
        || SHELLCHECK_RC=$?
    if [[ "$SHELLCHECK_RC" -gt 1 || ! -s "$SHELLCHECK_OUT" ]]; then
        # Safe-default, same contract parse_agent_file uses above: the degraded
        # state is written INTO $FINDINGS, not merely echoed. Stage D reads
        # $FINDINGS and nothing else, so a stdout-only warning would leave the
        # machine-readable verdict byte-identical to a clean scan and let the
        # gate advance on unscanned shell.
        echo "Stage C: WARNING — '${SHELLCHECK_BIN}' produced no report" \
             "(rc=${SHELLCHECK_RC}); shell findings are UNKNOWN, not zero."
        echo "[HIGH]     C4 NOT RUN — '${SHELLCHECK_BIN}' unavailable or produced no report (rc=${SHELLCHECK_RC}); shell findings UNKNOWN — (scanner-unavailable)" >> "$FINDINGS"
    else
        # Severity mapping loaded from $SHELLCHECK_SEV_JSON (canonical above).
        python3 - "$SHELLCHECK_OUT" >> "$FINDINGS" <<'PY' || true
import json, os, sys
try:
    with open(sys.argv[1]) as f:
        data = json.load(f)
except (json.JSONDecodeError, FileNotFoundError):
    # stdout is appended to $FINDINGS. A half-written or non-JSON report is
    # evidence the scanner died, not evidence the code is clean — exiting
    # quietly here was the last path by which C4 could report zero without
    # having run.
    print("[HIGH]     C4 REPORT UNPARSEABLE — scanner output was not valid JSON;"
          " shell findings UNKNOWN — (scanner-output-unparseable)")
    sys.exit(0)
sev_map = json.loads(os.environ["SHELLCHECK_SEV_JSON"])
items = data if isinstance(data, list) else data.get("comments", [])
for r in items:
    sev = sev_map.get(r.get("level", ""), "LOW")
    msg = r.get("message", "(no msg)")
    path = r.get("file", "?")
    line = r.get("line", 0)
    code = r.get("code", 0)
    print(f"[{sev}]     SC{code} {msg} — {path}:{line}")
PY
    fi
fi

TOTAL=$(grep -cE "^\[(CRITICAL|HIGH|MEDIUM|LOW)\]" "$FINDINGS" || true)
echo "Stage C aggregate: ${TOTAL} findings → $FINDINGS"
# === stage-c-aggregate (END) ===
```

**C3 severity table** (mirror of `RUFF_SEV_JSON` above; change both in the
same commit). Each tier is the default severity of the matching legacy
`Bnnn` check under the mapping it replaces (HIGH→CRITICAL, MEDIUM→HIGH,
LOW→MEDIUM).

| Contract severity | Ruff S codes |
|---|---|
| `[CRITICAL]` | S201 S202 S324 S413 S501 S502 S507 S602 S605 S609 S701 |
| `[HIGH]` | S102 S103 S104 S108 S113 S301 S302 S303 S304 S305 S306 S307 S308 S310 S312 S313 S314 S315 S316 S317 S318 S319 S320 S321 S323 S503 S505 S506 S508 S509 S601 S604 S608 S610 S611 S612 S702 S704 |
| `[MEDIUM]` | S101 S105 S106 S107 S110 S112 S311 S401 S402 S403 S404 S405 S406 S407 S408 S409 S411 S412 S415 S504 S603 S606 S607 |
| `[HIGH]` (default) | any code not listed — an unknown rule fails conservative |

Line format: `[SEV]     <code> <message> — <file>:<row>`.
