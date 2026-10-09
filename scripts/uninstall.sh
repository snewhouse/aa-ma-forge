#!/usr/bin/env bash
# uninstall.sh — Remove AA-MA Forge artifacts from ~/.claude/
#
# Finds all symlinks in ~/.claude/ that point back into this repo and removes
# them. Also removes the 3 copied spec docs. Optionally restores each path from
# its newest aa-ma-forge-* backup.
#
# Usage:
#   scripts/uninstall.sh              # remove symlinks + copied docs
#   scripts/uninstall.sh --restore    # also restore each path from its newest backup
#   scripts/uninstall.sh --dry-run    # preview without changes

set -euo pipefail

# ---------------------------------------------------------------------------
# Colour helpers — degrade gracefully when tput is unavailable
# ---------------------------------------------------------------------------
if command -v tput &>/dev/null && [ -t 1 ]; then
    GREEN=$(tput setaf 2)
    YELLOW=$(tput setaf 3)
    RED=$(tput setaf 1)
    BOLD=$(tput bold)
    RESET=$(tput sgr0)
else
    GREEN=""
    YELLOW=""
    RED=""
    BOLD=""
    RESET=""
fi

info()    { printf "%s[INFO]%s  %s\n" "${GREEN}" "${RESET}" "$1"; }
warn()    { printf "%s[WARN]%s  %s\n" "${YELLOW}" "${RESET}" "$1"; }
error()   { printf "%s[ERROR]%s %s\n" "${RED}" "${RESET}" "$1"; }
header()  { printf "\n%s%s%s\n" "${BOLD}" "$1" "${RESET}"; }

# ---------------------------------------------------------------------------
# Resolve repo root (parent of the directory containing this script)
# ---------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# why: pwd -P — points_into_repo compares against `readlink -f`, which is canonical.
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd -P)"
# shellcheck source=lib/aa-ma-install-lib.sh
# shellcheck disable=SC1090,SC1091
. "${SCRIPT_DIR}/lib/aa-ma-install-lib.sh"
CLAUDE_HOME="${HOME}/.claude"

# ---------------------------------------------------------------------------
# Parse flags
# ---------------------------------------------------------------------------
DRY_RUN=false
RESTORE=false

for arg in "$@"; do
    case "${arg}" in
        --dry-run) DRY_RUN=true ;;
        --restore) RESTORE=true ;;
        *)
            error "Unknown flag: ${arg}"
            echo "Usage: $0 [--dry-run] [--restore]"
            exit 1
            ;;
    esac
done

if ${DRY_RUN}; then
    header "=== DRY RUN — no changes will be made ==="
fi

# A malformed hook row must stop the uninstall before it removes anything: links gone
# but hooks still registered would point every session at missing files.
if ! aa_ma_hooks_validate; then
    error "Fix AA_MA_HOOKS in ${SCRIPT_DIR}/lib/aa-ma-install-lib.sh, then re-run."
    exit 1
fi

# ---------------------------------------------------------------------------
# Counters for summary
# ---------------------------------------------------------------------------
LINKS_REMOVED=0
DOCS_REMOVED=0
FILES_RESTORED=0

# ---------------------------------------------------------------------------
# 1. Find and remove all symlinks pointing into this repo
# ---------------------------------------------------------------------------
header "Scanning for symlinks pointing to ${REPO_ROOT}..."

# We search known directories rather than recursing all of ~/.claude/ to avoid
# touching unrelated areas. Symlinks can be files or directories.
SEARCH_DIRS=(
    "${CLAUDE_HOME}/commands"
    "${CLAUDE_HOME}/skills"
    "${CLAUDE_HOME}/agents"
    "${CLAUDE_HOME}/rules"
    "${CLAUDE_HOME}/hooks"
    "${CLAUDE_HOME}/hooks/lib"
)

for search_dir in "${SEARCH_DIRS[@]}"; do
    [ -d "${search_dir}" ] || continue

    # Find symlinks in this directory (non-recursive — depth 1 only)
    while IFS= read -r -d '' link; do
        # Resolve where the symlink points
        link_target="$(readlink "${link}")"
        if points_into_repo "${link}"; then
            if ${DRY_RUN}; then
                info "Would remove symlink: ${link} -> ${link_target}"
            else
                rm "${link}"
                info "Removed symlink: ${link}"
            fi
            LINKS_REMOVED=$((LINKS_REMOVED + 1))
        fi
    done < <(find "${search_dir}" -maxdepth 1 -type l -print0 2>/dev/null)
done

# ---------------------------------------------------------------------------
# 2. Remove copied spec docs
# ---------------------------------------------------------------------------
# Derive the list from the repo's docs/spec/ directory so it stays in sync
# with whatever install.sh copies (rather than hardcoding filenames).
header "Removing copied spec docs..."

SPEC_DOCS=()
for f in "${REPO_ROOT}/docs/spec/"*.md; do
    [ -e "${f}" ] || continue
    SPEC_DOCS+=("$(basename "${f}")")
