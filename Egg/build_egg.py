"""Builds Egg_<Kind>.rbxmx and .glb (rig + KeyframeSequences + client scripts) for the six eggs.

Run: python build_egg.py
Reuses the rbxmx writer of ../PoliceGoose. Coordinates are in studs, ground at y = 0, the egg faces -Z.
All eggs share one frame: the shell is split at the cut plane y = CUT into Base (lower half, root of the rig) and
Top (upper half, carries the Topper accessory), the break line is a zigzag of tooth plates, and a smiling Star hides
inside the lower half until Hatch. Each kind only differs in colors, surface pattern and accessories (EGGS below).
"""

import math
import sys
from pathlib import Path
from types import SimpleNamespace

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "PoliceGoose"))

from build_police_goose import (  # noqa: E402
    BLACK, CF, GOLD, MODEL_STREAMING_ATOMIC, ORANGE, RUN_CONTEXT_CLIENT, SILVER, WHITE, Item, angles, build_joint,
    build_keyframe_sequence, build_part, cf, xml_attributes, xml_string,
)
from export_glb import export  # noqa: E402

PINK = (255, 111, 181)
BLUE = (61, 184, 245)
PURPLE = (155, 107, 255)
LAVENDER = (214, 190, 255)
GREEN = (92, 214, 107)
RED = (255, 90, 77)
MINT = (127, 240, 208)
GOLD_DARK = (201, 154, 18)
WOOD = (181, 115, 60)
CRACK = (122, 74, 36)
PEARL = (252, 240, 250)
RAINBOW = [RED, ORANGE, GOLD, GREEN, BLUE, PURPLE, PINK]

CUT = 1.5
RADIUS = 1.15
BAND_RADIUS = 1.14
LOWER_BAND = (1.0, CUT)
UPPER_BAND = (CUT, 1.75)
TOP_SHELL = 2.85
TOPPER_Y = 2.65
STAR_CENTER = (0.0, 0.85, 0.0)
MATERIAL_NEON = 288


def egg_radius(y):
    """Radius of the egg at height y: widest near the cut plane, a little narrower toward the top."""
    t = (y - CUT) / CUT
    return RADIUS * math.sqrt(max(1 - t * t, 0)) * (1 - 0.12 * t)


def surface_frame(phi, y, inset=0.0):
    """Frame on the egg surface: z = outward normal, y = up along the shell, x = toward the viewer's right.
    phi is the angle around the egg in degrees, 0 = front (-Z), positive toward the viewer's right (+X is left)."""
    p = math.radians(phi)
    r = egg_radius(y)
    slope = (egg_radius(y + 0.01) - egg_radius(y - 0.01)) / 0.02
    n = (-math.sin(p), -slope, -math.cos(p))
    length = math.sqrt(sum(v * v for v in n))
    n = tuple(v / length for v in n)
    x = (-math.cos(p), 0.0, math.sin(p))
    up = (n[1] * x[2] - n[2] * x[1], n[2] * x[0] - n[0] * x[2], n[0] * x[1] - n[1] * x[0])
    pos = (-r * math.sin(p) - inset * n[0], y - inset * n[1], -r * math.cos(p) - inset * n[2])
    return CF(pos, ((x[0], up[0], n[0]), (x[1], up[1], n[1]), (x[2], up[2], n[2])))


def half_of(y):
    return "Top" if y > CUT else "Base"


def shade(color, amount):
    return tuple(int(c * amount) for c in color)


# ---------------------------------------------------------------- shared frame: shell, teeth, cracks, star

def cylinder_band(name, y_lo, y_hi, color, bone):
    """Vertical cylinder with a flat face: the straight ring of shell around the cut plane."""
    return (name, "cylinder", (y_hi - y_lo, 2 * BAND_RADIUS, 2 * BAND_RADIUS),
            cf(0, (y_lo + y_hi) / 2, 0, 0, 0, 90), color, bone)


def shell_slices(prefix, y_lo, y_hi, count, color, bone, floor=None):
    """Stack of flattened ellipsoids that follows the egg profile; they overlap so the surface stays smooth."""
    step = (y_hi - y_lo) / count
    parts = []
    for i in range(count):
        a, b = y_lo + i * step, y_lo + (i + 1) * step
        lo, hi = a - 2.5 * step, b + 2.5 * step
        if floor is not None:
            lo = max(lo, floor)
        width = 2 * egg_radius((a + b) / 2)
        parts.append((f"{prefix}{i + 1}", "ellipsoid", (width, hi - lo, width), cf(0, (lo + hi) / 2, 0), color, bone))
    return parts


