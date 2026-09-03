from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from tests.helpers import valid_report
from verified_code_security_audit.validation import (
    AuditValidationError,
    load_report,
    schema_path,
    validate_report,
)


class ValidationTests(unittest.TestCase):
    def test_accepts_valid_report(self) -> None:
        validate_report(valid_report())

    def test_schema_is_available(self) -> None:
        self.assertTrue(schema_path().is_file())

    def test_loads_utf8_json_object(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "audit.json"
            path.write_text(json.dumps(valid_report("pt-BR"), ensure_ascii=False), encoding="utf-8")
            self.assertEqual(load_report(path)["metadata"]["content_locale"], "pt-BR")

    def test_rejects_parent_path_evidence(self) -> None:
        report = valid_report()
        report["findings"][0]["evidence"][0]["path"] = "../outside.env"
        with self.assertRaisesRegex(AuditValidationError, "repository-relative"):
            validate_report(report)

    def test_rejects_windows_absolute_path(self) -> None:
        report = valid_report()
        report["findings"][0]["evidence"][0]["path"] = "C:/outside.env"
        with self.assertRaisesRegex(AuditValidationError, "repository-relative"):
            validate_report(report)

    def test_rejects_reversed_line_range(self) -> None:
        report = valid_report()
        item = report["findings"][0]["evidence"][0]
        item["start_line"] = 20
        item["end_line"] = 10
        with self.assertRaisesRegex(AuditValidationError, "end_line"):
            validate_report(report)

    def test_rejects_duplicate_finding_ids(self) -> None:
        report = valid_report()
        report["findings"].append(copy.deepcopy(report["findings"][0]))
        with self.assertRaisesRegex(AuditValidationError, "duplicate finding id"):
            validate_report(report)

    def test_rejects_unknown_recommendation_finding(self) -> None:
        report = valid_report()
        report["recommendations"][0]["finding_ids"] = ["F404"]
        with self.assertRaisesRegex(AuditValidationError, "unknown finding"):
            validate_report(report)

    def test_rejects_unknown_category_reference(self) -> None:
        report = valid_report()
        report["findings"][0]["category_id"] = "missing-category"
        with self.assertRaisesRegex(AuditValidationError, "unknown category"):
            validate_report(report)

    def test_rejects_locale_mismatch(self) -> None:
        with self.assertRaisesRegex(AuditValidationError, "content_locale"):
            validate_report(valid_report("en"), expected_locale="pt-BR")

    def test_rejects_raw_secret_shapes(self) -> None:
        report = valid_report()
        report["findings"][0]["evidence"][0]["snippet"] = (
            "token = 'ghp_abcdefghijklmnopqrstuvwxyz123456'"
        )
        with self.assertRaisesRegex(AuditValidationError, "redact"):
            validate_report(report)

    def test_rejects_raw_secret_outside_evidence_snippets(self) -> None:
        for section, mutate in (
            ("description", lambda report: report["findings"][0].__setitem__(
                "description", "The key AKIAIOSFODNN7EXAMPLE is committed."
            )),
            ("remediation", lambda report: report["findings"][0].__setitem__(
                "remediation", "Rotate ghp_abcdefghijklmnopqrstuvwxyz123456 immediately."
            )),
            ("limitation", lambda report: report["limitations"][0].__setitem__(
                "details", "-----BEGIN RSA PRIVATE KEY-----"
            )),
        ):
            with self.subTest(section=section):
                report = valid_report()
                mutate(report)
                with self.assertRaisesRegex(AuditValidationError, "redact"):
                    validate_report(report)

    def test_rejects_incoherent_coverage_status(self) -> None:
        cases = {
            "exhaustive coverage requires reviewed": {"reviewed": 3},
            "exhaustive coverage requires a discovered": {"discovered": None},
            "not-applicable coverage requires": {"status": "not-applicable"},
        }
        for message, changes in cases.items():
            with self.subTest(changes=changes):
                report = valid_report()
                report["coverage"][0].update(changes)
                with self.assertRaisesRegex(AuditValidationError, message):
                    validate_report(report)

    def test_accepts_sampled_coverage_below_discovered(self) -> None:
        report = valid_report()
        report["coverage"][0].update(status="sampled", reviewed=3)
        validate_report(report)

    def test_rejects_non_object_json(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "audit.json"
            path.write_text("[]", encoding="utf-8")
            with self.assertRaisesRegex(AuditValidationError, "root must be an object"):
                load_report(path)


if __name__ == "__main__":
    unittest.main()
