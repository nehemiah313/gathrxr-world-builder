"""House of Velvet - reference-matched headless Blender build for GathrXR WebXR.

v3: REFERENCE-DRIVEN REBUILD.
Earlier versions were built from world_spec.json text and never compared against the
Kling key art. This version matches the art directly:
  - house-models-keyart-9x16.png : floor-level runway between banks of red velvet seats,
    paparazzi flashbulb field, shattered skeletal roof, visible moon + hard shaft,
    near-monochrome teal/black with red + gold as the only accents. No stage, no curtain.
  - atelier-lab-16x9.png : attic with raking broken beams, brass-domed glass tanks with
    copper pipework and draped chains, glowing gowns suspended inside, a long receding row
    of dress forms, a glass cutting table lit from within, a blazing green arch with a
    gowned skeleton in it. All green, single-color room.

Surreal rules (one broken law per room):
  - Showroom : the audience never moves but the flashbulbs keep firing. Runway is INFINITE,
               exiting the north wall into void with flashbulbs receding forever.
  - Atelier  : the gowns are alive, the bodies are not. Through the green arch the room
               is INVERTED (tanks hanging from the ceiling, light growing upward).
  - Makeup   : light with no source.
  - Cold     : zero light.

Palette discipline: strict monochrome per zone, one accent each.

Run:  python3 build_house_of_velvet.py     (bpy module)  or  blender -b -P build_house_of_velvet.py
Outputs -> ./out/
Authoring Z-up; glTF exports +Y up. Units meters.
"""
import json
import math
import os

import bpy

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
os.makedirs(OUT, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.unit_settings.system = "METRIC"

MATS = {}


def hex2rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))


def mat(name, hexcolor, rough=0.9, metal=0.0, emit=0.0, alpha=1.0):
    if name in MATS:
        return MATS[name]
    color = hex2rgb(hexcolor)
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1.0)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if "Emission Color" in b.inputs:
        b.inputs["Emission Color"].default_value = (*color, 1.0)
        b.inputs["Emission Strength"].default_value = emit
    if alpha < 1.0:
        b.inputs["Alpha"].default_value = alpha
        m.blend_method = "BLEND"
    MATS[name] = m
    return m


# ---------------- ZONE PALETTES (strict monochrome, one accent each) ----------------
# SHOWROOM: teal-black. Accents: red velvet seats, gold flashbulbs.
SHOW_WALL = mat("show_wall", "081014")
SHOW_FLOOR = mat("show_floor", "0a1519", rough=0.45)
RUNWAY = mat("runway_wet", "0d2027", rough=0.06, metal=0.25)   # wet, reflective
SEAT_RED = mat("seat_velvet", "320a0e", rough=1.0)
SEAT_FRAME = mat("seat_frame", "14181c", rough=0.6, metal=0.4)
HEAD = mat("mannequin_head", "0f1418", rough=0.8)
FLASH = mat("flashbulb", "ffe8bc", emit=22.0)
MOON = mat("moon_disc", "dce8ff", emit=18.0)
SHAFT = mat("moon_shaft", "9fc0e8", emit=0.22, alpha=0.016)
RAFTER = mat("rafter", "04070a", rough=1.0)

# HALLS: slate mono. Accent: one green exit.
HALL_WALL = mat("hall_wall", "0e1217")
EXIT_GREEN = mat("exit_green", "2bff78", emit=7.0)

# OFFICE: amber mono.
OFF_WALL = mat("office_wall", "17120c")
AMBER = mat("amber_glow", "ffcf87", emit=6.0)
RED_CLOCK = mat("clock_red", "ff2a2a", emit=7.0)

# BACKSTAGE: plum mono.
PLUM_WALL = mat("plum_wall", "140e1a")
PLUM_GLOW = mat("plum_glow", "8a46d6", emit=4.0)
RACK = mat("rack", "241a2e", rough=1.0)

# MAKEUP: white mono, sourceless light.
WHITE_WALL = mat("white_wall", "e6e6ec", rough=0.85)
WHITE_HOT = mat("white_hot", "ffffff", emit=14.0)
MIRROR = mat("mirror", "c6ccd4", rough=0.02, metal=1.0)

# COLD STORAGE: pure black.
BLACK = mat("cold_black", "040406", rough=1.0)

# ATELIER: all green, single-color room.
AT_WALL = mat("atelier_wall", "0a1d16")
AT_BEAM = mat("atelier_beam", "0d2419", rough=1.0)
GLASS = mat("tank_glass", "7fe7d0", rough=0.03, alpha=0.22)
BRASS = mat("brass_green", "6d6a3c", rough=0.3, metal=0.9)
COPPER = mat("copper_pipe", "5e5536", rough=0.35, metal=0.9)
GOWN_GLOW = mat("gown_glow", "b9ffe4", emit=3.2)
FORM = mat("dress_form", "1b3a2c", rough=0.95)
GOWN_PALE = mat("gown_pale", "9fe6c4", rough=1.0)
ARCH_BLAZE = mat("arch_blaze", "49ff9d", emit=6.5)
BONE = mat("skeleton", "0a1410", rough=0.9)
GLASSTABLE = mat("glass_table", "8fffd8", emit=1.4, alpha=0.5)

