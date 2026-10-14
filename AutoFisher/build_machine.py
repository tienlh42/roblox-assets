"""Builds AutoFisher_<Rarity>.rbxmx and .glb (rig + KeyframeSequences + client scripts) for the five fishing machines.

Run: python build_machine.py
Reuses the rbxmx writer of ../PoliceGoose and the color and part helpers of ../Egg. Coordinates are in studs, ground at
y = 0, the machine faces -Z (the water).
The machine is a pelican made of machinery: a barrel body with a gear and a status lamp, a chimney, wings, a tail, a
head with a hard hat and a big beak whose pouch holds the catch. Three bamboo rods are plugged into sockets (a rod on
the back, one on each shoulder) and cast and reel by themselves; the game replaces them with FishingRod models later.
All five rarities share one frame and only differ in colors and extras (RARITIES below).
"""

import math
import sys
from pathlib import Path
from types import SimpleNamespace

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "Egg"))

from build_egg import (  # noqa: E402
    BLUE, GOLD_DARK, LAVENDER, MATERIAL_NEON, PEARL, PINK, PURPLE, RAINBOW, RED, WOOD, crystal, ring_around, set_prop,
    shade,
)
from build_police_goose import (  # noqa: E402
    BLACK, CF, GOLD, MODEL_STREAMING_ATOMIC, ORANGE, RUN_CONTEXT_CLIENT, SILVER, WHITE, Item, build_joint,
    build_keyframe_sequence, build_part, cf, xml_attributes, xml_string,
)
from export_glb import export  # noqa: E402

WOOD_DARK = (122, 74, 36)
BAMBOO = (205, 185, 95)
POUCH = (255, 205, 150)
IRON = (84, 90, 100)
LAMP_YELLOW = (255, 200, 50)
P = cf


def cyl_y(name, y_lo, y_hi, dia, color, bone, x=0.0, z=0.0):
    """Cylinder standing on the Y axis (Roblox cylinders lie along X, so it is turned 90 degrees)."""
    return (name, "cylinder", (y_hi - y_lo, dia, dia), cf(x, (y_lo + y_hi) / 2, z, 0, 0, 90), color, bone)


def ball(name, size, pos, color, bone):
    return (name, "ball", (size,) * 3, cf(*pos), color, bone)


def axis_rotation(axis, deg):
    """Rotation of deg degrees around a world axis (Rodrigues)."""
    n = math.sqrt(sum(v * v for v in axis))
    x, y, z = (v / n for v in axis)
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    t = 1 - c
    return CF(rot=((t * x * x + c, t * x * y - s * z, t * x * z + s * y),
                   (t * x * y + s * z, t * y * y + c, t * y * z - s * x),
                   (t * x * z - s * y, t * y * z + s * x, t * z * z + c)))


# ---------------------------------------------------------------- the three rods

# slot: position of the socket on the machine, d: horizontal direction the rod leans toward (the water), tilt: degrees
# from vertical. The rod frame has y along the rod.
SLOTS = [
    SimpleNamespace(pos=(0.0, 3.05, 1.0), d=(0.0, -1.0), tilt=20),
    SimpleNamespace(pos=(1.15, 2.95, 0.0), d=(0.85, -0.53), tilt=55),
    SimpleNamespace(pos=(-1.15, 2.95, 0.0), d=(-0.85, -0.53), tilt=55),
]
ROD_A, ROD_B = (0.3, 2.1), (2.1, 3.7)  # rod sections, measured along the rod from the socket
HOOK_DROP = 1.3


def slot_frame(slot):
    length = math.hypot(*slot.d)
    dx, dz = slot.d[0] / length, slot.d[1] / length
    return CF(slot.pos) * axis_rotation((dz, 0, -dx), slot.tilt)