done

for doc in "${SPEC_DOCS[@]}"; do
    target="${CLAUDE_HOME}/docs/${doc}"
    if [ -f "${target}" ] && [ ! -L "${target}" ]; then
        if ${DRY_RUN}; then
            info "Would remove copied doc: ${target}"
        else
            rm "${target}"
            info "Removed: ${target}"
        fi
        DOCS_REMOVED=$((DOCS_REMOVED + 1))
    elif [ -L "${target}" ]; then
        # Unlikely but handle it: if somehow it's a symlink to our repo
        if points_into_repo "${target}"; then
            if ${DRY_RUN}; then
                info "Would remove symlinked doc: ${target}"
            else
                rm "${target}"
                info "Removed symlinked doc: ${target}"
            fi
            DOCS_REMOVED=$((DOCS_REMOVED + 1))
        fi
    else
        warn "Not found (already removed?): ${target}"
    fi
done

# ------------------------------------------------------------------
# Deregister all AA-MA hooks from settings.json (symmetric with install.sh),
# with or without --restore. Every row of AA_MA_HOOKS (the one table, sourced
# above) is removed. A literal substring match on the link path removes both the
# `<path>` and `bash <path>` command forms. Idempotent.
# ------------------------------------------------------------------
SETTINGS_FILE="${CLAUDE_HOME}/settings.json"

deregister_hook() {
    local event="$1" src_base="$2"
    local link_path="${CLAUDE_HOME}/hooks/lib/${src_base}"
    local has
    if ! has=$(jq -r --arg event "$event" --arg link "$link_path" \
        '(.hooks[$event] // []) | map(select(any(.hooks[]?; (.command // "") | contains($link)))) | length' \
        "${SETTINGS_FILE}"); then
        warn "Could not read ${SETTINGS_FILE}; ${event} [${src_base}] left registered"
        return 0
    fi
    [ "${has}" = "0" ] && return 0
    if ${DRY_RUN}; then
        info "Would deregister ${event} [${src_base}] from settings.json"
        return 0
    fi
    local tmp="${SETTINGS_FILE}.tmp.$$"
    # Write failures warn and return 0, like the read above: links are already gone, so
    # aborting here would leave a half-done uninstall and skip --restore.
    if ! jq --arg event "$event" --arg link "$link_path" \
        '.hooks[$event] = ((.hooks[$event] // []) | map(select(.hooks | all((.command // "") | contains($link) | not))))' \
        "${SETTINGS_FILE}" > "${tmp}" \
        || ! chmod --reference="${SETTINGS_FILE}" "${tmp}" || ! mv "${tmp}" "${SETTINGS_FILE}"; then
        rm -f "${tmp}"
        warn "Could not update ${SETTINGS_FILE}; ${event} [${src_base}] left registered"
        return 0
    fi
    info "Deregistered ${event} [${src_base}] from settings.json"
}

header "Deregistering hooks..."
if [ ! -f "${SETTINGS_FILE}" ]; then
    info "No ${SETTINGS_FILE}; nothing to deregister."
elif ! command -v jq &>/dev/null; then
    warn "jq not found; AA-MA hooks left registered in ${SETTINGS_FILE}"
else
    declare -A DEREGISTERED=()
    for entry in "${AA_MA_HOOKS[@]}"; do
        aa_ma_hook_parse "${entry}"   # validated at the top
        [ -n "${DEREGISTERED[${HOOK_EVENT}|${HOOK_SRC}]:-}" ] && continue
        DEREGISTERED["${HOOK_EVENT}|${HOOK_SRC}"]=1
        deregister_hook "${HOOK_EVENT}" "${HOOK_SRC}"
    done
fi

# manifest_slot_ok REL — REL (relative to ~/.claude) is one name in a slot install.sh
# links into. A row is only data from ~/.claude/backups, so `..`, nesting and any other
# path are refused rather than followed out of ~/.claude.
manifest_slot_ok() {
    [[ "$1" =~ ^(skills|agents|rules|commands|hooks/lib)/[^/]+$ && "${1##*/}" != "." && "${1##*/}" != ".." ]]
}

# slot_free_for_restore LINK — nothing is at LINK, or (in a dry run, which removed none of
# our links) what is there is one of our links that a real run would already have removed.
slot_free_for_restore() {
    { [ ! -e "$1" ] && [ ! -L "$1" ]; } || { ${DRY_RUN} && [ -L "$1" ] && points_into_repo "$1"; }
}