STEEL = mat("steel", "2b3034", rough=0.4, metal=0.8)
DEBRIS = mat("debris", "0c1014", rough=1.0)


# ---------------- primitives (GathrXR coords: x, y_up, z ; Blender x, -z, y) -------
def _box(name, cx, cy, cz, sx, sy, sz, material, rot=None):
    bpy.ops.mesh.primitive_cube_add(size=1, location=(cx, cy, cz))
    o = bpy.context.active_object
    o.name = name
    o.scale = (sx, sy, sz)
    if rot:
        o.rotation_euler = rot
    o.data.materials.append(material)
    return o


def gbox(name, gx, gy, gz, sx, sy, sz, material, rot_x=0.0, rot_y=0.0):
    rot = (rot_x, 0, rot_y) if (rot_x or rot_y) else None
    return _box(name, gx, -gz, gy, sx, sz, sy, material, rot=rot)


def gcyl(name, gx, gy, gz, r, h, material, verts=12, rot_x=0.0, rot_z=0.0):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=h,
                                        location=(gx, -gz, gy))
    o = bpy.context.active_object
    o.name = name
    if rot_x or rot_z:
        o.rotation_euler = (rot_x, 0, rot_z)
    o.data.materials.append(material)
    return o


def gcone(name, gx, gy, gz, r1, r2, h, material, verts=14, flip=False):
    bpy.ops.mesh.primitive_cone_add(vertices=verts, radius1=r1, radius2=r2, depth=h,
                                    location=(gx, -gz, gy))
    o = bpy.context.active_object
    o.name = name
    if flip:
        o.rotation_euler = (math.pi, 0, 0)
    o.data.materials.append(material)
    return o


def gsph(name, gx, gy, gz, r, material, segs=10):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segs, ring_count=max(6, segs // 2),
                                         radius=r, location=(gx, -gz, gy))
    o = bpy.context.active_object
    o.name = name
    o.data.materials.append(material)
    return o


def join_group(name, objs):
    """Merge a list of meshes into one object to keep WebXR draw calls low."""
    objs = [o for o in objs if o and o.name in bpy.data.objects]
    if len(objs) < 2:
        if objs:
            objs[0].name = name
        return objs[0] if objs else None
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    merged = bpy.context.active_object
    merged.name = name
    return merged


H = 5.0            # showroom wall height (taller than v2 for roof drama)
SHOW_N = -26.2     # north end of the showroom
VOID_END = -74.0   # how far the infinite runway recedes

# ===================== SHOWROOM (reference-matched) =====================
gbox("floor_show", 0, -0.06, -13, 20.4, 0.12, 26.2, SHOW_FLOOR)
gbox("wall_show_W", -10.2, H / 2, -13, 0.4, H, 26.2, SHOW_WALL)
gbox("wall_show_E_N", 10.2, H / 2, -17.1, 0.4, H, 18, SHOW_WALL)
gbox("wall_show_E_S", 10.2, H / 2, -2.9, 0.4, H, 6.2, SHOW_WALL)
gbox("backstage_lintel", 10.2, 4.2, -7, 0.4, 1.6, 2.4, SHOW_WALL)
# north wall, split for the infinite runway to pass through
gbox("wall_show_N_W", -6.1, H / 2, SHOW_N, 8.2, H, 0.4, SHOW_WALL)
gbox("wall_show_N_E", 6.1, H / 2, SHOW_N, 8.2, H, 0.4, SHOW_WALL)
gbox("wall_show_N_lintel", 0, 4.3, SHOW_N, 4.4, 1.4, 0.4, SHOW_WALL)
# south wall with the two hall doorways
gbox("wall_S_A", -7.5, H / 2, 0, 5, H, 0.4, SHOW_WALL)
gbox("wall_S_B", 0, H / 2, 0, 5, H, 0.4, SHOW_WALL)
gbox("wall_S_C", 7.5, H / 2, 0, 5, H, 0.4, SHOW_WALL)

# --- the runway: FLOOR LEVEL, wet and reflective (key art, not a raised catwalk) ---
gbox("runway", 0, 0.09, -13.5, 3.4, 0.18, 24.0, RUNWAY)
gbox("runway_lip_W", -1.74, 0.1, -13.5, 0.08, 0.2, 24.0, SEAT_FRAME)
gbox("runway_lip_E", 1.74, 0.1, -13.5, 0.08, 0.2, 24.0, SEAT_FRAME)

# --- SURREAL 1: INFINITE RUNWAY. Continues through the north wall into black void. ---
_void = [gbox("runway_void", 0, 0.09, -50, 3.4, 0.18, 48.0, RUNWAY)]
_voidflash = []
_z = SHOW_N - 2.0
_step = 1.6
while _z > VOID_END:
    _fall = max(0.12, 1.0 - (SHOW_N - _z) / 52.0)   # bulbs shrink as they recede
    for sx in (-2.6, 2.6):
        _voidflash.append(gsph(f"voidflash_{abs(int(_z*10))}_{sx}", sx * _fall * 1.6,
                               1.4, _z, 0.085 * _fall, FLASH, segs=6))
    _z -= _step
    _step *= 1.06
