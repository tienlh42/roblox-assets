"""Builds Rod_<Kind>.rbxmx and .glb (rig + KeyframeSequences + client scripts) for the six fishing rods.

Run: python build_rod.py
Reuses the rbxmx writer of ../PoliceGoose and the color and part helpers of ../Egg. Coordinates are in studs, ground at
y = 0, the rod stands upright and its front (the casting direction, the reel and the guides) is -Z.
All rods share one frame (handle, reel with crank, three rod sections that bend, guides, hook and float); each kind only
differs in colors and in its animal spirit: parts that look and move like an animal (RODS below). The fishing line is a
Beam made by RodEffects between the rod tip and the part LineEnd.
"""

import sys
from pathlib import Path
from types import SimpleNamespace

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "Egg"))

from build_egg import (  # noqa: E402
    BLUE, GOLD_DARK, GREEN, LAVENDER, MINT, PEARL, PINK, PURPLE, RAINBOW, RED, WOOD, set_prop, shade,
)
from build_police_goose import (  # noqa: E402
    BLACK, CF, GOLD, MODEL_STREAMING_ATOMIC, ORANGE, RUN_CONTEXT_CLIENT, SILVER, WHITE, Item, build_joint,
    build_keyframe_sequence, build_part, cf, xml_attributes, xml_string,
)
from export_glb import export  # noqa: E402

WOOD_DARK = (122, 74, 36)
GRIP_DARK = (70, 70, 76)
REEL = (0.0, 1.75, -0.4)  # center of the reel, in front of the rod
HOOK_Z = -0.5  # the hook and float hang in front of the rod
HOOK_REST = (0.0, 4.65, HOOK_Z)
P = cf


def cyl_y(name, y_lo, y_hi, dia, color, bone, x=0.0, z=0.0):
    """Cylinder standing on the Y axis (Roblox cylinders lie along X, so it is turned 90 degrees)."""
    return (name, "cylinder", (y_hi - y_lo, dia, dia), cf(x, (y_lo + y_hi) / 2, z, 0, 0, 90), color, bone)


# ---------------------------------------------------------------- shared frame

def frame_parts(rod, band, grip, trim, bobber):
    parts = [
        ("HumanoidRootPart", "block", (1, 1, 1), cf(0, 0.5, 0), WHITE, None),
        cyl_y("Grip", 0.2, 1.2, 0.42, grip, None),
        ("ButtCap", "ellipsoid", (0.5, 0.3, 0.5), cf(0, 0.2, 0), trim, "Grip"),
        cyl_y("Collar", 1.2, 1.32, 0.5, SILVER, "Grip"),
        ("ReelMount", "block", (0.2, 0.3, 0.4), cf(0, 1.55, -0.2), SILVER, "Grip"),
        ("CrankAxle", "cylinder", (0.34, 0.1, 0.1), cf(0.43, REEL[1], REEL[2]), SILVER, "Grip"),
        ("Crank", "block", (0.07, 0.4, 0.09), cf(0.6, 1.95, REEL[2]), SILVER, None),
        ("CrankKnob", "ball", (0.14, 0.14, 0.14), cf(0.62, 2.12, REEL[2]), trim, "Crank"),
        cyl_y("Rod1", 1.2, 2.8, 0.3, rod, None),
        cyl_y("Rod2", 2.8, 4.4, 0.24, rod, None),
        cyl_y("Rod3", 4.4, 5.9, 0.17, rod, None),
        cyl_y("Ferrule0", 1.32, 1.4, 0.34, band, "Rod1"),
        cyl_y("Ferrule1", 2.74, 2.86, 0.34, band, "Rod1"),
        cyl_y("Ferrule2", 4.34, 4.46, 0.28, band, "Rod2"),
        ("Guide1", "ball", (0.12, 0.12, 0.12), cf(0, 2.4, -0.2), SILVER, "Rod1"),
        ("Guide2", "ball", (0.12, 0.12, 0.12), cf(0, 3.6, -0.2), SILVER, "Rod2"),
        ("Guide3", "ball", (0.12, 0.12, 0.12), cf(0, 4.9, -0.18), SILVER, "Rod3"),
        ("Tip", "ball", (0.18, 0.18, 0.18), cf(0, 5.95, 0), SILVER, "Rod3"),
        ("Hook", "ball", (0.12, 0.12, 0.12), cf(*HOOK_REST), SILVER, None),
        ("HookShank", "block", (0.05, 0.28, 0.05), cf(0, 4.5, HOOK_Z), SILVER, "Hook"),
        ("HookCurve", "block", (0.05, 0.05, 0.2), cf(0, 4.36, HOOK_Z - 0.08), SILVER, "Hook"),
        ("HookTip", "block", (0.05, 0.14, 0.05), cf(0, 4.43, HOOK_Z - 0.18), SILVER, "Hook"),
        ("LineEnd", "ball", (0.04, 0.04, 0.04), cf(0, 5.12, HOOK_Z), WHITE, "Hook"),
    ]
    for i, y in enumerate((0.38, 0.68, 0.98), start=1):
        parts.append(cyl_y(f"GripBand{i}", y - 0.04, y + 0.04, 0.46, trim, "Grip"))
    if bobber:
        parts += [
            ("Float", "ball", (0.3, 0.3, 0.3), cf(0, 4.92, HOOK_Z), bobber, "Hook"),
            ("FloatCap", "ellipsoid", (0.3, 0.14, 0.3), cf(0, 5.04, HOOK_Z), WHITE, "Hook"),
        ]
    return parts


