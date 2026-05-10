# Lessons Learned (aa-ma-forge)

Project-local pattern + prevention rules. Reviewed at session start.
Newest at top. See also: `~/.claude/rules/self-improvement-loop.md`.

---

## L-001 (2026-05-10) — External URL First Principle

**Pattern:** During `/aa-ma-plan` for skill-ecosystem-integration, a Phase 3
research agent was dispatched to audit "mattpocock/skills" without being
given the URL. The agent looked at locally-installed `anthropic-agent-skills`
plugin contents and concluded "this is Anthropic's catalog, not mattpocock".
The conclusion was wrong — `mattpocock/skills` is a real GitHub repo with
68k stars and 17 production skills, including the canonical `grill-with-docs`
and `grill-me`. The misattribution propagated into the AA-MA plan's
executive summary, M2 description, and Assumption A5. The user caught it
("did you read https://github.com/mattpocock/skills/tree/main in detail?")
and demanded re-work ("do not be lazy like this again").

**Rule:** When a user explicitly names a specific external source — a GitHub
URL, an RFC number, a vendor doc URL, a paper DOI — the planning process
MUST fetch that source directly BEFORE any agent delegation. For GitHub:
use `gh api repos/<owner>/<repo>/contents` to enumerate and
`gh api .../SKILL.md --jq .content | base64 -d` for individual files. For
other URLs: WebFetch with a tight prompt.

Only dispatch research agents AFTER the canonical inventory is captured.
The agent's job is then synthesis/comparison against ground truth, not
discovery. The agent prompt must include the verified inventory as
ground-truth context to prevent hallucination on the source's identity.

**Why this matters:** Conflation between locally-installed skills and the
upstream they were sourced from is the silent default failure mode. Two
plugins with the same skill name can come from different repos; one repo
can be a subset/superset of another; aliases and curators (mattpocock,
anthropic-agent-skills) can muddy attribution. The only authoritative
answer is the URL the user named.

**How to apply:**
- Trigger keyword: any URL in the user message; any phrase like "the X repo"
  or "the X catalog" where X is a named external entity.
- First call after Phase 1.2 context-gathering: fetch the named URL.
- Embed the verified inventory in any subsequent agent prompt as
  ground-truth context.
- Save the inventory in the AA-MA `reference.md` so re-dispatches don't
  re-discover.

---