join_group("runway_void", _void)
join_group("void_flashbulbs", _voidflash)

# --- SURREAL 2: AUDIENCE OF HEADS. Banks of red velvet seats, identical heads, ---
# --- all facing the runway, flashes firing from empty hands.                   ---
_seats, _frames, _heads, _flashes = [], [], [], []
_row_z = -23.4
_r = 0
while _row_z < -4.0:
    for side in (-1, 1):
        for col in range(4):
            sx = side * (2.9 + col * 1.75)
            _seats.append(gbox(f"seat_{_r}_{side}_{col}", sx, 0.45, _row_z, 1.5, 0.22, 1.0, SEAT_RED))
            _seats.append(gbox(f"seatback_{_r}_{side}_{col}", sx, 0.85, _row_z - 0.45, 1.5, 0.86, 0.18, SEAT_RED))
            _frames.append(gbox(f"seatleg_{_r}_{side}_{col}", sx, 0.17, _row_z, 1.3, 0.34, 0.8, SEAT_FRAME))
            # head: slightly above the backrest, facing the runway centre
            _heads.append(gsph(f"head_{_r}_{side}_{col}", sx, 1.42, _row_z - 0.1, 0.135, HEAD, segs=8))
            _heads.append(gcyl(f"neck_{_r}_{side}_{col}", sx, 1.18, _row_z - 0.1, 0.07, 0.3, HEAD, verts=8))
            # flashbulbs fire from the crowd, but only on some seats
            if (_r * 3 + col * 2) % 4 != 1:
                _flashes.append(gsph(f"flash_{_r}_{side}_{col}", sx + side * 0.45, 1.62,
                                     _row_z + 0.3, 0.1, FLASH, segs=6))
    _row_z += 1.55
    _r += 1
join_group("audience_seats", _seats)
join_group("audience_frames", _frames)
join_group("audience_heads", _heads)
join_group("audience_flashbulbs", _flashes)

# --- shattered skeletal roof: rafters with broken slats, open to the night ---
_roof = []
for i in range(14):
    rz = -25.0 + i * 1.85
    _roof.append(gbox(f"rafter_{i}", 0, H + 0.1, rz, 20.4, 0.22, 0.26, RAFTER))
for i in range(26):          # broken slat fragments, irregular gaps
    sz = -25.5 + i * 1.0
    if 8 <= i <= 15:         # the tear the moon shines through
        continue
    for sx in (-7.6, -4.2, 4.2, 7.6):
        if (i + int(sx)) % 3 == 0:
            continue
        _roof.append(gbox(f"slat_{i}_{int(sx)}", sx, H + 0.26, sz, 2.6, 0.1, 0.8, RAFTER,
                          rot_x=0.06 * ((i % 5) - 2)))
join_group("skeletal_roof", _roof)

# --- the moon, visible through the tear, with a hard shaft down the runway ---
gsph("moon", 0.4, 10.2, -15.0, 0.85, MOON, segs=16)
gcone("moon_shaft", 0.2, 4.0, -14.5, 1.45, 0.42, 7.0, SHAFT, verts=20)

# ===================== HALLS + OFFICE (slate mono, one green accent) ============
gbox("hall_W_N", -5.2, 2, 3.3, 0.4, 4, 6.6, HALL_WALL)
gbox("hall_W_S", -5.2, 2, 10.9, 0.4, 4, 6.2, HALL_WALL)
gbox("closet_lintel", -5.2, 3.5, 7.2, 0.4, 1, 1.4, HALL_WALL)
gbox("hall_E", 5.2, 2, 7, 0.4, 4, 14, HALL_WALL)
gbox("hall_divider", 0, 2, 7, 4.6, 4, 14, HALL_WALL)
gbox("ceil_halls", 0, 4.1, 9, 10.4, 0.3, 18.4, HALL_WALL)
gbox("closet_N", -6.5, 2, 6, 2.6, 4, 0.4, HALL_WALL)
gbox("closet_S", -6.5, 2, 8.6, 2.6, 4, 0.4, HALL_WALL)
gbox("closet_W", -7.6, 2, 7.3, 0.4, 4, 3, HALL_WALL)
gbox("closet_ceil", -6.5, 4.1, 7.3, 2.6, 0.3, 3, HALL_WALL)
gbox("exit_sign", -3.75, 3.3, 13.4, 0.7, 0.25, 0.08, EXIT_GREEN)
_deb = [gbox(f"debris_{i}", dx, dy, dz, s, s * 0.6, s, DEBRIS, rot_x=rx)
        for i, (dx, dy, dz, s, rx) in enumerate(
            [(-3.0, 0.15, 4, 0.5, 0.0), (3.2, 0.1, 9, 0.4, 0.3), (-2.6, 0.2, 11, 0.6, 0.6)])]