JOINTS = [
    ("Grip", "HumanoidRootPart", (0, 1.0, 0)),
    ("Rod1", "Grip", (0, 1.2, 0)),
    ("Rod2", "Rod1", (0, 2.8, 0)),
    ("Rod3", "Rod2", (0, 4.4, 0)),
    ("Crank", "Grip", (0.6, REEL[1], REEL[2])),
    ("Hook", "Rod3", (0, 5.95, 0)),
]
CHAIN = ["Grip", "Rod1", "Rod2", "Rod3"]


# ---------------------------------------------------------------- the six rods (colors and animal spirit)

def ball(name, size, pos, color, bone):
    return (name, "ball", (size,) * 3, cf(*pos), color, bone)


def starter_decor():
    """Bamboo-colored rod with a wooden spool. Spirit: the float is a duckling that tucks its neck, and a sprout grows
    from the tip."""
    yellow = GOLD
    parts = [
        ("ReelBody", "cylinder", (0.5, 0.72, 0.72), cf(*REEL), WOOD, "Grip"),
        ("ReelCord", "cylinder", (0.46, 0.62, 0.62), cf(*REEL), (235, 225, 200), "Grip"),
        ("ReelFlangeL", "cylinder", (0.06, 0.92, 0.92), cf(0.28, REEL[1], REEL[2]), WOOD_DARK, "Grip"),
        ("ReelFlangeR", "cylinder", (0.06, 0.92, 0.92), cf(-0.28, REEL[1], REEL[2]), WOOD_DARK, "Grip"),
        ("SpiritA", "block", (0.05, 0.22, 0.05), cf(0, 6.06, 0), GREEN, None),
        ("LeafL", "ellipsoid", (0.38, 0.08, 0.18), cf(0.2, 6.2, 0, 0, 0, -20), GREEN, "SpiritA"),
        ("LeafR", "ellipsoid", (0.38, 0.08, 0.18), cf(-0.2, 6.2, 0, 0, 0, 20), GREEN, "SpiritA"),
        ("DuckBody", "ellipsoid", (0.46, 0.38, 0.5), cf(0, 4.95, HOOK_Z), yellow, "Hook"),
        ("DuckTail", "ellipsoid", (0.16, 0.12, 0.2), cf(0, 5.0, HOOK_Z + 0.26, -20, 0, 0), yellow, "Hook"),
        ("DuckWingL", "ellipsoid", (0.1, 0.2, 0.3), cf(0.23, 4.96, HOOK_Z + 0.02), shade(yellow, 0.9), "Hook"),
        ("DuckWingR", "ellipsoid", (0.1, 0.2, 0.3), cf(-0.23, 4.96, HOOK_Z + 0.02), shade(yellow, 0.9), "Hook"),
        ("SpiritB", "ellipsoid", (0.28, 0.28, 0.28), cf(0, 5.25, HOOK_Z - 0.14), yellow, None),
        ("DuckBeak", "ellipsoid", (0.15, 0.08, 0.18), cf(0, 5.22, HOOK_Z - 0.3), ORANGE, "SpiritB"),
        ("DuckEyeL", "ball", (0.06, 0.06, 0.06), cf(0.09, 5.29, HOOK_Z - 0.26), BLACK, "SpiritB"),
        ("DuckEyeR", "ball", (0.06, 0.06, 0.06), cf(-0.09, 5.29, HOOK_Z - 0.26), BLACK, "SpiritB"),
    ]
    joints = [("SpiritA", "Rod3", (0, 5.95, 0)), ("SpiritB", "Hook", (0, 5.12, HOOK_Z - 0.1))]
    # SpiritA: the sprout (rz), SpiritB: the duckling's head (rx, + tucks it back).
    gestures = {
        "calm": {}, "calmB": {"SpiritA": P(rz=6), "SpiritB": P(rx=8)},
        "alert": {"SpiritA": P(rz=-8), "SpiritB": P(rx=-12)},
        "strain": {"SpiritA": P(rz=-14), "SpiritB": P(rx=24)},
        "joy": {"SpiritA": P(rz=22), "SpiritB": P(rx=-28)}, "joyB": {"SpiritA": P(rz=-22), "SpiritB": P(rx=-18)},
        "sad": {"SpiritA": P(rz=-30), "SpiritB": P(rx=35)}, "sadB": {"SpiritA": P(rz=-26), "SpiritB": P(rx=28)},
    }
    return parts, joints, gestures


