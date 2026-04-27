"""Read-only indexer configuration (UPG-GOV-TMG-EKG-READONLY-INDEX-PROTOTYPE-001)."""

from __future__ import annotations

# Child + parent UPG (graph / evidence traceability)
UPG_AUTHORITY = "UPG-GOV-TMG-EKG-READONLY-INDEX-PROTOTYPE-001"
PARENT_UPG_AUTHORITY = "UPG-GOV-GITNEXUS-MCP-STRUCTURAL-AWARENESS-001"
ENV_INPUT_ROOT = "EKG_GOVERNANCE_ROOT"
# Override graph repo identity (Chancellor, Dean, etc.): --repo-id or EKG_REPO_ID
ENV_REPO_ID = "EKG_REPO_ID"
# Legacy label only; the graph `github` field is resolved at run time.
DEFAULT_DOC_REPO = "TMGContracting/governance"

# Phase 1C (UPG-GOV-TMG-EKG-GRAPH-QUALITY-PHASE1C-001) — v0.1 emit + enrichment
PHASE1C_UPG_AUTHORITY = "UPG-GOV-TMG-EKG-GRAPH-QUALITY-PHASE1C-001"
PHASE1C_PARENT_UPG_AUTHORITY = "UPG-GOV-GITNEXUS-MCP-STRUCTURAL-AWARENESS-001"
AUTHORITY_CHANCELLOR_ID = "n-authority-chancellor"
AUTHORITY_REGISTRY: dict[str, dict[str, str]] = {
    AUTHORITY_CHANCELLOR_ID: {"label": "Chancellor"},
}
# Ordered pairs (from_authority_id, to_authority_id). Empty = zero precedes edges (R4).
AUTHORITY_PRECEDENCE_PAIRS: list[tuple[str, str]] = []
