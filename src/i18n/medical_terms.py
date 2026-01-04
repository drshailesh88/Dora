"""
Medical terminology mapping for multilingual support.

Provides standardized medical term translations with clinical accuracy.
Maintains UMLS concept mappings where applicable.
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class MedicalTerm:
    """Represents a medical term with translations."""

    english: str
    hindi: str
    marathi: Optional[str] = None
    tamil: Optional[str] = None
    telugu: Optional[str] = None
    bengali: Optional[str] = None
    umls_cui: Optional[str] = None  # UMLS Concept Unique Identifier
    category: str = "general"  # disease, symptom, anatomy, drug, procedure, lab


class MedicalTermsDatabase:
    """Database of medical terminology in multiple languages."""

    # Common diseases
    DISEASES = [
        MedicalTerm("diabetes", "मधुमेह", "मधुमेह", "நீரிழிவு", "మధుమేహం", "ডায়াবেটিস", "C0diabetes mellitus", "disease"),
        MedicalTerm("hypertension", "उच्च रक्तचाप", "उच्च रक्तदाब", "உயர் இரத்த அழுத்தம்", "అధిక రక్తపోటు", "উচ্চ রক্তচাপ", "C0020538", "disease"),
        MedicalTerm("asthma", "दमा", "दमा", "ஆஸ்துமா", "ఆస్తమా", "হাঁপানি", "C0004096", "disease"),
        MedicalTerm("tuberculosis", "तपेदिक", "क्षयरोग", "காசநோய்", "క్షయ", "যক্ষ্মা", "C0041296", "disease"),
        MedicalTerm("malaria", "मलेरिया", "मलेरिया", "மலேரியா", "మలేరియా", "ম্যালেরিয়া", "C0024530", "disease"),
        MedicalTerm("dengue", "डेंगू", "डेंग्यू", "டெங்கு", "డెంగ్యూ", "ডেঙ্গু", "C0011311", "disease"),
        MedicalTerm("typhoid", "टायफाइड", "विषमज्वर", "டைபாய்டு", "టైఫాయిడ్", "টাইফয়েড", "C0041466", "disease"),
        MedicalTerm("pneumonia", "निमोनिया", "न्युमोनिया", "நிமோனியா", "న్యుమోనియా", "নিউমোনিয়া", "C0032285", "disease"),
        MedicalTerm("heart disease", "हृदय रोग", "हृदयरोग", "இதய நோய்", "గుండె జబ్బు", "হৃদরোগ", "C0018799", "disease"),
        MedicalTerm("stroke", "आघात", "पक्षाघात", "பக்கவாதம்", "స్ట్రోక్", "স্ট্রোক", "C0038454", "disease"),
        MedicalTerm("cancer", "कैंसर", "कर्करोग", "புற்றுநோய்", "క్యాన్సర్", "ক্যান্সার", "C0006826", "disease"),
        MedicalTerm("arthritis", "गठिया", "संधिवात", "மூட்டுவலி", "కీళ్ళ నొప్పులు", "বাত", "C0003864", "disease"),
        MedicalTerm("hepatitis", "हेपेटाइटिस", "यकृतशोथ", "கல்லீரல் அழற்சி", "హెపటైటిస్", "হেপাটাইটিস", "C0019158", "disease"),
        MedicalTerm("anemia", "एनीमिया", "पांडुरोग", "இரத்த சோகை", "రక్తహీనత", "রক্তাল্পতা", "C0002871", "disease"),
        MedicalTerm("kidney disease", "गुर्दे की बीमारी", "मूत्रपिंड रोग", "சிறுநீரக நோய்", "మూత్రపిండాల వ్యాధి", "কিডনি রোগ", "C0022658", "disease"),
    ]

    # Common symptoms
    SYMPTOMS = [
        MedicalTerm("fever", "बुखार", "ताप", "காய்ச்சல்", "జ్వరం", "জ্বর", category="symptom"),
        MedicalTerm("cough", "खांसी", "खोकला", "இருமல்", "దగ్గు", "কাশি", category="symptom"),
        MedicalTerm("headache", "सिरदर्द", "डोकेदुखी", "தலைவலி", "తలనొప్పి", "মাথাব্যথা", category="symptom"),
        MedicalTerm("pain", "दर्द", "वेदना", "வலி", "నొప్పి", "ব্যথা", category="symptom"),
        MedicalTerm("nausea", "मतली", "मळमळणे", "குமட்டல்", "వాంతి భావం", "বমি বমি ভাব", category="symptom"),
        MedicalTerm("vomiting", "उल्टी", "उलट्या", "வாந்தி", "వాంతులు", "বমি", category="symptom"),
        MedicalTerm("diarrhea", "दस्त", "अतिसार", "வயிற்றுப்போக்கு", "విరేచనం", "ডায়রিয়া", category="symptom"),
        MedicalTerm("constipation", "कब्ज", "बद्धकोष्ठता", "மலச்சிக்கல்", "మలబద్ధకం", "কোষ্ঠকাঠিন্য", category="symptom"),
        MedicalTerm("fatigue", "थकान", "थकवा", "சோர்வு", "అలసట", "ক্লান্তি", category="symptom"),
        MedicalTerm("weakness", "कमजोरी", "अशक्तपणा", "பலவீனம்", "బలహీనత", "দুর্বলতা", category="symptom"),
        MedicalTerm("dizziness", "चक्कर", "चक्कर येणे", "தலைசுற்றல்", "తలతిరగడం", "মাথা ঘোরা", category="symptom"),
        MedicalTerm("chest pain", "सीने में दर्द", "छातीत दुखणे", "மார்பு வலி", "ఛాతీ నొప్పి", "বুকে ব্যথা", category="symptom"),
        MedicalTerm("shortness of breath", "सांस फूलना", "श्वास लागणे", "மூச்சுத் திணறல்", "ఊపిరాడక", "শ্বাসকষ্ট", category="symptom"),
        MedicalTerm("swelling", "सूजन", "सूज", "வீக்கம்", "వాపు", "ফোলাভাব", category="symptom"),
        MedicalTerm("rash", "दाने", "पुरळ", "தடிப்பு", "దద్దుర్లు", "ফুসকুড়ি", category="symptom"),
        MedicalTerm("itching", "खुजली", "खाज", "அரிப்பு", "దురద", "চুলকানি", category="symptom"),
        MedicalTerm("bleeding", "रक्तस्राव", "रक्तस्त्राव", "இரத்தப்போக்கு", "రక్తస్రావం", "রক্তপাত", category="symptom"),
        MedicalTerm("abdominal pain", "पेट दर्द", "ओटीपोटात दुखणे", "வயிற்று வலி", "కడుపు నొప్పి", "পেটে ব্যথা", category="symptom"),
    ]

    # Body parts
    ANATOMY = [
        MedicalTerm("heart", "हृदय", "हृदय", "இதயம்", "గుండె", "হৃদয়", category="anatomy"),
        MedicalTerm("brain", "मस्तिष्क", "मेंदू", "மூளை", "మెదడు", "মস্তিষ্ক", category="anatomy"),
        MedicalTerm("liver", "यकृत", "यकृत", "கல்லீரல்", "కాలేయం", "যকৃত", category="anatomy"),
        MedicalTerm("kidney", "गुर्दा", "मूत्रपिंड", "சிறுநீரகம்", "మూత్రపిండం", "কিডনি", category="anatomy"),
        MedicalTerm("lung", "फेफड़ा", "फुफ्फुस", "நுரையீரல்", "ఊపిరితిత్తి", "ফুসফুস", category="anatomy"),
        MedicalTerm("stomach", "पेट", "पोट", "வயிறு", "కడుపు", "পেট", category="anatomy"),
        MedicalTerm("intestine", "आंत", "आतडे", "குடல்", "పేగు", "অন্ত্র", category="anatomy"),
        MedicalTerm("blood", "रक्त", "रक्त", "இரத்தம்", "రక్తం", "রক্ত", category="anatomy"),
        MedicalTerm("bone", "हड्डी", "हाड", "எலும்பு", "ఎముక", "হাড়", category="anatomy"),
        MedicalTerm("muscle", "मांसपेशी", "स्नायू", "தசை", "కండరం", "পেশী", category="anatomy"),
        MedicalTerm("skin", "त्वचा", "त्वचा", "தோல்", "చర్మం", "ত্বক", category="anatomy"),
        MedicalTerm("eye", "आंख", "डोळा", "கண்", "కన్ను", "চোখ", category="anatomy"),
        MedicalTerm("ear", "कान", "कान", "காது", "చెవి", "কান", category="anatomy"),
        MedicalTerm("nose", "नाक", "नाक", "மூக்கு", "ముక్కు", "নাক", category="anatomy"),
        MedicalTerm("throat", "गला", "घसा", "தொண்டை", "గొంతు", "গলা", category="anatomy"),
    ]

    # Drug classes
    DRUGS = [
        MedicalTerm("antibiotic", "एंटीबायोटिक", "प्रतिजैविक", "நுண்ணுயிர் எதிர்ப்பு", "యాంటీబయాటిక్", "অ্যান্টিবায়োটিক", category="drug"),
        MedicalTerm("painkiller", "दर्दनिवारक", "वेदनाशामक", "வலி நிவாரணி", "నొప్పి నివారణ", "ব্যথানাশক", category="drug"),
        MedicalTerm("antacid", "एंटासिड", "आम्लनाशक", "அமில நடுநிலையாக்கி", "యాంటాసిడ్", "অ্যান্টাসিড", category="drug"),
        MedicalTerm("vitamin", "विटामिन", "जीवनसत्व", "வைட்டமின்", "విటమిన్", "ভিটামিন", category="drug"),
        MedicalTerm("insulin", "इंसुलिन", "इन्सुलिन", "இன்சுலின்", "ఇన్సులిన్", "ইনসুলিন", category="drug"),
        MedicalTerm("blood pressure medication", "रक्तचाप की दवा", "रक्तदाब औषध", "இரத்த அழுத்த மருந்து", "రక్తపోటు మందు", "রক্তচাপের ওষুধ", category="drug"),
        MedicalTerm("antidiabetic", "मधुमेह रोधी", "मधुमेहविरोधी", "நீரிழிவு எதிர்ப்பு", "డయాబెటిస్ నిరోధక", "ডায়াবেটিস বিরোধী", category="drug"),
        MedicalTerm("steroid", "स्टेरॉयड", "स्टिरॉइड", "ஸ்டீராய்டு", "స్టెరాయిడ్", "স্টেরয়েড", category="drug"),
        MedicalTerm("antiviral", "एंटीवायरल", "विषाणूनाशक", "வைரஸ் எதிர்ப்பு", "యాంటీవైరల్", "অ্যান্টিভাইরাল", category="drug"),
    ]

    # Lab tests
    LAB_TESTS = [
        MedicalTerm("blood test", "रक्त परीक्षण", "रक्त तपासणी", "இரத்த பரிசோதனை", "రక్త పరీక్ష", "রক্ত পরীক্ষা", category="lab"),
        MedicalTerm("urine test", "मूत्र परीक्षण", "मूत्र तपासणी", "சிறுநீர் பரிசோதனை", "మూత్ర పరీక్ష", "প্রস্রাব পরীক্ষা", category="lab"),
        MedicalTerm("X-ray", "एक्स-रे", "क्ष-किरण", "எக்ஸ்ரே", "ఎక్స్-రే", "এক্স-রে", category="lab"),
        MedicalTerm("ultrasound", "अल्ट्रासाउंड", "प्रतिध्वनि", "அல்ட்ராசவுண்ட்", "అల్ట్రాసౌండ్", "আল্ট্রাসাউন্ড", category="lab"),
        MedicalTerm("ECG", "ईसीजी", "हृद्विद्युतलेख", "மின்னதிர்வு வரைவு", "ఈసీజీ", "ইসিজি", category="lab"),
        MedicalTerm("blood sugar", "रक्त शर्करा", "रक्त साखर", "இரத்த சர்க்கரை", "రక్త చక్కెర", "রক্তে শর্করা", category="lab"),
        MedicalTerm("cholesterol", "कोलेस्ट्रॉल", "कोलेस्टेरॉल", "கொலஸ்ட்ரால்", "కొలెస్ట్రాల్", "কোলেস্টেরল", category="lab"),
        MedicalTerm("hemoglobin", "हीमोग्लोबिन", "रक्तद्रव्य", "ஹீமோகுளோபின்", "హీమోగ్లోబిన్", "হিমোগ্লোবিন", category="lab"),
    ]

    # Medical procedures
    PROCEDURES = [
        MedicalTerm("surgery", "शल्य चिकित्सा", "शस्त्रक्रिया", "அறுவை சிகிச்சை", "శస్త్రచికిత్స", "অস্ত্রোপচার", category="procedure"),
        MedicalTerm("injection", "इंजेक्शन", "सुई", "ஊசி", "ఇంజెక్షన్", "ইনজেকশন", category="procedure"),
        MedicalTerm("vaccination", "टीकाकरण", "लसीकरण", "தடுப்பூசி", "టీకా", "টিকাকরণ", category="procedure"),
        MedicalTerm("checkup", "जांच", "तपासणी", "பரிசோதனை", "తనిఖీ", "পরীক্ষা", category="procedure"),
        MedicalTerm("consultation", "परामर्श", "सल्लामसलत", "ஆலோசனை", "సంప్రదింపు", "পরামর্শ", category="procedure"),
        MedicalTerm("treatment", "इलाज", "उपचार", "சிகிச்சை", "చికిత్స", "চিকিৎসা", category="procedure"),
        MedicalTerm("therapy", "चिकित्सा", "थेरपी", "சிகிச்சை முறை", "థెరపీ", "থেরাপি", category="procedure"),
        MedicalTerm("diagnosis", "निदान", "निदान", "நோய் கண்டறிதல்", "రోగ నిర్ధారణ", "রোগ নির্ণয়", category="procedure"),
    ]

    # Medical personnel
    PERSONNEL = [
        MedicalTerm("doctor", "डॉक्टर", "डॉक्टर", "மருத்துவர்", "డాక్టర్", "ডাক্তার", category="personnel"),
        MedicalTerm("nurse", "नर्स", "परिचारिका", "செவிலியர்", "నర్సు", "নার্স", category="personnel"),
        MedicalTerm("patient", "रोगी", "रुग्ण", "நோயாளி", "రోగి", "রোগী", category="personnel"),
        MedicalTerm("surgeon", "शल्य चिकित्सक", "शल्यचिकित्सक", "அறுவை சிகிச்சை நிபுணர்", "శస్త్రచికిత్సకుడు", "সার্জন", category="personnel"),
        MedicalTerm("specialist", "विशेषज्ञ", "तज्ञ", "நிபுணர்", "నిపుణుడు", "বিশেষজ্ঞ", category="personnel"),
    ]

    @classmethod
    def get_all_terms(cls) -> List[MedicalTerm]:
        """Get all medical terms."""
        return (
            cls.DISEASES +
            cls.SYMPTOMS +
            cls.ANATOMY +
            cls.DRUGS +
            cls.LAB_TESTS +
            cls.PROCEDURES +
            cls.PERSONNEL
        )

    @classmethod
    def get_terms_by_category(cls, category: str) -> List[MedicalTerm]:
        """Get terms filtered by category."""
        all_terms = cls.get_all_terms()
        return [term for term in all_terms if term.category == category]

    @classmethod
    def find_term(cls, english_term: str) -> Optional[MedicalTerm]:
        """Find medical term by English name."""
        for term in cls.get_all_terms():
            if term.english.lower() == english_term.lower():
                return term
        return None

    @classmethod
    def translate_term(cls, english_term: str, target_lang: str) -> str:
        """
        Translate medical term to target language.

        Args:
            english_term: English medical term
            target_lang: Target language code (hi, mr, ta, te, bn)

        Returns:
            Translated term or original if not found
        """
        term = cls.find_term(english_term)
        if not term:
            return english_term

        lang_map = {
            "en": term.english,
            "hi": term.hindi,
            "mr": term.marathi,
            "ta": term.tamil,
            "te": term.telugu,
            "bn": term.bengali,
        }

        translation = lang_map.get(target_lang)
        return translation if translation else term.english

    @classmethod
    def get_translation_dict(cls, target_lang: str) -> Dict[str, str]:
        """
        Get dictionary mapping English terms to target language.

        Args:
            target_lang: Target language code

        Returns:
            Dictionary of {english: translation}
        """
        result = {}
        for term in cls.get_all_terms():
            translation = cls.translate_term(term.english, target_lang)
            result[term.english] = translation
        return result

    @classmethod
    def reverse_lookup(cls, translated_term: str, source_lang: str) -> Optional[str]:
        """
        Find English term from translation.

        Args:
            translated_term: Term in source language
            source_lang: Source language code

        Returns:
            English term if found, None otherwise
        """
        for term in cls.get_all_terms():
            lang_attr = {
                "hi": term.hindi,
                "mr": term.marathi,
                "ta": term.tamil,
                "te": term.telugu,
                "bn": term.bengali,
            }.get(source_lang)

            if lang_attr and lang_attr.lower() == translated_term.lower():
                return term.english

        return None


# Convenience functions
def translate_medical_term(term: str, target_lang: str) -> str:
    """Translate medical term to target language."""
    return MedicalTermsDatabase.translate_term(term, target_lang)


def get_medical_terms_dict(target_lang: str) -> Dict[str, str]:
    """Get medical terms dictionary for target language."""
    return MedicalTermsDatabase.get_translation_dict(target_lang)
