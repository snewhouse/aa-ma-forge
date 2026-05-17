# Playwright Skill Reference

Immutable facts and constants for skill implementation.

## File Locations

- **Skill Directory:** `/home/sjnewhouse/.claude/skills/playwright-testing/`
- **Main Skill File:** `SKILL.md` (< 500 lines)
- **Reference Files:** `PATTERNS.md`, `CONFIGURATION.md`, `GOTCHAS.md`, `EXAMPLES.md`

## Skill Metadata (YAML Frontmatter)

```yaml
---
name: playwright-testing
description: Production-grade Playwright testing for E2E, API, and component tests.
  Use for browser automation, visual regression, cross-browser testing, page object
  model, fixtures, locator strategies, and CI/CD integration. Covers getByRole,
  getByText, test isolation, authentication reuse, and debugging.
---
```

## Trigger Patterns

### Keywords (promptTriggers.keywords)
```json
[
  "playwright", "e2e", "end-to-end", "browser testing",
  "visual testing", "screenshot", "component testing",
  "page object", "locator", "getByRole", "getByText",
  "test automation", "browser automation", "cross-browser"
]
```

### Intent Patterns (promptTriggers.intentPatterns)
```json
[
  "(write|create|add|implement).*?(e2e|end.to.end|playwright).*?test",
  "(test|verify|check).*?(ui|user interface|browser|page)",
  "(automate|automation).*?(browser|web|testing)",
  "visual.*?(regression|testing|comparison)",
  "page.*?object.*?(model|pattern)"
]
```

### File Triggers (fileTriggers.paths)
```json
[
  "**/*.spec.ts", "**/*.spec.js",
  "**/playwright.config.*",
  "**/e2e/**", "**/tests/**",
  "**/playwright/**"
]
```

## Playwright Core Concepts

### Locator Priority (Official Best Practice)
1. `page.getByRole()` - Accessibility-first, most resilient
2. `page.getByText()` - User-visible text
3. `page.getByLabel()` - Form labels
4. `page.getByPlaceholder()` - Input placeholders
5. `page.getByTestId()` - Stable test identifiers
6. `page.locator()` with CSS - Last resort
7. XPath - Avoid

### Web-First Assertions (Auto-Retry)
```typescript
// ✅ Correct - auto-retries until condition met
await expect(page.getByText('welcome')).toBeVisible();

// ❌ Wrong - no retry, immediate evaluation
expect(await page.getByText('welcome').isVisible()).toBe(true);
```

### Built-in Fixtures
- `page` - Isolated page per test
- `context` - Isolated browser context per test
- `browser` - Shared browser instance
- `browserName` - 'chromium' | 'firefox' | 'webkit'
- `request` - API request context

### Browser Support
- Chromium (Chrome, Edge)
- Firefox
- WebKit (Safari)

### Node.js Requirements
- Node.js 20.x, 22.x, or 24.x

## Content Structure Standards

### SKILL.md Sections (Required)
1. Purpose & When to Use
2. Quick Start (minimal example)
3. Locator Strategy Hierarchy
4. Core Assertions
5. Page Object Pattern (summary)
6. Test Isolation
7. Configuration Essentials
8. Critical Gotchas (top 5)
9. Related Skills
10. Reference Files

### Reference File Structure
- Table of contents at top if > 100 lines
- Clear section headers with `##`
- Code examples with language tags
- Anti-patterns marked with `// ❌`
- Best practices marked with `// ✅`

## Line Count Limits

| File | Max Lines | Notes |
|------|-----------|-------|
| SKILL.md | 500 | Anthropic hard limit |
| PATTERNS.md | 800 | Can be longer, has TOC |
| CONFIGURATION.md | 600 | Config reference |
| GOTCHAS.md | 500 | Common pitfalls |
| EXAMPLES.md | 800 | Complete code examples |

## Related Skills

- `test-driven-development` - TDD workflow integration
- `debugging-strategies` - Debug failed tests

_Last Updated: 2025-12-23 10:53_
