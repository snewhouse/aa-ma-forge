#!/usr/bin/env bash
# install.sh — Deploy AA-MA Forge artifacts into ~/.claude/ via symlinks
#
# Symlinks operational files (commands, skills, agents, rules, hooks) from this
# repo into ~/.claude/ so Claude Code picks them up. Spec docs are copied (not
# symlinked) because ~/.claude/docs/ contains non-AA-MA files and mixing
# symlinks with regular files in a shared directory is fragile.
#
# Usage:
#   scripts/install.sh              # install with backup
#   scripts/install.sh --dry-run    # preview without changes
#   scripts/install.sh --force      # skip backup (CI/testing)

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
FORCE=false

for arg in "$@"; do
    case "${arg}" in
        --dry-run) DRY_RUN=true ;;
        --force)   FORCE=true ;;
        *)
            error "Unknown flag: ${arg}"
            echo "Usage: $0 [--dry-run] [--force]"
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
LINKS_CREATED=0
FILES_COPIED=0
FILES_BACKED_UP=0
STALE_REMOVED=0

# ---------------------------------------------------------------------------
# Verify target directories exist (we do NOT create them)
# ---------------------------------------------------------------------------
REQUIRED_DIRS=(
    "${CLAUDE_HOME}/commands"
    "${CLAUDE_HOME}/skills"
    "${CLAUDE_HOME}/agents"
    "${CLAUDE_HOME}/rules"
    "${CLAUDE_HOME}/hooks"
    "${CLAUDE_HOME}/docs"
)

header "Checking target directories..."
for dir in "${REQUIRED_DIRS[@]}"; do
    if [ ! -d "${dir}" ]; then
        error "Required directory does not exist: ${dir}"
        error "Please ensure Claude Code is set up before running this installer."
        exit 1
    fi
done
info "All required target directories exist."

# ---------------------------------------------------------------------------
# Create directories we ARE allowed to create
# ---------------------------------------------------------------------------
# ~/.claude/hooks/lib/ may not exist yet — the installer creates it
if [ ! -d "${CLAUDE_HOME}/hooks/lib" ]; then
    if ${DRY_RUN}; then
        info "Would create: ${CLAUDE_HOME}/hooks/lib/"
    else
        mkdir -p "${CLAUDE_HOME}/hooks/lib"
        info "Created: ${CLAUDE_HOME}/hooks/lib/"
    fi
fi

# ---------------------------------------------------------------------------
# Backup existing AA-MA files
# ---------------------------------------------------------------------------
# Collect paths that would be overwritten so we can back them up.
# Only real files (not existing symlinks) need backup.
backup_targets=()

collect_backup_target() {
    local target="$1"
    if [ -e "${target}" ] && [ ! -L "${target}" ]; then
        backup_targets+=("${target}")
    fi
}

# Commands
for f in "${REPO_ROOT}/claude-code/commands/"*.md; do
    [ -e "${f}" ] || continue
    collect_backup_target "${CLAUDE_HOME}/commands/$(basename "${f}")"
done

# Skills directory
collect_backup_target "${CLAUDE_HOME}/skills/aa-ma-execution"

# Agents
for f in "${REPO_ROOT}/claude-code/agents/"*.md; do
    [ -e "${f}" ] || continue
    collect_backup_target "${CLAUDE_HOME}/agents/$(basename "${f}")"
done

# Rules
collect_backup_target "${CLAUDE_HOME}/rules/aa-ma.md"

# Hooks
collect_backup_target "${CLAUDE_HOME}/hooks/lib/pre-compact-aa-ma.sh"

# Spec docs (copies, not symlinks)
for f in "${REPO_ROOT}/docs/spec/"*.md; do
    [ -e "${f}" ] || continue
    collect_backup_target "${CLAUDE_HOME}/docs/$(basename "${f}")"
done