def catfish_decor():
    """Gray-blue rod, the reel is a catfish head with a wide mouth, two long whiskers wag at the tip."""
    fish, fish_dark = (120, 150, 172), (60, 90, 110)
    parts = [
        ("ReelBody", "ellipsoid", (0.75, 0.62, 0.72), cf(*REEL), fish, "Grip"),
        ("ReelBelly", "ellipsoid", (0.55, 0.3, 0.5), cf(0, 1.55, -0.5), (190, 205, 215), "Grip"),
        ("ReelMouth", "block", (0.5, 0.07, 0.06), cf(0, 1.62, -0.76), BLACK, "Grip"),
        ("ReelWhiskerL", "ellipsoid", (0.3, 0.04, 0.04), cf(0.3, 1.6, -0.74, 0, 0, -20), fish_dark, "Grip"),
        ("ReelWhiskerR", "ellipsoid", (0.3, 0.04, 0.04), cf(-0.3, 1.6, -0.74, 0, 0, 20), fish_dark, "Grip"),
        ("SpiritA", "ellipsoid", (0.8, 0.06, 0.06), cf(0.36, 5.78, 0, 0, 0, -40), fish_dark, None),
        ("WhiskerL2", "ellipsoid", (0.55, 0.05, 0.05), cf(0.28, 5.84, 0, 0, 0, -70), fish_dark, "SpiritA"),
        ("SpiritB", "ellipsoid", (0.8, 0.06, 0.06), cf(-0.36, 5.78, 0, 0, 0, 40), fish_dark, None),
        ("WhiskerR2", "ellipsoid", (0.55, 0.05, 0.05), cf(-0.28, 5.84, 0, 0, 0, 70), fish_dark, "SpiritB"),
    ]
    for side, x in (("L", 1), ("R", -1)):
        parts += [
            ball(f"ReelEye{side}", 0.2, (x * 0.2, 1.98, -0.58), WHITE, "Grip"),
            ball(f"ReelPupil{side}", 0.1, (x * 0.2, 1.98, -0.68), BLACK, "Grip"),
            ball(f"ReelShine{side}", 0.04, (x * 0.18, 2.02, -0.72), WHITE, "Grip"),
        ]
    joints = [("SpiritA", "Rod3", (0.05, 5.95, 0)), ("SpiritB", "Rod3", (-0.05, 5.95, 0))]
    # Whiskers (A at +X, B at -X): + rz lifts A, - rz lifts B.
    def whiskers(a):
        return {"SpiritA": P(rz=a), "SpiritB": P(rz=-a)}
    gestures = {"calm": {}, "calmB": whiskers(8), "alert": whiskers(15), "strain": whiskers(28), "joy": whiskers(40),
                "joyB": whiskers(28), "sad": whiskers(-25), "sadB": whiskers(-20)}
    return parts, joints, gestures


