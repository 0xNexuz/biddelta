"""Explicit packet contracts. IDs and revisions are never reused."""
from enum import StrEnum
from typing import Literal
from uuid import uuid4
from datetime import datetime, timezone
from pydantic import BaseModel, ConfigDict, Field


def new_id() -> str:
    return str(uuid4())


class Record(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ApprovalState(StrEnum):
    UNREVIEWED = "unreviewed"
    APPROVED = "approved"
    NEEDS_SCOPE = "needs_scope_confirmation"
    STALE = "stale"


class SourceSpan(Record):
    id: str = Field(default_factory=new_id)
    document_version_id: str
    page: int = Field(ge=1)
    start: int = Field(ge=0)
    end: int = Field(gt=0)
    quote: str = Field(min_length=1)


class DocumentVersion(Record):
    id: str = Field(default_factory=new_id)
    source_id: str
    version: int = Field(ge=1)
    supersedes_id: str | None = None
    kind: Literal["tender", "amendment", "response", "evidence_register"]
    sha256: str
    byte_size: int
    pages: list[str]
    spans: list[SourceSpan]
    extraction_gaps: list[int] = Field(default_factory=list)


class Requirement(Record):
    id: str
    text: str
    source_span_ids: list[str] = Field(min_length=1)


class EvidenceRevision(Record):
    id: str = Field(default_factory=new_id)
    evidence_id: str
    revision: int
    source_span_id: str
    status: Literal["missing", "conflict", "asserted"]
    note: str


class ResponseItem(Record):
    id: str
    text: str
    source_span_ids: list[str] = Field(min_length=1)
    requirement_ids: list[str] = Field(min_length=1)
    evidence_ids: list[str] = Field(default_factory=list)
    approval_state: ApprovalState = ApprovalState.UNREVIEWED
    approved_revision: int | None = None


class ChangeEvent(Record):
    id: str = Field(default_factory=new_id)
    revision: int
    document_version_id: str
    source_span_id: str
    description: str
    requirement_ids: list[str]
    reviewed: bool = False


class ImpactLink(Record):
    change_id: str
    response_item_id: str
    disposition: Literal["affected", "unaffected"]
    decision_id: str


class AnalysisRun(Record):
    id: str = Field(default_factory=new_id)
    revision: int
    model: str
    status: Literal["proposed", "failed"]
    note: str
    # No field can confer review authority or mark review complete.


class ReviewDecision(Record):
    id: str = Field(default_factory=new_id)
    actor: str
    revision: int
    action: Literal["impact", "scope", "approve", "evidence"]
    target_id: str
    rationale: str = Field(min_length=1)


class AuditEvent(Record):
    id: str = Field(default_factory=new_id)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    actor: str
    revision: int
    action: str
    target_id: str


class ExportGate(Record):
    packet_id: str
    revision: int
    allowed: bool
    blockers: list[str]
    disclaimer: str = "Reviewed state only; not legal compliance or proof of completeness."


class Packet(Record):
    id: str = Field(default_factory=new_id)
    owner_id: str
    revision: int = 1
    scope_confirmed_revision: int = 0
    documents: list[DocumentVersion] = Field(default_factory=list)
    requirements: list[Requirement] = Field(default_factory=list)
    items: list[ResponseItem] = Field(default_factory=list)
    evidence: list[EvidenceRevision] = Field(default_factory=list)
    changes: list[ChangeEvent] = Field(default_factory=list)
    impacts: list[ImpactLink] = Field(default_factory=list)
    analyses: list[AnalysisRun] = Field(default_factory=list)
    decisions: list[ReviewDecision] = Field(default_factory=list)
    audit: list[AuditEvent] = Field(default_factory=list)