TEETH = 10
TOOTH_HALF = math.pi * BAND_RADIUS / TEETH  # half the width of one tooth diamond, measured along the shell
TOOTH_RISE = TOOTH_HALF / 2


def tooth_parts(color):
    """Jagged break line. Square plates turned 45 degrees stand on the shell: the lower half's tips point up and the
    upper half's tips point down, offset by half a pitch, so when closed they tile the seam and when apart both
    halves keep a zigzag edge (the egg looks cracked in two, not cut)."""
    side = TOOTH_HALF * math.sqrt(2)
    parts = []
    pitch = 360 / TEETH
    for k in range(TEETH):
        for name, phi, y, bone in ((f"ToothLow{k + 1}", k * pitch, CUT - TOOTH_RISE, "Base"),
                                   (f"ToothUp{k + 1}", k * pitch + pitch / 2, CUT + TOOTH_RISE, "Top")):
            parts.append((name, "block", (side, side, 0.08), surface_frame(phi, y, inset=0.06) * angles(rz=45),
                          color, bone))
    return parts


# level: [(phi, y)] points of a zigzag; the game shows level 1, 2, 3 as the incubation progresses.
CRACKS = {
    1: [(8, 2.4), (16, 2.2), (9, 2.05), (17, 1.85)],
    2: [(-4, 1.3), (-8, 1.1), (-3, 0.9), (-7, 0.65)],
    3: [(105, 1.35), (99, 1.2), (106, 1.05), (100, 0.9), (-62, 2.3), (-68, 2.1), (-61, 1.95), (-67, 1.75)],
}


def crack_parts():
    parts = []
    for level, points in CRACKS.items():
        # The level 3 list holds two separate zigzags; the break between them is where phi jumps.
        for i, ((p0, y0), (p1, y1)) in enumerate(zip(points, points[1:])):
            if abs(p1 - p0) > 30:
                continue
            y = (y0 + y1) / 2
            dx = math.radians(p1 - p0) * egg_radius(y)
            dy = y1 - y0
            frame = surface_frame((p0 + p1) / 2, y) * angles(rz=math.degrees(math.atan2(dy, dx)))
            parts.append((f"Crack{level}_{i + 1}", "block", (math.hypot(dx, dy) + 0.03, 0.07, 0.07), frame, CRACK,
                          half_of(y)))
    return parts


def star_parts():
    """Five-armed chubby star (arms are flattened ellipsoids) with a face on its front (-Z)."""
    cx, cy, cz = STAR_CENTER
    parts = [("Star", "ellipsoid", (0.8, 0.8, 0.5), cf(cx, cy, cz), GOLD, None)]
    for i in range(5):
        a = 72 * i
        parts.append((f"StarArm{i + 1}", "ellipsoid", (0.5, 0.85, 0.26),
                      cf(cx - 0.36 * math.sin(math.radians(a)), cy + 0.36 * math.cos(math.radians(a)), cz, 0, 0, a),
                      GOLD, "Star"))
    for side, x in (("L", -1), ("R", 1)):
        parts += [
            (f"StarEye{side}", "ellipsoid", (0.14, 0.2, 0.08), cf(cx + x * 0.17, cy + 0.07, cz - 0.22), BLACK, "Star"),
            (f"StarShine{side}", "ball", (0.06, 0.06, 0.06), cf(cx + x * 0.15, cy + 0.12, cz - 0.27), WHITE, "Star"),
            (f"StarBlush{side}", "ellipsoid", (0.15, 0.09, 0.06), cf(cx + x * 0.3, cy - 0.06, cz - 0.17), PINK, "Star"),
            (f"StarSmile{side}", "block", (0.1, 0.035, 0.04), cf(cx + x * 0.11, cy - 0.08, cz - 0.225, 0, 0, x * 25),
             BLACK, "Star"),
        ]
    parts.append(("StarSmileC", "block", (0.1, 0.035, 0.04), cf(cx, cy - 0.115, cz - 0.235), BLACK, "Star"))
    return parts


# ---------------------------------------------------------------- pattern helpers (colored decorations)

def dots(prefix, items, color, thickness=0.16):
    """Flat discs on the shell: (phi, y, diameter). Keep them clear of the seam and of the crack lines."""
    return [(f"{prefix}{i + 1}", "ellipsoid", (d, d, thickness), surface_frame(phi, y), color, half_of(y))
            for i, (phi, y, d) in enumerate(items)]