def turtle_decor():
    """Blue rod, the reel is a turtle shell whose head peeks out (and hides when the catch is missed)."""
    shell, skin = (70, 170, 120), (130, 200, 120)
    parts = [
        ("ReelBody", "ellipsoid", (0.95, 0.62, 0.95), cf(*REEL), shell, "Grip"),
        ("ShellRim", "ellipsoid", (1.0, 0.14, 1.0), cf(0, 1.55, REEL[2]), (230, 215, 150), "Grip"),
        ("ShellPlate1", "ellipsoid", (0.34, 0.1, 0.34), cf(0, 2.04, REEL[2]), (120, 210, 150), "Grip"),
        ("ShellPlate2", "ellipsoid", (0.3, 0.1, 0.3), cf(0.3, 1.97, -0.15), (120, 210, 150), "Grip"),
        ("ShellPlate3", "ellipsoid", (0.3, 0.1, 0.3), cf(-0.3, 1.97, -0.15), (120, 210, 150), "Grip"),
        ("ShellPlate4", "ellipsoid", (0.3, 0.1, 0.3), cf(0.3, 1.97, -0.65), (120, 210, 150), "Grip"),
        ("ShellPlate5", "ellipsoid", (0.3, 0.1, 0.3), cf(-0.3, 1.97, -0.65), (120, 210, 150), "Grip"),
        ("SpiritA", "ellipsoid", (0.36, 0.34, 0.4), cf(0, 1.72, -0.98), skin, None),
        ("TurtleNeck", "ellipsoid", (0.24, 0.24, 0.35), cf(0, 1.68, -0.8), skin, "SpiritA"),
        ("TurtleSmile", "block", (0.18, 0.03, 0.04), cf(0, 1.64, -1.17), BLACK, "SpiritA"),
        ("SpiritB", "ellipsoid", (0.4, 0.12, 0.26), cf(0.72, 1.56, -0.5, 0, 0, -30), skin, None),
    ]
    for side, x in (("L", 1), ("R", -1)):
        parts += [
            ball(f"TurtleEye{side}", 0.12, (x * 0.1, 1.8, -1.12), WHITE, "SpiritA"),
            ball(f"TurtlePupil{side}", 0.06, (x * 0.1, 1.8, -1.18), BLACK, "SpiritA"),
        ]
    joints = [("SpiritA", "Grip", (0, 1.7, -0.85)), ("SpiritB", "Grip", (0.5, 1.65, -0.5))]
    # SpiritA: the head (z - stretches it out, z + hides it in the shell), SpiritB: the flipper (rz).
    gestures = {
        "calm": {}, "calmB": {"SpiritA": P(y=0.04), "SpiritB": P(rz=-12)},
        "alert": {"SpiritA": P(z=-0.12), "SpiritB": P(rz=15)},
        "strain": {"SpiritA": P(z=-0.2), "SpiritB": P(rz=25)},
        "joy": {"SpiritA": P(y=0.12, z=-0.1, rx=-15), "SpiritB": P(rz=40)},
        "joyB": {"SpiritA": P(y=0.06, z=-0.15), "SpiritB": P(rz=-25)},
        "sad": {"SpiritA": P(z=0.28), "SpiritB": P(rz=-30)}, "sadB": {"SpiritA": P(z=0.22), "SpiritB": P(rz=-20)},
    }
    return parts, joints, gestures


def fox_decor():
    """Purple rod, the reel is a fox face (the right eye winks), a fluffy fox tail wags at the tip."""
    parts = [
        ("ReelBody", "ellipsoid", (0.85, 0.7, 0.72), cf(*REEL), PURPLE, "Grip"),
        ("ReelMuzzle", "ellipsoid", (0.46, 0.32, 0.4), cf(0, 1.62, -0.72), LAVENDER, "Grip"),
        ball("ReelNose", 0.1, (0, 1.7, -0.9), BLACK, "Grip"),
        ("SpiritA", "ellipsoid", (0.62, 0.8, 0.62), cf(0.1, 6.25, 0, 0, 0, -20), PURPLE, None),
        ("TailMid", "ellipsoid", (0.55, 0.5, 0.55), cf(0.24, 6.65, 0, 0, 0, -20), shade(PURPLE, 0.9), "SpiritA"),
        ("TailTip", "ellipsoid", (0.45, 0.4, 0.45), cf(0.36, 6.98, 0, 0, 0, -20), WHITE, "SpiritA"),
        # The lid sits inside the head behind the right eye; moving it forward (z -) closes the eye.
        ball("SpiritB", 0.24, (-0.22, 1.9, -0.58), PURPLE, None),
    ]
    for side, x in (("L", 1), ("R", -1)):
        parts += [
            (f"ReelCheek{side}", "ellipsoid", (0.3, 0.22, 0.3), cf(x * 0.3, 1.65, -0.62), LAVENDER, "Grip"),
            (f"ReelEye{side}", "ellipsoid", (0.12, 0.17, 0.06), cf(x * 0.22, 1.9, -0.72), BLACK, "Grip"),
            ball(f"ReelShine{side}", 0.04, (x * 0.2, 1.95, -0.76), WHITE, "Grip"),
            (f"Ear{side}", "ellipsoid", (0.3, 0.42, 0.12), cf(x * 0.34, 2.12, -0.35, 0, 0, -x * 28), PURPLE, "Grip"),
            (f"EarInner{side}", "ellipsoid", (0.16, 0.26, 0.08), cf(x * 0.34, 2.1, -0.4, 0, 0, -x * 28), LAVENDER,
             "Grip"),
        ]
    joints = [("SpiritA", "Rod3", (0, 5.95, 0)), ("SpiritB", "Grip", (-0.22, 1.9, -0.58))]
    # SpiritA: the tail (rz), SpiritB: the winking eyelid (z - closes the eye).
    wink = {"SpiritB": P(z=-0.18)}
    gestures = {
        "calm": {}, "calmB": {"SpiritA": P(rz=8)}, "alert": {"SpiritA": P(rz=-10)}, "strain": {"SpiritA": P(rz=-16)},
        "joy": {"SpiritA": P(rz=20), **wink}, "joyB": {"SpiritA": P(rz=-20)},
        "sad": {"SpiritA": P(rz=-35)}, "sadB": {"SpiritA": P(rz=-28)},
    }
    return parts, joints, gestures