# ---------------------------------------------------------------------------
# 3. Restore from backup (if --restore flag set)
# ---------------------------------------------------------------------------
if ${RESTORE}; then
    header "Looking for backups..."

    BACKUP_BASE="${CLAUDE_HOME}/backups"

    if [ ! -d "${BACKUP_BASE}" ]; then
        warn "No backup directory found at ${BACKUP_BASE}/"
    else
        # Every aa-ma-forge backup dir, newest first (the YYYYMMDD-HHMMSS suffix sorts
        # lexicographically). why: one install run backs up only what was real at that
        # moment, so the newest dir alone (e.g. a re-run that backed up just the copied
        # spec docs) can hide the dir holding the real skills. Each path is restored from
        # its newest backup; older copies of an already-restored path are skipped.
        BACKUPS=()
        while IFS= read -r -d '' dir; do
            BACKUPS+=("${dir}")
        done < <(find "${BACKUP_BASE}" -maxdepth 1 -type d -name "aa-ma-forge-*" -print0 2>/dev/null | sort -rz)

        if [ ${#BACKUPS[@]} -eq 0 ]; then
            warn "No aa-ma-forge backups found in ${BACKUP_BASE}/"
        else
            info "Backups (newest first): ${#BACKUPS[@]}"
            declare -A RESTORED=()
            for backup_dir in "${BACKUPS[@]}"; do
                # Restore units are what install.sh backed up: depth-2 entries
                # (skills/<name>, commands/<x>.md, rules/…, docs/…) plus hooks/lib/<x>.
                # A unit is copied whole from its newest backup, never merged per file.
                while IFS= read -r -d '' unit; do
                    rel_path="${unit#"${backup_dir}"/}"
                    [ -n "${RESTORED[${rel_path}]:-}" ] && continue   # a newer backup already won
                    RESTORED["${rel_path}"]=1
                    restore_target="${CLAUDE_HOME}/${rel_path}"

                    # Only restore if the slot is free (we just removed our symlinks).
                    if [ -e "${restore_target}" ] && [ ! -L "${restore_target}" ]; then
                        warn "Skipping restore (exists): ${restore_target}"
                        continue
                    fi
                    if [ -L "${restore_target}" ] && ! ${DRY_RUN}; then
                        rm "${restore_target}"   # dangling symlink
                    fi

                    if ${DRY_RUN}; then
                        info "Would restore: ${unit} -> ${restore_target}"
                    else
                        mkdir -p "$(dirname "${restore_target}")"
                        cp -a "${unit}" "${restore_target}"
                        info "Restored: ${rel_path} (from ${backup_dir##*/})"
                    fi
                    FILES_RESTORED=$((FILES_RESTORED + 1))
                done < <(
                    find "${backup_dir}" -mindepth 2 -maxdepth 2 ! -path "${backup_dir}/hooks/lib" -print0 2>/dev/null
                    find "${backup_dir}/hooks/lib" -mindepth 1 -maxdepth 1 -print0 2>/dev/null
                )

                # Foreign symlinks install.sh replaced (one "<link>\t<dest>" per row).
                manifest="${backup_dir}/foreign-symlinks.tsv"
                [ -f "${manifest}" ] || continue
                while IFS=$'\t' read -r link dest; do
                    rel_path="${link#"${CLAUDE_HOME}"/}"
                    if [[ "${link}" != "${CLAUDE_HOME}/"* || -z "${dest}" ]] || ! manifest_slot_ok "${rel_path}"; then
                        warn "Skipping manifest row (not an install slot under ${CLAUDE_HOME}/): ${link}"
                        continue
                    fi
                    [ -n "${RESTORED[${rel_path}]:-}" ] && continue
                    RESTORED["${rel_path}"]=1
                    if ! slot_free_for_restore "${link}"; then
                        warn "Skipping foreign-symlink restore (exists): ${link}"
                        continue
                    fi
                    if ${DRY_RUN}; then
                        info "Would restore foreign symlink: ${link} -> ${dest}"
                    else
                        mkdir -p "$(dirname "${link}")"
                        ln -s "${dest}" "${link}"
                        info "Restored foreign symlink: ${link} -> ${dest}"
                    fi
                    FILES_RESTORED=$((FILES_RESTORED + 1))
                done < "${manifest}"
            done
        fi
    fi
else
    header "Backup restore"
    info "Skipped (use --restore to restore from the most recent backup)."

    # Show available backups as a convenience
    BACKUP_BASE="${CLAUDE_HOME}/backups"
    if [ -d "${BACKUP_BASE}" ]; then
        backup_count=0
        while IFS= read -r -d '' dir; do
            backup_count=$((backup_count + 1))
            if [ ${backup_count} -eq 1 ]; then
                info "Available backups:"
            fi
            info "  $(basename "${dir}")"
        done < <(find "${BACKUP_BASE}" -maxdepth 1 -type d -name "aa-ma-forge-*" -print0 2>/dev/null | sort -z)

        if [ ${backup_count} -eq 0 ]; then
            info "No aa-ma-forge backups found."
        fi
    fi
fi

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
header "=== Uninstall Summary ==="
info "Symlinks removed:      ${LINKS_REMOVED}"
info "Spec docs removed:     ${DOCS_REMOVED}"
info "Files restored:        ${FILES_RESTORED}"

if ${DRY_RUN}; then
    warn "This was a dry run. No changes were made."
else
    info "${GREEN}${BOLD}AA-MA Forge uninstalled successfully.${RESET}"
fi
