"""Builds PoliceGoose.rbxmx (rig + KeyframeSequences + client animator) for Roblox Studio.

Run: python build_police_goose.py
Coordinates are in studs, ground at y = 0, the goose faces -Z (Roblox LookVector).
"""

import base64
import math
import struct
from pathlib import Path
from xml.sax.saxutils import escape

HERE = Path(__file__).parent


class CF:
    def __init__(self, pos=(0.0, 0.0, 0.0), rot=((1, 0, 0), (0, 1, 0), (0, 0, 1))):
        self.pos = tuple(float(v) for v in pos)
        self.rot = tuple(tuple(float(v) for v in row) for row in rot)

    def __mul__(self, other):
        r, o = self.rot, other.rot
        rot = tuple(tuple(sum(r[i][k] * o[k][j] for k in range(3)) for j in range(3)) for i in range(3))
        pos = tuple(sum(r[i][k] * other.pos[k] for k in range(3)) + self.pos[i] for i in range(3))
        return CF(pos, rot)

    def inverse(self):
        rt = tuple(tuple(self.rot[j][i] for j in range(3)) for i in range(3))
        pos = tuple(-sum(rt[i][k] * self.pos[k] for k in range(3)) for i in range(3))
        return CF(pos, rt)


def angles(rx=0, ry=0, rz=0):
    """Same as Roblox CFrame.Angles (degrees): Rx * Ry * Rz."""
    cx, sx = math.cos(math.radians(rx)), math.sin(math.radians(rx))
    cy, sy = math.cos(math.radians(ry)), math.sin(math.radians(ry))
    cz, sz = math.cos(math.radians(rz)), math.sin(math.radians(rz))
    x = CF(rot=((1, 0, 0), (0, cx, -sx), (0, sx, cx)))
    y = CF(rot=((cy, 0, sy), (0, 1, 0), (-sy, 0, cy)))
    z = CF(rot=((cz, -sz, 0), (sz, cz, 0), (0, 0, 1)))
    return x * y * z


def cf(x=0, y=0, z=0, rx=0, ry=0, rz=0):
    return CF((x, y, z)) * angles(rx, ry, rz)


WHITE = (245, 245, 240)
LID = (228, 228, 222)
NAVY = (31, 58, 104)
CAP_NAVY = (24, 40, 74)
BLACK = (28, 28, 30)
GOLD = (242, 194, 48)
ORANGE = (255, 140, 26)
DARK_ORANGE = (230, 112, 20)
EYE_WHITE = (255, 255, 255)
PUPIL = (18, 18, 20)
SILVER = (205, 208, 215)
BATON_GRIP = (70, 70, 76)


def cuff_ring(name, center, radius=0.17, segments=8):
    """A handcuff ring built from small blocks (no torus primitive in Roblox), lying in the Y-Z plane."""
    tangent = 2 * radius * math.tan(math.pi / segments) + 0.02
    parts = []
    for i in range(segments):
        a = 360 * i / segments + 180 / segments
        offset = (0, radius * math.cos(math.radians(a)), radius * math.sin(math.radians(a)))
        position = [c + o for c, o in zip(center, offset)]
        parts.append((f"{name}_{i + 1}", "block", (0.07, 0.07, tangent), cf(*position, rx=a), SILVER, "Cuffs"))
    return parts


