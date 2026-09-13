#!/usr/bin/env python3
# -----------------------------------------------------------------------------
# Role: Verifies MCP capability block behavior for the MCP block.
# File Name: F5.16_mcp_capability_block.py
# Author: Alexandre EL
# Email: alex@hackinvent.com
# Created Date: 2024-11-15
# -----------------------------------------------------------------------------

"""F5.16 - MCP capability block.

The test calls McpBlock directly to verify MCP registry resolution and runtime
capability emission without starting external MCP servers.
"""

# Test cases:
# - FB1 - Resolve an MCP registry reference through the supplied resolver service.
# - FB2 - Execute the block and verify it emits a capability/mcp output.
# - FB3 - Render MCP inspector choices from the available registry refs.
# - FB4 - Verify a missing MCP reference produces a clear configuration error.

from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace

from ui_smoke_common import expect
from blocs.mcp.block import McpBlock
from bloxsmith_app.block_runtime import BlockRuntimeContext
from bloxsmith_app.block_ui import render_block_modal


def context(root: Path, config: dict) -> BlockRuntimeContext:
    return BlockRuntimeContext(
        run_id="test-run",
        node_id="mcp-1",
        kind="mcp",
        title="MCP",
        config=config,
        inputs={},
        input_content_types={},
        input_message="",
        input_ports=(),
        output_ports=(SimpleNamespace(id=1, name="mcp"),),
        root_dir=root,
    )


def test_mcp_modal_uses_generic_surface_contract() -> None:
    """TC5 - MCP modal stays a simple generic surface without block JS."""

    rendered = render_block_modal("mcp", {"node": {"id": "mcp-1", "kind": "mcp", "title": "MCP", "config": {"mcp_ref": "docs"}}, "runtime": {}})
    html = str(rendered.get("html") or "")
    assets = rendered.get("assets") or []

    expect("block-config-modal" in html, "MCP modal must use the generic config layout.")
    expect("data-block-apply" in html, "MCP modal must keep generic Apply persistence.")
    expect("data-block-runtime-refresh" not in html, "MCP modal must not claim autonomous refresh without block JS.")
    expect(assets == [], "MCP modal must not declare block JS while it has no custom interaction.")


def main() -> None:
    test_mcp_modal_uses_generic_surface_contract()
    block = McpBlock()

    resolved = block.resolve_config(
        {"mcp_ref": "docs"},
        resolver=lambda ref: {"mcp_ref": ref, "name": "Docs MCP", "url": "http://example.invalid/mcp"},
    )
    expect(resolved["name"] == "Docs MCP", "MCP resolver result must be used.")
    expect(block.config_label(resolved) == "Docs MCP (http://example.invalid/mcp)", "MCP label mismatch.")
    rendered = block.render_inspector_panel(
        node={"id": "mcp-1", "kind": "mcp", "title": "MCP", "config": {"mcp_ref": "docs"}},
        payload={"mcp_server_refs": [{"ref": "docs", "name": "Docs MCP"}, {"ref": "search", "name": "Search MCP"}]},
    )
    html = str(rendered.get("html") or "")
    expect("docs · Docs MCP" in html and 'value="docs" selected' in html, "MCP inspector must render and select registry refs.")

    with TemporaryDirectory(prefix="bloxsmith-mcp-test-") as tmp:
        result = block.execute_runtime(context(Path(tmp), resolved))
    expect(result.status == "success", "MCP runtime execution must succeed.")
    expect(result.outputs[0].content_type == "capability/mcp", "MCP output content type mismatch.")
    expect(result.metadata.get("mcp_ref") == "docs", "MCP metadata must keep the resolved ref.")

    try:
        block.resolve_config({})
    except ValueError as exc:
        expect("mcp_ref" in str(exc), "Missing MCP reference error must mention mcp_ref.")
    else:
        raise AssertionError("Missing MCP reference must fail.")
    print("[ok] F5.16_mcp_capability_block")


if __name__ == "__main__":
    main()
