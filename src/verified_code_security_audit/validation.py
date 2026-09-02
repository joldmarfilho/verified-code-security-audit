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
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bsk-[A-Za-z0-9]{20,}\b"),
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
        if error.validator == "pattern" and list(error.absolute_path)[-1:] == ["path"]:
            errors.append(f"{location}: path must be repository-relative and use forward slashes")
        else:
            errors.append(f"{location}: {error.message}")
    return errors


def _all_evidence(report: Mapping[str, Any]) -> Iterable[tuple[str, Mapping[str, Any]]]:
    for section in ("stack", "categories", "findings", "strengths"):
        for index, item in enumerate(report.get(section, [])):
            for evidence_index, evidence in enumerate(item.get("evidence", [])):
                yield f"$.{section}[{index}].evidence[{evidence_index}]", evidence


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
            "$.metadata.content_locale: "
            f"expected {expected_locale!r}, got {metadata.get('content_locale')!r}"
        )

    categories = report.get("categories", [])
    category_ids = {item["id"] for item in categories}
    category_duplicates = _duplicates(item["id"] for item in categories)
    for value in sorted(category_duplicates):
        errors.append(f"duplicate category id: {value}")

    findings = report.get("findings", [])
    finding_ids = {item["id"] for item in findings}
    finding_duplicates = _duplicates(item["id"] for item in findings)
    for value in sorted(finding_duplicates):
        errors.append(f"duplicate finding id: {value}")
    for item in findings:
        if item["category_id"] not in category_ids:
            errors.append(
                f"finding {item['id']} references unknown category {item['category_id']}"
            )

    recommendation_ids = (item["id"] for item in report.get("recommendations", []))
    for value in sorted(_duplicates(recommendation_ids)):
        errors.append(f"duplicate recommendation id: {value}")
    for recommendation in report.get("recommendations", []):
        for finding_id in recommendation["finding_ids"]:
            if finding_id not in finding_ids:
                errors.append(
                    f"recommendation {recommendation['id']} references unknown finding {finding_id}"
                )

    for location, item in _all_evidence(report):
        path = str(item["path"])
        if not _is_repository_relative(path):
            errors.append(f"{location}.path: path must be repository-relative")
        end_line = item.get("end_line")
        if end_line is not None and end_line < item["start_line"]:
            errors.append(f"{location}.end_line must be greater than or equal to start_line")
        snippet = str(item["snippet"])
        if any(pattern.search(snippet) for pattern in _RAW_SECRET_PATTERNS):
            errors.append(f"{location}.snippet: redact raw secret material")

    for index, item in enumerate(report.get("coverage", [])):
        discovered = item.get("discovered")
        if discovered is not None and item["reviewed"] > discovered:
            errors.append(f"$.coverage[{index}].reviewed cannot exceed discovered")
    return errors


def validate_report(
    report: Mapping[str, Any], *, expected_locale: str | None = None
) -> None:
    errors = _schema_errors(report)
    if not errors:
        errors.extend(_semantic_errors(report, expected_locale))
    if errors:
        raise AuditValidationError(errors)