# name, shape, size, rest CFrame, color, bone (the animated part it is welded to; None = it is a bone)
# shape: "ellipsoid" (Part + SpecialMesh Sphere), "block", "ball", "cylinder" (axis = local X), "wedge"
PARTS = [
    ("HumanoidRootPart", "block", (2, 2, 2), cf(0, 2.6, 0), WHITE, None),
    ("Body", "ellipsoid", (2.6, 2.2, 3.6), cf(0, 2.7, 0.3), NAVY, None),
    ("Belt", "ellipsoid", (2.75, 0.3, 3.8), cf(0, 2.25, 0.3), BLACK, "Body"),
    ("Buckle", "block", (0.45, 0.32, 0.1), cf(0, 2.25, -1.62), GOLD, "Body"),
    ("Badge", "block", (0.32, 0.38, 0.08), cf(-0.45, 3.05, -1.33, 20, 15, 0), GOLD, "Body"),
    ("NeckLower", "ellipsoid", (0.8, 1.5, 0.8), cf(0, 3.9, -1.3, -12), WHITE, None),
    ("NeckUpper", "ellipsoid", (0.7, 1.4, 0.7), cf(0, 4.95, -1.55, 8), WHITE, None),
    ("Head", "ellipsoid", (1.0, 1.0, 1.3), cf(0, 5.75, -1.75), WHITE, None),
    ("Beak", "wedge", (0.5, 0.32, 0.85), cf(0, 5.68, -2.65), ORANGE, "Head"),
    ("BeakLower", "block", (0.42, 0.14, 0.75), cf(0, 5.45, -2.6), DARK_ORANGE, None),
    ("WhistleMouth", "block", (0.12, 0.1, 0.35), cf(0, 5.55, -3.15), SILVER, "Head"),
    ("WhistleBarrel", "cylinder", (0.34, 0.3, 0.3), cf(0.1, 5.55, -3.38), SILVER, "Head"),
    ("EyeL", "ball", (0.32, 0.32, 0.32), cf(-0.3, 5.88, -2.15), EYE_WHITE, "Head"),
    ("EyeR", "ball", (0.32, 0.32, 0.32), cf(0.3, 5.88, -2.15), EYE_WHITE, "Head"),
    ("PupilL", "ball", (0.16, 0.16, 0.16), cf(-0.27, 5.86, -2.3), PUPIL, "Head"),
    ("PupilR", "ball", (0.16, 0.16, 0.16), cf(0.27, 5.86, -2.3), PUPIL, "Head"),
    ("LidL", "ball", (0.4, 0.4, 0.4), cf(-0.3, 5.88, -1.9), LID, None),
    ("LidR", "ball", (0.4, 0.4, 0.4), cf(0.3, 5.88, -1.9), LID, None),
    ("BrowL", "block", (0.36, 0.09, 0.1), cf(-0.3, 6.04, -2.22, 0, 0, -20), BLACK, "Head"),
    ("BrowR", "block", (0.36, 0.09, 0.1), cf(0.3, 6.04, -2.22, 0, 0, 20), BLACK, "Head"),
    ("CapBand", "cylinder", (0.25, 1.1, 1.1), cf(0, 6.2, -1.72, 0, 0, 90), BLACK, "Head"),
    ("CapCrown", "cylinder", (0.3, 1.25, 1.25), cf(0, 6.45, -1.72, 0, 0, 90), CAP_NAVY, "Head"),
    ("CapTop", "cylinder", (0.12, 1.45, 1.45), cf(0, 6.64, -1.72, 0, 0, 90), CAP_NAVY, "Head"),
    ("CapBrim", "block", (1.0, 0.08, 0.45), cf(0, 6.16, -2.4, -15), BLACK, "Head"),
    ("CapBadge", "block", (0.24, 0.24, 0.08), cf(0, 6.45, -2.37, 0, 0, 45), GOLD, "Head"),
    ("WingL", "ellipsoid", (0.45, 1.2, 2.5), cf(-1.32, 2.95, 0.45, -8), NAVY, None),
    ("WingTipL", "ellipsoid", (0.35, 0.8, 1.2), cf(-1.36, 3.05, 1.55, -15), WHITE, "WingL"),
    ("WingR", "ellipsoid", (0.45, 1.2, 2.5), cf(1.32, 2.95, 0.45, -8), NAVY, None),
    ("WingTipR", "ellipsoid", (0.35, 0.8, 1.2), cf(1.36, 3.05, 1.55, -15), WHITE, "WingR"),
    ("Tail", "ellipsoid", (1.1, 0.6, 1.1), cf(0, 3.25, 2.25, -30), WHITE, None),
    ("LegL", "block", (0.28, 1.5, 0.28), cf(-0.55, 0.95, 0.35), ORANGE, None),
    ("FootL", "wedge", (0.85, 0.22, 1.0), cf(-0.55, 0.11, 0.0), DARK_ORANGE, None),
    ("LegR", "block", (0.28, 1.5, 0.28), cf(0.55, 0.95, 0.35), ORANGE, None),
    ("FootR", "wedge", (0.85, 0.22, 1.0), cf(0.55, 0.11, 0.0), DARK_ORANGE, None),
    # Baton hangs from the front edge of the right wing, gripped near its top end.
    ("Baton", "cylinder", (1.6, 0.17, 0.17), cf(1.62, 2.1, -0.35, 0, 0, 90), BLACK, None),
    ("BatonGrip", "cylinder", (0.45, 0.21, 0.21), cf(1.62, 2.67, -0.35, 0, 0, 90), BATON_GRIP, "Baton"),
    ("BatonTip", "cylinder", (0.08, 0.2, 0.2), cf(1.62, 1.34, -0.35, 0, 0, 90), SILVER, "Baton"),
    # Handcuffs hooked on the left side of the belt.
    ("Cuffs", "block", (0.08, 0.2, 0.08), cf(-1.27, 2.25, -0.55), SILVER, None),
    *cuff_ring("CuffTop", (-1.27, 2.0, -0.55)),
    ("CuffChain1", "block", (0.05, 0.1, 0.05), cf(-1.27, 1.78, -0.55), SILVER, "Cuffs"),
    ("CuffChain2", "block", (0.05, 0.1, 0.05), cf(-1.27, 1.69, -0.55, 0, 90, 0), SILVER, "Cuffs"),
    *cuff_ring("CuffBottom", (-1.27, 1.45, -0.55)),
]

