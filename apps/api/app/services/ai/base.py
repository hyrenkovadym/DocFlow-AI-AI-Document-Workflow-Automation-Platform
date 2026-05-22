from abc import ABC, abstractmethod

from app.services.ai.schemas import DocumentClassification, ExtractedFields


class AIProviderError(RuntimeError):
    """Base error for AI provider failures."""


class AIProviderConfigurationError(AIProviderError):
    """Raised when provider settings are invalid or missing."""


class AIProviderResponseError(AIProviderError):
    """Raised when provider response cannot be parsed/validated."""


class AIProvider(ABC):
    @abstractmethod
    def classify_document(self, text: str) -> DocumentClassification:
        raise NotImplementedError

    @abstractmethod
    def extract_fields(self, text: str, document_type: str) -> ExtractedFields:
        raise NotImplementedError