def cat_decor():
    """Gold rod, the reel is a ball of yarn with cat eyes, a white cat paw beckons at the tip, a bell jingles."""
    yarn = PINK
    parts = [
        ball("ReelBody", 0.8, REEL, yarn, "Grip"),
        ("Yarn1", "ellipsoid", (0.84, 0.07, 0.84), cf(*REEL, 0, 0, 35), shade(yarn, 0.8), "Grip"),
        ("Yarn2", "ellipsoid", (0.84, 0.07, 0.84), cf(*REEL, 0, 0, -35), shade(yarn, 0.8), "Grip"),
        ("Yarn3", "ellipsoid", (0.84, 0.07, 0.84), cf(*REEL, 90, 0, 0), shade(yarn, 0.8), "Grip"),
        ("SpiritA", "ellipsoid", (0.5, 0.46, 0.44), cf(0, 6.22, 0), WHITE, None),
        ("PawPad", "ellipsoid", (0.22, 0.16, 0.08), cf(0, 6.15, -0.2), PINK, "SpiritA"),
        ball("PawBeanL", 0.09, (0.15, 6.32, -0.2), PINK, "SpiritA"),
        ball("PawBeanR", 0.09, (-0.15, 6.32, -0.2), PINK, "SpiritA"),
        ball("PawBeanC", 0.09, (0, 6.38, -0.21), PINK, "SpiritA"),
        ("ClawL", "ellipsoid", (0.06, 0.16, 0.06), cf(0.14, 6.5, -0.05), (255, 240, 200), "SpiritA"),
        ("ClawR", "ellipsoid", (0.06, 0.16, 0.06), cf(-0.14, 6.5, -0.05), (255, 240, 200), "SpiritA"),
        ("ClawC", "ellipsoid", (0.06, 0.16, 0.06), cf(0, 6.54, -0.05), (255, 240, 200), "SpiritA"),
        cyl_y("Ribbon", 1.08, 1.16, 0.5, RED, "Grip"),
        ball("SpiritB", 0.2, (0, 1.0, -0.3), GOLD, None),
        ("BellSlit", "block", (0.12, 0.02, 0.02), cf(0, 0.98, -0.4), BLACK, "SpiritB"),
    ]
    for side, x in (("L", 1), ("R", -1)):
        parts += [
            ("ReelEye" + side, "ellipsoid", (0.16, 0.2, 0.06), cf(x * 0.2, 1.85, -0.74), WHITE, "Grip"),
            ("ReelPupil" + side, "ellipsoid", (0.04, 0.16, 0.04), cf(x * 0.2, 1.85, -0.77), BLACK, "Grip"),
        ]
    joints = [("SpiritA", "Rod3", (0, 5.95, 0)), ("SpiritB", "Grip", (0, 1.14, -0.3))]
    # SpiritA: the paw (rz waves it), SpiritB: the bell (rz swings it).
    gestures = {
        "calm": {}, "calmB": {"SpiritA": P(rz=18), "SpiritB": P(rz=20)},
        "alert": {"SpiritA": P(rz=-10), "SpiritB": P(rz=-15)}, "strain": {"SpiritA": P(rz=-20), "SpiritB": P(rz=-25)},
        "joy": {"SpiritA": P(rz=40), "SpiritB": P(rz=40)}, "joyB": {"SpiritA": P(rz=-30), "SpiritB": P(rz=-40)},
        "sad": {"SpiritA": P(rz=-45)}, "sadB": {"SpiritA": P(rz=-38), "SpiritB": P(rz=15)},
    }
    return parts, joints, gestures