# part1, part0, pivot (world position at rest)
JOINTS = [
    ("Body", "HumanoidRootPart", (0, 2.7, 0.3)),
    ("NeckLower", "Body", (0, 3.3, -1.15)),
    ("NeckUpper", "NeckLower", (0, 4.4, -1.45)),
    ("Head", "NeckUpper", (0, 5.45, -1.6)),
    ("BeakLower", "Head", (0, 5.5, -2.25)),
    ("LidL", "Head", (-0.3, 5.88, -1.9)),
    ("LidR", "Head", (0.3, 5.88, -1.9)),
    ("WingL", "Body", (-1.2, 3.4, -0.6)),
    ("WingR", "Body", (1.2, 3.4, -0.6)),
    ("Tail", "Body", (0, 3.1, 1.8)),
    ("LegL", "Body", (-0.55, 1.65, 0.35)),
    ("FootL", "LegL", (-0.55, 0.22, 0.35)),
    ("LegR", "Body", (0.55, 1.65, 0.35)),
    ("FootR", "LegR", (0.55, 0.22, 0.35)),
    ("Baton", "WingR", (1.62, 2.7, -0.35)),
    ("Cuffs", "Body", (-1.27, 2.35, -0.55)),
]

HIP_HEIGHT = 1.6  # bottom of HumanoidRootPart (y = 1.6) to the ground

# Pose transforms (joint space, world-aligned at rest): +rx pitches nose/leg forward-up, +ry turns
# to the goose's left, +rz rolls its top to its left. Left wing opens with -rz, right wing with +rz.
P = cf


def wings(rz, rx=0):
    return {"WingL": P(rx=rx, rz=-rz), "WingR": P(rx=rx, rz=rz)}


def legs(swing, foot=None):
    foot = -swing if foot is None else foot
    return {"LegL": P(rx=swing), "LegR": P(rx=-swing), "FootL": P(rx=foot), "FootR": P(rx=-foot)}