def rod_parts(i, slot):
    """Socket, two bamboo sections, guide, tip, and the hook with its float hanging below the tip."""
    frame = slot_frame(slot)
    pre = f"Rod{i}_"
    tip = (frame * CF((0, ROD_B[1], 0))).pos
    hook = (tip[0], tip[1] - HOOK_DROP, tip[2])

    def along(name, y_lo, y_hi, dia, color, bone):
        return (name, "cylinder", (y_hi - y_lo, dia, dia), frame * cf(y=(y_lo + y_hi) / 2, rz=90), color, bone)

    parts = [
        along(f"Socket{i}", -0.1, 0.4, 0.4, SILVER, "Body"),
        along(f"SocketRim{i}", 0.35, 0.45, 0.5, IRON, "Body"),
        along(pre + "A", *ROD_A, 0.2, BAMBOO, None),
        along(pre + "B", *ROD_B, 0.14, BAMBOO, None),
        along(pre + "Node1", 0.85, 0.95, 0.26, WOOD_DARK, pre + "A"),
        along(pre + "Node2", 1.55, 1.65, 0.26, WOOD_DARK, pre + "A"),
        along(pre + "Node3", 2.75, 2.85, 0.2, WOOD_DARK, pre + "B"),
        (pre + "Tip", "ball", (0.14,) * 3, frame * cf(y=ROD_B[1]), SILVER, pre + "B"),
        (pre + "Hook", "ball", (0.1,) * 3, cf(*hook), SILVER, None),
        (pre + "Shank", "block", (0.04, 0.22, 0.04), cf(hook[0], hook[1] - 0.14, hook[2]), SILVER, pre + "Hook"),
        (pre + "Curve", "block", (0.04, 0.04, 0.16), cf(hook[0], hook[1] - 0.25, hook[2] - 0.06), SILVER, pre + "Hook"),
        (pre + "Float", "ball", (0.24,) * 3, cf(hook[0], hook[1] + 0.25, hook[2]), RED, pre + "Hook"),
        (pre + "FloatCap", "ellipsoid", (0.24, 0.11, 0.24), cf(hook[0], hook[1] + 0.34, hook[2]), WHITE, pre + "Hook"),
        (pre + "LineEnd", "ball", (0.04,) * 3, cf(hook[0], hook[1] + 0.42, hook[2]), WHITE, pre + "Hook"),
        # Cap and padlock cover the socket while the slot is locked (RodEffects shows them).
        (f"LockCap{i}", "cylinder", (0.14, 0.5, 0.5), frame * cf(y=0.5, rz=90), IRON, "Body"),
        (f"LockBody{i}", "block", (0.24, 0.28, 0.14), frame * cf(0, 0.62, -0.14), GOLD, "Body"),
    ]
    return parts, hook


# ---------------------------------------------------------------- the pelican machine

