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

# Skills directories (auto-discover all)
for d in "${REPO_ROOT}/claude-code/skills/"*/; do
    [ -d "${d}" ] || continue
    collect_backup_target "${CLAUDE_HOME}/skills/$(basename "${d}")"
done

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
# 2. Symlink skills directories (auto-discover all)
# ---------------------------------------------------------------------------
header "Linking skills..."
for d in "${REPO_ROOT}/claude-code/skills/"*/; do
    [ -d "${d}" ] || continue
    create_symlink "${d%/}" "${CLAUDE_HOME}/skills/$(basename "${d}")"
done

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
# 5. Preflight: jq is required for settings.json registration
# ---------------------------------------------------------------------------
if ! command -v jq &>/dev/null; then
    error "jq is required for hook registration but was not found in PATH."
    error "  Ubuntu/WSL:  sudo apt-get install -y jq"
    error "  macOS:       brew install jq"
    exit 1
fi

# ---------------------------------------------------------------------------
# 5a. Symlink hooks + register in settings.json (idempotent, conditional)
# ---------------------------------------------------------------------------
# Each AA-MA hook is declared once below. Entries are processed in-order:
#   1. Symlink the source file into ~/.claude/hooks/lib/ (only if source exists).
#   2. Register the hook in ~/.claude/settings.json (only if source exists).
#
# The "only if source exists" rule makes install.sh idempotent across a
# multi-milestone plan: re-running after new hook files land adds their
# registrations without touching already-registered entries.
#
# Hook entries use a pipe-delimited schema:
#   event|matcher|source_basename|timeout|statusMessage
# Empty matcher = no tool-name match restriction (applies to SessionStart, etc.).

AA_MA_HOOKS=(
    "SessionStart||aa-ma-session-start.sh|5|Loading AA-MA context..."
    "PreCompact||pre-compact-aa-ma.sh|5|"
    "PreToolUse|Bash|aa-ma-commit-signature.sh|10|"
    "SessionEnd||aa-ma-session-end-dirty.sh|5|"
    "PostToolUse|Bash|aa-ma-commit-drift.sh|5|"
)

SETTINGS_FILE="${CLAUDE_HOME}/settings.json"
SETTINGS_BACKED_UP=false

header "Linking hooks + registering in settings.json..."

# Helper library must be symlinked so hooks can source it from their
# installed location (~/.claude/hooks/lib/<hook>.sh finds ./aa-ma-parse.sh
# as a sibling).
if [ -f "${REPO_ROOT}/claude-code/hooks/lib/aa-ma-parse.sh" ]; then
    create_symlink "${REPO_ROOT}/claude-code/hooks/lib/aa-ma-parse.sh" \
                   "${CLAUDE_HOME}/hooks/lib/aa-ma-parse.sh"
fi

# Back up settings.json once before first mutation.
backup_settings_once() {
    ${SETTINGS_BACKED_UP} && return 0
    if [ -f "${SETTINGS_FILE}" ] && ! ${FORCE}; then
        if ${DRY_RUN}; then
            info "Would back up ${SETTINGS_FILE} → ${SETTINGS_FILE}.bak"
        else
            cp -a "${SETTINGS_FILE}" "${SETTINGS_FILE}.bak"
            info "Backed up ${SETTINGS_FILE} → ${SETTINGS_FILE}.bak"
        fi
    fi
    SETTINGS_BACKED_UP=true
}

register_hook() {
    local event="$1" matcher="$2" src_base="$3" timeout="$4" status_msg="$5"
    local src_path="${REPO_ROOT}/claude-code/hooks/${src_base}"
    local link_path="${CLAUDE_HOME}/hooks/lib/${src_base}"
    local hook_cmd="bash ${link_path}"

    # Skip if source file not yet authored (multi-milestone idempotence).
    if [ ! -f "${src_path}" ]; then
        info "Skipping ${src_base} — source not present (future milestone?)"
        return 0
    fi

    # 1. Symlink.
    create_symlink "${src_path}" "${link_path}"

    # 2. Check idempotence in settings.json.
    #    Idempotence normalises `bash <path>` and `<path>` forms: a manually-
    #    registered plain-path entry and a script-registered `bash <path>`
    #    entry should count as the same hook. We match on whether the link
    #    path substring appears in any registered command for this event.
    if [ ! -f "${SETTINGS_FILE}" ]; then
        warn "${SETTINGS_FILE} not found — skipping registration for ${src_base}"
        return 0
    fi
    local already
    already=$(jq -r \
        --arg event "$event" \
        --arg link "$link_path" \
        '(.hooks[$event] // []) | map(select(.hooks[]? | .command | test($link; "l"))) | length' \
        "${SETTINGS_FILE}" 2>/dev/null || echo "0")

    if [ "${already}" != "0" ]; then
        info "${event} [${src_base}] already registered in settings.json (skipping)"
        return 0
    fi

    backup_settings_once

    if ${DRY_RUN}; then
        info "Would register ${event} [${src_base}] in settings.json"
        return 0
    fi

    # 3. Atomic write: tempfile + jq empty validation + mv.
    local tmp="${SETTINGS_FILE}.tmp.$$"
    jq \
        --arg event "$event" \
        --arg matcher "$matcher" \
        --arg cmd "$hook_cmd" \
        --argjson timeout "$timeout" \
        --arg status "$status_msg" \
        '
        .hooks[$event] = ((.hooks[$event] // []) + [(
            {
                matcher: $matcher,
                hooks: [
                    ({type: "command", command: $cmd, timeout: $timeout}
                     + (if $status == "" then {} else {statusMessage: $status} end))
                ]
            }
            | if $matcher == "" then del(.matcher) else . end
        )])
        ' "${SETTINGS_FILE}" > "${tmp}" || {
            error "Failed to patch settings.json for ${event} [${src_base}]"
            rm -f "${tmp}"
            return 1
        }

    # Validate before atomic replace.
    if ! jq empty "${tmp}" 2>/dev/null; then
        error "Patched settings.json failed jq validation — reverting"
        rm -f "${tmp}"
        return 1
    fi

    mv "${tmp}" "${SETTINGS_FILE}"
    info "Registered ${event} [${src_base}] in settings.json"
}

for entry in "${AA_MA_HOOKS[@]}"; do
    IFS='|' read -r h_event h_matcher h_src h_timeout h_status <<< "${entry}"
    register_hook "${h_event}" "${h_matcher}" "${h_src}" "${h_timeout}" "${h_status}"
done

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
