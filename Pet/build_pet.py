"""Builds Pet_<Kind>.rbxmx and .glb (rig + KeyframeSequences + client scripts) for the six pets that hatch from the eggs.

Run: python build_pet.py
Reuses the rbxmx writer of ../PoliceGoose and the color and part helpers of ../Egg. Coordinates are in studs at design
size (about 2.8 tall without hat), ground at y = 0, the pet faces -Z. Every pet is scaled by its rarity at the end.
All pets share one chibi biped frame (body, big head with big eyes and eyelids, two arms, two legs, a tail) with
a Humanoid so they can follow the player (Humanoid:MoveTo); each kind only differs in species, colors, outfit and
the job it does (a held Tool, a Hat and a Job animation). One egg hatches one pet.
"""

import sys
from pathlib import Path
from types import SimpleNamespace

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "Egg"))

from build_egg import (  # noqa: E402
    BLUE, GOLD_DARK, GREEN, LAVENDER, MATERIAL_NEON, PEARL, PINK, PURPLE, RAINBOW, RED, WOOD, ring_around, set_prop,
    shade,
)
from build_police_goose import (  # noqa: E402
    BLACK, CAP_NAVY, CF, DARK_ORANGE, DISPLAY_DISTANCE_NONE, GOLD, MODEL_STREAMING_ATOMIC, NAVY, ORANGE, RIG_TYPE_R15,
    RUN_CONTEXT_CLIENT, SILVER, WHITE, Item, build_joint, build_keyframe_sequence, build_part, cf, xml_attributes,
    xml_string,
)
from export_glb import export  # noqa: E402

P = cf
ROOT_Y = 0.9
HIP_HEIGHT = ROOT_Y - 0.5  # bottom of the HumanoidRootPart to the ground


def ell(name, size, pos, color, bone, rot=(0, 0, 0)):
    return (name, "ellipsoid", size, cf(*pos, *rot), color, bone)


def ball(name, size, pos, color, bone):
    return (name, "ball", (size,) * 3, cf(*pos), color, bone)


def block(name, size, pos, color, bone, rot=(0, 0, 0)):
    return (name, "block", size, cf(*pos, *rot), color, bone)


def cyl_y(name, y_lo, y_hi, dia, color, bone, x=0.0, z=0.0):
    """Cylinder standing on the Y axis (Roblox cylinders lie along X, so it is turned 90 degrees)."""
    return (name, "cylinder", (y_hi - y_lo, dia, dia), cf(x, (y_lo + y_hi) / 2, z, 0, 0, 90), color, bone)


# L is the pet's left (-X, it faces -Z), R its right (+X).
SIDES = (("L", -1), ("R", 1))


# ---------------------------------------------------------------- shared frame

def frame_parts(c):
    """Body, belly, arms with hands, legs with feet, head, big eyes with shine, eyelids and blush."""
    parts = [
        ("HumanoidRootPart", "block", (1, 1, 1), cf(0, ROOT_Y, 0), WHITE, None),
        ell("Body", (1.35, 1.2, 1.15), (0, 1.2, 0), c.fur, None),
        ell("Belly", (0.9, 0.85, 0.4), (0, 1.12, -0.42), c.belly, "Body"),
        ell("Head", (1.6, 1.4, 1.45), (0, 2.25, -0.05), c.fur, None),
    ]
    for side, x in SIDES:
        parts += [
            cyl_y(f"Leg{side}", 0.15, 0.7, 0.34, c.leg, None, x * 0.35, 0),
            ell(f"Foot{side}", (0.5, 0.2, 0.7), (x * 0.35, 0.1, -0.1), c.paw, f"Leg{side}"),
            ell(f"Arm{side}", c.arm, (x * 0.82, 1.2, -0.05), c.sleeve, None, (0, 0, -x * 8)),
            ball(f"Hand{side}", c.arm[0] * 0.95, (x * 0.86, 0.82, -0.05), c.paw, f"Arm{side}"),
            ell(f"Eye{side}", (0.27, 0.36, 0.14), (x * 0.42, 2.3, -0.72), BLACK, "Head"),
            ball(f"Shine{side}", 0.12, (x * 0.38, 2.4, -0.79), WHITE, "Head"),
            ball(f"ShineB{side}", 0.06, (x * 0.47, 2.2, -0.79), WHITE, "Head"),
            ell(f"Blush{side}", (0.26, 0.14, 0.08), (x * 0.62, 2.04, -0.62), PINK, "Head"),
            # The lid sits inside the head behind the eye; moving it forward (z -) closes the eye.
            ell(f"Lid{side}", (0.4, 0.5, 0.26), (x * 0.42, 2.3, -0.56), c.fur, None),
        ]
    return parts