join_group("hall_debris", _deb)

gbox("office_W", -4.2, 2, 16, 0.4, 4, 4, OFF_WALL)
gbox("office_E_N", 4.2, 2, 14.5, 0.4, 4, 1, OFF_WALL)
gbox("office_E_S", 4.2, 2, 17, 0.4, 4, 2, OFF_WALL)
gbox("office_E_vtop", 4.2, 2.5, 15.5, 0.4, 3, 1, OFF_WALL)
gbox("office_S", 0, 2, 18.2, 8.8, 4, 0.4, OFF_WALL)
gbox("office_N", 0, 2, 14, 4.6, 4, 0.4, OFF_WALL)
gbox("corner_W", -4.7, 2, 14, 1.2, 4, 0.4, OFF_WALL)
gbox("corner_E", 4.7, 2, 14, 1.2, 4, 0.4, OFF_WALL)
gbox("desk", 0, 0.75, 17.2, 2.2, 0.1, 0.9, SEAT_FRAME)
gbox("desk_leg_L", -1.0, 0.37, 17.2, 0.1, 0.75, 0.8, SEAT_FRAME)
gbox("desk_leg_R", 1.0, 0.37, 17.2, 0.1, 0.75, 0.8, SEAT_FRAME)
gbox("monitor_L", -0.6, 1.1, 17.5, 0.6, 0.45, 0.08, AMBER)
gbox("monitor_R", 0.6, 1.1, 17.5, 0.6, 0.45, 0.08, AMBER)
gbox("clock_1200", 0, 2.7, 17.95, 0.9, 0.3, 0.06, RED_CLOCK)
# vent: longer than the building is wide (the office's broken law)
gbox("vent_N", 10.6, 0.55, 15, 12.4, 1.1, 0.2, STEEL)
gbox("vent_S", 10.6, 0.55, 16, 12.4, 1.1, 0.2, STEEL)
gbox("vent_ceil", 10.6, 1.15, 15.5, 12.4, 0.2, 1.2, STEEL)
gbox("vent_mouth", 17.6, 0.55, 15.5, 0.12, 1.0, 0.9, RED_CLOCK)

# ===================== EAST WING (plum / white / black monochrome) =============
gbox("wing_N", 17, 2, -10.4, 13.6, 4, 0.4, PLUM_WALL)
gbox("wing_E", 23.8, 2, 0.8, 0.4, 4, 22.8, PLUM_WALL)
gbox("wing_S_W", 10.9, 2, 4, 1.4, 4, 0.4, PLUM_WALL)
gbox("wing_S_E", 16.5, 2, 4, 1.0, 4, 0.4, PLUM_WALL)
for nm, gz, sz in [("P1", -9.2, 2.4), ("P2", -4.7, 2.6), ("P3", -0.5, 3.0), ("P4", 3.3, 1.4)]:
    gbox(f"partition_{nm}", 17, 2, gz, 0.4, 4, sz, PLUM_WALL)
gbox("wing_ceil", 15.5, 4.1, -3.2, 10.6, 0.3, 14.4, PLUM_WALL)
gbox("rack_1", 11.8, 1, -8.5, 0.3, 2, 3, RACK)
gbox("rack_2", 11.8, 1, -4, 0.3, 2, 3, RACK)
gbox("lobby_S", 20.4, 2, 12.2, 7.2, 4, 0.4, PLUM_WALL)
gbox("lobby_W", 16.8, 2, 8.1, 0.4, 4, 8.2, PLUM_WALL)
_gate = [gcyl(f"freight_bar_{i}", 11.9 + i * 0.8, 1.8, 4, 0.08, 3.6, STEEL) for i in range(5)]
_gate.append(gbox("freight_header", 13.8, 3.7, 4, 5.4, 0.3, 0.2, STEEL))
join_group("freight_gate", _gate)
gbox("service_ramp", 22.4, 2.1, -3.5, 2.0, 0.25, 11.8, STEEL, rot_x=0.365)
gbox("ramp_rail", 21.3, 2.2, -3.5, 0.2, 4.4, 11.6, PLUM_WALL)

# MAKEUP ROOM: all white, light with no source
gbox("makeup_div", 20.4, 2, -4.3, 6.8, 4, 0.4, WHITE_WALL)
gbox("makeup_wall_N", 20.4, 2, -10.2, 6.8, 4, 0.2, WHITE_WALL)
gbox("makeup_wall_E", 23.6, 2, -7.3, 0.2, 4, 6, WHITE_WALL)
gbox("makeup_floor", 20.4, 0.02, -7.3, 6.8, 0.08, 6, WHITE_WALL)
gbox("makeup_ceil", 20.4, 3.98, -7.3, 6.8, 0.08, 6, WHITE_HOT)   # the sourceless light
gbox("mirror", 20.4, 1.8, -10.05, 3.6, 2.3, 0.08, MIRROR)
gbox("makeup_counter", 20.4, 0.5, -9.4, 3.8, 1.0, 0.8, WHITE_WALL)
_bulbs = [gsph(f"vanity_bulb_{i}", 18.8 + i * 0.64, 3.12, -10.0, 0.075, WHITE_HOT, segs=8)
          for i in range(6)]
