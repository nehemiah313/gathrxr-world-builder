"""House of Velvet — headless Blender blockout + export for GathrXR WebXR.

Follows gathrxr-world-builder SKILL.md:
  G1 blockout architecture -> checkpoint .blend + 640x360 preview -> GLB export -> reimport validation.

Run:  blender -b -P build_house_of_velvet.py    (or: python with the bpy module)
Outputs land in ./out/: house_of_velvet.blend, house_of_velvet.glb, preview_hero.png, metrics.json

Authoring in Blender Z-up; glTF exporter converts to +Y up for GathrXR.
All units meters. Spec: world_spec.json (same directory).
"""
import json
import math
import os

import bpy

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
os.makedirs(OUT, exist_ok=True)

# ---------- scene reset ----------
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.unit_settings.system = "METRIC"

MATS = {}


def mat(name, color, rough=0.9, metal=0.0, emit=0.0, alpha=1.0):
    if name in MATS:
        return MATS[name]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metal
    if "Emission Color" in bsdf.inputs:
        bsdf.inputs["Emission Color"].default_value = (*color, 1.0)
        bsdf.inputs["Emission Strength"].default_value = emit
    if alpha < 1.0:
        bsdf.inputs["Alpha"].default_value = alpha
        m.blend_method = "BLEND"
    MATS[name] = m
    return m


def hex2rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))


# Palette (matches live primitive world)
WALL = mat("wall_dark", hex2rgb("16161c"))
WALL2 = mat("wall_wing", hex2rgb("1d1d26"))
FLOOR = mat("floor_tile", hex2rgb("23232b"), rough=0.6)
CURTAIN = mat("curtain_red", hex2rgb("5c0a0a"), rough=1.0)
STAGEWOOD = mat("stage_wood", hex2rgb("6b4a2f"), rough=0.8)
CATWALK = mat("catwalk_gloss", hex2rgb("111114"), rough=0.15)
EDGE = mat("runway_edge", hex2rgb("e8e8ff"), emit=1.5)
GOLD = mat("gold_sign", hex2rgb("d4af37"), rough=0.3, metal=0.9)
STEEL = mat("steel", hex2rgb("3a3a42"), rough=0.4, metal=0.8)
TANK = mat("tank_fluid", hex2rgb("7fe7d0"), rough=0.05, alpha=0.35)
MIRROR = mat("mirror", hex2rgb("cfd6dd"), rough=0.03, metal=1.0)
BULB = mat("vanity_bulb", hex2rgb("fff2e0"), emit=4.0)
DUCT = mat("vent_duct", hex2rgb("2e2e34"), rough=0.5, metal=0.7)


def box(name, cx, cy, cz, sx, sy, sz, material, rot=None):
    """Axis sizes are full extents (Blender X=GathrXR X, Blender Y=GathrXR -Z, Blender Z=up)."""
    bpy.ops.mesh.primitive_cube_add(size=1, location=(cx, cy, cz))
    o = bpy.context.active_object
    o.name = name
    o.scale = (sx, sy, sz)
    if rot:
        o.rotation_euler = rot
    o.data.materials.append(material)
    return o


def cyl(name, cx, cy, cz, r, h, material, verts=12):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=h, location=(cx, cy, cz))
    o = bpy.context.active_object
    o.name = name
    o.data.materials.append(material)
    return o


# GathrXR [x, y_up, z] -> Blender (x, -z, y_up). Helper takes GathrXR-style args.
def gbox(name, gx, gy, gz, sx, sy, sz, material, rot_x=0.0):
    rot = (rot_x, 0, 0) if rot_x else None
    return box(name, gx, -gz, gy, sx, sz, sy, material, rot=rot)  # note axis swap


def gcyl(name, gx, gy, gz, r, h, material, verts=12):
    return cyl(name, gx, -gz, gy, r, h, material, verts=verts)


H = 4.0  # wall height

# ---------- ground slab ----------
gbox("floor_slab", 6.8, -0.05, 2.0, 35.0, 0.1, 33.2, FLOOR)

# ---------- showroom shell ----------
gbox("north_wall", 0, 2, -14.2, 20.4, H, 0.4, WALL)
gbox("west_showroom_wall", -10.2, 2, -7, 0.4, H, 14.4, WALL)
gbox("east_showroom_wall_N", 10.2, 2, -11.1, 0.4, H, 6.2, WALL)
gbox("east_showroom_wall_S", 10.2, 2, -2.9, 0.4, H, 6.2, WALL)
gbox("backstage_lintel", 10.2, 3.5, -7, 0.4, 1, 2.4, WALL)
gbox("south_wall_A", -7.5, 2, 0, 5, H, 0.4, WALL)
gbox("south_wall_B", 0, 2, 0, 5, H, 0.4, WALL)
gbox("south_wall_C", 7.5, 2, 0, 5, H, 0.4, WALL)