def swirl(name, phi, y, radius, color, bone, segments=8):
    """Ring made of small blocks lying on the shell (no torus primitive in Roblox) with a dot in the middle."""
    frame = surface_frame(phi, y, inset=0.02)
    chord = 2 * radius * math.sin(math.pi / segments) + 0.02
    parts = [(f"{name}_{i + 1}", "block", (chord, 0.06, 0.06),
              frame * cf(radius * math.cos(math.radians(a)), radius * math.sin(math.radians(a)), 0, 0, 0, a + 90),
              color, bone)
             for i, a in enumerate(360 * i / segments for i in range(segments))]
    parts.append((f"{name}_Dot", "ball", (0.13, 0.13, 0.13), frame, color, bone))
    return parts


def plate_rows(prefix, ys, side, pitch, color_of):
    """Rows of diamond plates (staggered like scales or cut facets) lying on the shell, kept off the seam."""
    parts = []
    for r, y in enumerate(ys):
        n = max(4, round(2 * math.pi * egg_radius(y) / pitch))
        for k in range(n):
            phi = 360 * k / n + (180 / n if r % 2 else 0)
            parts.append((f"{prefix}{r + 1}_{k + 1}", "block", (side, side, 0.07),
                          surface_frame(phi, y, inset=0.02) * angles(rz=45), color_of(r, k), half_of(y)))
    return parts


def crystal(name, frame, height, width, color, bone):
    """Column with a diamond cross-section topped by a cube standing on its corner. frame: y = column axis."""
    return [
        (name, "block", (width, height, width), frame * cf(y=height / 2, ry=45), color, bone),
        (f"{name}Tip", "block", (width * 0.75,) * 3, frame * cf(y=height) * angles(rx=-35.264, rz=45), color,
         bone or name),
    ]


def spike(name, frame, length, width, color, bone):
    """Rounded cone made of three stacked ellipsoids along the frame's y axis. With bone None the first one is the
    bone itself (named name) and the others are welded to it."""
    return [(name if i == 1 and bone is None else f"{name}{i}", "ellipsoid", (width * w, length * h, width * w),
             frame * cf(y=length * y), color, None if i == 1 and bone is None else bone or name)
            for i, (w, h, y) in enumerate(((1.0, 0.5, 0.2), (0.7, 0.45, 0.5), (0.4, 0.4, 0.8)), start=1)]


def ring_around(radius, height, tilt, colors, segments=16):
    """Spinning halo: a ring of Neon blocks around the egg, tilted. Part "Halo" is the hub the script rotates."""
    hub = CF((0, height, 0)) * angles(rx=tilt)
    parts = [("Halo", "block", (0.1, 0.1, 0.1), hub, WHITE, "HumanoidRootPart")]
    chord = 2 * radius * math.sin(math.pi / segments) + 0.04
    for i in range(segments):
        a = 360 * i / segments
        frame = hub * cf(radius * math.cos(math.radians(a)), 0, radius * math.sin(math.radians(a)), 0, -(a + 90), 0)
        parts.append((f"HaloRing{i + 1}", "block", (chord, 0.1, 0.1), frame, colors[i % len(colors)], "Halo"))
    return parts


# ---------------------------------------------------------------- the six eggs

STARTER_SPOTS = [(-35, 0.62, 0.62), (30, 0.95, 0.7), (75, 0.55, 0.45), (-80, 1.05, 0.5), (0, 0.3, 0.4),
                 (150, 0.8, 0.6), (-145, 0.6, 0.55), (-20, 2.0, 0.55), (45, 2.1, 0.5), (105, 1.85, 0.5),
                 (-100, 2.15, 0.45), (180, 2.0, 0.55), (-160, 2.1, 0.5)]


def starter_decor():
    """Pot lid on top (silver plate and dome, black handle, two latches with bolts) and orange spots."""
    topper = [
        ("Topper", "cylinder", (0.2, 1.84, 1.84), cf(0, TOPPER_Y + 0.1, 0, 0, 0, 90), SILVER, None),
        ("LidDome", "ellipsoid", (1.5, 0.6, 1.5), cf(0, 2.86, 0), SILVER, "Topper"),
        ("HandleBar", "block", (0.8, 0.13, 0.18), cf(0, 3.33, 0), BLACK, "Topper"),
    ]
    for side, x in (("L", -1), ("R", 1)):
        topper += [
            (f"HandlePost{side}", "block", (0.12, 0.3, 0.14), cf(x * 0.3, 3.2, 0), BLACK, "Topper"),
            (f"Latch{side}", "block", (0.2, 0.42, 0.3), cf(x * 0.98, 2.6, 0), BLACK, "Topper"),
            (f"LatchBolt{side}", "ball", (0.1, 0.1, 0.1), cf(x * 1.0, 2.68, -0.16), SILVER, "Topper"),
        ]
    return [*dots("Spot", STARTER_SPOTS, ORANGE), *topper]


