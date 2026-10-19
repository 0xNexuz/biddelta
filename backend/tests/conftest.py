import pytest
import pymupdf
from biddelta.documents import extract_document
from biddelta.engine import Engine
from biddelta.models import Requirement, ResponseItem
from biddelta.store import Store


def pdf_bytes(text="Deadline 10 October. Deliver 10 units."):
    with pymupdf.open() as pdf:
        page = pdf.new_page()
        if text:
            page.insert_text((72, 72), text)
        return pdf.tobytes()


def document(source_id, kind, content=None, **kwargs):
    content = content if content is not None else pdf_bytes()
    return extract_document(content, source_id=source_id, kind=kind, **kwargs), content


def make_packet(engine, evidence_status="asserted"):
    tender = document("tender", "tender")
    response = document("response", "response")
    register = document("register", "evidence_register",
                        f"evidence_id,status,note\ne1,{evidence_status},Owner assertion\n".encode())
    reqs = [Requirement(id=f"r{i}", text=f"Requirement {i}",
                        source_span_ids=[tender[0].spans[0].id]) for i in (1, 2)]
    items = [ResponseItem(id=f"i{i}", text=f"Claim {i}",
                          source_span_ids=[response[0].spans[0].id],
                          requirement_ids=[f"r{i}"], evidence_ids=["e1"] if i == 1 else [])
             for i in (1, 2)]
    return engine.create("owner", [tender, response, register], reqs, items)


def amendment(engine, packet, req_ids=None, source="amendment-1", content=None, **kwargs):
    doc, content = document(source, "amendment", content, **kwargs)
    changes = [] if req_ids is None else [{"source_span_id": doc.spans[0].id,
               "description": "Deadline changed", "requirement_ids": req_ids}]
    return engine.amend(packet.id, "owner", packet.revision, doc, content, changes)


def approve_all(engine, packet):
    packet = engine.confirm_scope(packet.id, "owner", packet.revision,
                                  "Reviewed full document inventory and all response scope")
    for item in packet.items:
        packet = engine.approve(packet.id, "owner", packet.revision, item.id,
                                "Reviewed claim and current evidence")
    return packet


@pytest.fixture
def engine(tmp_path):
    return Engine(Store(tmp_path / "packet.sqlite3"))


@pytest.fixture
def approved(engine):
    return approve_all(engine, make_packet(engine))
