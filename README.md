# tmg-enterprise-knowledge-graph

**UPG:** [`UPG-GOV-TMG-EKG-READONLY-INDEX-PROTOTYPE-001`](https://github.com/TMGContracting/governance/blob/main/UPG/UPG-GOV-TMG-EKG-READONLY-INDEX-PROTOTYPE-001.md) (child)  
**Parent:** [`UPG-GOV-GITNEXUS-MCP-STRUCTURAL-AWARENESS-001`](https://github.com/TMGContracting/governance/blob/main/UPG/UPG-GOV-GITNEXUS-MCP-STRUCTURAL-AWARENESS-001.md)  
**Phase 1C graph quality (scaffold / schemas):** [`UPG-GOV-TMG-EKG-GRAPH-QUALITY-PHASE1C-001`](https://github.com/TMGContracting/governance/blob/main/UPG/UPG-GOV-TMG-EKG-GRAPH-QUALITY-PHASE1C-001.md) — JSON Schema **v0.1** and validators are in-repo; the indexer **still emits v0** until an explicit **rule-pack GO** authorizes enrichment merges. Evidence **v0.1** requires **`rule_pack_version`:** `UPG-GOV-TMG-EKG-GRAPH-QUALITY-PHASE1C-001-R4`.

## Repository status

**Phase 1:** a minimal **read-only** indexer (no network, no mutating `git` commands, no MCP server) indexes **one** checked-out repo root at a time (for example [TMGContracting/governance](https://github.com/TMGContracting/governance) or [TMGContracting/gomerai-governance](https://github.com/TMGContracting/gomerai-governance)) under the globs in `docs/feasibility/PHASE1_FEASIBILITY_PACKET.md` (v0). Default run outputs are **v0** `graph.json` and `evidence.json` with JSON Schema checks.

**Phase 1C scaffold:** **v0.1** schemas (`schemas/tmg_ekg_graph_v0_1.schema.json`, `schemas/tmg_ekg_evidence_v0_1.schema.json`) and `tools/readonly_index/validation.py` dispatch on `schema_version`; CI validates **v0 and v0.1**. No new enrichment edges are emitted by the indexer in this phase.

- **This is not** a claim that Section 6 production-merge gates are closed — see `docs/feasibility/PHASE1_FEASIBILITY_PACKET.md`.
- **No** production MCP, **no** GitNexus dependency or copied code (`docs/CONTAMINATION_CONTROL.md`).

## Layout (closed-set)

- `docs/feasibility/PHASE1_FEASIBILITY_PACKET.md` — feasibility and fail-closed rules
- `docs/CONTAMINATION_CONTROL.md` — clean-room controls
- `schemas/tmg_ekg_graph_v0.schema.json` — graph v0
- `schemas/tmg_ekg_evidence_v0.schema.json` — evidence v0
- `schemas/tmg_ekg_graph_v0_1.schema.json` — graph v0.1 (Phase 1C)
- `schemas/tmg_ekg_evidence_v0_1.schema.json` — evidence v0.1 (Phase 1C; `rule_pack_version` = `UPG-GOV-TMG-EKG-GRAPH-QUALITY-PHASE1C-001-R4`)
- `tools/readonly_index/` — indexer
- `data/index_runs/<RUN_ID>/` — run output directory

## CLI

From the **tmg-enterprise-knowledge-graph** repo root, with a local **governance**-layout clone (Chancellor or Dean, one root per run):

```bash
pip install -e .
EKG_GOVERNANCE_ROOT="/path/to/governance" tmg-ekg-index run --output-parent data/index_runs
# or: tmg-ekg-index run --input-root /path/to/gomerai-governance --repo-id TMGContracting/gomerai-governance --output-parent data/index_runs
```

**Repository identity in the graph `repo` node** (`github` and `label`): use `--repo-id Org/Repo`, or set `EKG_REPO_ID`, or omit both and the tool will try a **read-only** `git remote get-url origin` in the **input** tree when it is a `github.com` remote (fails closed if the input is not a git working tree with such an origin, unless you set `--repo-id` / `EKG_REPO_ID`).

This writes `data/index_runs/<RUN_ID>/graph.json` and `data/index_runs/<RUN_ID>/evidence.json` in this repository only, validates them against the **v0** schemas (default), and **does not** open network connections, modify the input working tree, or use mutating `git` subcommands. Read-only `git` in the **input** root (for `origin` URL) and in the **implementation** repo (for `repo_commit` in evidence) is allowed. For the evidence `outputs[1].content_sha256` field, the prototype uses the 64-ASCII-`0` **template** hash (see `docs/feasibility/PHASE1_FEASIBILITY_PACKET.md` context).
