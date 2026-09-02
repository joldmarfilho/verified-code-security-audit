import unittest

from tests.helpers import valid_report
from verified_code_security_audit.localization import load_locale
from verified_code_security_audit.markdown import (
    group_actionable_findings,
    render_issues,
)


class MarkdownTests(unittest.TestCase):
    def test_groups_related_actionable_findings(self) -> None:
        groups = group_actionable_findings(valid_report())
        self.assertEqual(
            [[item["id"] for item in group] for group in groups],
            [["F1", "F2"]],
        )

    def test_excludes_non_actionable_informational_finding(self) -> None:
        text = render_issues(valid_report(), load_locale("en"))
        self.assertNotIn("F3", text)

    def test_renders_one_complete_issue_block(self) -> None:
        text = render_issues(valid_report(), load_locale("en"))
        self.assertEqual(text.count("--- ISSUE 1 ---"), 1)
        for heading in (
            "Labels",
            "Problem",
            "Exploitability",
            "Evidence",
            "Impact",
            "Remediation",
            "Acceptance criteria",
        ):
            self.assertIn(f"## {heading}", text)

    def test_preserves_code_fences_without_interpreting_html(self) -> None:
        report = valid_report()
        report["findings"][0]["evidence"][0]["snippet"] = (
            "<script>alert('x')</script>"
        )
        text = render_issues(report, load_locale("en"))
        self.assertIn("```text\n<script>alert('x')</script>\n```", text)

    def test_uses_a_longer_fence_when_snippet_contains_backticks(self) -> None:
        report = valid_report()
        report["findings"][0]["evidence"][0]["snippet"] = (
            "```\nsynthetic\n```"
        )
        text = render_issues(report, load_locale("en"))
        self.assertIn("````text\n```\nsynthetic\n```\n````", text)


if __name__ == "__main__":
    unittest.main()
