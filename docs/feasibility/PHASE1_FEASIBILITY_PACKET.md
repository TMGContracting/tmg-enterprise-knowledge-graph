# Phase 1 feasibility packet — read-only index prototype (R2)

**Status:** **R2 / READY FOR SPEC REVIEW** — this packet is fit for **Spec / HITL** review to authorize a **first non-stub read-only indexer PR** (it is **not** a claim of implementation complete or of finished indexer product).  
**Predecessor:** CCP R1 (MODIFY) — `PHASE1_FEASIBILITY_PACKET_CCP_REVIEW_R1.md` in the governance child lane.  
**Child UPG:** [`UPG-GOV-TMG-EKG-READONLY-INDEX-PROTOTYPE-001`](https://github.com/TMGContracting/governance/blob/main/UPG/UPG-GOV-TMG-EKG-READONLY-INDEX-PROTOTYPE-001.md)  
**Parent UPG:** [`UPG-GOV-GITNEXUS-MCP-STRUCTURAL-AWARENESS-001`](https://github.com/TMGContracting/governance/blob/main/UPG/UPG-GOV-GITNEXUS-MCP-STRUCTURAL-AWARENESS-001.md)  

**Constraints preserved:** no MCP server, no production MCP, no network in the index tool, no GitNexus dependency/copy/fork/vendor, **no non-stub indexer code in this revision** (documentation and schema only).  

---

## 1. Gate checklist (child UPG Section 6) — R2

| Gate | Artifact | R2 status |
| --- | --- | --- |
| 1 | Phase 1 feasibility packet (this file) | **R2** — **READY FOR SPEC REVIEW**; concrete contract + examples; **HITL/Spec sign-off** still required to authorize the first **non-stub** merge |
| 2 | Closed-set file matrix | Reproduced in **§14**; no path drift in this change set |
| 3 | Graph schema v0 | `schemas/tmg_ekg_graph_v0.schema.json` — **tightened (R2)**; see **§2** and **§10** |
| 4 | Evidence schema v0 | `schemas/tmg_ekg_evidence_v0.schema.json` — **tightened (R2)**; see **§2** and **§11** |
| 5 | Contamination-control | `docs/CONTAMINATION_CONTROL.md` (unchanged path) |
| 6 | Fail-closed + **§6 refused-run policy** + **§9** CI/validator | **Documented** |
| 7 | UPG Section 10 acceptance outline | **§12** |

---

## 2. Proposed schema (child UPG Section 11)

| Artifact | Path | Notes (R2) |
| --- | --- | --- |
| Graph v0 | `schemas/tmg_ekg_graph_v0.schema.json` | **Minimal valid examples:** **§10**. `file` / `upg` / `artifact` nodes require **`classification`**; `repo` / `authority` may omit; **lane_tags** for sparse **EPAP / VQT / PMS** (optional). |
| Evidence v0 | `schemas/tmg_ekg_evidence_v0.schema.json` | **`upg_authority` required**; `validation_status` may be `PASS` \| `FAIL_CLOSED` \| `STUB_NOOP` \| `ERROR`; `fail_closed_reasons` is an array of structured objects (see schema). **§11** minimal example. |

**Child UPG Section 11 “example minimal valid documents”:** satisfied in **§10** and **§11** (embedded JSON).

---

## 3. First input root contract (single root only — v0.1)

**Environment variable (exact name):** `EKG_GOVERNANCE_ROOT`  

- **Value:** **absolute** path to a **checked-out** clone of **`TMGContracting/governance`** on the local disk or in CI.  
- **Not** a URL, **not** a GitHub web path; the clone must **already exist** (read-only from the index tool; **no** `git fetch`, no network in the index tool).  
- **Out of scope for the first read-only run:** a second root (e.g. gomerai-governance). Adding roots requires a **packet revision** (or UPG update if scope change is material).  

**First scan scope (repository):**  
**`TMGContracting/governance` only** (via `EKG_GOVERNANCE_ROOT`).

**First allowed include globs (only these three; v0.1) — all relative to `EKG_GOVERNANCE_ROOT`:**

1. `UPG/*.md`  
2. `upg/*/artifacts/*.md`  
3. `upg/*/artifacts/*.json`  

Implementations **must** resolve these **only** under `EKG_GOVERNANCE_ROOT` (no `..` escape, no symlink **escape outside the root** — **fail closed** if resolution leaves the root). Do **not** add broader `**` crawls in v0.1.  

> **Path spelling:** the governance repo on disk uses **`UPG/`** (uppercase) and **`upg/`** (lowercase) on case-sensitive filesystems.  

---

## 4. Proposed read-only outputs

- `data/index_runs/<RUN_ID>/graph.json` — must validate against the graph v0 schema.  
- `data/index_runs/<RUN_ID>/evidence.json` — must validate against the evidence v0 schema.  

**`<RUN_ID>`:** e.g. UTC ISO timestamp + 8+ hex char content hash of configuration; **no** path characters (`/`, `\\`, `..`).

**Writes:** only under `data/index_runs/<RUN_ID>/` (child UPG Section 5.1).  

---

## 5. Proposed validation gates (pre-write)

1. **JSON Schema** validation of `graph.json` and `evidence.json` **before** (or as part of) atomic write (temp + rename).  
2. **Content hash** of each indexed file recorded in `evidence.json` `inputs`; on mismatch if re-read (policy in implementation) — **fail closed** with `FAIL_CLOSED`.  
3. **Allowlist** root missing, unreadable, or ambiguous → **refused run** (see **§6**).  
4. **No** graph emit if evidence validation fails, and **vice versa** (pair must both pass, except **refused-run** case in **§6**).  

---

## 6. Refused-run policy (HITL / CCP R1)

| Situation | Behavior |
| --- | --- |
| A refused run (e.g. bad/missing `EKG_GOVERNANCE_ROOT`, unwritable output parent) **and** a **valid** and **safe** `data/index_runs/<RUN_ID>/` can be created | The implementation **should** still write a **valid** `evidence.json` with `validation_status` **`FAIL_CLOSED`**, populated `fail_closed_reasons`, empty or partial `outputs` as appropriate, and `inputs` as much as is safe to record. **Omit** `graph.json` if no graph was produced, or include only if the schema and pipeline allow; **or** default `graph.json` to a minimal **empty** graph (nodes `[]`, edges `[]`) if the schema and product choice allow — **pick one strategy in the first non-stub PR and document in code** (must be consistent with this packet). This packet **recommends:** **no** `graph.json` on refusal if no index pass ran; if that is not valid for tooling, a **minimal** empty graph (see **§10** structure with empty `nodes`/`edges`) is acceptable. |
| Output path **invalid** (unsafe) or `RUN_ID` **bad** (path traversal) | **No write**; **stderr-only** with non-zero exit; no `evidence.json` (cannot be written safely). |
| Catastrophic / unexpected internal error | **`validation_status` = `ERROR`** in `evidence.json` if `evidence.json` can be written; otherwise **stderr** + exit. |

**Network:** not used by the index tool (default).  

**`git`:** **no** mutating `git` commands.  

---

## 7. Future MCP tool names (planning only)

Prefix **`tmg.ekg.*`**, **no** server, **no** stdio, **no** product registration in this UPG.

| Planned tool id (documentation) | Note |
| --- | --- |
| `tmg.ekg.query_graph` | Future |
| `tmg.ekg.validate_evidence` | Future |

---

## 8. Fail-closed summary (aligns with child UPG Section 9)

- Missing/ambiguous `EKG_GOVERNANCE_ROOT` → refused run (see **§6**).  
- Output path escapes `data/index_runs/<RUN_ID>/` or invalid `RUN_ID` → no write, stderr-only if unsafe.  
- Schema validation failure → do not emit final outputs; evidence records **`FAIL_CLOSED`** or **`ERROR`**.  
- No **network** in the index process unless a **future** packet + UPG revision justifies it.  

**Stub (current) CLI** exits with non-zero without scanning; **no** change to stub behavior in this R2 (documentation + schema only).  

---

## 9. Validator / CI story (JSON Schema + `date-time`)

- **CI** (`.github/workflows/readonly_index_validate.yml` **R2**): installs `jsonschema[format-nongpl]`, uses `Draft202012Validator` (or equivalent) with **format checker** for `date-time` on **schema** parse and for **instance** validation of the **minimal examples** in **§10–§11** (embedded in the workflow, same JSON as in this file).  
- If format validation is **unavailable** in a given environment, the implementation **must** still validate structure and const/required; **and** must **record** in evidence or in CI logs that **strict** `date-time` format was not applied (R2: CI does apply format checker when `jsonschema` is used as above).  
- **No** new repository paths: examples stay **in this packet**; CI inlines the same instance JSON as heredoc/Python.  

---

## 10. Concrete minimal valid Graph JSON (example)

```json
{
  "schema_version": "tmgekg.graph.v0",
  "graph_id": "example-r2-minimum",
  "generated_at_utc": "2026-04-28T12:00:00Z",
  "upg_authority": "UPG-GOV-TMG-EKG-READONLY-INDEX-PROTOTYPE-001",
  "parent_upg_authority": "UPG-GOV-GITNEXUS-MCP-STRUCTURAL-AWARENESS-001",
  "nodes": [
    {
      "id": "node-repo-governance",
      "kind": "repo",
      "label": "TMGContracting/governance",
      "github": "TMGContracting/governance",
      "lane_tags": ["NONE"]
    },
    {
      "id": "node-upg-ekg-child",
      "kind": "upg",
      "label": "UPG-GOV-TMG-EKG-READONLY-INDEX-PROTOTYPE-001",
      "path": "UPG/UPG-GOV-TMG-EKG-READONLY-INDEX-PROTOTYPE-001.md",
      "classification": "canonical"
    }
  ],
  "edges": [
    {
      "id": "edge-contains-1",
      "kind": "contains",
      "from": "node-repo-governance",
      "to": "node-upg-ekg-child"
    }
  ]
}
```

**Empty graph** (e.g. refused with no index): `nodes: []` and `edges: []` are valid; same top-level `schema_version`, `graph_id`, `generated_at_utc`, `upg_authority` are still **required** by the schema.  

**Example `file` node (classification required in schema):**

```json
{
  "id": "node-file-example",
  "kind": "file",
  "path": "UPG/UPG-GOV-TMG-EKG-READONLY-INDEX-PROTOTYPE-001.md",
  "classification": "canonical",
  "lane_tags": ["EPAP"]
}
```

(**Sparse v0:** use `["EPAP"]` / `["VQT"]` / `["PMS"]` / `["NONE"]` or combinations; schema allows multiple tags and `uniqueItems`.)  

---

## 11. Concrete minimal valid Evidence JSON (example)

```json
{
  "schema_version": "tmgekg.evidence.v0",
  "run_id": "2026-04-28T12:00:00Z-abcdef12",
  "started_at_utc": "2026-04-28T12:00:00Z",
  "ended_at_utc": "2026-04-28T12:00:05Z",
  "tool_version": "0.0.0",
  "repo_commit": "0000000000000000000000000000000000000000",
  "upg_authority": "UPG-GOV-TMG-EKG-READONLY-INDEX-PROTOTYPE-001",
  "inputs": [
    {
      "path": "UPG/UPG-GOV-TMG-EKG-READONLY-INDEX-PROTOTYPE-001.md",
      "content_sha256": "2c26b46b68ffc68ff99b453c1d3041340e3ee2cbfda8517f29b3d4d0c0d0b0a1"
    }
  ],
  "outputs": [
    {
      "path": "data/index_runs/2026-04-28T12:00:00Z-abcdef12/graph.json",
      "content_sha256": "3a7bd3e2360a3d29ebea90ce6901c6c9147500c9b150b6f0f5e0c8a7b7a6e8a7"
    },
    {
      "path": "data/index_runs/2026-04-28T12:00:00Z-abcdef12/evidence.json",
      "content_sha256": "4a7bd3e2360a3d29ebea90ce6901c6c9147500c9b150b6f0f5e0c8a7b7a6e8a8"
    }
  ],
  "validation_status": "PASS",
  "fail_closed_reasons": []
}
```

(Replace placeholder SHA-256 values with real hashes in actual runs. `repo_commit` must be the **implementation repo** `tmg-enterprise-knowledge-graph` commit in real use.)  

**`STUB_NOOP`:** for current stub CLI; **`ERROR`:** for unexpected internal failure.  

---

## 12. Proposed command shape (first non-stub; spec only in R2)

```bash
export EKG_GOVERNANCE_ROOT="/absolute/path/to/governance-clone"
tmg-ekg-index run --input-root "$EKG_GOVERNANCE_ROOT" --output-parent data/index_runs
```

- The **`run`** subcommand and flags are **to be implemented** in the first non-stub PR.  
- The stub CLI may still print **STUB** until that PR.  

---

## 13. CCP R1 (MODIFY) — addressed in R2

- **Pinned** single root: `EKG_GOVERNANCE_ROOT`  
- **Minimal JSON examples** in this file  
- **Refused-run** and **format validation** in CI narrative  
- **Not** a claim of implementation or GO without Spec/HITL on this R2 document  

**Governance reference:** CCP R1: `governance` repo `upg/UPG-GOV-TMG-EKG-READONLY-INDEX-PROTOTYPE-001/artifacts/PHASE1_FEASIBILITY_PACKET_CCP_REVIEW_R1.md`  

---

## 14. Closed-set path matrix (child UPG Section 5.1) — no drift

This repository’s **additions/revisions in R2** are **only** under:  

`docs/feasibility/PHASE1_FEASIBILITY_PACKET.md` · `schemas/tmg_ekg_graph_v0.schema.json` · `schemas/tmg_ekg_evidence_v0.schema.json` · `docs/CONTAMINATION_CONTROL.md` (if touched) · `.github/workflows/readonly_index_validate.yml` (CI only) — all **pre-authorized** paths.  

**No** new top-level paths (no `examples/` tree).  

---

## 15. Acceptance test outline (child UPG Section 10)

1. `export EKG_GOVERNANCE_ROOT=…` to a test clone of `TMGContracting/governance`.  
2. Run the **non-stub** `tmg-ekg-index run …` once merged.  
3. Validate `graph.json` and `evidence.json` with JSON Schema (with format) against v0 schemas.  
4. **CI** R2 must pass on PRs.  
5. Verify **no** `git` write, **no** network in index code, **no** new paths, **no** GitNexus touch.  