LIDS_CLOSED = {"LidL": P(z=-0.3), "LidR": P(z=-0.3)}
LIDS_HALF = {"LidL": P(z=-0.17), "LidR": P(z=-0.17)}
BATON_RAISED = {"WingR": P(rz=55), "Baton": P(z=-0.5, rx=115)}
BATON_TAP = {"WingR": P(rz=45), "Baton": P(z=-0.5, rx=70)}
GLARE = {"Body": P(y=0.05), "NeckLower": P(rx=-10), "Head": P(rx=5), "BeakLower": P(rx=-12)}


def walk_frame(swing, roll, bob, neck):
    return {"Body": P(y=bob, rz=roll), "NeckLower": P(rx=-neck), "Head": P(rx=neck), "Cuffs": P(rx=swing * 0.5),
            **legs(swing), **wings(4)}


def run_frame(swing, roll, bob, flap):
    return {
        "Body": P(y=bob, rx=-10, rz=roll),
        "NeckLower": P(rx=-40),
        "NeckUpper": P(rx=10),
        "Head": P(rx=30),
        "BeakLower": P(rx=-20),
        "Tail": P(rx=-10),
        "Cuffs": P(rx=swing * 0.8),
        **legs(swing, foot=-swing * 0.75),
        **wings(flap),
    }


def fly_frame(flap, bob):
    return {
        "Body": P(y=bob, rx=-12),
        "NeckLower": P(rx=-45),
        "NeckUpper": P(rx=-5),
        "Head": P(rx=48),
        "Tail": P(rx=10),
        "LegL": P(rx=-75),
        "LegR": P(rx=-75),
        "FootL": P(rx=-20),
        "FootR": P(rx=-20),
        **wings(flap),
    }


def sleep_frame(breath):
    return {
        "Body": P(y=-1.45 + breath),
        "LegL": P(y=1.45),
        "LegR": P(y=1.45),
        "NeckLower": P(rx=-15),
        "NeckUpper": P(rx=-30),
        "Head": P(rx=-35 - breath * 100, rz=10),
        "Tail": P(rx=-15),
        "Baton": P(rx=-85),
        "Cuffs": P(rx=-70),
        **wings(-3 - breath * 20),
        **LIDS_CLOSED,
    }


def attack_windup(beak):
    return {
        "Body": P(rx=5),
        "NeckLower": P(rx=12),
        "NeckUpper": P(rx=15),
        "Head": P(rx=-20),
        "BeakLower": P(rx=beak),
        **wings(40),
    }


ATTACK_STRIKE = {
    "Body": P(z=-0.35, rx=-10),
    "NeckLower": P(rx=-50),
    "NeckUpper": P(rx=5),
    "Head": P(rx=25),
    "BeakLower": P(),
    **wings(55),
}

FAINT_DOWN = {
    "Body": P(x=-0.7, y=-1.35, rz=85),
    "NeckLower": P(rz=25),
    "Head": P(rx=-20, rz=20),
    "BeakLower": P(rx=-25),
    "WingR": P(rz=20),
    "LegL": P(rz=15),
    "LegR": P(rz=-15),
    **LIDS_CLOSED,
}

