# tmg-enterprise-knowledge-graph

**UPG:** [`UPG-GOV-TMG-EKG-READONLY-INDEX-PROTOTYPE-001`](https://github.com/TMGContracting/governance/blob/main/UPG/UPG-GOV-TMG-EKG-READONLY-INDEX-PROTOTYPE-001.md) (child)  
**Parent:** [`UPG-GOV-GITNEXUS-MCP-STRUCTURAL-AWARENESS-001`](https://github.com/TMGContracting/governance/blob/main/UPG/UPG-GOV-GITNEXUS-MCP-STRUCTURAL-AWARENESS-001.md)

## Repository status: STUB ONLY

This repository is a **governance-authorized scaffold** for the **TMG Enterprise Knowledge Graph** read-only index prototype.

- **No meaningful indexer logic** is implemented yet; CLI and modules are stubs.
- **This is not** a claim that Section 6 implementation-merge gates are closed for production indexing PRs — see `docs/feasibility/PHASE1_FEASIBILITY_PACKET.md` for gate status.
- **No** MCP server, **no** production MCP registration, **no** GitNexus dependency or copied code (see `docs/CONTAMINATION_CONTROL.md`).

## Planned layout (closed-set)

See the child UPG **Section 5.1** for the authoritative path matrix. Key paths:

- `docs/feasibility/PHASE1_FEASIBILITY_PACKET.md` — feasibility and fail-closed definition
- `docs/CONTAMINATION_CONTROL.md` — clean-room / contamination controls
- `schemas/tmg_ekg_graph_v0.schema.json` — Graph JSON v0
- `schemas/tmg_ekg_evidence_v0.schema.json` — Evidence JSON v0
- `tools/readonly_index/` — indexer package (stub)
- `data/index_runs/<RUN_ID>/` — run outputs (when implemented)

## CLI (stub)

```bash
pip install -e .
tmg-ekg-index --help
```

Default invocation (without real configuration) exits with a stub message and non-zero status until indexing is implemented under a follow-on change.
