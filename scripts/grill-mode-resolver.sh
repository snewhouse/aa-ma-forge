#!/usr/bin/env bash
# scripts/grill-mode-resolver.sh
#
# Resolves the grill-mode for /aa-ma-plan Phase 1.3 (skill-ecosystem-integration M1).
#
# Inputs (precedence: CLI > env > default):
#   --grill-mode=<value>          CLI flag
#   AA_MA_GRILL_MODE=<value>      Environment variable
#   (default: auto)
#
# Valid values: auto | with-docs | simple | skip
#
# Outputs:
#   stdout                        Resolved mode (one of: with-docs, simple, skip)
#   stderr                        Human-readable decision rationale
#
# Exit codes:
#   0   Success — resolved mode emitted to stdout
#   2   Invalid mode — error to stderr; "skip" emitted to stdout as safe default
#
# Auto-resolution rule (mode=auto only):
#   If CONTEXT.md exists at CWD root             → with-docs
#   Else if docs/adr/ exists and is readable     → with-docs
#   Else if docs/adr/ exists but unreadable      → simple (with WARN to stderr)
#   Else                                          → simple
#
# Force-mode rules (mode in {with-docs, simple, skip}):
#   Bypasses auto-detection; emits forced mode unconditionally.
#
# Backward compat:
#   Greenfield projects (no CONTEXT.md, no docs/adr/) resolve to 'simple', which
#   preserves identical behavior to /aa-ma-plan v0.5.0 (existing /grill-me protocol).

set -euo pipefail

GRILL_MODE="${AA_MA_GRILL_MODE:-auto}"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --grill-mode=*)
            GRILL_MODE="${1#*=}"
            shift
            ;;
        --grill-mode)
            GRILL_MODE="${2:-}"
            shift 2
            ;;
        *)
            shift
            ;;
    esac
done

case "$GRILL_MODE" in
    auto|with-docs|simple|skip)
        ;;
    *)
        echo "ERROR: invalid --grill-mode value: '${GRILL_MODE}' (valid: auto, with-docs, simple, skip)" >&2
        echo "Treating as 'skip' for safety; Phase 1.3 will be bypassed." >&2
        echo "skip"
        exit 2
        ;;
esac

case "$GRILL_MODE" in
    with-docs)
        echo "GRILL-MODE: with-docs (forced via --grill-mode/AA_MA_GRILL_MODE)" >&2
        echo "with-docs"
        exit 0
        ;;
    simple)
        echo "GRILL-MODE: simple (forced via --grill-mode/AA_MA_GRILL_MODE)" >&2
        echo "simple"
        exit 0
        ;;
    skip)
        echo "GRILL-MODE: skip (Phase 1.3 bypassed via --grill-mode/AA_MA_GRILL_MODE)" >&2
        echo "skip"
        exit 0
        ;;
esac

# auto-detection branch
if [[ -f CONTEXT.md ]]; then
    echo "GRILL-MODE: with-docs (auto: CONTEXT.md found at $(pwd))" >&2
    echo "with-docs"
    exit 0
fi

if [[ -d docs/adr ]]; then
    if [[ -r docs/adr ]] && [[ -x docs/adr ]]; then
        echo "GRILL-MODE: with-docs (auto: docs/adr/ found and readable at $(pwd)/docs/adr)" >&2
        echo "with-docs"
        exit 0
    else
        echo "WARN: docs/adr/ exists at $(pwd)/docs/adr but is not readable; falling back to simple grill-me protocol" >&2
        echo "GRILL-MODE: simple (auto: docs/adr/ unreadable — see WARN)" >&2
        echo "simple"
        exit 0
    fi
fi

echo "GRILL-MODE: simple (auto: no CONTEXT.md and no docs/adr/ at $(pwd))" >&2
echo "simple"
exit 0