def dragon_decor():
    """Pearl rod with rainbow rings, the reel is a dragon egg, a baby dragon head holds the line at the tip (it
    nods and burps rainbow smoke) with golden horns and wavy whiskers."""
    parts = [
        ("ReelBody", "ellipsoid", (0.72, 0.98, 0.72), cf(0, 1.78, REEL[2]), PEARL, "Grip"),
        ("SpiritA", "ellipsoid", (0.52, 0.46, 0.7), cf(0, 6.25, -0.2), PEARL, None),
        ("DragonSnout", "ellipsoid", (0.32, 0.26, 0.4), cf(0, 6.18, -0.58), PEARL, "SpiritA"),
        ("DragonSmile", "block", (0.2, 0.03, 0.04), cf(0, 6.1, -0.74), BLACK, "SpiritA"),
        ball("NostrilL", 0.06, (0.07, 6.25, -0.76), BLACK, "SpiritA"),
        ball("NostrilR", 0.06, (-0.07, 6.25, -0.76), BLACK, "SpiritA"),
        ("SpiritB", "ellipsoid", (0.7, 0.05, 0.05), cf(0.4, 6.08, -0.45, 0, 0, -30), GOLD, None),
        ("WhiskerR", "ellipsoid", (0.7, 0.05, 0.05), cf(-0.4, 6.08, -0.45, 0, 0, 30), GOLD, "SpiritB"),
    ]
    for i, (x, y, z, color) in enumerate(((0, 1.55, -0.74, RED), (0.22, 1.75, -0.71, ORANGE), (-0.22, 1.75, -0.71, GOLD),
                                          (0, 1.95, -0.74, GREEN), (0.2, 2.15, -0.66, BLUE), (-0.2, 2.15, -0.66, PURPLE)),
                                         start=1):
        parts.append((f"EggScale{i}", "block", (0.2, 0.2, 0.06), cf(x, y, z, 0, 0, 45), color, "Grip"))
    for side, x in (("L", 1), ("R", -1)):
        parts += [
            ball(f"DragonEye{side}", 0.14, (x * 0.2, 6.36, -0.36), WHITE, "SpiritA"),
            ball(f"DragonPupil{side}", 0.08, (x * 0.2, 6.36, -0.43), BLACK, "SpiritA"),
            (f"Horn{side}", "ellipsoid", (0.1, 0.32, 0.1), cf(x * 0.14, 6.6, -0.1, 0, 0, -x * 20), GOLD, "SpiritA"),
            (f"DragonBlush{side}", "ellipsoid", (0.12, 0.08, 0.05), cf(x * 0.26, 6.2, -0.4), PINK, "SpiritA"),
        ]
    for i, y in enumerate((1.6, 2.0, 2.4)):
        parts.append(cyl_y(f"RodRingA{i + 1}", y - 0.05, y + 0.05, 0.34, RAINBOW[i], "Rod1"))
    for i, y in enumerate((3.2, 3.6, 4.0)):
        parts.append(cyl_y(f"RodRingB{i + 1}", y - 0.05, y + 0.05, 0.28, RAINBOW[i + 3], "Rod2"))
    for i, y in enumerate((4.8, 5.2, 5.6)):
        parts.append(cyl_y(f"RodRingC{i + 1}", y - 0.05, y + 0.05, 0.21, RAINBOW[(i + 6) % 7], "Rod3"))
    joints = [("SpiritA", "Rod3", (0, 5.95, 0)), ("SpiritB", "SpiritA", (0, 6.2, -0.4))]
    # SpiritA: the head (rx, + raises the snout for a burp), SpiritB: both whiskers (rx lifts them).
    gestures = {
        "calm": {}, "calmB": {"SpiritA": P(rx=5), "SpiritB": P(rx=12)},
        "alert": {"SpiritA": P(rx=-8), "SpiritB": P(rx=-10)}, "strain": {"SpiritA": P(rx=-12), "SpiritB": P(rx=-18)},
        "joy": {"SpiritA": P(rx=25), "SpiritB": P(rx=25)}, "joyB": {"SpiritA": P(rx=15), "SpiritB": P(rx=15)},
        "sad": {"SpiritA": P(rx=-20), "SpiritB": P(rx=-25)}, "sadB": {"SpiritA": P(rx=-15), "SpiritB": P(rx=-18)},
    }
    return parts, joints, gestures


