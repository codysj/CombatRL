# P11 Backend And Dashboard Scope

Status: implementation-ready draft, pending product approval.

## Users And Workflows

P11 serves one local developer or researcher working with CombatRL artifacts.
The first workflow is read-only: discover local evaluation runs, inspect their
metadata and metrics, and open an existing replay in the browser viewer. A
secondary workflow compares selected evaluation runs without starting training.

Training, evaluation, simulator control, account management, remote storage,
multi-user collaboration, and live LLM calls are out of scope.

## Decision

FastAPI is justified only for a small local artifact catalog because browsers
cannot safely enumerate arbitrary local artifact trees. It is not required for
opening a user-selected replay directory, which remains frontend-only.

The backend owns filesystem discovery, Pydantic validation, stable read-only
JSON contracts, path containment, and clear unavailable/corrupt states. The
frontend owns filtering, tables, comparison presentation, and routing into the
existing replay viewer. Neither layer recomputes simulation or evaluation data.

## Minimal API

All endpoints bind to loopback by default and return JSON.

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/api/v1/health` | Process and contract version |
| `GET` | `/api/v1/runs` | Validated evaluation/training run summaries |
| `GET` | `/api/v1/runs/{run_id}` | One run and its available artifacts |
| `GET` | `/api/v1/runs/{run_id}/metrics` | Existing metrics/report data |
| `GET` | `/api/v1/replays/{replay_id}/manifest` | Validated replay file URLs |
| `GET` | `/api/v1/replays/{replay_id}/files/{name}` | One allowlisted replay file |

Identifiers are opaque catalog IDs, never raw paths. Allowed roots are explicit
configuration. File serving is limited to known artifact filenames and rejects
path traversal, symlinks escaping a root, oversized files, and unsupported
schema versions.

## Artifact Discovery

Discovery scans configured local roots on startup and explicit refresh. It does
not watch continuously in the first pass. Invalid entries are represented with
diagnostics rather than crashing or disappearing. Catalog ordering is stable.
No artifact is modified, deleted, uploaded, or automatically migrated.

## Acceptance Tests

1. Empty, valid, partially written, corrupt, and mixed-version roots return
   deterministic catalog results.
2. Paths outside configured roots and traversal attempts return an error.
3. Existing replay files are served byte-for-byte and still pass the Python
   validator and browser loader.
4. The dashboard works with an empty catalog and clearly marks unavailable
   metrics or files.
5. API contract tests run without network services, cloud credentials, a live
   simulator, or a training process.
6. Browser tests open a catalog replay and retain the existing local-directory
   workflow.

## Delivery Plan

1. CRL-009 defines catalog models, fixture trees, containment rules, and API
   contract tests.
2. CRL-010 implements the read-only local FastAPI service.
3. CRL-011 adds the dashboard run browser and replay handoff.

Approval should confirm the read-only local boundary, configured roots, and
deferred control surfaces before CRL-010 begins.
