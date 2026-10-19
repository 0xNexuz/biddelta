# P0-A domain contract and limits

The executable contracts are in backend/biddelta/models.py. This is a local Python
service foundation, with no exposed HTTP mutation endpoints. The only HTTP route
is health. Trusted local callers supply the owner identity; production/session
authentication is not implemented.

| Record | Identity and responsibility |
| --- | --- |
| Packet | Owner, increasing packet revision, latest scope confirmation |
| DocumentVersion | Stable source_id, unique version ID, SHA-256, predecessor and exact stored bytes |
| SourceSpan | Unique ID, document version, 1-based page (CSV record), text offsets and exact quote |
| Requirement | Stable ID, tender-source references |
| ResponseItem | Response-source references, known requirement/evidence dependencies, approval state |
| EvidenceRevision | Stable evidence_id, increasing revision, original CSV assertion link and owner notes |
| ChangeEvent | Amendment source, packet revision, known requirement references and review status |
| ImpactLink | Change-to-item affected/unaffected disposition linked to a review decision |
| AnalysisRun | Proposed/failed AI analysis metadata contract only; no completion authority |
| ReviewDecision | Immutable historical owner decision, target, rationale and packet revision |
| ApprovalState | Unreviewed, approved, needs scope confirmation, stale |
| ExportGate | Current revision's deterministic blockers and disclaimer; no export artifact yet |
| AuditEvent | Actor, revision, action, target, timestamp |

Initial creation requires one tender PDF, response PDF and evidence CSV. CSV schema:
`evidence_id,status,note`; status is missing, conflict or asserted. Assertions are
not authenticated facts. No hidden default of evidence-complete is applied.
Document metadata and span quotes are checked against extraction from original
bytes. Text extraction does not prove correct interpretation, reading order, or
coverage of images. Empty pages remain blocking extraction gaps; no OCR escape.

Every amendment increments packet revision, stores a new document version and
opens scope review even when the proposed change list is empty. Known requirement
dependencies become stale immediately. Other approved items keep their original
approval decision but enter needs-scope state. Each change needs a human disposition
for every response item; known dependency edges cannot be denied. Review may add
additional affected items. All historical unreviewed changes must be reviewed,
including when two amendments arrive before review ends.

After impact review, an owner scope decision attests that the entire inventory and
all response scope were checked. Only needs-scope approvals can carry forward;
stale items require a fresh owner approval at the current revision. Fresh approval
cannot bypass unresolved linked evidence. The export gate independently blocks all
latest missing/conflicting evidence, unreviewed impacts, scope gaps, extraction gaps,
and absent/stale item approvals. An owner can be wrong about semantic scope; these
rules do not prove no dependency was missed.

Evidence correction creates a new packet/evidence revision and invalidates linked
items, preserving prior assertions. In P0-A it is an explicit owner correction note
linked to that evidence's original CSV span, not a replacement upload or external
verification. Changed response text, replacement registers, new requirements,
correction workflows and downloadable exports belong to later work.

SQLite uses serialized write transactions and expected packet revisions. Every
successful command appends an aggregate snapshot containing the complete history.
Original bytes are stored as BLOBs. SQL triggers reject update/delete of snapshots
and sources. This protects normal application operations, not a hostile database
administrator. Database files need private filesystem permissions. Snapshot growth,
malicious PDF resource limits, encryption, retention and hosted isolation require
later work. No multi-user security or production reliability is asserted.
