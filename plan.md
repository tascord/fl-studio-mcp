# FL Studio MCP roadmap

## Goal
Extend the MCP from low-level studio controls toward higher-value DAW workflows that are more natural for AI-assisted music production.

## Priority 1: Arrangement and playlist clip operations
- Add tooling to inspect playlist structure, selected arrangement ranges, and clip metadata.
- Support inserting or moving pattern clips on the playlist timeline.
- Allow AI agents to read arrangement state before making composition decisions.

## Priority 2: Automation lane support
- Add automation lane discovery and inspection.
- Allow reading and writing automation points for plugin and mixer parameters.
- Expose automation state through a compact, AI-friendly format.

## Priority 3: Project state snapshots
- Save named snapshots of the current project state for versioned experiments.
- Restore a snapshot without manually redoing work.
- Store enough metadata to compare arrangement, mixer, and pattern changes over time.

## Delivery sequence
1. Add the missing playlist/arrangement primitives in the controller and MCP layer.
2. Expose compact automation lane inspection and editing commands.
3. Add project snapshot save/restore helpers and a lightweight state model.
4. Validate with Python syntax checks and document usage examples.

## Notes
The current server already covers transport, mixer, channels, plugins, and pattern/song markers well. The missing value is the arrangement and automation layer, which is where AI-driven composition workflows become significantly more useful.
