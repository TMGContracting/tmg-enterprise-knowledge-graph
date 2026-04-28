# context_packs

Per `UPG-GOV-TMG-EKG-AGENT-CONTEXT-PACK-001`, static Agent Context Pack outputs are written under:

- `data/context_packs/<RUN_ID>/AGENT_CONTEXT_PACK.md`
- `data/context_packs/<RUN_ID>/agent_context_pack.json`

Generation is fail-closed and bound to one validated Phase 1C run pair:

- `data/index_runs/<RUN_ID>/graph.json`
- `data/index_runs/<RUN_ID>/evidence.json`

The generator must reject:

- RUN_ID mismatch between path and `evidence.run_id`
- `schema_version` values outside approved v0.1
- `rule_pack_version` outside `UPG-GOV-TMG-EKG-GRAPH-QUALITY-PHASE1C-001-R4`

No MCP runtime, no network access, and no cross-repo merge is authorized by this output path.
