import sqlite3
import pytest
from biddelta.engine import Engine
from biddelta.models import ApprovalState
from biddelta.store import Store
from conftest import amendment, approve_all, document, make_packet, pdf_bytes


def states(p):
    return {i.id: i.approval_state for i in p.items}


def test_revision_creation_preserves_original_bytes(engine, approved):
    original = approved.documents[0]
    before = engine.store.source_bytes(approved.id, original.id, "owner")
    p = amendment(engine, approved, ["r1"])
    assert p.revision == 2
    assert len(p.documents) == 4
    assert p.documents[:3] == approved.documents
    assert engine.store.source_bytes(p.id, original.id, "owner") == before
    assert engine.store.get(p.id, "owner") == p


def test_dependent_approval_expires_and_unaffected_waits_for_scope(engine, approved):
    p = amendment(engine, approved, ["r1"])
    assert states(p) == {"i1": ApprovalState.STALE, "i2": ApprovalState.NEEDS_SCOPE}
    assert p.items[0].approved_revision == 1
    p = engine.review_impact(p.id, "owner", 2, p.changes[0].id, ["i1"], "Deadline affects i1 only")
    assert not engine.gate(p.id, "owner").allowed
    p = engine.confirm_scope(p.id, "owner", 2, "Full packet reviewed, i2 unchanged")
    assert states(p) == {"i1": ApprovalState.STALE, "i2": ApprovalState.APPROVED}
    assert p.items[1].approved_revision == 2
    assert "approval_required:i1" in engine.gate(p.id, "owner").blockers
    p = engine.approve(p.id, "owner", 2, "i1", "Fresh review against deadline amendment")
    assert engine.gate(p.id, "owner").allowed
    assert len([d for d in p.decisions if d.action == "approve" and d.target_id == "i2"]) == 1


def test_missing_impact_blocks_scope_approval_and_export(engine, approved):
    p = amendment(engine, approved, ["r1"])
    assert "missing_impact_review" in engine.gate(p.id, "owner").blockers
    with pytest.raises(ValueError, match="Missing impact"):
        engine.confirm_scope(p.id, "owner", 2, "Skip review")
    with pytest.raises(ValueError, match="Scope and impact"):
        engine.approve(p.id, "owner", 2, "i1", "Skip review")
    assert engine.store.get(p.id, "owner") == p


def test_stale_approval_request_rejected(engine, approved):
    p = amendment(engine, approved, ["r1"])
    with pytest.raises(ValueError, match="Stale packet revision"):
        engine.approve(p.id, "owner", 1, "i1", "Old browser revision")
    assert engine.store.get(p.id, "owner") == p
    assert not engine.gate(p.id, "owner").allowed


def test_known_dependency_cannot_be_reviewed_as_no_impact(engine, approved):
    p = amendment(engine, approved, ["r1"])
    with pytest.raises(ValueError, match="cannot be declared unaffected"):
        engine.review_impact(p.id, "owner", 2, p.changes[0].id, [], "No impact")
    assert not engine.store.get(p.id, "owner").changes[0].reviewed


def test_zero_change_amendment_still_requires_scope_confirmation(engine, approved):
    p = amendment(engine, approved)
    assert all(i.approval_state == ApprovalState.NEEDS_SCOPE for i in p.items)
    assert not engine.gate(p.id, "owner").allowed
    p = engine.confirm_scope(p.id, "owner", 2, "Reviewed source; no changes or missed impacts")
    assert engine.gate(p.id, "owner").allowed
    assert all(i.approved_revision == 2 for i in p.items)


def test_audit_and_reviews_survive_reopen_and_sql_updates_rejected(engine, approved):
    p = amendment(engine, approved, ["r1"])
    p = engine.review_impact(p.id, "owner", 2, p.changes[0].id, ["i1"], "Affected")
    p = engine.confirm_scope(p.id, "owner", 2, "Inventory checked")
    p = engine.approve(p.id, "owner", 2, "i1", "Rechecked")
    reopened = Engine(Store(engine.store.path))
    saved = reopened.store.get(p.id, "owner")
    assert saved.audit[:len(approved.audit)] == approved.audit
    assert saved.decisions[:len(approved.decisions)] == approved.decisions
    assert [d.revision for d in saved.decisions if d.action == "approve" and d.target_id == "i1"] == [1, 2]
    with reopened.store.connect() as db:
        assert db.execute('SELECT count(*) FROM snapshots').fetchone()[0] == len(saved.audit)
        with pytest.raises(sqlite3.IntegrityError, match="immutable"):
            db.execute('UPDATE snapshots SET body=?', ('{}',))
        with pytest.raises(sqlite3.IntegrityError, match="immutable"):
            db.execute('DELETE FROM sources')


@pytest.mark.parametrize("status", ["missing", "conflict"])
def test_unresolved_evidence_prevents_completion(engine, status):
    p = make_packet(engine, status)
    p = engine.confirm_scope(p.id, "owner", 1, "Scope reviewed")
    with pytest.raises(ValueError, match="Unresolved evidence"):
        engine.approve(p.id, "owner", 1, "i1", "Unsupported completion")
    assert "unresolved_evidence:e1" in engine.gate(p.id, "owner").blockers
    assert not engine.gate(p.id, "owner").allowed


