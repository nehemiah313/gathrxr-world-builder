# GathrXR World Builder Skill

Codex skill for building, revising, validating, and optimizing Blender environments for GathrXR WebXR from reference images.

See [SKILL.md](SKILL.md) for the complete workflow, export checks, performance gates, and delivery requirements.

## Install locally

Place this repository's contents in `~/.codex/skills/gathrxr-world-builder/` so that `SKILL.md` is directly inside that directory.

The skill describes a workflow; it does not bundle Blender, world assets, runtime integrations, or custom agent definitions. Its optional `gathr-sol-worker` role must be configured separately if used. Blender and the project's build tools must already be available.

## Scope

Includes reference interpretation, headless Blender construction, image-based materials, GLB export, collision separation, optimization, and validation. Actual GathrXR/headset testing is required before claiming runtime readiness.
