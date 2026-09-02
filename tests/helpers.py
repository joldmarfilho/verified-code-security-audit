from __future__ import annotations

from typing import Any


def evidence(path: str, line: int, snippet: str) -> dict[str, Any]:
    return {
        "path": path,
        "start_line": line,
        "end_line": line,
        "snippet": snippet,
    }


def valid_report(locale: str = "en") -> dict[str, Any]:
    portuguese = locale == "pt-BR"
    finding_title = (
        "Consulta de reserva não filtra pela organização"
        if portuguese
        else "Booking lookup does not filter by organization"
    )
    return {
        "schema_version": "1.0.0",
        "metadata": {
            "project_name": "Acme Booking",
            "repository": "https://example.invalid/acme/booking",
            "revision": "0123456789abcdef0123456789abcdef01234567",
            "branch": "main",
            "audited_at": "2026-09-02T12:00:00Z",
            "worktree_dirty": False,
            "content_locale": locale,
        },
        "scope": {
            "summary": "Application source, deployment configuration, and repository history.",
            "included_paths": ["app/", ".github/workflows/"],
            "excluded_paths": [{"path": "vendor/", "reason": "Third-party generated code."}],
        },
        "stack": [
            {
                "kind": "framework",
                "name": "FastAPI",
                "version": "0.116",
                "evidence": [evidence("pyproject.toml", 12, '"fastapi>=0.116"')],
            }
        ],
        "coverage": [
            {
                "surface": "API routes",
                "status": "exhaustive",
                "discovered": 18,
                "reviewed": 18,
                "method": "Enumerated every FastAPI route registration.",
                "exclusions": [],
            }
        ],
        "categories": [
            {
                "id": "tenant-isolation",
                "name": "Tenant isolation",
                "status": "reviewed",
                "summary": "Organization filters were traced through all booking routes.",
                "evidence": [evidence("app/api/bookings.py", 1, "router = APIRouter()")],
            }
        ],
        "findings": [
            {
                "id": "F1",
                "category_id": "tenant-isolation",
                "severity": "high",
                "confidence": "high",
                "title": finding_title,
                "description": "A booking is fetched by public identifier without organization scope.",
                "preconditions": ["An authenticated user knows another booking identifier."],
                "exploit_path": "GET /bookings/{id} passes id to an unscoped repository lookup.",
                "impact": "A user can read booking details belonging to another organization.",
                "evidence": [
                    evidence(
                        "app/api/bookings.py",
                        42,
                        "return repository.get_by_id(booking_id)",
                    )
                ],
                "remediation": "Filter by both booking id and the authenticated organization id.",
                "acceptance_criteria": [
                    "A cross-organization booking id returns 404.",
                    "A same-organization booking remains accessible.",
                ],
                "actionable": True,
                "issue_group": "authorization",
                "references": ["CWE-639"],
            },
            {
                "id": "F2",
                "category_id": "tenant-isolation",
                "severity": "medium",
                "confidence": "high",
                "title": (
                    "Atualização de reserva aceita organização do payload"
                    if portuguese
                    else "Booking update trusts organization from the payload"
                ),
                "description": "The update flow trusts a caller-controlled organization identifier.",
                "preconditions": ["An authenticated user can submit a booking update."],
                "exploit_path": "PATCH /bookings/{id} forwards organization_id from the request body.",
                "impact": "A user can attempt to move a booking into another organization.",
                "evidence": [
                    evidence(
                        "app/api/bookings.py",
                        67,
                        "repository.update(booking_id, payload.model_dump())",
                    )
                ],
                "remediation": "Derive organization scope from the authenticated principal.",
                "acceptance_criteria": [
                    "Organization scope is never accepted from the request body.",
                    "A cross-organization booking id returns 404.",
                ],
                "actionable": True,
                "issue_group": "authorization",
                "references": ["CWE-639"],
            },
            {
                "id": "F3",
                "category_id": "tenant-isolation",
                "severity": "informational",
                "confidence": "high",
                "title": (
                    "Consultas administrativas têm escopo explícito"
                    if portuguese
                    else "Administrative queries use explicit scope"
                ),
                "description": "Administrative list queries explicitly apply organization scope.",
                "preconditions": ["An administrator lists bookings."],
                "exploit_path": "No exploit path was verified for this informational observation.",
                "impact": "This control reduces accidental cross-organization data access.",
                "evidence": [
                    evidence(
                        "app/api/admin.py",
                        24,
                        "repository.list_for_organization(principal.organization_id)",
                    )
                ],
                "remediation": "Keep this explicit scope when refactoring administrative queries.",
                "acceptance_criteria": [
                    "Administrative booking lists remain scoped by organization."
                ],
                "actionable": False,
                "references": [],
            },
        ],
        "strengths": [
            {
                "title": "JWT signature and expiry are verified",
                "description": "The authentication dependency rejects invalid or expired tokens.",
                "evidence": [evidence("app/auth.py", 31, "jwt.decode(token, public_key, algorithms=['RS256'])")],
            }
        ],
        "recommendations": [
            {
                "id": "R1",
                "priority": "P1",
                "title": "Scope booking queries by organization",
                "details": "Centralize organization scoping in the booking repository.",
                "finding_ids": ["F1", "F2"],
            }
        ],
        "limitations": [
            {
                "title": "Runtime testing not performed",
                "details": "The review was static and did not execute the application.",
                "affected_paths": ["app/"],
            }
        ],
    }