# rarity colors: body barrel, belly patch, bands, head (head, neck, wings, tail), hat, platform.
def pelican_parts(c):
    parts = [
        ("HumanoidRootPart", "block", (1, 1, 1), cf(0, 0.5, 0), WHITE, None),
        ("Platform", "block", (4.2, 0.3, 3.6), cf(0, 0.15, 0), c.platform, "HumanoidRootPart"),
        ("PlatformTrim", "block", (4.3, 0.08, 3.7), cf(0, 0.32, 0), shade(c.platform, 0.8), "HumanoidRootPart"),
    ]
    for side, x in (("L", 1), ("R", -1)):
        parts += [
            cyl_y(f"Bollard{side}", 0.3, 0.85, 0.34, IRON, "HumanoidRootPart", x * 1.75, -1.4),
            ball(f"BollardCap{side}", 0.4, (x * 1.75, 0.88, -1.4), IRON, "HumanoidRootPart"),
            cyl_y(f"Leg{side}", 0.3, 0.8, 0.22, ORANGE, "HumanoidRootPart", x * 0.7, -0.2),
            (f"Foot{side}", "ellipsoid", (0.9, 0.16, 1.2), cf(x * 0.7, 0.4, -0.35), ORANGE, "HumanoidRootPart"),
        ]
    parts += [
        ("Body", "ellipsoid", (2.6, 2.4, 2.4), cf(0, 1.9, 0.1), c.body, None),
        ("Belly", "ellipsoid", (1.7, 1.4, 0.6), cf(0, 1.7, -0.95), c.belly, "Body"),
        ("GearDish", "cylinder", (0.12, 1.1, 1.1), cf(0, 1.55, -1.18, 0, 90, 0), IRON, "Body"),
        ("Gear", "cylinder", (0.14, 0.8, 0.8), cf(0, 1.55, -1.25, 0, 90, 0), GOLD_DARK, None),
        ("GearHub", "ball", (0.2, 0.2, 0.2), cf(0, 1.55, -1.34), SILVER, "Gear"),
        ("LampRing", "cylinder", (0.12, 0.46, 0.46), cf(0, 2.6, -1.2, 0, 90, 0), SILVER, "Body"),
        ("Lamp", "ball", (0.3, 0.3, 0.3), cf(0, 2.6, -1.3), LAMP_YELLOW, "Body"),
        cyl_y("Chimney", 2.9, 3.7, 0.36, IRON, "Body", 0.8, 0.7),
        cyl_y("ChimneyRim", 3.62, 3.74, 0.46, shade(IRON, 0.8), "Body", 0.8, 0.7),
    ]
    for i, y in enumerate((1.35, 1.9, 2.45)):
        radius = 1.2 * math.sqrt(1 - ((y - 1.9) / 1.2) ** 2)
        parts.append(cyl_y(f"Band{i + 1}", y - 0.05, y + 0.05, 2 * radius + 0.1, c.bands[i % len(c.bands)], "Body",
                           0.0, 0.1))
    for i in range(8):
        a = 360 * i / 8
        parts.append(("GearTooth%d" % (i + 1), "block", (0.14, 0.16, 0.14),
                      cf(0.46 * math.cos(math.radians(a)), 1.55 + 0.46 * math.sin(math.radians(a)), -1.25, 0, 0, a),
                      GOLD_DARK, "Gear"))
    for side, x in (("L", 1), ("R", -1)):
        parts += [
            (f"Wing{side}", "ellipsoid", (0.5, 1.3, 1.5), cf(x * 1.4, 2.0, 0.15, 0, 0, x * 8), c.head, None),
            (f"WingTip{side}", "ellipsoid", (0.4, 0.5, 0.9), cf(x * 1.46, 1.45, 0.25, 0, 0, x * 8), c.wing_tip,
             f"Wing{side}"),
            ball(f"Eye{side}", 0.4, (x * 0.4, 4.25, -1.5), WHITE, "Head"),
            ball(f"Pupil{side}", 0.2, (x * 0.4, 4.25, -1.68), BLACK, "Head"),
            ball(f"Shine{side}", 0.08, (x * 0.36, 4.32, -1.74), WHITE, "Head"),
            (f"Brow{side}", "block", (0.3, 0.07, 0.08), cf(x * 0.4, 4.55, -1.5, 0, 0, -x * 15), BLACK, "Head"),
            ("Blush" + side, "ellipsoid", (0.2, 0.12, 0.08), cf(x * 0.58, 3.95, -1.48), PINK, "Head"),
            ball(f"Lid{side}", 0.46, (x * 0.4, 4.25, -1.38), c.head, None),
        ]
    parts += [
        ("Tail", "ellipsoid", (0.9, 0.5, 1.0), cf(0, 1.9, 1.4), c.head, None),
        ("Neck", "ellipsoid", (0.85, 1.5, 0.85), cf(0, 3.25, -0.65, -20, 0, 0), c.head, None),
        ("Head", "ellipsoid", (1.2, 1.05, 1.25), cf(0, 4.0, -1.05), c.head, None),
        ("Beak", "ellipsoid", (0.52, 0.3, 2.1), cf(0, 4.02, -2.25), ORANGE, "Head"),
        ball("BeakTip", 0.16, (0, 3.95, -3.28), RED, "Head"),
        ("Jaw", "ellipsoid", (0.46, 0.16, 1.95), cf(0, 3.84, -2.15), shade(ORANGE, 0.9), None),
        ("Pouch", "ellipsoid", (0.62, 0.36, 1.7), cf(0, 3.7, -2.1), POUCH, None),
        ("PouchBulge1", "ellipsoid", (0.68, 0.5, 1.75), cf(0, 3.6, -2.1), POUCH, "Pouch"),
        ("PouchBulge2", "ellipsoid", (0.74, 0.72, 1.8), cf(0, 3.46, -2.1), POUCH, "Pouch"),
        ("PouchBulge3", "ellipsoid", (0.8, 0.98, 1.85), cf(0, 3.32, -2.1), POUCH, "Pouch"),
        ("HatDome", "ellipsoid", (1.35, 0.7, 1.35), cf(0, 4.7, -1.05), c.hat, "Head"),
        ("HatRidge", "block", (0.14, 0.12, 1.2), cf(0, 5.03, -1.05), shade(c.hat, 0.85), "Head"),
        ("HatBrim", "block", (1.4, 0.09, 0.65), cf(0, 4.52, -1.7, -8, 0, 0), c.hat, "Head"),
        ball("HatLamp", 0.2, (0, 4.85, -1.72), GOLD, "Head"),
    ]
    return parts


