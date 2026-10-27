# House of Velvet — build continuation

Original IP: **5 Nights at Velvet's** (Neo / Cosmic Funk Studios). A condemned 1980s fashion house where undead runway models of every size (thin, thick, BBW) still walk after midnight. Spielberg-restraint horror.

This directory continues the live GathrXR primitive build through this repo's SKILL.md pipeline, upgrading it to a proper Blender-authored GLB environment.

## Status

| Gate | Status |
|---|---|
| G1 architecture | blockout script written, pending headless run |
| G2 composition | pending |
| G3 appearance | pending |
| G4 performance/export | pending |

- Live playable world (primitive build, 124 objects): GathrXR world `6edf4e41-e136-49da-acdf-2ed6d07d44ca`
- Spec: `world_spec.json`
- Build: `build_house_of_velvet.py` (headless Blender / bpy module)
- Outputs: `out/house_of_velvet.blend`, `out/house_of_velvet.glb`, `out/preview_hero.png`, `out/metrics.json`

## Zones

Showroom with runway catwalk and collapsed-roof moonbeam, twin camera halls, security office (spawn) with floor vent, supply closet, backstage wardrobe, overexposed makeup room (LIGHT), cold storage (DARK), barred freight gate, service ramp to level 2, the Atelier lab (specimen tanks, dress forms in three sizes), Director's office, half-open lab gate.

## Reference images

Generated with Kling 3.0 Omni, locked character sheet (Seraphine / Madame Volta / Duchess Pearl):
- house-models-keyart-9x16.png
- volta-makeup-room-16x9.png
- atelier-lab-16x9.png

## Runtime testing

NOT yet performed in GathrXR/WebXR. GLB export success does not mean runtime readiness (per SKILL.md delivery rules).
