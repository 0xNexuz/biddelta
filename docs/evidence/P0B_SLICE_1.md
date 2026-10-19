# P0-B slice 1 execution evidence — 2026-10-19

Branch: feat/biddelta-p0b-packet-review. Base: preserved P0-A commit
66a5192cdeb3d5f923a3ec949d6e90388f09dd15. At the end of implementation, changes
were local and uncommitted. GitHub preservation is a separate authorized task
recorded in PROJECT_CONTEXT.md. During implementation no push, merge, deployment,
provider call or API spending occurred. Local verification
servers were stopped after the checks.

## Actual targeted tests

```bash
/workspace/.biddelta-env/venv/bin/python -m pytest -q backend/tests/test_api.py backend/tests/test_workflow_api.py backend/tests/test_engine.py -k 'not test_engine or dependent_approval or missing_impact or stale_approval_request or unresolved_evidence'
```

Result: **18 passed, 15 deselected in 0.75s**. Raw output: p0b-api-tests.txt.
This ran 13 affected API cases and five selected original engine cases. The full
37-test P0-A suite and unrelated provider/extraction tests were not rerun.

Verified: upload/preview/create; page dependency mapping and quoted CSV identities;
initial scope/approval; amendment revisions; selective approval expiration and
scope carry-forward; impact/gate blocking; stale-request 409; unresolved-evidence
blocking; immutable decision history; invalid uploads/references rollback;
cross-session packet denial; forged owner fields rejected; untrusted origin/host
and missing custom write-header rejection; HTTP body limit. No key is required.

The first targeted run had 16 passes and one failure: the new test incorrectly
expected seven decisions when the six submitted decisions had been preserved.
The assertion was corrected to six. No application invariant was changed to make
it pass. A CSV preview identity edge case was also covered before the final run.

## Browser → API → data → response

Both local servers ran bound to 127.0.0.1, using the Vite /api proxy. Playwright
with the system Chromium browser executed the authored synthetic fixture journey:

Upload/preview → manual page mapping → create → scope → approve both items →
reviewed gate open → synthetic amendment mapped only to r-1 → i-1 stale and i-2
needs scope → impact review → scope confirmation carries i-2 → fresh i-1 approval
→ gate open → browser reload retains revision 2 and review history.

Raw result: p0b-browser.txt. Reproducible script: frontend/tests/review_browser.py.
The script was executed from work/p0b-browser.py before preserving its source;
only browser executable discovery and scratch-directory creation were generalized.
It rejected non-local browser requests. No external/provider requests or runtime
errors were observed. At 390 px width no horizontal page overflow was detected.
A full-page mobile screenshot was retained locally under ignored work/.

The first browser launch found no Playwright-managed binary; the existing system
/usr/bin/chromium was used successfully. No browser dependency was installed.
This is one synthetic scenario, not a held-out model or production security test.

## Frontend build

`cd frontend && npm run build` executed TypeScript checking and a Vite build.
Final result: success in 126ms; raw output p0b-frontend-build.txt. No new application
dependencies were added. Original dependency lockfile and P0-A evidence are retained.

## Remaining limitations and blockers

Real Nebius inference remains UNVERIFIED and prohibited here. Builder Program
approval is pending; account/key/model/credits and provider egress still need
verification. Page candidates and mappings are authored/human-reviewed; no model
semantic detection is claimed. No private hosted upload support, worker isolation,
response/evidence correction UI, downloadable reviewed export, or full evaluation.
Browser sessions survive page reload while the backend runs but are lost on backend
restart; persistent recovery is future work. Original packet history stays in SQLite.

Stop after this slice. Recommended next bounded phase: offline correction/recheck,
then reproducible reviewed export, under further development authorization.