# name: (looped, priority, easing, [(time, {joint: transform})])
ANIMATIONS = {
    "Idle": (True, "Idle", "Cubic", [
        (0.0, {}),
        (0.6, {"Body": P(y=0.05), "NeckLower": P(rx=-3), "Head": P(rx=4), "Tail": P(ry=8)}),
        (1.2, {"Head": P(ry=25), "NeckUpper": P(rx=2)}),
        (1.8, {"Body": P(y=0.05), "Head": P(ry=-20), "Tail": P(ry=-8)}),
        (2.4, {}),
    ]),
    "Walk": (True, "Movement", "Cubic", [
        (0.0, walk_frame(20, 5, 0, 6)),
        (0.25, walk_frame(0, 0, 0.1, -2)),
        (0.5, walk_frame(-20, -5, 0, 6)),
        (0.75, walk_frame(0, 0, 0.1, -2)),
        (1.0, walk_frame(20, 5, 0, 6)),
    ]),
    "Run": (True, "Movement", "Linear", [
        (0.0, run_frame(40, 4, 0, 40)),
        (0.11, run_frame(0, 0, 0.18, 65)),
        (0.22, run_frame(-40, -4, 0, 40)),
        (0.33, run_frame(0, 0, 0.18, 65)),
        (0.44, run_frame(40, 4, 0, 40)),
    ]),
    "Fly": (True, "Movement", "Cubic", [
        (0.0, fly_frame(140, 1.0)),
        (0.25, fly_frame(25, 1.35)),
        (0.5, fly_frame(140, 1.0)),
    ]),
    "Attack": (True, "Action", "Cubic", [
        (0.0, attack_windup(-25)),
        (0.3, attack_windup(-35)),
        (0.42, ATTACK_STRIKE),
        (0.55, ATTACK_STRIKE),
        (0.7, attack_windup(-25)),
    ]),
    "Sleep": (True, "Idle", "Cubic", [
        (0.0, sleep_frame(0)),
        (1.5, sleep_frame(0.08)),
        (3.0, sleep_frame(0)),
    ]),
    "Faint": (False, "Action", "Cubic", [
        (0.0, {}),
        (0.25, {"Body": P(rx=5), "NeckLower": P(rz=-15), "Head": P(rz=25), **LIDS_HALF}),
        (0.5, {"Body": P(rx=-3), "NeckLower": P(rz=15), "Head": P(rz=-25), "BeakLower": P(rx=-15), **LIDS_HALF}),
        (0.75, {"NeckLower": P(rz=-10), "Head": P(rz=20), "LegL": P(rx=15), "LegR": P(rx=-10), **LIDS_HALF}),
        (1.1, FAINT_DOWN),
        (1.25, {**FAINT_DOWN, "Body": P(x=-0.7, y=-1.15, rz=82)}),
        (1.4, FAINT_DOWN),
        (1.7, {**FAINT_DOWN, "LegR": P(rx=25, rz=-15)}),
        (1.85, FAINT_DOWN),
        (2.0, {**FAINT_DOWN, "LegR": P(rx=25, rz=-15)}),
        (2.2, FAINT_DOWN),
    ]),
    "Alert": (False, "Action", "Cubic", [
        (0.0, {}),
        (0.25, {"Body": P(y=0.1), "NeckLower": P(rx=12), "NeckUpper": P(y=0.25, rx=8), "Head": P(rx=-15), "Tail": P(rx=15)}),
        (0.55, {"Body": P(y=0.1), "NeckLower": P(rx=12), "NeckUpper": P(y=0.25, rx=8), "Head": P(rx=-15, ry=35), "Tail": P(rx=15)}),
        (0.85, {"Body": P(y=0.1), "NeckLower": P(rx=12), "NeckUpper": P(y=0.25, rx=8), "Head": P(rx=-15, ry=-35), "Tail": P(rx=15)}),
        (1.1, {"Body": P(y=0.1), "NeckLower": P(rx=12), "NeckUpper": P(y=0.25, rx=8), "Head": P(rx=-25), "Tail": P(rx=15)}),
        (1.4, {"Body": P(y=0.1), "NeckLower": P(rx=12), "NeckUpper": P(y=0.25, rx=8), "Head": P(rx=-25), "Tail": P(rx=15)}),
    ]),
    "Whistle": (False, "Action", "Cubic", [
        (0.0, {}),
        (0.2, {"Body": P(y=0.15, rx=6), "NeckLower": P(rx=8), "Head": P(rx=30), "Tail": P(rx=20), **wings(20)}),
        (0.35, {"Body": P(y=0.15, rx=6), "NeckLower": P(rx=8), "Head": P(rx=40), "Tail": P(rx=20), **wings(60)}),
        (0.5, {"Body": P(y=0.15, rx=6), "NeckLower": P(rx=8), "Head": P(rx=30), "Tail": P(rx=20), **wings(45)}),
        (0.65, {"Body": P(y=0.15, rx=6), "NeckLower": P(rx=8), "Head": P(rx=42), "Tail": P(rx=20), **wings(65)}),
        (0.8, {"Body": P(y=0.15, rx=6), "NeckLower": P(rx=8), "Head": P(rx=30), "Tail": P(rx=20), **wings(40)}),
        (1.0, {}),
    ]),
    "Stunned": (False, "Action", "Cubic", [
        (0.0, {}),
        (0.12, {"Body": P(z=0.4, rx=12), "NeckLower": P(rx=15), "Head": P(rx=10), "BeakLower": P(rx=-15), **wings(30), **LIDS_HALF}),
        (0.3, {"Body": P(z=0.3, rx=8), "NeckLower": P(rx=10), "Head": P(rx=5, rz=20), "BeakLower": P(rx=-15), **wings(25), **LIDS_HALF}),
        (0.45, {"Body": P(z=0.2, rx=5), "NeckLower": P(rx=6), "Head": P(rz=-20), "BeakLower": P(rx=-10), **wings(20), **LIDS_HALF}),
        (0.6, {"Body": P(z=0.1), "Head": P(rz=12), **wings(10)}),
        (0.75, {"Head": P(rz=-6)}),
        (0.9, {}),
    ]),
    "Search": (True, "Movement", "Cubic", [
        (0.0, {"NeckLower": P(rx=-25), "NeckUpper": P(rx=-10), "Head": P(rx=20)}),
        (0.6, {"NeckLower": P(rx=-25, ry=15), "NeckUpper": P(rx=-10), "Head": P(rx=20, ry=40)}),
        (1.2, {"NeckLower": P(rx=-30), "NeckUpper": P(rx=-10), "Head": P(rx=30), "BeakLower": P(rx=-10)}),
        (1.8, {"NeckLower": P(rx=-25, ry=-15), "NeckUpper": P(rx=-10), "Head": P(rx=20, ry=-40)}),
        (2.4, {"NeckLower": P(rx=-25), "NeckUpper": P(rx=-10), "Head": P(rx=20)}),
    ]),
    "Threaten": (False, "Action", "Cubic", [
        (0.0, {}),
        (0.3, {**GLARE, **BATON_RAISED}),
        (0.5, {**GLARE, **BATON_TAP}),
        (0.7, {**GLARE, **BATON_RAISED}),
        (0.9, {**GLARE, **BATON_TAP}),
        (1.1, {**GLARE, **BATON_RAISED, "WingL": P(rz=-20), "Cuffs": P(rz=-35)}),
        (1.3, {**GLARE, **BATON_RAISED, "WingL": P(rz=-20), "Cuffs": P(rz=-5)}),
        (1.5, {**GLARE, **BATON_RAISED, "WingL": P(rz=-20), "Cuffs": P(rz=-35)}),
        (1.7, {**GLARE, **BATON_RAISED, "WingL": P(rz=-20), "Cuffs": P(rz=-5), "Head": P(rx=5, ry=20)}),
        (2.4, {}),
    ]),
}