FRAME_JOINTS = [
    ("Body", "HumanoidRootPart", (0, 0.7, 0)),
    ("Head", "Body", (0, 1.7, 0)),
    ("ArmL", "Body", (-0.7, 1.55, 0)),
    ("ArmR", "Body", (0.7, 1.55, 0)),
    ("LegL", "HumanoidRootPart", (-0.35, 0.7, 0)),
    ("LegR", "HumanoidRootPart", (0.35, 0.7, 0)),
    ("Tail", "Body", (0, 0.9, 0.5)),
    ("LidL", "Head", (-0.42, 2.3, -0.56)),
    ("LidR", "Head", (0.42, 2.3, -0.56)),
]


# ---------------------------------------------------------------- species: faces, ears, tails

def cat_face(c, ear_inner=PINK):
    parts = [
        ell("Muzzle", (0.55, 0.36, 0.32), (0, 2.02, -0.68), c.belly, "Head"),
        ball("Nose", 0.14, (0, 2.12, -0.84), PINK, "Head"),
        block("Smile", (0.26, 0.03, 0.04), (0, 1.94, -0.84), BLACK, "Head"),
        ell("Tail", (0.32, 1.0, 0.32), (0, 1.5, 0.78), c.fur, None, (20, 0, 0)),
        ell("TailTip", (0.34, 0.34, 0.34), (0, 1.95, 0.93), c.tail_tip, "Tail", (20, 0, 0)),
    ]
    for side, x in SIDES:
        parts += [
            ell(f"Ear{side}", (0.5, 0.64, 0.22), (x * 0.62, 3.0, -0.05), c.fur, None, (0, 0, -x * 18)),
            ell(f"EarInner{side}", (0.28, 0.4, 0.1), (x * 0.62, 2.98, -0.15), ear_inner, f"Ear{side}",
                (0, 0, -x * 18)),
        ]
        for i, (dy, tilt) in enumerate(((0.06, 12), (0.0, 0), (-0.06, -12))):
            parts.append(ell(f"Whisker{side}{i}", (0.5, 0.03, 0.03), (x * 0.66, 2.0 + dy, -0.62), WHITE, "Head",
                             (0, 0, -x * tilt)))
    joints = [("EarL", "Head", (-0.62, 2.85, -0.05)), ("EarR", "Head", (0.62, 2.85, -0.05))]
    return parts, joints


def dog_face(c):
    parts = [
        ell("Muzzle", (0.72, 0.5, 0.55), (0, 1.98, -0.72), c.belly, "Head"),
        ball("Nose", 0.22, (0, 2.12, -0.97), BLACK, "Head"),
        ell("Tongue", (0.2, 0.06, 0.26), (0, 1.78, -0.9), PINK, "Head"),
        block("Smile", (0.34, 0.03, 0.04), (0, 1.86, -0.96), BLACK, "Head"),
        ell("Tail", (0.3, 0.75, 0.3), (0, 1.25, 0.78), c.fur, None, (40, 0, 0)),
    ]
    for side, x in SIDES:
        parts.append(ell(f"Ear{side}", (0.42, 0.85, 0.26), (x * 0.88, 2.45, -0.05), c.ear, None, (0, 0, x * 12)))
    joints = [("EarL", "Head", (-0.75, 2.85, -0.05)), ("EarR", "Head", (0.75, 2.85, -0.05))]
    return parts, joints


# ---------------------------------------------------------------- the six pets

