from __future__ import annotations

import json
import re
import sysconfig
from collections.abc import Iterable, Mapping
from pathlib import Path, PurePosixPath
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker


class AuditValidationError(ValueError):
    """One or more audit-record validation failures."""

    def __init__(self, errors: list[str]) -> None:
        self.errors = tuple(errors)
        super().__init__("; ".join(errors))


_RAW_SECRET_PATTERNS = (
    re.compile(r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\b(?:gh[pousr]_|github_pat_)[A-Za-z0-9_]{20,}\b"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"\bxox[baprs]-[0-9A-Za-z-]{10,}\b"),
    re.compile(r"\bglpat-[0-9a-zA-Z_-]{20,}\b"),
)


def schema_path() -> Path:
    source_path = Path(__file__).resolve().parents[2] / "schema" / "audit-report.schema.json"
    if source_path.is_file():
        return source_path
    installed_path = (
        Path(sysconfig.get_path("data"))
        / "share"
        / "verified-code-security-audit"
        / "schema"
        / "audit-report.schema.json"
    )
    if installed_path.is_file():
        return installed_path
    raise AuditValidationError(["audit-report.schema.json is not installed"])


def load_report(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise AuditValidationError([f"cannot read audit JSON: {exc}"]) from exc
    if not isinstance(value, dict):
        raise AuditValidationError(["audit JSON root must be an object"])
    return value


def _json_path(parts: Iterable[object]) -> str:
    path = "$"
    for part in parts:
        path += f"[{part}]" if isinstance(part, int) else f".{part}"
    return path


def _schema_errors(report: Mapping[str, Any]) -> list[str]:
    schema = json.loads(schema_path().read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors: list[str] = []
    for error in sorted(validator.iter_errors(report), key=lambda item: list(item.absolute_path)):
        location = _json_path(error.absolute_path)
        is_path_field = list(error.absolute_path)[-1:] == ["path"] or (
            len(error.absolute_path) >= 2
            and error.absolute_path[-2] in ("included_paths", "affected_paths")
        )
        if error.validator == "pattern" and is_path_field:
            errors.append(f"{location}: path must be repository-relative and use forward slashes")
        else:
            # jsonschema messages can echo arbitrary credentials, including unknown
            # property names. Only schema-owned constraints belong in diagnostics.
            errors.append(
                f"{location}: invalid value; schema constraint {error.validator} "
                f"requires {error.validator_value!r}"
            )
    return errors


def _all_evidence(report: Mapping[str, Any]) -> Iterable[tuple[str, Mapping[str, Any]]]:
    for section in ("stack", "categories", "findings", "strengths"):
        for index, item in enumerate(report.get(section, [])):
            for evidence_index, evidence in enumerate(item.get("evidence", [])):
                yield f"$.{section}[{index}].evidence[{evidence_index}]", evidence


def _walk_strings(value: Any, location: str = "$") -> Iterable[tuple[str, str]]:
    """Yield every string in the record with its JSON path."""

    if isinstance(value, str):
        yield location, value
    elif isinstance(value, Mapping):
        for key, item in value.items():
            yield from _walk_strings(item, f"{location}.{key}")
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            yield from _walk_strings(item, f"{location}[{index}]")


def _is_repository_relative(value: str) -> bool:
    if not value or "\\" in value or value.startswith("/") or re.match(r"^[A-Za-z]:", value):
        return False
    return ".." not in PurePosixPath(value).parts


def _duplicates(values: Iterable[str]) -> set[str]:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for value in values:
        if value in seen:
            duplicates.add(value)
        seen.add(value)
    return duplicates


def _semantic_errors(report: Mapping[str, Any], expected_locale: str | None) -> list[str]:
    errors: list[str] = []
    metadata = report.get("metadata", {})
    if expected_locale is not None and metadata.get("content_locale") != expected_locale:
        errors.append(
            "$.metadata.content_locale: does not match the requested locale"
        )

    categories = report.get("categories", [])
    category_ids = {item["id"] for item in categories}
    category_duplicates = _duplicates(item["id"] for item in categories)
    if category_duplicates:
        errors.append("$.categories: duplicate category id")

    findings = report.get("findings", [])
    finding_ids = {item["id"] for item in findings}
    finding_duplicates = _duplicates(item["id"] for item in findings)
    if finding_duplicates:
        errors.append("$.findings: duplicate finding id")
    for index, item in enumerate(findings):
        if item["category_id"] not in category_ids:
            errors.append(
                f"$.findings[{index}].category_id: references unknown category"
            )

    recommendation_ids = (item["id"] for item in report.get("recommendations", []))
    if _duplicates(recommendation_ids):
        errors.append("$.recommendations: duplicate recommendation id")
    for index, recommendation in enumerate(report.get("recommendations", [])):
        for finding_index, finding_id in enumerate(recommendation["finding_ids"]):
            if finding_id not in finding_ids:
                errors.append(
                    f"$.recommendations[{index}].finding_ids[{finding_index}]: "
                    "references unknown finding"
                )

    for location, item in _all_evidence(report):
        path = str(item["path"])
        if not _is_repository_relative(path):
            errors.append(f"{location}.path: path must be repository-relative")
        end_line = item.get("end_line")
        if end_line is not None and end_line < item["start_line"]:
            errors.append(f"{location}.end_line must be greater than or equal to start_line")
    for location, text in _walk_strings(report):
        if any(pattern.search(text) for pattern in _RAW_SECRET_PATTERNS):
            errors.append(f"{location}: redact raw secret material")

    for index, item in enumerate(report.get("coverage", [])):
        location = f"$.coverage[{index}]"
        discovered = item.get("discovered")
        reviewed = item["reviewed"]
        status = item["status"]
        if discovered is not None and reviewed > discovered:
            errors.append(f"{location}.reviewed cannot exceed discovered")
        if status == "exhaustive":
            if discovered is None:
                errors.append(f"{location}: exhaustive coverage requires a discovered count")
            elif reviewed < discovered:
                errors.append(f"{location}: exhaustive coverage requires reviewed == discovered")
        if status == "not-applicable" and reviewed:
            errors.append(f"{location}: not-applicable coverage requires reviewed == 0")
        if status == "not-applicable" and discovered != 0:
            errors.append(f"{location}: not-applicable coverage requires discovered == 0")
        if status == "sampled" and (discovered is None or reviewed == 0):
            errors.append(
                f"{location}: sampled coverage requires a known discovered count "
                "and reviewed > 0; use limited when the total or review is unavailable"
            )
    return errors


def validate_report(
    report: Mapping[str, Any], *, expected_locale: str | None = None
) -> None:
    errors = _schema_errors(report)
    if not errors:
        errors.extend(_semantic_errors(report, expected_locale))
    if errors:
        raise AuditValidationError(errors)
