# index_runs

Per **UPG-GOV-TMG-EKG-READONLY-INDEX-PROTOTYPE-001**, indexer outputs (when implemented) must be written only under:

`data/index_runs/<RUN_ID>/graph.json`  
`data/index_runs/<RUN_ID>/evidence.json`

Default indexer runs validate against **graph/evidence v0**. **v0.1** schemas exist for **UPG-GOV-TMG-EKG-GRAPH-QUALITY-PHASE1C-001** (see `schemas/tmg_ekg_*_v0_1.schema.json`); Phase 1C completion runs will use **`tmgekg.graph.v0_1`** / **`tmgekg.evidence.v0_1`** and evidence **`rule_pack_version`:** `UPG-GOV-TMG-EKG-GRAPH-QUALITY-PHASE1C-001-R4` after enrichment is merged under that UPG.

Do not commit large run trees to `main` unless explicitly reviewed as evidence bundles.