if [ ${#backup_targets[@]} -gt 0 ] && ! ${FORCE}; then
    BACKUP_DIR="${CLAUDE_HOME}/backups/aa-ma-forge-$(date +%Y%m%d-%H%M%S)"

    header "Backing up existing files..."
    if ${DRY_RUN}; then
        info "Would create backup dir: ${BACKUP_DIR}/"
    else
        mkdir -p "${BACKUP_DIR}"
        info "Backup directory: ${BACKUP_DIR}/"
    fi

    for target in "${backup_targets[@]}"; do
        # Preserve the relative path under ~/.claude/ in the backup
        rel_path="${target#"${CLAUDE_HOME}"/}"
        backup_dest="${BACKUP_DIR}/${rel_path}"

        if ${DRY_RUN}; then
            info "Would backup: ${target} -> ${backup_dest}"
        else
            mkdir -p "$(dirname "${backup_dest}")"
            if [ -d "${target}" ]; then
                cp -a "${target}" "${backup_dest}"
            else
                cp -a "${target}" "${backup_dest}"
            fi
            info "Backed up: ${rel_path}"
        fi
        FILES_BACKED_UP=$((FILES_BACKED_UP + 1))
    done
elif [ ${#backup_targets[@]} -gt 0 ] && ${FORCE}; then
    warn "Skipping backup (--force flag set)"
else
    info "No existing files to back up."
fi

# ---------------------------------------------------------------------------
# Helper: create a symlink, removing stale symlinks first (idempotent)
# ---------------------------------------------------------------------------
create_symlink() {
    local source="$1"
    local target="$2"

    # Remove stale symlink (pointing anywhere, including our repo)
    if [ -L "${target}" ]; then
        if ${DRY_RUN}; then
            info "Would remove stale symlink: ${target}"
        else
            rm "${target}"
        fi
        STALE_REMOVED=$((STALE_REMOVED + 1))
    fi

    # Remove real file/dir that's in our way (already backed up above)
    if [ -e "${target}" ] && [ ! -L "${target}" ]; then
        if ${DRY_RUN}; then
            info "Would remove existing: ${target}"
        else
            rm -rf "${target}"
        fi
    fi

    if ${DRY_RUN}; then
        info "Would symlink: ${target} -> ${source}"
    else
        ln -s "${source}" "${target}"
        info "Linked: ${target} -> ${source}"
    fi
    LINKS_CREATED=$((LINKS_CREATED + 1))
}

# ---------------------------------------------------------------------------
# Helper: copy a file (idempotent — overwrites existing)
# ---------------------------------------------------------------------------
copy_file() {
    local source="$1"
    local target="$2"

    # If target is a symlink, remove it first (we want a real copy)
    if [ -L "${target}" ]; then
        if ${DRY_RUN}; then
            info "Would remove symlink before copy: ${target}"
        else
            rm "${target}"
        fi
        STALE_REMOVED=$((STALE_REMOVED + 1))
    fi

    if ${DRY_RUN}; then
        info "Would copy: ${source} -> ${target}"
    else
        cp "${source}" "${target}"
        info "Copied: $(basename "${source}") -> ${target}"
    fi
    FILES_COPIED=$((FILES_COPIED + 1))
}

# ---------------------------------------------------------------------------
# 1. Symlink commands (each file individually)
# ---------------------------------------------------------------------------
header "Linking commands..."
for f in "${REPO_ROOT}/claude-code/commands/"*.md; do
    [ -e "${f}" ] || continue
    create_symlink "${f}" "${CLAUDE_HOME}/commands/$(basename "${f}")"
done

# ---------------------------------------------------------------------------
# 2. Symlink skills directory
# ---------------------------------------------------------------------------
header "Linking skills..."
create_symlink "${REPO_ROOT}/claude-code/skills/aa-ma-execution" \
               "${CLAUDE_HOME}/skills/aa-ma-execution"

# ---------------------------------------------------------------------------
# 3. Symlink agents (each file individually)
# ---------------------------------------------------------------------------
header "Linking agents..."
for f in "${REPO_ROOT}/claude-code/agents/"*.md; do
    [ -e "${f}" ] || continue
    create_symlink "${f}" "${CLAUDE_HOME}/agents/$(basename "${f}")"
done

# ---------------------------------------------------------------------------
# 4. Symlink rules
# ---------------------------------------------------------------------------
header "Linking rules..."
create_symlink "${REPO_ROOT}/claude-code/rules/aa-ma.md" \
               "${CLAUDE_HOME}/rules/aa-ma.md"

# ---------------------------------------------------------------------------
# 5. Symlink hooks
# ---------------------------------------------------------------------------
header "Linking hooks..."
create_symlink "${REPO_ROOT}/claude-code/hooks/pre-compact-aa-ma.sh" \
               "${CLAUDE_HOME}/hooks/lib/pre-compact-aa-ma.sh"

# ---------------------------------------------------------------------------
# 6. Copy spec docs (NOT symlinks — shared directory with non-AA-MA files)
# ---------------------------------------------------------------------------
header "Copying spec docs..."
for f in "${REPO_ROOT}/docs/spec/"*.md; do
    [ -e "${f}" ] || continue
    copy_file "${f}" "${CLAUDE_HOME}/docs/$(basename "${f}")"
done

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
header "=== Installation Summary ==="
info "Symlinks created:      ${LINKS_CREATED}"
info "Files copied:          ${FILES_COPIED}"
info "Files backed up:       ${FILES_BACKED_UP}"
info "Stale links removed:   ${STALE_REMOVED}"

if ${DRY_RUN}; then
    warn "This was a dry run. No changes were made."
else
    info "${GREEN}${BOLD}AA-MA Forge installed successfully.${RESET}"
fi
