import io
import zipfile

import httpx

PDF_BYTES = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\n%%EOF\n"
DOC_BYTES = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1" + b"\x00" * 64


def docx_bytes() -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("[Content_Types].xml", "<Types/>")
        zf.writestr("word/document.xml", "<w:document/>")
    return buf.getvalue()


def plain_zip_bytes() -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("notes.txt", "hello")
    return buf.getvalue()


async def create_lead(
    client: httpx.AsyncClient,
    *,
    first_name: str = "Ada",
    last_name: str = "Lovelace",
    email: str = "ada@example.com",
    filename: str = "resume.pdf",
    content: bytes = PDF_BYTES,
    content_type: str = "application/pdf",
) -> httpx.Response:
    return await client.post(
        "/api/v1/leads",
        data={"first_name": first_name, "last_name": last_name, "email": email},
        files={"resume": (filename, content, content_type)},
    )
