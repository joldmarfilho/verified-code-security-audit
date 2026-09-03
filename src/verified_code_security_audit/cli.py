"""Command-line interface for validation and deterministic report rendering."""

from __future__ import annotations

import argparse
import os
import sys
import tempfile
from collections.abc import Mapping, Sequence
from pathlib import Path

from verified_code_security_audit.localization import SUPPORTED_LOCALES, load_locale
from verified_code_security_audit.markdown import render_issues
from verified_code_security_audit.pdf import render_pdf
from verified_code_security_audit.validation import (
    AuditValidationError,
    load_report,
    validate_report,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="vcsa",
        description="Validate and render evidence-backed security audit reports.",
    )
    subcommands = parser.add_subparsers(dest="command", required=True)

    validate = subcommands.add_parser("validate", help="validate an audit JSON file")
    validate.add_argument("input", type=Path, metavar="INPUT")

    render = subcommands.add_parser("render", help="render PDF and Markdown outputs")
    render.add_argument("input", type=Path, metavar="INPUT")
    render.add_argument("--locale", choices=SUPPORTED_LOCALES)
    render.add_argument("--output", required=True, type=Path, metavar="DIRECTORY")
    return parser


def _temporary_path(directory: Path, suffix: str) -> Path:
    handle = tempfile.NamedTemporaryFile(
        mode="wb",
        prefix=".vcsa-",
        suffix=suffix,
        dir=directory,
        delete=False,
    )
    try:
        return Path(handle.name)
    finally:
        handle.close()


def _render_outputs(
    report: Mapping[str, object],
    locale: str,
    output_directory: Path,
) -> tuple[Path, Path]:
    strings = load_locale(locale)
    output_directory.mkdir(parents=True, exist_ok=True)
    pdf_target = output_directory / f"security-audit-report.{locale}.pdf"
    markdown_target = output_directory / f"github-issues.{locale}.md"
    temporary_paths: list[Path] = []

    try:
        pdf_temporary = _temporary_path(output_directory, ".pdf")
        markdown_temporary = _temporary_path(output_directory, ".md")
        temporary_paths.extend([pdf_temporary, markdown_temporary])

        render_pdf(report, strings, pdf_temporary)

        markdown = render_issues(report, strings)
        if not markdown or not markdown.endswith("\n"):
            raise ValueError("invalid Markdown output")
        markdown_temporary.write_text(markdown, encoding="utf-8", newline="\n")
        if markdown_temporary.stat().st_size == 0:
            raise ValueError("invalid Markdown output")

        os.replace(pdf_temporary, pdf_target)
        os.replace(markdown_temporary, markdown_target)
        return pdf_target, markdown_target
    finally:
        for path in temporary_paths:
            try:
                path.unlink(missing_ok=True)
            except OSError:
                pass


def _declared_locale(report: Mapping[str, object]) -> str:
    metadata = report["metadata"]
    if not isinstance(metadata, Mapping):
        raise AuditValidationError(["metadata must be an object"])
    return str(metadata["content_locale"])


def main(argv: Sequence[str] | None = None) -> int:
    """Run the CLI and return a process-compatible exit code."""

    try:
        arguments = _parser().parse_args(argv)
    except SystemExit as exc:
        return int(exc.code or 0)

    try:
        report = load_report(arguments.input)
        validate_report(report)
        if arguments.command == "validate":
            print(f"valid: {arguments.input}")
            return 0

        locale = arguments.locale or _declared_locale(report)
        load_locale(locale)
        validate_report(report, expected_locale=locale)
    except (AuditValidationError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    try:
        output_directory = arguments.output.resolve()
        pdf_path, markdown_path = _render_outputs(
            report,
            locale,
            output_directory,
        )
    except Exception as exc:  # The CLI must contain renderer failures.
        print(
            f"render failed ({type(exc).__name__}: {exc}); "
            "no temporary files were retained",
            file=sys.stderr,
        )
        return 1

    print(f"rendered: {pdf_path}")
    print(f"rendered: {markdown_path}")
    return 0


def entrypoint() -> None:
    raise SystemExit(main())