JOINTS = [
    ("Body", "HumanoidRootPart", (0, 0.7, 0)),
    ("Gear", "Body", (0, 1.55, -1.25)),
    ("WingL", "Body", (1.2, 2.6, 0.1)),
    ("WingR", "Body", (-1.2, 2.6, 0.1)),
    ("Tail", "Body", (0, 1.9, 1.0)),
    ("Neck", "Body", (0, 2.8, -0.4)),
    ("Head", "Neck", (0, 3.75, -0.85)),
    ("Jaw", "Head", (0, 3.86, -1.4)),
    ("Pouch", "Jaw", (0, 3.85, -2.1)),
    ("LidL", "Head", (0.4, 4.25, -1.38)),
    ("LidR", "Head", (-0.4, 4.25, -1.38)),
]


# ---------------------------------------------------------------- rarities (colors and extras)

def no_extras(c):
    return []


def rare_extras(c):
    """Three seashells on the platform."""
    return [(f"Shell{i}", "ellipsoid", (0.5, 0.2, 0.4), cf(x, 0.4, z, 0, a, 0), color, "HumanoidRootPart")
            for i, (x, z, a, color) in enumerate(((1.4, 1.2, 20, PINK), (-1.5, 0.9, -30, WHITE), (1.0, -1.3, 60, PINK)),
                                                 start=1)]


def epic_extras(c):
    """Crystals growing at the four corners of the platform."""
    parts = []
    for i, (x, z, tilt) in enumerate(((1.8, 1.4, 12), (-1.8, 1.4, -12), (1.8, -1.0, 12), (-1.8, -1.0, -12)), start=1):
        parts += crystal(f"PlatformCrystal{i}", cf(x, 0.3, z, 0, 0, -tilt), 0.9 + 0.2 * (i % 2), 0.28,
                         LAVENDER if i % 2 else PURPLE, "HumanoidRootPart")
    return parts


def legendary_extras(c):
    return ring_around(2.6, 2.2, 18, [(255, 215, 95)])


def mythic_extras(c):
    horns = [(f"HatHorn{side}", "ellipsoid", (0.12, 0.4, 0.12), cf(x * 0.42, 5.2, -1.05, 0, 0, -x * 22), GOLD, "Head")
             for side, x in (("L", 1), ("R", -1))]
    return [*horns, *ring_around(2.7, 2.2, -18, RAINBOW)]


RARITIES = {
    "Common": SimpleNamespace(body=WOOD, belly=(245, 230, 200), bands=[SILVER], head=WHITE, wing_tip=(60, 60, 70),
                              hat=GOLD, platform=WOOD_DARK, extras=no_extras),
    "Rare": SimpleNamespace(body=BLUE, belly=(225, 245, 255), bands=[GOLD_DARK], head=WHITE, wing_tip=(40, 90, 150),
                            hat=ORANGE, platform=(190, 160, 120), extras=rare_extras),
    "Epic": SimpleNamespace(body=PURPLE, belly=(235, 225, 255), bands=[LAVENDER], head=(246, 240, 255),
                            wing_tip=(110, 70, 200), hat=PINK, platform=(150, 140, 180), extras=epic_extras),
    "Legendary": SimpleNamespace(body=GOLD, belly=(255, 240, 190), bands=[GOLD_DARK], head=WHITE,
                                 wing_tip=GOLD_DARK, hat=RED, platform=(100, 62, 30), extras=legendary_extras),
    "Mythic": SimpleNamespace(body=PEARL, belly=(255, 255, 255), bands=[RED, GOLD, BLUE], head=WHITE,
                              wing_tip=PURPLE, hat=PINK, platform=(120, 90, 140), extras=mythic_extras),
}


