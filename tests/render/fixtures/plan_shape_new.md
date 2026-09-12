# Fixture Plan
**Created:** 2026-09-11
**Diagram-Waiver:** none

## 13. Architecture View
### Component view
```mermaid
flowchart LR
  A[src/aa_ma/plan_parsers.py] --> B[("src/aa_ma/render/db.py (new)")]
  A --> C[["src/aa_ma/render/sub.py (new)"]]
```
### Flow view
```mermaid
sequenceDiagram
  A->>B: lint
```

### Milestone 1: Code
- Audit-Profile: code-only
- **Critical-Path:** data-xform
