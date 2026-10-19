import pytest
from biddelta.documents import MAX_FILE_BYTES, extract_document
from conftest import document, pdf_bytes


def test_pdf_spans_match_extracted_page():
    doc, _ = document("tender", "tender")
    assert doc.spans[0].quote == doc.pages[0]
    assert doc.spans[0].document_version_id == doc.id
    assert not doc.extraction_gaps


@pytest.mark.parametrize("content", [b"", b"x" * (MAX_FILE_BYTES + 1)], ids=["empty", "oversize"])
def test_file_size_bounds(content):
    with pytest.raises(ValueError, match="20 MiB"):
        extract_document(content, source_id="x", kind="tender")


@pytest.mark.parametrize("csv", [b"wrong,header\n", b"evidence_id,status,note\ne,done,n\n",
                                b"evidence_id,status,note\ne,missing,n\ne,asserted,n\n"])
def test_invalid_evidence_csv(csv):
    with pytest.raises(ValueError):
        extract_document(csv, source_id="csv", kind="evidence_register")