# rarity: the Rarity attribute read by RodEffects. rod, band, grip, trim: colors of the rod sections, the rings between
# them, the handle and its wraps. bobber: color of the float (None when the spirit is the float). decor: spirit parts.
RODS = {
    "Starter": SimpleNamespace(rarity="Common", rod=(205, 185, 95), band=WOOD_DARK, grip=(120, 80, 50), trim=WOOD,
                               bobber=None, decor=starter_decor),
    "Catfish": SimpleNamespace(rarity="Common", rod=(120, 150, 172), band=(60, 90, 110), grip=GRIP_DARK,
                               trim=(60, 90, 110), bobber=RED, decor=catfish_decor),
    "Turtle": SimpleNamespace(rarity="Rare", rod=BLUE, band=(150, 220, 250), grip=(50, 80, 120), trim=MINT,
                              bobber=WHITE, decor=turtle_decor),
    "Fox": SimpleNamespace(rarity="Epic", rod=PURPLE, band=LAVENDER, grip=(60, 40, 110), trim=LAVENDER, bobber=PINK,
                           decor=fox_decor),
    "Cat": SimpleNamespace(rarity="Legendary", rod=GOLD, band=GOLD_DARK, grip=(120, 60, 30), trim=GOLD_DARK,
                           bobber=RED, decor=cat_decor),
    "Dragon": SimpleNamespace(rarity="Mythic", rod=PEARL, band=RED, grip=(90, 60, 110), trim=GOLD, bobber=PINK,
                              decor=dragon_decor),
}


# ---------------------------------------------------------------- animation

def chain_matrix(poses):
    """World transform of the rod tip subtree: each joint is pivot * pose * pivot^-1, parents first."""
    matrix = CF()
    for name in CHAIN:
        pivot = CF(next(p for n, _, p in JOINTS if n == name))
        matrix = matrix * pivot * poses.get(name, CF()) * pivot.inverse()
    return matrix


def hook_pose(poses, target):
    """Translation of the Hook joint that puts the hook ball at world position target given the rod pose."""
    local = chain_matrix(poses).inverse() * CF(target)
    return cf(*(local.pos[i] - HOOK_REST[i] for i in range(3)))


def stage(grip, bends, hook=None, crank=None):
    """Pose of the rod chain (grip tilt and the bend of each section, rx degrees; - leans forward), optionally with
    the hook at a world position and the reel crank turned."""
    poses = {"Grip": P(rx=grip), "Rod1": P(rx=bends[0]), "Rod2": P(rx=bends[1]), "Rod3": P(rx=bends[2])}
    if hook is not None:
        poses["Hook"] = hook_pose(poses, hook)
    if crank is not None:
        poses["Crank"] = P(rx=crank)
    return poses


WATER = (0, 1.1, -4.8)  # where the hook lies after a cast
TAKE = {"rest": "calm", "calmB": "calmB", "wind": "alert", "whip": "alert", "land": "alert", "hold": "alert",
        "strain": "strain", "jerk": "strain", "pop": "joy", "joy": "joyB", "slack": "sad", "droop": "sad",
        "shake": "sadB"}
