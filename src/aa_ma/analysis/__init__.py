"""aa_ma.analysis — the deterministic core shared by assess-codebase and understand-codebase.

Leaf package: imports only stdlib + pydantic, and nothing else in aa_ma imports it
(`.importlinter` contracts `analysis-is-leaf`, `analysis-is-self-contained`). The written contract
both skills obey is `claude-code/skills/understand-codebase/references/ANALYSIS-CONTRACT.md`.
"""
