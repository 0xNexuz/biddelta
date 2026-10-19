# BidDelta

Trace tender amendments into response items, evidence and approval decisions.
P0-B slice 1 provides an offline, local-owner upload and review workflow. The full
application architecture and real Nemotron integration remain incomplete.

Read [project context](docs/PROJECT_CONTEXT.md) and [agent instructions](AGENTS.md).
Existing MIT license is retained. No deployment or inference spending is authorized.

## Local setup

Python 3.12+ and Node 24 were used. From the repository root:

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -e 'backend[test]'
python -m uvicorn biddelta.api:app --host 127.0.0.1 --port 8000
```

In another terminal:

```bash
cd frontend
npm ci
npm run dev
```

Open http://127.0.0.1:5173. Keep both services bound to loopback. The frontend proxies
`/api` to port 8000, so cookies and review requests use the same browser origin.
Production hosting and public uploads are not supported.

## Offline review journey

1. Select a tender text PDF, draft response text PDF and UTF-8 evidence CSV, or use
   the explicitly labeled synthetic example files. CSV header is
   `evidence_id,status,note`; status is asserted, missing or conflict.
2. Preview sources. Each readable tender/response page becomes a candidate. Inspect
   the extracted text and choose each response page's requirement/evidence links.
   Defaults conservatively include every dependency. These are manual mappings,
   not detected semantic claims. Create the packet after checking them.
3. Enter a rationale, confirm the complete inventory/scope, then review and approve
   individual items. Missing evidence, conflicts and extraction gaps block the gate.
4. Upload or preview a synthetic amendment. Review its page change candidates and
   requirement links, or explicitly record that no supported changes were found.
5. Record the amendment. Review each change's affected/unaffected response scope,
   confirm complete scope, and freshly approve affected items. The backend decides
   when the reviewed gate opens. Earlier review decisions remain in history.

The synthetic two-page example can demonstrate selective expiration: map response
page 1 only to tender page 1, page 2 only to tender page 2, and the synthetic deadline
amendment only to r-1. Then i-1 becomes stale and i-2 can carry forward after scope
confirmation. This is an authored example, not a model accuracy result.

Bounds: five files including amendments, up to two amendments, 60 total PDF pages,
20 MiB/file, 50 MiB decoded packet. JSON/base64 transport has a 72 MiB HTTP cap.
No OCR. Page granularity, extraction order and human scope attestation do not prove
semantic completeness. Evidence entries remain owner assertions. Reviewed state is
not legal compliance. Downloadable export is not implemented in this slice.

## Local data and request boundaries

The backend stores exact bytes and immutable historical snapshots in
`.biddelta/packets.sqlite3`, ignored by Git. Its directory/files are created private;
use `umask 077` and keep the workspace private. No source filenames become paths.
A browser receives an opaque HttpOnly SameSite=Strict cookie; server state binds it
to an owner. APIs reject untrusted origins/hosts and require a custom write header.
This is local session isolation, not production authentication or retention policy.

Packet state survives page reload in the same running backend. Session ownership
is currently in memory: restarting the backend loses access to prior browser-owned
packets, although their bytes/history remain in SQLite. Persistent recovery is
remaining work. Do not use this development slice for sensitive production packets.

## Focused verification

```bash
. .venv/bin/activate
python -m pytest -q backend/tests/test_api.py backend/tests/test_workflow_api.py backend/tests/test_engine.py -k 'not test_engine or dependent_approval or missing_impact or stale_approval_request or unresolved_evidence'
cd frontend
npm run build
```

An optional browser check is preserved at `frontend/tests/review_browser.py`.
With both local servers running and Playwright Python/Chromium available in your
development environment, run `python frontend/tests/review_browser.py` from the
repository root. Playwright is not an application dependency. The check rejects
external browser requests and uses only authored synthetic fixture files.

[Slice evidence](docs/evidence/P0B_SLICE_1.md) records actual execution and limits;
[earlier P0-A evidence](docs/evidence/RESULTS.md) remains unchanged. No key is needed.
The adapter remains disabled and is not invoked by any upload/review endpoint.
See [Token Factory feasibility](docs/TOKEN_FACTORY.md) for unverified access needs
and [domain contract](docs/DOMAIN_CONTRACT.md) for engine semantics. P0-A service
contracts remain intact; the new API maps manual page candidates into them.

Next proposed phase: offline correction/recheck and reviewed export, under a new
bounded authorization. Builder Program approval and real inference remain pending.