MATERIAL = {"SmoothPlastic": 272, "Metal": 1088}
PART_SHAPE = {"ball": 0, "block": 1, "ellipsoid": 1, "cylinder": 2}
PRIORITY = {"Idle": 0, "Movement": 1, "Action": 2}
POSE_EASING_STYLE = {"Linear": 0, "Cubic": 3}
POSE_EASING_DIRECTION_INOUT = 2
RIG_TYPE_R15 = 1
DISPLAY_DISTANCE_NONE = 2
RUN_CONTEXT_CLIENT = 2
MODEL_STREAMING_ATOMIC = 1


def xml_cframe(name, c):
    (r00, r01, r02), (r10, r11, r12), (r20, r21, r22) = c.rot
    values = dict(X=c.pos[0], Y=c.pos[1], Z=c.pos[2], R00=r00, R01=r01, R02=r02,
                  R10=r10, R11=r11, R12=r12, R20=r20, R21=r21, R22=r22)
    inner = "".join(f"<{k}>{v:.6g}</{k}>" for k, v in values.items())
    return f'<CoordinateFrame name="{name}">{inner}</CoordinateFrame>'


def xml_vector3(name, v):
    return f'<Vector3 name="{name}"><X>{v[0]:.6g}</X><Y>{v[1]:.6g}</Y><Z>{v[2]:.6g}</Z></Vector3>'


