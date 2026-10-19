"""Human review authority and deterministic gates; no AI calls or assertions."""
from .documents import extract_document, MAX_PACKET_BYTES
from .models import (ApprovalState, AuditEvent, ChangeEvent, DocumentVersion,
                     EvidenceRevision, ExportGate, ImpactLink, Packet,
                     Requirement, ResponseItem, ReviewDecision)
from .store import Store


class Engine:
    def __init__(self, store: Store):
        self.store = store

    @staticmethod
    def _audit(p, actor, action, target):
        p.audit.append(AuditEvent(actor=actor, revision=p.revision, action=action, target_id=target))

    def _decision(self, p, actor, action, target, rationale):
        decision = ReviewDecision(actor=actor, revision=p.revision, action=action,
                                  target_id=target, rationale=rationale)
        p.decisions.append(decision)
        self._audit(p, actor, action, target)
        return decision

    @staticmethod
    def _find(records, identity):
        for record in records:
            if record.id == identity:
                return record
        raise ValueError(f"Unknown reference: {identity}")

    @staticmethod
    def _check_document(doc: DocumentVersion, content: bytes):
        actual = extract_document(content, source_id=doc.source_id, kind=doc.kind,
                                  version=doc.version, supersedes_id=doc.supersedes_id)
        if (actual.sha256, actual.pages, actual.byte_size, actual.extraction_gaps) != (
                doc.sha256, doc.pages, doc.byte_size, doc.extraction_gaps):
            raise ValueError("Document metadata does not match source bytes")
        for span in doc.spans:
            if (span.document_version_id != doc.id or span.page > len(doc.pages)
                    or span.start >= span.end or span.end > len(doc.pages[span.page - 1])
                    or doc.pages[span.page - 1][span.start:span.end] != span.quote):
                raise ValueError("Invalid source span")

    @staticmethod
    def _limits(docs):
        # Historical source versions count toward storage/page bounds.
        if (len(docs) > 5 or sum(d.byte_size for d in docs) > MAX_PACKET_BYTES
                or sum(len(d.pages) for d in docs if d.kind != "evidence_register") > 60
                or sum(d.kind == "amendment" for d in docs) > 2):
            raise ValueError("Packet bounds exceeded")

    def create(self, actor: str, documents: list[tuple[DocumentVersion, bytes]],
               requirements: list[Requirement], items: list[ResponseItem]) -> Packet:
        if not actor.strip() or not requirements or not items:
            raise ValueError("Owner, requirements and response items required")
        docs = [d for d, _ in documents]
        self._limits(docs)
        if (any(d.kind == "amendment" or d.version != 1 or d.supersedes_id for d in docs)
                or sum(d.kind == "tender" for d in docs) != 1
                or sum(d.kind == "response" for d in docs) != 1
                or sum(d.kind == "evidence_register" for d in docs) != 1
                or len(docs) != 3):
            raise ValueError("Initial packet requires tender, response, evidence CSV")
        for doc, content in documents:
            self._check_document(doc, content)
        for ids in ([d.id for d in docs], [d.source_id for d in docs],
                    [s.id for d in docs for s in d.spans], [r.id for r in requirements],
                    [i.id for i in items]):
            if len(set(ids)) != len(ids):
                raise ValueError("Duplicate identity")
        span_kinds = {s.id: d.kind for d in docs for s in d.spans}
        req_ids = {r.id for r in requirements}
        for req in requirements:
            if any(span_kinds.get(s) != "tender" for s in req.source_span_ids):
                raise ValueError("Requirement needs tender source")
        p = Packet(owner_id=actor, documents=docs, requirements=requirements, items=items)
        csv_doc = next(d for d in docs if d.kind == "evidence_register")
        # Re-read validated CSV to preserve quoted commas in notes.
        import csv, io
        csv_content = next(b for d, b in documents if d.id == csv_doc.id)
        rows = list(csv.reader(io.StringIO(csv_content.decode("utf-8-sig"))))
        for n, row in enumerate(rows[1:], 2):
            span = next(s for s in csv_doc.spans if s.page == n)
            p.evidence.append(EvidenceRevision(evidence_id=row[0], revision=1,
                              source_span_id=span.id, status=row[1], note=row[2]))
        evidence_ids = {e.evidence_id for e in p.evidence}
        for item in items:
            if (item.approval_state != ApprovalState.UNREVIEWED or item.approved_revision is not None
                    or not set(item.requirement_ids) <= req_ids
                    or not set(item.evidence_ids) <= evidence_ids
                    or any(span_kinds.get(s) != "response" for s in item.source_span_ids)):
                raise ValueError("Invalid response dependencies or pre-approved item")
        self._audit(p, actor, "create", p.id)
        with self.store.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            db.execute('INSERT INTO snapshots VALUES (?,?,?)', (p.id, 1, p.model_dump_json()))
            db.executemany('INSERT INTO sources VALUES (?,?,?)',
                           [(p.id, d.id, b) for d, b in documents])
        return p

    def amend(self, packet_id: str, actor: str, expected_revision: int,
              document: DocumentVersion, content: bytes,
              changes: list[dict]) -> Packet:
        """Changes are proposed inventory; impact/scope remain human decisions."""
        self._check_document(document, content)
        with self.store.edit(packet_id, actor, expected_revision) as (db, p):
            if document.kind != "amendment" or document.id in {d.id for d in p.documents}:
                raise ValueError("New amendment document required")
            old_span_ids = {s.id for d in p.documents for s in d.spans}
            new_span_ids = [s.id for s in document.spans]
            if len(set(new_span_ids)) != len(new_span_ids) or old_span_ids & set(new_span_ids):
                raise ValueError("Duplicate source span identity")
            previous = [d for d in p.documents if d.source_id == document.source_id]
            if previous:
                last = previous[-1]
                if document.supersedes_id != last.id or document.version != last.version + 1:
                    raise ValueError("Source version chain mismatch")
            elif document.version != 1 or document.supersedes_id:
                raise ValueError("New source must start at version one")
            if previous and previous[-1].kind != "amendment":
                raise ValueError("Amendment cannot replace another document kind")
            self._limits(p.documents + [document])
            p.revision += 1
            known = {r.id for r in p.requirements}
            spans = {s.id for s in document.spans}
            affected = set()
            for draft in changes:
                if set(draft) != {"source_span_id", "description", "requirement_ids"}:
                    raise ValueError("Invalid change draft fields")
                c = ChangeEvent(**draft, revision=p.revision, document_version_id=document.id)
                if c.source_span_id not in spans or not set(c.requirement_ids) <= known:
                    raise ValueError("Unknown change source or dependency")
                p.changes.append(c)
                affected.update(c.requirement_ids)
            for item in p.items:
                if set(item.requirement_ids) & affected:
                    item.approval_state = ApprovalState.STALE
                elif item.approval_state == ApprovalState.APPROVED:
                    item.approval_state = ApprovalState.NEEDS_SCOPE
            p.documents.append(document)
            self._audit(p, actor, "amendment", document.id)
            db.execute('INSERT INTO sources VALUES (?,?,?)', (p.id, document.id, content))
        return p

    def review_impact(self, packet_id, actor, expected_revision, change_id,
                      affected_item_ids: list[str], rationale: str) -> Packet:
        with self.store.edit(packet_id, actor, expected_revision) as (_, p):
            c = self._find(p.changes, change_id)
            if c.reviewed:
                raise ValueError("Impact already reviewed; preserve original decision")
            affected = set(affected_item_ids)
            known = {i.id for i in p.items}
            required = {i.id for i in p.items if set(i.requirement_ids) & set(c.requirement_ids)}
            if not required <= affected or not affected <= known:
                raise ValueError("Known dependent items cannot be declared unaffected")
            d = self._decision(p, actor, "impact", c.id, rationale)
            for item in p.items:
                disposition = "affected" if item.id in affected else "unaffected"
                p.impacts.append(ImpactLink(change_id=c.id, response_item_id=item.id,
                                            disposition=disposition, decision_id=d.id))
                if item.id in affected:
                    item.approval_state = ApprovalState.STALE
            c.reviewed = True
        return p

    def confirm_scope(self, packet_id, actor, expected_revision, rationale: str) -> Packet:
        """Owner attests complete inventory and reviews all items across amendments."""
        with self.store.edit(packet_id, actor, expected_revision) as (_, p):
            if any(not c.reviewed for c in p.changes):
                raise ValueError("Missing impact review")
            if any(d.extraction_gaps for d in p.documents):
                raise ValueError("Unresolved extraction gaps")
            self._decision(p, actor, "scope", p.id, rationale)
            p.scope_confirmed_revision = p.revision
            for item in p.items:
                if item.approval_state == ApprovalState.NEEDS_SCOPE:
                    item.approval_state = ApprovalState.APPROVED
                    item.approved_revision = p.revision
        return p

    @staticmethod
    def _unresolved(p):
        latest = {e.evidence_id: e for e in p.evidence}
        return [e.evidence_id for e in latest.values() if e.status != "asserted"]

    def approve(self, packet_id, actor, expected_revision, item_id, rationale: str) -> Packet:
        with self.store.edit(packet_id, actor, expected_revision) as (_, p):
            item = self._find(p.items, item_id)
            if p.scope_confirmed_revision != p.revision or any(not c.reviewed for c in p.changes):
                raise ValueError("Scope and impact review required before approval")
            if set(item.evidence_ids) & set(self._unresolved(p)):
                raise ValueError("Unresolved evidence")
            self._decision(p, actor, "approve", item_id, rationale)
            item.approval_state = ApprovalState.APPROVED
            item.approved_revision = p.revision
        return p

    def revise_evidence(self, packet_id, actor, expected_revision, evidence_id,
                        status: str, note: str, source_span_id: str, rationale: str) -> Packet:
        """Explicit owner assertion, not authenticated evidence. History remains."""
        with self.store.edit(packet_id, actor, expected_revision) as (_, p):
            revisions = [e for e in p.evidence if e.evidence_id == evidence_id]
            spans = {s.id for d in p.documents if d.kind == "evidence_register" for s in d.spans}
            if (not revisions or source_span_id not in spans
                    or source_span_id not in {e.source_span_id for e in revisions}):
                raise ValueError("Unknown evidence or register source")
            p.revision += 1
            p.evidence.append(EvidenceRevision(evidence_id=evidence_id,
                              revision=revisions[-1].revision + 1, status=status,
                              source_span_id=source_span_id, note=note))
            for item in p.items:
                if evidence_id in item.evidence_ids:
                    item.approval_state = ApprovalState.STALE
                elif item.approval_state == ApprovalState.APPROVED:
                    item.approval_state = ApprovalState.NEEDS_SCOPE
            self._decision(p, actor, "evidence", evidence_id, rationale)
        return p

    def gate(self, packet_id, actor) -> ExportGate:
        return self.gate_for_packet(self.store.get(packet_id, actor))

    @staticmethod
    def gate_for_packet(p: Packet) -> ExportGate:
        blockers = []
        if p.scope_confirmed_revision != p.revision:
            blockers.append("scope_confirmation_required")
        if any(not c.reviewed for c in p.changes):
            blockers.append("missing_impact_review")
        if any(d.extraction_gaps for d in p.documents):
            blockers.append("extraction_gaps")
        blockers.extend(f"unresolved_evidence:{e}" for e in Engine._unresolved(p))
        blockers.extend(f"approval_required:{i.id}" for i in p.items
                        if i.approval_state != ApprovalState.APPROVED or i.approved_revision != p.revision)
        return ExportGate(packet_id=p.id, revision=p.revision, allowed=not blockers, blockers=blockers)