def cat_pot():
    """Mèo Đội Nồi, a chef: a rice-cooker lid as a hat (like the Starter egg), an apron, a ladle."""
    c = SimpleNamespace(fur=(255, 160, 50), belly=(255, 236, 200), leg=(255, 160, 50), paw=(255, 236, 200),
                        sleeve=(255, 160, 50), arm=(0.32, 0.75, 0.32), tail_tip=(255, 236, 200))
    parts = frame_parts(c)
    face, joints = cat_face(c)
    parts += face
    stripe = shade(c.fur, 0.8)
    for i, (x, rz) in enumerate(((-0.25, 12), (0, 0), (0.25, -12))):
        parts.append(ell(f"Stripe{i}", (0.14, 0.34, 0.08), (x, 2.82, -0.62), stripe, "Head", (-18, 0, rz)))
    for i, y in enumerate((1.4, 1.1)):
        parts.append(ell(f"BodyStripe{i}", (0.2, 0.1, 0.1), (-0.66, y, -0.2), stripe, "Body"))
    parts += [
        ell("Apron", (1.0, 0.9, 0.2), (0, 1.1, -0.56), WHITE, "Body"),
        block("ApronPocket", (0.4, 0.28, 0.06), (0, 0.95, -0.67), shade(WHITE, 0.9), "Body"),
        # Rice-cooker lid hat: silver plate and dome, black handle, two latches.
        cyl_y("Hat", 2.95, 3.12, 1.1, SILVER, None),
        ell("HatDome", (0.9, 0.42, 0.9), (0, 3.12, -0.05), SILVER, "Hat"),
        block("HatHandle", (0.5, 0.1, 0.14), (0, 3.4, -0.05), BLACK, "Hat"),
        block("HatPostL", (0.1, 0.22, 0.12), (-0.17, 3.3, -0.05), BLACK, "Hat"),
        block("HatPostR", (0.1, 0.22, 0.12), (0.17, 3.3, -0.05), BLACK, "Hat"),
        # Ladle in the right hand.
        cyl_y("Tool", 0.82, 1.9, 0.11, SILVER, None, 0.86, -0.12),
        ell("LadleBowl", (0.34, 0.2, 0.34), (0.86, 1.97, -0.12), SILVER, "Tool"),
    ]
    joints += [("Hat", "Head", (0, 2.95, -0.05)), ("Tool", "ArmR", (0.86, 0.82, -0.12))]
    job = [
        (0.0, {}),
        (0.4, {"ArmR": P(rx=175), "Tool": P(rz=25), "Head": P(rx=5)}),
        (0.8, {"ArmR": P(rx=160), "Tool": P(rz=55), "Hat": P(y=-0.1), "Head": P(rx=-6), "EarL": P(rz=15),
               "EarR": P(rz=-15)}),
        (1.2, {"ArmR": P(rx=175), "Tool": P(rz=25), "Hat": P(y=0.04), "Head": P(rx=3)}),
        (1.6, {"ArmR": P(rx=160), "Tool": P(rz=55), "Hat": P(y=-0.1), "Head": P(rx=-6), "EarL": P(rz=15),
               "EarR": P(rz=-15)}),
        (2.0, {"Head": P(rz=8), "Hat": P(rz=5)}),
        (2.4, {}),
    ]
    return parts, joints, job


def dog_baker():
    """Chó Bánh Mì, a baker: a tall chef hat, an apron, a baguette that he swings."""
    c = SimpleNamespace(fur=(215, 160, 90), belly=(255, 235, 200), leg=(215, 160, 90), paw=(255, 235, 200),
                        sleeve=(215, 160, 90), arm=(0.32, 0.75, 0.32), ear=(170, 115, 55))
    parts = frame_parts(c)
    face, joints = dog_face(c)
    parts += face
    parts += [
        ell("Apron", (1.0, 0.9, 0.2), (0, 1.1, -0.56), WHITE, "Body"),
        ell("ApronBread", (0.3, 0.16, 0.06), (0, 1.12, -0.68), (230, 190, 120), "Body"),
        cyl_y("Hat", 2.9, 3.1, 1.2, WHITE, None),
        ell("HatPuff", (1.25, 0.95, 1.25), (0, 3.45, -0.05), WHITE, "Hat"),
        ell("HatPuffL", (0.7, 0.6, 0.7), (-0.42, 3.38, -0.05), WHITE, "Hat"),
        ell("HatPuffR", (0.7, 0.6, 0.7), (0.42, 3.38, -0.05), WHITE, "Hat"),
        # Baguette in the right hand with three diagonal cuts.
        ("Tool", "ellipsoid", (0.3, 1.5, 0.3), cf(0.86, 1.3, -0.12), (225, 175, 100), None),
    ]
    for i, y in enumerate((0.95, 1.3, 1.65)):
        parts.append(block(f"BaguetteCut{i}", (0.34, 0.07, 0.05), (0.86, y, -0.26), (190, 130, 65), "Tool", (0, 0, 28)))
    joints += [("Hat", "Head", (0, 2.9, -0.05)), ("Tool", "ArmR", (0.86, 0.82, -0.12))]
    job = [
        (0.0, {}),
        (0.4, {"ArmR": P(rx=160), "Body": P(rx=6), "Tail": P(ry=20), "Head": P(rx=6)}),
        (0.8, {"ArmR": P(rx=50), "Tool": P(rx=20), "Body": P(rx=-10), "Head": P(rx=-8), "Tail": P(ry=-20)}),
        (1.2, {"ArmR": P(rx=70), "Tail": P(ry=20), "Head": P(rx=-4)}),
        (1.6, {"ArmR": P(rx=120), "Head": P(rx=8), "Tail": P(ry=-20), "Body": P(y=0.05)}),
        (2.0, {"ArmR": P(rx=30), "Tail": P(ry=12)}),
        (2.4, {}),
    ]
    return parts, joints, job


