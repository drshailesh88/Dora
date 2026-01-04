# Dora Internationalization (i18n) Module

Comprehensive multilingual support for the Dora medical knowledge platform, with full support for Indian languages.

## Supported Languages

- 🇬🇧 **English (en)** - Default language
- 🇮🇳 **Hindi (hi)** - हिंदी - **Full support with 200+ UI strings and 100+ medical terms**
- 🇮🇳 **Marathi (mr)** - मराठी - Structure file (translations needed)
- 🇮🇳 **Tamil (ta)** - தமிழ் - Structure file (translations needed)
- 🇮🇳 **Telugu (te)** - తెలుగు - Structure file (translations needed)
- 🇮🇳 **Bengali (bn)** - বাংলা - Structure file (translations needed)

## Features

✅ **Translation Service**
- Fallback to English for missing translations
- Parameter interpolation with {placeholders}
- Pluralization support
- Nested key access with dot notation

✅ **Language Detection**
- Automatic detection from user queries
- Unicode range detection for Indian scripts
- Word-based language identification
- Confidence scoring

✅ **Medical Terminology Database**
- 100+ medical terms in multiple languages
- Diseases, symptoms, body parts, drugs, lab tests, procedures
- Clinical accuracy maintained across translations
- UMLS concept mapping (where applicable)

✅ **Locale-Specific Formatting**
- Number formatting (Indian vs Western numbering)
- Date/time formatting
- Medical abbreviation handling

## Installation

The i18n module is part of the Dora project. No additional installation needed.

```python
from src.i18n import Translator, detect_language, translate_medical_term
```

## Quick Start

### Basic Translation

```python
from src.i18n import Translator

# Create translator instance
translator = Translator("hi")  # Hindi

# Translate a key
text = translator.translate("nav.home")
# Returns: "होम"

# Translate with parameters
welcome = translator.translate(
    "messages.welcome",
    params={"name": "डॉ. शर्मा"}
)
# Returns: "स्वागत है, डॉ. शर्मा"

# Shorthand
text = translator.t("buttons.submit")
# Returns: "सबमिट करें"
```

### Language Detection

```python
from src.i18n import detect_language

# Detect language from text
lang, confidence = detect_language("मधुमेह का इलाज क्या है?")
# Returns: ("hi", 0.95)

# Check if Indian language
from src.i18n import is_indian_language
is_indian = is_indian_language("नमस्ते")
# Returns: True
```

### Medical Term Translation

```python
from src.i18n import translate_medical_term

# Translate medical term
term_hi = translate_medical_term("diabetes", "hi")
# Returns: "मधुमेह"

term_ta = translate_medical_term("fever", "ta")
# Returns: "காய்ச்சல்"
```

### Query Translation Workflow

```python
from src.i18n import Translator, detect_language

# 1. Detect language from user query
user_query = "मधुमेह का इलाज क्या है?"
lang, confidence = detect_language(user_query)

# 2. Initialize translator
translator = Translator(lang)

# 3. Translate query to English for RAG pipeline
# (Use AI translation service in production)
english_query = "What is the treatment for diabetes?"

# 4. Process through RAG pipeline
rag_response = process_rag_query(english_query)

# 5. Translate response back to user's language
response_template = translator.t("responses.answer_template")
draft_warning = translator.t("responses.draft_warning")

# Return to user in their language
return {
    "answer": rag_response,
    "warning": draft_warning,
    "locale": lang
}
```

## Integration Examples

### FastAPI Backend

```python
from fastapi import FastAPI, Depends, Header
from src.i18n import Translator

def get_translator(accept_language: str = Header(None)) -> Translator:
    locale = accept_language.split(",")[0].split("-")[0] if accept_language else "en"
    return Translator(locale)

@app.get("/api/hello")
async def hello(translator: Translator = Depends(get_translator)):
    return {"message": translator.t("messages.welcome", name="User")}
```

See `examples/api_integration.py` for complete FastAPI example.

### Flet Desktop App

```python
import flet as ft
from src.i18n import get_translator

translator = get_translator("hi")

# Use in UI
ft.Text(translator.t("nav.home"))
ft.ElevatedButton(text=translator.t("buttons.submit"))
```

See `examples/desktop_integration.py` for complete Flet example.

### Flutter Mobile App

1. Run `flutter gen-l10n` to generate localizations
2. Import generated code:

```dart
import 'package:dora/generated/l10n/app_localizations.dart';

// In widget:
final localizations = AppLocalizations.of(context)!;
Text(localizations.home)
```

See `examples/flutter_integration.dart` for complete Flutter example.

## Translation Keys Structure

Translation keys use dot notation for organization:

