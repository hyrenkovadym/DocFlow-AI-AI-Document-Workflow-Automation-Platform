import json
import re
from abc import ABC, abstractmethod

import httpx

from app.core.config import get_settings
from app.models.enums import DocumentType
from app.schemas.extraction import DocumentClassification, ExtractedFields


class AIProvider(ABC):
    @abstractmethod
    def classify_document(self, text: str) -> DocumentClassification:
        raise NotImplementedError

    @abstractmethod
    def extract_fields(self, text: str, document_type: str) -> ExtractedFields:
        raise NotImplementedError


class MockAIProvider(AIProvider):
    def classify_document(self, text: str) -> DocumentClassification:
        lowered = text.lower()
        if "invoice" in lowered:
            dtype = DocumentType.INVOICE
        elif "contract" in lowered or "agreement" in lowered:
            dtype = DocumentType.CONTRACT
        elif "request" in lowered:
            dtype = DocumentType.REQUEST
        elif "report" in lowered:
            dtype = DocumentType.REPORT
        else:
            dtype = DocumentType.UNKNOWN

        confidence = 0.88 if dtype != DocumentType.UNKNOWN else 0.55
        return DocumentClassification(
            document_type=dtype,
            confidence_score=confidence,
            reasoning="Keyword-based mock classifier",
        )

    def extract_fields(self, text: str, document_type: str) -> ExtractedFields:
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        title = lines[0][:120] if lines else "Untitled document"
        summary = " ".join(lines[:5])[:500] if lines else "No text extracted"

        date_matches = re.findall(r"\b\d{4}-\d{2}-\d{2}\b", text)
        amount_match = re.search(r"\$\s?\d+(?:,\d{3})*(?:\.\d{2})?", text)

        lowered = text.lower()
        priority = "high" if any(token in lowered for token in ["urgent", "asap", "immediately"]) else "normal"
        recommended_action = "review_financials" if document_type == DocumentType.INVOICE.value else "review_content"

        confidence = 0.81 if document_type != DocumentType.UNKNOWN.value else 0.61

        return ExtractedFields(
            document_type=DocumentType(document_type),
            title=title,
            summary=summary,
            dates=date_matches[:10],
            people_or_companies=[],
            amount=amount_match.group(0) if amount_match else None,
            priority=priority,
            recommended_action=recommended_action,
            confidence_score=confidence,
        )


class OpenAICompatibleProvider(AIProvider):
    def __init__(self) -> None:
        settings = get_settings()
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required for OpenAI provider")
        self.base_url = settings.openai_api_base_url.rstrip("/")
        self.api_key = settings.openai_api_key
        self.model = settings.openai_model

    def _chat_json(self, prompt: str) -> dict:
        response = httpx.post(
            f"{self.base_url}/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a document AI assistant. Return strict JSON only.",
                    },
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0,
                "response_format": {"type": "json_object"},
            },
            timeout=90,
        )
        response.raise_for_status()
        data = response.json()
        content = data["choices"][0]["message"]["content"]
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            cleaned = content.strip().replace("```json", "").replace("```", "")
            return json.loads(cleaned)

    def classify_document(self, text: str) -> DocumentClassification:
        prompt = (
            "Classify the document type. "
            "Allowed: invoice, contract, request, report, unknown. "
            "Return JSON with keys: document_type, confidence_score, reasoning.\n\n"
            f"Text:\n{text[:8000]}"
        )
        payload = self._chat_json(prompt)
        return DocumentClassification.model_validate(payload)

    def extract_fields(self, text: str, document_type: str) -> ExtractedFields:
        prompt = (
            "Extract structured fields from this document. "
            "Return JSON with keys: document_type, title, summary, dates, people_or_companies, amount, "
            "priority, recommended_action, confidence_score.\n"
            f"Document type hint: {document_type}\n\nText:\n{text[:12000]}"
        )
        payload = self._chat_json(prompt)
        return ExtractedFields.model_validate(payload)


def get_ai_provider() -> AIProvider:
    settings = get_settings()
    if settings.ai_provider.lower() == "openai":
        return OpenAICompatibleProvider()
    return MockAIProvider()
