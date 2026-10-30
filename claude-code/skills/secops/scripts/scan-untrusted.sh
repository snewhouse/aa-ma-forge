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
# Exit 0 covers Python, shell, the lockfiles osv-scanner reads, and secrets in every blob. Other
# languages (JS/TS, workflow YAML, Dockerfiles, …) are not scanned unless a shebang names them.
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
work=$(cd -- "${work}" && pwd -P)      # physical path: scanners report it, so prefixes match
mkdir "${work}/blobs" "${work}/tree" "${work}/ruff"
: > "${work}/osv.toml"

findings=0 suppressors=0 unknown=0
finding()    { printf 'FINDING %s\n' "$*"; findings=$((findings + 1)); }
suppressor() { printf 'SUPPRESSOR %s\n' "$*"; suppressors=$((suppressors + 1)); }
unknown()    { printf 'UNKNOWN %s\n' "$*"; unknown=$((unknown + 1)); }

# --- head tree lookups and kernel-style symlink resolution ---------------------------------
# lookup <path>: sets L_MODE / L_SHA for that entry at head (empty when there is none).
lookup() {
    local e=""
    # why: || true — no entry (or a failed ls-tree) leaves e empty, which callers treat as missing
    IFS= read -r -d '' e < <(git --literal-pathspecs -C "${repo}" ls-tree -z "${head_sha}" -- "$1") || true
    L_MODE="" L_SHA=""
    [[ -z "${e}" ]] || read -r L_MODE _ L_SHA <<<"${e%%$'\t'*}"
}