```
app.name                    - Application name
app.tagline                 - Application tagline

nav.home                    - Navigation items
nav.search
nav.library

buttons.submit              - Button labels
buttons.cancel

forms.labels.email          - Form field labels
forms.placeholders.email    - Form placeholders
forms.validation.required   - Validation messages

errors.general              - Error messages
errors.network

success.saved               - Success messages

messages.welcome            - General messages

medical.terms.diabetes      - Medical terms
medical.specialties.cardiology
medical.dosage.once_daily
medical.vital_signs.blood_pressure

responses.answer_template   - Response templates
responses.draft_warning

search.search_placeholder   - Search-related
patient.patient_name        - Patient-related
settings.language           - Settings
time.today                  - Time-related
voice.listening             - Voice commands
offline.offline_mode        - Offline features
common.and                  - Common words
```

## Adding New Translations

### Adding a new language:

1. Create `locales/{lang_code}.json` file
2. Copy structure from `locales/en.json`
3. Translate all values
4. Add language code to `Translator.SUPPORTED_LOCALES` in `translator.py`
5. Add language to `LanguageDetector` patterns in `detector.py`

### Adding new translation keys:

1. Add to `locales/en.json` (English is the reference)
2. Add to all other language files
3. Use consistent key naming (lowercase, underscores)
4. Document in this README

## Medical Terms

The module includes a comprehensive medical terminology database with 100+ terms:

- **Diseases**: diabetes, hypertension, asthma, tuberculosis, malaria, etc.
- **Symptoms**: fever, cough, headache, pain, nausea, etc.
- **Anatomy**: heart, brain, liver, kidney, lung, etc.
- **Drugs**: antibiotic, painkiller, insulin, etc.
- **Lab Tests**: blood test, X-ray, ECG, etc.
- **Procedures**: surgery, injection, vaccination, etc.

Access via:
```python
from src.i18n import MedicalTermsDatabase

# Get all terms
terms = MedicalTermsDatabase.get_all_terms()

# Get terms by category
diseases = MedicalTermsDatabase.get_terms_by_category("disease")

# Get translation dictionary
hindi_terms = MedicalTermsDatabase.get_translation_dict("hi")
```

## Best Practices

### DO:
✅ Always provide English translation as fallback
✅ Use parameter interpolation for dynamic values
✅ Keep medical abbreviations consistent (BP, ECG, etc.)
✅ Preserve medical accuracy in translations
✅ Test with actual native speakers
✅ Use AI draft warning for generated content

### DON'T:
❌ Hard-code UI strings in code
❌ Mix translation keys inconsistently
❌ Translate medical abbreviations
❌ Skip fallback translations
❌ Ignore locale-specific formatting

## API Reference

### Translator Class

```python
Translator(locale: str = "en")
    .translate(key: str, params: Dict = None, locale: str = None) -> str
    .t(key: str, **kwargs) -> str  # Shorthand
    .set_locale(locale: str)
    .get_locale() -> str
    .format_number(number: float, decimals: int = 2) -> str
    .format_date(date: datetime, format: str = "medium") -> str
    .translate_medical_term(term: str) -> str
    .get_all_translations(locale: str = None) -> Dict
    .is_rtl(locale: str = None) -> bool
```

### LanguageDetector Class

```python
LanguageDetector.detect(text: str) -> Tuple[str, float]
LanguageDetector.is_indian_language(text: str) -> bool
LanguageDetector.detect_query_language(query: str) -> str
```

### MedicalTermsDatabase Class

```python
MedicalTermsDatabase.get_all_terms() -> List[MedicalTerm]
MedicalTermsDatabase.get_terms_by_category(category: str) -> List[MedicalTerm]
MedicalTermsDatabase.find_term(english_term: str) -> Optional[MedicalTerm]
MedicalTermsDatabase.translate_term(english_term: str, target_lang: str) -> str
MedicalTermsDatabase.get_translation_dict(target_lang: str) -> Dict[str, str]
```

## Translation Coverage

### Hindi (hi)
- ✅ **220+ UI strings** (100% coverage)
- ✅ **100+ medical terms** (100% coverage)
- ✅ Complete navigation, buttons, forms, errors, messages
- ✅ Medical specialties, dosage instructions, vital signs
- ✅ Response templates and warnings

### Other Languages
- ⚠️ **Structure files only** - Need native speaker translations
- ✅ Basic navigation and medical terms included as samples
- 📝 Full translations needed: ~220 strings per language

## Contributing Translations

We welcome contributions from native speakers!

To contribute:
1. Fork the repository
2. Edit `locales/{lang_code}.json`
3. Translate missing strings
4. Maintain clinical accuracy for medical terms
5. Submit pull request

For medical term translations, please consult with medical professionals to ensure accuracy.

## Testing

```python
# Run tests
python -m pytest tests/test_i18n.py

# Test language detection
python -m src.i18n.detector

# Test translator
python -m src.i18n.translator
```

## License

Part of the Dora project. See main LICENSE file.

## Support

For questions or issues:
- Open an issue on GitHub
- Contact: dora-support@docassist.in
- Documentation: https://docs.docassist.in/i18n

---

**Last Updated**: January 2026
**Version**: 1.0.0
**Maintainer**: Dora Development Team
