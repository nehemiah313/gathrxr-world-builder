---
name: gathrxr-world-builder
description: Build, revise, validate, and optimize Blender environments from reference images for GathrXR WebXR. Use for headless Blender world creation, GLB export, scene matching, reusable assets, and performance optimization.
---

# GathrXR reference-to-world production

Use the existing project's proven WebXR pipeline and export settings. Do not replace working materials, coordinate conventions, collisions, or GLB conventions without a specific reason.

## Inputs
Reference image(s), requested world type, known dimensions, existing asset library, platform limits (if measured), output directory. Record assumptions about unseen geometry and dimensions; do not claim to reconstruct hidden parts exactly.

## Model routing
- **Astra lead**: reference interpretation, ambiguous architecture, multi-level spatial planning, camera matching, difficult failures, and final visual assessment.
- **Sol worker**: routine Blender Python implementation, procedural furniture and modular props, materials and UVs, scene population, routine bug fixes, and export scripts.
- **Deterministic Python/Blender (no model)**: execute headless builds, count triangles, verify files, render previews, inspect missing textures, reimport GLB, and write metrics.
- If Codex supports custom subagents, delegate bounded implementation tasks to `gathr-sol-worker`; otherwise keep execution in the active model and clearly report that model routing was not performed. Do not claim to have used Sol unless it actually ran.
- Avoid unnecessary parallel agents; they incur independent token costs. Keep agents from editing the same files concurrently.

## Workflow
1. **Inspect** existing repository, build scripts, assets, target WebXR runtime, and reference. Reuse proven conventions. Make a compact `world_spec.json` with dimensions, object list, scene graph, materials, camera, assumptions, and budget.
2. **Plan** geometry and prioritize silhouette, room proportions, levels, windows, stairs, focal points, and reference camera. Astra resolves ambiguous structure; Sol can implement the approved plan.
3. **Blockout** headlessly with reusable Python functions. Save a checkpoint `.blend` and low-resolution camera preview. Validate geometry and scale before detail.
4. **Populate** with linked meshes and existing assets. Assign Sol independent, clearly scoped assets/scripts. Keep generated modules reusable and avoid re-creating common objects.
5. **Shade/light** using WebXR-compatible PBR materials and tested export conventions. Use baked detail where appropriate. Never assume Blender-only shaders, lights, or effects will export to GLB.
6. **Compare** reference and preview. Have Astra identify the three largest *actionable* visual discrepancies, then give Sol narrowly scoped fixes. At most two automatic correction cycles per gate; stop for user approval when still off-target.
7. **Optimize** against measured runtime budgets where available. Otherwise use configurable provisional budgets. Inspect triangles, materials, texture memory, instances, draw-call proxies, normals, UVs, and collision mesh separation. Preserve visual fidelity.
8. **Export** `.blend`, `.glb`, preview images, `world_spec.json`, manifest, and performance report. Reimport GLB in a clean scene and validate visible geometry and material assignments. If runtime access exists, test in WebXR; otherwise explicitly state runtime testing was not performed.

## Gates
- G1 architecture: proportions, navigation, major levels, camera.
- G2 composition: primary assets and focal points.
- G3 appearance: materials, color, lighting, visual fidelity.
- G4 performance/export: geometry, texture, GLB compatibility, reimport.

## Cost discipline
- Keep an iteration log of model, task, measured usage if available, and results. Never invent token or dollar totals.
- Favor deterministic scripts over model calls; avoid rereading unchanged code and reanalyzing references.
- Use previews around 640x360 for iteration; higher resolution only for approved review.
- Save checkpoints before changes and patch only affected objects/scripts.
- Honor configured cost or iteration caps. If no reliable monetary usage API exists, enforce iteration caps and flag monetary budget as unverified.

## Delivery
Report artifact paths, reference-match limitations, counts, validation status, and whether actual WebXR testing occurred. Do not say a world is fully WebXR-ready solely because Blender export succeeded.
