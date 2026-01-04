"""
Internationalization (i18n) module for Dora medical knowledge platform.

Provides comprehensive multilingual support for Indian languages including:
- Hindi (हिंदी)
- Marathi (मराठी)
- Tamil (தமிழ்)
- Telugu (తెలుగు)
- Bengali (বাংলা)

Features:
- Translation service with fallback
- Language detection
- Medical terminology database
- Query translation for RAG pipeline
- Locale-specific formatting

Usage:
    from src.i18n import Translator, t, detect_language

    # Initialize translator
    translator = Translator("hi")

    # Translate a key
    text = translator.translate("nav.home")  # Returns: "होम"

    # Or use global function
    text = t("messages.welcome", name="डॉ. शर्मा")

    # Detect language
    lang, confidence = detect_language("मधुमेह का इलाज क्या है?")
    # Returns: ("hi", 0.95)
"""

from .translator import Translator, get_translator, t
from .detector import LanguageDetector, detect_language, is_indian_language
from .medical_terms import (
    MedicalTerm,
    MedicalTermsDatabase,
    translate_medical_term,
    get_medical_terms_dict,
)

__all__ = [
    # Translator
    "Translator",
    "get_translator",
    "t",
    # Language detector
    "LanguageDetector",
    "detect_language",
    "is_indian_language",
    # Medical terms
    "MedicalTerm",
    "MedicalTermsDatabase",
    "translate_medical_term",
    "get_medical_terms_dict",
]

__version__ = "1.0.0"
