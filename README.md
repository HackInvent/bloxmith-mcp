# MCP Block

<!-- block-metadata:start -->
[![Block version: 0.1.0](https://img.shields.io/badge/block-0.1.0-blue)](model.json)
[![BloxSmith compatibility: 1.0.9](https://img.shields.io/badge/BloxSmith-1.0.9-brightgreen)](compatibility.json)
[![License: Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-blue)](LICENSE)

Verified BloxSmith versions: **1.0.9** (bundled-block tests; see [test evidence](compatibility.json)).
<!-- block-metadata:end -->


## Role

`mcp` exposes a configured MCP server as a runtime capability for downstream blocks, especially Codex blocks.

## Files

- `block.py`: MCP reference resolution, capability payload emission, and inspector rendering.
- `model.json`: default MCP reference and capability output.
- `node_card.html`: canvas card body rendered by the block-owned UI contract.
- `inspector_panel.html`: MCP selector UI.

## Ports

- Outputs:
  - `mcp` (`id: 1`): emits `capability/mcp`.

The block has no inputs.

## Configuration

- `mcp_ref`: logical reference to an MCP server defined in the MCP registry/configuration.

The block must not store server URLs, headers, or secrets in graph documents.

## Runtime Behavior

`build_runtime_config()` resolves `mcp_ref` through the injected MCP registry service.

`execute_runtime()` emits the normalized MCP capability reference as
`capability/mcp`. The runtime manifest marks `mcp` as a generic source and MCP
provider for both centralized graph binding and active runtime wiring.

## UI Behavior

The canvas card and inspector are both rendered from templates owned by this
block. The inspector renders available MCP refs from the payload and lets the
user choose the configured reference. Reference changes are kept pending while
edited and are persisted through the GraphController only when the user clicks
**Apply**.

## Modal

`block_modal.html` is owned by this block and rendered by the generic modal contract. It shows block state and lets users edit supported title/config fields through generic bindings. It intentionally does not declare autonomous refresh or block-owned modal JavaScript because the modal has no custom interaction beyond generic Apply; registry-specific selection remains in the inspector template.

## Maintenance Notes

Keep secrets out of the graph. Any new MCP field should be resolved from registry state at runtime, not persisted in node config.

## Compatibility policy

[compatibility.json](compatibility.json) records HackInvent's verified BloxSmith versions and test evidence. Only the versions listed above have been verified, using the block-owned suites in a **bundled-block test installation**. This is not a certification of managed-package installation, every browser/OS, or live provider availability. Other framework versions are unverified, not necessarily incompatible.

The block-version badge follows `model.json`, not a published Git tag. `unversioned` means that no block release version is declared; no number is inferred from the framework version. The framework still uses `model.json` for its runtime/install contract; the tester-owned JSON does not replace it. Official integration tests run in the private `bloxmith-blocs` workspace. Test helpers and the proprietary framework are not bundled in this public block repository.
