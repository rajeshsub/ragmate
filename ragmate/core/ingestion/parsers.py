"""Extract plain text from supported document formats."""

from pathlib import Path

SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".md", ".docx"}


def parse_document(path: Path) -> str:
    ext = path.suffix.lower()
    if ext == ".pdf":
        return _parse_pdf(path)
    if ext in {".txt", ".md"}:
        return path.read_text(encoding="utf-8", errors="replace")
    if ext == ".docx":
        return _parse_docx(path)
    raise ValueError(f"Unsupported file type: {ext}")


def _parse_pdf(path: Path) -> str:
    from pypdf import PdfReader

    reader = PdfReader(str(path))
    text = "\n".join(page.extract_text() or "" for page in reader.pages)
    if len(text.strip()) < 100:
        raise ValueError(
            "PDF appears to be scanned or image-based (no extractable text found). "
            "Only text-based PDFs are supported."
        )
    return text


def _parse_docx(path: Path) -> str:
    from docx import Document

    doc = Document(str(path))
    return "\n".join(para.text for para in doc.paragraphs)