join_group("vanity_bulbs", _bulbs)

# COLD STORAGE: pure black, zero lights
gbox("cold_div", 20.4, 2, -0.2, 6.8, 4, 0.4, BLACK)
gbox("cold_floor", 20.4, 0.02, -2.3, 6.8, 0.08, 4, BLACK)
gbox("cold_ceil", 20.4, 3.98, -2.3, 6.8, 0.08, 4, BLACK)
gbox("cold_wall_E", 23.6, 2, -2.3, 0.2, 4, 4, BLACK)

# ===================== ATELIER (level 2, all green) ============================
L2 = 4.6
gbox("L2_slab", 17, L2 - 0.15, 10, 14, 0.3, 16, AT_WALL)
gbox("L2_slab_lab", 13.5, L2 - 0.15, 5, 7.5, 0.3, 7, AT_WALL)
gbox("at_wall_W", 9.9, L2 + 2.2, 6, 0.3, 4.4, 9, AT_WALL)
gbox("at_wall_N", 13.5, L2 + 2.2, 1.6, 7.5, 4.4, 0.3, AT_WALL)
gbox("at_wall_S", 13.5, L2 + 2.2, 10.4, 7.5, 4.4, 0.3, AT_WALL)
# raking attic beams with gaps (the moon reaches in here too)
_beams = []
for i in range(8):
    bz = 2.2 + i * 1.1
    _beams.append(gbox(f"at_beam_{i}", 13.5, L2 + 4.3, bz, 8.0, 0.2, 0.24, AT_BEAM,
                       rot_x=0.0))
for i in range(10):
    bz = 2.0 + i * 0.9
    if 3 <= i <= 6:
        continue
    _beams.append(gbox(f"at_slat_{i}", 11.0 + (i % 3) * 1.6, L2 + 4.45, bz, 2.2, 0.08, 0.7,
                       AT_BEAM, rot_x=0.08 * ((i % 4) - 1)))
join_group("atelier_beams", _beams)

# brass-domed glass tanks with copper pipework and draped chains, glowing gowns inside
_tanks, _gowns, _pipes = [], [], []
for i, tx in enumerate([11.3, 13.3, 15.3]):
    tz = 4.4
    _tanks.append(gcyl(f"tank_glass_{i}", tx, L2 + 1.35, tz, 0.72, 2.6, GLASS, verts=20))
    _tanks.append(gcyl(f"tank_base_{i}", tx, L2 + 0.08, tz, 0.84, 0.22, BRASS, verts=20))
    _tanks.append(gcyl(f"tank_collar_{i}", tx, L2 + 2.68, tz, 0.84, 0.18, BRASS, verts=20))
    _tanks.append(gcone(f"tank_dome_{i}", tx, L2 + 2.95, tz, 0.8, 0.22, 0.42, BRASS, verts=20))
    _tanks.append(gcyl(f"tank_finial_{i}", tx, L2 + 3.26, tz, 0.07, 0.24, BRASS, verts=8))
    # the gown inside: alive, no body
    _gowns.append(gcone(f"gown_skirt_{i}", tx, L2 + 0.85, tz, 0.52, 0.17, 1.5, GOWN_GLOW, verts=16))
    _gowns.append(gcyl(f"gown_bodice_{i}", tx, L2 + 1.92, tz, 0.17, 0.72, GOWN_GLOW, verts=12))
    # copper standpipes + a draped chain to the next tank
    for px in (-0.95, 0.95):
        _pipes.append(gcyl(f"pipe_{i}_{px}", tx + px, L2 + 1.3, tz, 0.055, 2.6, COPPER, verts=8))
    _pipes.append(gcyl(f"pipe_cross_{i}", tx, L2 + 2.45, tz, 0.05, 1.9, COPPER, verts=8,
                       rot_z=math.pi / 2))
    if i < 2:
        _pipes.append(gcyl(f"chain_{i}", tx + 1.0, L2 + 0.62, tz - 0.55, 0.035, 1.5, BRASS,
                           verts=6, rot_z=math.pi / 2.3))
join_group("atelier_tanks", _tanks)
join_group("atelier_gowns", _gowns)
join_group("atelier_pipework", _pipes)

# the long receding row of dress forms (repetition into darkness)
_forms = []
for i in range(11):
    fx = 10.6 + i * 0.62
    fz = 8.1 + i * 0.12
    _forms.append(gcone(f"form_torso_{i}", fx, L2 + 1.42, fz, 0.21, 0.13, 0.72, FORM, verts=12))
    _forms.append(gcyl(f"form_pole_{i}", fx, L2 + 0.5, fz, 0.035, 1.0, BRASS, verts=6))
    _forms.append(gcyl(f"form_foot_{i}", fx, L2 + 0.04, fz, 0.2, 0.06, BRASS, verts=10))
    _forms.append(gcone(f"form_gown_{i}", fx, L2 + 0.78, fz, 0.42, 0.2, 1.1,
                        GOWN_PALE if i % 2 else GOWN_GLOW, verts=12))
