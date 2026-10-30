#!/usr/bin/env bash
# scan-untrusted.sh — security-scan a range of commits the operator did not write.
#
#   scan-untrusted.sh --base <trusted ref> [--head <ref>] <repo>
#
# The base (e.g. main) is trusted; every commit in base..head is not. A scanned repo controls
# its scanner config, ignore files, inline suppressions, file names, attributes and history,
# so this script never lets any of them decide what is scanned:
#   - gitleaks reads every blob version the range introduces (git rev-list --objects), each
#     written under its blob id: commits added then reverted are seen, .gitattributes is never
#     applied, and the default path allowlist never matches. -i points at that empty dir, so
#     no .gitleaksignore applies, and there is no repo .gitleaks.toml to load.
#   - Ruff, ShellCheck and osv-scanner run on the head version of each changed file, passed
#     by name after `--`, with Ruff --isolated --ignore-noqa, ShellCheck --norc and
#     osv-scanner --config <empty>. Files are chosen by extension or shebang.
#   - Inline suppressions (in the head version of each scanned file, and gitleaks:allow in
#     every blob of the range) and changed scanner config files are SUPPRESSOR lines. No flag
#     turns off a `# shellcheck …` directive, so those are blanked in the copies before ShellCheck.
#
# Output (stdout), one line each: FINDING <scanner> <path>[:<line>] <rule> …,
# SUPPRESSOR <path>[:<line>] <marker>, UNKNOWN <scanner> <reason>; last line
# `scan-untrusted: findings=N suppressors=M unknown=K`. Secrets are redacted.
# Exit: 0 clean, 1 findings or suppressors, 2 usage or git error, 3 a scanner could not run.
# Env: RUFF_BIN, SHELLCHECK_BIN, GITLEAKS_BIN, OSV_SCANNER_BIN (operator-trusted; defaults
# on PATH). Needs git and jq.

set -Eeuo pipefail
# Any unexpected failure is exit 2 with its line, never a silent death or an undocumented code.
trap 'echo "scan-untrusted: failed at line ${LINENO}: ${BASH_COMMAND}" >&2; exit 2' ERR
# why: byte-wise matching everywhere, so an invalid UTF-8 byte cannot make grep, sed and
# [[ =~ ]] disagree about a line (e.g. reported as a directive but not blanked).
export LC_ALL=C

RUFF_BIN="${RUFF_BIN:-ruff}"
SHELLCHECK_BIN="${SHELLCHECK_BIN:-shellcheck}"
GITLEAKS_BIN="${GITLEAKS_BIN:-gitleaks}"
OSV_SCANNER_BIN="${OSV_SCANNER_BIN:-osv-scanner}"

usage() { echo "usage: scan-untrusted.sh --base <ref> [--head <ref>] <repo>" >&2; exit 2; }

base="" head="HEAD" repo=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        --base) [[ $# -ge 2 ]] || usage; base="$2"; shift 2 ;;
        --head) [[ $# -ge 2 ]] || usage; head="$2"; shift 2 ;;
        -h|--help) usage ;;
        -*) echo "scan-untrusted: unknown option $1" >&2; usage ;;
        *) [[ -z "${repo}" ]] || usage; repo="$1"; shift ;;
    esac
done
[[ -n "${base}" && -n "${repo}" ]] || usage

g() { git -C "${repo}" "$@"; }
resolve() {
    local sha
    # why: stderr dropped — the failure is reported on the next line with the ref named
    if ! sha=$(git -C "${repo}" rev-parse --verify --quiet --end-of-options "$1^{commit}" 2>/dev/null); then
        echo "scan-untrusted: not a commit in ${repo}: $1" >&2; exit 2
    fi
    printf '%s\n' "${sha}"
}
base_sha=$(resolve "${base}")
head_sha=$(resolve "${head}")

work=""
trap 'if [[ -n "${work}" ]]; then rm -rf -- "${work}"; fi' EXIT
work=$(mktemp -d "${TMPDIR:-/tmp}/scan-untrusted.XXXXXX")
mkdir "${work}/blobs" "${work}/tree"
: > "${work}/osv.toml"

findings=0 suppressors=0 unknown=0
finding()    { printf 'FINDING %s\n' "$*"; findings=$((findings + 1)); }
suppressor() { printf 'SUPPRESSOR %s\n' "$*"; suppressors=$((suppressors + 1)); }
unknown()    { printf 'UNKNOWN %s\n' "$*"; unknown=$((unknown + 1)); }

