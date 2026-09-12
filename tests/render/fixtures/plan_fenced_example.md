# Fixture Plan
**Created:** 2026-09-11
**Diagram-Waiver:** none

## 13. Architecture View
### Component view
```mermaid
flowchart LR
  A[src/aa_ma/plan_parsers.py] --> B["src/aa_ma/render/mermaid_lint.py (new)"]
```
### Flow view
```mermaid
sequenceDiagram
  A->>B: lint
```

### Milestone 1: Docs
- Audit-Profile: docs-only

Example of the field:

```markdown
- Audit-Profile: code-only
- **Critical-Path:** data-xform
```