join_group("atelier_dressforms", _forms)

# glass cutting table lit from within, pattern grids on top
gbox("cut_table", 13.3, L2 + 0.45, 8.6, 2.6, 0.9, 1.3, GLASSTABLE)
_grids = [gbox(f"pattern_{i}", 12.4 + i * 0.85, L2 + 0.92, 8.6, 0.62, 0.02, 0.9, GOWN_PALE)
          for i in range(3)]
join_group("cut_patterns", _grids)

# the blazing green arch, with a gowned skeleton standing in it
gbox("arch_blaze", 17.35, L2 + 1.5, 6.0, 0.12, 3.0, 2.0, ARCH_BLAZE)
gbox("arch_jamb_N", 17.3, L2 + 1.6, 4.85, 0.5, 3.2, 0.3, AT_WALL)
gbox("arch_jamb_S", 17.3, L2 + 1.6, 7.15, 0.5, 3.2, 0.3, AT_WALL)
gbox("arch_head", 17.3, L2 + 3.3, 6.0, 0.5, 0.35, 2.6, AT_WALL)
_skel = [gcyl("skel_spine", 17.0, L2 + 1.35, 6.0, 0.075, 1.3, BONE, verts=8),
         gsph("skel_skull", 17.0, L2 + 2.12, 6.0, 0.15, BONE, segs=8),
         gcyl("skel_arm_L", 16.78, L2 + 1.45, 6.0, 0.04, 1.0, BONE, verts=6),
         gcyl("skel_arm_R", 17.22, L2 + 1.45, 6.0, 0.04, 1.0, BONE, verts=6),
         gcone("skel_gown", 17.0, L2 + 0.62, 6.0, 0.48, 0.16, 1.25, GOWN_PALE, verts=12)]
join_group("arch_skeleton", _skel)

# --- SURREAL 3: THE INVERTED ATELIER, beyond the green arch ---
# Same room, upside down: tanks hang from the ceiling, light grows upward.
IV_FLOOR = L2 + 4.4      # what reads as "ceiling" here is the inverted room's floor
gbox("iv_ceil", 20.8, IV_FLOOR, 6.0, 6.4, 0.3, 8.4, AT_WALL)
gbox("iv_floor_glow", 20.8, L2 - 0.1, 6.0, 6.4, 0.12, 8.4,
     mat("iv_floor_glow_m", "3ad98a", emit=2.2))   # light from below
gbox("iv_wall_N", 20.8, L2 + 2.2, 1.9, 6.4, 4.4, 0.3, AT_WALL)
gbox("iv_wall_S", 20.8, L2 + 2.2, 10.1, 6.4, 4.4, 0.3, AT_WALL)
gbox("iv_wall_E", 23.9, L2 + 2.2, 6.0, 0.3, 4.4, 8.4, AT_WALL)
_iv = []
for i, tx in enumerate([19.3, 21.1, 22.9]):
    tz = 4.6
    # tanks hang downward from the ceiling: dome at the BOTTOM
    _iv.append(gcyl(f"iv_tank_{i}", tx, IV_FLOOR - 1.45, tz, 0.72, 2.4, GLASS, verts=20))
    _iv.append(gcyl(f"iv_collar_{i}", tx, IV_FLOOR - 0.2, tz, 0.84, 0.2, BRASS, verts=20))
    _iv.append(gcone(f"iv_dome_{i}", tx, IV_FLOOR - 2.85, tz, 0.8, 0.22, 0.42, BRASS,
                     verts=20, flip=True))
    _iv.append(gcone(f"iv_gown_{i}", tx, IV_FLOOR - 1.95, tz, 0.5, 0.17, 1.4, GOWN_GLOW,
                     verts=14, flip=True))
for i in range(6):          # dress forms standing upside down on the ceiling
    fx = 19.1 + i * 0.72
    fz = 8.4
    _iv.append(gcone(f"iv_form_{i}", fx, IV_FLOOR - 1.1, fz, 0.21, 0.13, 0.7, FORM,
                     verts=12, flip=True))
    _iv.append(gcyl(f"iv_pole_{i}", fx, IV_FLOOR - 0.5, fz, 0.035, 1.0, BRASS, verts=6))
    _iv.append(gcone(f"iv_gownf_{i}", fx, IV_FLOOR - 1.5, fz, 0.4, 0.19, 1.05, GOWN_PALE,
                     verts=12, flip=True))
join_group("inverted_atelier", _iv)

# director's desk, mounted where it should not be
gbox("dir_desk", 21, L2 + 0.5, 15, 1.8, 0.8, 0.9, SEAT_FRAME)
gbox("dir_lampglow", 21.6, L2 + 1.05, 14.6, 0.14, 0.2, 0.14, AMBER)

# ===================== LIGHTS (monochrome discipline) ==========================
LIGHT_SCALE = 15.0


