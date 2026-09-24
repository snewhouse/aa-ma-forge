# sigil-edges Plan

Fixture for the `PHANTOM_EDGE` tier (diagram-generation M8, map Ticket 5). Linted against a
throwaway repo built by `tests/render/test_phantom_edge.py`, where `src/app/a.py` imports
and calls `src/app/b.py`, and `scripts/run.sh` exists but is not in the graph.

## 13. Architecture View

### Component view

```mermaid
graph TD
    A["src/app/a.py"]
    B["src/app/b.py"]
    N["src/app/new.py (new)"]
    SH["scripts/run.sh"]
    K["claude-code/skills/x/SKILL.md"]
    G["group of things"]
    A -->|"@import"| B
    A -->|"@call"| B
    A -->|"@improt"| B
    A -->|fork| B
    A --> B
    A -->|"@import"| N
    A -->|"@import"| SH
    A -->|"@skill"| K
    G -->|"@import"| B
    classDef start stroke-width:4px
    class A start
```

### Flow view

Node ids are per fence: `A` here is a different file.

```mermaid
flowchart LR
    A["src/app/b.py"] -->|runs| C["src/app/a.py"]
```
