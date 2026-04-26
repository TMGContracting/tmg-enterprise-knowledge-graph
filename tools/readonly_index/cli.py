"""CLI for tmg-ekg-index: read-only governance index (no network, no mutating git, no MCP)."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from . import config as cfg
from . import indexer
from . import validation as V

try:
    from importlib.metadata import version as pkg_version
except ImportError:  # pragma: no cover
    pkg_version = lambda _n: "0.0.0"  # type: ignore[assignment, misc]


def _tool_version() -> str:
    try:
        return pkg_version("tmg-enterprise-knowledge-graph")
    except Exception:  # noqa: BLE001
        return "0.0.0"


def _arg_input_root(p: argparse.ArgumentParser) -> None:
    p.add_argument(
        "--input-root",
        type=Path,
        default=None,
        metavar="DIR",
        help=f"Governance repo root (or set {cfg.ENV_INPUT_ROOT})",
    )
    p.add_argument(
        "--output-parent",
        type=Path,
        default=Path("data/index_runs"),
        metavar="DIR",
        help="Write runs under <DIR>/<RUN_ID>/ (default: data/index_runs)",
    )


def cmd_run(args: argparse.Namespace) -> int:
    if args.input_root is not None:
        root: Path = args.input_root
    else:
        env = os.environ.get(cfg.ENV_INPUT_ROOT)
        if not env or not str(env).strip():
            print(
                f"Missing --input-root or {cfg.ENV_INPUT_ROOT} (EKG governance clone root).",
                file=sys.stderr,
            )
            return 2
        root = Path(env)
    try:
        r = indexer.run_index(root, args.output_parent, _tool_version())
    except (FileNotFoundError, NotADirectoryError) as e:
        print(f"EKG read-only index: {e}", file=sys.stderr)
        return 2
    except (OSError, ValueError, RuntimeError) as e:
        print(f"EKG read-only index (fail-closed): {e}", file=sys.stderr)
        return 2
    out_root = V.repo_root()
    try:
        g_rel = r.graph_path.resolve().relative_to(out_root)
        e_rel = r.evidence_path.resolve().relative_to(out_root)
    except ValueError:
        g_rel, e_rel = r.graph_path, r.evidence_path
    print(f"run_id: {r.run_id}")
    print(f"inputs: {r.input_count}")
    print(f"graph:  {g_rel}")
    print(f"evid:   {e_rel}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="tmg-ekg-index",
        description="TMG EKG read-only index (governance) — UPG " + cfg.UPG_AUTHORITY,
    )
    sub = parser.add_subparsers(dest="command", required=True)

    runp = sub.add_parser("run", help="Index allowed globs under a governance clone (read-only)")
    _arg_input_root(runp)
    runp.set_defaults(func=cmd_run)

    args = parser.parse_args()
    if args.command == "run":
        return int(args.func(args))
    return 2