MOSS = [(-35, 0.5, 0.7), (20, 0.8, 0.8), (75, 0.45, 0.55), (-80, 1.0, 0.6), (150, 0.7, 0.8), (-145, 0.5, 0.7),
        (0, 0.25, 0.5), (-20, 2.05, 0.6), (50, 2.15, 0.55), (110, 1.9, 0.5), (-100, 2.2, 0.5), (180, 2.05, 0.6)]


def reed_decor():
    """Moss patches, a tuft of grass and two cattails on top, and a frog that wants to share the egg."""
    stem, head, tip = GREEN, WOOD, CRACK
    topper = [("Topper", "ellipsoid", (1.0, 0.34, 1.0), cf(0, 2.85, 0), GREEN, None)]
    blades = [(-0.3, 0.1, 0, 10, 1.1), (0.1, 0.25, -12, 0, 0.9), (-0.1, -0.25, 12, -6, 1.0), (0.35, 0.05, 0, -14, 0.8),
              (-0.45, -0.1, 4, 18, 0.7)]
    for i, (x, z, rx, rz, h) in enumerate(blades, start=1):
        topper.append((f"Blade{i}", "ellipsoid", (0.2, h, 0.07), cf(x, 2.95 + h / 2, z, rx, 0, rz), GREEN, "Topper"))
    for i, (x, z, stem_h, rz) in enumerate(((-0.15, 0.15, 1.2, 4), (-0.5, -0.1, 0.9, -8)), start=1):
        top = 2.9 + stem_h
        topper += [
            (f"CattailStem{i}", "block", (0.07, stem_h, 0.07), cf(x, 2.9 + stem_h / 2, z, 0, 0, rz), stem, "Topper"),
            (f"CattailHead{i}", "cylinder", (0.5, 0.22, 0.22), cf(x - 0.02, top - 0.05, z, 0, 0, 90 + rz), head,
             "Topper"),
            (f"CattailTip{i}", "ellipsoid", (0.1, 0.2, 0.1), cf(x - 0.02, top + 0.22, z), tip, "Topper"),
        ]
    fx, fy, fz, f = 0.25, 3.15, -0.12, 1.3  # frog center and size factor

    def at(dx, dy, dz):
        return fx + dx * f, fy + dy * f, fz + dz * f

    def sized(*size):
        return tuple(v * f for v in size)

    topper += [
        ("FrogBody", "ellipsoid", sized(0.7, 0.5, 0.6), cf(*at(0, 0, 0)), GREEN, "Topper"),
        ("FrogBelly", "ellipsoid", sized(0.45, 0.3, 0.3), cf(*at(0, -0.08, -0.22)), MINT, "Topper"),
        ("FrogLegL", "ellipsoid", sized(0.2, 0.18, 0.3), cf(*at(0.22, -0.22, -0.28)), GREEN, "Topper"),
        ("FrogLegR", "ellipsoid", sized(0.2, 0.18, 0.3), cf(*at(-0.22, -0.22, -0.28)), GREEN, "Topper"),
        ("FrogSmile", "block", sized(0.3, 0.03, 0.04), cf(*at(0, -0.03, -0.31)), BLACK, "Topper"),
    ]
    for side, x in (("L", 1), ("R", -1)):
        topper += [
            (f"FrogEye{side}", "ball", sized(0.26, 0.26, 0.26), cf(*at(x * 0.2, 0.28, -0.12)), WHITE, "Topper"),
            (f"FrogPupil{side}", "ball", sized(0.14, 0.14, 0.14), cf(*at(x * 0.2, 0.28, -0.24)), BLACK, "Topper"),
            (f"FrogShine{side}", "ball", sized(0.05, 0.05, 0.05), cf(*at(x * 0.18, 0.33, -0.29)), WHITE, "Topper"),
        ]
    return [*dots("Moss", MOSS, GREEN, 0.14), *topper]


BUBBLES = [(-60, 0.6, 0.35), (-100, 1.1, 0.25), (70, 0.5, 0.4), (110, 1.05, 0.3), (-140, 0.7, 0.4), (150, 0.9, 0.3),
           (60, 2.1, 0.35), (-50, 2.2, 0.3), (-110, 1.95, 0.25), (130, 2.2, 0.35), (180, 1.9, 0.3)]
