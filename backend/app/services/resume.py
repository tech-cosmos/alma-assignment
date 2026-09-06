"""Resume validation: type sniffed from magic bytes (never trusted from the client)."""

import io
import zipfile
from dataclasses import dataclass

PDF_MAGIC = b"%PDF-"
OLE2_MAGIC = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"  # legacy .doc (Compound File Binary)
ZIP_MAGIC = b"PK\x03\x04"  # .docx is an OOXML zip package

MIME_PDF = "application/pdf"
MIME_DOC = "application/msword"
MIME_DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
EXTENSIONS = {MIME_PDF: "pdf", MIME_DOC: "doc", MIME_DOCX: "docx"}


class InvalidResume(ValueError):
    """Raised when an uploaded resume is not an accepted document."""


@dataclass(frozen=True, slots=True)
class ResumeUpload:
    filename: str
    content_type: str  # detected, not client-supplied
    data: bytes

    @property
    def extension(self) -> str:
        return EXTENSIONS[self.content_type]


def detect_type(data: bytes) -> str | None:
    if data.startswith(PDF_MAGIC):
        return MIME_PDF
    if data.startswith(OLE2_MAGIC):
        return MIME_DOC
    if data.startswith(ZIP_MAGIC) and _is_docx(data):
        return MIME_DOCX
    return None


def _is_docx(data: bytes) -> bool:
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            return "word/document.xml" in zf.namelist()
    except zipfile.BadZipFile:
        return False


def validate_resume(filename: str | None, data: bytes, *, max_bytes: int) -> ResumeUpload:
    if not data:
        raise InvalidResume("Resume file is empty.")
    if len(data) > max_bytes:
        raise InvalidResume(f"Resume exceeds the {max_bytes // (1024 * 1024)} MB limit.")
    content_type = detect_type(data)
    if content_type is None:
        raise InvalidResume("Resume must be a PDF, DOC, or DOCX file.")
    name = (filename or "").strip() or f"resume.{EXTENSIONS[content_type]}"
    return ResumeUpload(filename=name[:255], content_type=content_type, data=data)