# resolve <path>: follows the path one component at a time as the kernel would — a symlink is
# read and spliced in, `..` steps up from the physical directory reached so far. Sets
# R_SHA (the regular file reached) or R_ERR, and R_TOUCH=1 when any entry on the way changed in the range.
declare -A changed_set=()
resolve() {
    local -a todo=() parts=()
    local cur="" comp cand target hops=0
    R_SHA="" R_ERR="" R_TOUCH=0
    IFS=/ read -r -a todo <<<"$1"
    while [[ ${#todo[@]} -gt 0 ]]; do
        comp="${todo[0]}"; todo=("${todo[@]:1}")
        case "${comp}" in
            ''|.) continue ;;
            ..) if [[ -z "${cur}" ]]; then R_ERR="points outside the repo"; return 0; fi
                if [[ "${cur}" == */* ]]; then cur="${cur%/*}"; else cur=""; fi
                continue ;;
        esac
        cand="${cur:+${cur}/}${comp}"
        lookup "${cand}"
        [[ -z "${changed_set[${cand}]:-}" ]] || R_TOUCH=1
        case "${L_MODE}" in
            120000)
                hops=$((hops + 1))
                if [[ ${hops} -gt 40 ]]; then R_ERR="too many levels of symlinks"; return 0; fi
                g cat-file blob "${L_SHA}" > "${work}/link"
                # Counted with tr, not grep: grep is line-based, so it never sees a newline.
                if [[ $(tr -d -c '[:cntrl:]' < "${work}/link" | wc -c) -gt 0 ]]; then
                    R_ERR="target has control characters"; return 0
                fi
                target=$(<"${work}/link")
                if [[ "${target}" == /* ]]; then R_ERR="points outside the repo"; return 0; fi
                IFS=/ read -r -a parts <<<"${target}"
                todo=("${parts[@]}" "${todo[@]}") ;;      # cur stays: the link's own directory
            040000) cur="${cand}"
                    if [[ ${#todo[@]} -eq 0 ]]; then R_ERR="resolves to a directory"; return 0; fi ;;
            100*)   if [[ ${#todo[@]} -gt 0 ]]; then R_ERR="passes through a file"; return 0; fi
                    R_SHA="${L_SHA}"; return 0 ;;
            '')     R_ERR="target missing at head"; return 0 ;;
            *)      R_ERR="resolves to a submodule"; return 0 ;;
        esac
    done
    R_ERR="resolves to a directory"
}

# --- changed files at head: write each by name under tree/ --------------------------------
# A symlink is written under its own name with the content the kernel would open, so it is
# classified by the name an importer or caller uses. A symlink already on the base is handled
# the same way when anything on its route changed. Producers write to files first: a git error
# inside a process substitution would otherwise be ignored and read as an empty, clean range.
git -C "${repo}" diff-tree -r -z --no-renames --diff-filter=AMT "${base_sha}" "${head_sha}" > "${work}/changed.z" \
    || { echo "scan-untrusted: git diff-tree failed" >&2; exit 2; }
declare -a c_path=() c_mode=() c_blob=() changed=()
while IFS= read -r -d '' meta && IFS= read -r -d '' path; do
    read -r _ mode _ blob _ <<<"${meta#:}"
    if [[ "${path}" == *[[:cntrl:]]* ]]; then
        unknown "path with control characters not scanned: $(printf '%q' "${path}")"; continue
    fi
    case "/${path}/" in */../*|*/./*) echo "scan-untrusted: refusing path ${path}" >&2; exit 2 ;; esac
    c_path+=("${path}") c_mode+=("${mode}") c_blob+=("${blob}")
    changed_set["${path}"]=1
done < "${work}/changed.z"

write_tree() { mkdir -p -- "${work}/tree/$(dirname -- "$1")"; g cat-file blob "$2" > "${work}/tree/$1"; changed+=("$1"); }
for i in "${!c_path[@]}"; do
    path="${c_path[i]}"
    case "${c_mode[i]}" in
        120000) resolve "${path}"
                if [[ -n "${R_ERR}" ]]; then unknown "symlink ${path}: ${R_ERR}"; else write_tree "${path}" "${R_SHA}"; fi ;;
        100*)   write_tree "${path}" "${c_blob[i]}" ;;
        160000) unknown "not scanned ${path} (submodule)" ;;
        *)      unknown "not scanned ${path} (mode ${c_mode[i]})" ;;
    esac
done

git -C "${repo}" ls-tree -r -z "${head_sha}" > "${work}/head.z" \
    || { echo "scan-untrusted: git ls-tree failed" >&2; exit 2; }
while IFS= read -r -d '' e; do
    [[ "${e}" == 120000* ]] || continue
    path="${e#*$'\t'}"
    [[ -z "${changed_set[${path}]:-}" && "${path}" != *[[:cntrl:]]* ]] || continue
    resolve "${path}"
    [[ ${R_TOUCH} -eq 1 ]] || continue
    if [[ -n "${R_ERR}" ]]; then unknown "symlink ${path}: ${R_ERR}"; else write_tree "${path}" "${R_SHA}"; fi
done < "${work}/head.z"

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
        .gitmodules)
            unknown "not scanned ${path} (submodule config)"; continue ;;
        uv.lock|poetry.lock|Pipfile.lock|requirements*.txt)
            unknown "pip-audit ${path} (run the table's hashed pip-audit command on the operator's export)"; continue ;;
        .gitleaksignore|.gitleaks.toml|.gitattributes|.shellcheckrc|osv-scanner.toml|pyproject.toml|ruff.toml|.ruff.toml)
            suppressor "${path} scanner config changed" ;;
    esac
    case "${name}" in
        *.py|*.pyi|*.pyw) py+=("${path}"); continue ;;
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
# Ruff, ShellCheck's in those sent to ShellCheck. ShellCheck directive keywords are then blanked in
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
    # Only the keyword is replaced: the rest of the line may be code (`echo a#shellcheck x=; eval $1`).
    sed -i -E 's/(#[[:space:]]*)shellcheck([[:space:]]+[a-z-]+=)/\1blanked\2/g' -- "${work}/tree/${path}"
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
        # Ruff lints only Python file names, so each file is copied under one (`run.toml`,
        # a python-shebang script, would otherwise be skipped without a word).
        declare -A rmap=()
        declare -a rpy=()
        for path in "${py[@]}"; do
            # PEP 263: CPython decodes with the codec a coding cookie on line 1 or 2 names; Ruff
            # always reads UTF-8. Rather than re-implement CPython's choice of cookie, fail closed:
            # on the first two lines (split on CR as well as LF, as CPython does), every
            # `coding[:=]` in a comment must name UTF-8, ASCII or Latin-1 (normalised as tokenize
            # does), or the file is UNKNOWN. This over-reports odd but harmless headers, never under.
            head -c 4096 -- "${work}/tree/${path}" | tr '\r' '\n' > "${work}/head2"
            l1="" l2="" bad=""
            { IFS= read -r l1 || true; IFS= read -r l2 || true; } < "${work}/head2"  # why: a short file ends the reads early
            for l in "${l1}" "${l2}"; do
                [[ "${l}" =~ ^[[:space:]]*# ]] || continue
                rest="${l}"
                while [[ "${rest}" =~ coding[:=][[:space:]]*([-_.[:alnum:]]*)(.*)$ ]]; do
                    name="${BASH_REMATCH[1]}"; rest="${BASH_REMATCH[2]}"
                    codec="${name,,}"; codec="${codec//_/-}"
                    if [[ -n "${codec}" && ! "${codec}" =~ ^(utf-8|utf8|ascii|us-ascii|latin-1|iso-8859-1|iso-latin-1)(-.*)?$ ]]; then
                        bad="${name}"; break 2
                    fi
                done
            done
            if [[ -n "${bad}" ]]; then unknown "ruff cannot read ${path} (coding: ${bad})"; continue; fi
            rpath="${path}"
            [[ "${path}" == *.py || "${path}" == *.pyi ]] || rpath="${path}.scan-untrusted.py"
            if [[ -n "${rmap[${rpath}]:-}" ]]; then unknown "ruff name clash ${path}"; continue; fi
            mkdir -p -- "${work}/ruff/$(dirname -- "${rpath}")"
            cp -- "${work}/tree/${path}" "${work}/ruff/${rpath}"
            rmap["${rpath}"]="${path}"; rpy+=("${rpath}")
        done
        ruff_args=(check --isolated --no-respect-gitignore --select S --config "${RUFF_TEST_ASSERTS}" --no-cache)
        # Every file handed over must be one Ruff selects (--show-files rejects --ignore-noqa;
        # noqa does not affect selection).
        rc=0
        (cd "${work}/ruff" && "${RUFF_BIN}" "${ruff_args[@]}" --show-files -- "${rpy[@]}" \
            > "${work}/ruff.files" 2>&1) || rc=$?
        if [[ ${rc} -ne 0 ]]; then unknown "ruff --show-files exited ${rc}: $(head -c 200 "${work}/ruff.files")"; fi
        declare -A rseen=()
        while IFS= read -r line; do [[ -z "${line}" ]] || rseen["${line#"${work}/ruff/"}"]=1; done < "${work}/ruff.files"
        for rpath in "${rpy[@]}"; do
            [[ -n "${rseen[${rpath}]:-}" ]] || unknown "ruff did not select ${rmap[${rpath}]}"
        done
        rc=0
        (cd "${work}/ruff" && "${RUFF_BIN}" "${ruff_args[@]}" --ignore-noqa --output-format json -- "${rpy[@]}" \
            > "${work}/ruff.json" 2> "${work}/ruff.err") || rc=$?
        # why: jq output dropped — a missing or malformed report is reported as UNKNOWN
        if [[ ${rc} -gt 1 ]] || ! jq -e 'type == "array"' "${work}/ruff.json" >/dev/null 2>&1; then
            unknown "ruff exited ${rc}: $(head -c 200 "${work}/ruff.err")"
        else
            before=$((findings + unknown))
            declare -A unparsed=()
            while IFS=$'\t' read -r file row code msg; do
                file="${file#"${work}/ruff/"}"; file="${rmap[${file}]:-${file}}"
                if [[ "${code}" == invalid-syntax ]]; then
                    [[ -n "${unparsed[${file}]:-}" ]] || unknown "ruff could not parse ${file}"
                    unparsed["${file}"]=1
                else
                    finding "ruff ${file}:${row} ${code} ${msg}"
                fi
            done < <(jq -r '.[] | [.filename, .location.row, (.code // "invalid-syntax"), .message] | @tsv' "${work}/ruff.json")
            while IFS= read -r line; do
                [[ "${line}" =~ Failed\ to\ lint\ (.+):\  ]] && unknown "ruff could not lint ${rmap[${BASH_REMATCH[1]}]:-${BASH_REMATCH[1]}}"
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
# `--no-git` skips a file whose bytes match a binary format signature, at offset 0 or later (tar
# at 257, ISO at 32769), so a text file can be made to look binary. Each copy gitleaks reads
# starts with one 64 KiB line of spaces, which moves every byte the blob controls past the
# furthest signature offset gitleaks checks; reported lines are shifted back by 1. (`--pipe`
# skips the sniff but numbers lines per internal chunk, so findings cannot be mapped back.)
# ponytail: 64 KiB per blob on disk and one cat-file per blob; batch if PR ranges get large.
# ponytail: rev-list prints paths newline-separated, so a path with a newline is misnamed in output.
declare -A blob_path=() allow_seen=()
{ git -C "${repo}" rev-list --objects "${base_sha}..${head_sha}" | git -C "${repo}" cat-file --batch-check='%(objectname) %(objecttype) %(rest)'; } \
    > "${work}/objects.txt" || { echo "scan-untrusted: git rev-list failed" >&2; exit 2; }
mkdir "${work}/gl"
printf '%65536s\n' '' > "${work}/pad"
while read -r sha type rest; do
    [[ "${type}" == blob ]] || continue
    [[ -z "${blob_path[${sha}]:-}" ]] || continue          # same content seen under another path
    blob_path["${sha}"]="${rest}"
    g cat-file blob "${sha}" > "${work}/blobs/${sha}"
    cat -- "${work}/pad" "${work}/blobs/${sha}" > "${work}/gl/${sha}"
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
        (cd "${work}" && "${GITLEAKS_BIN}" detect --no-git --no-banner --redact -s gl -i gl \
            --report-format json --report-path report.json --exit-code 0 >/dev/null 2>"${work}/gitleaks.err") || rc=$?
        # why: jq output dropped — a missing or malformed report is reported as UNKNOWN
        if [[ ${rc} -ne 0 ]] || ! jq -e 'type == "array"' "${work}/report.json" >/dev/null 2>&1; then
            unknown "gitleaks exited ${rc}: $(head -c 200 "${work}/gitleaks.err")"
        else
            while IFS=$'\t' read -r file line rule; do
                finding "gitleaks ${blob_path[${file##*/}]:-${file}}:$((line - 1)) ${rule}"
            done < <(jq -r '.[] | [.File, .StartLine, .RuleID] | @tsv' "${work}/report.json")
        fi
    fi
fi

echo "scan-untrusted: findings=${findings} suppressors=${suppressors} unknown=${unknown}"
if [[ $((findings + suppressors)) -gt 0 ]]; then exit 1; fi
if [[ ${unknown} -gt 0 ]]; then exit 3; fi
exit 0
