# Canonical Audit Data Contract

## Contents

1. Source of truth
2. File and locale rules
3. Top-level sections
4. Evidence records
5. Categories, findings, and strengths
6. Recommendations and limitations
7. Complete safe finding example
8. Validation and rendering loop

## 1. Source of truth

[`schema/audit-report.schema.json`](../schema/audit-report.schema.json) is the
normative contract. This guide explains intent but does not replace the schema.
Generate JSON objects, never executable Python data files.

The current `schema_version` is `1.0.0`. Unknown keys are rejected in stable
objects so a typo cannot silently disappear from a report.

## 2. File and locale rules

Write UTF-8 JSON as `audit-report.<locale>.json`. Supported locale values are:

- `en` for English narrative text;
- `pt-BR` for Brazilian Portuguese narrative text.

`metadata.content_locale` must match the filename and the locale passed to the
renderer. Identifiers, enum values, paths, and source snippets remain stable
technical data; translate narrative names, descriptions, summaries, remediation,
criteria, and limitations.

All evidence and affected paths are POSIX-style and repository-relative. Never
use a leading slash, drive letter, backslash, or `..` segment.

## 3. Top-level sections

Every report contains all sections, including empty arrays where appropriate:

### `metadata`

- `project_name`: display name;
- `repository`: stable repository identifier or URL;
- `revision`: exact reviewed revision;
- `branch`: branch name or null;
- `audited_at`: RFC 3339 date-time;
- `worktree_dirty`: whether uncommitted content was in scope;
- `content_locale`: `en` or `pt-BR`.

### `scope`

- `summary`: concise boundary of the review;
- `included_paths`: paths intentionally reviewed;
- `excluded_paths`: objects containing `path` and `reason`.

### `stack`

Each component has a technical `kind`, display `name`, optional `version`, and at
least one evidence record. Do not infer versions.

### `coverage`

Each record contains:

- `surface`: stable name such as `api-routes`;
- `status`: `exhaustive`, `sampled`, `limited`, or `not-applicable`;
- `discovered`: known total or null;
- `reviewed`: non-negative reviewed count;
- `method`: how items were found and checked;
- `exclusions`: precise omissions or constraints.

`reviewed` cannot exceed a known `discovered` count. Validation also enforces the
meaning of each status: `exhaustive` requires a known `discovered` count equal to
`reviewed`, and `not-applicable` requires both counts to be zero. `sampled`
requires a known discovered count and at least one reviewed item. Use `limited`
for unknown totals or when no items could be reviewed.

### `categories`

Each category has a stable slug `id`, localized `name`, status `reviewed`,
`not-applicable`, `limited`, or `not-reviewed`, a `summary`, and supporting
`evidence`. Categories exist even when no vulnerability is found.

### `findings`

Each finding records a verified security observation. Required fields are:

- stable `id` and existing `category_id`;
- `severity` and `confidence`;
- localized `title` and `description`;
- `preconditions`, `exploit_path`, and `impact`;
- non-empty `evidence`;
- `remediation` and non-empty `acceptance_criteria`;
- `actionable` boolean;
- optional `issue_group` for related actionable findings;
- external `references`, such as CWE identifiers.

Use `informational` plus `actionable: false` for a verified observation that
should not become an issue. Do not use findings for unverified suspicions.

### `strengths`

Each strength has `title`, `description`, and non-empty exact `evidence`. Positive
claims require the same verification discipline as vulnerabilities.

### `recommendations`

Each recommendation has stable `id`, priority `P1`, `P2`, or `P3`, localized
`title` and `details`, and non-empty `finding_ids`. Every referenced finding must
exist.

### `limitations`

Each limitation has `title`, `details`, and `affected_paths`. Declare unavailable
history, excluded services, prohibited dynamic testing, and incomplete coverage.

## 4. Evidence records

An evidence record contains:

- `path`: repository-relative source path;
- `start_line`: one-based first line;
- optional `end_line`: one-based last line, not before `start_line`;
- `snippet`: the shortest useful code excerpt.

Line numbers refer to `metadata.revision` plus any declared dirty worktree state.
Keep snippets under the schema limit. Preserve code exactly except for credentials:
replace every sensitive value with `[REDACTED]` before displaying or writing it.
For structurally valid records, validation scans every string value, not only
snippets, for selected recognizable secret formats. It does not detect every
password, token format, encoded value, or secret split across fields. Manually
inspect all outputs. Schema and semantic diagnostics omit input values; validation
success is not a guarantee that the report contains no secrets.

Long snippet lines are wrapped when rendered to PDF, so a wide line is never
clipped off the page. Prefer the shortest excerpt that proves the point anyway.

## 5. Categories, findings, and strengths

A finding's `category_id` must match a category. A category can be reviewed with
zero findings and should then explain what was checked. Stack and category
evidence may overlap when the same line proves both facts, but do not manufacture
duplicate evidence to inflate coverage.

`issue_group` is a stable technical identifier. Give related actionable findings
the same value only when one GitHub issue can remediate them without losing
distinct paths, impacts, or acceptance criteria.

## 6. Recommendations and limitations

Sort recommendations by operational urgency:

- `P1`: contain a verified high-risk path or exposed credential;
- `P2`: reduce meaningful risk after immediate containment;
- `P3`: hardening, regression protection, or longer-term improvement.

Priority is not severity. One recommendation may address multiple related
findings, and more than one recommendation may reference a finding.

Limitations describe what the report cannot establish. They do not excuse a false
coverage claim and must name the affected path or surface when known.

## 7. Complete safe finding example

```json
{
  "id": "F1",
  "category_id": "tenant-isolation",
  "severity": "high",
  "confidence": "high",
  "title": "Booking lookup does not filter by organization",
  "description": "A booking is fetched without authenticated organization scope.",
  "preconditions": [
    "An authenticated user knows another booking identifier."
  ],
  "exploit_path": "GET /bookings/{id} reaches an unscoped repository lookup.",
  "impact": "A user can read a booking belonging to another organization.",
  "evidence": [
    {
      "path": "app/api/bookings.py",
      "start_line": 42,
      "end_line": 42,
      "snippet": "return repository.get_by_id(booking_id)"
    },
    {
      "path": "config/env.example",
      "start_line": 4,
      "end_line": 4,
      "snippet": "JWT_SIGNING_KEY=[REDACTED]"
    }
  ],
  "remediation": "Filter by booking id and authenticated organization id.",
  "acceptance_criteria": [
    "A cross-organization booking id returns 404.",
    "A same-organization booking remains accessible."
  ],
  "actionable": true,
  "issue_group": "tenant-authorization",
  "references": ["CWE-639"]
}
```

The second evidence item demonstrates redaction syntax only. Include it in a real
finding only when it directly supports that finding.

## 8. Validation and rendering loop

Validate before rendering:

```text
vcsa validate audit-report.en.json
```

Correct structural and semantic errors supported by available evidence. If tools,
permissions, or missing evidence prevent progress, stop retrying and report partial
results with pending deliverables. Never invent evidence to satisfy the schema.
After validation succeeds, render from the same file:

```text
vcsa render audit-report.en.json --locale en --output docs/security-audit
```

For Brazilian Portuguese, use `audit-report.pt-BR.json` and `--locale pt-BR`.
Never hand-edit the generated PDF or issue Markdown; update the canonical JSON,
validate again, and regenerate both outputs.
