# BidDelta — Project Context

## Identity and authority
Updated: 2026-10-19. Project: BidDelta. Repository: 0xNexuz/biddelta.
Stage: DEVELOPMENT. Current authorization: P0-B slice 1 — offline document upload
and packet review. P0-A deterministic foundation is preserved on GitHub at
66a5192cdeb3d5f923a3ec949d6e90388f09dd15 (PR #1). Its real Nemotron check remains
unverified. P0-B branch: feat/biddelta-p0b-packet-review, based on that exact commit. Discovery,
Strategy and Planning were completed separately in 0xNexuz/mags-skills and are not
repeated here. This file preserves the supplied planning handoff; project-specific
context belongs in this application repository. Read AGENTS.md before changes.

Status vocabulary: APPROVED = user-authorized direction; PLANNED/PROPOSED = not
implemented; IMPLEMENTED = code exists; VERIFIED = actual named execution evidence.
The overall architecture remains PLANNED until implemented and verified. Partial
foundation code does not establish a complete application or hackathon readiness.

## Verified hackathon requirements — inherited planning evidence
Verified in Discovery/Strategy, not re-researched during this milestone:
- Nebius x NVIDIA Global AI Hackathon; selected track direction Best Apps and Agents.
- Deadline 2026-10-30 18:00 Africa/Lagos (17:00 UTC).
- Working application using an NVIDIA open-source model plus Token Factory runtime
  inference or Nebius AI Cloud execution.
- Required description, track, working demo URL, public licensed repository, setup
  instructions, technology feedback, and public YouTube demo under three minutes.
  Explain significant updates to prior work.
- English materials/translations; free judge access through December 15.
- Equally weighted implementation, design, impact, and idea quality.
- Awards: one overall OR one track plus one bonus.
- Eligibility, account access and available credits remain UNVERIFIED.
Sources: https://nebiusglobalaihackathon.devpost.com/rules and
https://nebiusglobalaihackathon.devpost.com/details/faqs

## Approved concept and rationale
BidDelta traces amendment changes into affected response claims, evidence and
approval decisions. Selected for procurement/policy workflow fit, bounded document
processing, reusable evidence controls and meaningful Nemotron use. Customer demand
and reusable source-code assets remain unverified. Commercial competitors exist;
make no uniqueness claim.

Rejected alternative: AccessRepair, due to historical overlap with
AccessPatch/AccessTrace and higher repository-execution/accessibility-verification
complexity.

## MVP boundaries — approved development constraints
One English packet: original tender PDF, up to two amendment PDFs, draft response
PDF, one evidence-register CSV. Five files, 60 PDF pages total. Planning proposed
20 MB/file and 50 MB/packet; P0-A uses explicitly documented binary MiB limits.
Supported change directions: deadline, qualification/evidence, delivery/quantity.
Planned journey: source-linked impact review, missing-evidence requests, correction
notes, selective approval expiration, recheck and reviewed export.

Excluded: OCR, drawings, arbitrary spreadsheets, automatic proposal generation,
legal conclusions, automatic PDF editing, universal portal monitoring, procurement
submission, payments, enterprise collaboration, production deployment, Tavily,
final submission packaging. Do not expand beyond the authorized P0-B slice or run
a full Build Harness audit.

## Technical architecture — PLANNED overall
React/TypeScript frontend; FastAPI API; bounded Python worker; PyMuPDF/CSV
extraction; SQLite and private file storage. Nemotron through Nebius Token Factory
proposes semantic changes and mappings. Deterministic engine controls revisions,
authorization, approval validity, review coverage and export gates. Optional Tavily
retrieval belongs to P2; no sandbox beta dependency.

Core contracts: Packet, DocumentVersion, SourceSpan, Requirement, ResponseItem,
EvidenceRevision, ChangeEvent, ImpactLink, AnalysisRun, ReviewDecision,
ApprovalState, ExportGate and AuditEvent. Export artifacts remain PLANNED.

## Critical deterministic rules
Preserve source bytes, identities, versions and historical approvals. Amendment
arrival blocks reviewed export until review ends. Model completion does not equal
completed review. Every extracted change needs impact/no-impact review. Affected
dependencies require fresh review; stale approval fails. Unaffected approvals need
explicit scope confirmation. Missing evidence, conflicts and extraction gaps remain
unresolved. Evidence-register entries are user assertions, not authenticated facts.
Reviewed export is not legal compliance or proof of completeness.

## Trust and operating boundaries
Local owner mode accepts supported uploads and binds to loopback. Hosted demo is
PLANNED for curated public packets with isolated sessions. Protect provider keys,
review authority, source documents and budget. Documents/model outputs are
untrusted; source references must be validated. Require ownership checks, bounded
retries, safe rendering, file limits, and SSRF controls if retrieval is enabled.
Private hosted uploads require a later security/retention review. Host/operator and
inference provider remain trusted for data handling. P0-A's service actor is supplied
by trusted local Python code; it is not web authentication. P0-B adds a loopback-only HTTP upload/review workflow with opaque HttpOnly,
SameSite=Strict session cookies, server-bound owner identity, trusted host/origin
checks, a custom write-request header, bounded request bodies and private local
SQLite storage. No public hosting is implemented. Sessions are in memory and do
not survive backend restart; persistent session recovery remains unimplemented.

## Testing strategy — PLANNED application acceptance
Prove real Nebius inference, scoped impacts, missing-evidence blocking,
stale-approval rejection, correction/recheck, reproducible export, failure recovery
and session isolation. Evaluation: four development and eight held-out packet
cases; human-reviewed expectations; identical-model single-pass baseline. Report
missed/unsupported impacts, source/scope errors, abstentions, latency and actual
usage. No model evaluation results exist. All deterministic safety invariants must
pass; no critical approval/scope errors permitted on frozen held-out suite. Retain
sanitized traces, versioned inputs, decisions, actual test outputs, adverse results
and clearly labeled demo recordings. Targeted unit/service tests are not this
held-out evaluation or a full security audit.

## Main assumptions and risks
Model/account structured-output and tool support not tested. Suitable permitted
public packet not selected. Builder hours, customer access and expert review not
confirmed. Model can miss dependencies or misread scope/precedence. Commercial
products already cover amendment workflows. Small evaluation cannot establish
production reliability. Explicit scope confirmation is a human attestation of
inventory completeness, not a deterministic proof that no semantic change was missed.

## Milestones — P0-A foundation and bounded P0-B slice authorized
- P0-A: repository context, packet contract, revision/approval engine, targeted tests,
  and one real Nemotron capability check (metered check requires separate approval).
- P0-B: first offline upload/review slice AUTHORIZED and implemented; complete
  real end-to-end review journey remains PLANNED.
- P0-C: critical trust controls and qualification requirements — PLANNED.
- P1: recovery, adversarial evaluation, evidence and judge packaging — PLANNED.
- P2: reusable primitives and optional Tavily retrieval — PLANNED.
- P3: presentation polish — PLANNED.
Reserve final two days for verification/submission preparation.

## Decision history
- 2026-10-19 APPROVED: user selected BidDelta.
- 2026-10-19 PROPOSED in handoff: bounded packet-review architecture/milestones;
  no implementation or verification existed at planning handoff.
- 2026-10-19 APPROVED: user supplied repository and authorized bounded P0-A
  development; this supersedes handoff's pending-development and missing-repo status.
  Approval does not authorize deployment, publication, spending or submission.
- 2026-10-19 IMPLEMENTATION DECISION: minimal SQLite immutable aggregate snapshots
  and original-byte BLOBs, no ORM/event framework. Transactions serialize mutations;
  expected packet revision rejects stale review requests. Audit, decisions, evidence
  and document history persist. This is private local storage, not encrypted hosting.
- 2026-10-19 IMPLEMENTATION DECISION: known requirement dependencies expire
  deterministically. Impact review covers every item and cannot override known
  dependencies. Scope confirmation attests complete inventory, including zero-change
  amendments, and only carries unaffected approvals. Empty PDF pages stay gaps.
- 2026-10-19 IMPLEMENTATION DECISION: 20 MiB/file, 50 MiB/packet; historical versions
  count toward five files/60 PDF pages/two amendments. No pruning to bypass bounds.

- 2026-10-19 APPROVED: user authorized preserving the existing P0-A implementation
  on branch feat/biddelta-p0-foundation, committing, pushing to GitHub and opening
  a pull request targeting main. No automatic merge, deployment, metered inference
  or P0-B development is authorized. Existing executed test evidence is retained;
  comprehensive tests are not repeated for this preservation-only task.

- 2026-10-19 APPROVED: first bounded P0-B phase, upload and packet review through
  the frontend/API, with offline synthetic fixtures, no real provider calls, no API
  key, targeted tests only, and no push/merge/deployment/spending. Builder Program
  approval is pending. This supersedes earlier "no P0-B" authorization status.
- 2026-10-19 IMPLEMENTATION DECISION: page candidates and user-selected dependency
  mappings provide a manual workflow without simulated semantic inference.
  Original sources and the deterministic engine remain authoritative. JSON/base64
  upload transport avoids an added multipart dependency; both decoded files and
  total HTTP bodies are bounded. Request size cap is 72 MiB including base64.
- 2026-10-19 IMPLEMENTATION DECISION: one packet snapshot supplies both the UI packet
  and export gate so their revisions cannot disagree. Existing gate logic is shared,
  not reimplemented in the frontend. Local session ownership is server-generated.

- 2026-10-19 APPROVED: preserve completed P0-B slice 1 on
  feat/biddelta-p0b-packet-review by committing, pushing and opening a stacked PR
  against feat/biddelta-p0-foundation. Preserve existing evidence without rerunning
  comprehensive tests. No merge of either PR, new milestone, deployment or paid
  inference is authorized. This supersedes the prior local-only preservation limit.

## Implementation and verification evidence
IMPLEMENTED: AGENTS.md and authoritative context; React/TypeScript status scaffold;
FastAPI health route; typed packet/domain contracts; bounded PyMuPDF and CSV helpers;
SQLite original source bytes and immutable snapshots; revision/approval engine;
human impact/scope decisions; evidence revisions; export gate; disabled Token
Factory interface. See docs/DOMAIN_CONTRACT.md for exact service behavior.

VERIFIED on 2026-10-19: 37 targeted backend tests passed in 0.71s, no warnings;
TypeScript and Vite build passed in 238ms. Original bytes, revision chains, dependent
expiration, scoped unaffected carry-forward, missing-impact/evidence/gap blocking,
stale-request rejection, owner checks, rollback and retained audit/review history
were exercised. Provider-interface tests are synthetic only. Editable backend
installation used preprovisioned dependencies. See docs/evidence/RESULTS.md and raw
pytest/build logs for executed commands and limitations. The initial frontend CSS
type declaration failure was corrected before the passing build.

DOCUMENTATION VERIFIED: official Token Factory quickstart, model listing API,
chat API, structured JSON, tools, rate limits and official Nemotron cookbook were
inspected. Candidate model IDs and limitations are recorded with URLs in
docs/TOKEN_FACTORY.md. Account-visible availability and exact schema acceptance
remain UNVERIFIED. No model-generated inference results exist.

## P0-B slice 1 — implemented and verified
IMPLEMENTED: initial PDF/CSV upload and preview, exact quoted CSV evidence IDs,
manual tender/response page mappings, packet persistence, amendment source upload
and human change inventory, impact review, complete-scope confirmation, item
approvals, deterministic gate visibility and decision history. React uses a same-
origin Vite proxy to the FastAPI local API. Server ownership, origin/host checks,
body limits and private DB permissions are applied. Explicit synthetic fixture
files are generated offline, with no mock inference result presented as real.

VERIFIED: 18 focused tests passed in 0.75s (13 current API cases and five selected
engine regression cases; 15 unrelated engine tests deselected). A Chromium browser
check exercised browser → Vite proxy → API → SQLite → UI, including a reopened page
retaining reviewed revision 2. It demonstrated scoped approval carry-forward and
fresh review for the stale dependent item. No browser errors, external/provider
requests or mobile horizontal overflow were observed. TypeScript checking and
Vite build passed in 126ms. See docs/evidence/P0B_SLICE_1.md and raw logs. The prior
37-test P0-A result remains historical evidence, not a new full-suite result.

PLANNED/UNVERIFIED: semantic analysis, bounded worker runtime, correction/recheck UI,
evidence correction UI, persistent session recovery after backend restart,
downloadable/reproducible exports, hosted isolation, real inference, public packet
selection and held-out evaluation. Full architecture and P0-B remain incomplete.

## Current blockers and next phase
Nebius Builder Program approval is pending. Token Factory credentials, account-
visible model/credits and exact model structured-output capability remain
unverified. Real inference is prohibited in this slice and unnecessary for offline
verification. No provider call or API credit spend occurred.

The authorized development slice is complete. Current work is preservation only:
commit/push the existing P0-B branch and open the authorized stacked PR, then stop.
Recommended next bounded development phase: offline evidence correction and
response correction/recheck, followed by a reproducible reviewed export. Obtain
further authorization before starting that phase or pushing/merging/deploying.
The independent real Nemotron capability check still requires appropriate account
access, provider egress and explicit metered-call approval when authorized.

## Research sources reused from handoff
- https://devpost.com/software/accesspatch
- https://devpost.com/software/accesstrace
- https://devpost.com/software/lucius-open-reader
- https://askcontinua.com/ai-rfp-analysis
- https://zephior.com/insights/update-a-live-response-after-an-addendum
- https://nebius.com/blog/posts/serverless-ai-builders-challenge-winners
- https://docs.tokenfactory.nebius.com/ai-models-inference/json
- https://docs.tokenfactory.nebius.com/ai-models-inference/function-calling
