import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path

from tests.helpers import valid_report
from verified_code_security_audit.cli import main


class CliTests(unittest.TestCase):
    def _run(self, argv: list[str]) -> tuple[int, str, str]:
        stdout = StringIO()
        stderr = StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            code = main(argv)
        return code, stdout.getvalue(), stderr.getvalue()

    def _write_report(self, directory: Path, locale: str = "en") -> Path:
        path = directory / "audit.json"
        path.write_text(
            json.dumps(valid_report(locale), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return path

    def test_version_prints_prog_and_version(self) -> None:
        code, stdout, stderr = self._run(["--version"])
        self.assertEqual(code, 0)
        self.assertIn("vcsa 0.1.0", stdout)
        self.assertEqual(stderr, "")

    def test_validate_returns_zero_for_valid_report(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = self._write_report(Path(directory))
            code, stdout, stderr = self._run(["validate", str(path)])
        self.assertEqual(code, 0)
        self.assertIn(f"valid: {path}", stdout)
        self.assertEqual(stderr, "")

    def test_validate_with_matching_locale_succeeds(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = self._write_report(Path(directory), "pt-BR")
            code, stdout, stderr = self._run(["validate", str(path), "--locale", "pt-BR"])
        self.assertEqual(code, 0)
        self.assertIn(f"valid: {path}", stdout)
        self.assertEqual(stderr, "")

    def test_validate_with_mismatched_locale_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = self._write_report(Path(directory), "pt-BR")
            code, _, stderr = self._run(["validate", str(path), "--locale", "en"])
        self.assertEqual(code, 2)
        self.assertIn("content_locale", stderr)

    def test_validate_returns_two_for_invalid_json(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "audit.json"
            path.write_text("{", encoding="utf-8")
            code, _, stderr = self._run(["validate", str(path)])
        self.assertEqual(code, 2)
        self.assertIn("cannot read audit JSON", stderr)

    def test_render_writes_stable_localized_names(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = self._write_report(root, "pt-BR")
            output_dir = root / "output"
            code, stdout, stderr = self._run(
                [
                    "render",
                    str(path),
                    "--locale",
                    "pt-BR",
                    "--output",
                    str(output_dir),
                ]
            )
            self.assertEqual(code, 0)
            self.assertTrue(
                (output_dir / "security-audit-report.pt-BR.pdf").is_file()
            )
            self.assertTrue((output_dir / "github-issues.pt-BR.md").is_file())
            self.assertEqual(
                sorted(item.name for item in output_dir.iterdir()),
                ["github-issues.pt-BR.md", "security-audit-report.pt-BR.pdf"],
            )
        self.assertIn("rendered:", stdout)
        self.assertEqual(stderr, "")

    def test_render_rejects_locale_mismatch_without_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = self._write_report(root, "en")
            output_dir = root / "output"
            output_dir.mkdir()
            code, _, stderr = self._run(
                [
                    "render",
                    str(path),
                    "--locale",
                    "pt-BR",
                    "--output",
                    str(output_dir),
                ]
            )
            self.assertEqual(code, 2)
            self.assertEqual(list(output_dir.iterdir()), [])
        self.assertIn("content_locale", stderr)


if __name__ == "__main__":
    unittest.main()
