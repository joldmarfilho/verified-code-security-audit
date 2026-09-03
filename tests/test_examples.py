import unittest
from pathlib import Path

from verified_code_security_audit.validation import load_report, validate_report

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples" / "synthetic"


def _evidence_coordinates(report: dict) -> list[tuple[str, int, int | None]]:
    return [
        (
            item["path"],
            item["start_line"],
            item.get("end_line"),
        )
        for finding in report["findings"]
        for item in finding["evidence"]
    ]


class ExampleTests(unittest.TestCase):
    def test_bilingual_examples_are_valid_and_fact_equivalent(self) -> None:
        english = load_report(EXAMPLES / "audit-report.en.json")
        portuguese = load_report(EXAMPLES / "audit-report.pt-BR.json")
        validate_report(english, expected_locale="en")
        validate_report(portuguese, expected_locale="pt-BR")

        self.assertEqual(
            [item["id"] for item in english["findings"]],
            [item["id"] for item in portuguese["findings"]],
        )
        self.assertEqual(
            [(item["id"], item["status"]) for item in english["categories"]],
            [(item["id"], item["status"]) for item in portuguese["categories"]],
        )
        self.assertEqual(
            [item["severity"] for item in english["findings"]],
            [item["severity"] for item in portuguese["findings"]],
        )
        self.assertEqual(
            _evidence_coordinates(english),
            _evidence_coordinates(portuguese),
        )
        self.assertEqual(
            [item.get("issue_group") for item in english["findings"]],
            [item.get("issue_group") for item in portuguese["findings"]],
        )
        self.assertEqual(
            [item["finding_ids"] for item in english["recommendations"]],
            [item["finding_ids"] for item in portuguese["recommendations"]],
        )
        self.assertEqual(
            [
                (item["surface"], item["discovered"], item["reviewed"])
                for item in english["coverage"]
            ],
            [
                (item["surface"], item["discovered"], item["reviewed"])
                for item in portuguese["coverage"]
            ],
        )
        self.assertNotEqual(
            [item["title"] for item in english["findings"]],
            [item["title"] for item in portuguese["findings"]],
        )


if __name__ == "__main__":
    unittest.main()