# ---------------------------------------------------------------- animation

def swing(i, deg):
    """Bend of rod i toward the water (+) or away from it (-), a world rotation around the horizontal axis
    perpendicular to the rod's lean direction."""
    dx, dz = SLOTS[i - 1].d
    length = math.hypot(dx, dz)
    return axis_rotation((dz / length, 0, -dx / length), deg)


def rod_chain(i):
    """Pivots of the two rod joints in world space."""
    frame = slot_frame(SLOTS[i - 1])
    return [(f"Rod{i}_A", (frame * CF((0, ROD_A[0], 0))).pos), (f"Rod{i}_B", (frame * CF((0, ROD_B[0], 0))).pos)]


def rod_pose(i, bend_a, bend_b, reach=None, height=None):
    """Poses for the three joints of rod i. reach and height put the hook at that distance (along the lean direction,
    from the socket) and height above the ground; None leaves it hanging from the tip."""
    poses = {f"Rod{i}_A": swing(i, bend_a), f"Rod{i}_B": swing(i, bend_b)}
    if reach is None:
        return poses
    slot = SLOTS[i - 1]
    length = math.hypot(*slot.d)
    target = (slot.pos[0] + slot.d[0] / length * reach, height, slot.pos[2] + slot.d[1] / length * reach)
    matrix = CF()
    for name, pivot in rod_chain(i):
        matrix = matrix * CF(pivot) * poses[name] * CF(pivot).inverse()
    rest = rod_parts(i, slot)[1]
    local = matrix.inverse() * CF(target)
    poses[f"Rod{i}_Hook"] = cf(*(local.pos[k] - rest[k] for k in range(3)))
    return poses


# One cast and reel cycle of a rod, every 0.4 s of a 2.4 s loop: (bend of the lower and upper section, reach, height).
CYCLE = [
    (7, 12, 4.8, 0.9),    # hook lies in the water
    (9, 15, 4.0, 0.9),    # reeling in
    (11, 18, 3.2, 0.9),
    (-8, -14, -0.8, 3.8),  # wind up: the hook swings back
    (14, 22, 4.2, 3.0),   # whip: the hook flies out
    (8, 13, 4.9, 1.1),    # lands
]


def rods_working(s):
    """Rod poses at time s of the Work loop; each rod is 0.8 s behind the previous one."""
    poses = {}
    for i in (1, 2, 3):
        poses.update(rod_pose(i, *CYCLE[round(((s + 0.8 * (i - 1)) % 2.4) / 0.4) % 6]))
    return poses


def rods_hold(bend_a, bend_b, reach=None, height=None):
    poses = {}
    for i in (1, 2, 3):
        poses.update(rod_pose(i, bend_a, bend_b, reach, height))
    return poses


LID_HALF, LID_SHUT = {"LidL": P(z=-0.17), "LidR": P(z=-0.17)}, {"LidL": P(z=-0.28), "LidR": P(z=-0.28)}
LID_WIDE = {"LidL": P(z=0.05), "LidR": P(z=0.05)}
WORK_HEAD = {"Neck": P(rx=-6), "Head": P(rx=-12)}


def work_frame(k):
    """Work loop frame k (0 to 6): the machine shakes, the gear turns 60 degrees per frame, the head bobs."""
    sign = 1 if k % 2 else -1
    return {
        "Body": P(y=0.03 if k % 2 else 0, rz=sign * 1.2), "Gear": P(rz=60 * k if k < 6 else 358),
        "Neck": P(rx=-6), "Head": P(rx=-12 if k % 2 else -8), "WingL": P(rz=sign * 5), "WingR": P(rz=sign * 5),
        "Tail": P(ry=sign * 8), **rods_working(0.4 * k),
    }


