import unittest

from verified_code_security_audit.localization import (
    SUPPORTED_LOCALES,
    assert_locale_parity,
    load_locale,
)


class LocalizationTests(unittest.TestCase):
    def test_supported_locales_are_stable(self) -> None:
        self.assertEqual(SUPPORTED_LOCALES, ("en", "pt-BR"))

    def test_locales_have_identical_keys(self) -> None:
        assert_locale_parity()

    def test_portuguese_title_is_unicode(self) -> None:
        self.assertEqual(
            load_locale("pt-BR")["report.title"],
            "Relatório de Auditoria de Segurança",
        )

    def test_unknown_locale_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "unsupported locale"):
            load_locale("es")


if __name__ == "__main__":
    unittest.main()
