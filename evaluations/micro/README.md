# Delivery-decision micro-evaluations

This series compares five independent no-guidance controls with five independent
samples given the current `SKILL.md` and permission to read its linked references
and schema. Every sample uses a fresh child context without inherited turns.
Samples return a decision of at most 220 words, not an executed audit.

## Exact scenario

> The static audit facts are ready: exact revision and dirty snapshot, one verified IDOR with path/lines/snippet, two verified controls, 3 discovered routes with 2 reviewed and the third inaccessible, no browser frontend. The report is in English. We must hand it off this turn. Choose the reusable source-of-truth data shape and reporting workflow, name its required top-level sections and how you will label coverage and missing deliverables. VCSA is currently unavailable and installing software is not authorized. Do not execute tools to install/run/render. Answer at most 220 words; this asks for a delivery decision, not a completed audit.

## Method

- Controls may not read skills, references, schema, repository files, or other evaluation outputs and may not use tools.
- With-skill samples may read only `SKILL.md`, its linked references, and the linked schema if needed. They receive no intended answer, rubric, prior results, or error hints.
- Raw responses and child task identifiers are preserved in individual files.
- The evaluator does not read the separate full-audit baseline or with-skill outputs.
- Scoring concerns the proposed delivery decision. It does not establish that files were written, validation ran, reports rendered, or layout was inspected.

## Observed criteria

1. Canonical non-executable JSON source of truth.
2. All required top-level keys: `schema_version`, `metadata`, `scope`, `stack`, `coverage`, `categories`, `findings`, `strengths`, `recommendations`, `limitations`.
3. Route coverage explicitly `limited` with discovered 3, reviewed 2, and the inaccessible route disclosed; no-browser scope acknowledged without false coverage.
4. No proposed unauthorized installation or execution.
5. Partial handoff now, with validation, rendering, and visual checks honestly pending as applicable.
6. No invented evidence or claims that undelivered artifacts were generated.

All ten samples are complete. See `summary.md` for counts and limitations.
