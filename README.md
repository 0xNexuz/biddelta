# BidDelta

Amendment changes traced into response claims, evidence and approval decisions.
P0-A foundation only; the full application architecture remains planned.

Read [project context](docs/PROJECT_CONTEXT.md) and [agent instructions](AGENTS.md)
first. Development authorization does not include pushing, deployment or inference
spending. Existing MIT license is retained.

## Local setup

Python 3.12+ and Node 24 were used for verification. From the repository root:

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -e 'backend[test]'
python -m pytest -v backend/tests
cd frontend
npm ci
npm run build
npm run dev
```

The frontend is a foundation status screen, without packet workflows. Vite binds
to loopback. To run the API in a separate terminal from the repository root:

```bash
. .venv/bin/activate
python -m uvicorn biddelta.api:app --host 127.0.0.1 --port 8000
```

`GET /health` returns the milestone and explicitly unverified inference status.
No upload, approval or inference HTTP endpoints exist in this milestone.

## Domain service

`biddelta.documents.extract_document` creates bounded document metadata and exact
page/record source spans from original bytes. Use `Engine(Store(private_db_path))`
in trusted local Python code. Initial `create` receives an owner, three extracted
`(DocumentVersion, bytes)` pairs, source-linked Requirements and ResponseItems.

The targeted tests in `backend/tests/conftest.py` and `test_engine.py` provide small,
synthetic, executable examples of create → confirm_scope → approve → amend →
review_impact → confirm_scope → fresh approve → gate. They generate PDFs in memory;
no private procurement files or provider calls are needed.

Use a private directory and restrictive file permissions (`umask 077`) for SQLite.
The database stores original bytes and immutable historical snapshots; do not
commit it. Owner identity is a trusted local service argument, not web auth.

See [domain contract](docs/DOMAIN_CONTRACT.md) for record semantics and limits,
[Token Factory feasibility](docs/TOKEN_FACTORY.md) for official sources and access
requirements, and [verification evidence](docs/evidence/RESULTS.md) for actual runs.

## Inference access

No credentials are needed for deterministic tests or the frontend build. The
Token Factory adapter is disabled by default and never runs at startup. Configure
NEBIUS_API_KEY only on the server, select an account-verified NEBIUS_MODEL, and keep
BIDDELTA_ALLOW_METERED_INFERENCE=false until explicit spending approval. The
`backend/.env.example` file documents names; environment files are not auto-loaded.
No inference output has been verified. Synthetic HTTP tests validate local adapter
behavior only.

## Boundaries and next step

Implemented: typed contracts; SQLite transactions/source history; selective
approval expiration; human scope/impact review; evidence revisions; export gate;
bounded PDF/CSV helpers; minimal React/TypeScript and FastAPI foundations.

Not implemented: full upload/review journey, downloadable exports, worker runtime,
hosted isolation, retrieval, automatic proposal generation or deployment. Reviewed
state is not legal compliance or a proof of completeness. The remaining P0-A item
is one approved, bounded real Nemotron capability check. P0-B requires separate
authorization.
