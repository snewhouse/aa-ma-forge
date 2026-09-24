"""Declared-external references of the plugin surface (diagram-generation M4).

A name here resolves outside this repo — ``~/.claude/skills``, gstack, a plugin
namespace, a Claude Code built-in — so a reference to it is a design choice, not a
defect (``claude-code/rules/engineering-standards.md`` §1, three-valued references).
An external reference NOT listed here classifies ``DANGLING``: loud on purpose.
Verified against ``~/.claude/skills`` and ``~/.claude/plugins`` on 2026-09-24.
"""

from __future__ import annotations

__all__ = ["EXTERNAL", "HOOK_TABLE"]

EXTERNAL: dict[str, frozenset[str]] = {
    "skill": frozenset({
        "api-spec-workflow", "ast-grep", "browse", "code-intelligence",
        "code-intelligence-index", "doc-drift-detection", "first-principles-framework",
        "gsd-intel", "gsd-map-codebase", "gsd-scan", "improve-codebase-architecture",
        "plan-ceo-review", "plan-design-review", "plan-eng-review",
        "python-testing-patterns", "qa-only", "secrets-management",
        "spec-driven-development", "test-driven-development", "ubiquitous-language",
        "feature-dev:feature-dev",  # plugin-namespaced: the feature-dev plugin's command
    }),
    "agent": frozenset({"Explore", "general-purpose", "gsd-codebase-mapper"}),
    "hook": frozenset({"aa-ma-share-allow.sh"}),  # ships from scripts/, not claude-code/hooks/
}

# The one place hooks are wired to events (``event|matcher|hook.sh|...`` rows).
HOOK_TABLE = "scripts/install.sh"
