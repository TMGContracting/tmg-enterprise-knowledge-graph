"""Graph / evidence checks and JSON Schema validation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema import exceptions as jsonschema_exc

_SCHEMA_DIR = "schemas"

_GRAPH_SCHEMA_BY_VERSION: dict[str, str] = {
    "tmgekg.graph.v0": "tmg_ekg_graph_v0.schema.json",
    "tmgekg.graph.v0_1": "tmg_ekg_graph_v0_1.schema.json",
}

_EVIDENCE_SCHEMA_BY_VERSION: dict[str, str] = {
    "tmgekg.evidence.v0": "tmg_ekg_evidence_v0.schema.json",
    "tmgekg.evidence.v0_1": "tmg_ekg_evidence_v0_1.schema.json",
}

# Normative Phase 1C rule pack (UPG/UPG-GOV-TMG-EKG-GRAPH-QUALITY-PHASE1C-001.md)
RULE_PACK_VERSION_PHASE1C_R4 = "UPG-GOV-TMG-EKG-GRAPH-QUALITY-PHASE1C-001-R4"


def repo_root() -> Path:
    """`tmg-enterprise-knowledge-graph` repository root (package lives under `tools/readonly_index/`)."""
    return Path(__file__).resolve().parents[2]


def load_graph_schema() -> dict[str, Any]:
    """Load graph JSON Schema v0 (legacy helper)."""
    return _load_schema(_GRAPH_SCHEMA_BY_VERSION["tmgekg.graph.v0"])


def load_evidence_schema() -> dict[str, Any]:
    """Load evidence JSON Schema v0 (legacy helper)."""
    return _load_schema(_EVIDENCE_SCHEMA_BY_VERSION["tmgekg.evidence.v0"])


def load_graph_schema_for_version(schema_version: str) -> dict[str, Any]:
    name = _GRAPH_SCHEMA_BY_VERSION.get(schema_version)
    if not name:
        raise KeyError(f"unsupported graph schema_version: {schema_version!r}")
    return _load_schema(name)


def load_evidence_schema_for_version(schema_version: str) -> dict[str, Any]:
    name = _EVIDENCE_SCHEMA_BY_VERSION.get(schema_version)
    if not name:
        raise KeyError(f"unsupported evidence schema_version: {schema_version!r}")
    return _load_schema(name)


def _load_schema(filename: str) -> dict[str, Any]:
    p = repo_root() / _SCHEMA_DIR / filename
    return json.loads(p.read_text(encoding="utf-8"))


def validate_graph_jsonschema(document: dict[str, Any]) -> list[str]:
    """Return list of error strings; empty if valid for Draft 2020-12 + date-time (format)."""
    sv = document.get("schema_version")
    if sv not in _GRAPH_SCHEMA_BY_VERSION:
        return [f"unsupported_graph_schema_version:{sv!r}"]
    schema = load_graph_schema_for_version(str(sv))
    return _validate_against_schema(schema, document)


def validate_evidence_jsonschema(document: dict[str, Any]) -> list[str]:
    """Return list of error strings; empty if valid for Draft 2020-12 + date-time (format)."""
    sv = document.get("schema_version")
    if sv not in _EVIDENCE_SCHEMA_BY_VERSION:
        return [f"unsupported_evidence_schema_version:{sv!r}"]
    schema = load_evidence_schema_for_version(str(sv))
    return _validate_against_schema(schema, document)


def _validate_against_schema(schema: dict[str, Any], document: Any) -> list[str]:
    Draft202012Validator.check_schema(schema)
    v = Draft202012Validator(schema, format_checker=FormatChecker())
    try:
        v.validate(document)
    except jsonschema_exc.ValidationError as e:
        return [e.json_path + ": " + (e.message or "validation error")]
    return []


def validate_graph_minimal(document: dict[str, Any]) -> list[str]:
    """Return error strings; empty list means minimal structure OK (legacy helper)."""
    errors: list[str] = []
    required = (
        "schema_version",
        "graph_id",
        "generated_at_utc",
        "upg_authority",
        "nodes",
        "edges",
    )
    for key in required:
        if key not in document:
            errors.append(f"missing_field:{key}")
    sv = document.get("schema_version")
    if sv not in _GRAPH_SCHEMA_BY_VERSION:
        errors.append("invalid_schema_version")
    if not isinstance(document.get("nodes"), list):
        errors.append("nodes_not_list")
    if not isinstance(document.get("edges"), list):
        errors.append("edges_not_list")
    return errors


def validate_evidence_minimal(document: dict[str, Any]) -> list[str]:
    """Return error strings; empty list means minimal structure OK (legacy helper)."""
    errors: list[str] = []
    required_v0 = (
        "schema_version",
        "run_id",
        "started_at_utc",
        "ended_at_utc",
        "tool_version",
        "repo_commit",
        "upg_authority",
        "inputs",
        "outputs",
        "validation_status",
        "fail_closed_reasons",
    )
    required_v01 = required_v0 + (
        "edge_type_counts",
        "conditional_edge_zero_reasons",
        "lane_tag_counts",
        "rule_pack_version",
    )
    sv = document.get("schema_version")
    required = required_v01 if sv == "tmgekg.evidence.v0_1" else required_v0
    for key in required:
        if key not in document:
            errors.append(f"missing_field:{key}")
    if sv not in _EVIDENCE_SCHEMA_BY_VERSION:
        errors.append("invalid_schema_version")
    if sv == "tmgekg.evidence.v0_1":
        if document.get("rule_pack_version") != RULE_PACK_VERSION_PHASE1C_R4:
            errors.append("invalid_rule_pack_version")
    return errors
