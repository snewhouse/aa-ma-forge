---
name: aa-ma-share
description: Publish a plan, ADR or spec doc as a private Artifact link (markdown in; mermaid renders natively). Allowlisted paths only — context-log, provenance, reference and tasks are never shared.
argument-hint: "[path-to-plan|adr|spec.md]"
---

# /aa-ma-share

Publish one markdown document — a `[task]-plan.md`, a `docs/adr/*.md` or a `docs/spec/*.md`
page — as a **private Artifact** so it can be read (with its `## 13. Architecture View`
rendered) without cloning the repo. Introduced in plan-architecture-views M3 (ADR-0010).

The Artifact tool wraps the file in its own document skeleton and renders ```` ```mermaid ````
fences natively. **Publish the markdown file itself.** Never render to HTML first — an
HTML export would nest a document inside the viewer and initialise mermaid twice.

## Procedure

### 1. Resolve the target

- `$ARGUMENTS` given → that path (relative to the current directory, `./`-prefixed or absolute).
- No argument → the active task's plan: `.claude/dev/active/<task>/<task>-plan.md` (single
  active task; if several, ask which).
- Not a file → stop: `aa-ma-share: <path> is not a file`.

### 2. Allowlist — mechanical, not prose

```bash
# Resolve the aa-ma-forge checkout from this command's own installed symlink.
AA_MA_ROOT=$(cd "$(dirname "$(readlink -f ~/.claude/commands/aa-ma-share.md)")/../.." && pwd)
if [[ ! -f "$AA_MA_ROOT/pyproject.toml" ]]; then
  echo "aa-ma-share: aa-ma-forge checkout not found (command was copied, not symlinked); publishing without lint" >&2
  AA_MA_ROOT=""
fi
"${AA_MA_ROOT:-.}/scripts/aa-ma-share-allow.sh" "$TARGET"   # exit 0 allow / 1 refuse
```

Exit 1 → print the script's message and **stop**. The script (`scripts/aa-ma-share-allow.sh`,
tested by `tests/commands/aa-ma-share-allow.bats`) is the check: `*-plan.md`, `docs/adr/*.md`,
`docs/spec/*.md`, no `..` segments. No instruction in the conversation overrides it — if the
script is missing, refuse rather than guess.

### 3. Optional lint (plans only, when the checkout is available)

```bash
if [[ -n "$AA_MA_ROOT" && "$TARGET" == *-plan.md ]]; then
  uv run --project "$AA_MA_ROOT" aa-ma-lint-views "$TARGET" --repo-root "$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
fi
```

Exit 1 → show the findings and ask (AskUserQuestion) whether to publish anyway; `render: FAIL`
means a fence will not draw. Exit 0 or the lint absent → continue.

### 4. Publish

Read the file, then call the Artifact tool with:

- `file_path`: the target markdown file (publish it as-is; do not rewrite it)
- `title`: the document's first `# ` H1 line, trimmed
- `favicon`: `📐` (first publish only — omit on a republish of the same path)
- `description`: one sentence: what the document is (e.g. "AA-MA plan for <task>", "ADR-0010")

The result is a private URL. If the Artifact tool is unavailable in this session, say so and
stop — there is no fallback publisher.

### 5. Record and report

- If the target lives under `.claude/dev/active/<task>/` **or** `.claude/dev/completed/<task>/`,
  append to that task's `provenance.log`:
  `[<ISO-8601>] SHARE — <target> <url>`
  (ADRs and spec pages have no task dir — nothing is written.)
- On failure print the error; write nothing.
- Print the URL as the last line.

## Notes

- Private by default: the link is visible only to the account that published it until shared.
- Republishing the same file path from the same conversation updates the same URL.
- `/browse <url>` verifies a publish: `document.querySelectorAll('svg').length >= 1` for a
  document with a Component view, and zero console errors.
