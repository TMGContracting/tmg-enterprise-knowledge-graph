# Phase 1 feasibility packet — read-only index prototype

**Status:** **DRAFT — scaffold phase** (repository **STUB ONLY**; gate closure for **merge of meaningful indexer logic** is tracked below.)  
**Child UPG:** [`UPG-GOV-TMG-EKG-READONLY-INDEX-PROTOTYPE-001`](https://github.com/TMGContracting/governance/blob/main/UPG/UPG-GOV-TMG-EKG-READONLY-INDEX-PROTOTYPE-001.md)  
**Parent UPG:** [`UPG-GOV-GITNEXUS-MCP-STRUCTURAL-AWARENESS-001`](https://github.com/TMGContracting/governance/blob/main/UPG/UPG-GOV-GITNEXUS-MCP-STRUCTURAL-AWARENESS-001.md)

## 1. Gate checklist (child UPG Section 6)

| Gate | Artifact | Status |
| --- | --- | --- |
| 1 | Phase 1 feasibility packet (this file) | **Present** — content **DRAFT**; expand with concrete input roots before first real indexer merge |
| 2 | Closed-set file matrix | **Present** — reproduced in Section 9; must match `main` at merge time |
| 3 | TMG-native graph schema v0 | **Present** — `schemas/tmg_ekg_graph_v0.schema.json` |
| 4 | TMG-native evidence schema v0 | **Present** — `schemas/tmg_ekg_evidence_v0.schema.json` |
| 5 | Contamination-control statement | **Present** — `docs/CONTAMINATION_CONTROL.md` |
| 6 | Fail-closed behavior | **Defined** — Section 7 + stub behavior in `tools/readonly_index/` |
| 7 | Acceptance criteria (UPG Section 10) | **Referenced** — Section 8 test outline |

**Interpretation:** Artifacts exist so **documentation and schema gates** are satisfied for the **stub scaffold** commit. **Operational GO** for merging **non-stub indexer logic** still requires CCP/HITL sign-off that input roots, sample runs, and CI evidence are complete (per child UPG Section 6 narrative).

## 2. Proposed schema

- **Graph:** `schemas/tmg_ekg_graph_v0.schema.json` — JSON Schema 2020-12; nodes (`repo`, `authority`, `upg`, `artifact`, `file`) and edges (`contains`, `precedes`, `authorizes`, `blast_radius`, `derived_from`).
- **Evidence:** `schemas/tmg_ekg_evidence_v0.schema.json` — run metadata, hashed inputs/outputs, `FAIL_CLOSED` reasons, validation status.

## 3. Proposed index inputs (to be pinned before real scans)

Read-only allowlisted **filesystem roots** (developer machine or CI workspace), e.g. checked-out clones of:

- `TMGContracting/governance` — Chancellor UPGs and `upg/` execution artifacts
- `TMGContracting/gomerai-governance` — Dean governance (if in scope)
- Additional repos **only** if listed here and in `tools/readonly_index/config.py` for a given release

**Constraints:** no blind repo-wide crawl; max depth and include/exclude globs to be specified before indexer merge. **Default:** no network fetch of repositories — clones must exist locally or in CI checkout.

## 4. Proposed read-only outputs

Per run directory:

- `data/index_runs/<RUN_ID>/graph.json`
- `data/index_runs/<RUN_ID>/evidence.json`

`<RUN_ID>`: ISO8601 UTC timestamp + short content hash of configuration (format to be implemented).

## 5. Proposed validation gates

1. JSON Schema validation for `graph.json` and `evidence.json` before write completion (atomic write or write-to-temp + rename).
2. Hash mismatch between recorded input hash and file on disk → `FAIL_CLOSED` in evidence, no partial graph publish.
3. Missing allowlist root → refuse run (exit non-zero, evidence records reason).

## 6. Future MCP tool names (planning only — not implemented)

Reserved prefix: **`tmg.ekg.*`**

| Planned tool id (documentation only) | Purpose (future phase) |
| --- | --- |
| `tmg.ekg.query_graph` | Query materialized graph (not authorized in this repo yet) |
| `tmg.ekg.validate_evidence` | Validate last evidence packet |

**No** MCP server, **no** stdio transport, **no** Cursor registration in this child UPG.

## 7. Fail-closed behavior (operational summary)

Aligned with child UPG Section 9:

- Missing / ambiguous allowlist → **no run**
- Output path escapes `data/index_runs/<RUN_ID>/` → **no write**
- Schema validation failure → **no emit**; evidence documents `FAIL_CLOSED`
- No network unless explicitly listed in a future revision of this packet (default **none**)
- No `git` mutating commands; read-only filesystem reads

Stub CLI today exits without scanning (see `tools/readonly_index/cli.py`).

## 8. Acceptance criteria test outline (UPG Section 10)

When indexer is implemented (non-stub PR):

1. Run CLI against a fixture workspace with known small governance tree.
2. Validate outputs with a JSON Schema validator against v0 schemas.
3. Assert graph contains at least one node of each required kind for the fixture.
4. Assert evidence records input hashes, output hashes, commit, `validation_status`.
5. CI job `readonly_index_validate` passes on `pull_request`.

## 9. Closed-set path matrix (implementation repo excerpt)

Authoritative list: child UPG Section 5.1. This repository **must not** add paths outside that table without UPG amendment.