# halls + office
gbox("west_hall_N", -5.2, 2, 3.3, 0.4, H, 6.6, WALL)
gbox("west_hall_S", -5.2, 2, 10.9, 0.4, H, 6.2, WALL)
gbox("closet_lintel", -5.2, 3.5, 7.2, 0.4, 1, 1.4, WALL)
gbox("east_hall_wall", 5.2, 2, 7, 0.4, H, 14, WALL)
gbox("hall_divider", 0, 2, 7, 4.6, H, 14, WALL)
gbox("office_W", -4.2, 2, 16, 0.4, H, 4, WALL)
gbox("office_E_N", 4.2, 2, 14.5, 0.4, H, 1, WALL)
gbox("office_E_S", 4.2, 2, 17, 0.4, H, 2, WALL)
gbox("office_E_vent_top", 4.2, 2.5, 15.5, 0.4, 3, 1, WALL)
gbox("office_S", 0, 2, 18.2, 8.8, H, 0.4, WALL)
gbox("office_N", 0, 2, 14, 4.6, H, 0.4, WALL)
gbox("corner_W", -4.7, 2, 14, 1.2, H, 0.4, WALL)
gbox("corner_E", 4.7, 2, 14, 1.2, H, 0.4, WALL)

# ceilings (moon hole over catwalk end: gap x -2..2, z -9..-5)
gbox("ceil_show_N", 0, 4.1, -11.5, 20, 0.3, 5, WALL)
gbox("ceil_show_S", 0, 4.1, -2.5, 20, 0.3, 5, WALL)
gbox("ceil_show_W", -6, 4.1, -7, 8, 0.3, 4, WALL)
gbox("ceil_show_E", 6, 4.1, -7, 8, 0.3, 4, WALL)
gbox("ceil_halls", 0, 4.1, 9, 10.4, 0.3, 18.4, WALL)

# ---------- stage + runway ----------
gbox("stage", 0, 0.4, -12, 9, 0.8, 3.5, STAGEWOOD)
gbox("curtain", 0, 2.2, -13.8, 9.5, 3.2, 0.2, CURTAIN)
gbox("catwalk", 0, 0.3, -6.6, 2.4, 0.6, 7.4, CATWALK)
gbox("runway_edge_W", -1.25, 0.61, -6.6, 0.1, 0.04, 7.4, EDGE)
gbox("runway_edge_E", 1.25, 0.61, -6.6, 0.1, 0.04, 7.4, EDGE)
# marquee plate
gbox("marquee_plate", 0, 3.4, -13.65, 6.5, 0.9, 0.1, GOLD)

# party tables + hats
for i, (tx, tz) in enumerate([(-6, -6), (6, -6), (-6, -2.5)], 1):
    gcyl(f"table_{i}", tx, 0.5, tz, 0.6, 1.0, mat("table_dark", hex2rgb("2a2a33")))

# ---------- closet ----------
gbox("closet_N", -6.5, 2, 6, 2.6, H, 0.4, WALL)
gbox("closet_S", -6.5, 2, 8.6, 2.6, H, 0.4, WALL)
gbox("closet_W", -7.6, 2, 7.3, 0.4, H, 3, WALL)
gbox("closet_ceil", -6.5, 4.1, 7.3, 2.6, 0.3, 3, WALL)

# ---------- east wing ----------
gbox("wing_N", 17, 2, -10.4, 13.6, H, 0.4, WALL2)
gbox("wing_E", 23.8, 2, 0.8, 0.4, H, 22.8, WALL2)
gbox("wing_S_W", 10.9, 2, 4, 1.4, H, 0.4, WALL2)
gbox("wing_S_E", 16.5, 2, 4, 1.0, H, 0.4, WALL2)
for nm, gz, sz in [("P1", -9.2, 2.4), ("P2", -4.7, 2.6), ("P3", -0.5, 3.0), ("P4", 3.3, 1.4)]:
    gbox(f"partition_{nm}", 17, 2, gz, 0.4, H, sz, WALL2)
