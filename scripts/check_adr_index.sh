#!/usr/bin/env bash
# check_adr_index.sh — verify docs/adr/INDEX.md is in sync with on-disk ADR files.
#
# Mode: ADVISORY. Always exits 0. Prints findings to stderr; emits a summary line
# to stdout. Wire into pre-commit when promoted from advisory to blocking — see
# the TODO at the bottom of this file.
#
# Origin: AA-MA plan aa-ma-engineering-standards M2.8 (eng-review finding 1.2).
# Spec: docs/adr/ contains zero-padded NNNN-*.md files; INDEX.md lists each as a
# pipe-table row. A drift means an ADR shipped without an INDEX entry, or an
# INDEX entry references a missing ADR file.

set -u
set -o pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ADR_DIR="${REPO_ROOT}/docs/adr"
INDEX_FILE="${ADR_DIR}/INDEX.md"

if [[ ! -d "${ADR_DIR}" ]]; then
    echo "ADR directory not present (${ADR_DIR}); nothing to check." >&2
    echo "ADR-INDEX-CHECK: SKIP (no ADR directory)"
    exit 0
fi

if [[ ! -f "${INDEX_FILE}" ]]; then
    echo "ADR directory exists but INDEX.md is missing." >&2
    echo "ADR-INDEX-CHECK: WARN (INDEX.md missing)"
    exit 0
fi

# Count NNNN-*.md ADR files (zero-padded sequential, four-digit prefix).
ADR_COUNT=$(find "${ADR_DIR}" -maxdepth 1 -type f -name '[0-9][0-9][0-9][0-9]-*.md' | wc -l | tr -d ' ')

# Count INDEX entries: pipe-table rows that begin with a markdown link to an ADR.
# Match lines like:    | [0001](0001-foo.md) | Title | Status | Date |
INDEX_ENTRIES=$(grep -cE '^\| \[[0-9]{4}\]\([0-9]{4}-' "${INDEX_FILE}" || true)

# List which ADR files exist on disk
mapfile -t ADR_FILES < <(find "${ADR_DIR}" -maxdepth 1 -type f -name '[0-9][0-9][0-9][0-9]-*.md' -printf '%f\n' | sort)

# Extract ADR filenames cited inside INDEX.md (drop directory part)
mapfile -t INDEX_FILES < <(grep -oE '\][(]([0-9]{4}-[^)]+\.md)[)]' "${INDEX_FILE}" | sed -E 's/\]\((.*)\)/\1/' | sort -u)

UNINDEXED=()
ORPHANED=()

for f in "${ADR_FILES[@]}"; do
    found=0
    for i in "${INDEX_FILES[@]}"; do
        if [[ "${i}" == "${f}" ]]; then
            found=1
            break
        fi
    done
    [[ "${found}" -eq 0 ]] && UNINDEXED+=("${f}")
done

for i in "${INDEX_FILES[@]}"; do
    if [[ ! -f "${ADR_DIR}/${i}" ]]; then
        ORPHANED+=("${i}")
    fi
done

if [[ "${ADR_COUNT}" -ne "${INDEX_ENTRIES}" ]]; then
    echo "ADR count mismatch: ${ADR_COUNT} files on disk vs ${INDEX_ENTRIES} INDEX entries." >&2
fi

if [[ "${#UNINDEXED[@]}" -gt 0 ]]; then
    echo "ADR files not listed in INDEX.md:" >&2
    for f in "${UNINDEXED[@]}"; do echo "  - ${f}" >&2; done
fi

if [[ "${#ORPHANED[@]}" -gt 0 ]]; then
    echo "INDEX.md entries with no matching file:" >&2
    for i in "${ORPHANED[@]}"; do echo "  - ${i}" >&2; done
fi

# Summary line on stdout
if [[ "${ADR_COUNT}" -eq "${INDEX_ENTRIES}" && "${#UNINDEXED[@]}" -eq 0 && "${#ORPHANED[@]}" -eq 0 ]]; then
    echo "ADR-INDEX-CHECK: PASS (${ADR_COUNT} ADR files, ${INDEX_ENTRIES} INDEX entries)"
else
    echo "ADR-INDEX-CHECK: WARN (${ADR_COUNT} files / ${INDEX_ENTRIES} entries / ${#UNINDEXED[@]} unindexed / ${#ORPHANED[@]} orphaned)"
fi

# Always exit 0 — advisory mode.
# TODO(v0.6.0): promote to BLOCKING by changing this to `exit ${RC}` once
# pre-commit-full integration is implemented. Tracked as "Eng-review-1.2
# (deferred)" in aa-ma-engineering-standards-context-log.md deferred-items.
exit 0
