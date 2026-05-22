from __future__ import annotations

import json
from time import sleep

import httpx
from pydantic import ValidationError

from app.core.config import Settings, get_settings
from app.services.ai.base import AIProvider, AIProviderConfigurationError, AIProviderResponseError
from app.services.ai.schemas import DocumentClassification, ExtractedFields


class OpenAICompatibleProvider(AIProvider):
    def __init__(self, settings: Settings | None = None, client: httpx.Client | None = None) -> None:
        self.settings = settings or get_settings()
        if not self.settings.openai_api_key:
            raise AIProviderConfigurationError("OPENAI_API_KEY is required when AI_PROVIDER=openai")

        self.base_url = self.settings.openai_base_url.rstrip("/")
        self.model = self.settings.openai_model
        self.timeout_seconds = max(float(self.settings.openai_timeout_seconds), 1.0)
        self.max_retries = max(int(self.settings.openai_max_retries), 0)
        self._client = client or httpx.Client(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {self.settings.openai_api_key}",
                "Content-Type": "application/json",
            },
            timeout=self.timeout_seconds,
        )

    def classify_document(self, text: str) -> DocumentClassification:
        payload = self._chat_json(self._build_classification_prompt(text))
        try:
            return DocumentClassification.model_validate(payload)
        except ValidationError as exc:
            raise AIProviderResponseError(f"AI classification schema validation failed: {exc}") from exc

    def extract_fields(self, text: str, document_type: str) -> ExtractedFields:
        payload = self._chat_json(self._build_extraction_prompt(text, document_type))
        try:
            return ExtractedFields.model_validate(payload)
        except ValidationError as exc:
            raise AIProviderResponseError(f"AI extraction schema validation failed: {exc}") from exc

    def _chat_json(self, prompt: str) -> dict:
        request_payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are an assistant for business document automation. "
                        "Return strict JSON only, without markdown code fences."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0,
            "response_format": {"type": "json_object"},
        }

        attempts = self.max_retries + 1
        for attempt in range(attempts):
            try:
                response = self._client.post("/chat/completions", json=request_payload)
                if response.status_code in {429, 500, 502, 503, 504} and attempt < self.max_retries:
                    sleep(0.5 * (attempt + 1))
                    continue
                response.raise_for_status()
                return self._extract_json_payload(response)
            except (httpx.TimeoutException, httpx.NetworkError) as exc:
                if attempt < self.max_retries:
                    sleep(0.5 * (attempt + 1))
                    continue
                raise AIProviderResponseError(
                    "OpenAI-compatible request timed out or failed due to network issues"
                ) from exc
            except httpx.HTTPStatusError as exc:
                status_code = exc.response.status_code if exc.response else "unknown"
                raise AIProviderResponseError(
                    f"OpenAI-compatible request failed with status {status_code}"
                ) from exc
            except json.JSONDecodeError as exc:
                raise AIProviderResponseError("AI provider returned invalid JSON output") from exc

        raise AIProviderResponseError("OpenAI-compatible request failed after retries")

    def _extract_json_payload(self, response: httpx.Response) -> dict:
        body = response.json()
        choices = body.get("choices")
        if not isinstance(choices, list) or not choices:
            raise AIProviderResponseError("AI provider response did not include choices")

        first_choice = choices[0]
        content = first_choice.get("message", {}).get("content") if isinstance(first_choice, dict) else None
        if not isinstance(content, str) or not content.strip():
            raise AIProviderResponseError("AI provider response content is empty")

        cleaned = content.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        payload = json.loads(cleaned)
        if not isinstance(payload, dict):
            raise AIProviderResponseError("AI provider JSON output must be an object")
        return payload

    @staticmethod
    def _build_classification_prompt(text: str) -> str:
        return (
            "Classify the document type.\n"
            "Allowed document_type values: invoice, contract, request, report, unknown.\n"
            "Return JSON only with keys: document_type, confidence_score, reasoning.\n"
            "confidence_score must be a number between 0 and 1.\n"
            "Do not invent missing data. Treat output as preliminary automation assistance.\n\n"
            f"Document text:\n{text[:12000]}"
        )

    @staticmethod
    def _build_extraction_prompt(text: str, document_type: str) -> str:
        return (
            "Extract structured fields from the document.\n"
            "Return JSON only with keys:\n"
            "- document_type\n"
            "- title\n"
            "- summary\n"
            "- dates\n"
            "- people_or_companies\n"
            "- amount\n"
            "- priority\n"
            "- recommended_action\n"
            "- confidence_score\n\n"
            "Rules:\n"
            "- Allowed document_type: invoice, contract, request, report, unknown.\n"
            "- Allowed priority: low, medium, high.\n"
            "- confidence_score must be a number between 0 and 1.\n"
            "- Do not invent missing values.\n"
            "- Use null for missing scalar values.\n"
            "- Use empty arrays for missing list values.\n"
            "- Treat output as preliminary automation assistance.\n"
            "- Return JSON only, no extra text.\n\n"
            f"Document type hint: {document_type}\n\n"
            f"Document text:\n{text[:18000]}"
        )
