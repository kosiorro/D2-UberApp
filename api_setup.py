"""API onboarding shared by the UI and capture pipeline."""
API_KEY_URL = 'https://aistudio.google.com/apikey'


def setup_message(lang='pl'):
    return ('Connect your Gemini API key in Settings to start scanning.' if lang == 'en'
            else 'Aby rozpocząć skanowanie, podłącz klucz Gemini API w Ustawieniach.')


def has_api_key():
    import config
    return bool(str(config.GEMINI_API_KEY or '').strip())
