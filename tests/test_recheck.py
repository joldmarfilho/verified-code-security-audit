import json
import shutil
import subprocess
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path

from tests.helpers import evidence, valid_report
from verified_code_security_audit.cli import main
from verified_code_security_audit.recheck import (
    INTACT,
    MOVED,
    STALE,
    UNVERIFIABLE,
    GitUnavailableError,
    recheck_evidence,
    recheck_report,
    resolve_revision,
)

SOURCE = """import os


def get_booking(booking_id):
    return repository.get_by_id(booking_id)
"""


def _git(repository: Path, *arguments: str) -> None:
    subprocess.run(
        [
            "git",
            "-C",
            str(repository),
            "-c",
            "user.name=vcsa",
            "-c",
            "user.email=vcsa@example.invalid",
            *arguments,
        ],
        check=True,
        capture_output=True,
    )


@unittest.skipIf(shutil.which("git") is None, "git is not available")
class RepositoryFixture(unittest.TestCase):
    """Temporary git repository holding the audited fixture file."""

    def setUp(self) -> None:
        self._directory = tempfile.TemporaryDirectory()
        self.addCleanup(self._directory.cleanup)
        self.repository = Path(self._directory.name)
        _git(self.repository, "init", "-q")
        self._write("app.py", SOURCE)
        _git(self.repository, "add", "-A")
        _git(self.repository, "commit", "-qm", "initial")

    def _write(self, name: str, text: str) -> None:
        target = self.repository / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8", newline="\n")

    def _commit(self, message: str = "change") -> None:
        _git(self.repository, "add", "-A")
        _git(self.repository, "commit", "-qm", message)

    def _status(self, path: str, line: int, snippet: str):
        return recheck_evidence(
            "finding:F1",
            evidence(path, line, snippet),
            self.repository,
            "HEAD",
        )


class RecheckTests(RepositoryFixture):
    def test_unchanged_snippet_is_intact(self) -> None:
        status = self._status("app.py", 5, "    return repository.get_by_id(booking_id)")
        self.assertEqual(status.status, INTACT)
        self.assertEqual(status.current_line, 5)

    def test_reindented_snippet_still_matches(self) -> None:
        status = self._status("app.py", 5, "return repository.get_by_id(booking_id)")
        self.assertEqual(status.status, INTACT)

    def test_shifted_snippet_is_moved(self) -> None:
        self._write("app.py", "# audited\n" + SOURCE)
        self._commit()
        status = self._status("app.py", 5, "return repository.get_by_id(booking_id)")
        self.assertEqual(status.status, MOVED)
        self.assertEqual(status.current_line, 6)

    def test_multiline_snippet_matches_across_blank_lines(self) -> None:
        status = self._status(
            "app.py",
            4,
            "def get_booking(booking_id):\n\n    return repository.get_by_id(booking_id)",
        )
        self.assertEqual(status.status, INTACT)
        self.assertEqual(status.current_line, 4)

    def test_removed_snippet_is_stale(self) -> None:
        self._write("app.py", "import os\n")
        self._commit()
        status = self._status("app.py", 5, "return repository.get_by_id(booking_id)")
        self.assertEqual(status.status, STALE)
        self.assertIsNone(status.current_line)

    def test_deleted_file_is_stale(self) -> None:
        (self.repository / "app.py").unlink()
        self._commit()
        status = self._status("app.py", 5, "return repository.get_by_id(booking_id)")
        self.assertEqual(status.status, STALE)

    def test_redacted_snippet_is_unverifiable(self) -> None:
        status = self._status("app.py", 5, "SECRET = [REDACTED]")
        self.assertEqual(status.status, UNVERIFIABLE)

    def test_earlier_revision_still_resolves(self) -> None:
        first = resolve_revision(self.repository, "HEAD")
        self._write("app.py", "import os\n")
        self._commit()
        status = recheck_evidence(
            "finding:F1",
            evidence("app.py", 5, "return repository.get_by_id(booking_id)"),
            self.repository,
            first,
        )
        self.assertEqual(status.status, INTACT)

    def test_unknown_revision_raises(self) -> None:
        with self.assertRaises(GitUnavailableError):
            resolve_revision(self.repository, "does-not-exist")

    def test_report_walk_covers_every_section(self) -> None:
        report = _pinned_report()
        statuses = recheck_report(report, self.repository)
        self.assertTrue(statuses)
        owners = {status.owner.split(":", 1)[0] for status in statuses}
        self.assertEqual(owners, {"finding", "strength", "category", "stack"})
        self.assertTrue(all(status.status == INTACT for status in statuses))


class RecheckCliTests(RepositoryFixture):
    def _run(self, argv: list[str]) -> tuple[int, str, str]:
        stdout = StringIO()
        stderr = StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            code = main(argv)
        return code, stdout.getvalue(), stderr.getvalue()

    def _report_path(self) -> Path:
        path = self.repository / "audit.json"
        path.write_text(
            json.dumps(_pinned_report(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return path

    def test_cli_returns_zero_when_evidence_holds(self) -> None:
        code, stdout, stderr = self._run(
            ["recheck", str(self._report_path()), "--repo", str(self.repository)]
        )
        self.assertEqual(code, 0, stderr)
        self.assertIn("0 stale", stdout)
        self.assertIn("recorded revision:", stdout)

    def test_cli_returns_one_when_evidence_is_stale(self) -> None:
        path = self._report_path()
        self._write("app.py", "import os\n")
        self._commit()
        code, stdout, stderr = self._run(
            ["recheck", str(path), "--repo", str(self.repository)]
        )
        self.assertEqual(code, 1, stderr)
        self.assertIn(STALE, stdout)

    def test_cli_reports_unknown_revision(self) -> None:
        code, _, stderr = self._run(
            [
                "recheck",
                str(self._report_path()),
                "--repo",
                str(self.repository),
                "--rev",
                "does-not-exist",
            ]
        )
        self.assertEqual(code, 2)
        self.assertIn("error:", stderr)


def _pinned_report() -> dict:
    """A schema-valid report whose evidence all points at the fixture file."""

    report = valid_report()
    anchor = evidence("app.py", 5, "return repository.get_by_id(booking_id)")
    for key in ("findings", "strengths", "stack", "categories"):
        for item in report[key]:
            if "evidence" in item:
                item["evidence"] = [dict(anchor)]
    return report


if __name__ == "__main__":
    unittest.main()
