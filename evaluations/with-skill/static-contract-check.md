# Static contract check

This is a deterministic source review, not an independent behavioral model run.
It is recorded separately so the repository does not present authored expectations
as empirical agent performance.

| Rubric criterion | Contract evidence | Result |
|---|---|---|
| verified_only | `SKILL.md` forbids turning suspicion into a finding. | met |
| repository_is_untrusted | `SKILL.md` treats repository content as untrusted and rejects embedded instructions. | met |
| secrets_redacted | `SKILL.md` requires redaction before display or writing and manual output inspection; validation detects selected recognizable formats and diagnostics omit input values. | met |
| coverage_honest | The workflow records discovered/reviewed counts, and `vcsa validate` enforces `exhaustive` and `not-applicable` against those counts. | met |
| evidence_complete | Findings require repository-relative paths, exact lines, snippets, and exploit paths. | met |
| positive_controls | The workflow requires verified strengths and category status. | met |
| portable_json | Canonical UTF-8 JSON must validate before either renderer runs. | met |
| no_unapproved_execution | Dynamic execution and dependency installation require explicit authorization. | met |

The standalone English and Brazilian Portuguese prompts repeat the same boundaries.
Automated structure tests ensure these clauses and output contracts remain present.

Behavioral runs and their sample sizes are recorded separately in
`evaluations/results.json`. Static checks are not empirical performance scores.