gbox("makeup_cold_div", 20.4, 2, -4.3, 6.8, H, 0.4, WALL2)
gbox("cold_lobby_div", 20.4, 2, -0.2, 6.8, H, 0.4, WALL2)
gbox("lobby_S", 20.4, 2, 12.2, 7.2, H, 0.4, WALL2)
gbox("lobby_W", 16.8, 2, 8.1, 0.4, H, 8.2, WALL2)
gbox("wing_ceil", 15.5, 4.1, -3.2, 10.6, 0.3, 14.4, WALL2)

# freight gate (5 bars + header)
for i in range(5):
    gcyl(f"freight_bar_{i+1}", 11.9 + i * 0.8, 1.8, 4, 0.08, 3.6, STEEL)
gbox("freight_header", 13.8, 3.7, 4, 5.4, 0.3, 0.2, STEEL)

# service ramp (rot about Blender X)
gbox("service_ramp", 22.4, 2.1, -3.5, 2.0, 0.25, 11.8, STEEL, rot_x=0.365)
gbox("ramp_rail", 21.3, 2.2, -3.5, 0.2, 4.4, 11.6, WALL2)

# ---------- level 2 ----------
gbox("L2_slab", 17, 4.45, 10, 14, 0.3, 16, WALL2)
gbox("L2_rail_W", 10, 6, 10, 0.3, 2.8, 16, WALL2)
gbox("L2_rail_N", 15, 6, 2, 10, 2.8, 0.3, WALL2)
gbox("L2_rail_E", 24, 6, 10, 0.3, 2.8, 16, WALL2)
gbox("L2_rail_S", 17, 6, 18, 14, 2.8, 0.3, WALL2)
gbox("L2_div", 21.5, 6, 10, 5, 2.8, 0.3, WALL2)
for i in range(3):
    gcyl(f"labgate_bar_{i+1}", 20.5 + i * 0.6, 6, 2.2, 0.08, 2.8, STEEL)
gbox("labgate_header", 22, 7.3, 2.2, 4, 0.25, 0.2, STEEL)

# atelier
for i, (tx, tz) in enumerate([(12, 4.5), (14.5, 4.5), (12, 7.5)], 1):
    gcyl(f"tank_{i}", tx, 6.1, tz, 0.55, 3.0, TANK)
    gcyl(f"tank_base_{i}", tx, 4.75, tz, 0.65, 0.3, STEEL)
gbox("lab_table", 13.5, 5.05, 9, 3, 0.9, 1, STEEL)
# dress forms: thin / curvy / grand (simple lathe-ish stand-ins, resized cylinders)
for i, (dx, r) in enumerate([(15.2, 0.16), (15.9, 0.24), (16.7, 0.34)], 1):
    gcyl(f"dressform_{i}", dx, 5.5, 7.0, r, 1.5, mat("form_ivory", hex2rgb("d8d2c4"), rough=0.8))
    gcyl(f"dressform_pole_{i}", dx, 4.85, 7.0, 0.03, 0.6, STEEL)

# director office
gbox("dir_desk", 21, 5.0, 15, 1.8, 0.8, 0.9, STAGEWOOD)

# ---------- makeup room ----------
gbox("mirror", 19, 1.8, -10.1, 3.4, 2.2, 0.1, MIRROR)
gbox("makeup_counter", 19, 0.5, -9.5, 3.6, 1.0, 0.8, mat("counter_plum", hex2rgb("332833")))
for i in range(6):
    gcyl(f"vanity_bulb_{i+1}", 17.5 + i * 0.6, 3.05, -10.05, 0.06, 0.12, BULB)

# wardrobe racks
gbox("rack_1", 11.8, 1, -8.5, 0.3, 2, 3, mat("rack_plum", hex2rgb("4a3550")))
gbox("rack_2", 11.8, 1, -4, 0.3, 2, 3, MATS["rack_plum"])

# ---------- vent ----------
gbox("vent_N", 10.6, 0.55, 15, 12.4, 1.1, 0.2, DUCT)
gbox("vent_S", 10.6, 0.55, 16, 12.4, 1.1, 0.2, DUCT)
gbox("vent_ceil", 10.6, 1.15, 15.5, 12.4, 0.2, 1.2, DUCT)

# ---------- lights (Blender; exported as KHR_lights_punctual) ----------
LIGHT_SCALE = 15.0  # watts -> visible pools under Eevee headless


