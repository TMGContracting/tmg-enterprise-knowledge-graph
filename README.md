# tmg-enterprise-knowledge-graph

**UPG:** [`UPG-GOV-TMG-EKG-READONLY-INDEX-PROTOTYPE-001`](https://github.com/TMGContracting/governance/blob/main/UPG/UPG-GOV-TMG-EKG-READONLY-INDEX-PROTOTYPE-001.md) (child)  
**Parent:** [`UPG-GOV-GITNEXUS-MCP-STRUCTURAL-AWARENESS-001`](https://github.com/TMGContracting/governance/blob/main/UPG/UPG-GOV-GITNEXUS-MCP-STRUCTURAL-AWARENESS-001.md)

## Repository status

**Phase 1:** a minimal **read-only** indexer (no network, no mutating `git` commands, no MCP server) indexes **only** a checked-out [TMGContracting/governance](https://github.com/TMGContracting/governance) clone, under the globs in `docs/feasibility/PHASE1_FEASIBILITY_PACKET.md` (v0). Outputs are v0 `graph.json` and `evidence.json` with JSON Schema checks.

- **This is not** a claim that Section 6 production-merge gates are closed — see `docs/feasibility/PHASE1_FEASIBILITY_PACKET.md`.
- **No** production MCP, **no** GitNexus dependency or copied code (`docs/CONTAMINATION_CONTROL.md`).

## Layout (closed-set)

- `docs/feasibility/PHASE1_FEASIBILITY_PACKET.md` — feasibility and fail-closed rules
- `docs/CONTAMINATION_CONTROL.md` — clean-room controls
- `schemas/tmg_ekg_graph_v0.schema.json` — graph v0
- `schemas/tmg_ekg_evidence_v0.schema.json` — evidence v0
- `tools/readonly_index/` — indexer
- `data/index_runs/<RUN_ID>/` — run output directory

## CLI

From the **tmg-enterprise-knowledge-graph** repo root, with a local **governance** clone:

```bash
pip install -e .
EKG_GOVERNANCE_ROOT="/path/to/governance" tmg-ekg-index run --output-parent data/index_runs
# or: tmg-ekg-index run --input-root /path/to/governance --output-parent data/index_runs
```

This writes `data/index_runs/<RUN_ID>/graph.json` and `data/index_runs/<RUN_ID>/evidence.json` in this repository only, validates them against the v0 schemas, and **does not** open network connections, modify the governance working tree, or use mutating `git` subcommands in the index tool. (`git rev-parse` may be used read-only to record the implementation commit in evidence.) For the evidence `outputs[1].content_sha256` field, the prototype records the SHA-256 of the canonical JSON **template** in which that field is sixty-four ASCII `0` characters, so the value is not always equal to a raw re-hash of the final on-disk `evidence.json` bytes.
