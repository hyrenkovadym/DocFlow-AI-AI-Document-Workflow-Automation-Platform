import re

from app.models.enums import DocumentType
from app.services.ai.base import AIProvider
from app.services.ai.schemas import DocumentClassification, ExtractedFields


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
        if any(token in lowered for token in ["urgent", "asap", "immediately"]):
            priority = "high"
        elif any(token in lowered for token in ["low priority", "not urgent", "whenever possible"]):
            priority = "low"
        else:
            priority = "medium"

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
