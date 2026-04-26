"""Read-only governance index (no network, no mutating git, no MCP)."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import config as cfg
from . import validation as V

_RUN_ID_SAFE = re.compile(r"^[A-Za-z0-9._-]{4,256}$")

_HASH_ZERO = "0" * 64


@dataclass
class IndexResult:
    """Result of a successful index run."""

    run_id: str
    run_dir: Path
    graph_path: Path
    evidence_path: Path
    input_count: int


def _zulu(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _implementation_repo_commit() -> str:
    root = V.repo_root()
    try:
        r = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        if r.returncode == 0 and r.stdout:
            return r.stdout.strip()
    except OSError:
        pass
    return "unknown"


def _safe_run_id(resolved_input_root: Path, rel_paths: list[str]) -> str:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")
    key = str(resolved_input_root) + "\0" + "\0".join(sorted(rel_paths))
    short = hashlib.sha256(key.encode("utf-8")).hexdigest()[:8]
    rid = f"{ts}-{short}"
    if not _RUN_ID_SAFE.match(rid):
        raise ValueError("invalid generated run_id")
    return rid


def _validate_input_root_for_governance(root: Path) -> Path:
    r = root.resolve()
    if not r.is_dir():
        raise FileNotFoundError("EKG input root: not a directory")
    if not (r / "UPG").is_dir() and not (r / "upg").is_dir():
        raise ValueError(
            "EKG input root: not a valid governance tree (expected UPG/ and/or upg/ directory)"
        )
    return r


def _validate_output_and_run(
    input_root: Path, output_parent: Path, run_id: str, impl_root: Path
) -> tuple[Path, Path]:
    if not _RUN_ID_SAFE.match(run_id) or ".." in run_id or "/" in run_id or "\\" in run_id:
        raise ValueError("invalid or unsafe run_id")
    out_parent = output_parent.resolve()
    if out_parent.exists() and not out_parent.is_dir():
        raise NotADirectoryError("output parent exists but is not a directory")
    if not out_parent.is_relative_to(impl_root):
        raise ValueError(
            "refusing: output parent must be under tmg-enterprise-knowledge-graph (implementation) root"
        )
    iroot = input_root.resolve()
    if out_parent == iroot or out_parent.is_relative_to(iroot) or iroot.is_relative_to(out_parent):
        raise ValueError("refusing: input root and output parent must not overlap or nest each other")
    run_dir = (out_parent / run_id).resolve()
    if not run_dir.is_relative_to(out_parent):
        raise ValueError("refusing: run output directory escapes output parent (path traversal)")
    if run_dir == iroot or run_dir.is_relative_to(iroot) or iroot.is_relative_to(run_dir):
        raise ValueError("refusing: run output must not overlap the governance input root")
    return out_parent, run_dir


def _collect_allowed_files(iroot: Path) -> list[Path]:
    root = iroot.resolve()
    if not root.is_dir():
        raise FileNotFoundError("input root: not a directory")
    out: list[Path] = []
    for pattern in ("UPG/*.md", "upg/*/artifacts/*.md", "upg/*/artifacts/*.json"):
        for p in root.glob(pattern):
            if not p.is_file():
                continue
            try:
                rp = p.resolve()
            except OSError:
                continue
            if not rp.is_relative_to(root):
                continue
            out.append(rp)
    return sorted(set(out))


def _node_id_for_path(rel_posix: str) -> str:
    h = hashlib.sha256(rel_posix.encode("utf-8")).hexdigest()
    return f"n-{h}"


def _build_graph(rel_inputs: list[str], generated_at: str) -> dict[str, Any]:
    graph_id = "g-" + hashlib.sha256(("|".join(sorted(rel_inputs))).encode()).hexdigest()[:12]
    nodes: list[dict[str, Any]] = [
        {
            "id": "n-repo-governance",
            "kind": "repo",
            "label": cfg.REPO_GITHUB,
            "github": cfg.REPO_GITHUB,
            "lane_tags": ["NONE"],
        }
    ]
    edges: list[dict[str, Any]] = []
    for rel in rel_inputs:
        rel_p = rel.replace("\\", "/")
        nid = _node_id_for_path(rel_p)
        if rel_p.startswith("UPG/") and rel_p.endswith(".md"):
            kind = "upg"
            classification = "canonical"
        else:
            kind = "artifact"
            classification = "evidence"
        nodes.append(
            {
                "id": nid,
                "kind": kind,
                "path": rel_p,
                "label": Path(rel_p).name,
                "classification": classification,
                "lane_tags": ["NONE"],
            }
        )
        edges.append(
            {
                "id": f"e-contains-{nid}",
                "kind": "contains",
                "from": "n-repo-governance",
                "to": nid,
            }
        )
    return {
        "schema_version": "tmgekg.graph.v0",
        "graph_id": graph_id,
        "generated_at_utc": generated_at,
        "upg_authority": cfg.UPG_AUTHORITY,
        "parent_upg_authority": cfg.PARENT_UPG_AUTHORITY,
        "nodes": nodes,
        "edges": edges,
    }


def _canonical_json_bytes(document: dict[str, Any]) -> bytes:
    return (json.dumps(document, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _write_json(path: Path, document: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = _canonical_json_bytes(document).decode("utf-8")
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(data, encoding="utf-8")
    tmp.replace(path)


def _write_evidence_with_structural_self_hash(
    ev_path: Path, base: dict[str, Any], g_hash: str, run_id: str
) -> str:
    """evidence `outputs[1].content_sha256` is the SHA-256 of UTF-8 JSON where that field
    is sixty-four '0' characters (template), not a Kleene fixed point of the final file.
    """
    rel_g = f"data/index_runs/{run_id}/graph.json"
    rel_e = f"data/index_runs/{run_id}/evidence.json"
    self_placeholder = {
        "path": rel_e,
        "content_sha256": _HASH_ZERO,
    }
    template: dict[str, Any] = {
        **base,
        "outputs": [
            {"path": rel_g, "content_sha256": g_hash},
            self_placeholder,
        ],
    }
    template_bytes = _canonical_json_bytes(template)
    evidence_self_recorded = hashlib.sha256(template_bytes).hexdigest()
    final_doc: dict[str, Any] = {
        **base,
        "outputs": [
            {"path": rel_g, "content_sha256": g_hash},
            {
                "path": rel_e,
                "content_sha256": evidence_self_recorded,
            },
        ],
    }
    errs = V.validate_evidence_jsonschema(final_doc)
    if errs:
        raise ValueError("evidence JSON Schema: " + "; ".join(errs))
    _write_json(ev_path, final_doc)


def run_index(
    input_root: Path,
    output_parent: Path,
    tool_version: str,
) -> IndexResult:
    started = datetime.now(timezone.utc)
    started_s = _zulu(started)
    impl = V.repo_root()
    iroot = _validate_input_root_for_governance(input_root)
    abs_files = _collect_allowed_files(iroot)
    rel_files: list[str] = [str(p.relative_to(iroot)).replace("\\", "/") for p in abs_files]
    if any(".." in r or r.startswith(("/", "\\")) for r in rel_files):
        raise ValueError("refusing: illegal relative path in inputs")

    generated_t = started_s
    graph = _build_graph(rel_files, generated_t)
    errs = V.validate_graph_jsonschema(graph)
    if errs:
        raise ValueError("graph JSON Schema: " + "; ".join(errs))

    run_id = _safe_run_id(iroot, rel_files)
    out_parent, run_dir = _validate_output_and_run(iroot, output_parent, run_id, impl)

    out_parent.mkdir(parents=True, exist_ok=True)
    run_dir.mkdir(parents=True, exist_ok=True)
    if not out_parent.is_relative_to(impl) or not run_dir.is_relative_to(out_parent):
        raise ValueError("refusing: path contract failed after mkdir")

    graph_path = run_dir / "graph.json"
    ev_path = run_dir / "evidence.json"
    _write_json(graph_path, graph)
    g_hash = _sha256_file(graph_path)

    input_records: list[dict[str, str]] = [
        {"path": r, "content_sha256": _sha256_file(p)} for p, r in zip(abs_files, rel_files, strict=True)
    ]

    ended = datetime.now(timezone.utc)
    ended_s = _zulu(ended)
    ev_base: dict[str, Any] = {
        "schema_version": "tmgekg.evidence.v0",
        "run_id": run_id,
        "started_at_utc": started_s,
        "ended_at_utc": ended_s,
        "tool_version": tool_version,
        "repo_commit": _implementation_repo_commit(),
        "upg_authority": cfg.UPG_AUTHORITY,
        "inputs": input_records,
        "validation_status": "PASS",
        "fail_closed_reasons": [],
    }
    e0 = {**ev_base, "outputs": []}
    oerrs = V.validate_evidence_jsonschema(e0)
    if oerrs:
        raise ValueError("evidence (empty outputs): " + "; ".join(oerrs))

    _write_evidence_with_structural_self_hash(ev_path, ev_base, g_hash, run_id)
    final = json.loads(ev_path.read_text(encoding="utf-8"))
    verrs = V.validate_evidence_jsonschema(final)
    if verrs:
        raise ValueError("evidence (final): " + "; ".join(verrs))
    gfinal = json.loads(graph_path.read_text(encoding="utf-8"))
    gverrs = V.validate_graph_jsonschema(gfinal)
    if gverrs:
        raise ValueError("graph (final): " + "; ".join(gverrs))
    o_graph = [r for r in final["outputs"] if r["path"].endswith("/graph.json")][0]
    if o_graph["content_sha256"] != _sha256_file(graph_path):
        raise ValueError("refusing: graph output record does not match graph.json on disk")

    return IndexResult(
        run_id=run_id,
        run_dir=run_dir,
        graph_path=graph_path,
        evidence_path=ev_path,
        input_count=len(abs_files),
    )