def duck_muscle():
    """Vịt Cơ Bắp, a fitness coach: a tank top, a headband, big arms, a dumbbell."""
    c = SimpleNamespace(fur=GOLD, belly=(255, 236, 170), leg=ORANGE, paw=ORANGE, sleeve=GOLD, arm=(0.5, 0.95, 0.5))
    parts = frame_parts(c)
    parts += [
        ell("Beak", (0.85, 0.3, 0.6), (0, 2.05, -0.88), ORANGE, "Head"),
        ell("BeakLower", (0.7, 0.14, 0.5), (0, 1.9, -0.85), DARK_ORANGE, "Head"),
        ell("Tail", (0.45, 0.35, 0.45), (0, 1.15, 0.65), GOLD, None, (-25, 0, 0)),
        ell("Tuft", (0.2, 0.4, 0.2), (0, 3.0, -0.1), GOLD, "Head", (-10, 0, 0)),
        ell("Tank", (1.42, 0.85, 1.22), (0, 1.2, 0), WHITE, "Body"),
        ell("TankBolt", (0.3, 0.45, 0.1), (0, 1.2, -0.6), BLUE, "Body"),
        cyl_y("Headband", 2.5, 2.74, 1.52, BLUE, None),
        ell("HeadbandKnot", (0.3, 0.3, 0.3), (0, 2.62, 0.78), BLUE, "Headband"),
        ell("HeadbandTailL", (0.14, 0.55, 0.08), (-0.14, 2.35, 0.9), BLUE, "Headband", (0, 0, 15)),
        ell("HeadbandTailR", (0.14, 0.55, 0.08), (0.14, 2.35, 0.9), BLUE, "Headband", (0, 0, -15)),
        # Dumbbell held across the right hand.
        ("Tool", "cylinder", (1.1, 0.1, 0.1), cf(0.86, 0.82, -0.12), SILVER, None),
        ("PlateL", "cylinder", (0.16, 0.5, 0.5), cf(0.4, 0.82, -0.12), BLACK, "Tool"),
        ("PlateR", "cylinder", (0.16, 0.5, 0.5), cf(1.32, 0.82, -0.12), BLACK, "Tool"),
    ]
    for side, x in SIDES:
        parts += [
            ball(f"Biceps{side}", 0.5, (x * 0.88, 1.35, -0.08), GOLD, f"Arm{side}"),
            block(f"Brow{side}", (0.42, 0.1, 0.1), (x * 0.42, 2.62, -0.74), BLACK, "Head", (0, 0, x * 14)),
        ]
    joints = [("Tool", "ArmR", (0.86, 0.82, -0.12)), ("Headband", "Head", (0, 2.62, -0.05))]
    job = [
        (0.0, {}),
        (0.4, {"Body": P(y=-0.1), "ArmL": P(rz=35), "ArmR": P(rz=35), "Head": P(rx=5)}),
        (0.8, {"Body": P(y=0.05), "ArmL": P(rz=-100), "ArmR": P(rz=100), "Head": P(rx=10)}),
        (1.2, {"Body": P(y=0.0), "ArmL": P(rz=-110), "ArmR": P(rz=110), "Head": P(rx=12)}),
        (1.6, {"Body": P(y=0.1), "ArmL": P(rz=-120), "ArmR": P(rz=120), "Head": P(rx=8)}),
        (2.0, {"Body": P(y=0.0), "ArmL": P(rz=-60), "ArmR": P(rz=60)}),
        (2.4, {}),
    ]
    return parts, joints, job


def cat_magician():
    """Mèo Ảo Thuật Gia: a top hat that floats up in the trick, a bow tie, a cape, a wand."""
    c = SimpleNamespace(fur=PURPLE, belly=LAVENDER, leg=PURPLE, paw=LAVENDER, sleeve=PURPLE, arm=(0.32, 0.75, 0.32),
                        tail_tip=LAVENDER)
    parts = frame_parts(c)
    face, joints = cat_face(c, ear_inner=LAVENDER)
    parts += face
    parts += [
        block("Cape", (1.5, 1.5, 0.1), (0, 1.25, 0.66), (60, 40, 120), "Body"),
        ell("BowL", (0.3, 0.2, 0.15), (-0.2, 1.68, -0.6), RED, "Body", (0, 0, 20)),
        ell("BowR", (0.3, 0.2, 0.15), (0.2, 1.68, -0.6), RED, "Body", (0, 0, -20)),
        ball("BowKnot", 0.14, (0, 1.68, -0.62), RED, "Body"),
        # Top hat: brim, tall crown, pink band and a little star.
        cyl_y("Hat", 2.92, 3.0, 1.3, BLACK, None),
        cyl_y("HatCrown", 3.0, 3.75, 0.85, BLACK, "Hat"),
        cyl_y("HatBand", 3.0, 3.2, 0.9, PINK, "Hat"),
        block("HatStar", (0.2, 0.2, 0.06), (0, 3.5, -0.44), GOLD, "Hat", (0, 0, 45)),
        # Wand in the right hand: black stick, white tips.
        cyl_y("Tool", 0.82, 1.6, 0.07, BLACK, None, 0.86, -0.12),
        cyl_y("WandTip", 1.5, 1.6, 0.09, WHITE, "Tool", 0.86, -0.12),
    ]
    joints += [("Hat", "Head", (0, 2.95, -0.05)), ("Tool", "ArmR", (0.86, 0.82, -0.12))]
    job = [
        (0.0, {}),
        (0.4, {"ArmR": P(rx=100), "Tool": P(rx=-10), "Head": P(rx=5), "Hat": P(y=0.05)}),
        (0.8, {"ArmR": P(rx=130), "Tool": P(rx=-40), "Hat": P(y=0.55, rz=12), "Head": P(rx=8)}),
        (1.2, {"ArmR": P(rx=125), "Hat": P(y=0.7, rz=-10), "Head": P(rx=8)}),
        (1.6, {"ArmR": P(rx=60), "Hat": P(y=0.15, rz=6), "Body": P(rx=-10), "Head": P(rx=-12)}),
        (2.0, {"Body": P(rx=-10), "Head": P(rx=-12)}),
        (2.4, {}),
    ]
    return parts, joints, job