def xml_color3uint8(rgb):
    value = 0xFF000000 | (rgb[0] << 16) | (rgb[1] << 8) | rgb[2]
    return f'<Color3uint8 name="Color3uint8">{value}</Color3uint8>'


def xml_string(name, value):
    return f'<string name="{name}">{escape(value)}</string>'


def xml_attributes(attributes):
    """Roblox binary attribute format; only string values are needed here."""
    data = struct.pack("<I", len(attributes))
    for key, value in attributes.items():
        key_bytes, value_bytes = key.encode(), value.encode()
        data += struct.pack("<I", len(key_bytes)) + key_bytes + b"\x02"
        data += struct.pack("<I", len(value_bytes)) + value_bytes
    return f'<BinaryString name="AttributesSerialize">{base64.b64encode(data).decode()}</BinaryString>'


class Item:
    counter = 0

    def __init__(self, class_name, props):
        Item.counter += 1
        self.ref = f"RBX{Item.counter:04d}"
        self.class_name = class_name
        self.props = props
        self.children = []

    def add(self, child):
        self.children.append(child)
        return child

    def to_xml(self, indent=1):
        pad = "  " * indent
        props = "".join(self.props)
        children = "".join(child.to_xml(indent + 1) for child in self.children)
        return (f'{pad}<Item class="{self.class_name}" referent="{self.ref}">'
                f"<Properties>{props}</Properties>\n{children}{pad}</Item>\n")


def build_part(name, shape, size, rest, color, anchored=False):
    material = "Metal" if color == SILVER else "SmoothPlastic"
    props = [
        xml_string("Name", name),
        xml_cframe("CFrame", rest),
        xml_vector3("size", size),
        xml_color3uint8(color),
        f'<token name="Material">{MATERIAL[material]}</token>',
        f'<bool name="Anchored">{"true" if anchored else "false"}</bool>',
        f'<bool name="CanCollide">{"true" if name == "Body" else "false"}</bool>',
        '<token name="TopSurface">0</token>',
        '<token name="BottomSurface">0</token>',
    ]
    if name == "HumanoidRootPart":
        props.append('<float name="Transparency">1</float>')
    if shape != "wedge":
        props.append(f'<token name="shape">{PART_SHAPE[shape]}</token>')
    part = Item("WedgePart" if shape == "wedge" else "Part", props)
    if shape == "ellipsoid":
        part.add(Item("SpecialMesh", [
            xml_string("Name", "Mesh"),
            '<token name="MeshType">3</token>',
            xml_vector3("Scale", (1, 1, 1)),
        ]))
    return part


def build_joint(class_name, name, part0, part1, pivot):
    c0 = part0.rest.inverse() * pivot
    c1 = part1.rest.inverse() * pivot
    return Item(class_name, [
        xml_string("Name", name),
        f'<Ref name="Part0">{part0.ref}</Ref>',
        f'<Ref name="Part1">{part1.ref}</Ref>',
        xml_cframe("C0", c0),
        xml_cframe("C1", c1),
    ])


