"""STUB ONLY — CLI entry for tmg-ekg-index. No scans, no network, no MCP."""

from __future__ import annotations

import sys


def main() -> int:
    if len(sys.argv) > 1 and sys.argv[1] in ("-h", "--help"):
        print(
            "tmg-ekg-index — TMG Enterprise Knowledge Graph read-only index (STUB ONLY).\n"
            "No indexing, no MCP server. See README.md."
        )
        return 0
    print(
        "STUB ONLY: indexing is not enabled. "
        "See README.md and docs/feasibility/PHASE1_FEASIBILITY_PACKET.md.",
        file=sys.stderr,
    )
    return 2
