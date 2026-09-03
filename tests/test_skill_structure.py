import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class SkillStructureTests(unittest.TestCase):
    def test_skill_frontmatter_and_size(self) -> None:
        text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        frontmatter = text.split("---", 2)[1]
        body = text.split("---", 2)[2]
        self.assertIn("name: verified-code-security-audit", frontmatter)
        description = re.search(r"^description:\s*(.+)$", frontmatter, re.MULTILINE)
        self.assertIsNotNone(description)
        value = description.group(1)
        self.assertTrue(value.startswith("Use when"))
        self.assertIn("repository", value.lower())
        self.assertIn("security audit", value.lower())
        self.assertNotRegex(value.lower(), r"\b(you|your)\b")
        self.assertLess(len(re.findall(r"\b\w+[\w'-]*\b", body)), 500)

    def test_skill_links_contract_and_safety_boundary(self) -> None:
        text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        for path in ("references/methodology.md", "references/data-contract.md"):
            self.assertIn(f"]({path})", text)
        for phrase in (
            "audit-report.<locale>.json",
            "python -m pip install",
            "vcsa validate",
            "vcsa render",
            "untrusted",
            "explicit authorization",
        ):
            self.assertIn(phrase, text)

    def test_every_linked_local_path_exists_and_uses_slashes(self) -> None:
        text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        for target in re.findall(r"\]\(([^)]+)\)", text):
            if "://" in target or target.startswith("#"):
                continue
            self.assertNotIn("\\", target)
            self.assertTrue((ROOT / target).is_file(), target)

    def test_openai_metadata_has_skill_prompt(self) -> None:
        text = (ROOT / "agents" / "openai.yaml").read_text(encoding="utf-8")
        self.assertRegex(text, r'default_prompt:\s*"[^"]+"')
        self.assertIn("$verified-code-security-audit", text)

    def test_standalone_prompts_preserve_the_output_contract(self) -> None:
        required = (
            "snapshot",
            "stack",
            "coverage",
            "findings",
            "strengths",
            "not-applicable",
            "[redacted]",
            "json",
            "vcsa validate",
            "pdf",
            "markdown",
        )
        for filename in ("audit.en.md", "audit.pt-BR.md"):
            text = (ROOT / "prompts" / filename).read_text(encoding="utf-8").lower()
            for phrase in required:
                self.assertIn(phrase, text, f"{filename}: {phrase}")

    def test_readmes_document_the_complete_public_workflow(self) -> None:
        cases = {
            "README.md": {
                "language": "virtual environment",
                "limitations": "limitations",
                "counterpart": "](README.pt-BR.md)",
                "image": "docs/images/report-en.png",
            },
            "README.pt-BR.md": {
                "language": "ambiente virtual",
                "limitations": "limitações",
                "counterpart": "](README.md)",
                "image": "docs/images/report-pt-BR.png",
            },
        }
        common = (
            "$verified-code-security-audit",
            "~/.agents/skills",
            "~/.claude/skills",
            "vcsa validate",
            "vcsa render",
            "pt-BR",
            "security-audit-report.",
            "github-issues.",
            "MIT",
        )
        branding = (
            "actions/workflows/tests.yml/badge.svg",
            "img.shields.io/badge/Python-3.10%2B",
            "img.shields.io/badge/JSON_Schema-Draft_2020--12",
            "img.shields.io/badge/ReportLab-PDF",
            "img.shields.io/badge/Matplotlib-Charts",
            "img.shields.io/badge/GitHub_Actions-CI",
            "img.shields.io/badge/Markdown-Reports",
            "img.shields.io/badge/Agent_Skill-Codex",
            "img.shields.io/badge/Locales-EN_%7C_PT--BR",
            "cdn.buymeacoffee.com/buttons/v2/default-yellow.png",
            "buymeacoffee.com/joldmarxxtz",
        )
        for filename, expected in cases.items():
            text = (ROOT / filename).read_text(encoding="utf-8")
            for phrase in common:
                self.assertIn(phrase, text, f"{filename}: {phrase}")
            for marker in branding:
                self.assertIn(marker, text, f"{filename}: {marker}")
            self.assertIn(expected["language"], text.lower())
            self.assertIn(expected["limitations"], text.lower())
            self.assertIn(expected["counterpart"], text)
            self.assertNotRegex(text, r"[A-Za-z]:[/\\]Users")
            self.assertIn(f"]({expected['image']})", text)
            self.assertTrue((ROOT / expected["image"]).is_file())
            self.assertRegex(
                text,
                r"\]\(examples/synthetic/audit-report\.(?:en|pt-BR)\.json\)",
            )

    def test_public_markdown_has_no_workstation_paths(self) -> None:
        for path in ROOT.rglob("*.md"):
            text = path.read_text(encoding="utf-8")
            self.assertNotRegex(
                text,
                r"[A-Za-z]:[/\\]Users",
                str(path.relative_to(ROOT)),
            )


if __name__ == "__main__":
    unittest.main()