WATER = (140, 215, 250)
BUBBLE_LIGHT = (200, 236, 255)


def bubble_decor():
    """Round porthole with a goldfish on the front, bubbles, and a snorkel standing on the top half."""
    window = surface_frame(0, 0.95, inset=0.02)
    fish = window * cf(0, 0, 0.1)
    parts = [
        ("PortholeRim", "ellipsoid", (1.0, 1.0, 0.16), window, GOLD, "Base"),
        ("PortholeWater", "ellipsoid", (0.82, 0.82, 0.18), window * cf(z=0.01), WATER, "Base"),
        ("FishBody", "ellipsoid", (0.44, 0.28, 0.12), fish * cf(0.05, 0, 0.02), ORANGE, "Base"),
        ("FishTail", "ellipsoid", (0.2, 0.28, 0.08), fish * cf(-0.2, 0, 0.02, 0, 0, 25), ORANGE, "Base"),
        ("FishFin", "ellipsoid", (0.16, 0.2, 0.08), fish * cf(0.04, 0.17, 0.02, 0, 0, -20), RED, "Base"),
        ("FishEye", "ball", (0.08, 0.08, 0.08), fish * cf(0.19, 0.04, 0.08), BLACK, "Base"),
        ("FishShine", "ball", (0.03, 0.03, 0.03), fish * cf(0.2, 0.06, 0.12), WHITE, "Base"),
        ("WaterBubble1", "ball", (0.1, 0.1, 0.1), window * cf(0.2, 0.22, 0.12), BUBBLE_LIGHT, "Base"),
        ("WaterBubble2", "ball", (0.07, 0.07, 0.07), window * cf(0.27, 0.12, 0.12), BUBBLE_LIGHT, "Base"),
        *dots("Bubble", BUBBLES, BUBBLE_LIGHT, 0.14),
    ]
    sx = -1.0
    snorkel = [
        ("Topper", "cylinder", (1.6, 0.2, 0.2), cf(sx, 2.95, -0.05, 0, 0, 90), (31, 100, 200), None),
        ("SnorkelCap", "ball", (0.27, 0.27, 0.27), cf(sx, 3.78, -0.05), (31, 100, 200), "Topper"),
        ("SnorkelMouth", "cylinder", (0.4, 0.2, 0.2), cf(sx - 0.18, 3.7, -0.05), (31, 100, 200), "Topper"),
        ("SnorkelBand", "cylinder", (0.18, 0.27, 0.27), cf(sx, 3.4, -0.05, 0, 0, 90), GOLD, "Topper"),
        ("SnorkelClamp", "cylinder", (0.2, 0.32, 0.32), cf(sx, 2.35, -0.05, 0, 0, 90), GOLD, "Topper"),
        ("SnorkelBubble1", "ball", (0.2, 0.2, 0.2), cf(sx - 0.35, 4.1, -0.05), BUBBLE_LIGHT, "Topper"),
        ("SnorkelBubble2", "ball", (0.13, 0.13, 0.13), cf(sx - 0.55, 4.4, -0.05), BUBBLE_LIGHT, "Topper"),
    ]
    return [*parts, *snorkel]


def crystal_decor():
    """Cut-crystal facets, a ring of crystals around the base, a crystal cluster on top, floating bubbles."""
    palette = [LAVENDER, PURPLE, shade(PURPLE, 0.72)]
    parts = plate_rows("Facet", [0.5, 1.0, 2.0, 2.5], 0.56, 0.79, lambda r, k: palette[(r + k) % 3])
    for i in range(8):
        psi = 45 * i + 20
        foot = (-1.0 * math.sin(math.radians(psi)), 0.0, -1.0 * math.cos(math.radians(psi)))
        parts += crystal(f"BaseCrystal{i + 1}", CF(foot) * angles(ry=psi + 180) * angles(rx=20),
                         1.2 - 0.2 * (i % 2), 0.26, shade(PURPLE, 0.85) if i % 2 else LAVENDER, "Base")
    parts += [
        *crystal("Topper", cf(0, 2.75, 0), 1.25, 0.36, LAVENDER, None),
        *crystal("TopCrystalL", cf(0.38, 2.7, 0.05, 0, 0, -20), 0.85, 0.28, PURPLE, "Topper"),
        *crystal("TopCrystalR", cf(-0.38, 2.7, 0.05, 0, 0, 20), 0.7, 0.26, shade(PURPLE, 0.8), "Topper"),
    ]
    for i, (x, y, size, color) in enumerate(((0.85, 3.2, 0.3, PINK), (1.05, 3.7, 0.2, MINT), (-0.8, 3.4, 0.26, BLUE),
                                             (-1.0, 3.9, 0.17, PINK)), start=1):
        parts.append((f"FloatBubble{i}", "ball", (size,) * 3, cf(x, y, 0), color, "Topper"))
        parts.append((f"FloatShine{i}", "ball", (size * 0.3,) * 3, cf(x + size * 0.15, y + size * 0.2, -size * 0.35),
                      WHITE, "Topper"))
    return parts