def light(name, kind, gx, gy, gz, hexcolor, energy, spot_size=None, rot=None):
    ld = bpy.data.lights.new(name, kind)
    ld.color = hex2rgb(hexcolor)
    ld.energy = energy * LIGHT_SCALE
    if kind == "SPOT" and spot_size:
        ld.spot_size = spot_size
        ld.spot_blend = 0.35
    lo = bpy.data.objects.new(name, ld)
    lo.location = (gx, -gz, gy)
    if rot:
        lo.rotation_euler = rot
    scene.collection.objects.link(lo)
    return lo


# showroom: the moon shaft is the only real key light. Flashbulbs do the rest.
light("moon_key", "SPOT", 0.4, 11.0, -14.5, "cdddff", 2600, spot_size=0.52)
light("runway_bounce", "POINT", 0, 0.8, -12, "7fa8c8", 55)
light("runway_bounce_far", "POINT", 0, 0.8, -22, "7fa8c8", 40)
light("crowd_glow_W", "POINT", -6.0, 1.5, -14, "ffd9a0", 16)
light("crowd_glow_E", "POINT", 6.0, 1.5, -14, "ffd9a0", 16)
light("void_pull", "POINT", 0, 1.4, -34, "ffe8bc", 45)
# halls / office
light("hall_W_spot", "SPOT", -3.75, 3.9, 8, "aebccc", 220, spot_size=1.0)
light("exit_green_l", "POINT", -3.75, 3.2, 13.4, "2bff78", 45)
light("office_amber", "POINT", 0, 3, 16, "ffcf87", 85)
light("vent_red", "POINT", 17.6, 0.6, 15.5, "ff3322", 25)
# backstage plum
light("backstage_plum", "POINT", 13.5, 3, -3, "8a46d6", 70)
light("gate_plum", "POINT", 13.8, 3, 5.5, "8a46d6", 45)
# makeup: sourceless white
light("makeup_sourceless", "AREA", 20.4, 3.7, -7.3, "ffffff", 900)
# atelier: single green world + the moon reaching in
light("atelier_green", "POINT", 13.3, L2 + 2.0, 5.5, "4dff9d", 70)
light("atelier_green2", "POINT", 12.0, L2 + 1.6, 8.5, "4dff9d", 45)
light("atelier_moon", "SPOT", 13.0, L2 + 5.4, 5.0, "cdddff", 520, spot_size=1.1)
light("arch_blaze_l", "POINT", 17.6, L2 + 1.6, 6.0, "49ff9d", 120)
light("inverted_updraft", "POINT", 20.8, L2 + 0.6, 6.0, "49ff9d", 95)
light("dir_gold", "POINT", 21, L2 + 2.4, 14.5, "ffcf87", 70)


# ===================== THE HOUSE MODELS (key art subject) ======================
GOWN_BLACK = mat("gown_black", "0b0b0e", rough=0.55)
GOLD_THREAD = mat("gold_thread", "c8a24a", emit=1.6, metal=0.8, rough=0.3)
GOWN_CRIMSON = mat("gown_crimson", "5a1218", rough=1.0)
GOWN_IVORY = mat("gown_ivory", "d8cfbd", rough=0.9)
SKIN = mat("model_skin", "707c74", rough=0.72)
HAIR = mat("model_hair", "241610", rough=1.0)
PEARL = mat("pearl_trim", "efe8d8", rough=0.35)

RW = 0.18   # runway top


def model(tag, gx, gz, height, hip, gown_mat, hair_mat, hair_r, trim=None):
    """Stylised walking figure. Narrow silhouette: couture reads tall, not conical."""
    parts = []
    gown_h = height * 0.50
    # skirt: narrow at the hem, not a traffic cone
    parts.append(gcone(f"{tag}_gown", gx, RW + gown_h / 2, gz, hip, hip * 0.52,
                       gown_h, gown_mat, verts=18))
    # long bodice
    parts.append(gcyl(f"{tag}_torso", gx, RW + gown_h + height * 0.17, gz,
                      hip * 0.50, height * 0.34, gown_mat, verts=14))
    # shoulders
    parts.append(gbox(f"{tag}_shoulders", gx, RW + height * 0.80, gz,
                      hip * 1.15, height * 0.045, hip * 0.62, gown_mat))
    parts.append(gcyl(f"{tag}_neck", gx, RW + height * 0.845, gz, 0.052,
                      height * 0.075, SKIN, verts=8))
    parts.append(gsph(f"{tag}_head", gx, RW + height * 0.925, gz, height * 0.072,
                      SKIN, segs=14))
    parts.append(gsph(f"{tag}_hair", gx, RW + height * 0.962, gz, hair_r,
                      hair_mat, segs=14))
    for sgn in (-1, 1):
        parts.append(gcyl(f"{tag}_arm{sgn}", gx + sgn * (hip * 0.92), RW + height * 0.58,
                          gz + 0.03, 0.036, height * 0.40, SKIN, verts=8,
                          rot_x=sgn * 0.05))
    if trim:
        for i in range(5):
            parts.append(gcyl(f"{tag}_trim{i}", gx - hip * 0.62 + i * hip * 0.31,
                              RW + gown_h * 0.52, gz - hip * 0.30, 0.009,
                              gown_h * 0.86, trim, verts=6))
    return parts