def dog_k9():
    """Chó K9 Cảnh Sát: a navy police cap with a badge, a vest, a baton; he salutes (the goose is police too)."""
    c = SimpleNamespace(fur=(230, 180, 80), belly=(255, 240, 200), leg=(230, 180, 80), paw=(255, 240, 200),
                        sleeve=(230, 180, 80), arm=(0.32, 0.75, 0.32), ear=(150, 100, 40))
    parts = frame_parts(c)
    face, joints = dog_face(c)
    parts += face
    parts += [
        ell("Vest", (1.45, 0.9, 1.25), (0, 1.15, 0), NAVY, "Body"),
        block("VestBadge", (0.2, 0.22, 0.06), (-0.3, 1.45, -0.6), GOLD, "Body", (0, 0, 15)),
        block("VestK9", (0.5, 0.2, 0.05), (0.15, 1.0, -0.62), WHITE, "Body"),
        cyl_y("Hat", 2.9, 3.05, 1.2, CAP_NAVY, None),
        cyl_y("HatCrown", 3.05, 3.3, 1.0, CAP_NAVY, "Hat"),
        block("HatBrim", (0.95, 0.08, 0.4), (0, 2.95, -0.85), BLACK, "Hat", (-12, 0, 0)),
        block("HatBadge", (0.22, 0.22, 0.06), (0, 3.12, -0.66), GOLD, "Hat", (0, 0, 45)),
        # Baton at the belt on the left side, and a collar with a tag.
        cyl_y("Baton", 0.75, 1.5, 0.12, BLACK, "Body", -0.78, -0.15),
        ball("CollarTag", 0.18, (0, 1.62, -0.6), GOLD, "Body"),
    ]
    joints += [("Hat", "Head", (0, 2.9, -0.05))]
    job = [
        (0.0, {}),
        (0.4, {"ArmR": P(rx=165, rz=-12), "Head": P(rx=3), "Body": P(y=0.04)}),
        (0.8, {"ArmR": P(rx=165, rz=-12), "Tail": P(ry=25), "Body": P(y=0.04), "Head": P(rx=3)}),
        (1.2, {"ArmR": P(rx=165, rz=-12), "Tail": P(ry=-25), "Body": P(y=0.0)}),
        (1.6, {"ArmR": P(rx=165, rz=-12), "Tail": P(ry=25), "Body": P(y=0.05)}),
        (2.0, {"ArmR": P(rx=20), "Tail": P(ry=-10)}),
        (2.4, {}),
    ]
    return parts, joints, job


