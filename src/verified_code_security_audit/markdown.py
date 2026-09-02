"""Render deterministic, localized GitHub issue drafts from audit records."""

from __future__ import annotations

import re
from collections.abc import Mapping

_SEVERITY_ORDER = {
    "critical": 0,
    "high": 1,
    "medium": 2,
    "low": 3,
    "informational": 4,
}


def group_actionable_findings(
    report: Mapping[str, object],
) -> list[list[Mapping[str, object]]]:
    """Group actionable findings in source order using the optional issue key."""

    grouped: dict[str, list[Mapping[str, object]]] = {}
    for finding in report["findings"]:  # type: ignore[union-attr]
        if not finding["actionable"]:
            continue
        key = finding.get("issue_group") or f"finding:{finding['id']}"
        grouped.setdefault(str(key), []).append(finding)
    return list(grouped.values())


def _fenced(snippet: object) -> str:
    text = str(snippet)
    longest_run = max(
        (len(match.group(0)) for match in re.finditer(r"`+", text)),
        default=0,
    )
    fence = "`" * max(3, longest_run + 1)
    return f"{fence}text\n{text}\n{fence}"


def _location(evidence: Mapping[str, object]) -> str:
    start = evidence["start_line"]
    end = evidence.get("end_line")
    suffix = str(start) if end in (None, start) else f"{start}-{end}"
    return f"{evidence['path']}:{suffix}"


def _unique_strings(values: list[object]) -> list[str]:
    return list(dict.fromkeys(str(value) for value in values))


def render_issues(
    report: Mapping[str, object], strings: Mapping[str, str]
) -> str:
    """Return localized, copy-ready issue blocks ending in exactly one newline."""

    groups = group_actionable_findings(report)
    if not groups:
        return f"{strings['issue.none']}\n"

    blocks: list[str] = []
    for number, group in enumerate(groups, start=1):
        severity = min(
            (str(item["severity"]) for item in group),
            key=_SEVERITY_ORDER.__getitem__,
        )
        localized_severity = strings[f"severity.{severity}"]
        titles = "; ".join(str(item["title"]) for item in group)

        problem = "\n".join(
            f"- **{item['id']} — {item['title']}**: {item['description']}"
            for item in group
        )
        exploitability = "\n".join(
            f"- **{item['id']}**: {item['exploit_path']} "
            f"({' '.join(str(value) for value in item['preconditions'])})"
            for item in group
        )

        evidence_parts: list[str] = []
        for item in group:
            for evidence in item["evidence"]:
                evidence_parts.append(
                    f"- **{item['id']} — {_location(evidence)}**\n\n"
                    f"{_fenced(evidence['snippet'])}"
                )

        impact = "\n".join(
            f"- **{item['id']}**: {item['impact']}" for item in group
        )
        remediation = "\n".join(
            f"- **{item['id']}**: {item['remediation']}" for item in group
        )
        criteria = _unique_strings(
            [criterion for item in group for criterion in item["acceptance_criteria"]]
        )
        acceptance = "\n".join(f"- [ ] {criterion}" for criterion in criteria)

        blocks.append(
            "\n".join(
                [
                    f"--- {strings['issue.start']} {number} ---",
                    "",
                    f"# [{strings['issue.title_prefix']}][{localized_severity}] {titles}",
                    "",
                    f"## {strings['issue.labels']}",
                    "",
                    f"`security`, `severity:{severity}`",
                    "",
                    f"## {strings['issue.problem']}",
                    "",
                    problem,
                    "",
                    f"## {strings['issue.exploitability']}",
                    "",
                    exploitability,
                    "",
                    f"## {strings['issue.evidence']}",
                    "",
                    "\n\n".join(evidence_parts),
                    "",
                    f"## {strings['issue.impact']}",
                    "",
                    impact,
                    "",
                    f"## {strings['issue.remediation']}",
                    "",
                    remediation,
                    "",
                    f"## {strings['issue.acceptance']}",
                    "",
                    acceptance,
                    "",
                    f"--- {strings['issue.end']} {number} ---",
                ]
            )
        )

    return "\n\n".join(blocks) + "\n"
