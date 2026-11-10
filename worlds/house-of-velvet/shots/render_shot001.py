"""Render Shot 001 blocking frames from the saved scene, Cycles CPU (no GPU context)."""
import os, bpy
HERE=os.path.dirname(os.path.abspath(__file__))
OUT=os.path.join(HERE,"out"); os.makedirs(OUT,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE,"shot001_runway_walk.blend"))
sc=bpy.context.scene
sc.render.engine="CYCLES"; sc.cycles.device="CPU"; sc.cycles.samples=16
sc.cycles.use_denoising=True; sc.cycles.max_bounces=3
sc.view_settings.view_transform="Standard"; sc.view_settings.exposure=-0.75
sc.render.resolution_x,sc.render.resolution_y=432,768
cam=bpy.data.objects.get("cam_hero"); sc.camera=cam
for f in [1,30,60,90,120]:
    sc.frame_set(f); sc.render.filepath=os.path.join(OUT,f"s001_f{f:03d}.png")
    bpy.ops.render.render(write_still=True); print("FRAME",f,flush=True)
print("DONE")
