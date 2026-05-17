# Playwright Skill Plan

**Objective:** Create a production-grade Playwright testing skill with progressive disclosure pattern
**Owner:** Claude Code / sjnewhouse
**Created:** 2025-12-23
**Last Updated:** 2025-12-23

## Executive Summary

Create a comprehensive Playwright testing skill following Anthropic's 500-line rule and progressive disclosure pattern. The skill will provide E2E, API, and component testing guidance with modern best practices (locator hierarchy, page object model, fixtures, CI/CD integration).

## Scope

### In Scope
- E2E testing fundamentals and patterns
- Locator strategy hierarchy (getByRole, getByText, getByTestId)
- Page Object Model pattern
- Custom fixtures and test isolation
- Visual regression testing
- API testing (standalone and hybrid E2E+API)
- Component testing (React, Vue, Svelte - experimental)
- CI/CD integration (GitHub Actions, sharding)
- Configuration reference (playwright.config.ts)
- Common gotchas and debugging strategies

### Out of Scope
- Framework-specific details beyond Playwright
- Mobile native testing (Appium)
- Performance testing tools
- Non-TypeScript/JavaScript implementations (Python/Java/.NET mentioned but not detailed)

## Success Criteria

1. SKILL.md is under 500 lines (following Anthropic best practices)
2. All reference files provide progressive disclosure
3. Trigger patterns activate on relevant prompts (e2e, playwright, browser testing)
4. Code examples are syntactically correct and runnable
5. Cross-references between files work correctly
6. Skill integrates with existing test-driven-development skill

## Architecture Decision

**Pattern:** Progressive disclosure following orchestration-coordination-framework model

```
skills/playwright-testing/
├── SKILL.md              # Core (< 500 lines)
├── PATTERNS.md           # Implementation patterns
├── CONFIGURATION.md      # Config reference
├── GOTCHAS.md            # Common pitfalls
└── EXAMPLES.md           # Complete code examples
```

**Rationale:**
- Matches existing skill patterns in repository
- Follows Anthropic's documented best practices
- Allows token-efficient loading (core file small, details on-demand)
- Easy to maintain and extend

## Dependencies

- No external dependencies
- Cross-references: test-driven-development, debugging-strategies skills

## Risks & Mitigations

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| SKILL.md exceeds 500 lines | Medium | Low | Aggressively move content to reference files |
| Playwright API changes | Low | Medium | Use only stable, documented APIs |
| Trigger false positives | Medium | Low | Test patterns thoroughly |
| Missing key use cases | Low | Medium | Iterate based on actual usage |

## Research Completed

### Sources Used
- https://playwright.dev/docs/intro - Core features
- https://playwright.dev/docs/best-practices - Best practices
- https://playwright.dev/docs/api-testing - API testing
- https://playwright.dev/docs/test-components - Component testing
- https://playwright.dev/docs/pom - Page Object Model
- https://playwright.dev/docs/test-fixtures - Fixtures
- https://playwright.dev/docs/test-configuration - Configuration

### Key Findings
1. Locator hierarchy: getByRole() > getByText() > getByTestId() > CSS/XPath
2. Web-first assertions with auto-retry are critical
3. Test isolation via browser contexts is fundamental
4. storageState enables authentication reuse
5. Component testing is experimental but valuable
6. Sharding enables CI/CD parallelization

## Next Action

Proceed to Milestone 1: Create SKILL.md (core skill file)