def dragon_office():
    """Rồng Con Văn Phòng: shirt collar and red tie, a name tag, a briefcase; he checks his empty wallet and sighs."""
    c = SimpleNamespace(fur=PEARL, belly=(255, 255, 255), leg=PEARL, paw=PEARL, sleeve=PEARL, arm=(0.32, 0.75, 0.32))
    parts = frame_parts(c)
    parts += [
        ell("Snout", (0.8, 0.55, 0.6), (0, 1.98, -0.75), (255, 230, 240), "Head"),
        ball("NostrilL", 0.07, (-0.12, 2.06, -1.04), BLACK, "Head"),
        ball("NostrilR", 0.07, (0.12, 2.06, -1.04), BLACK, "Head"),
        block("Smile", (0.34, 0.03, 0.04), (0, 1.86, -1.03), BLACK, "Head"),
        ell("Tail", (0.5, 0.45, 1.0), (0, 1.0, 0.95), PEARL, None, (-15, 0, 0)),
        ell("TailSpike", (0.2, 0.3, 0.3), (0, 1.1, 1.5), GOLD, "Tail", (-15, 0, 0)),
        ell("Crest1", (0.16, 0.34, 0.16), (0, 3.0, -0.25), GOLD, "Head"),
        ell("Crest2", (0.16, 0.28, 0.16), (0, 2.95, 0.05), GOLD, "Head"),
        ell("Crest3", (0.16, 0.22, 0.16), (0, 2.85, 0.3), GOLD, "Head"),
        ell("Collar", (1.0, 0.18, 0.7), (0, 1.62, -0.35), WHITE, "Body"),
        block("TieKnot", (0.16, 0.14, 0.1), (0, 1.58, -0.66), RED, "Body"),
        ell("Tie", (0.2, 0.7, 0.08), (0, 1.2, -0.62), RED, "Body"),
        block("NameTag", (0.3, 0.18, 0.04), (-0.38, 1.4, -0.58), WHITE, "Body"),
        block("NameTagLine", (0.2, 0.03, 0.04), (-0.38, 1.4, -0.61), BLACK, "Body"),
        # Briefcase in the right hand, hanging by its handle.
        block("Tool", (0.7, 0.5, 0.25), (0.86, 0.45, -0.12), (140, 90, 50), None),
        block("BriefcaseHandle", (0.3, 0.06, 0.06), (0.86, 0.74, -0.12), BLACK, "Tool"),
        block("BriefcaseClasp", (0.12, 0.1, 0.04), (0.86, 0.55, -0.26), SILVER, "Tool"),
    ]
    for i, (y, color) in enumerate(((1.45, RED), (1.25, ORANGE), (1.05, GOLD), (0.85, GREEN))):
        parts.append(ell(f"BellyStripe{i}", (0.82, 0.1, 0.1), (0, y, -0.56), color, "Body"))
    for side, x in SIDES:
        parts += [
            ell(f"Horn{side}", (0.18, 0.7, 0.18), (x * 0.42, 3.1, -0.1), GOLD, "Head", (0, 0, -x * 25)),
            ell(f"Ear{side}", (0.3, 0.5, 0.1), (x * 0.82, 2.55, -0.05), PINK, None, (0, 0, -x * 35)),
            ell(f"Wing{side}", (1.3, 0.12, 1.1), (x * 1.05, 1.8, 0.55), PEARL, None, (0, 0, -x * 35)),
            ell(f"WingInner{side}", (0.9, 0.14, 0.7), (x * 1.05, 1.8, 0.5), PINK, f"Wing{side}", (0, 0, -x * 35)),
        ]
    joints = [("EarL", "Head", (-0.7, 2.6, -0.05)), ("EarR", "Head", (0.7, 2.6, -0.05)),
              ("WingL", "Body", (-0.55, 1.65, 0.45)), ("WingR", "Body", (0.55, 1.65, 0.45)),
              ("Tool", "ArmR", (0.86, 0.74, -0.12))]
    job = [
        (0.0, {}),
        (0.4, {"ArmL": P(rx=100), "Head": P(rx=-12), "Tool": P(rx=8)}),
        (0.8, {"ArmL": P(rx=100), "Body": P(rx=-6), "Head": P(rx=-18), "Tool": P(rx=8)}),
        (1.2, {"ArmL": P(rx=100), "Body": P(rx=-8), "Head": P(rx=-22), "EarL": P(rz=20), "EarR": P(rz=-20),
               "WingL": P(rz=18), "WingR": P(rz=-18)}),
        (1.6, {"Body": P(rx=-6), "Head": P(rx=-18), "Tool": P(rx=15), "WingL": P(rz=18), "WingR": P(rz=-18)}),
        (2.0, {"Head": P(rx=-5), "Tool": P(rx=-6)}),
        (2.4, {}),
    ]
    return parts, joints, job


# rarity: Rarity attribute read by PetEffects. scale: size factor of the rarity. ring: spinning halo colors.
PETS = {
    "CatPot": SimpleNamespace(rarity="Common", scale=1.0, build=cat_pot, ring=None),
    "DogBaker": SimpleNamespace(rarity="Common", scale=1.0, build=dog_baker, ring=None),
    "DuckMuscle": SimpleNamespace(rarity="Rare", scale=1.05, build=duck_muscle, ring=None),
    "CatMagician": SimpleNamespace(rarity="Epic", scale=1.1, build=cat_magician, ring=None),
    "DogK9": SimpleNamespace(rarity="Legendary", scale=1.15, build=dog_k9, ring=[(255, 215, 95)]),
    "DragonOffice": SimpleNamespace(rarity="Mythic", scale=1.2, build=dragon_office, ring=RAINBOW),
}


# ---------------------------------------------------------------- animation (shared frames, then the Job)

def walk_frame(swing, bob, roll):
    return {"LegL": P(rx=swing), "LegR": P(rx=-swing), "ArmL": P(rx=-swing * 0.8), "ArmR": P(rx=swing * 0.8),
            "Body": P(y=bob, rz=roll), "Head": P(rz=-roll), "Tail": P(ry=roll * 4), "EarL": P(rz=-bob * 20),
            "EarR": P(rz=bob * 20)}


