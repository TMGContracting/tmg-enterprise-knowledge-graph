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
