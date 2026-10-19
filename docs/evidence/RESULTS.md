# P0-A execution evidence — 2026-10-19

Final targeted run:

```text
/workspace/.biddelta-env/venv/bin/python -m pytest -v backend/tests
37 passed in 0.71s
```

Raw output: [pytest.txt](pytest.txt). Breakdown: 20 engine cases, 6 extraction
cases, 10 synthetic provider-interface cases and 1 ASGI API case. Test data is
synthetic: generated PDFs and CSV assertions, not a real public tender corpus.

Verified: new packet/document revisions and predecessor chains; byte preservation;
dependent approval expiration; unaffected approval carry-forward only after scope
confirmation; missing-impact blocking; stale revision rejection; append-only review
and audit history after SQLite reopen; missing/conflicting evidence blocks; evidence
revision/recheck; two pending amendments cannot restore stale approvals; known
impacts cannot be denied; source references/identities validated; owner checks;
transaction rollback; extraction-gap and packet/file bounds.

Provider tests use httpx.MockTransport. They verify disabled/no-key behavior,
request/schema construction, rejected truncation/refusal/unknown references/authority
fields, and no retry on HTTP 429. They are NOT inference feasibility evidence.

Frontend:

```text
cd frontend
npm ci --ignore-scripts --no-audit --no-fund
npm run build
TypeScript check passed; Vite 8.3.4 build completed in 238ms.
```

Raw final output: [frontend-build.txt](frontend-build.txt). This is compilation and
bundling evidence only; no browser interaction or complete frontend journey tested.
A first build failed with TS2882 for the CSS import; adding the standard Vite client
type declaration fixed it. No deployment occurred.

Backend package installation was executed with:
`python -m pip install --no-deps -e backend` using the provisioned environment's
pinned dependencies. This is not proof of a clean-machine dependency install.

Earlier targeted run: 24 tests passed in 2.56s; verbose pytest automatically expanded
an oversized byte fixture into a huge test ID. Explicit IDs corrected test output.
Next run: 35 passed in 0.80s with a FastAPI/Starlette TestClient deprecation warning.
The API test switched to httpx ASGITransport; the final 37-case run has no warnings.
No application assertion failures occurred in these runs.

Not verified: real Token Factory account/model list/inference/usage, model-specific
JSON support, semantic detection quality, legal correctness, real packet evaluation,
full workflow, export artifact reproducibility, hosted session isolation, production
security, resource-isolated worker, failure recovery across the full journey or
hackathon eligibility. No full Build Harness audit was run.

P0-A deterministic implementation is delivered. P0-A as originally planned remains
PARTIAL because its real Nemotron capability check is blocked by access and spending
authorization. No P0-B development, push, publication, metered call or deployment.