def light(name, kind, gx, gy, gz, color, energy, spot_size=None):
    ld = bpy.data.lights.new(name, kind)
    ld.color = color
    ld.energy = energy * LIGHT_SCALE
    if kind == "SPOT" and spot_size:
        ld.spot_size = spot_size
    lo = bpy.data.objects.new(name, ld)
    lo.location = (gx, -gz, gy)
    if kind == "SPOT":
        lo.rotation_euler = (0, 0, 0)  # -Z default: straight down
    scene.collection.objects.link(lo)
    return lo


light("stage_red_spot", "SPOT", 0, 3.9, -12, hex2rgb("ff2a2a"), 800, spot_size=1.2)
light("moonbeam", "SPOT", 0, 6, -7, hex2rgb("bcd4ff"), 1200, spot_size=1.0)
light("runway_glow", "POINT", 0, 1, -6.5, hex2rgb("e8e8ff"), 60)
light("show_purple", "POINT", 0, 2.5, -4, hex2rgb("6622cc"), 80)
light("hall_W_spot", "SPOT", -3.75, 3.9, 8, hex2rgb("e8e8ff"), 300, spot_size=1.0)
light("exit_green", "POINT", -3.75, 3.5, 13, hex2rgb("33ff77"), 40)
light("hall_E_red", "POINT", 3.75, 3, 7, hex2rgb("ff3333"), 40)
light("office_amber", "POINT", 0, 3, 16, hex2rgb("ffd9a0"), 80)
light("makeup_white", "POINT", 19, 3.2, -7.2, hex2rgb("ffffff"), 400)
light("backstage_purple", "POINT", 13.5, 3, -3, hex2rgb("7733cc"), 60)
light("gate_amber", "POINT", 13.8, 3, 5.5, hex2rgb("ffaa33"), 60)
light("ramp_red", "POINT", 22.4, 4.4, 1, hex2rgb("ff2222"), 25)
light("vent_red", "POINT", 17.6, 0.6, 15.5, hex2rgb("ff3322"), 25)
light("lab_green", "POINT", 13.5, 7.5, 6, hex2rgb("4dff9d"), 150)
light("lab_moon", "SPOT", 13.3, 8.5, 5.5, hex2rgb("bcd4ff"), 700, spot_size=1.2)
light("dir_gold", "POINT", 21, 7, 14.5, hex2rgb("ffd27a"), 80)

# ================= G2/G3 DETAIL + POLISH PASS =================
# New materials for the detail layer
BRASS = mat("brass", hex2rgb("b8933f"), rough=0.35, metal=0.9)
CHROME = mat("chrome", hex2rgb("c9ced6"), rough=0.1, metal=1.0)
FABRIC_RED = mat("fabric_red", hex2rgb("6e1414"), rough=1.0)
FABRIC_IVORY = mat("fabric_ivory", hex2rgb("d8d0bd"), rough=1.0)
FABRIC_CRIMSON = mat("fabric_crimson", hex2rgb("4a0d10"), rough=1.0)
SILHOUETTE = mat("tank_silhouette", hex2rgb("0a1a17"), rough=0.9, alpha=0.9)
COVE = mat("cove_cyan", hex2rgb("5577aa"), emit=2.0)
WARM = mat("sconce_warm", hex2rgb("ffcf8a"), emit=5.0)
REDLENS = mat("par_red", hex2rgb("ff2a2a"), emit=6.0)
WHITELENS = mat("par_white", hex2rgb("fff4e0"), emit=6.0)
GREENLENS = mat("lab_lens", hex2rgb("4dff9d"), emit=5.0)
MOONSHAFT = mat("moon_shaft", hex2rgb("aec4ff"), emit=0.6, alpha=0.06)
DEBRIS = mat("debris", hex2rgb("17171d"), rough=1.0)

# --- stage lighting truss + par cans ---
gbox("truss_beam", 0, 3.85, -11.2, 9, 0.18, 0.18, CHROME)
gbox("truss_beam_front", 0, 3.85, -9.6, 9, 0.18, 0.18, CHROME)
for i, tx in enumerate([-3.4, -1.7, 0, 1.7, 3.4]):
    gcyl(f"parcan_{i}", tx, 3.6, -11.2, 0.14, 0.4, STEEL)
    lens = REDLENS if i % 2 == 0 else WHITELENS
    gcyl(f"parlens_{i}", tx, 3.38, -11.2, 0.12, 0.05, lens)

