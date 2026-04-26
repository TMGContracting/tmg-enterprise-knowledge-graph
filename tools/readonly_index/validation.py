"""STUB validation helpers — minimal structural checks until full JSON Schema validation is wired."""

from __future__ import annotations

from typing import Any


def validate_graph_minimal(document: dict[str, Any]) -> list[str]:
    """Return error strings; empty list means minimal structure OK."""
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
    if document.get("schema_version") != "tmgekg.graph.v0":
        errors.append("invalid_schema_version")
    if not isinstance(document.get("nodes"), list):
        errors.append("nodes_not_list")
    if not isinstance(document.get("edges"), list):
        errors.append("edges_not_list")
    return errors


def validate_evidence_minimal(document: dict[str, Any]) -> list[str]:
    """Return error strings; empty list means minimal structure OK."""
    errors: list[str] = []
    required = (
        "schema_version",
        "run_id",
        "started_at_utc",
        "ended_at_utc",
        "tool_version",
        "repo_commit",
        "inputs",
        "outputs",
        "validation_status",
        "fail_closed_reasons",
    )
    for key in required:
        if key not in document:
            errors.append(f"missing_field:{key}")
    if document.get("schema_version") != "tmgekg.evidence.v0":
        errors.append("invalid_schema_version")
    return errors
