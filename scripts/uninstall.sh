#!/usr/bin/env bash
# uninstall.sh — Remove AA-MA Forge artifacts from ~/.claude/
#
# Finds all symlinks in ~/.claude/ that point back into this repo and removes
# them. Also removes the 3 copied spec docs. Optionally restores from the most
# recent backup.
#
# Usage:
#   scripts/uninstall.sh              # remove symlinks + copied docs
#   scripts/uninstall.sh --restore    # also restore from latest backup
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
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
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
        link_target="$(readlink -f "${link}" 2>/dev/null || true)"

        # Check if the resolved target lives under our repo root
        if [[ "${link_target}" == "${REPO_ROOT}"* ]]; then
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
        link_target="$(readlink -f "${target}" 2>/dev/null || true)"
        if [[ "${link_target}" == "${REPO_ROOT}"* ]]; then
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

# ---------------------------------------------------------------------------
# 3. Restore from backup (if --restore flag set)
# ---------------------------------------------------------------------------
if ${RESTORE}; then
    header "Looking for backups..."

    BACKUP_BASE="${CLAUDE_HOME}/backups"

    if [ ! -d "${BACKUP_BASE}" ]; then
        warn "No backup directory found at ${BACKUP_BASE}/"
    else
        # Find the most recent aa-ma-forge backup by directory name (sorted
        # lexicographically — the YYYYMMDD-HHMMSS suffix guarantees correct order)
        LATEST_BACKUP=""
        while IFS= read -r -d '' dir; do
            LATEST_BACKUP="${dir}"
        done < <(find "${BACKUP_BASE}" -maxdepth 1 -type d -name "aa-ma-forge-*" -print0 2>/dev/null | sort -z)

        if [ -z "${LATEST_BACKUP}" ]; then
            warn "No aa-ma-forge backups found in ${BACKUP_BASE}/"
        else
            info "Most recent backup: ${LATEST_BACKUP}"

            # Walk the backup directory and restore each file to its original
            # location under ~/.claude/
            while IFS= read -r -d '' backup_file; do
                # Compute the relative path within the backup
                rel_path="${backup_file#"${LATEST_BACKUP}"/}"
                restore_target="${CLAUDE_HOME}/${rel_path}"

                # Only restore if the target doesn't already exist (we just
                # removed symlinks, so the slot should be free)
                if [ -e "${restore_target}" ] && [ ! -L "${restore_target}" ]; then
                    warn "Skipping restore (file exists): ${restore_target}"
                    continue
                fi

                # Remove dangling symlink if present
                if [ -L "${restore_target}" ]; then
                    if ! ${DRY_RUN}; then
                        rm "${restore_target}"
                    fi
                fi

                if ${DRY_RUN}; then
                    info "Would restore: ${backup_file} -> ${restore_target}"
                else
                    mkdir -p "$(dirname "${restore_target}")"
                    if [ -d "${backup_file}" ]; then
                        cp -a "${backup_file}" "${restore_target}"
                    else
                        cp -a "${backup_file}" "${restore_target}"
                    fi
                    info "Restored: ${rel_path}"
                fi
                FILES_RESTORED=$((FILES_RESTORED + 1))
            done < <(find "${LATEST_BACKUP}" -type f -print0 2>/dev/null)
        fi
    fi
else
    header "Backup restore"
    info "Skipped (use --restore to restore from the most recent backup)."

    # Remove SessionStart hook from settings.json (if registered)
    SETTINGS_FILE="${CLAUDE_HOME}/settings.json"
    HOOK_CMD="bash ${CLAUDE_HOME}/hooks/lib/aa-ma-session-start.sh"
    if command -v jq &>/dev/null && [ -f "${SETTINGS_FILE}" ]; then
        HAS_HOOK=$(jq -r \
            --arg cmd "$HOOK_CMD" \
            '.hooks.SessionStart // [] | map(select(.hooks[]?.command == $cmd)) | length' \
            "${SETTINGS_FILE}" 2>/dev/null || echo "0")

        if [ "${HAS_HOOK}" != "0" ]; then
            if ${DRY_RUN}; then
                info "Would remove SessionStart hook from settings.json"
            else
                jq --arg cmd "$HOOK_CMD" \
                    '.hooks.SessionStart = [.hooks.SessionStart[] | select(.hooks | all(.command != $cmd))]' \
                    "${SETTINGS_FILE}" > "${SETTINGS_FILE}.tmp" \
                    && mv "${SETTINGS_FILE}.tmp" "${SETTINGS_FILE}"
                info "Removed SessionStart hook from settings.json"
            fi
        fi
    fi

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