def gold_decor():
    """Gold egg with darker gold swirls, goose bite holes, two white feathers on top and a spinning halo."""
    parts = []
    for i, (phi, y, r) in enumerate(((-40, 0.6, 0.3), (45, 0.85, 0.3), (150, 0.7, 0.32), (-130, 0.9, 0.28),
                                     (-30, 2.1, 0.3), (50, 2.3, 0.28), (120, 2.0, 0.3), (-110, 2.3, 0.26),
                                     (180, 2.2, 0.3)), start=1):
        parts += swirl(f"Swirl{i}", phi, y, r, GOLD_DARK, half_of(y))
    holes = [(0, 0.45, 0.32), (-75, 1.0, 0.26), (95, 0.75, 0.3), (10, 2.3, 0.3), (-70, 1.95, 0.26), (150, 2.05, 0.28)]
    parts += dots("HoleRim", [(p, y, d + 0.1) for p, y, d in holes], GOLD_DARK, 0.14)
    parts += [(f"Hole{i}", "ellipsoid", (d, d, 0.2), surface_frame(p, y, inset=-0.01), CRACK, half_of(y))
              for i, (p, y, d) in enumerate(holes, start=1)]
    parts += [
        ("Topper", "ellipsoid", (0.5, 0.2, 0.5), cf(0, 2.85, 0), GOLD_DARK, None),
        ("Feather1", "ellipsoid", (0.38, 0.8, 0.06), cf(0.4, 3.1, 0, 0, 0, -50), WHITE, "Topper"),
        ("Feather1Gold", "ellipsoid", (0.07, 0.65, 0.08), cf(0.4, 3.1, -0.01, 0, 0, -50), GOLD, "Topper"),
        ("Feather2", "ellipsoid", (0.38, 0.8, 0.06), cf(-0.4, 3.1, 0, 0, 0, 50), WHITE, "Topper"),
        ("Feather2Gold", "ellipsoid", (0.07, 0.65, 0.08), cf(-0.4, 3.1, -0.01, 0, 0, 50), GOLD, "Topper"),
    ]
    return [*parts, *ring_around(1.75, 1.5, 24, [(255, 215, 95)])]


def dragon_decor():
    """Rainbow scales, gold spikes, a paper bag with a fish that hangs from the side, and a rainbow halo."""
    parts = plate_rows("Scale", [0.4, 0.75, 1.1, 1.9, 2.25, 2.6], 0.5, 0.707, lambda r, k: RAINBOW[r])
    parts += spike("Topper", cf(0, 2.8, 0), 0.9, 0.34, GOLD, None)
    for i, (phi, y, tilt) in enumerate(((65, 2.5, 38), (-65, 2.5, 38), (115, 2.15, 42), (-115, 2.15, 42)), start=1):
        parts += spike(f"Spike{i}", surface_frame(phi, y, inset=0.1) * angles(rx=tilt), 0.75, 0.3, GOLD, "Topper")
    hinge = surface_frame(70, 1.0).pos
    hx, hy, hz = hinge
    paper = (230, 190, 130)
    parts += [
        ("BagHinge", "block", (0.1, 0.1, 0.1), cf(hx, hy, hz), WHITE, "Base"),
        ("BagLoop", "ball", (0.14, 0.14, 0.14), cf(hx, hy, hz), SILVER, "BagHinge"),
        ("BagString", "block", (0.04, 0.3, 0.04), cf(hx - 0.04, hy - 0.15, hz), SILVER, "BagHinge"),
        ("BagBody", "block", (0.55, 0.6, 0.3), cf(hx - 0.1, hy - 0.62, hz), paper, "BagHinge"),
        ("BagFold", "block", (0.57, 0.12, 0.32), cf(hx - 0.1, hy - 0.36, hz), WOOD, "BagHinge"),
        ("BagFish", "ellipsoid", (0.24, 0.14, 0.04), cf(hx - 0.1, hy - 0.64, hz - 0.16), ORANGE, "BagHinge"),
        ("BagFishTail", "ellipsoid", (0.1, 0.12, 0.04), cf(hx + 0.04, hy - 0.64, hz - 0.16, 0, 0, 25), ORANGE,
         "BagHinge"),
    ]
    return [*parts, *ring_around(1.8, 1.5, -14, RAINBOW)]


