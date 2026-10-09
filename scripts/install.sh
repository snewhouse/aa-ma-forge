#!/usr/bin/env bash
# install.sh — Deploy AA-MA Forge artifacts into ~/.claude/ via symlinks
#
# Symlinks operational files (skills, agents, rules, hooks) from this
# repo into ~/.claude/ so Claude Code picks them up. Spec docs are copied (not
# symlinked) because ~/.claude/docs/ contains non-AA-MA files and mixing
# symlinks with regular files in a shared directory is fragile.
#
# Usage:
#   scripts/install.sh              # install with backup
#   scripts/install.sh --dry-run    # preview without changes
#   scripts/install.sh --force      # skip file backups (CI/testing); real directories are still backed up

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
FORCE=false
WIRE_GIT_HOOK=false

for arg in "$@"; do
    case "${arg}" in
        --dry-run)       DRY_RUN=true ;;
        --force)         FORCE=true ;;
        --wire-git-hook) WIRE_GIT_HOOK=true ;;
        *)
            error "Unknown flag: ${arg}"
            echo "Usage: $0 [--dry-run] [--force] [--wire-git-hook]"
            exit 1
            ;;
    esac
done

if ${DRY_RUN}; then
    header "=== DRY RUN — no changes will be made ==="
fi

# A malformed hook row must stop the install before it changes anything.
if ! aa_ma_hooks_validate; then
    error "Fix AA_MA_HOOKS in ${SCRIPT_DIR}/lib/aa-ma-install-lib.sh, then re-run."
    exit 1
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
# commands/ is no longer required: the forge ships no commands (M3, ADR-0020); the
# stale-link sweep below is a no-op when the directory is absent.
REQUIRED_DIRS=(
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
collect_backup_target "${CLAUDE_HOME}/rules/engineering-standards.md"

# Hooks
collect_backup_target "${CLAUDE_HOME}/hooks/lib/pre-compact-aa-ma.sh"
collect_backup_target "${CLAUDE_HOME}/hooks/lib/ruff-format.sh"

# Spec docs (copies, not symlinks)
for f in "${REPO_ROOT}/docs/spec/"*.md; do
    [ -e "${f}" ] || continue
    collect_backup_target "${CLAUDE_HOME}/docs/$(basename "${f}")"
done

# why: --force skips file backups, but create_symlink `rm -rf`s whatever is in the way —
# a real directory (e.g. a skill that predates the forge) is never deleted unbacked.
if ${FORCE}; then
    warn "Skipping file backups (--force flag set); real directories are still backed up"
    forced_targets=()
    for target in "${backup_targets[@]}"; do
        [ -d "${target}" ] && forced_targets+=("${target}")
    done
    backup_targets=("${forced_targets[@]}")
fi

RUN_TS="$(date +%Y%m%d-%H%M%S)"
BACKUP_DIR="${CLAUDE_HOME}/backups/aa-ma-forge-${RUN_TS}"
# why: a sibling file, not inside BACKUP_DIR — settings.json is not a symlinked target, and
# `uninstall.sh --restore` must never overwrite the live settings.json from a backup dir.
SETTINGS_BACKUP="${CLAUDE_HOME}/backups/settings-aa-ma-forge-${RUN_TS}.json"

if [ ${#backup_targets[@]} -gt 0 ]; then

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
elif ! ${FORCE}; then
    info "No existing files to back up."
fi

# ---------------------------------------------------------------------------
# Helper: record a foreign symlink's destination before it is replaced
# ---------------------------------------------------------------------------
# A link that points outside this repo is someone else's install; replacing it
# loses where it pointed. Record "<link>\t<destination>" so --restore can put it back.
FOREIGN_MANIFEST="${BACKUP_DIR}/foreign-symlinks.tsv"
record_foreign_symlink() {
    local target="$1" dest
    points_into_repo "${target}" && return 0
    dest=$(readlink "${target}")
    if ${DRY_RUN}; then
        info "Would record foreign symlink: ${target} -> ${dest}"
        return 0
    fi
    mkdir -p "${BACKUP_DIR}"
    printf '%s\t%s\n' "${target}" "${dest}" >> "${FOREIGN_MANIFEST}"
    warn "Replacing foreign symlink (recorded in ${FOREIGN_MANIFEST}): ${target} -> ${dest}"
}

# ---------------------------------------------------------------------------
# Helper: create a symlink, removing stale symlinks first (idempotent)
# ---------------------------------------------------------------------------
create_symlink() {
    local source="$1"
    local target="$2"

    # Remove stale symlink (pointing anywhere, including our repo)
    if [ -L "${target}" ]; then
        record_foreign_symlink "${target}"
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
# 1. Sweep command links left by earlier installs
# ---------------------------------------------------------------------------
header "Removing stale command links..."
# A command that became a skill leaves ~/.claude/commands/<x>.md dangling into this repo.
for link in "${CLAUDE_HOME}/commands/"*.md; do
    if [ ! -L "${link}" ] || [ -e "${link}" ] || ! points_into_repo "${link}"; then
        continue
    fi
    dest=$(readlink "${link}")
    if ${DRY_RUN}; then
        info "Would remove stale command link: ${link} -> ${dest}"
    else
        rm "${link}"
        info "Removed stale command link: ${link} -> ${dest}"
    fi
    STALE_REMOVED=$((STALE_REMOVED + 1))
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
create_symlink "${REPO_ROOT}/claude-code/rules/engineering-standards.md" \
               "${CLAUDE_HOME}/rules/engineering-standards.md"

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
# Hook rows come from AA_MA_HOOKS in scripts/lib/aa-ma-install-lib.sh (the one table).

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

# Charting guard is invoked from the /aa-ma-chart and /aa-ma-plan --from-map
# command bodies via the `_cand` resolution (repo-local first, then
# ${CLAUDE_HOME}/hooks/lib). Not a registered hook event; L-005 — helpers
# are never auto-linked, so it gets its own block like aa-ma-parse.sh.
if [ -f "${REPO_ROOT}/claude-code/hooks/lib/aa-ma-chart-guard.sh" ]; then
    create_symlink "${REPO_ROOT}/claude-code/hooks/lib/aa-ma-chart-guard.sh" \
                   "${CLAUDE_HOME}/hooks/lib/aa-ma-chart-guard.sh"
fi

# Marker-writer helper is invoked from the /aa-ma-plan command body — not a
# registered hook event, but needs to live at the installed location so the
# command's `bash ~/.claude/hooks/lib/aa-ma-plan-marker.sh ...` works.
if [ -f "${REPO_ROOT}/claude-code/hooks/aa-ma-plan-marker.sh" ]; then
    create_symlink "${REPO_ROOT}/claude-code/hooks/aa-ma-plan-marker.sh" \
                   "${CLAUDE_HOME}/hooks/lib/aa-ma-plan-marker.sh"
fi

# Back up settings.json once before first mutation.
backup_settings_once() {
    ${SETTINGS_BACKED_UP} && return 0
    if [ -f "${SETTINGS_FILE}" ] && ! ${FORCE}; then
        if ${DRY_RUN}; then
            info "Would back up ${SETTINGS_FILE} → ${SETTINGS_BACKUP}"
        else
            mkdir -p "${SETTINGS_BACKUP%/*}"
            cp -a "${SETTINGS_FILE}" "${SETTINGS_BACKUP}"
            info "Backed up ${SETTINGS_FILE} → ${SETTINGS_BACKUP}"
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
    aa_ma_hook_parse "${entry}"   # validated before anything changed (top of script)
    register_hook "${HOOK_EVENT}" "${HOOK_MATCHER}" "${HOOK_SRC}" "${HOOK_TIMEOUT}" "${HOOK_STATUS}"
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
# 7. codemem post-commit hook wiring (opt-in via --wire-git-hook)
# ---------------------------------------------------------------------------
# Task 1.11: two options to wire the codemem post-commit hook into the
# caller's current repo. We pick option (a): append a guarded line to
# .git/hooks/post-commit. Rationale:
#
#   (a) Append-to-.git/hooks/post-commit
#       Pros: preserves the user's existing post-commit hooks (if any).
#             Idempotent via a sentinel comment check.
#       Cons: only wires the CURRENT repo. Users in multi-repo
#             workflows must re-run --wire-git-hook per repo.
#
#   (b) git config core.hooksPath claude-code/codemem/hooks
#       Pros: one flip, repo-wide.
#       Cons: clobbers the user's hooksPath — if they already have
#             a custom hooks path (Husky, lefthook, pre-commit), our
#             config mutation silently disables theirs.
#
# We ship (a). Users who prefer (b) can set it manually — we document
# both trade-offs here so the choice is transparent.

if ${WIRE_GIT_HOOK}; then
    header "Wiring codemem post-commit hook (option (a))..."

    if ! git -C "${REPO_ROOT}" rev-parse --git-dir >/dev/null 2>&1; then
        warn "Not a git repo at ${REPO_ROOT} — skipping --wire-git-hook"
    else
        GIT_DIR="$(git -C "${REPO_ROOT}" rev-parse --git-dir)"
        # --git-dir prints a relative path when run from inside the
        # worktree; anchor it to the worktree for absolute safety.
        case "${GIT_DIR}" in
            /*) ABS_GIT_DIR="${GIT_DIR}" ;;
            *)  ABS_GIT_DIR="${REPO_ROOT}/${GIT_DIR}" ;;
        esac
        HOOK_FILE="${ABS_GIT_DIR}/hooks/post-commit"
        SOURCE_HOOK="${REPO_ROOT}/claude-code/codemem/hooks/post-commit.sh"
        SENTINEL="# codemem-post-commit-installed"

        if [ ! -f "${SOURCE_HOOK}" ]; then
            warn "Source hook missing: ${SOURCE_HOOK}"
        elif [ -f "${HOOK_FILE}" ] && grep -qF "${SENTINEL}" "${HOOK_FILE}"; then
            info "codemem post-commit hook already wired — ${HOOK_FILE}"
        else
            if ${DRY_RUN}; then
                info "Would append codemem post-commit hook to ${HOOK_FILE}"
            else
                # Ensure the hook file exists and is executable.
                if [ ! -f "${HOOK_FILE}" ]; then
                    printf '#!/usr/bin/env bash\n' > "${HOOK_FILE}"
                fi
                chmod +x "${HOOK_FILE}"

                # Append the guarded stanza. The sentinel comment lets
                # re-runs detect prior installation and skip.
                cat <<EOF >> "${HOOK_FILE}"

${SENTINEL}
if [ -x "${SOURCE_HOOK}" ]; then
    "${SOURCE_HOOK}" || true
fi
EOF
                info "Wired codemem post-commit hook → ${HOOK_FILE}"
            fi
        fi
    fi
fi

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
