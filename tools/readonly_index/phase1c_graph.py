"""Phase 1C v0.1 deterministic graph — UPG-GOV-TMG-EKG-GRAPH-QUALITY-PHASE1C-001 (R4)."""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

from . import config as cfg

INPUT_REPO_NODE = "n-input-repo"

ALL_EDGE_KINDS = (
    "contains",
    "precedes",
    "authorizes",
    "blast_radius",
    "derived_from",
    "has_artifact",
    "parent_of",
    "child_of",
)

# R4 labels; value may include backticks / paths (Chancellor front matter).
_PARENT_LABEL_RES = re.compile(
    r"^\s*(?:\*\*)?Parent(?:\s+UPG|\s+lineage)?(?:\*\*)?\s*:\s*(.+)\s*$",
    re.IGNORECASE,
)
_PARENT_BULLET_RES = re.compile(
    r"^\s*[-*]\s*(?:\*\*)?Parent(?:\s+UPG|\s+lineage)?(?:\*\*)?\s*:\s*(.+)\s*$",
    re.IGNORECASE,
)
_UPG_SLUG_IN_TEXT_RES = re.compile(r"(UPG-[A-Z0-9-]+)")

_DERIVED_RES = re.compile(
    r"^\s*(?:\*\*)?Derived\s+from(?:\*\*)?\s*:\s*(.+)\s*$",
    re.IGNORECASE | re.MULTILINE,
)

_BLAST_HEADING_RES = re.compile(r"^#{1,6}\s*Blast\s*radius\s*$", re.IGNORECASE | re.MULTILINE)

_AUTH_LABELS = frozenset(
    {
        "authorizes",
        "authorized implementation repo",
        "authorized paths",
        "implementation target",
        "target implementation repo",
    }
)


def _nfc(s: str) -> str:
    return unicodedata.normalize("NFC", s)


def _node_id_for_path(rel_posix: str) -> str:
    h = hashlib.sha256(rel_posix.encode("utf-8")).hexdigest()
    return f"n-{h}"


def _read_text_normalized(iroot: Path, rel: str, max_bytes: int | None) -> str:
    p = (iroot / rel.replace("\\", "/")).resolve()
    if not p.is_file() or not p.is_relative_to(iroot.resolve()):
        return ""
    raw = p.read_bytes()
    if max_bytes is not None:
        raw = raw[:max_bytes]
    t = raw.decode("utf-8", errors="replace")
    return t.replace("\r\n", "\n").replace("\r", "\n")


def lane_tags_for_path(rel_posix: str) -> list[str]:
    """R4 lane table: priority EPAP, GOV, VQT, PMS, EA; else [NONE]."""
    rp = rel_posix.replace("\\", "/")
    name = PurePosixPath(rp).name
    tags: list[str] = []
    if "/UPG-EPAP-" in rp or "/upg/UPG-EPAP-" in rp or name.startswith("UPG-EPAP-"):
        tags.append("EPAP")
    if "UPG-GOV-" in rp:
        tags.append("GOV")
    if "-VQT-" in rp or "/VQT/" in rp or "UPG-VQT-" in rp:
        tags.append("VQT")
    if "-PMS-" in rp or "UPG-PMS-" in rp or "/PMS/" in rp:
        tags.append("PMS")
    if "-EA-" in rp or "UPG-EA-" in rp or "GomerAI-EA" in rp:
        tags.append("EA")
    if not tags:
        return ["NONE"]
    order = ("EPAP", "GOV", "VQT", "PMS", "EA")
    seen: set[str] = set()
    out: list[str] = []
    for o in order:
        if o in tags and o not in seen:
            out.append(o)
            seen.add(o)
    return out


def _line_label_and_value(line: str) -> tuple[str, str] | None:
    s = line.strip()
    if ":" not in s:
        return None
    pre, post = s.split(":", 1)
    pre_st = pre.strip()
    if pre_st.startswith("**") and pre_st.endswith("**"):
        pre_st = pre_st[2:-2].strip()
    label = pre_st.casefold()
    return label, post.strip()


