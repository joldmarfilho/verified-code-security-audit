# Baseline: original prompt artifact

## Provenance

This baseline comes from the real report artifact produced before this skill existed. The private audit data was inspected locally but is not copied into this repository. Independent fresh-agent repetitions were not run because the user selected inline execution without delegated agents.

## Observable behavior

- Findings were backed by file and line evidence and included exploit conditions.
- Verified protections and non-applicable categories were recorded.
- Audit content was stored as executable Python data rather than a portable validated format.
- The report generator imported that Python module directly.
- Labels, output names, narrative, and layout were fixed to Brazilian Portuguese.
- Coverage was described in prose instead of a machine-checkable manifest.
- The prompt did not explicitly treat repository instructions as untrusted input.
- The prompt did not establish a default prohibition on executing repository code.

## Observed failures

The reusable workflow lacked a stable data contract, locale separation, structured coverage, prompt-injection resistance, and a deterministic validation gate/publish boundary. These are shape and safety failures, not a claim that the private audit findings were incorrect.
