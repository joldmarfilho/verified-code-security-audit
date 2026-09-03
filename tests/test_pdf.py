import tempfile
import unittest
from pathlib import Path

from pypdf import PdfReader

from tests.helpers import valid_report
from verified_code_security_audit.localization import load_locale
from verified_code_security_audit.pdf import (
    render_pdf,
    severity_chart,
    verify_pdf_structure,
)
from verified_code_security_audit.validation import load_report

ROOT = Path(__file__).resolve().parents[1]


class PdfTests(unittest.TestCase):
    def _extract(self, report: dict, locale: str = "en") -> str:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "report.pdf"
            render_pdf(report, load_locale(locale), path)
            return "\n".join(
                page.extract_text() or "" for page in PdfReader(path).pages
            )

    def test_renders_unicode_portuguese_title(self) -> None:
        report = valid_report("pt-BR")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "report.pdf"
            render_pdf(report, load_locale("pt-BR"), path)
            text = "\n".join(
                page.extract_text() or "" for page in PdfReader(path).pages
            )
            self.assertIn("Relatório de Auditoria de Segurança", text)

    def test_zero_findings_chart_is_nonempty_png(self) -> None:
        report = valid_report()
        report["findings"] = []
        image = severity_chart(report, load_locale("en"))
        self.assertTrue(image.getvalue().startswith(b"\x89PNG"))

    def test_structural_verifier_rejects_non_pdf(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.pdf"
            path.write_bytes(b"not a pdf")
            with self.assertRaisesRegex(ValueError, "invalid PDF"):
                verify_pdf_structure(path)

    def test_complete_report_contains_sections_and_records(self) -> None:
        strings = load_locale("en")
        text = self._extract(valid_report())

        for key, value in strings.items():
            if key.startswith("section."):
                self.assertIn(value, text)
        for value in ("F1", "F2", "F3", "R1", "FastAPI", "18 / 18"):
            self.assertIn(value, text)
        self.assertIn(strings["disclaimer"], text)

    def test_empty_report_keeps_every_section_and_empty_state(self) -> None:
        report = valid_report()
        report["findings"] = []
        report["strengths"] = []
        report["recommendations"] = []
        strings = load_locale("en")
        text = self._extract(report)

        self.assertIn(strings["chart.no_findings"], text)
        for key, value in strings.items():
            if key.startswith("section."):
                self.assertIn(value, text)

    def test_synthetic_report_avoids_orphan_heading_and_sparse_tail(self) -> None:
        for locale in ("en", "pt-BR"):
            with self.subTest(locale=locale):
                report = load_report(
                    ROOT
                    / "examples"
                    / "synthetic"
                    / f"audit-report.{locale}.json"
                )
                strings = load_locale(locale)
                with tempfile.TemporaryDirectory() as directory:
                    path = Path(directory) / "report.pdf"
                    render_pdf(report, strings, path)
                    pages = [
                        page.extract_text() or "" for page in PdfReader(path).pages
                    ]

                heading = strings["section.findings"]
                heading_page = next(
                    text for text in pages if heading in text.splitlines()
                )
                heading_lines = heading_page.splitlines()
                after_heading = "\n".join(
                    heading_lines[heading_lines.index(heading) + 1 :]
                )
                self.assertIn("F1", after_heading)
                self.assertIn(
                    strings["section.github_issues"], pages[-1].splitlines()
                )
                self.assertGreater(len(pages[-1]), 1200)


if __name__ == "__main__":
    unittest.main()
