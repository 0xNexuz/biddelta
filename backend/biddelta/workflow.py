"""Offline upload contracts and human page mappings. No semantic inference."""
import base64
import binascii
import csv
from typing import Literal
from pydantic import Field
from .documents import extract_document, MAX_FILE_BYTES
from .models import Record, Requirement, ResponseItem


class Upload(Record):
    kind: Literal['tender', 'response', 'evidence_register', 'amendment']
    content_base64: str = Field(max_length=4 * ((MAX_FILE_BYTES + 2) // 3))

    def extract(self):
        try:
            content = base64.b64decode(self.content_base64, validate=True)
            doc = extract_document(content, source_id=self.kind, kind=self.kind)
            return doc, content
        except (ValueError, binascii.Error, RuntimeError, csv.Error) as exc:
            raise ValueError('Invalid PDF/CSV upload or unsupported file bounds') from exc


class Preview(Record):
    uploads: list[Upload] = Field(min_length=1, max_length=3)


class ItemMapping(Record):
    page: int = Field(ge=1)
    requirement_pages: list[int] = Field(min_length=1, max_length=60)
    evidence_ids: list[str] = Field(max_length=1000)


class CreatePacket(Preview):
    mappings: list[ItemMapping] = Field(min_length=1, max_length=60)


def create_packet(engine, actor, body):
    documents = [u.extract() for u in body.uploads]
    by_kind = {doc.kind: doc for doc, _ in documents}
    if len(documents) != 3 or set(by_kind) != {'tender', 'response', 'evidence_register'}:
        raise ValueError('Upload exactly one tender PDF, response PDF and evidence CSV')
    tender, response = by_kind['tender'], by_kind['response']
    requirements = [Requirement(id=f'r-{s.page}', text=s.quote, source_span_ids=[s.id]) for s in tender.spans]
    spans = {s.page: s for s in response.spans}
    if len({m.page for m in body.mappings}) != len(body.mappings) or {m.page for m in body.mappings} != set(spans):
        raise ValueError('Map every readable response page exactly once')
    if any(not set(m.requirement_pages) <= {s.page for s in tender.spans} for m in body.mappings):
        raise ValueError('Unknown tender page')
    items = [ResponseItem(id=f'i-{m.page}', text=spans[m.page].quote,
                          source_span_ids=[spans[m.page].id],
                          requirement_ids=[f'r-{n}' for n in m.requirement_pages],
                          evidence_ids=m.evidence_ids) for m in body.mappings]
    return engine.create(actor, documents, requirements, items)


class Decision(Record):
    expected_revision: int = Field(ge=1)
    rationale: str = Field(min_length=1, max_length=4000, pattern=r'\S')


class ImpactDecision(Decision):
    affected_item_ids: list[str] = Field(max_length=60)


class ChangeDraft(Record):
    page: int = Field(ge=1)
    description: str = Field(min_length=1, max_length=8000, pattern=r'\S')
    requirement_ids: list[str] = Field(max_length=60)


class Amendment(Record):
    expected_revision: int = Field(ge=1)
    upload: Upload
    changes: list[ChangeDraft] = Field(max_length=120)


def add_amendment(engine, packet_id, actor, body):
    # Authenticate before parsing bytes; source identity is server-generated.
    packet = engine.store.get(packet_id, actor)
    if packet.revision != body.expected_revision:
        raise ValueError('Stale packet revision')
    if body.upload.kind != 'amendment':
        raise ValueError('Amendment PDF required')
    doc, content = body.upload.extract()
    doc.source_id = f'amendment-{doc.id}'
    spans = {s.page: s.id for s in doc.spans}
    if any(c.page not in spans for c in body.changes):
        raise ValueError('Change must cite a readable amendment page')
    changes = [dict(source_span_id=spans[c.page], description=c.description,
                    requirement_ids=c.requirement_ids) for c in body.changes]
    return engine.amend(packet_id, actor, body.expected_revision, doc, content, changes)
