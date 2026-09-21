# -----------------------------------------------------------------------------
# Role: Implements the MCP block runtime and UI contract.
# File Name: block.py
# Author: Alexandre EL
# Email: alex@hackinvent.com
# Created Date: 2024-10-09
# -----------------------------------------------------------------------------

from __future__ import annotations

from html import escape
from typing import Any

from bloxsmith_app.block_api import (
    BlockDefinition,
    BlockRuntimeContext,
    BlockRuntimeOutput,
    BlockRuntimeResult,
    render_inspector_template,
    render_node_card_template,
)

# The framework stopped exporting this port type when MCP configuration moved to
# the studio. The block keeps the historical value so existing graphs stay loadable.
CAPABILITY_MCP = "capability/mcp"


# Functional behavior:
# FB1 - Resolve an MCP server reference from the project registry.
# FB2 - Emit the resolved MCP capability name/ref as capability/mcp.
# FB3 - Render MCP inspector choices from the available registry refs.
# FB4 - Fail early with a clear configuration error when no MCP reference is available.
class McpBlock(BlockDefinition):
    """Autonomous block implementation for `McpBlock`."""
    kind = "mcp"

    def ui_assets(self, surface: str = "modal") -> list[dict[str, str]]:
        """Return block-owned frontend assets for the requested UI surface.

        Args:
            surface: UI surface requesting assets.
        """
        return []

    def render_node_card(self, *, node: dict[str, Any], payload: dict[str, Any] | None = None) -> dict[str, Any]:
        """Render the MCP canvas card body from the block-owned template.

        Args:
            node: Serialized MCP node being rendered.
            payload: Optional UI payload, currently unused by the card.

        Returns:
            Block UI payload used by the generic canvas shell.
        """

        config = self._ui_config(node)
        ref = self.ref_from_config(config)
        return render_node_card_template(
            block=self,
            node=node,
            node_classes=["mcp-node"],
            replacements={
                "title": node.get("title") or self.default_title(),
                "ref": ref or "missing mcp_ref",
                "summary": "Obsolete · compatibilite temporaire",
            },
        )

    def render_inspector_panel(self, *, node: dict[str, Any], payload: dict[str, Any] | None = None) -> dict[str, Any]:
        """Render the MCP inspector panel with registry reference options.

        Args:
            node: Serialized MCP node being inspected.
            payload: Optional UI payload containing available MCP registry references.

        Returns:
            Inspector HTML plus context for the frontend shell.
        """

        ref = self.ref_from_config(self._ui_config(node))
        template = (self.directory / "inspector_panel.html").read_text(encoding="utf-8")
        html = render_inspector_template(
            template=template.replace("{{ mcp_options }}", self._render_mcp_options(ref, payload or {})),
            node={**node, "type": self.kind, "kind": self.kind},
            payload=payload,
        )
        return {"html": html, "context": {"node_id": str(node.get("id") or ""), "full_panel": True}}

    def _ui_config(self, node: dict[str, Any]) -> dict[str, Any]:
        """Return the MCP config object used by UI renderers.

        Args:
            node: Serialized MCP node from the graph document or frontend state.

        Returns:
            Canonical node config.
        """

        return node.get("config") if isinstance(node.get("config"), dict) else {}

    def _render_mcp_options(self, selected_ref: str, payload: dict[str, Any]) -> str:
        """Render select options for configured MCP registry references.

        Args:
            selected_ref: MCP ref currently configured on the node.
            payload: Inspector payload that may contain ``mcp_server_refs``.

        Returns:
            HTML option markup for the inspector select.
        """

        servers = payload.get("mcp_server_refs") if isinstance(payload.get("mcp_server_refs"), list) else []
        if not servers:
            return '<option value="">No MCP configured</option>'
        options = []
        for server in servers:
            if not isinstance(server, dict):
                continue
            ref = str(server.get("ref") or "").strip()
            if not ref:
                continue
            name = str(server.get("name") or ref)
            label = f"{ref} · {name}" if name and name != ref else ref
            options.append(f'<option value="{escape(ref)}"{" selected" if ref == selected_ref else ""}>{escape(label)}</option>')
        return "\n".join(options) or '<option value="">No MCP configured</option>'

    def build_runtime_config(self, *, node: Any, config: dict[str, Any], **runtime_services: Any) -> dict[str, Any]:
        """Resolve the runtime MCP configuration through the injected registry service.

        Args:
            node: Runtime node object, kept for the block runtime contract.
            config: Persisted node config containing the MCP reference.
            runtime_services: Services provided by the orchestrator, including the resolver.

        Returns:
            Resolved MCP configuration used by downstream Codex/MCP integration.
        """

        resolver = runtime_services.get("mcp_registry_resolver")
        return self.resolve_config(config, resolver=resolver)

    def preview_received(self, *, node: Any, **runtime_services: Any) -> str:
        """Return a human-readable MCP label for worker previews.

        Args:
            node: Runtime node object whose config identifies the MCP ref.
            runtime_services: Optional registry resolver service.

        Returns:
            Resolved MCP label, or a clear fallback when the ref is missing/unresolved.
        """

        config = getattr(node, "config", {}) if isinstance(getattr(node, "config", {}), dict) else {}
        try:
            resolved = self.build_runtime_config(node=node, config=config, **runtime_services)
            return self.config_label(resolved)
        except Exception:
            ref = self.ref_from_config(config)
            return f"{ref or 'missing mcp_ref'} (not configured)"

    def resolve_config(self, config: dict[str, Any], *, resolver: Any = None) -> dict[str, Any]:
        """Resolve a persisted MCP reference into a runtime configuration.

        Args:
            config: Persisted MCP block config.
            resolver: Optional callable that resolves a registry ref.

        Returns:
            Runtime MCP configuration including ``mcp_ref``.

        Raises:
            ValueError: If no registry reference is present.
        """

        mcp_ref = self.ref_from_config(config)
        if mcp_ref and callable(resolver):
            return resolver(mcp_ref)
        if mcp_ref:
            resolved = dict(config)
            resolved["mcp_ref"] = mcp_ref
            return resolved

        raise ValueError("MCP node without mcp_ref. Configure the MCP block with a registry reference.")

    def ref_from_config(self, config: dict[str, Any]) -> str:
        """Extract the normalized MCP reference from a config object."""

        return str(config.get("mcp_ref") or "").strip()

    def config_label(self, config: dict[str, Any]) -> str:
        """Return a compact label for a resolved MCP configuration."""

        name = str(config.get("name") or config.get("mcp_ref") or "mcp_server").strip() or "mcp_server"
        url = str(config.get("url") or "").strip()
        return f"{name} ({url or 'URL not defined'})"

    def execute_runtime(self, context: BlockRuntimeContext) -> BlockRuntimeResult:
        """Emit the configured MCP capability reference on every output port.

        Args:
            context: Runtime context with resolved MCP config and output ports.

        Returns:
            Runtime result publishing the MCP capability for downstream blocks.
        """

        name = self._mcp_name(context.config)
        outputs = [
            BlockRuntimeOutput(
                port_id=int(getattr(port, "id", 0) or 0),
                port_name=str(getattr(port, "name", "") or ""),
                value=name,
                content_type=CAPABILITY_MCP,
            )
            for port in context.output_ports
        ]
        return BlockRuntimeResult(
            status="success",
            outputs=outputs,
            logs=[f"[mcp] {context.node_id}: MCP reference '{name}' emitted."],
            last_message=name,
            content_type=CAPABILITY_MCP,
            worker_received=name,
            metadata={"mcp_ref": str(context.config.get("mcp_ref") or name)},
        )

    def _mcp_name(self, config: dict[str, Any]) -> str:
        """Return the runtime MCP capability name from a resolved config."""

        return str(
            config.get("name")
            or config.get("mcp_ref")
            or "mcp_server"
        ).strip() or "mcp_server"
