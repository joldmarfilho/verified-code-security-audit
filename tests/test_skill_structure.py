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


if __name__ == "__main__":
    unittest.main()