# rarity: the Rarity attribute read by EggEffects. shell: shell and teeth color. lining: color of the flat cut faces.
EGGS = {
    "Starter": SimpleNamespace(rarity="Common", shell=WHITE, lining=(255, 205, 140), decor=starter_decor),
    "Reed": SimpleNamespace(rarity="Common", shell=WHITE, lining=(225, 240, 190), decor=reed_decor),
    "Bubble": SimpleNamespace(rarity="Rare", shell=BLUE, lining=(200, 235, 255), decor=bubble_decor),
    "Crystal": SimpleNamespace(rarity="Epic", shell=PURPLE, lining=LAVENDER, decor=crystal_decor),
    "Gold": SimpleNamespace(rarity="Legendary", shell=GOLD, lining=(255, 236, 170), decor=gold_decor),
    "Dragon": SimpleNamespace(rarity="Mythic", shell=PEARL, lining=(255, 230, 240), decor=dragon_decor),
}


def egg_parts(egg):
    return [
        ("HumanoidRootPart", "block", (1, 1, 1), cf(0, 0.5, 0), WHITE, None),
        cylinder_band("Base", *LOWER_BAND, egg.shell, None),
        *shell_slices("BaseShell", 0, LOWER_BAND[0], 8, egg.shell, "Base", floor=0),
        ("LiningLower", "cylinder", (0.04, 2.0, 2.0), cf(0, CUT, 0, 0, 0, 90), egg.lining, "Base"),
        cylinder_band("Top", *UPPER_BAND, egg.shell, None),
        *shell_slices("TopShell", UPPER_BAND[1], TOP_SHELL, 8, egg.shell, "Top"),
        ("LiningUpper", "cylinder", (0.04, 2.0, 2.0), cf(0, CUT, 0, 0, 0, 90), egg.lining, "Top"),
        *tooth_parts(egg.shell),
        *crack_parts(),
        *egg.decor(),
        *star_parts(),
    ]


JOINTS = [
    ("Base", "HumanoidRootPart", (0, 0, 0)),
    ("Top", "Base", (0, CUT, 0)),
    ("Topper", "Top", (0, TOPPER_Y, 0)),
    ("Star", "Base", STAR_CENTER),
]

P = cf


def rattle(roll, lift, topper_roll):
    return {"Base": P(y=0.04, rz=roll), "Topper": P(y=lift, rz=topper_roll)}


