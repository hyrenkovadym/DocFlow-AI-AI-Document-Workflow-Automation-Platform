from app.core.config import Settings, get_settings
from app.services.ai.base import AIProvider
from app.services.ai.mock_provider import MockAIProvider
from app.services.ai.openai_provider import OpenAICompatibleProvider


def get_ai_provider(settings: Settings | None = None) -> AIProvider:
    current_settings = settings or get_settings()
    provider_name = current_settings.resolved_ai_provider

    if provider_name == "openai":
        return OpenAICompatibleProvider(settings=current_settings)
    return MockAIProvider()