def build_keyframe_sequence(name, looped, priority, easing, keyframes, joints=JOINTS):
    sequence = Item("KeyframeSequence", [
        xml_string("Name", name),
        f'<bool name="Loop">{"true" if looped else "false"}</bool>',
        f'<token name="Priority">{PRIORITY[priority]}</token>',
    ])
    children = {}
    for part1, part0, _ in joints:
        children.setdefault(part0, []).append(part1)

    def build_pose(pose_name, transforms):
        pose = Item("Pose", [
            xml_string("Name", pose_name),
            xml_cframe("CFrame", transforms.get(pose_name, CF())),
            f'<token name="EasingStyle">{POSE_EASING_STYLE[easing]}</token>',
            f'<token name="EasingDirection">{POSE_EASING_DIRECTION_INOUT}</token>',
            '<float name="Weight">1</float>',
        ])
        for child in children.get(pose_name, []):
            pose.add(build_pose(child, transforms))
        return pose

    for time, transforms in keyframes:
        keyframe = sequence.add(Item("Keyframe", [xml_string("Name", "Keyframe"), f'<float name="Time">{time:.6g}</float>']))
        keyframe.add(build_pose("HumanoidRootPart", transforms))
    return sequence


def build_model():
    parts = {}
    for name, shape, size, rest, color, _ in PARTS:
        part = build_part(name, shape, size, rest, color)
        part.rest = rest
        parts[name] = part

    model = Item("Model", [
        xml_string("Name", "PoliceGoose"),
        f'<Ref name="PrimaryPart">{parts["HumanoidRootPart"].ref}</Ref>',
        f'<token name="ModelStreamingMode">{MODEL_STREAMING_ATOMIC}</token>',
        xml_attributes({"Anim": "Idle"}),
    ])
    for part in parts.values():
        model.add(part)

    for part1, part0, pivot in JOINTS:
        parts[part0].add(build_joint("Motor6D", part1, parts[part0], parts[part1], CF(pivot)))
    for name, _, _, rest, _, bone in PARTS:
        if bone:
            parts[bone].add(build_joint("Weld", name, parts[bone], parts[name], rest))

    model.add(Item("Humanoid", [
        xml_string("Name", "Humanoid"),
        f'<token name="RigType">{RIG_TYPE_R15}</token>',
        f'<float name="HipHeight">{HIP_HEIGHT}</float>',
        f'<token name="DisplayDistanceType">{DISPLAY_DISTANCE_NONE}</token>',
        '<bool name="RequiresNeck">false</bool>',
        '<float name="WalkSpeed">10</float>',
    ]))

    folder = model.add(Item("Folder", [xml_string("Name", "Animations")]))
    for name, (looped, priority, easing, keyframes) in ANIMATIONS.items():
        folder.add(build_keyframe_sequence(name, looped, priority, easing, keyframes))

    for script_name in ("GooseAnimator", "GooseSounds"):
        source = (HERE / f"{script_name}.client.luau").read_text(encoding="utf-8")
        model.add(Item("Script", [
            xml_string("Name", script_name),
            f'<token name="RunContext">{RUN_CONTEXT_CLIENT}</token>',
            f'<ProtectedString name="Source"><![CDATA[{source}]]></ProtectedString>',
        ]))
    return model


def main():
    model = build_model()
    xml = ('<roblox xmlns:xmime="http://www.w3.org/2005/05/xmlmime" '
           'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
           'xsi:noNamespaceSchemaLocation="http://www.roblox.com/roblox.xsd" version="4">\n'
           "  <External>null</External>\n  <External>nil</External>\n"
           f"{model.to_xml()}</roblox>\n")
    out = HERE / "PoliceGoose.rbxmx"
    out.write_text(xml, encoding="utf-8")
    print(f"Wrote {out} ({len(PARTS)} parts, {len(JOINTS)} joints, {len(ANIMATIONS)} animations)")


if __name__ == "__main__":
    main()
