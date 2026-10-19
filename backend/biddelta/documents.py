"""Bounded text PDF / UTF-8 CSV extraction; no OCR or network fetches."""
import csv
import hashlib
import io
import pymupdf
from .models import DocumentVersion, SourceSpan

MAX_FILE_BYTES = 20 * 1024 * 1024
MAX_PACKET_BYTES = 50 * 1024 * 1024


def extract_document(content: bytes, *, source_id: str, kind: str,
                     version: int = 1, supersedes_id: str | None = None) -> DocumentVersion:
    if not source_id.strip() or not 0 < len(content) <= MAX_FILE_BYTES:
        raise ValueError("Source identity and nonempty file up to 20 MiB required")
    if kind == "evidence_register":
        rows = list(csv.reader(io.StringIO(content.decode("utf-8-sig")), strict=True))
        if not rows or rows[0] != ["evidence_id", "status", "note"]:
            raise ValueError("CSV header must be evidence_id,status,note")
        if any(len(row) != 3 for row in rows[1:]):
            raise ValueError("Invalid CSV row")
        if len({row[0] for row in rows[1:]}) != len(rows) - 1:
            raise ValueError("Duplicate evidence identity")
        if any(not row[0].strip() or row[1] not in {"missing", "conflict", "asserted"} for row in rows[1:]):
            raise ValueError("Invalid evidence identity/status")
        pages = [",".join(row) for row in rows]
        gaps = []
    else:
        with pymupdf.open(stream=content, filetype="pdf") as pdf:
            if pdf.needs_pass or not 0 < len(pdf) <= 60:
                raise ValueError("Encrypted, empty, or oversized PDF unsupported")
            pages = [page.get_text() for page in pdf]
        gaps = [n for n, text in enumerate(pages, 1) if not text.strip()]
    doc = DocumentVersion(source_id=source_id, version=version,
                          supersedes_id=supersedes_id, kind=kind,
                          sha256=hashlib.sha256(content).hexdigest(), byte_size=len(content),
                          pages=pages, spans=[], extraction_gaps=gaps)
    doc.spans = [SourceSpan(document_version_id=doc.id, page=n, start=0,
                            end=len(text), quote=text)
                 for n, text in enumerate(pages, 1) if text.strip()]
    return doc
