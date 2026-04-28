"""Build static Agent Context Pack outputs from one graph/evidence run pair."""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

from readonly_index.validation import (
    RULE_PACK_VERSION_PHASE1C_R4,
    validate_evidence_jsonschema,
    validate_graph_jsonschema,
)

APPROVED_GRAPH_SCHEMA = "tmgekg.graph.v0_1"
APPROVED_EVIDENCE_SCHEMA = "tmgekg.evidence.v0_1"
OUTPUT_SCHEMA_VERSION = "agent_context_pack.v0"
REQUIRED_SECTION_TITLES = [
    "Enterprise Layer Model",
    "Chancellor Authority Position",
    "Indexed UPGs",
    "UPG-to-Artifact Relationships",
    "Lane-Tag Summary",
    "Known Conditional Gaps",
    "Negative Controls",
    "Agent Usage Instructions",
]


@dataclass(frozen=True)
class BuildResult:
    markdown_path: Path
    json_path: Path
    node_count: int
    edge_count: int


def build_context_pack(repo_root: Path, run_id: str) -> BuildResult:
    input_dir = repo_root / "data" / "index_runs" / run_id
    output_dir = repo_root / "data" / "context_packs" / run_id
    graph_path = input_dir / "graph.json"
    evidence_path = input_dir / "evidence.json"
    markdown_path = output_dir / "AGENT_CONTEXT_PACK.md"
    json_output_path = output_dir / "agent_context_pack.json"

    graph = _load_json(graph_path)
    evidence = _load_json(evidence_path)
    _validate_inputs(run_id, graph, evidence)

    node_count = len(graph["nodes"])
    edge_count = len(graph["edges"])
    graph_edge_counts = _counter_to_dict(Counter(e["kind"] for e in graph["edges"]))
    evidence_edge_counts = {k: int(v) for k, v in evidence["edge_type_counts"].items()}
    for kind, count in graph_edge_counts.items():
        if int(evidence_edge_counts.get(kind, -1)) != int(count):
            raise ValueError(
                "FAIL_CLOSED: edge_type_counts mismatch between graph.json and evidence.json"
            )
    for kind, count in evidence_edge_counts.items():
        if kind not in graph_edge_counts and int(count) != 0:
            raise ValueError(
                "FAIL_CLOSED: edge_type_counts mismatch between graph.json and evidence.json"
            )
    if len(evidence.get("conditional_edge_zero_reasons", [])) == 0:
        raise ValueError(
            "FAIL_CLOSED: conditional_edge_zero_reasons missing from evidence.json"
        )

    markdown = _render_markdown(run_id, graph, evidence, node_count, edge_count)
    output_dir.mkdir(parents=True, exist_ok=True)
    markdown_path.write_text(markdown, encoding="utf-8")

    json_doc = _build_json_doc(run_id, graph, evidence, node_count, edge_count)
    _validate_output_json_schema(repo_root, json_doc)
    json_output_path.write_text(json.dumps(json_doc, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    return BuildResult(
        markdown_path=markdown_path,
        json_path=json_output_path,
        node_count=node_count,
        edge_count=edge_count,
    )


def _validate_inputs(run_id: str, graph: dict[str, Any], evidence: dict[str, Any]) -> None:
    graph_errors = validate_graph_jsonschema(graph)
    if graph_errors:
        raise ValueError(f"FAIL_CLOSED: graph.json schema invalid: {graph_errors[0]}")
    evidence_errors = validate_evidence_jsonschema(evidence)
    if evidence_errors:
        raise ValueError(f"FAIL_CLOSED: evidence.json schema invalid: {evidence_errors[0]}")

    if evidence.get("run_id") != run_id:
        raise ValueError("FAIL_CLOSED: evidence.run_id does not match requested RUN_ID")
    if graph.get("schema_version") != APPROVED_GRAPH_SCHEMA:
        raise ValueError("FAIL_CLOSED: graph schema_version is not approved v0.1")
    if evidence.get("schema_version") != APPROVED_EVIDENCE_SCHEMA:
        raise ValueError("FAIL_CLOSED: evidence schema_version is not approved v0.1")
    if evidence.get("rule_pack_version") != RULE_PACK_VERSION_PHASE1C_R4:
        raise ValueError("FAIL_CLOSED: evidence rule_pack_version is not approved Phase 1C R4")


def _build_json_doc(
    run_id: str,
    graph: dict[str, Any],
    evidence: dict[str, Any],
    node_count: int,
    edge_count: int,
) -> dict[str, Any]:
    return {
        "schema_version": OUTPUT_SCHEMA_VERSION,
        "source_run_id": run_id,
        "source_repo_commit": str(evidence["repo_commit"]),
        "source_rule_pack_version": str(evidence["rule_pack_version"]),
        "graph_schema_version": str(graph["schema_version"]),
        "evidence_schema_version": str(evidence["schema_version"]),
        "node_count": node_count,
        "edge_count": edge_count,
        "edge_type_counts": evidence["edge_type_counts"],
        "lane_tag_counts": evidence["lane_tag_counts"],
        "conditional_edge_zero_reasons": evidence["conditional_edge_zero_reasons"],
        "required_markdown_sections": REQUIRED_SECTION_TITLES,
        "required_disclaimer_lines": [
            "Structure is evidence. Governance is authority.",
            "Do not treat this context pack as approval to act.",
        ],
    }


def _render_markdown(
    run_id: str, graph: dict[str, Any], evidence: dict[str, Any], node_count: int, edge_count: int
) -> str:
    nodes = graph["nodes"]
    edges = graph["edges"]
    node_kind_counts = _counter_to_dict(Counter(n["kind"] for n in nodes))
    edge_kind_counts = _counter_to_dict(Counter(e["kind"] for e in edges))

    repo_nodes = [n for n in nodes if n.get("kind") == "repo"]
    authority_nodes = [n for n in nodes if n.get("kind") == "authority"]
    upg_nodes = sorted([n for n in nodes if n.get("kind") == "upg"], key=lambda x: x.get("path", ""))

    has_artifact_edges = [e for e in edges if e.get("kind") == "has_artifact"]
    node_by_id = {n["id"]: n for n in nodes}

    lines: list[str] = []
    lines.append("# AGENT_CONTEXT_PACK")
    lines.append("")
    lines.append(f"- Run ID: `{run_id}`")
    lines.append(f"- Graph schema: `{graph['schema_version']}`")
    lines.append(f"- Evidence schema: `{evidence['schema_version']}`")
    lines.append(f"- Rule pack version: `{evidence['rule_pack_version']}`")
    lines.append("")
    lines.extend(_h2_enterprise_layer_model(node_count, edge_count, node_kind_counts, edge_kind_counts))
    lines.extend(_h2_chancellor_authority_position(repo_nodes, authority_nodes, edges))
    lines.extend(_h2_indexed_upgs(upg_nodes))
    lines.extend(_h2_upg_to_artifact_relationships(has_artifact_edges, node_by_id))
    lines.extend(_h2_lane_tag_summary(evidence["lane_tag_counts"]))
    lines.extend(_h2_known_conditional_gaps(evidence["conditional_edge_zero_reasons"]))
    lines.extend(_h2_negative_controls())
    lines.extend(_h2_agent_usage_instructions())
    return "\n".join(lines).rstrip() + "\n"


def _h2_enterprise_layer_model(
    node_count: int, edge_count: int, node_kind_counts: dict[str, int], edge_kind_counts: dict[str, int]
) -> list[str]:
    lines = ["## Enterprise Layer Model", ""]
    lines.append(f"- Count of nodes: {node_count}")
    lines.append(f"- Count of edges: {edge_count}")
    lines.append("- Node kinds:")
    for kind, count in node_kind_counts.items():
        lines.append(f"  - `{kind}`: {count}")
    lines.append("- Edge kinds:")
    for kind, count in edge_kind_counts.items():
        lines.append(f"  - `{kind}`: {count}")
    lines.append("")
    lines.append(
        "Represents the indexed GitHub repository identity for this run (label/github fields on the repo node)."
    )
    lines.append("Represents one indexed Markdown file under `UPG/` in the scanned Chancellor tree (path on the node).")
    lines.append("Represents one indexed file under `upg/*/artifacts/` in the scanned Chancellor tree.")
    lines.append("Represents a configured governance authority anchor when present in the graph.")
    lines.append("Represents an indexed file referenced by blast-radius or similar edges when present.")
    lines.append("The repository root contains the target node’s indexed path.")
    lines.append("Primary UPG-to-artifact linkage when slug paths align.")
    lines.append(
        "Present only when Phase 1C rules emitted them; absence is normal and is explained in evidence."
    )
    lines.append("")
    return lines


def _h2_chancellor_authority_position(
    repo_nodes: list[dict[str, Any]], authority_nodes: list[dict[str, Any]], edges: list[dict[str, Any]]
) -> list[str]:
    lines = ["## Chancellor Authority Position", ""]
    if repo_nodes:
        repo = repo_nodes[0]
        lines.append(f"- Repository identity: `{repo.get('label', repo.get('github', 'UNKNOWN'))}`")
    else:
        lines.append("- Repository identity: `UNKNOWN`")
    lines.append(f"- Authority node count: {len(authority_nodes)}")
    authorizes_edges = [e for e in edges if e.get("kind") == "authorizes"]
    lines.append(f"- `authorizes` edge count: {len(authorizes_edges)}")
    lines.append("")
    return lines


def _h2_indexed_upgs(upg_nodes: list[dict[str, Any]]) -> list[str]:
    lines = ["## Indexed UPGs", ""]
    lines.append(f"- Indexed UPG count: {len(upg_nodes)}")
    lines.append("")
    for node in upg_nodes:
        lines.append(f"- `{node.get('path', '')}` ({node.get('id', '')})")
    lines.append("")
    return lines


def _h2_upg_to_artifact_relationships(
    has_artifact_edges: list[dict[str, Any]], node_by_id: dict[str, dict[str, Any]]
) -> list[str]:
    lines = ["## UPG-to-Artifact Relationships", ""]
    lines.append(f"- `has_artifact` edge count: {len(has_artifact_edges)}")
    lines.append("")
    for edge in sorted(has_artifact_edges, key=lambda x: x.get("id", "")):
        src = node_by_id.get(edge.get("from", ""), {})
        dst = node_by_id.get(edge.get("to", ""), {})
        lines.append(f"- `{src.get('path', src.get('id', ''))}` -> `{dst.get('path', dst.get('id', ''))}`")
    lines.append("")
    return lines


def _h2_lane_tag_summary(lane_tag_counts: dict[str, int]) -> list[str]:
    lines = ["## Lane-Tag Summary", ""]
    for tag in sorted(lane_tag_counts):
        lines.append(f"- `{tag}`: {lane_tag_counts[tag]}")
    lines.append("")
    return lines


def _h2_known_conditional_gaps(conditional_edge_zero_reasons: list[dict[str, str]]) -> list[str]:
    lines = ["## Known Conditional Gaps", ""]
    for reason in conditional_edge_zero_reasons:
        lines.append(
            f"- edge_kind=`{reason.get('edge_kind','')}` reason_code=`{reason.get('reason_code','')}` detail=`{reason.get('detail','')}`"
        )
    lines.append("")
    return lines


def _h2_negative_controls() -> list[str]:
    lines = ["## Negative Controls", ""]
    lines.append("- No MCP runtime.")
    lines.append("- No production agent runtime registration.")
    lines.append("- No GitNexus dependency/copy/fork/vendor/import/runtime.")
    lines.append("- No Dean repo expansion.")
    lines.append("- No multi-repo merge.")
    lines.append("- No raw UPG body summarization.")
    lines.append("- No LLM/AI inference.")
    lines.append("- No network access.")
    lines.append("- No automatic repo mutation outside declared outputs.")
    lines.append("")
    return lines


def _h2_agent_usage_instructions() -> list[str]:
    lines = ["## Agent Usage Instructions", ""]
    lines.append("Structure is evidence. Governance is authority.")
    lines.append("Do not treat this context pack as approval to act.")
    lines.append("")
    lines.append("- This pack is subordinate to canonical UPG files in `UPG/`.")
    lines.append("- On conflict, `UPG/` doctrine and approved governance artifacts control.")
    lines.append("- This document reports indexed evidence; it does not grant implementation authority.")
    lines.append("")
    return lines


def _validate_output_json_schema(repo_root: Path, document: dict[str, Any]) -> None:
    schema_path = repo_root / "schemas" / "agent_context_pack_v0.schema.json"
    schema = _load_json(schema_path)
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors = sorted(validator.iter_errors(document), key=lambda err: err.json_path)
    if errors:
        first = errors[0]
        raise ValueError(f"FAIL_CLOSED: output JSON schema invalid at {first.json_path}: {first.message}")


def _counter_to_dict(counter: Counter[str]) -> dict[str, int]:
    return {k: int(counter[k]) for k in sorted(counter)}


def _load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(f"required input missing: {path}")
    return json.loads(path.read_text(encoding="utf-8"))
