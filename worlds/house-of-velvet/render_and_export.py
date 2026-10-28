"""Render + export from the saved House of Velvet scene.

Split out of the main build because headless EEVEE needs an EGL/GPU context that
intermittently fails in this container (EGL_BAD_MATCH). The GLB export needs no
context at all, so it runs first and always succeeds; rendering then tries EEVEE
and falls back to Cycles on CPU, which needs no GPU.
"""
import json
import os

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")

bpy.ops.wm.open_mainfile(filepath=os.path.join(OUT, "house_of_velvet.blend"))
scene = bpy.context.scene

# ---- 1. GLB export (no graphics context required) ----
bpy.ops.export_scene.gltf(
    filepath=os.path.join(OUT, "house_of_velvet.glb"),
    export_format="GLB",
    export_lights=False,
    export_apply=True,
    export_yup=True,
)
print("GLB_EXPORTED")

# ---- 2. renders ----
SHOTS = [("cam_hero", "preview_hero.png", 540, 960, -0.75),
         ("cam_atelier", "preview_atelier.png", 768, 432, -1.9),
         ("cam_inverted", "preview_inverted.png", 768, 432, -2.1)]


def configure(engine):
    scene.render.engine = engine
    if engine == "CYCLES":
        scene.cycles.device = "CPU"
        scene.cycles.samples = 24
        scene.cycles.use_denoising = True
        scene.cycles.max_bounces = 4
        scene.cycles.transmission_bounces = 2
        scene.cycles.transparent_max_bounces = 4
    else:
        try:
            scene.eevee.taa_render_samples = 10
        except AttributeError:
            pass


def shoot(engine):
    configure(engine)
    ok = []
    for cam_name, fname, rx, ry, expo in SHOTS:
        cam = bpy.data.objects.get(cam_name)
        if not cam:
            continue
        scene.camera = cam
        scene.render.resolution_x, scene.render.resolution_y = rx, ry
        scene.view_settings.view_transform = "Standard"
        scene.view_settings.exposure = expo
        path = os.path.join(OUT, fname)
        before = os.path.getmtime(path) if os.path.exists(path) else 0
        scene.render.filepath = path
        try:
            bpy.ops.render.render(write_still=True)
        except Exception as e:
            print("RENDER_FAIL", engine, fname, e)
            continue
        after = os.path.getmtime(path) if os.path.exists(path) else 0
        if after > before:
            ok.append(fname)
            print("RENDERED", engine, fname, flush=True)
    return ok


done = shoot("BLENDER_EEVEE")
if len(done) < len(SHOTS):
    print("EEVEE incomplete, falling back to Cycles CPU", flush=True)
    done = list(set(done) | set(shoot("CYCLES")))

tri = 0
for o in bpy.data.objects:
    if o.type == "MESH":
        o.data.calc_loop_triangles()
        tri += len(o.data.loop_triangles)

report = {
    "objects": len([o for o in bpy.data.objects if o.type == "MESH"]),
    "triangles": tri,
    "materials": len(bpy.data.materials),
    "glb_bytes": os.path.getsize(os.path.join(OUT, "house_of_velvet.glb")),
    "rendered": sorted(done),
}
with open(os.path.join(OUT, "render_report.json"), "w") as f:
    json.dump(report, f, indent=2)
print("DONE", json.dumps(report))