def run_frame(swing, bob, roll):
    return {"LegL": P(rx=swing), "LegR": P(rx=-swing), "ArmL": P(rx=-swing * 1.2), "ArmR": P(rx=swing * 1.2),
            "Body": P(y=bob, rx=-8, rz=roll), "Head": P(rx=6, rz=-roll), "Tail": P(ry=roll * 5),
            "EarL": P(rz=18), "EarR": P(rz=-18)}


LID_HALF = {"LidL": P(z=-0.12), "LidR": P(z=-0.12)}
LID_SHUT = {"LidL": P(z=-0.2), "LidR": P(z=-0.2)}
SIT = {"Body": P(y=-0.45, rx=10), "LegL": P(rx=80), "LegR": P(rx=80), "ArmL": P(rx=30), "ArmR": P(rx=30),
       **LID_SHUT, "EarL": P(rz=15), "EarR": P(rz=-15)}


def animations(job):
    """name: (looped, priority, easing, [(time, {joint: pose})]); the standard set shared by all pets plus the Job."""
    return {
        "Idle": (True, "Idle", "Cubic", [
            (0.0, {}),
            (0.6, {"Body": P(y=0.03), "Head": P(rz=3), "Tail": P(ry=10), "ArmL": P(rx=3), "ArmR": P(rx=-3)}),
            (1.2, {"Head": P(rz=-2)}),
            (1.35, {**LID_SHUT, "Head": P(rz=-2)}),
            (1.5, {"Head": P(rz=-2)}),
            (1.8, {"Body": P(y=0.03), "Tail": P(ry=-10), "Head": P(rz=2)}),
            (2.4, {}),
        ]),
        "Walk": (True, "Movement", "Cubic", [
            (0.0, walk_frame(25, 0, 3)), (0.25, walk_frame(0, 0.05, 0)), (0.5, walk_frame(-25, 0, -3)),
            (0.75, walk_frame(0, 0.05, 0)), (1.0, walk_frame(25, 0, 3)),
        ]),
        "Run": (True, "Movement", "Linear", [
            (0.0, run_frame(45, 0, 4)), (0.15, run_frame(0, 0.14, 0)), (0.3, run_frame(-45, 0, -4)),
            (0.45, run_frame(0, 0.14, 0)), (0.6, run_frame(45, 0, 4)),
        ]),
        "Attack": (True, "Action", "Cubic", [
            (0.0, {"Body": P(rx=8), "ArmR": P(rx=160), "Head": P(rx=5), "Tail": P(ry=15)}),
            (0.3, {"Body": P(rx=12, z=0.1), "ArmR": P(rx=175), "Head": P(rx=8), "Tail": P(ry=-15)}),
            (0.45, {"Body": P(rx=-15, z=-0.35), "ArmR": P(rx=40), "Head": P(rx=-14), "Tail": P(ry=20),
                    "EarL": P(rz=20), "EarR": P(rz=-20)}),
            (0.6, {"Body": P(rx=-15, z=-0.35), "ArmR": P(rx=40), "Head": P(rx=-14), "Tail": P(ry=-20)}),
            (0.8, {"Body": P(rx=8), "ArmR": P(rx=160), "Head": P(rx=5), "Tail": P(ry=15)}),
        ]),
        "Hurt": (False, "Action", "Cubic", [
            (0.0, {}),
            (0.15, {"Body": P(z=0.4, rx=12), "Head": P(rx=15), **LID_HALF, "EarL": P(rz=20), "EarR": P(rz=-20),
                    "Tail": P(ry=30)}),
            (0.35, {"Body": P(z=0.3, rz=8), "Head": P(rz=15), **LID_HALF, "Tail": P(ry=-25)}),
            (0.55, {"Body": P(z=0.1), "Head": P(rz=-8)}),
            (0.7, {}),
        ]),
        "Exhausted": (False, "Action", "Cubic", [
            (0.0, {}),
            (0.3, {"Head": P(rz=12), "Body": P(rz=6), **LID_HALF}),
            (0.6, {"Head": P(rz=-12), "Body": P(rz=-6), **LID_HALF}),
            (0.9, {**SIT, "Head": P(rx=20)}),
            (1.2, {**SIT, "Head": P(rx=28)}),
            (1.6, {**SIT, "Head": P(rx=25)}),
        ]),
        "Happy": (False, "Action", "Cubic", [
            (0.0, {}),
            (0.25, {"Body": P(y=-0.15), "LegL": P(rx=-10), "LegR": P(rx=-10)}),
            (0.5, {"Body": P(y=0.6), "ArmL": P(rz=-150), "ArmR": P(rz=150), "Head": P(rx=8), "Tail": P(ry=25)}),
            (0.8, {"Body": P(y=-0.1), "ArmL": P(rz=-40), "ArmR": P(rz=40), "Tail": P(ry=-25)}),
            (1.1, {"ArmR": P(rz=140), "Head": P(rz=8), "Tail": P(ry=25)}),
            (1.4, {"ArmR": P(rz=120), "Head": P(rz=-6), "Tail": P(ry=-20)}),
            (1.6, {}),
        ]),
        "Job": (False, "Action", "Cubic", job),
    }


