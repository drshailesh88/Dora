"""
Language detection for Dora medical knowledge platform.

Detects language from user queries to enable automatic translation.
"""

import re
from typing import Optional, Tuple


class LanguageDetector:
    """Detect language from text input."""

    # Unicode ranges for Indian languages
    UNICODE_RANGES = {
        "hi": (0x0900, 0x097F),  # Devanagari (Hindi/Marathi)
        "ta": (0x0B80, 0x0BFF),  # Tamil
        "te": (0x0C00, 0x0C7F),  # Telugu
        "kn": (0x0C80, 0x0CFF),  # Kannada
        "bn": (0x0980, 0x09FF),  # Bengali
    }

    # Common Hindi words
    HINDI_WORDS = {
        "है", "हैं", "का", "की", "के", "को", "में", "से", "पर", "और", "या",
        "नहीं", "क्या", "कैसे", "कब", "कहाँ", "कौन", "यह", "वह", "मुझे",
        "मरीज", "रोगी", "डॉक्टर", "दवा", "बीमारी", "इलाज", "लक्षण", "जांच"
    }

    # Common Marathi words
    MARATHI_WORDS = {
        "आहे", "आहेत", "चा", "ची", "चे", "मध्ये", "आणि", "किंवा", "नाही",
        "काय", "कसे", "कधी", "कुठे", "कोण", "हा", "ता", "मला"
    }

    # Common Tamil words
    TAMIL_WORDS = {
        "என்ன", "எப்படி", "எப்போது", "எங்கே", "யார்", "இது", "அது",
        "நோயாளி", "மருத்துவர்", "மருந்து", "நோய்", "சிகிச்சை"
    }

    # Common Telugu words
    TELUGU_WORDS = {
        "ఏమిటి", "ఎలా", "ఎప్పుడు", "ఎక్కడ", "ఎవరు", "ఇది", "అది",
        "రోగి", "వైద్యుడు", "ఔషధం", "వ్యాధి", "చికిత్స"
    }

    # Common Kannada words
    KANNADA_WORDS = {
        "ಏನು", "ಹೇಗೆ", "ಯಾವಾಗ", "ಎಲ್ಲಿ", "ಯಾರು", "ಇದು", "ಅದು",
        "ರೋಗಿ", "ವೈದ್ಯರು", "ಔಷಧ", "ರೋಗ", "ಚಿಕಿತ್ಸೆ"
    }

    # Common Bengali words
    BENGALI_WORDS = {
        "কি", "কিভাবে", "কখন", "কোথায়", "কে", "এটা", "সেটা",
        "রোগী", "ডাক্তার", "ওষুধ", "রোগ", "চিকিৎসা"
    }

    LANGUAGE_WORDS = {
        "hi": HINDI_WORDS,
        "mr": MARATHI_WORDS,
        "ta": TAMIL_WORDS,
        "te": TELUGU_WORDS,
        "kn": KANNADA_WORDS,
        "bn": BENGALI_WORDS,
    }

    @classmethod
    def detect(cls, text: str) -> Tuple[str, float]:
        """
        Detect language from text.

        Args:
            text: Input text to analyze

        Returns:
            Tuple of (language_code, confidence_score)
            language_code: "en", "hi", "mr", "ta", "te", "bn"
            confidence_score: 0.0 to 1.0

        Examples:
            >>> detector = LanguageDetector()
            >>> detector.detect("मधुमेह का इलाज क्या है?")
            ("hi", 0.95)
            >>> detector.detect("What is the treatment for diabetes?")
            ("en", 0.90)
        """
        if not text or not text.strip():
            return ("en", 0.0)

        text = text.strip()
        scores = {
            "en": 0.0,
            "hi": 0.0,
            "mr": 0.0,
            "ta": 0.0,
            "te": 0.0,
            "kn": 0.0,
            "bn": 0.0,
        }

        # Check Unicode ranges
        for char in text:
            char_code = ord(char)

            for lang, (start, end) in cls.UNICODE_RANGES.items():
                if start <= char_code <= end:
                    scores[lang] += 1

        # Check for language-specific words
        words = text.split()
        for lang, word_set in cls.LANGUAGE_WORDS.items():
            for word in words:
                if word in word_set:
                    scores[lang] += 5  # Word matches are stronger signals

        # Check for English (ASCII letters)
        ascii_count = sum(1 for c in text if ord(c) < 128 and c.isalpha())
        scores["en"] = ascii_count

        # Disambiguate Hindi and Marathi (both use Devanagari)
        if scores["hi"] > 0 or scores["mr"] > 0:
            hindi_word_count = sum(1 for word in words if word in cls.HINDI_WORDS)
            marathi_word_count = sum(1 for word in words if word in cls.MARATHI_WORDS)

            if marathi_word_count > hindi_word_count:
                scores["mr"] += scores["hi"]
                scores["hi"] = marathi_word_count * 5
            else:
                scores["hi"] += scores["mr"]
                scores["mr"] = 0

        # Calculate confidence
        total_score = sum(scores.values())
        if total_score == 0:
            return ("en", 0.0)

        # Get language with highest score
        detected_lang = max(scores, key=scores.get)
        confidence = scores[detected_lang] / total_score

        return (detected_lang, confidence)

    @classmethod
    def is_indian_language(cls, text: str) -> bool:
        """
        Check if text is in any Indian language.

        Args:
            text: Input text

        Returns:
            True if Indian language detected, False otherwise
        """
        lang, confidence = cls.detect(text)
        return lang != "en" and confidence > 0.5

    @classmethod
    def detect_query_language(cls, query: str) -> str:
        """
        Detect language from user query.

        Args:
            query: User's medical query

        Returns:
            Language code with fallback to "en"
        """
        lang, confidence = cls.detect(query)

        # Require minimum confidence threshold
        if confidence < 0.3:
            return "en"

        return lang

    @classmethod
    def get_script_name(cls, lang_code: str) -> str:
        """
        Get script name for a language code.

        Args:
            lang_code: Language code

        Returns:
            Script name
        """
        scripts = {
            "en": "Latin",
            "hi": "Devanagari",
            "mr": "Devanagari",
            "ta": "Tamil",
            "te": "Telugu",
            "kn": "Kannada",
            "bn": "Bengali",
        }
        return scripts.get(lang_code, "Unknown")

    @classmethod
    def transliterate_to_latin(cls, text: str) -> str:
        """
        Transliterate Indian language text to Latin script (basic).

        This is a simple mapping for common characters.
        For production, use a proper transliteration library.

        Args:
            text: Text in Indian language

        Returns:
            Transliterated text
        """
        # Basic Devanagari to Latin mapping (incomplete, for demonstration)
        devanagari_map = {
            "अ": "a", "आ": "aa", "इ": "i", "ई": "ee", "उ": "u", "ऊ": "oo",
            "ए": "e", "ऐ": "ai", "ओ": "o", "औ": "au",
            "क": "ka", "ख": "kha", "ग": "ga", "घ": "gha",
            "च": "cha", "छ": "chha", "ज": "ja", "झ": "jha",
            "ट": "ta", "ठ": "tha", "ड": "da", "ढ": "dha",
            "त": "ta", "थ": "tha", "द": "da", "ध": "dha",
            "न": "na", "प": "pa", "फ": "pha", "ब": "ba", "भ": "bha",
            "म": "ma", "य": "ya", "र": "ra", "ल": "la", "व": "va",
            "श": "sha", "ष": "sha", "स": "sa", "ह": "ha",
        }

        result = []
        for char in text:
            if char in devanagari_map:
                result.append(devanagari_map[char])
            else:
                result.append(char)

        return "".join(result)


# Convenience functions
def detect_language(text: str) -> Tuple[str, float]:
    """
    Detect language from text.

    Args:
        text: Input text

    Returns:
        Tuple of (language_code, confidence)
    """
    return LanguageDetector.detect(text)


def is_indian_language(text: str) -> bool:
    """
    Check if text is in Indian language.

    Args:
        text: Input text

    Returns:
        True if Indian language, False otherwise
    """
    return LanguageDetector.is_indian_language(text)
