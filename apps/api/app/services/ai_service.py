"""Backward-compatible AI service re-exports.

New code should import from `app.services.ai`.
"""

from app.services.ai import (
    AIProvider,
    AIProviderConfigurationError,
    AIProviderError,
    AIProviderResponseError,
    DocumentClassification,
    ExtractedFields,
    MockAIProvider,
    OpenAICompatibleProvider,
    get_ai_provider,
)

__all__ = [
    "AIProvider",
    "AIProviderError",
    "AIProviderConfigurationError",
    "AIProviderResponseError",
    "DocumentClassification",
    "ExtractedFields",
    "MockAIProvider",
    "OpenAICompatibleProvider",
    "get_ai_provider",
]
