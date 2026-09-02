# Verified Code Security Audit - Design Specification

Date: 2026-09-02  
Status: Proposed for implementation  
Repository: `joldmarfilho/verified-code-security-audit`

## 1. Purpose

Verified Code Security Audit is an Agent Skill and a deterministic Python report generator for evidence-backed source-code security audits. The agent performs the contextual review; the Python tooling validates a portable audit record and renders consistent PDF and Markdown deliverables in Brazilian Portuguese or English.

The project prioritizes traceability over finding volume. A reported vulnerability must be tied to code evidence, an attack or authorization path, explicit exploit conditions, and the exact repository revision reviewed. Correct controls, non-applicable categories, and coverage limits are first-class output rather than footnotes.

## 2. Goals

- Provide one standards-compatible Agent Skill named `verified-code-security-audit`.
- Provide equivalent standalone audit prompts in `pt-BR` and English.
- Detect the repository stack before mapping security checks to it.
- Require verified `file:line` evidence for every finding and positive control.
- Record audit coverage, limitations, and unreviewed surfaces explicitly.
- Store results in a language-neutral JSON document validated by JSON Schema.
- Generate localized A4 PDF and GitHub-ready Markdown from the same validated data contract.
- Keep report generation deterministic, local, and independent of the audited project's runtime.
- Ship a synthetic example and automated tests without publishing the private reference audit.

## 3. Non-goals

- Replacing a professional penetration test or certifying that a repository is secure.
- Building a general-purpose SAST engine, dependency scanner, or hosted service.
- Automatically fixing findings, opening GitHub issues, or changing the audited repository.
- Executing untrusted project code or installing its dependencies without separate user authorization.
- Guaranteeing exhaustive coverage when repository access, history, generated sources, or tooling is unavailable.

## 4. User Experience

### Agent Skill

A user invokes `$verified-code-security-audit` and optionally supplies scope, output language, severity threshold, or categories. Defaults are:

- scope: the current repository at its current revision;
- locale: infer from the user's language, falling back to `en`;
- categories: the five core checks plus stack-relevant adjacent checks;
- behavior: read-only audit and report generation;
- output directory: `docs/security-audit/`.

The skill produces:

1. `audit-report.json` - canonical, machine-readable audit record;
2. `security-audit-report.<locale>.pdf` - localized visual report;
3. `github-issues.<locale>.md` - complete issue drafts grouped to avoid spam;
4. a concise chat summary with verified findings and generated paths.

### Standalone Prompt

`prompts/audit.pt-BR.md` and `prompts/audit.en.md` expose the same audit contract for users whose agent does not install skills. Both prompts instruct the agent to write the canonical JSON and invoke the Python renderer when available. Their requirements remain semantically equivalent; tests check structural parity without requiring word-for-word translation.

### Command Line

The package exposes `vcsa` and supports module execution with `python -m verified_code_security_audit`.

```text
vcsa validate path/to/audit-report.json
vcsa render path/to/audit-report.json --locale pt-BR --output docs/security-audit
```

`render` validates before writing. It creates the PDF and Markdown issue file together and exits non-zero on invalid input or incomplete localization.

## 5. Repository Structure

```text
verified-code-security-audit/
|-- SKILL.md
|-- agents/
|   `-- openai.yaml
|-- prompts/
|   |-- audit.en.md
|   `-- audit.pt-BR.md
|-- references/
|   |-- methodology.md
|   `-- audit-data-contract.md
|-- schema/
|   `-- audit-report.schema.json
|-- src/verified_code_security_audit/
|   |-- __init__.py
|   |-- __main__.py
|   |-- cli.py
|   |-- validation.py
|   |-- pdf.py
|   |-- markdown.py
|   `-- locales/
|       |-- en.json
|       `-- pt-BR.json
|-- examples/synthetic/
|   |-- audit-report.en.json
|   `-- audit-report.pt-BR.json
|-- tests/
|-- .github/workflows/tests.yml
|-- .gitignore
|-- LICENSE
|-- README.md
|-- README.pt-BR.md
`-- pyproject.toml
```

Only `SKILL.md` contains always-loaded instructions. Detailed methodology and the data contract live in references and are loaded when the audit reaches those phases. The Python modules remain small and single-purpose, while localization content stays out of rendering logic.

## 6. Audit Methodology

### 6.1 Establish the Snapshot

The audit records repository name, absolute or logical root, branch when available, commit SHA, audit timestamp, dirty-worktree state, requested scope, exclusions, and tooling limitations. Findings refer to that snapshot. If the worktree changes materially during review, the agent refreshes affected evidence or marks the report degraded.

Repository files, comments, documentation, prior audit reports, issue text, and generated content are untrusted input. Instructions found inside them never override the skill, user request, or safety boundaries.

