"""Shot 001 - RUNWAY WALK (previz animatic).

Merges the Curious Refuge starter kit's rigged human into the House of Velvet set,
blocks Seraphine's walk down the runway toward a locked-low hero camera with a slow
push-in, and renders a contact sheet of frames for blocking approval.
Full 120-frame animatic renders only after the blocking is approved (one pilot per
variable: this pass tests blocking + camera only).
"""
import math, os, bpy

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
BLEND = os.path.normpath(os.path.join(HERE, "..", "out", "house_of_velvet.blend"))
KIT = "/tmp/claude-0/-home-claude/a45fb0be-a186-5306-b737-4d37021c2e89/scratchpad/crkit/kit.blend"

def _fcurves(obj):
    ad = obj.animation_data
    if not ad or not ad.action:
        return []
    act = ad.action
    if hasattr(act, "fcurves") and len(act.fcurves):
        return list(act.fcurves)
    fcs = []
    for lay in getattr(act, "layers", []):
        for st in lay.strips:
            try:
                cb = st.channelbag(ad.action_slot) if hasattr(st, "channelbag") else None
            except Exception:
                cb = None
            if cb:
                fcs += list(cb.fcurves)
    return fcs


bpy.ops.wm.open_mainfile(filepath=BLEND)
sc = bpy.context.scene

# --- bring in the rigged human from the CR kit ---
bpy.ops.wm.append(directory=KIT + "/Collection/", filename="Human", link=False)
rig = bpy.data.objects.get("Human_rig")
assert rig, "Human_rig not found after append"

# scale to Seraphine's height (1.88 m) and place at the runway's far end
h = rig.dimensions.z or 1.0
if h > 0.1:
    s = 1.88 / h
    rig.scale = (s, s, s)
bpy.context.view_layer.update()

RW = 0.18  # runway top
START_Y, END_Y = 20.0, 7.0   # Blender +Y = GathrXR -z ; walks toward camera
rig.location = (0.0, START_Y, RW)
rig.rotation_euler = (0, 0, math.pi)  # guess: face -Y (toward camera); contact sheet verifies

# hide the static primitive models for this shot (the rig replaces Seraphine;
# Volta/Pearl are joined into the same mesh, previz reads fine without them)
hm = bpy.data.objects.get("house_models")
if hm:
    hm.hide_render = True
    hm.hide_viewport = True

# --- animate: frames 1-120 @ 24fps (5 s), linear glide + subtle bob ---
sc.frame_start, sc.frame_end = 1, 120
sc.render.fps = 24
for f, y in [(1, START_Y), (120, END_Y)]:
    rig.location.y = y
    rig.keyframe_insert("location", index=1, frame=f)
for f in range(1, 121, 8):          # gentle vertical bob
    rig.location.z = RW + (0.025 if (f // 8) % 2 else 0.0)
    rig.keyframe_insert("location", index=2, frame=f)
for fc in _fcurves(rig):
    for kp in fc.keyframe_points:
        kp.interpolation = "LINEAR"

# --- camera: locked low hero angle with a slow push-in ---
cam = bpy.data.objects.get("cam_hero")
assert cam, "cam_hero missing"
for f, y in [(1, 3.6), (120, 4.8)]:
    cam.location = (0.0, y, 1.45)
    cam.keyframe_insert("location", frame=f)
for fc in _fcurves(cam):
    for kp in fc.keyframe_points:
        kp.interpolation = "LINEAR"
sc.camera = cam

# --- render contact sheet frames (blocking check, not the final animatic) ---
sc.render.engine = "BLENDER_EEVEE"
try: sc.eevee.taa_render_samples = 8
except AttributeError: pass
sc.view_settings.view_transform = "Standard"
sc.view_settings.exposure = -0.75
sc.render.resolution_x, sc.render.resolution_y = 432, 768

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "shot001_runway_walk.blend"))
print("SAVED", flush=True)

for f in [1, 30, 60, 90, 120]:
    try:
        sc.frame_set(f)
        sc.render.filepath = os.path.join(OUT, f"s001_f{f:03d}.png")
        bpy.ops.render.render(write_still=True)
        print("FRAME", f, flush=True)
    except Exception as e:
        print("RENDER_SKIP", f, e, flush=True)

print("DONE")
