#!/usr/bin/env bash
# PostToolUse(Edit|Write): format + autofix edited .py files with ruff. Advisory — never blocks.
# Why log to a file, not stdout/stderr: PostToolUse output is fed back to the model on every
# edit; a file keeps failures visible (tail ~/.claude/logs/hooks.log) without that noise.
[[ "${AA_MA_HOOKS_DISABLE:-0}" == "1" ]] && exit 0   # master kill switch, like every AA-MA hook
LOG="${CLAUDE_HOOK_LOG:-$HOME/.claude/logs/hooks.log}"
f=$(jq -r '.tool_input.file_path // empty')
[[ "$f" == *.py && -f "$f" ]] && command -v ruff >/dev/null || exit 0
# Fix first, then format: ruff's documented order, so autofix output is formatted too.
# Why only format failures are logged: format exits non-zero only on syntax errors / bad config.
# `ruff check` exiting 1 just means unfixed lint remains, which is normal, not a failure.
ruff check --fix --unfixable F401,F841 --quiet -- "$f" >/dev/null 2>&1
if ! out=$(ruff format -- "$f" 2>&1); then
  mkdir -p "${LOG%/*}"
  printf '%s ERROR ruff-format: %s: %s\n' "$(date -Is)" "$f" "${out//$'\n'/ | }" >>"$LOG"
fi
exit 0