def test_evidence_revisions_preserve_history_and_require_recheck(engine, approved):
    old = approved.evidence[0]
    p = engine.revise_evidence(approved.id, "owner", 1, "e1", "missing", "Withdrawn",
                               old.source_span_id, "Owner withdrew evidence assertion")
    assert len(p.evidence) == 2 and p.evidence[0] == old
    assert p.evidence[-1].revision == 2
    assert states(p) == {"i1": ApprovalState.STALE, "i2": ApprovalState.NEEDS_SCOPE}
    p = engine.revise_evidence(p.id, "owner", 2, "e1", "asserted", "Owner reconfirmed",
                               old.source_span_id, "Owner supplied correction note")
    assert p.revision == 3
    p = approve_all(engine, p)
    assert engine.gate(p.id, "owner").allowed
    assert len(p.evidence) == 3


def test_second_amendment_cannot_restore_earlier_stale_approval(engine, approved):
    p = amendment(engine, approved, ["r1"])
    p = amendment(engine, p, ["r2"], source="amendment-2")
    for c, affected in zip(p.changes, (["i1"], ["i2"])):
        p = engine.review_impact(p.id, "owner", 3, c.id, affected, "Reviewed dependency")
    p = engine.confirm_scope(p.id, "owner", 3, "Both amendments fully reviewed")
    assert all(i.approval_state == ApprovalState.STALE for i in p.items)
    assert not engine.gate(p.id, "owner").allowed


def test_source_version_chain_preserved(engine, approved):
    p = amendment(engine, approved)
    first = p.documents[-1]
    p = amendment(engine, p, source=first.source_id, version=2, supersedes_id=first.id)
    assert p.documents[-1].supersedes_id == first.id
    assert p.documents[-1].version == 2


def test_invalid_mutation_rolls_back_bytes_and_revision(engine, approved):
    doc, content = document("amendment", "amendment")
    with pytest.raises(ValueError, match="Unknown change"):
        engine.amend(approved.id, "owner", 1, doc, content,
                     [{"source_span_id": doc.spans[0].id, "description": "Bad ref", "requirement_ids": ["unknown"]}])
    assert engine.store.get(approved.id, "owner") == approved
    with pytest.raises(KeyError):
        engine.store.source_bytes(approved.id, doc.id, "owner")


def test_foreign_owner_rejected(engine, approved):
    with pytest.raises(PermissionError):
        engine.gate(approved.id, "intruder")
    with pytest.raises(PermissionError):
        engine.confirm_scope(approved.id, "intruder", 1, "Forged authority")
    with pytest.raises(PermissionError):
        engine.store.source_bytes(approved.id, approved.documents[0].id, "intruder")


def test_extraction_gap_is_never_complete(engine, approved):
    p = amendment(engine, approved, content=pdf_bytes(""))
    assert p.documents[-1].extraction_gaps == [1]
    with pytest.raises(ValueError, match="extraction gaps"):
        engine.confirm_scope(p.id, "owner", 2, "Cannot ignore blank page")
    assert "extraction_gaps" in engine.gate(p.id, "owner").blockers


def test_forged_source_span_rejected(engine, approved):
    doc, content = document("amendment", "amendment")
    doc.spans[0].quote = "Fabricated quote"
    with pytest.raises(ValueError, match="Invalid source span"):
        engine.amend(approved.id, "owner", 1, doc, content, [])


def test_duplicate_review_cannot_rewrite_history(engine, approved):
    p = amendment(engine, approved, ["r1"])
    c = p.changes[0]
    p = engine.review_impact(p.id, "owner", 2, c.id, ["i1"], "Reviewed")
    with pytest.raises(ValueError, match="already reviewed"):
        engine.review_impact(p.id, "owner", 2, c.id, ["i1", "i2"], "Overwrite")
    assert engine.store.get(p.id, "owner") == p


def test_packet_file_bounds_enforced(engine, approved):
    p = amendment(engine, approved)
    p = amendment(engine, p, source="amendment-2")
    with pytest.raises(ValueError, match="bounds"):
        amendment(engine, p, source="amendment-3")
    assert engine.store.get(p.id, "owner") == p


def test_duplicate_span_cannot_alias_historical_source(engine, approved):
    doc, content = document("new-amendment", "amendment")
    doc.spans[0].id = approved.documents[0].spans[0].id
    with pytest.raises(ValueError, match="Duplicate source span"):
        engine.amend(approved.id, "owner", 1, doc, content, [])


def test_evidence_revision_cannot_point_at_csv_header(engine, approved):
    header = approved.documents[2].spans[0].id
    with pytest.raises(ValueError, match="Unknown evidence"):
        engine.revise_evidence(approved.id, "owner", 1, "e1", "asserted", "Bad link", header, "Invalid provenance")
    assert engine.store.get(approved.id, "owner") == approved