def _slug_from_artifact_rel(rel: str) -> str | None:
    rel = rel.replace("\\", "/")
    m = re.match(r"^upg/([^/]+)/artifacts/", rel, re.IGNORECASE)
    if not m:
        return None
    return _nfc(m.group(1))


@dataclass
class Phase1cBuild:
    graph: dict[str, Any]
    edge_type_counts: dict[str, int]
    conditional_edge_zero_reasons: list[dict[str, str]]
    lane_tag_counts: dict[str, int]


def _validate_precedence_config() -> None:
    pairs = cfg.AUTHORITY_PRECEDENCE_PAIRS
    if not pairs:
        return
    reg = cfg.AUTHORITY_REGISTRY
    for a, b in pairs:
        if a not in reg or b not in reg:
            raise ValueError(
                "EKG_PRECEDES_CONFIG_MALFORMED: AUTHORITY_PRECEDENCE_PAIRS references unknown authority id"
            )


def _authority_nodes_for_ids(required_ids: set[str]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for pid in sorted(required_ids):
        meta = cfg.AUTHORITY_REGISTRY.get(pid)
        if not meta:
            raise ValueError(f"EKG_PRECEDES_CONFIG_MALFORMED: unknown authority id {pid!r}")
        out[pid] = {
            "id": pid,
            "kind": "authority",
            "label": meta.get("label", pid),
            "lane_tags": ["NONE"],
        }
    return out


def _parse_authorizes(text: str, upg_slug: str) -> tuple[bool, str | None]:
    """Returns (emit_edge, ambiguity_code_or_none)."""
    prefix = text[:12000]
    hits: list[str] = []
    for line in prefix.split("\n"):
        parsed = _line_label_and_value(line)
        if not parsed:
            continue
        label, value = parsed
        if label not in _AUTH_LABELS:
            continue
        if upg_slug not in value and _nfc(upg_slug) not in _nfc(value):
            continue
        hits.append(value)
    if not hits:
        return False, None
    norm = {_nfc(h) for h in hits}
    if len(norm) == 1:
        return True, None
    return False, "EKG_AUTHORIZES_AMBIGUOUS"


def _parse_parent_slugs(text: str) -> tuple[list[str] | None, str | None]:
    prefix = text[:8000]
    found: set[str] = set()
    for line in prefix.split("\n"):
        m = _PARENT_LABEL_RES.match(line) or _PARENT_BULLET_RES.match(line)
        if not m:
            continue
        value = m.group(1)
        for sm in _UPG_SLUG_IN_TEXT_RES.finditer(value):
            found.add(_nfc(sm.group(1)))
    if len(found) > 1:
        return None, "parent_ambiguous"
    if len(found) == 1:
        return [next(iter(found))], None
    return [], None


def _parse_derived_target(text: str) -> tuple[str | None, str | None]:
    prefix = text[:8000]
    paths: list[str] = []
    for m in _DERIVED_RES.finditer(prefix):
        paths.append(m.group(1).strip())
    if not paths:
        return None, None
    norm = {_nfc(p) for p in paths}
    if len(norm) > 1:
        return None, "derived_ambiguous"
    return paths[0], None


def _blast_paths_from_json(text: str) -> tuple[list[str], str | None]:
    try:
        doc = json.loads(text)
    except json.JSONDecodeError:
        return [], "EKG_BLAST_JSON_INVALID"
    if not isinstance(doc, dict):
        return [], "EKG_BLAST_JSON_INVALID"
    raw = doc.get("blast_radius_paths")
    if raw is None:
        return [], None
    if not isinstance(raw, list):
        return [], "EKG_BLAST_JSON_INVALID"
    out: list[str] = []
    for item in raw:
        if isinstance(item, str):
            out.append(item)
    return out, None if out else None


def _blast_paths_from_markdown(text: str) -> list[str]:
    m = _BLAST_HEADING_RES.search(text)
    if not m:
        return []
    after = text[m.end() :]
    paths: list[str] = []
    for line in after.split("\n"):
        st = line.strip()
        if st.startswith("#"):
            break
        mo = re.match(r"^[-*]\s+(.+)$", st)
        if mo:
            paths.append(mo.group(1).strip())
    return paths


def _resolve_under_root(iroot: Path, base_rel: str, target: str) -> Path | None:
    t = target.strip().replace("\\", "/")
    if not t or ".." in PurePosixPath(t).parts:
        return None
    base = (iroot / base_rel).parent if "/" in base_rel else iroot
    cand = (iroot / t).resolve()
    try:
        cand.relative_to(iroot.resolve())
    except ValueError:
        return None
    if cand.is_file():
        return cand
    alt = (base / t).resolve()
    try:
        alt.relative_to(iroot.resolve())
    except ValueError:
        return None
    if alt.is_file():
        return alt
    return None


def build_phase1c_graph(
    iroot: Path,
    rel_inputs: list[str],
    abs_files: list[Path],
    generated_at: str,
    input_repo_id: str,
) -> Phase1cBuild:
    del abs_files
    _validate_precedence_config()
    iroot_r = iroot.resolve()

    upg_slug_to_nid: dict[str, str] = {}
    for rel in rel_inputs:
        rel_p = rel.replace("\\", "/")
        if rel_p.startswith("UPG/") and rel_p.endswith(".md"):
            slug = _nfc(PurePosixPath(rel_p).stem)
            if slug in upg_slug_to_nid:
                raise ValueError("EKG_AMBIGUOUS_UPG_SLUG: duplicate UPG slug " + slug)
            nid = _node_id_for_path(rel_p)
            upg_slug_to_nid[slug] = nid

    nodes: list[dict[str, Any]] = [
        {
            "id": INPUT_REPO_NODE,
            "kind": "repo",
            "label": input_repo_id,
            "github": input_repo_id,
            "lane_tags": ["NONE"],
        }
    ]
    node_ids: set[str] = {INPUT_REPO_NODE}
    edges: list[dict[str, Any]] = []
    reasons: list[dict[str, str]] = []

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
                "label": PurePosixPath(rel_p).name,
                "classification": classification,
                "lane_tags": lane_tags_for_path(rel_p),
            }
        )
        node_ids.add(nid)
        edges.append(
            {
                "id": f"e-contains-{nid}",
                "kind": "contains",
                "from": INPUT_REPO_NODE,
                "to": nid,
            }
        )

    for rel in rel_inputs:
        rel_p = rel.replace("\\", "/")
        if not rel_p.startswith("UPG/") or not rel_p.endswith(".md"):
            continue
        text = _read_text_normalized(iroot_r, rel_p, None)
        child_nid = _node_id_for_path(rel_p)
        ps, pamb = _parse_parent_slugs(text)
        if pamb:
            reasons.append(
                {"edge_kind": "parent_of", "reason_code": pamb, "detail": rel_p}
            )
        elif ps and len(ps) == 1:
            pnid = upg_slug_to_nid.get(ps[0])
            if pnid:
                edges.append(
                    {
                        "id": f"e-parent-{pnid}-{child_nid}",
                        "kind": "parent_of",
                        "from": pnid,
                        "to": child_nid,
                    }
                )

    authorizes_edges: list[dict[str, Any]] = []
    has_any_authorizes = False
    for rel in rel_inputs:
        rel_p = rel.replace("\\", "/")
        if not rel_p.startswith("UPG/") or not rel_p.endswith(".md"):
            continue
        slug = _nfc(PurePosixPath(rel_p).stem)
        text = _read_text_normalized(iroot_r, rel_p, None)
        child_nid = _node_id_for_path(rel_p)
        emit_auth, auth_amb = _parse_authorizes(text, slug)
        if auth_amb:
            reasons.append(
                {"edge_kind": "authorizes", "reason_code": auth_amb, "detail": rel_p}
            )
            continue
        if emit_auth:
            authorizes_edges.append(
                {
                    "id": f"e-auth-{cfg.AUTHORITY_CHANCELLOR_ID}-{child_nid}",
                    "kind": "authorizes",
                    "from": cfg.AUTHORITY_CHANCELLOR_ID,
                    "to": child_nid,
                }
            )
            has_any_authorizes = True

    prec_ids: set[str] = set()
    for a, b in cfg.AUTHORITY_PRECEDENCE_PAIRS:
        prec_ids.add(a)
        prec_ids.add(b)

    auth_required: set[str] = set(prec_ids)
    if has_any_authorizes:
        auth_required.add(cfg.AUTHORITY_CHANCELLOR_ID)

    for an in _authority_nodes_for_ids(auth_required).values():
        if an["id"] not in node_ids:
            nodes.append(an)
            node_ids.add(an["id"])

    edges.extend(authorizes_edges)

    for rel in rel_inputs:
        rel_p = rel.replace("\\", "/")
        slug_art = _slug_from_artifact_rel(rel_p)
        if not slug_art:
            continue
        upg_nid = upg_slug_to_nid.get(slug_art)
        if not upg_nid:
            continue
        art_nid = _node_id_for_path(rel_p)
        edges.append(
            {
                "id": f"e-has-art-{upg_nid}-{art_nid}",
                "kind": "has_artifact",
                "from": upg_nid,
                "to": art_nid,
            }
        )

    for rel in rel_inputs:
        rel_p = rel.replace("\\", "/")
        if not (rel_p.startswith("UPG/") or "/artifacts/" in rel_p):
            continue
        src_nid = _node_id_for_path(rel_p)
        is_upg = rel_p.startswith("UPG/") and rel_p.endswith(".md")
        is_art = "/artifacts/" in rel_p
        if not (is_upg or is_art):
            continue
        if rel_p.endswith(".json"):
            raw_t = _read_text_normalized(iroot_r, rel_p, None)
            bpaths, jerr = _blast_paths_from_json(raw_t)
            if jerr and not bpaths:
                reasons.append(
                    {"edge_kind": "blast_radius", "reason_code": jerr, "detail": rel_p}
                )
                continue
        else:
            raw_t = _read_text_normalized(iroot_r, rel_p, None)
            bpaths = _blast_paths_from_markdown(raw_t)
        for bp in bpaths:
            rp = _resolve_under_root(iroot_r, rel_p, bp)
            if not rp:
                raise ValueError(
                    f"blast_radius path escape or missing file: {bp!r} (from {rel_p})"
                )
            rel_target = str(rp.relative_to(iroot_r)).replace("\\", "/")
            fnid = _node_id_for_path(rel_target)
            if fnid not in node_ids:
                nodes.append(
                    {
                        "id": fnid,
                        "kind": "file",
                        "path": rel_target,
                        "label": PurePosixPath(rel_target).name,
                        "classification": "evidence",
                        "lane_tags": lane_tags_for_path(rel_target),
                    }
                )
                node_ids.add(fnid)
                edges.append(
                    {
                        "id": f"e-contains-{fnid}",
                        "kind": "contains",
                        "from": INPUT_REPO_NODE,
                        "to": fnid,
                    }
                )
            edges.append(
                {
                    "id": f"e-blast-{src_nid}-{fnid}",
                    "kind": "blast_radius",
                    "from": src_nid,
                    "to": fnid,
                }
            )

    for rel in rel_inputs:
        rel_p = rel.replace("\\", "/")
        if not (rel_p.endswith(".md") or rel_p.endswith(".json")):
            continue
        text = _read_text_normalized(iroot_r, rel_p, None)
        tgt, derr = _parse_derived_target(text)
        if derr:
            reasons.append(
                {"edge_kind": "derived_from", "reason_code": derr, "detail": rel_p}
            )
            continue
        if not tgt:
            continue
        src_nid = _node_id_for_path(rel_p)
        rp = _resolve_under_root(iroot_r, rel_p, tgt)
        if not rp:
            reasons.append(
                {
                    "edge_kind": "derived_from",
                    "reason_code": "derived_unresolved",
                    "detail": rel_p,
                }
            )
            continue
        rel_target = str(rp.relative_to(iroot_r)).replace("\\", "/")
        if rel_target not in rel_inputs:
            reasons.append(
                {
                    "edge_kind": "derived_from",
                    "reason_code": "derived_target_not_indexed",
                    "detail": rel_target,
                }
            )
            continue
        tnid = _node_id_for_path(rel_target)
        sk = next(n["kind"] for n in nodes if n["id"] == src_nid)
        tk = next(n["kind"] for n in nodes if n["id"] == tnid)
        if sk not in ("upg", "artifact") or tk not in ("upg", "artifact"):
            continue
        edges.append(
            {
                "id": f"e-derived-{src_nid}-{tnid}",
                "kind": "derived_from",
                "from": src_nid,
                "to": tnid,
            }
        )

    for a, b in cfg.AUTHORITY_PRECEDENCE_PAIRS:
        if a in node_ids and b in node_ids:
            edges.append(
                {
                    "id": f"e-prec-{a}-{b}",
                    "kind": "precedes",
                    "from": a,
                    "to": b,
                }
            )

    for rel in rel_inputs:
        rel_p = rel.replace("\\", "/")
        slug_art = _slug_from_artifact_rel(rel_p)
        if not slug_art or slug_art not in upg_slug_to_nid:
            continue
        upg_nid = upg_slug_to_nid[slug_art]
        art_nid = _node_id_for_path(rel_p)
        if not any(
            e["kind"] == "has_artifact" and e["from"] == upg_nid and e["to"] == art_nid
            for e in edges
        ):
            raise ValueError(
                "EKG_HAS_ARTIFACT_MISSING: slug-linked artifact without has_artifact edge "
                + rel_p
            )

    counts: dict[str, int] = {k: 0 for k in ALL_EDGE_KINDS}
    for e in edges:
        counts[e["kind"]] = counts.get(e["kind"], 0) + 1

    cond_kinds = ("parent_of", "authorizes", "precedes", "blast_radius", "derived_from")
    for ck in cond_kinds:
        if counts.get(ck, 0) == 0:
            code = "no_markers_found"
            if ck == "precedes":
                code = (
                    "config_empty"
                    if not cfg.AUTHORITY_PRECEDENCE_PAIRS
                    else "no_peer_authority_node"
                )
            if ck == "blast_radius":
                code = "no_parseable_declaration"
            if not any(r.get("edge_kind") == ck for r in reasons):
                reasons.append({"edge_kind": ck, "reason_code": code, "detail": "aggregate"})

    lane_tag_counts: dict[str, int] = {}
    for n in nodes:
        for t in n.get("lane_tags") or []:
            lane_tag_counts[t] = lane_tag_counts.get(t, 0) + 1

    graph_id = "g-" + hashlib.sha256(("|".join(sorted(rel_inputs))).encode()).hexdigest()[:12]
    graph: dict[str, Any] = {
        "schema_version": "tmgekg.graph.v0_1",
        "graph_id": graph_id,
        "generated_at_utc": generated_at,
        "upg_authority": cfg.PHASE1C_UPG_AUTHORITY,
        "parent_upg_authority": cfg.PHASE1C_PARENT_UPG_AUTHORITY,
        "nodes": nodes,
        "edges": edges,
    }
    return Phase1cBuild(
        graph=graph,
        edge_type_counts=counts,
        conditional_edge_zero_reasons=reasons,
        lane_tag_counts=lane_tag_counts,
    )
