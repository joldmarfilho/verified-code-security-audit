"""Load and compare the report's bundled locale dictionaries."""

from __future__ import annotations

import json
from importlib import resources

SUPPORTED_LOCALES = ("en", "pt-BR")


def load_locale(locale: str) -> dict[str, str]:
    """Return a validated copy of the requested locale dictionary."""

    if locale not in SUPPORTED_LOCALES:
        raise ValueError(f"unsupported locale: {locale}")

    resource = resources.files("verified_code_security_audit").joinpath(
        "locales", f"{locale}.json"
    )
    value = json.loads(resource.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or not all(
        isinstance(key, str) and isinstance(text, str) and text
        for key, text in value.items()
    ):
        raise ValueError(f"invalid locale file: {locale}")
    return value


def assert_locale_parity() -> None:
    """Raise when a translated dictionary gains or loses a message key."""

    baseline = set(load_locale(SUPPORTED_LOCALES[0]))
    for locale in SUPPORTED_LOCALES[1:]:
        current = set(load_locale(locale))
        if current != baseline:
            missing = sorted(baseline - current)
            extra = sorted(current - baseline)
            raise ValueError(
                f"locale {locale} differs: missing={missing}, extra={extra}"
            )
