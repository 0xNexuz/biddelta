# P0-B phase 2 — correction/recheck evidence

Date: 2026-10-19. Branch: feat/biddelta-p0b-correction-recheck.
Base: origin/feat/biddelta-p0-foundation at
857e6592f4af5da73da69867454834e3ee2284ae, containing merged PR #2 and its P0-B
implementation. The clean working tree was inspected before branching. No work
was based on main or recreated. PR #1's merge into main was also confirmed.

## Implemented boundary

POST /api/packets/{packet_id}/evidence-revisions validates owner session, packet
revision, evidence identity, explicit status, nonblank correction note and rationale.
Source reference is derived on the server from that evidence's history. The existing
Engine.revise_evidence transaction appends the new evidence revision, audit event
and review decision, expires dependent approvals and reopens scope. No engine
invariant or database schema changed. Saving asserted evidence never approves it
as an authenticated fact or approves any response item.

The UI shows latest status, dependent responses, original CSV source, all evidence
revisions, correction form and explanatory gate blockers. Scope confirmation and
fresh response approval remain separate owner actions. Missing/conflicting evidence
keeps linked approval disabled and the gate blocked. No replacement document,
downloadable export, public hosting, new dependency or inference was introduced.

## Actual tests

```bash
/workspace/.biddelta-env/venv/bin/python -m pytest -q backend/tests/test_evidence_api.py backend/tests/test_workflow_api.py::test_upload_amend_review_and_gate_vertical_slice backend/tests/test_engine.py::test_evidence_revisions_preserve_history_and_require_recheck
```

**13 passed in 1.14s.** Raw output: p0b-correction-tests.txt.
Eleven new cases cover correction history and original bytes/source preservation,
dependent expiration, unaffected scope carry-forward, fresh approval, missing and
conflicting evidence, wrong ownership, request-origin/header boundaries, stale
revision rejection after fresh review, concurrent correction writers (one 200,
one 409), and invalid/forged fields leaving state unchanged. Two existing focused
engine/upload/amendment regressions passed. No comprehensive suite rerun.

## Browser verification

Executed `python frontend/tests/correction_browser.py` against the loopback API
and Vite proxy with system Chromium. Existing synthetic upload/amendment journey
was exercised before missing → blocked approval → asserted correction → complete
scope → fresh dependent approval → gate open → reload retaining packet revision 4.
All three evidence revisions share the original source reference. No automatic
response approval or provider request occurred. Raw output: p0b-correction-browser.txt.

| Boundary | Executed evidence |
| --- | --- |
| UI | Explicit status/note/rationale correction form and evidence history |
| Client to API | Successful correction POSTs through same-origin Vite proxy |
| API to data | Existing transactional engine; persisted evidence revisions read back |
| Data to response | Packet revision 4, three evidence revisions, one source reference |
| Response to UI | Stale/needs-scope states, unresolved blockers, fresh approvals, reload |

The first walkthrough stopped at the new status control: its implicit label
included option text and was not accessible under its intended exact name. An
explicit label association fixed it. The second walkthrough passed. No application
code changed after that successful walkthrough. Browser reported no runtime errors,
non-local requests or mobile horizontal overflow. Screenshot remains in ignored work/.
This is one authored offline scenario, not semantic-model or production evaluation.

Final `cd frontend && npm run build` passed TypeScript checking and Vite bundling
in **185ms**, after the label fix. Raw output: p0b-correction-build.txt.
No provider key was needed. Local verification servers were stopped after checks.

## Limits and blockers

User-reported: Nebius onboarding is currently blocked because Nigeria is unavailable
in its billing-country list. This was recorded from the user's report, not verified
with a billing/account request. Builder Program review and promotional credits
remain pending. Real inference, exact model/schema support and account access remain
unverified; inference stayed disabled, with no paid requests.

Persistent session recovery after backend restart, response correction/replacement,
reproducible downloadable reviewed export, semantic analysis, worker isolation and
held-out evaluation remain future work. Recommended next bounded slice: persistent
local-session recovery before extending reviewed exports. No further phase is started.

Feature-branch commit/push and PR against feat/biddelta-p0-foundation are explicitly
authorized for preservation. No automatic merge or deployment is authorized.