# --- chandelier over showroom ---
gcyl("chand_ring", 0, 3.6, -5, 0.9, 0.08, BRASS, verts=20)
gcyl("chand_stem", 0, 3.85, -5, 0.03, 0.5, BRASS)
import math as _m
for i in range(10):
    a = i / 10.0 * 2 * _m.pi
    bx, bz = 0.8 * _m.cos(a), -5 + 0.8 * _m.sin(a)
    gcyl(f"chand_bead_{i}", bx, 3.35, bz, 0.05, 0.12, WARM)

# --- stage footlights (row of warm domes at stage front) ---
for i in range(9):
    gcyl(f"footlight_{i}", -3.6 + i * 0.9, 0.82, -10.35, 0.07, 0.1, WARM)

# --- runway edge dot-lights ---
for i in range(10):
    z = -3.2 - i * 0.72
    gcyl(f"runway_dot_L_{i}", -1.2, 0.62, z, 0.05, 0.06, WHITELENS)
    gcyl(f"runway_dot_R_{i}", 1.2, 0.62, z, 0.05, 0.06, WHITELENS)

# --- showroom cove lighting (thin emissive strips near ceiling) ---
gbox("cove_N", 0, 3.9, -13.9, 18, 0.06, 0.1, COVE)
gbox("cove_W", -9.9, 3.9, -7, 0.1, 0.06, 13, COVE)
gbox("cove_E", 9.9, 3.9, -7, 0.1, 0.06, 13, COVE)

# --- wall sconces down the halls (warm pinpoints) ---
for z in (3, 6, 10, 13):
    gbox(f"sconce_W_{z}", -5.0, 2.6, z, 0.08, 0.3, 0.08, WARM)
    gbox(f"sconce_E_{z}", 5.0, 2.6, z, 0.08, 0.3, 0.08, WARM)

# --- specimen tank silhouettes (a gown-body suspended in each tank) ---
for i, (tx, tz) in enumerate([(12, 4.5), (14.5, 4.5), (12, 7.5)], 1):
    gcyl(f"tank_body_{i}", tx, 6.3, tz, 0.22, 1.6, SILHOUETTE, verts=10)
    gcyl(f"tank_head_{i}", tx, 7.2, tz, 0.14, 0.3, SILHOUETTE, verts=10)
    gcyl(f"tank_ring_{i}", tx, 4.65, tz, 0.6, 0.08, BRASS, verts=16)

# --- draped couture on mannequins + catwalk (angled fabric planes) ---
gbox("drape_mann_1", 15.5, 0.9, -8.8, 0.9, 1.6, 0.05, FABRIC_CRIMSON, rot_x=0.12)
gbox("drape_mann_2", 15.5, 0.9, -3.2, 0.9, 1.6, 0.05, FABRIC_IVORY, rot_x=-0.1)
gbox("drape_catwalk", 0.3, 0.65, -4.5, 0.8, 0.05, 1.4, FABRIC_CRIMSON, rot_x=0.0)
gbox("drape_floor_show", -4.5, 0.08, -5, 1.6, 0.04, 1.2, FABRIC_CRIMSON)

# --- curtain vertical folds (relief over the flat curtain) ---
for i in range(9):
    fx = -4 + i * 1.0
    gbox(f"curtain_fold_{i}", fx, 2.2, -13.68, 0.12, 3.0, 0.12, mat("curtain_fold", hex2rgb("4a0808"), rough=1.0))

# --- debris in halls (fallen clutter) ---
for nm, (dx, dy, dz, s, rx) in {
    "debris_1": (-3.0, 0.15, 4, 0.5, 0.0),
    "debris_2": (3.2, 0.1, 9, 0.4, 0.3),
    "debris_3": (-2.6, 0.2, 11, 0.6, 0.6),
    "debris_4": (13.0, 0.15, 1.5, 0.5, 0.0),
}.items():
    gbox(nm, dx, dy, dz, s, s * 0.6, s, DEBRIS, rot_x=rx)

# --- director desk lamp glow + gold plate ---
gcyl("dir_lamp", 21.6, 5.55, 14.6, 0.06, 0.18, WARM)
gbox("dir_plate", 21, 5.95, 17.7, 1.6, 0.5, 0.06, BRASS)

# --- fake volumetric moon shaft (big faint translucent cone from the roof hole) ---
bpy.ops.mesh.primitive_cone_add(vertices=24, radius1=2.6, radius2=0.5,
                                depth=5.0, location=(0, 7, 4.0))
_shaft = bpy.context.active_object
_shaft.name = "moon_shaft"
_shaft.data.materials.append(MOONSHAFT)

