"""CLI entrypoint for static Agent Context Pack generation."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .builder import build_context_pack


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="tmg-ekg-context-pack",
        description="Generate static Agent Context Pack from one Phase 1C graph/evidence pair.",
    )
    parser.add_argument("--run-id", required=True, help="Bound RUN_ID under data/index_runs/<RUN_ID>/")
    parser.add_argument(
        "--repo-root",
        default=".",
        help="Implementation repository root (default: current directory).",
    )
    args = parser.parse_args()

    try:
        result = build_context_pack(Path(args.repo_root).resolve(), str(args.run_id))
    except (FileNotFoundError, ValueError, OSError) as exc:
        print(f"FAIL_CLOSED: {exc}", file=sys.stderr)
        return 2

    print(f"markdown: {result.markdown_path}")
    print(f"json: {result.json_path}")
    print(f"node_count: {result.node_count}")
    print(f"edge_count: {result.edge_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
