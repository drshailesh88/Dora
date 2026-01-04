"""
Translation service for Dora medical knowledge platform.

Provides comprehensive internationalization support with:
- Fallback to English for missing translations
- Parameter interpolation
- Pluralization rules
- Locale-specific number/date formatting
- Medical abbreviation handling
"""

import json
import re
from pathlib import Path
from typing import Dict, Any, Optional, Union
from datetime import datetime
from decimal import Decimal


class Translator:
    """Main translation service for Dora platform."""

    DEFAULT_LOCALE = "en"
    SUPPORTED_LOCALES = ["en", "hi", "mr", "ta", "te", "kn", "bn"]

    def __init__(self, locale: str = DEFAULT_LOCALE):
        """
        Initialize translator with specified locale.

        Args:
            locale: Language code (en, hi, mr, ta, te, bn)
        """
        self.locale = locale if locale in self.SUPPORTED_LOCALES else self.DEFAULT_LOCALE
        self.translations: Dict[str, Dict[str, Any]] = {}
        self.locales_dir = Path(__file__).parent / "locales"
        self._load_translations()

    def _load_translations(self):
        """Load all translation files into memory."""
        for locale in self.SUPPORTED_LOCALES:
            locale_file = self.locales_dir / f"{locale}.json"
            if locale_file.exists():
                with open(locale_file, "r", encoding="utf-8") as f:
                    self.translations[locale] = json.load(f)
            else:
                self.translations[locale] = {}

    def set_locale(self, locale: str):
        """
        Change the current locale.

        Args:
            locale: New language code
        """
        if locale in self.SUPPORTED_LOCALES:
            self.locale = locale

    def get_locale(self) -> str:
        """Get current locale."""
        return self.locale

    def translate(
        self,
        key: str,
        params: Optional[Dict[str, Any]] = None,
        locale: Optional[str] = None,
        fallback: Optional[str] = None
    ) -> str:
        """
        Translate a key to the current or specified locale.

        Args:
            key: Translation key (e.g., "nav.home", "medical.diabetes")
            params: Parameters for interpolation (e.g., {"name": "John", "count": 5})
            locale: Override locale for this translation
            fallback: Fallback text if translation not found

        Returns:
            Translated string with interpolated parameters

        Examples:
            >>> t = Translator("hi")
            >>> t.translate("nav.home")
            "होम"
            >>> t.translate("messages.welcome", {"name": "डॉ. शर्मा"})
            "स्वागत है, डॉ. शर्मा"
        """
        target_locale = locale or self.locale

        # Get translation from target locale
        translation = self._get_nested_value(
            self.translations.get(target_locale, {}),
            key
        )

        # Fallback to English if not found
        if translation is None and target_locale != self.DEFAULT_LOCALE:
            translation = self._get_nested_value(
                self.translations.get(self.DEFAULT_LOCALE, {}),
                key
            )

        # Use fallback or key itself if still not found
        if translation is None:
            translation = fallback or key

        # Interpolate parameters
        if params and isinstance(translation, str):
            translation = self._interpolate(translation, params)

        return translation

    def t(self, key: str, **kwargs) -> str:
        """
        Shorthand for translate().

        Args:
            key: Translation key
            **kwargs: Parameters for interpolation

        Returns:
            Translated string
        """
        return self.translate(key, params=kwargs)

    def _get_nested_value(self, data: Dict, key: str) -> Any:
        """
        Get value from nested dictionary using dot notation.

        Args:
            data: Dictionary to search
            key: Dot-separated key (e.g., "nav.home")

        Returns:
            Value if found, None otherwise
        """
        keys = key.split(".")
        value = data

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return None
            else:
                return None

        return value

    def _interpolate(self, text: str, params: Dict[str, Any]) -> str:
        """
        Interpolate parameters into translation string.

        Supports:
        - Simple: "{name}" -> "John"
        - Nested: "{user.name}" -> "John"
        - Pluralization: "{count:plural(item,items)}" -> "items" if count != 1

        Args:
            text: Text with placeholders
            params: Parameters to interpolate

        Returns:
            Interpolated text
        """
        def replace_placeholder(match):
            placeholder = match.group(1)

            # Handle pluralization: {count:plural(singular,plural)}
            if ":plural(" in placeholder:
                var_name, plural_args = placeholder.split(":plural(")
                plural_args = plural_args.rstrip(")")
                singular, plural = plural_args.split(",")

                count = params.get(var_name, 0)
                if isinstance(count, (int, float, Decimal)):
                    return plural if count != 1 else singular
                return singular

            # Handle nested keys
            value = self._get_nested_value(params, placeholder)

            if value is not None:
                return str(value)

            return match.group(0)  # Return original if not found

        # Replace {key} placeholders
        return re.sub(r"\{([^}]+)\}", replace_placeholder, text)

    def format_number(self, number: Union[int, float, Decimal], decimals: int = 2) -> str:
        """
        Format number according to locale conventions.

        Args:
            number: Number to format
            decimals: Number of decimal places

        Returns:
            Formatted number string
        """
        if self.locale == "hi":
            # Indian numbering system (lakhs, crores)
            # For simplicity, using comma separation
            formatted = f"{number:,.{decimals}f}"
            return formatted
        else:
            # Western numbering system
            return f"{number:,.{decimals}f}"

    def format_date(self, date: datetime, format: str = "medium") -> str:
        """
        Format date according to locale conventions.

        Args:
            date: Date to format
            format: Format type ("short", "medium", "long", "full")

        Returns:
            Formatted date string
        """
        if self.locale == "hi":
            formats = {
                "short": "%d/%m/%Y",
                "medium": "%d %b %Y",
                "long": "%d %B %Y",
                "full": "%A, %d %B %Y"
            }
        else:
            formats = {
                "short": "%m/%d/%Y",
                "medium": "%b %d, %Y",
                "long": "%B %d, %Y",
                "full": "%A, %B %d, %Y"
            }

        fmt = formats.get(format, formats["medium"])
        return date.strftime(fmt)

    def translate_medical_term(
        self,
        term: str,
        locale: Optional[str] = None,
        preserve_abbreviations: bool = True
    ) -> str:
        """
        Translate medical term with special handling.

        Args:
            term: Medical term or abbreviation
            locale: Target locale (defaults to current)
            preserve_abbreviations: Keep common medical abbreviations untranslated

        Returns:
            Translated medical term
        """
        target_locale = locale or self.locale

        # Common medical abbreviations that should not be translated
        medical_abbrevs = {
            "BP", "HR", "RR", "SpO2", "CBC", "ECG", "MRI", "CT", "HIV", "AIDS",
            "COVID", "COPD", "GERD", "UTI", "CHF", "MI", "DVT", "PE", "DM",
            "HTN", "CAD", "CKD", "ESRD", "ICU", "ER", "OPD", "IPD", "IV", "IM",
            "SC", "PO", "PR", "mg", "ml", "L", "kg", "cm", "mmHg", "BPM"
        }

        if preserve_abbreviations and term.upper() in medical_abbrevs:
            return term

        # Try to translate from medical terms section
        translation = self.translate(
            f"medical.terms.{term.lower().replace(' ', '_')}",
            locale=target_locale
        )

        # If translation is the same as key, return original term
        if translation == f"medical.terms.{term.lower().replace(' ', '_')}":
            return term

        return translation

    def get_all_translations(self, locale: Optional[str] = None) -> Dict[str, Any]:
        """
        Get all translations for a locale.

        Args:
            locale: Target locale (defaults to current)

        Returns:
            Dictionary of all translations
        """
        target_locale = locale or self.locale
        return self.translations.get(target_locale, {})

    def is_rtl(self, locale: Optional[str] = None) -> bool:
        """
        Check if locale uses right-to-left text direction.

        Args:
            locale: Locale to check (defaults to current)

        Returns:
            True if RTL, False otherwise
        """
        target_locale = locale or self.locale
        rtl_locales = ["ar", "he", "ur"]  # None of our current locales are RTL
        return target_locale in rtl_locales


# Global translator instance
_global_translator: Optional[Translator] = None


def get_translator(locale: Optional[str] = None) -> Translator:
    """
    Get global translator instance.

    Args:
        locale: Locale to set (if provided)

    Returns:
        Global Translator instance
    """
    global _global_translator

    if _global_translator is None:
        _global_translator = Translator(locale or Translator.DEFAULT_LOCALE)
    elif locale:
        _global_translator.set_locale(locale)

    return _global_translator


def t(key: str, **kwargs) -> str:
    """
    Global translation function.

    Args:
        key: Translation key
        **kwargs: Parameters for interpolation

    Returns:
        Translated string
    """
    translator = get_translator()
    return translator.translate(key, params=kwargs)