# --- BEVEL PASS: round every hard box/cylinder edge (kills the flat-blockout look) ---
_meshes = [o for o in bpy.data.objects if o.type == "MESH"]
for o in _meshes:
    md = o.modifiers.new("bev", "BEVEL")
    md.width = 0.012
    md.segments = 2
    md.limit_method = "ANGLE"
    md.angle_limit = math.radians(50)
    bpy.context.view_layer.objects.active = o
    try:
        bpy.ops.object.modifier_apply(modifier="bev")
    except Exception as e:
        o.modifiers.remove(md)

# --- dark-blue world ambient so shadows read as night, not void ---
world = bpy.data.worlds.new("night")
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.012, 0.014, 0.03, 1.0)
    bg.inputs["Strength"].default_value = 1.0
scene.world = world

# ---------- hero camera (G1 preview) ----------
cam_data = bpy.data.cameras.new("hero_cam")
cam_data.lens = 24
cam = bpy.data.objects.new("hero_cam", cam_data)
cam.location = (0, 2.0, 1.4)       # GathrXR (0, 1.4, -2) -> at runway end area
cam.rotation_euler = (math.radians(83), 0, 0)  # faces blender +Y = toward stage
scene.collection.objects.link(cam)
scene.camera = cam
scene.render.resolution_x = 640
scene.render.resolution_y = 360
scene.render.engine = "BLENDER_EEVEE"
try:
    scene.eevee.taa_render_samples = 16
except AttributeError:
    pass
scene.view_settings.view_transform = "Standard"
scene.view_settings.exposure = -0.5
scene.render.filepath = os.path.join(OUT, "preview_hero.png")

# ---------- metrics + save + export ----------
tri_count = 0
for o in bpy.data.objects:
    if o.type == "MESH":
        m = o.data
        m.calc_loop_triangles()
        tri_count += len(m.loop_triangles)

metrics = {
    "objects": len([o for o in bpy.data.objects if o.type == "MESH"]),
    "lights": len([o for o in bpy.data.objects if o.type == "LIGHT"]),
    "materials": len(bpy.data.materials),
    "triangles": tri_count,
    "budget_triangles_max": 150000,
    "within_budget": tri_count <= 150000,
}
with open(os.path.join(OUT, "metrics.json"), "w") as f:
    json.dump(metrics, f, indent=2)

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "house_of_velvet.blend"))

try:
    bpy.ops.render.render(write_still=True)
except Exception as e:  # headless GPU may be absent; preview is optional
    print("preview render skipped:", e)

# G1 geometry proof: overhead workbench render (ignores lighting)
try:
    cam2_data = bpy.data.cameras.new("overhead_cam")
    cam2_data.type = "ORTHO"
    cam2_data.ortho_scale = 40
    cam2 = bpy.data.objects.new("overhead_cam", cam2_data)
    cam2.location = (7, -2, 40)  # over the footprint, looking straight down
    cam2.rotation_euler = (0, 0, 0)
    scene.collection.objects.link(cam2)
    scene.camera = cam2
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.render.filepath = os.path.join(OUT, "preview_overhead.png")
    bpy.ops.render.render(write_still=True)
    scene.camera = cam
except Exception as e:
    print("overhead render skipped:", e)

# Gallery angle: backstage looking at the bright makeup room vs dark cold storage
try:
    scene.render.engine = "BLENDER_EEVEE"
    cam3_data = bpy.data.cameras.new("makeup_cam")
    cam3_data.lens = 22
    cam3 = bpy.data.objects.new("makeup_cam", cam3_data)
    cam3.location = (19, 6.2, 1.7)   # makeup room center, GathrXR ~ (19, 1.7, -6.2)
    cam3.rotation_euler = (math.radians(84), 0, 0)  # faces the mirror/vanity wall
    scene.collection.objects.link(cam3)
    scene.camera = cam3
    scene.render.filepath = os.path.join(OUT, "preview_makeup.png")
    bpy.ops.render.render(write_still=True)
    scene.camera = cam
except Exception as e:
    print("makeup render skipped:", e)

bpy.ops.export_scene.gltf(
    filepath=os.path.join(OUT, "house_of_velvet.glb"),
    export_format="GLB",
    export_lights=False,  # GathrXR live world carries its own lights; GLB ships geometry + emissives
    export_apply=True,
    export_yup=True,
)

print("DONE", json.dumps(metrics))