# ---------------------------------------------------------------- data, scale, model

def scale_cf(c, k):
    return CF(tuple(v * k for v in c.pos), c.rot)


def pet_data(pet):
    parts, joints, job = pet.build()
    if pet.ring:
        parts += ring_around(1.9, 1.3, -18, pet.ring)
    k = pet.scale
    animations_ = {name: (looped, priority, easing,
                          [(t, {j: scale_cf(pose, k) for j, pose in poses.items()}) for t, poses in frames])
                   for name, (looped, priority, easing, frames) in animations(job).items()}
    return SimpleNamespace(
        PARTS=[(n, shape, tuple(s * k for s in size), scale_cf(rest, k), color, bone)
               for n, shape, size, rest, color, bone in parts],
        JOINTS=[(n, par, tuple(v * k for v in pv)) for n, par, pv in [*FRAME_JOINTS, *joints]],
        ANIMATIONS=animations_, hip=HIP_HEIGHT * k)


def build_model(kind, pet, data):
    parts = {}
    for name, shape, size, rest, color, _ in data.PARTS:
        part = build_part(name, shape, size, rest, color)
        part.rest = rest
        if name == "Halo":
            set_prop(part, "Transparency", '<float name="Transparency">1</float>')
        if name.startswith("HaloRing"):
            set_prop(part, "Material", f'<token name="Material">{MATERIAL_NEON}</token>')
            set_prop(part, "Transparency", '<float name="Transparency">0.25</float>')
        parts[name] = part

    model = Item("Model", [
        xml_string("Name", f"Pet_{kind}"),
        f'<Ref name="PrimaryPart">{parts["HumanoidRootPart"].ref}</Ref>',
        f'<token name="ModelStreamingMode">{MODEL_STREAMING_ATOMIC}</token>',
        xml_attributes({"Anim": "Idle", "Rarity": pet.rarity}),
    ])
    for part in parts.values():
        model.add(part)
    for part1, part0, pivot in data.JOINTS:
        parts[part0].add(build_joint("Motor6D", part1, parts[part0], parts[part1], CF(pivot)))
    for name, _, _, rest, _, bone in data.PARTS:
        if bone:
            parts[bone].add(build_joint("Weld", name, parts[bone], parts[name], rest))

    model.add(Item("Humanoid", [
        xml_string("Name", "Humanoid"),
        f'<token name="RigType">{RIG_TYPE_R15}</token>',
        f'<float name="HipHeight">{data.hip:.4g}</float>',
        f'<token name="DisplayDistanceType">{DISPLAY_DISTANCE_NONE}</token>',
        '<bool name="RequiresNeck">false</bool>',
        '<float name="WalkSpeed">16</float>',
    ]))

    folder = model.add(Item("Folder", [xml_string("Name", "Animations")]))
    for name, (looped, priority, easing, keyframes) in data.ANIMATIONS.items():
        folder.add(build_keyframe_sequence(name, looped, priority, easing, keyframes, data.JOINTS))

    for script_name, source_path in (("PetAnimator", HERE.parent / "PoliceGoose" / "GooseAnimator.client.luau"),
                                     ("PetEffects", HERE / "PetEffects.client.luau")):
        model.add(Item("Script", [
            xml_string("Name", script_name),
            f'<token name="RunContext">{RUN_CONTEXT_CLIENT}</token>',
            f'<ProtectedString name="Source"><![CDATA[{source_path.read_text(encoding="utf-8")}]]></ProtectedString>',
        ]))
    return model


def main():
    for kind, pet in PETS.items():
        data = pet_data(pet)
        xml = ('<roblox xmlns:xmime="http://www.w3.org/2005/05/xmlmime" '
               'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
               'xsi:noNamespaceSchemaLocation="http://www.roblox.com/roblox.xsd" version="4">\n'
               "  <External>null</External>\n  <External>nil</External>\n"
               f"{build_model(kind, pet, data).to_xml()}</roblox>\n")
        out = HERE / f"Pet_{kind}.rbxmx"
        out.write_text(xml, encoding="utf-8")
        print(f"Wrote {out.name} ({len(data.PARTS)} parts, {len(data.JOINTS)} joints)")
        export(data, f"Pet_{kind}", HERE / f"Pet_{kind}.glb")


if __name__ == "__main__":
    main()
