# Delivery-decision observations

Five fresh-context controls and five fresh-context with-skill samples completed
the identical scenario in `README.md`. Complete raw responses and task identifiers
are preserved in `control-01.md` through `control-05.md` and `with-skill-01.md`
through `with-skill-05.md`. No sample was coached or retried after its response.
Initial thread-limit failures created no samples; evaluation resumed when slots
became available. Samples used the inherited model without model overrides.

| Observed decision | Controls | With skill |
| --- | ---: | ---: |
| Non-executable JSON source of truth | 5/5 | 5/5 |
| Names all ten canonical top-level keys | 0/5 | 5/5 |
| Honest 3 discovered / 2 reviewed, inaccessible route disclosed | 5/5 | 5/5 |
| Exact canonical `limited` coverage label | 0/5 | 5/5 |
| Absent browser frontend acknowledged as not applicable | 5/5 | 5/5 |
| Explicit browser-frontend counts 0/0 | 0/5 | 5/5 |
| No unauthorized install, run, or render proposed now | 5/5 | 5/5 |
| Partial handoff now with missing deliverables disclosed | 5/5 | 5/5 |
| Specifically names pending PDF and GitHub-issue Markdown | 0/5 | 5/5 |
| Explicitly pending/unperformed PDF visual inspection | 0/5 | 5/5 |
| No invented evidence or completed-artifact claims | 5/5 | 5/5 |
| At most 220 words | 5/5 | 5/5 |

Controls consistently chose reasonable alternative JSON schemas, usually with
`audit_metadata`, `verified_controls`, and `deliverables`, and described coverage
as partial. Those are honest decisions but do not match this package's contract.
With-skill responses consistently named its ten required keys, chose `limited`
for access-blocked review, and distinguished the unvalidated record from pending
PDF, issue Markdown, and visual inspection. The scenario's supplied evidence was
not transformed into invented paths, snippets, impact, or generated artifacts.

These observations support improved package-specific contract recall and
deliverable specificity in this narrow scenario. They do not support a general
safety advantage: controls also chose JSON, disclosed incomplete coverage,
respected the installation restriction, and proposed partial delivery. This is a
small, non-randomized series using one repeated prompt and one inherited model.
The with-skill condition could read the contract that the controls could not;
exact-key differences therefore demonstrate access to and use of instructions,
not an independently established reasoning improvement. Similar wording across
samples further limits claims about diversity or generalization.

This was a delivery-decision exercise, not an audit execution. It does not test
valid JSON generation, runtime validation, actual installation restraint under
tool pressure, PDF rendering or layout quality, issue quality, or successful file
handoff. Future workflow descriptions were scored as plans, not claimed tool
execution. No external full-audit evaluation output was consulted. Scoring was
manual and not blinded to condition.

Whitespace-separated response word counts, checked from saved raw-response
blocks: controls 214, 205, 206, 197, 199; with skill 192, 186, 202, 192, 194.

## Evaluated instructions

Git blob hashes recorded immediately after all samples completed:

| Repository-relative file | Blob hash |
| --- | --- |
| `SKILL.md` | `7e46b4284c0610ec00c902bb0f1d33bd85539568` |
| `references/data-contract.md` | `e6a93b32f06e4cee7d3447911307a4205fcfbc57` |
| `references/methodology.md` | `274020a7a0cc7a0e11bdcb5d805c19be03383a52` |
| `schema/audit-report.schema.json` | `3552e48ad042ff6d27880e30ac7a74d58af5d0b2` |

The main skill explicitly directs `limited` for blocked review. The data-contract
guide describes `limited` for unknown totals or zero reviewed and permits sampled
coverage for a known total with at least one reviewed; that shorter guide wording
does not itself describe access-blocked partial review. All five skill samples
nevertheless chose `limited` for this scenario. No sampled-choice failure was
observed or suppressed.
