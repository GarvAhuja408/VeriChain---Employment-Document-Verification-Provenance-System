"""
Extracts plain text from uploaded files (.txt, .docx, .pdf).
"""

import io
from pypdf import PdfReader
from docx import Document


def extract_text(filename: str, file_bytes: bytes) -> str:
    lower = filename.lower()

    if lower.endswith(".txt"):
        return file_bytes.decode("utf-8", errors="ignore")

    if lower.endswith(".docx"):
        doc = Document(io.BytesIO(file_bytes))
        return "\n".join(p.text for p in doc.paragraphs)

    if lower.endswith(".pdf"):
        reader = PdfReader(io.BytesIO(file_bytes))
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        return text

    raise ValueError(f"Unsupported file type: {filename}")