_m = []
# Seraphine: thin, tall, torn black chiffon with gold thread (leads, nearest camera)
_m += model("seraphine", 0.0, -8.6, 1.95, 0.21, GOWN_BLACK, HAIR, 0.055, trim=GOLD_THREAD)
# Madame Volta: curvy, crimson velvet, towering beehive
_m += model("volta", -1.06, -10.9, 1.78, 0.30, GOWN_CRIMSON, HAIR, 0.145)
# Duchess Pearl: grand, pearl-encrusted ivory
_m += model("pearl", 1.08, -10.7, 1.76, 0.37, GOWN_IVORY, HAIR, 0.115, trim=PEARL)
join_group("house_models", _m)

# a soft key so the lead model is actually lit, as in the art
light("model_key", "SPOT", 0.0, 6.2, -8.4, "cfe0ff", 95, spot_size=0.55)
light("model_fill", "POINT", 0.0, 1.9, -6.2, "ffe8bc", 5)

# ===================== BEVEL PASS ==============================================
for o in [o for o in bpy.data.objects if o.type == "MESH"]:
    md = o.modifiers.new("bev", "BEVEL")
    md.width = 0.011
    md.segments = 2
    md.limit_method = "ANGLE"
    md.angle_limit = math.radians(50)
    bpy.context.view_layer.objects.active = o
    try:
        bpy.ops.object.modifier_apply(modifier="bev")
    except Exception:
        o.modifiers.remove(md)

# near-black world so the void actually reads as void
world = bpy.data.worlds.new("night")
world.use_nodes = True
_bg = world.node_tree.nodes.get("Background")
if _bg:
    _bg.inputs["Color"].default_value = (0.004, 0.007, 0.012, 1.0)
    _bg.inputs["Strength"].default_value = 1.0
scene.world = world

# ===================== CAMERAS / RENDER ========================================
scene.render.resolution_x = 540
scene.render.resolution_y = 960
scene.render.engine = "BLENDER_EEVEE"
try:
    scene.eevee.taa_render_samples = 10
except AttributeError:
    pass
scene.view_settings.view_transform = "Standard"
scene.view_settings.exposure = -0.75


def add_cam(name, gx, gy, gz, lens, pitch_deg, yaw_deg=0.0, vertical=False):
    cd = bpy.data.cameras.new(name)
    cd.lens = lens
    c = bpy.data.objects.new(name, cd)
    c.location = (gx, -gz, gy)
    c.rotation_euler = (math.radians(pitch_deg), 0, math.radians(yaw_deg))
    scene.collection.objects.link(c)
    return c


# hero: match the key art. Standing on the runway, low, looking up its length.
cam_hero = add_cam("cam_hero", 0, 1.45, -3.6, 20, 95, 0)
cam_atelier = add_cam("cam_atelier", 9.6, L2 + 2.25, 10.6, 17, 84, -46)
cam_inverted = add_cam("cam_inverted", 17.0, L2 + 2.0, 6.0, 16, 90, -90)

tri_count = 0
for o in bpy.data.objects:
    if o.type == "MESH":
        o.data.calc_loop_triangles()
        tri_count += len(o.data.loop_triangles)

metrics = {
    "objects": len([o for o in bpy.data.objects if o.type == "MESH"]),
    "lights": len([o for o in bpy.data.objects if o.type == "LIGHT"]),
    "materials": len(bpy.data.materials),
    "triangles": tri_count,
    "budget_triangles_max": 150000,
    "within_budget": tri_count <= 150000,
    "reference_matched": ["house-models-keyart-9x16.png", "atelier-lab-16x9.png"],
    "surreal_moves": ["infinite_runway", "audience_of_heads", "inverted_atelier"],
    "palette": "strict monochrome per zone",
}
with open(os.path.join(OUT, "metrics.json"), "w") as f:
    json.dump(metrics, f, indent=2)

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "house_of_velvet.blend"))

for cam, fname, rx, ry, expo in [(cam_hero, "preview_hero.png", 540, 960, -0.75),
                                 (cam_atelier, "preview_atelier.png", 768, 432, -1.9),
                                 (cam_inverted, "preview_inverted.png", 768, 432, -2.1)]:
    scene.camera = cam
    scene.render.resolution_x, scene.render.resolution_y = rx, ry
    scene.view_settings.exposure = expo
    scene.render.filepath = os.path.join(OUT, fname)
    try:
        bpy.ops.render.render(write_still=True)
    except Exception as e:
        print("render skipped", fname, e)

scene.camera = cam_hero
bpy.ops.export_scene.gltf(
    filepath=os.path.join(OUT, "house_of_velvet.glb"),
    export_format="GLB",
    export_lights=False,
    export_apply=True,
    export_yup=True,
)

print("DONE", json.dumps(metrics))