def full_frame(body_y, wing_l, wing_r, head):
    return {"Body": P(y=body_y), "Neck": P(rx=10), "Head": P(rx=head), "Jaw": P(rx=-22), "WingL": P(rz=wing_l),
            "WingR": P(rz=wing_r), **LID_WIDE, **rods_hold(-2, -3)}


STRAIN = rods_hold(11, 18, 3.2, 0.9)
IDLE_RODS = rods_hold(2, 3)
# name: (looped, priority, easing, [(time, {joint: transform})]); times in seconds, see README for the timing marks.
ANIMATIONS = {
    "Idle": (True, "Idle", "Cubic", [
        (0.0, {**IDLE_RODS}),
        (0.6, {"Neck": P(rx=-12), "Head": P(rx=-8), "Body": P(y=-0.03), "Tail": P(ry=4), **LID_HALF, **IDLE_RODS}),
        (1.2, {"Neck": P(rx=-2), "Head": P(rx=-2), **{"LidL": P(z=-0.1), "LidR": P(z=-0.1)}, **IDLE_RODS}),
        (1.8, {"Neck": P(rx=-12), "Head": P(rx=-8), "Body": P(y=-0.03), "Tail": P(ry=-4), **LID_HALF, **IDLE_RODS}),
        (2.4, {**IDLE_RODS}),
    ]),
    "Work": (True, "Action", "Linear", [(0.4 * k, work_frame(k)) for k in range(7)]),
    "Catch": (False, "Action", "Cubic", [
        (0.0, {**WORK_HEAD, **STRAIN}),
        (0.25, {"Neck": P(rx=18), "Head": P(rx=12), "Jaw": P(rx=-20), "WingL": P(rz=25), "WingR": P(rz=25),
                **STRAIN}),
        (0.5, {"Neck": P(rx=8), "Head": P(rx=5), "Pouch": P(y=-0.12), "WingL": P(rz=10), "WingR": P(rz=10),
               "Body": P(y=0.06), **STRAIN}),
        (0.8, {"Neck": P(rx=-4), "Head": P(rx=-8), **STRAIN}),
        (1.2, {**WORK_HEAD, **STRAIN}),
    ]),
    "Full": (True, "Action", "Cubic", [
        (0.0, full_frame(0.05, 10, 10, 12)),
        (0.6, full_frame(0.12, 30, 5, 12)),
        (1.2, full_frame(0.05, 10, 10, 6)),
        (1.8, full_frame(0.12, 5, 30, 12)),
        (2.4, full_frame(0.05, 10, 10, 12)),
    ]),
    "Collect": (False, "Action", "Cubic", [
        (0.0, {**IDLE_RODS}),
        (0.35, {"Neck": P(rx=22), "Head": P(rx=18), "Body": P(y=-0.08), "WingL": P(rz=20), "WingR": P(rz=20),
                **LID_SHUT, **IDLE_RODS}),
        (0.6, {"Neck": P(rx=-18), "Head": P(rx=-14), "Jaw": P(rx=-38), "Pouch": P(y=0.1), "Body": P(y=0.08),
               "WingL": P(rz=5), "WingR": P(rz=5), **IDLE_RODS}),
        (0.9, {"Neck": P(rx=-8), "Head": P(rx=-4), "Jaw": P(rx=-20), **IDLE_RODS}),
        (1.2, {"Neck": P(rx=14), **LID_SHUT, **IDLE_RODS}),
        (1.4, {"Neck": P(rx=-22), "Head": P(rx=-18), "Body": P(y=-0.06), **LID_SHUT, **IDLE_RODS}),
        (1.6, {**IDLE_RODS}),
    ]),
}


