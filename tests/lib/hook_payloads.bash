# hook_payloads.bash — real hook payloads captured live from Claude Code (M7.5).
# The fixtures in tests/fixtures/hook-payloads/ are scrubbed only of identity
# (home prefix, session/prompt/tool_use ids, scratchpad uid); every field name
# and shape is what Claude Code actually sent. tests/test_hook_payloads.py guards them.

HOOK_PAYLOADS="$(cd "${BATS_TEST_DIRNAME}/../fixtures/hook-payloads" && pwd)"

# payload <Event[-Matcher]> [jq options...] <filter> — that payload, edited by a jq filter.
payload() {
    local name="$1"; shift
    jq -c "$@" "${HOOK_PAYLOADS}/${name}.json"
}