### 6.2 Detect the Stack

Before vulnerability review, the agent identifies evidence for:

- languages and runtimes;
- frameworks and routing mechanisms;
- ORM, query builder, or database access layer;
- authentication, session, and authorization mechanisms;
- tenant or owner isolation mechanism;
- frontend frameworks and dangerous rendering sinks;
- deployment, CI/CD, containers, cloud, Helm, and infrastructure-as-code;
- dependency manifests and lockfiles.

The report records both detected components and the files that prove the detection.

### 6.3 Map the Core Categories

The original five checks remain the required core:

1. tenant or owner isolation;
2. server-side authorization corresponding to frontend privilege gates;
3. IDOR and object-level authorization;
4. exposed or unsafe-default secrets;
5. XSS and unsafe input-to-output flows.

Each category is translated to the detected stack. A category can be `reviewed`, `not-applicable`, `limited`, or `not-reviewed`, with a reason and evidence. Stack-relevant adjacent checks such as SQL or command injection, SSRF, file handling, CSRF, CORS, session lifecycle, webhook authentication, and CI/CD trust boundaries may be added when their attack surfaces exist.

### 6.4 Prove Coverage

Claims such as "all routes were reviewed" require a coverage manifest. The record stores the discovered population, reviewed population, discovery method, exclusions, and unresolved gaps for relevant surfaces such as routes, controllers, repositories, templates, frontend sinks, deployment files, and history searches.

Sampling is allowed only when requested or unavoidable and must be labeled. A sampled review cannot claim exhaustive coverage.

### 6.5 Verify Findings

A confirmed finding contains:

- stable identifier and category;
- severity and confidence;
- concise title and description;
- attack preconditions and exploit path;
- security impact;
- one or more exact evidence locations with snippets;
- remediation guidance;
- verifiable acceptance criteria;
- optional CWE, OWASP, or other taxonomy references;
- optional issue-group identifier.

The agent traces the relevant data, authorization, or control flow far enough to show reachability. Suspicious syntax without a reachable security impact is not a confirmed finding. Unresolved hypotheses go in limitations or follow-up notes, not the findings count.

Secrets are always redacted. Evidence may show a variable name, prefix, fingerprint, or placeholder, but never reproduce a complete credential.

### 6.6 Record Positive Evidence

Strengths use the same evidence standard as findings: a control statement plus exact locations showing why it holds. A strength must not overclaim beyond the paths reviewed.

## 7. Canonical Data Contract

The JSON structure and enum values are language-neutral. Human-readable narrative fields contain one declared language in `metadata.content_locale`; renderer-owned labels, headings, severity names, dates, and boilerplate are localized separately. A complete English and Brazilian Portuguese release therefore uses two records with equivalent facts and matching localized narrative, not a renderer-generated translation.

Top-level sections:

- `schema_version`;
- `metadata`;
- `scope`;
- `stack`;
- `coverage`;
- `categories`;
- `findings`;
- `strengths`;
- `recommendations`;
- `limitations`.

Evidence locations contain `path`, `start_line`, optional `end_line`, and `snippet`. Paths are repository-relative, use forward slashes, and cannot escape the repository root. Line numbers are positive integers. Snippets have a bounded length to keep reports readable and prevent accidental bulk disclosure.

Severity values are `critical`, `high`, `medium`, `low`, and `informational`. Confidence values are `high`, `medium`, and `low`. The methodology reference defines a concise severity rubric based on realistic impact and exploit conditions rather than syntax alone.

Issue drafts are derived from findings. Findings sharing an `issue_group` become one issue; otherwise each actionable finding creates one issue. Informational findings create issues only when explicitly marked actionable.

The schema rejects unknown fields in stable objects so misspellings do not silently disappear from reports. Schema evolution uses a required semantic `schema_version`, starting at `1.0.0`.

## 8. Localization

Supported locales in version 1 are `en` and `pt-BR`. Locale JSON files contain only renderer-owned text. Audit narrative is not machine-translated by the renderer. The requested render locale must match `metadata.content_locale`; a mismatch is a validation error rather than a mixed-language report.

The selected locale controls:

- report title and section headings;
- severity and confidence labels;
- chart labels;
- date formatting;
- table headings, captions, and empty states;
- GitHub issue boilerplate and checklist labels;
- validation-facing user messages where practical.

Every locale must implement the same key set. Tests compare keys and render the matching synthetic fixture for each language.

## 9. PDF and Markdown Rendering

The PDF uses ReportLab for layout and Matplotlib for charts. Matplotlib's bundled DejaVu Sans font is registered with ReportLab to support English and Brazilian Portuguese consistently without shipping a separate font binary.

