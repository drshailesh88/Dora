"""
Translation Coverage Report Generator for Dora i18n.

Analyzes translation files and generates comprehensive coverage statistics.
"""

import json
from pathlib import Path
from typing import Dict, List, Tuple
from collections import defaultdict


class CoverageReporter:
    """Generate translation coverage reports."""

    def __init__(self, locales_dir: Path = None):
        """
        Initialize coverage reporter.

        Args:
            locales_dir: Path to locales directory
        """
        if locales_dir is None:
            locales_dir = Path(__file__).parent / "locales"
        self.locales_dir = locales_dir
        self.translations = {}
        self._load_all_translations()

    def _load_all_translations(self):
        """Load all translation files."""
        for locale_file in self.locales_dir.glob("*.json"):
            locale = locale_file.stem
            with open(locale_file, 'r', encoding='utf-8') as f:
                self.translations[locale] = json.load(f)

    def _count_keys(self, data: Dict, prefix: str = "") -> List[str]:
        """
        Recursively count all translation keys.

        Args:
            data: Dictionary to analyze
            prefix: Key prefix for nested keys

        Returns:
            List of all keys
        """
        keys = []

        for key, value in data.items():
            # Skip metadata keys
            if key.startswith("_") or key.startswith("@"):
                continue

            full_key = f"{prefix}.{key}" if prefix else key

            if isinstance(value, dict):
                # Recurse into nested dictionaries
                keys.extend(self._count_keys(value, full_key))
            else:
                # Leaf node - actual translation
                keys.append(full_key)

        return keys

    def get_locale_stats(self, locale: str) -> Dict:
        """
        Get statistics for a specific locale.

        Args:
            locale: Language code

        Returns:
            Dictionary with statistics
        """
        if locale not in self.translations:
            return {"error": "Locale not found"}

        data = self.translations[locale]
        keys = self._count_keys(data)

        # Categorize by top-level key
        categories = defaultdict(int)
        for key in keys:
            category = key.split(".")[0]
            categories[category] += 1

        # Count medical terms specifically
        medical_terms = len([k for k in keys if k.startswith("medical.terms.")])

        return {
            "locale": locale,
            "total_keys": len(keys),
            "categories": dict(categories),
            "medical_terms": medical_terms,
            "all_keys": keys
        }

    def compare_coverage(self, base_locale: str = "en") -> Dict:
        """
        Compare coverage of all locales against base locale.

        Args:
            base_locale: Reference locale (usually English)

        Returns:
            Coverage comparison dictionary
        """
        if base_locale not in self.translations:
            return {"error": "Base locale not found"}

        base_keys = set(self._count_keys(self.translations[base_locale]))

        coverage = {}
        for locale in self.translations.keys():
            if locale == base_locale:
                coverage[locale] = {
                    "total_keys": len(base_keys),
                    "translated": len(base_keys),
                    "missing": 0,
                    "coverage_percent": 100.0
                }
            else:
                locale_keys = set(self._count_keys(self.translations[locale]))
                translated = len(locale_keys & base_keys)
                missing = len(base_keys - locale_keys)
                coverage_percent = (translated / len(base_keys)) * 100 if base_keys else 0

                coverage[locale] = {
                    "total_keys": len(base_keys),
                    "translated": translated,
                    "missing": missing,
                    "coverage_percent": coverage_percent,
                    "missing_keys": list(base_keys - locale_keys)[:10]  # First 10
                }

        return coverage

    def generate_report(self, output_file: Path = None) -> str:
        """
        Generate comprehensive coverage report.

        Args:
            output_file: Optional file path to write report

        Returns:
            Report as string
        """
        report_lines = [
            "=" * 80,
            "DORA INTERNATIONALIZATION COVERAGE REPORT",
            "=" * 80,
            "",
            f"Report Date: {self._get_current_date()}",
            f"Locales Directory: {self.locales_dir}",
            "",
        ]

        # Overall statistics
        report_lines.extend([
            "SUPPORTED LANGUAGES",
            "-" * 80,
            ""
        ])

        language_names = {
            "en": "English",
            "hi": "Hindi (हिंदी)",
            "mr": "Marathi (मराठी)",
            "ta": "Tamil (தமிழ்)",
            "te": "Telugu (తెలుగు)",
            "bn": "Bengali (বাংলা)"
        }

        for locale in sorted(self.translations.keys()):
            stats = self.get_locale_stats(locale)
            lang_name = language_names.get(locale, locale.upper())
            report_lines.append(f"  {locale.upper()}: {lang_name}")
            report_lines.append(f"      Total Strings: {stats['total_keys']}")
            report_lines.append(f"      Medical Terms: {stats['medical_terms']}")
            report_lines.append("")

        # Detailed coverage comparison
        report_lines.extend([
            "",
            "TRANSLATION COVERAGE (vs English baseline)",
            "-" * 80,
            ""
        ])

        coverage = self.compare_coverage("en")

        for locale in sorted(coverage.keys()):
            data = coverage[locale]
            lang_name = language_names.get(locale, locale.upper())

            status_icon = "✅" if data["coverage_percent"] == 100 else "⚠️"

            report_lines.append(f"{status_icon} {locale.upper()} - {lang_name}")
            report_lines.append(f"   Total Keys: {data['total_keys']}")
            report_lines.append(f"   Translated: {data['translated']}")
            report_lines.append(f"   Missing: {data['missing']}")
            report_lines.append(f"   Coverage: {data['coverage_percent']:.1f}%")

            if data.get("missing_keys"):
                report_lines.append(f"   Sample Missing Keys:")
                for key in data["missing_keys"][:5]:
                    report_lines.append(f"     - {key}")

            report_lines.append("")

        # Category breakdown for Hindi (most complete)
        if "hi" in self.translations:
            report_lines.extend([
                "",
                "HINDI (हिंदी) - CATEGORY BREAKDOWN",
                "-" * 80,
                ""
            ])

            hi_stats = self.get_locale_stats("hi")
            categories = hi_stats["categories"]

            category_names = {
                "app": "Application Info",
                "nav": "Navigation",
                "buttons": "Buttons",
                "forms": "Forms",
                "errors": "Error Messages",
                "success": "Success Messages",
                "messages": "General Messages",
                "medical": "Medical Terms & Info",
                "responses": "Response Templates",
                "search": "Search Interface",
                "patient": "Patient Management",
                "settings": "Settings",
                "time": "Time & Date",
                "voice": "Voice Commands",
                "offline": "Offline Features",
                "common": "Common Phrases"
            }

            for category, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
                cat_name = category_names.get(category, category.title())
                report_lines.append(f"  {category:<15} : {count:>3} strings - {cat_name}")

            report_lines.append("")
            report_lines.append(f"  TOTAL           : {hi_stats['total_keys']} strings")

        # Medical terms breakdown
        report_lines.extend([
            "",
            "",
            "MEDICAL TERMINOLOGY DATABASE",
            "-" * 80,
            ""
        ])

        # Import medical terms database
        try:
            from src.i18n.medical_terms import MedicalTermsDatabase

            all_terms = MedicalTermsDatabase.get_all_terms()
            categories = defaultdict(int)
            for term in all_terms:
                categories[term.category] += 1

            report_lines.append(f"Total Medical Terms: {len(all_terms)}")
            report_lines.append("")
            report_lines.append("By Category:")

            for category, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
                report_lines.append(f"  {category.title():<15} : {count:>3} terms")

            # Sample translations
            report_lines.extend([
                "",
                "Sample Medical Term Translations:",
                ""
            ])

            sample_terms = ["diabetes", "hypertension", "fever", "heart", "treatment"]
            for term_en in sample_terms:
                term_obj = MedicalTermsDatabase.find_term(term_en)
                if term_obj:
                    report_lines.append(f"  {term_en.title()}")
                    report_lines.append(f"    English : {term_obj.english}")
                    report_lines.append(f"    Hindi   : {term_obj.hindi}")
                    if term_obj.marathi:
                        report_lines.append(f"    Marathi : {term_obj.marathi}")
                    if term_obj.tamil:
                        report_lines.append(f"    Tamil   : {term_obj.tamil}")
                    report_lines.append("")

        except ImportError:
            report_lines.append("  (Medical terms database not available)")

        # Integration status
        report_lines.extend([
            "",
            "INTEGRATION STATUS",
            "-" * 80,
            "",
            "✅ Backend (FastAPI)      : Example available at examples/api_integration.py",
            "✅ Desktop (Flet)         : Example available at examples/desktop_integration.py",
            "✅ Mobile (Flutter)       : ARB files + example at examples/flutter_integration.dart",
            "✅ Translation Service    : Core module at src/i18n/translator.py",
            "✅ Language Detection     : Module at src/i18n/detector.py",
            "✅ Medical Terms Database : Module at src/i18n/medical_terms.py",
            "",
        ])

        # Recommendations
        report_lines.extend([
            "",
            "RECOMMENDATIONS",
            "-" * 80,
            "",
            "1. Complete translations for Marathi, Tamil, Telugu, and Bengali",
            "2. Engage native speakers for translation review",
            "3. Validate medical term accuracy with healthcare professionals",
            "4. Add more regional language support (Kannada, Malayalam, etc.)",
            "5. Implement AI-powered query translation for RAG pipeline",
            "6. Add transliteration support for search queries",
            "7. Create user preference management for language selection",
            "8. Add A/B testing for translation quality",
            "",
        ])

        # Footer
        report_lines.extend([
            "=" * 80,
            "END OF REPORT",
            "=" * 80,
        ])

        report = "\n".join(report_lines)

        # Write to file if specified
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"Report written to: {output_file}")

        return report

    @staticmethod
    def _get_current_date() -> str:
        """Get current date as string."""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def main():
    """Generate and print coverage report."""
    reporter = CoverageReporter()
    report = reporter.generate_report()
    print(report)

    # Also save to file
    output_path = Path(__file__).parent / "COVERAGE_REPORT.txt"
    reporter.generate_report(output_path)


if __name__ == "__main__":
    main()