# Resolve a symlink's target against its own directory; prints nothing if it leaves the repo.
link_target() {
    local dir="" part
    local -a parts=() stack=()
    [[ "$1" != */* ]] || dir="${1%/*}/"
    [[ "$2" != /* ]] || return 0
    IFS=/ read -r -a parts <<<"${dir}$2"
    for part in "${parts[@]}"; do
        case "${part}" in
            ''|.) ;;
            ..) [[ ${#stack[@]} -gt 0 ]] || return 0; unset 'stack[-1]' ;;
            *) stack+=("${part}") ;;
        esac
    done
    [[ ${#stack[@]} -eq 0 ]] || (IFS=/; printf '%s\n' "${stack[*]}")
}

# --- changed files at head: write each by name under tree/ --------------------------------
# A symlink is written under its own name with its target's content, so it is classified by
# the name an importer or caller uses. Producers write to files first: a git error inside a
# process substitution would otherwise be ignored and read as an empty, clean range.
git -C "${repo}" diff-tree -r -z --no-renames --diff-filter=AMT "${base_sha}" "${head_sha}" > "${work}/changed.z" \
    || { echo "scan-untrusted: git diff-tree failed" >&2; exit 2; }
declare -a changed=()
while IFS= read -r -d '' meta && IFS= read -r -d '' path; do
    read -r _ mode _ blob _ <<<"${meta#:}"
    if [[ "${path}" == *[[:cntrl:]]* ]]; then
        unknown "path with control characters not scanned: $(printf '%q' "${path}")"; continue
    fi
    case "/${path}/" in */../*|*/./*) echo "scan-untrusted: refusing path ${path}" >&2; exit 2 ;; esac
    if [[ "${mode}" == 120000 ]]; then
        target=$(g cat-file blob "${blob}")
        resolved=$(link_target "${path}" "${target}")
        if [[ -z "${resolved}" ]]; then
            unknown "symlink ${path} -> $(printf '%q' "${target}") points outside the repo"; continue
        fi
        entry=""
        IFS= read -r -d '' entry < <(git --literal-pathspecs -C "${repo}" ls-tree -z "${head_sha}" -- "${resolved}") || true  # why: no entry means the target is missing; handled next
        if [[ "${entry}" != 100* ]]; then
            unknown "symlink ${path} -> $(printf '%q' "${target}") is not a regular file at head"; continue
        fi
        read -r _ _ blob <<<"${entry%%$'\t'*}"
    elif [[ "${mode}" != 100* ]]; then
        continue                                   # submodules: no content in this repo
    fi
    mkdir -p -- "${work}/tree/$(dirname -- "${path}")"
    g cat-file blob "${blob}" > "${work}/tree/${path}"
    changed+=("${path}")
done < "${work}/changed.z"

# First line, NUL bytes dropped (binary files), control characters shown as ?.
shebang() {
    local first
    # why: no early-closing reader in the pipe (head -n 1 would SIGPIPE tr under pipefail)
    first=$(head -c 256 -- "${work}/tree/$1" | tr -d '\0')
    printf '%s\n' "${first%%$'\n'*}"
}
declare -a py=() sh=() locks=()
for path in "${changed[@]}"; do
    name="${path##*/}"
    case "${name}" in
        package-lock.json|pnpm-lock.yaml|yarn.lock|bun.lock|renv.lock|go.mod|Cargo.lock|pom.xml|gradle.lockfile|Gemfile.lock|composer.lock|packages.lock.json)
            locks+=("${path}"); continue ;;
        uv.lock|poetry.lock|Pipfile.lock|requirements*.txt)
            unknown "pip-audit ${path} (run the table's hashed pip-audit command on the operator's export)"; continue ;;
        .gitleaksignore|.gitleaks.toml|.gitattributes|.shellcheckrc|osv-scanner.toml|pyproject.toml|ruff.toml|.ruff.toml)
            suppressor "${path} scanner config changed" ;;
    esac
    case "${name}" in
        *.py|*.pyi) py+=("${path}"); continue ;;
        *.sh|*.bash|*.ksh|*.dash|*.bats) sh+=("${path}"); continue ;;
        *.ipynb|*.pth) unknown "not scanned ${path} (no scanner reads this type)"; continue ;;
    esac
    first=$(shebang "${path}")
    if [[ "${first}" =~ ^#!.*(python|pypy|uv[[:space:]]+run) ]]; then py+=("${path}")
    elif [[ "${first}" =~ ^#!.*(/|[[:space:]])(sh|bash|dash|ksh|bats)([[:space:]]|$) ]]; then sh+=("${path}")
    elif [[ "${first}" == '#!'* ]]; then unknown "not scanned ${path} (${first//[[:cntrl:]]/?})"
    fi
done

# --- inline suppressions --------------------------------------------------------------------
# Each marker counts where its scanner reads it, in the whole head version of the file (a
# directive already on the base still covers new lines): Ruff markers in the files sent to
# Ruff, ShellCheck's in those sent to ShellCheck. ShellCheck directives are then blanked in
# the copies, since no flag turns them off. gitleaks:allow is checked in every blob below.
py_re='(noqa|ruff:[[:space:]]*(noqa|disable)|nosec)'
# Any directive (`# shellcheck key=value …`): one directive can carry several keys.
sh_re='#[[:space:]]*shellcheck[[:space:]]+[a-z-]+='
for path in "${py[@]}"; do
    while IFS=: read -r n text; do
        [[ "${text}" =~ ${py_re} ]] || continue
        m="${BASH_REMATCH[1]}"; [[ "${m}" == ruff:* ]] && m="ruff directive"
        suppressor "${path}:${n} ${m}"
    done < <(grep -a -n -E -- "${py_re}" "${work}/tree/${path}" || true)  # why: grep exits 1 when a file has no marker
done
for path in "${sh[@]}"; do
    while IFS=: read -r n _; do
        suppressor "${path}:${n} shellcheck directive"
    done < <(grep -a -n -E -- "${sh_re}" "${work}/tree/${path}" || true)  # why: grep exits 1 when a file has no marker
    sed -i -E 's/#[[:space:]]*shellcheck[[:space:]]+[a-z-]+=.*$//' -- "${work}/tree/${path}"
done

# assert (S101) is how tests check things; it is a finding only in shipped code.
RUFF_TEST_ASSERTS="lint.per-file-ignores = {'**/tests/**' = ['S101'], '**/test_*.py' = ['S101'], '**/*_test.py' = ['S101'], '**/conftest.py' = ['S101']}"

# --- Ruff ---------------------------------------------------------------------------------
# JSON, not text lines: a path or message can never split a finding. A file Ruff could not
# decode or parse, or a non-zero exit with nothing parsed, is UNKNOWN, never clean.
if [[ ${#py[@]} -gt 0 ]]; then
    # why: output dropped — a scanner that is not on PATH becomes an UNKNOWN line, never a skip
    if ! command -v -- "${RUFF_BIN}" >/dev/null 2>&1; then unknown "ruff not runnable (${RUFF_BIN})"
    else
        rc=0
        (cd "${work}/tree" && "${RUFF_BIN}" check --isolated --ignore-noqa --no-respect-gitignore \
            --select S --config "${RUFF_TEST_ASSERTS}" --output-format json --no-cache -- "${py[@]}" \
            > "${work}/ruff.json" 2> "${work}/ruff.err") || rc=$?
        # why: jq output dropped — a missing or malformed report is reported as UNKNOWN
        if [[ ${rc} -gt 1 ]] || ! jq -e 'type == "array"' "${work}/ruff.json" >/dev/null 2>&1; then
            unknown "ruff exited ${rc}: $(head -c 200 "${work}/ruff.err")"
        else
            before=$((findings + unknown))
            declare -A unparsed=()
            while IFS=$'\t' read -r file row code msg; do
                file="${file#"${work}/tree/"}"
                if [[ "${code}" == invalid-syntax ]]; then
                    [[ -n "${unparsed[${file}]:-}" ]] || unknown "ruff could not parse ${file}"
                    unparsed["${file}"]=1
                else
                    finding "ruff ${file}:${row} ${code} ${msg}"
                fi
            done < <(jq -r '.[] | [.filename, .location.row, (.code // "invalid-syntax"), .message] | @tsv' "${work}/ruff.json")
            while IFS= read -r line; do
                [[ "${line}" =~ Failed\ to\ lint\ (.+):\  ]] && unknown "ruff could not lint ${BASH_REMATCH[1]}"
            done < "${work}/ruff.err"
            if [[ ${rc} -eq 1 && $((findings + unknown)) -eq ${before} ]]; then unknown "ruff exited 1 with no finding parsed"; fi
        fi
    fi
fi

# --- ShellCheck ---------------------------------------------------------------------------
if [[ ${#sh[@]} -gt 0 ]]; then
    # why: output dropped — a scanner that is not on PATH becomes an UNKNOWN line, never a skip
    if ! command -v -- "${SHELLCHECK_BIN}" >/dev/null 2>&1; then unknown "shellcheck not runnable (${SHELLCHECK_BIN})"
    else
        rc=0
        (cd "${work}/tree" && "${SHELLCHECK_BIN}" --norc --enable=check-set-e-suppressed \
            -f json1 -- "${sh[@]}" > "${work}/sc.json" 2> "${work}/sc.err") || rc=$?
        # why: jq output dropped — a missing or malformed report is reported as UNKNOWN
        if [[ ${rc} -gt 1 ]] || ! jq -e '.comments | type == "array"' "${work}/sc.json" >/dev/null 2>&1; then
            unknown "shellcheck exited ${rc}: $(head -c 200 "${work}/sc.err")"
        else
            before=${findings}
            while IFS=$'\t' read -r file line code msg; do
                finding "shellcheck ${file}:${line} SC${code} ${msg}"
            done < <(jq -r '.comments[] | [.file, .line, .code, .message] | @tsv' "${work}/sc.json")
            if [[ ${rc} -eq 1 && ${findings} -eq ${before} ]]; then unknown "shellcheck exited 1 with no finding parsed"; fi
        fi
    fi
fi

# --- osv-scanner --------------------------------------------------------------------------
for lock in "${locks[@]}"; do
    # why: output dropped — a scanner that is not on PATH becomes an UNKNOWN line, never a skip
    if ! command -v -- "${OSV_SCANNER_BIN}" >/dev/null 2>&1; then unknown "osv-scanner not runnable (${OSV_SCANNER_BIN}) for ${lock}"; continue; fi
    rc=0
    out=$("${OSV_SCANNER_BIN}" scan --config "${work}/osv.toml" --format json \
        -L "${work}/tree/${lock}" 2>"${work}/osv.err") || rc=$?
    # why: jq stderr dropped — unparseable output is reported as UNKNOWN on the next line
    if [[ ${rc} -gt 1 ]] || ! ids=$(jq -r '[.results[]?.packages[]?.vulnerabilities[]?.id] | unique | join(" ")' <<<"${out}" 2>/dev/null); then
        unknown "osv-scanner exited ${rc} for ${lock}: $(head -c 200 "${work}/osv.err")"; continue
    fi
    [[ -z "${ids}" ]] || finding "osv-scanner ${lock} ${ids}"
done

# --- gitleaks: every blob the range introduces, named by blob id ---------------------------
# ponytail: one cat-file per blob; switch to `cat-file --batch` if PR ranges get large.
# ponytail: rev-list prints paths newline-separated, so a path with a newline is misnamed in output.
declare -A blob_path=() allow_seen=()
{ git -C "${repo}" rev-list --objects "${base_sha}..${head_sha}" | git -C "${repo}" cat-file --batch-check='%(objectname) %(objecttype) %(rest)'; } \
    > "${work}/objects.txt" || { echo "scan-untrusted: git rev-list failed" >&2; exit 2; }
while read -r sha type rest; do
    [[ "${type}" == blob ]] || continue
    [[ -n "${blob_path[${sha}]:-}" ]] || blob_path["${sha}"]="${rest}"
    g cat-file blob "${sha}" > "${work}/blobs/${sha}"
    while IFS=: read -r n _; do
        [[ -z "${allow_seen[${rest}:${n}]:-}" ]] || continue   # same line in several versions
        allow_seen["${rest}:${n}"]=1
        suppressor "${rest}:${n} gitleaks:allow"
    done < <(grep -a -n -F -- 'gitleaks:allow' "${work}/blobs/${sha}" || true)  # why: grep exits 1 when a file has no marker
done < "${work}/objects.txt"

if [[ ${#blob_path[@]} -gt 0 ]]; then
    # why: output dropped — a scanner that is not on PATH becomes an UNKNOWN line, never a skip
    if ! command -v -- "${GITLEAKS_BIN}" >/dev/null 2>&1; then unknown "gitleaks not runnable (${GITLEAKS_BIN})"
    else
        rc=0
        (cd "${work}" && "${GITLEAKS_BIN}" detect --no-git --no-banner --redact -s blobs -i blobs \
            --report-format json --report-path report.json --exit-code 0 >/dev/null 2>"${work}/gitleaks.err") || rc=$?
        # why: jq output dropped — a missing or malformed report is reported as UNKNOWN
        if [[ ${rc} -ne 0 ]] || ! jq -e 'type == "array"' "${work}/report.json" >/dev/null 2>&1; then
            unknown "gitleaks exited ${rc}: $(head -c 200 "${work}/gitleaks.err")"
        else
            while IFS=$'\t' read -r file line rule; do
                finding "gitleaks ${blob_path[${file##*/}]:-${file}}:${line} ${rule}"
            done < <(jq -r '.[] | [.File, .StartLine, .RuleID] | @tsv' "${work}/report.json")
        fi
    fi
fi

echo "scan-untrusted: findings=${findings} suppressors=${suppressors} unknown=${unknown}"
if [[ $((findings + suppressors)) -gt 0 ]]; then exit 1; fi
if [[ ${unknown} -gt 0 ]]; then exit 3; fi
exit 0
