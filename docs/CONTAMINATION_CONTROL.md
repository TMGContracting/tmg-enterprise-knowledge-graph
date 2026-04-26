# Contamination control — TMG Enterprise Knowledge Graph (read-only index)

**UPG:** `UPG-GOV-TMG-EKG-READONLY-INDEX-PROTOTYPE-001`  
**Repository:** `TMGContracting/tmg-enterprise-knowledge-graph`

This document satisfies the **mandatory contamination-control statement** in the child UPG (Section 7).

## Binding commitments

1. **No upstream GitNexus tree** in this workspace: no Git submodule, no `vendor/` copy, and no mirrored source tree from the public `abhigyanpatwari/GitNexus` repository (or any fork of it).

2. **No source-code copying** from GitNexus: no line-by-line or structural copy of its implementation.

3. **No exact reproduction** of GitNexus CLI commands, MCP tool names, wire formats, generated artifact shapes, or indexing heuristics taken from that project.

4. **TMG-native requirements only:** behavior and data shapes are defined by TMG governance UPGs, this repository’s JSON Schemas (`schemas/`), and the Phase 1 feasibility packet — not by re-implementing GitNexus.

5. **Future MCP naming (planning only):** reserved tool namespace prefix **`tmg.ekg.*`** may appear in documentation for a **future** MCP phase. **No** MCP server, listener, or production MCP registration is implemented under the current child UPG scope.

6. **No GitNexus package dependency:** `pyproject.toml` and lockfiles must not declare dependencies on GitNexus or packages that bundle its code.

7. **Default no network:** the read-only indexer must not open network connections unless a future UPG-approved feasibility revision explicitly documents justified exceptions.

## Review

Any PR that introduces paths outside the child UPG **Section 5.1** closed set, adds a GitNexus-related dependency, or adds MCP server runtime code is **out of scope** and must be rejected pending UPG amendment.
