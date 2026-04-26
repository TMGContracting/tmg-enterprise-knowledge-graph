"""Graph / evidence checks and JSON Schema validation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema import exceptions as jsonschema_exc


def repo_root() -> Path:
    """`tmg-enterprise-knowledge-graph` repository root (package lives under `tools/readonly_index/`)."""
    return Path(__file__).resolve().parents[2]


def load_graph_schema() -> dict[str, Any]:
    p = repo_root() / "schemas" / "tmg_ekg_graph_v0.schema.json"
    return json.loads(p.read_text(encoding="utf-8"))


def load_evidence_schema() -> dict[str, Any]:
    p = repo_root() / "schemas" / "tmg_ekg_evidence_v0.schema.json"
    return json.loads(p.read_text(encoding="utf-8"))


def validate_graph_jsonschema(document: dict[str, Any]) -> list[str]:
    """Return list of error strings; empty if valid for Draft 2020-12 + date-time (format)."""
    schema = load_graph_schema()
    return _validate_against_schema(schema, document)


def validate_evidence_jsonschema(document: dict[str, Any]) -> list[str]:
    """Return list of error strings; empty if valid for Draft 2020-12 + date-time (format)."""
    schema = load_evidence_schema()
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
    if document.get("schema_version") != "tmgekg.graph.v0":
        errors.append("invalid_schema_version")
    if not isinstance(document.get("nodes"), list):
        errors.append("nodes_not_list")
    if not isinstance(document.get("edges"), list):
        errors.append("edges_not_list")
    return errors


def validate_evidence_minimal(document: dict[str, Any]) -> list[str]:
    """Return error strings; empty list means minimal structure OK (legacy helper)."""
    errors: list[str] = []
    required = (
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
    for key in required:
        if key not in document:
            errors.append(f"missing_field:{key}")
    if document.get("schema_version") != "tmgekg.evidence.v0":
        errors.append("invalid_schema_version")
    return errors
