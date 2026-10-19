"""Public synthetic local examples, generated offline. No model output."""
import pymupdf


def fixture(name: str) -> tuple[bytes, str]:
    if name == 'evidence.csv':
        return b'evidence_id,status,note\ne1,asserted,Synthetic owner assertion only\n', 'text/csv'
    texts = {
        'tender.pdf': ['SYNTHETIC TENDER: deadline 20 October.', 'SYNTHETIC TENDER: deliver 10 units.'],
        'response.pdf': ['SYNTHETIC RESPONSE: we plan delivery by 20 October.', 'SYNTHETIC RESPONSE: we offer 10 units.'],
        'amendment.pdf': ['SYNTHETIC AMENDMENT: deadline changes to 25 October.'],
    }
    if name not in texts:
        raise KeyError(name)
    with pymupdf.open() as pdf:
        for text in texts[name]:
            pdf.new_page().insert_text((72, 72), text)
        return pdf.tobytes(), 'application/pdf'
