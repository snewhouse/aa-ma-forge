---
name: llm-output-safety
description: "Production safety requirements for pipelines that put LLM-generated text into client-facing outputs: non-Latin character sanitization, programmatic citation integrity, and treating recurring issues as architectural deficiencies. Use when generating reports, exports, or any client-facing document from LLM output."
---

# LLM Output Safety Rules

Derived from lessons L-050, L-051, L-052. These are production safety requirements for any pipeline that uses LLM-generated text in client-facing outputs.

## Non-Latin Character Sanitization (L-050)

**Trigger:** Any LLM-generated text destined for English-language reports or exports.

**Requirements:**
- Detect and flag non-Latin script characters (CJK, Cyrillic, Arabic, etc.) in English outputs
- Strip or replace with appropriate English text
- Log every sanitization event for audit trail
- Run at the boundary between LLM response generation and report assembly
- Integration point: the post-processing method that is the universal boundary across all analyzers

**Why:** LLM training data leaks (e.g., Chinese character "犬" appearing in an English veterinary report) destroy ALL credibility.

## Citation Integrity (L-051)

**Requirements:**
- Citation assignment MUST be **programmatic and deterministic**, not LLM-dependent
- Post-generation validation: verify cited reference IDs exist in the reference list
- Cardinality rules: flag >5 citations per paragraph as suspicious, >10 as certain hallucination
- LLMs are fundamentally unreliable at citation attribution — this must be a system-level guarantee

## Recurring Issues = Architectural Deficiency (L-052)

**Rule:** When the same CLASS of issue appears in 2+ independent QA reviews, treat it as an **architectural deficiency** requiring structural redesign, not a per-report bug fix.

**Required architectural responses:**
- Timeout resilience: critical systems must have retry logic with extended timeouts
- Citation pipeline: fully programmatic with deterministic numbering
- Output validation: LLM text must pass validation before export (non-ASCII, citation patterns, consistency)
- Executive summary cross-validation: programmatically verify claims match structured analysis data
