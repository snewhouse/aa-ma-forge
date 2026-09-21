#!/usr/bin/env bats
# fork-drift.bats — scripts/fork-drift.sh classifies against the manifest via a
# stubbed `gh` (GH= env seam). Only HTTP 404 may become ORPHAN.

setup() {
    REPO_ROOT="$(cd "${BATS_TEST_DIRNAME}/../.." && pwd)"
    SCRIPT="${REPO_ROOT}/scripts/fork-drift.sh"
    MANIFEST="${BATS_TEST_DIRNAME}/fixtures/forks/FORKS.json"
    WORK="$(mktemp -d "${BATS_TMPDIR}/fork-drift.XXXXXX")"
    # The stub returns base64("Hello") for alpha; the fixture's upstream_md5 is md5("Hello").
    HELLO_MD5="$(printf 'Hello' | md5sum | cut -d' ' -f1)"
}

teardown() { rm -rf "$WORK"; }

# $1 = stderr text + exit 1 for the beta file; alpha always returns base64("Hello").
make_stub() {
    cat > "$WORK/stub-gh" <<STUB
#!/usr/bin/env bash
case "\$*" in
  "api repos/mattpocock/skills --jq .full_name") echo mattpocock/skills ;;   # repo pre-flight
  *alpha/SKILL.md*) printf 'SGVsbG8=\n' ;;
  *beta/SKILL.md*)  echo "$1" >&2; exit 1 ;;
  *) echo "unexpected: \$*" >&2; exit 99 ;;
esac
STUB
    chmod +x "$WORK/stub-gh"
}

@test "GH=/nonexistent/gh → exit 1 with a message" {
    run env GH=/nonexistent/gh "$SCRIPT" --manifest "$MANIFEST"
    [ "$status" -eq 1 ]
    [[ "$output" == *"gh CLI not found"* ]]
}

@test "stub: alpha fetched, beta HTTP 404 → SAME and ORPHAN rows" {
    make_stub "gh: Not Found (HTTP 404)"
    run env GH="$WORK/stub-gh" "$SCRIPT" --manifest "$MANIFEST" --sha c55ee46
    [ "$status" -eq 0 ]
    [[ "$output" == *"alpha | SKILL.md | ${HELLO_MD5} | ${HELLO_MD5} | SAME"* ]]
    [[ "$output" == *"alpha | * | | | SAME"* ]]
    [[ "$output" == *"beta | SKILL.md | ${HELLO_MD5} | - | ORPHAN"* ]]
    [[ "$output" == *"beta | * | | | ORPHAN"* ]]
}

@test "stub: HTTP 403 → exit 1, never ORPHAN" {
    make_stub "gh: Forbidden (HTTP 403)"
    run env GH="$WORK/stub-gh" "$SCRIPT" --manifest "$MANIFEST"
    [ "$status" -eq 1 ]
    [[ "$output" == *"HTTP 403"* ]]
    [[ "$output" != *"ORPHAN"* ]]
}

@test "unknown flag → exit 2 usage" {
    run "$SCRIPT" --bogus
    [ "$status" -eq 2 ]
}

@test "malformed manifest (row missing files) → exit 1 naming the key, no rows" {
    make_stub "gh: Not Found (HTTP 404)"
    printf '{"x": {"upstream": "skills/x"}}\n' > "$WORK/bad.json"
    run env GH="$WORK/stub-gh" "$SCRIPT" --manifest "$WORK/bad.json"
    [ "$status" -eq 1 ]
    [[ "$output" == *"files"* ]]
    [[ "$output" != *"| * |"* ]]
}

@test "--help prints the whole header comment and no code" {
    run "$SCRIPT" --help
    [ "$status" -eq 0 ]
    [[ "$output" == *"never reported ORPHAN"* ]]
    [[ "$output" != *"set -euo"* ]]
}

@test "repo unreachable (404 on the repo itself) → exit 1, never ORPHAN" {
    cat > "$WORK/stub-gh" <<'STUB'
#!/usr/bin/env bash
echo "gh: Not Found (HTTP 404)" >&2; exit 1
STUB
    chmod +x "$WORK/stub-gh"
    run env GH="$WORK/stub-gh" "$SCRIPT" --manifest "$MANIFEST"
    [ "$status" -eq 1 ]
    [[ "$output" != *"ORPHAN"* ]]
}