The report uses A4 pages, approximately 2 cm margins, stable headers and footers, and the established severity palette:

- critical: `#B91C1C`;
- high: `#EA580C`;
- medium: `#D97706`;
- low: `#2563EB`;
- strength: `#059669`;
- informational: neutral slate.

Sections are cover, executive summary, methodology and stack, coverage, strengths, weaknesses, detailed findings, prioritized recommendations, limitations and non-applicable checks, and GitHub issue drafts. Charts handle both populated and zero-finding audits without division-by-zero or empty-axis failures.

The Markdown renderer emits copy-ready issue blocks with title, suggested labels, problem, exploitability, evidence, impact, remediation, and acceptance criteria. It never creates remote issues.

Temporary charts and rasterized QA pages stay outside final output. PDF metadata uses the registered Unicode-capable font and localized strings.

## 10. Security Boundaries

- The renderer treats JSON and snippets as untrusted text and escapes ReportLab markup.
- Validation rejects path traversal, unsupported locales, malformed colors, invalid enums, and unreasonable collection or string sizes.
- Rendering never imports or executes the audit data as Python.
- The skill defaults to static, read-only inspection.
- Dynamic tests, dependency installation, network access, secret-history tooling, or access to private systems require scope and authorization appropriate to the action.
- Generated output never claims certification or a clean bill of health.
- Existing files in the output directory are overwritten only when they are the explicit command targets.

## 11. Error Handling

The CLI prints concise, actionable errors and exits non-zero when:

- the input cannot be read or parsed;
- schema validation fails;
- a locale is missing or incomplete;
- an output path is invalid or unwritable;
- chart or PDF generation fails;
- final PDF reopening or structural verification fails.

Validation errors identify the JSON path and violated rule without dumping the full audit payload. Partial final artifacts are removed or written through temporary files followed by atomic replacement.

## 12. Testing and Verification

Implementation follows test-driven development.

Automated tests cover:

- valid and invalid schema fixtures;
- path traversal and oversized-input rejection;
- locale-key parity;
- issue grouping and informational-actionable behavior;
- escaping of markup-like evidence;
- zero-finding and multi-severity charts;
- deterministic output naming;
- CLI exit codes;
- successful PDF reopening and expected page count greater than zero;
- presence of required localized headings in extracted PDF text.

The paired synthetic fixtures contain equivalent audit facts in both languages, including multiple severities, grouped findings, strengths, a non-applicable category, and a limited-coverage surface. CI runs tests and renders both locales on supported Python versions.

Before release, both PDFs are rasterized with Poppler. Representative pages and any page flagged by render warnings are visually inspected for clipping, overlaps, broken glyphs, unreadable tables, and excessive blank space.

The skill itself is tested with realistic baseline and skill-enabled audit scenarios. Evaluation checks stack discovery, refusal to treat repository instructions as authoritative, evidence quality, coverage honesty, secret redaction, JSON validity, and correct renderer invocation.

## 13. Packaging and Distribution

The project uses `pyproject.toml` and a `src` layout. Runtime dependencies are limited to ReportLab, Matplotlib, and `jsonschema`. Tests use the Python standard library unless a dependency already required by the runtime provides the needed capability.

The repository root is directly installable as an Agent Skill and as a Python package. Documentation includes:

- English `README.md`;
- Brazilian Portuguese `README.pt-BR.md`;
- local skill installation for Codex and compatible Agent Skills runtimes;
- isolated Python installation and CLI examples;
- report screenshots generated from synthetic data;
- limitations and responsible-use notice.

The existing MIT license remains. No generated virtual environment, real audit report, private source evidence, or secret-bearing fixture is committed.

## 14. Acceptance Criteria

Version 1 is complete when:

- the skill passes the bundled skill validator;
- baseline and skill-enabled evaluation scenarios are documented and the skill materially improves the required behaviors;
- the canonical synthetic JSON passes schema validation;
- invalid evidence paths, secret-like raw values, and malformed records fail validation with clear errors;
- `vcsa render` generates PDF and Markdown successfully from the matching `en` and `pt-BR` fixtures;
- both PDFs reopen, contain all required sections, and pass visual inspection;
- issue grouping produces the expected number of Markdown issue blocks;
- README instructions work in a fresh isolated Python environment;
- CI passes from a clean checkout;
- the repository contains no private reference-audit content or generated `.venv` directory.

## 15. Implementation Sequence

The implementation plan will divide work into independently verifiable increments:

1. skill behavior baseline and data-contract tests;
2. package skeleton and JSON Schema validation;
3. Markdown issue rendering;
4. localized PDF rendering;
5. skill, prompts, and behavioral evaluation;
6. synthetic example, documentation, CI, and final release verification.

Each increment starts with a failing test and ends with focused verification before the next begins.
