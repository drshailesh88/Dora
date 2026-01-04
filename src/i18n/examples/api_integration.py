"""
Example: FastAPI backend integration with i18n.

This shows how to use the translation system in FastAPI endpoints
to support multilingual responses.
"""

from fastapi import FastAPI, Request, Depends, Header
from typing import Optional
from src.i18n import Translator, detect_language

app = FastAPI()


def get_translator(
    accept_language: Optional[str] = Header(None),
    user_locale: Optional[str] = None
) -> Translator:
    """
    Dependency to get translator based on Accept-Language header or user preference.

    Args:
        accept_language: Accept-Language header from request
        user_locale: User's saved language preference (from DB/session)

    Returns:
        Translator instance configured for appropriate locale
    """
    # Priority: user_locale > accept_language > default (en)
    locale = "en"

    if user_locale and user_locale in Translator.SUPPORTED_LOCALES:
        locale = user_locale
    elif accept_language:
        # Parse Accept-Language header (e.g., "hi,en-US;q=0.9,en;q=0.8")
        langs = accept_language.split(",")
        for lang in langs:
            lang_code = lang.split(";")[0].split("-")[0].strip()
            if lang_code in Translator.SUPPORTED_LOCALES:
                locale = lang_code
                break

    return Translator(locale)


@app.get("/api/v1/hello")
async def hello(
    name: str = "User",
    translator: Translator = Depends(get_translator)
):
    """
    Example endpoint with translated response.

    Usage:
        curl -H "Accept-Language: hi" "http://localhost:8000/api/v1/hello?name=शर्मा"
    """
    return {
        "message": translator.translate("messages.welcome", params={"name": name}),
        "locale": translator.get_locale()
    }


@app.post("/api/v1/query")
async def process_query(
    request: Request,
    translator: Translator = Depends(get_translator)
):
    """
    Example: Process medical query with language detection and translation.

    Workflow:
    1. Detect language from user query
    2. If Hindi/Indian language, translate query to English for RAG
    3. Process query through RAG pipeline
    4. Translate response back to user's language
    """
    data = await request.json()
    user_query = data.get("query", "")

    # Detect query language
    detected_lang, confidence = detect_language(user_query)

    # Set translator to detected language if high confidence
    if confidence > 0.7:
        translator.set_locale(detected_lang)

    # Simulate RAG response (in practice, this would call your RAG pipeline)
    rag_response = {
        "answer": "Type 2 diabetes is managed with diet, exercise, and medications.",
        "sources": [
            {"title": "UpToDate: Diabetes Management", "url": "..."}
        ]
    }

    # Translate response template
    response_template = translator.translate("responses.answer_template")
    based_on = translator.translate("responses.based_on")
    sources_label = translator.translate("responses.sources")
    draft_warning = translator.translate("responses.draft_warning")

    # In production, you'd translate the actual answer using AI translation
    # For medical accuracy, consider keeping medical terms in English
    # or using the medical_terms translation database

    return {
        "query": user_query,
        "detected_language": detected_lang,
        "confidence": confidence,
        "locale": translator.get_locale(),
        "response": {
            "template": response_template,
            "answer": rag_response["answer"],
            "warning": draft_warning,
            "sources_label": sources_label,
            "sources": rag_response["sources"]
        }
    }


@app.get("/api/v1/medical-term/{term}")
async def translate_medical_term(
    term: str,
    translator: Translator = Depends(get_translator)
):
    """
    Example: Translate medical term to user's language.

    Usage:
        curl -H "Accept-Language: hi" "http://localhost:8000/api/v1/medical-term/diabetes"
    """
    translated = translator.translate_medical_term(term)

    return {
        "term": term,
        "translation": translated,
        "locale": translator.get_locale()
    }


@app.get("/api/v1/translations")
async def get_all_translations(
    translator: Translator = Depends(get_translator)
):
    """
    Get all translations for current locale.

    Useful for initializing frontend apps with translations.

    Usage:
        curl -H "Accept-Language: hi" "http://localhost:8000/api/v1/translations"
    """
    return {
        "locale": translator.get_locale(),
        "translations": translator.get_all_translations()
    }


# Middleware example for setting locale from user session
from starlette.middleware.base import BaseHTTPMiddleware

class LocaleMiddleware(BaseHTTPMiddleware):
    """
    Middleware to set locale from user session/cookie.
    """
    async def dispatch(self, request: Request, call_next):
        # Get locale from cookie or session
        locale = request.cookies.get("locale")

        if locale and locale in Translator.SUPPORTED_LOCALES:
            # Store in request state for use in dependencies
            request.state.locale = locale

        response = await call_next(request)
        return response


# Add middleware
app.add_middleware(LocaleMiddleware)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