def machine_data(c):
    parts = pelican_parts(c)
    joints = list(JOINTS)
    for i, slot in enumerate(SLOTS, start=1):
        rod, hook = rod_parts(i, slot)
        parts += rod
        (_, pivot_a), (_, pivot_b) = rod_chain(i)
        joints += [(f"Rod{i}_A", "Body", pivot_a), (f"Rod{i}_B", f"Rod{i}_A", pivot_b),
                   (f"Rod{i}_Hook", f"Rod{i}_B", (slot_frame(slot) * CF((0, ROD_B[1], 0))).pos)]
    parts += c.extras(c)
    return SimpleNamespace(PARTS=parts, JOINTS=joints, ANIMATIONS=ANIMATIONS)


HIDDEN_AT_START = ("LockCap", "LockBody", "PouchBulge")


def build_model(rarity, data):
    parts = {}
    for name, shape, size, rest, color, _ in data.PARTS:
        part = build_part(name, shape, size, rest, color, anchored=name == "HumanoidRootPart")
        part.rest = rest
        if name.startswith(HIDDEN_AT_START) or name == "Halo" or name.endswith("_LineEnd"):
            set_prop(part, "Transparency", '<float name="Transparency">1</float>')
        if name.startswith("HaloRing") or name == "Lamp":
            set_prop(part, "Material", f'<token name="Material">{MATERIAL_NEON}</token>')
        if name.startswith("HaloRing"):
            set_prop(part, "Transparency", '<float name="Transparency">0.25</float>')
        parts[name] = part

    model = Item("Model", [
        xml_string("Name", f"AutoFisher_{rarity}"),
        f'<Ref name="PrimaryPart">{parts["HumanoidRootPart"].ref}</Ref>',
        f'<token name="ModelStreamingMode">{MODEL_STREAMING_ATOMIC}</token>',
        xml_attributes({"Anim": "Idle", "Rarity": rarity}),
    ])
    for part in parts.values():
        model.add(part)
    for part1, part0, pivot in data.JOINTS:
        parts[part0].add(build_joint("Motor6D", part1, parts[part0], parts[part1], CF(pivot)))
    for name, _, _, rest, _, bone in data.PARTS:
        if bone:
            parts[bone].add(build_joint("Weld", name, parts[bone], parts[name], rest))

    folder = model.add(Item("Folder", [xml_string("Name", "Animations")]))
    for name, (looped, priority, easing, keyframes) in data.ANIMATIONS.items():
        folder.add(build_keyframe_sequence(name, looped, priority, easing, keyframes, data.JOINTS))

    for script_name, source_path in (("MachineAnimator", HERE.parent / "PoliceGoose" / "GooseAnimator.client.luau"),
                                     ("MachineEffects", HERE / "MachineEffects.client.luau")):
        model.add(Item("Script", [
            xml_string("Name", script_name),
            f'<token name="RunContext">{RUN_CONTEXT_CLIENT}</token>',
            f'<ProtectedString name="Source"><![CDATA[{source_path.read_text(encoding="utf-8")}]]></ProtectedString>',
        ]))
    return model


def main():
    for rarity, colors in RARITIES.items():
        data = machine_data(colors)
        xml = ('<roblox xmlns:xmime="http://www.w3.org/2005/05/xmlmime" '
               'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
               'xsi:noNamespaceSchemaLocation="http://www.roblox.com/roblox.xsd" version="4">\n'
               "  <External>null</External>\n  <External>nil</External>\n"
               f"{build_model(rarity, data).to_xml()}</roblox>\n")
        out = HERE / f"AutoFisher_{rarity}.rbxmx"
        out.write_text(xml, encoding="utf-8")
        print(f"Wrote {out.name} ({len(data.PARTS)} parts, {len(data.JOINTS)} joints)")
        # The GLB cannot hide parts, so it leaves out the ones the model hides until the game asks for them.
        shown = [p for p in data.PARTS if not p[0].startswith(HIDDEN_AT_START)]
        export(SimpleNamespace(PARTS=shown, JOINTS=data.JOINTS, ANIMATIONS=data.ANIMATIONS),
               f"AutoFisher_{rarity}", HERE / f"AutoFisher_{rarity}.glb")


if __name__ == "__main__":
    main()
