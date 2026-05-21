from pathlib import Path

from docx import Document as DocxDocument
from pypdf import PdfReader


class UnsupportedDocumentTypeError(ValueError):
    pass


def extract_text_from_file(file_path: Path, file_type: str) -> str:
    file_type = file_type.lower()
    if file_type == "txt":
        return file_path.read_text(encoding="utf-8", errors="ignore")
    if file_type == "pdf":
        reader = PdfReader(str(file_path))
        return "\n".join((page.extract_text() or "") for page in reader.pages)
    if file_type == "docx":
        doc = DocxDocument(str(file_path))
        return "\n".join(paragraph.text for paragraph in doc.paragraphs)

    raise UnsupportedDocumentTypeError(f"Unsupported file type: {file_type}")