# Standard timing (see STYLE_GUIDE.md section 4.5): Idle and Incubate loop every 2.4 s; Hatch lasts 5.0 s. The egg
# rocks with growing swings while cracks appear (0 to 2.0), squashes at 2.0, the shell gives at 2.2 and breaks in two
# at 2.4. The top half is shoved up and sideways, tips over and lands beside the base at 3.4 (a small bounce, then it
# rests); the star pushes out slowly, spins and hovers above. EggEffects uses the same marks.
# name: (looped, priority, easing, [(time, {joint: transform})])
TOP_LANDED = {"Top": P(x=1.9, y=0.1, rz=-120)}
ANIMATIONS = {
    "Idle": (True, "Idle", "Cubic", [
        (0.0, {}),
        (0.6, {"Base": P(y=0.02, rz=2)}),
        (1.2, {}),
        (1.8, {"Base": P(y=0.02, rz=-2)}),
        (2.4, {}),
    ]),
    "Incubate": (True, "Action", "Cubic", [
        (0.0, {}),
        (0.2, rattle(3, 0.08, -4)),
        (0.5, rattle(-3, 0, 3)),
        (0.8, rattle(2.5, 0.08, -3)),
        (1.1, rattle(-2, 0, 2)),
        (1.4, {"Base": P(rz=1)}),
        (1.6, {}),
        (2.0, {"Base": P(y=0.06)}),
        (2.4, {}),
    ]),
    "Hatch": (False, "Action", "Cubic", [
        (0.0, {}),
        (0.4, {"Base": P(y=0.02, rz=3), "Topper": P(y=0.05, rz=-3)}),
        (0.8, {"Base": P(rz=-4), "Topper": P(y=0.06, rz=4)}),
        (1.2, {"Base": P(y=0.03, rz=5), "Topper": P(y=0.08, rz=-5)}),
        (1.6, {"Base": P(rz=-6), "Topper": P(y=0.1, rz=6)}),
        (2.0, {"Base": P(y=-0.2), "Top": P(y=-0.04)}),
        (2.2, {"Base": P(y=0.04, rz=4), "Top": P(y=0.12, rz=3), "Topper": P(y=0.2, rz=-8)}),
        (2.4, {"Base": P(rz=6), "Top": P(x=0.2, y=0.85, rz=-16), "Topper": P(y=0.25, rz=-12),
               "Star": P(y=0.75, ry=20)}),
        (2.7, {"Base": P(rz=2), "Top": P(x=0.7, y=1.1, rz=-32), "Topper": P(y=0.15, rz=8), "Star": P(y=1.3, ry=70)}),
        (3.1, {"Base": P(rz=-2), "Top": P(x=1.3, y=0.9, rz=-70), "Topper": P(y=0.05, rz=-5),
               "Star": P(x=-0.2, y=2.1, ry=160)}),
        (3.4, {"Base": P(y=-0.08), "Top": P(x=1.8, y=0.25, rz=-118), "Star": P(x=-0.3, y=2.4, ry=250)}),
        (3.6, {"Top": P(x=1.9, y=0.45, rz=-112), "Star": P(y=2.3, ry=310)}),
        (3.8, {**TOP_LANDED, "Star": P(y=2.1, ry=358, rz=6)}),
        (4.2, {**TOP_LANDED, "Star": P(y=1.9, rz=-6)}),
        (4.6, {**TOP_LANDED, "Star": P(y=2.0, rz=4)}),
        (5.0, {**TOP_LANDED, "Star": P(y=1.95)}),
    ]),
}


def egg_data(egg):
    return SimpleNamespace(PARTS=egg_parts(egg), JOINTS=JOINTS, ANIMATIONS=ANIMATIONS)


def set_prop(part, name, xml):
    """Replace a property of a Roblox part item (or add it)."""
    prefix = f'<token name="{name}">' if name == "Material" else f'<float name="{name}">'
    part.props = [p for p in part.props if not p.startswith(prefix)] + [xml]


def build_model(kind, egg, data):
    parts = {}
    for name, shape, size, rest, color, _ in data.PARTS:
        part = build_part(name, shape, size, rest, color, anchored=name == "HumanoidRootPart")
        part.rest = rest
        if name.startswith("Crack") or name in ("Halo", "BagHinge"):
            set_prop(part, "Transparency", '<float name="Transparency">1</float>')
        if name.startswith("HaloRing"):
            set_prop(part, "Material", f'<token name="Material">{MATERIAL_NEON}</token>')
            set_prop(part, "Transparency", '<float name="Transparency">0.25</float>')
        parts[name] = part

    model = Item("Model", [
        xml_string("Name", f"Egg_{kind}"),
        f'<Ref name="PrimaryPart">{parts["HumanoidRootPart"].ref}</Ref>',
        f'<token name="ModelStreamingMode">{MODEL_STREAMING_ATOMIC}</token>',
        xml_attributes({"Anim": "Idle", "Rarity": egg.rarity}),
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

    for script_name, source_path in (("EggAnimator", HERE.parent / "PoliceGoose" / "GooseAnimator.client.luau"),
                                     ("EggEffects", HERE / "EggEffects.client.luau")):
        model.add(Item("Script", [
            xml_string("Name", script_name),
            f'<token name="RunContext">{RUN_CONTEXT_CLIENT}</token>',
            f'<ProtectedString name="Source"><![CDATA[{source_path.read_text(encoding="utf-8")}]]></ProtectedString>',
        ]))
    return model


def main():
    for kind, egg in EGGS.items():
        data = egg_data(egg)
        xml = ('<roblox xmlns:xmime="http://www.w3.org/2005/05/xmlmime" '
               'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
               'xsi:noNamespaceSchemaLocation="http://www.roblox.com/roblox.xsd" version="4">\n'
               "  <External>null</External>\n  <External>nil</External>\n"
               f"{build_model(kind, egg, data).to_xml()}</roblox>\n")
        out = HERE / f"Egg_{kind}.rbxmx"
        out.write_text(xml, encoding="utf-8")
        print(f"Wrote {out.name} ({len(data.PARTS)} parts, {len(data.JOINTS)} joints)")
        export(data, f"Egg_{kind}", HERE / f"Egg_{kind}.glb")


if __name__ == "__main__":
    main()