# name: (looped, priority, easing, [(time, mood, pose of the rod chain)])
STAGES = {
    "Idle": (True, "Idle", "Cubic", [
        (0.0, "rest", stage(0, (0, 0, 0))),
        (0.6, "calmB", stage(1.5, (0.5, 1, 1.5))),
        (1.2, "rest", stage(0, (0, 0, 0))),
        (1.8, "calmB", stage(-1.5, (-0.5, -1, -1.5))),
        (2.4, "rest", stage(0, (0, 0, 0))),
    ]),
    "Cast": (False, "Action", "Cubic", [
        (0.0, "rest", stage(0, (0, 0, 0))),
        (0.3, "wind", stage(30, (4, 8, 12), (0, 3.5, 2.2))),
        (0.6, "whip", stage(-40, (-3, -10, -18), (0, 5.5, -3.8))),
        (0.9, "land", stage(-32, (-3, -7, -10), (0, 2.0, -5.5))),
        (1.2, "hold", stage(-25, (-2, -5, -8), WATER)),
    ]),
    "Reel": (True, "Action", "Linear", [
        (0.0, "strain", stage(-25, (-3, -7, -12), (0, 1.1, -4.6), 0)),
        (0.4, "strain", stage(-25, (-3, -9, -16), (0, 1.15, -4.3), 90)),
        (0.8, "strain", stage(-25, (-3, -7, -12), (0, 1.1, -4.0), 180)),
        (1.2, "strain", stage(-25, (-3, -9, -16), (0, 1.15, -4.3), 270)),
        (1.6, "strain", stage(-25, (-3, -7, -12), (0, 1.1, -4.6), 358)),
    ]),
    "Catch": (False, "Action", "Cubic", [
        (0.0, "hold", stage(-25, (-2, -5, -8), WATER)),
        (0.3, "strain", stage(-30, (-3, -9, -16), (0, 1.1, -4.8))),
        (0.5, "jerk", stage(10, (3, 6, 10), (0, 5.5, -1.5))),
        (0.8, "pop", stage(-5, (-1, -3, -5), (0, 4.4, -0.8))),
        (1.1, "joy", stage(0, (0, 0, 0))),
        (1.4, "joy", stage(2, (0.5, 1, 2))),
        (1.6, "rest", stage(0, (0, 0, 0))),
    ]),
    "Miss": (False, "Action", "Cubic", [
        (0.0, "hold", stage(-25, (-2, -5, -8), WATER)),
        (0.3, "strain", stage(-28, (-3, -7, -12), (0, 1.1, -4.7))),
        (0.6, "slack", stage(-15, (-1, -2, -3), (0, 0.9, -3.2))),
        (0.9, "droop", stage(8, (1, 2, 3), (0, 3.0, -1.5))),
        (1.2, "shake", stage(4, (0.5, 1, 1.5), (0, 4.2, -0.6))),
        (1.4, "rest", stage(0, (0, 0, 0))),
    ]),
}


def animations(gestures):
    return {name: (looped, priority, easing, [(t, {**pose, **gestures[TAKE[mood]]}) for t, mood, pose in frames])
            for name, (looped, priority, easing, frames) in STAGES.items()}


def rod_data(rod):
    spirit_parts, spirit_joints, gestures = rod.decor()
    return SimpleNamespace(PARTS=[*frame_parts(rod.rod, rod.band, rod.grip, rod.trim, rod.bobber), *spirit_parts],
                           JOINTS=[*JOINTS, *spirit_joints], ANIMATIONS=animations(gestures))


def build_model(kind, rod, data):
    parts = {}
    for name, shape, size, rest, color, _ in data.PARTS:
        part = build_part(name, shape, size, rest, color, anchored=name == "HumanoidRootPart")
        part.rest = rest
        if name == "LineEnd":
            set_prop(part, "Transparency", '<float name="Transparency">1</float>')
        parts[name] = part

    model = Item("Model", [
        xml_string("Name", f"Rod_{kind}"),
        f'<Ref name="PrimaryPart">{parts["HumanoidRootPart"].ref}</Ref>',
        f'<token name="ModelStreamingMode">{MODEL_STREAMING_ATOMIC}</token>',
        xml_attributes({"Anim": "Idle", "Rarity": rod.rarity}),
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

    for script_name, source_path in (("RodAnimator", HERE.parent / "PoliceGoose" / "GooseAnimator.client.luau"),
                                     ("RodEffects", HERE / "RodEffects.client.luau")):
        model.add(Item("Script", [
            xml_string("Name", script_name),
            f'<token name="RunContext">{RUN_CONTEXT_CLIENT}</token>',
            f'<ProtectedString name="Source"><![CDATA[{source_path.read_text(encoding="utf-8")}]]></ProtectedString>',
        ]))
    return model


def main():
    for kind, rod in RODS.items():
        data = rod_data(rod)
        xml = ('<roblox xmlns:xmime="http://www.w3.org/2005/05/xmlmime" '
               'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
               'xsi:noNamespaceSchemaLocation="http://www.roblox.com/roblox.xsd" version="4">\n'
               "  <External>null</External>\n  <External>nil</External>\n"
               f"{build_model(kind, rod, data).to_xml()}</roblox>\n")
        out = HERE / f"Rod_{kind}.rbxmx"
        out.write_text(xml, encoding="utf-8")
        print(f"Wrote {out.name} ({len(data.PARTS)} parts, {len(data.JOINTS)} joints)")
        export(data, f"Rod_{kind}", HERE / f"Rod_{kind}.glb")


if __name__ == "__main__":
    main()
