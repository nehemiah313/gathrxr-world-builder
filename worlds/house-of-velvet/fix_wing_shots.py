"""Reposition the two wing cameras inside their rooms and re-render just those shots."""
import math, os, bpy
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
bpy.ops.wm.open_mainfile(filepath=os.path.join(OUT, "house_of_velvet.blend"))
sc = bpy.context.scene
L2 = 4.6

def place(name, gx, gy, gz, lens, pitch, yaw):
    c = bpy.data.objects[name]
    c.location = (gx, -gz, gy)
    c.rotation_euler = (math.radians(pitch), 0, math.radians(yaw))
    c.data.lens = lens
    return c

# inside the atelier, back corner, looking north-west across tanks + dress-form row
place("cam_atelier", 16.6, L2 + 1.75, 9.7, 20, 88, 35)
# inside the doorway, looking east into the inverted room
place("cam_inverted", 18.0, L2 + 1.9, 6.0, 18, 90, -90)

sc.render.engine = "BLENDER_EEVEE"
try: sc.eevee.taa_render_samples = 10
except AttributeError: pass
sc.view_settings.view_transform = "Standard"

for cam, fname, expo in [("cam_atelier", "preview_atelier.png", -0.6),
                         ("cam_inverted", "preview_inverted.png", -0.7)]:
    sc.camera = bpy.data.objects[cam]
    sc.render.resolution_x, sc.render.resolution_y = 768, 432
    sc.view_settings.exposure = expo
    sc.render.filepath = os.path.join(OUT, fname)
    try:
        bpy.ops.render.render(write_still=True)
        print("RENDERED", fname, flush=True)
    except Exception as e:
        print("FAIL", fname, e, flush=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "house_of_velvet.blend"))
print("DONE")
