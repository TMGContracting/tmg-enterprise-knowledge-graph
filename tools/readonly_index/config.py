"""STUB ONLY — configuration for read-only indexer (allowlists to be implemented)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ReadOnlyIndexConfig:
    """Allowlisted filesystem roots. Empty tuple means no scan is permitted (fail-closed)."""

    roots: tuple[Path, ...] = ()
