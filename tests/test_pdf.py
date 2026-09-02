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


class PdfTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
