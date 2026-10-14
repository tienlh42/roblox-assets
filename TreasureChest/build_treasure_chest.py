"""Builds TreasureChest_<Rarity>.rbxmx and .glb (rig + KeyframeSequences + client scripts) for all 5 rarities.

Run: python build_treasure_chest.py
Reuses the rbxmx writer of ../PoliceGoose. Coordinates are in studs, ground at y = 0, the chest faces -Z.
"""

import math
import sys
from pathlib import Path
from types import SimpleNamespace

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "PoliceGoose"))

from build_police_goose import (  # noqa: E402
    BLACK, CF, GOLD, MODEL_STREAMING_ATOMIC, ORANGE, PUPIL, RUN_CONTEXT_CLIENT, WHITE, Item, build_joint,
    build_keyframe_sequence, build_part, cf, xml_attributes, xml_string,
)
from export_glb import export  # noqa: E402

WOOD = (181, 115, 60)
WOOD_DARK = (122, 74, 36)
GOLD_DARK = (201, 154, 18)
COIN = (255, 215, 95)
TONGUE_GROOVE = (200, 55, 120)
PINK = (255, 111, 181)
BLUE = (61, 184, 245)
PURPLE = (155, 107, 255)
LAVENDER = (214, 190, 255)
MINT = (127, 240, 208)
GREEN = (92, 214, 107)
RED = (255, 90, 77)
RAINBOW = [RED, ORANGE, GOLD, GREEN, BLUE, PURPLE]
GEM_COLORS = [RED, BLUE, GREEN, PURPLE, PINK, MINT, ORANGE, BLUE]

# scale: Common is 2.6 studs tall. body is the wood, trim the lid hoops and side bands, metal the corner
# brackets and lock, iris the eyes, gems how many gems lie in the loot, side the side decoration
# ("ring" handle or the color of a gem plate).
TIERS = {
    "Common": dict(scale=1.1, body=WOOD, trim=GOLD, metal=GOLD, iris=MINT, gems=3, side="ring"),
    "Rare": dict(scale=1.2, body=WOOD, trim=BLUE, metal=GOLD, iris=BLUE, gems=4, side="ring"),
    "Epic": dict(scale=1.35, body=PURPLE, trim=GOLD, metal=GOLD, iris=PINK, gems=5, side=PINK),
    "Legendary": dict(scale=1.5, body=GOLD, trim=GOLD_DARK, metal=GOLD_DARK, iris=BLUE, gems=6, side=BLUE),
    "Mythic": dict(scale=1.7, body=WHITE, trim=GOLD, metal=GOLD, iris=PURPLE, gems=7, side="ring"),
}

# Base height (= lid hinge height) and the half-ellipse of the arched lid (z radius, y radius).
H = 1.4
ARCH_Z, ARCH_Y = 1.03, 0.95
TOP = H + ARCH_Y
# x, y above the base top, z, yaw of the gem.
LOOT_GEMS = [(-0.6, 0.5, -0.1, 20), (0.5, 0.5, 0.15, -25), (0.0, 0.55, 0.4, 10), (-0.2, 0.45, -0.45, -15),
             (0.75, 0.4, -0.3, 30), (-0.85, 0.35, 0.3, -10), (0.3, 0.45, -0.5, 0), (-0.4, 0.55, 0.35, 15)]
# width, thickness, length, z of each ellipsoid; the tongue is 1.7 long and widens from 0.5 to 1.2.
TONGUE_SEGMENTS = [(0.5, 0.16, 0.6, -0.55), (0.62, 0.16, 0.6, -0.3), (0.76, 0.17, 0.6, -0.05),
                   (0.92, 0.17, 0.6, 0.2), (1.07, 0.18, 0.6, 0.45), (1.2, 0.18, 0.55, 0.7)]
FEATHERS = [(15, 2.2), (38, 1.95), (60, 1.6), (80, 1.2)]  # angle from vertical (degrees), length
LOOT_COINS = [(-0.9, 0.2, -0.2, 70), (0.9, 0.22, 0.1, 110), (0.1, 0.3, -0.6, 80), (-0.3, 0.35, 0.5, 100),
              (0.6, 0.3, 0.45, 60), (-0.6, 0.38, -0.5, 120)]

P = cf


def wings(angle):
    """Only Mythic has wings; the other tiers ignore these poses."""
    return {"WingL": P(rz=angle), "WingR": P(rz=-angle)}


def shake(roll, lid, wing):
    return {"Base": P(y=0.05, rz=roll), "Lid": P(rx=lid), **wings(wing)}


# Lid hinge is at the back, so +rx lifts the front of the lid. The tongue rests flat inside the base with its
# narrow root at the front; to come out it turns 180 degrees around that root and sticks out, drooping a little.
def tongue_out(wag=0):
    return P(y=0.5, rx=-20, ry=180 + wag)


OPEN_HOLD = {"Lid": P(rx=105), "Tongue": tongue_out(), **wings(25)}


def tongue_wag(lid, wag):
    return {"Lid": P(rx=lid), "Tongue": tongue_out(wag), **wings(30)}


# name: (looped, priority, easing, [(time, {joint: transform})])
ANIMATIONS = {
    "Spawn": (False, "Action", "Cubic", [
        (0.0, {"Base": P(y=-1.3)}),
        (0.3, {"Base": P(y=0.75, rz=8), "Lid": P(rx=12)}),
        (0.5, {"Base": P(y=0.2, rz=-6), "Lid": P(rx=4)}),
        (0.65, {"Base": P(y=-0.12)}),
        (0.85, {"Base": P(y=0.18, rz=4), "Lid": P(rx=8)}),
        (1.05, {"Base": P(y=0)}),
        (1.2, {}),
    ]),
    "Idle": (True, "Idle", "Cubic", [
        (0.0, {}),
        (0.1, shake(5, 8, 15)),
        (0.2, shake(-5, 2, 5)),
        (0.3, shake(4, 7, 15)),
        (0.4, shake(-4, 2, 5)),
        (0.5, shake(2, 4, 10)),
        (0.6, {}),
        (1.0, {"Base": P(y=0.08), **wings(6)}),
        (1.4, {}),
    ]),
    "Open": (False, "Action", "Cubic", [
        (0.0, {}),
        (0.15, {"Base": P(y=-0.2)}),
        (0.3, {"Base": P(y=-0.25, rz=3)}),
        (0.42, {"Base": P(y=0.35), "Lid": P(rx=125), "Tongue": P(y=0.2, ry=90), **wings(35)}),
        (0.6, {**OPEN_HOLD, "Lid": P(rx=100)}),
        (0.8, tongue_wag(108, 14)),
        (1.0, tongue_wag(104, -14)),
        (1.2, tongue_wag(106, 12)),
        (1.4, OPEN_HOLD),
    ]),
    "Vanish": (False, "Action", "Cubic", [
        (0.0, OPEN_HOLD),
        (0.25, {"Base": P(y=0.5)}),
        (0.4, {"Base": P(y=-0.1)}),
        (0.55, {"Base": P(y=0.15, ry=120)}),
        (0.9, {"Base": P(y=-1.5, ry=240)}),
        (1.1, {"Base": P(y=-1.8, ry=358)}),
    ]),
}


def chest_data(tier):
    config = TIERS[tier]
    k = config["scale"]
    body, trim, metal, iris = config["body"], config["trim"], config["metal"], config["iris"]

    def part(name, shape, size, pos, color, bone, rot=(0, 0, 0)):
        return (name, shape, tuple(s * k for s in size), cf(*(p * k for p in pos), *rot), color, bone)

    def placed(name, shape, size, frame, color, bone):
        return (name, shape, tuple(s * k for s in size), CF(tuple(p * k for p in frame.pos), frame.rot), color, bone)

    def mirrored(name, shape, size, pos, color, bone, rot=(0, 0, 0)):
        """Left part at -x and right part at +x; ry and rz are mirrored. A "{}" in bone becomes L or R."""
        x, y, z = pos
        rx, ry, rz = rot
        left, right = (bone and bone.format(side) for side in "LR")
        return [part(name + "L", shape, size, (-x, y, z), color, left, (rx, -ry, -rz)),
                part(name + "R", shape, size, (x, y, z), color, right, rot)]

    def arch(name, x, width, thickness, inset, color):
        """Half-ellipse of slabs over the base (lid shell, lining, hoops, end rims); inset moves it inward."""
        rz, ry, segments = ARCH_Z - inset, ARCH_Y - inset, 8
        points = [(rz * math.cos(math.pi * i / segments), ry * math.sin(math.pi * i / segments))
                  for i in range(segments + 1)]
        slabs = []
        for i, ((z0, y0), (z1, y1)) in enumerate(zip(points, points[1:])):
            length = math.hypot(z1 - z0, y1 - y0) + 0.03
            angle = math.degrees(math.atan2(-(y1 - y0), z1 - z0))
            slabs.append(part(f"{name}{i + 1}", "block", (width, thickness, length),
                              (x, H + (y0 + y1) / 2, (z0 + z1) / 2), color, "Lid", (angle, 0, 0)))
        return slabs

    def end_cap(name, x):
        """Wooden half-disc closing the lid at one end, made of stacked strips."""
        rz, ry, strips = ARCH_Z - 0.2, ARCH_Y - 0.2, 5
        height = ry / strips
        return [part(f"{name}{j + 1}", "block",
                     (0.12, height + 0.01, 2 * rz * math.sqrt(1 - ((j + 1) * height * 0.97 / ry) ** 2)),
                     (x, H + (j + 0.5) * height, 0), body, "Lid") for j in range(strips)]

    def ring(name, center, radius, segments=6):
        """Ring in the Y-Z plane built from small blocks (no torus primitive in Roblox)."""
        cx, cy, cz = center
        tangent = 2 * radius * math.tan(math.pi / segments) + 0.02
        angles = [360 * i / segments + 180 / segments for i in range(segments)]
        return [part(f"{name}{i + 1}", "block", (0.07, 0.07, tangent),
                     (cx, cy + radius * math.cos(math.radians(a)), cz + radius * math.sin(math.radians(a))),
                     metal, "Base", (a, 0, 0))
                for i, a in enumerate(angles)]

    def gem(name, pos, size, color, bone, yaw=0, tilt=15, cross=False, shine=False):
        """Brilliant-cut diamond seen from the front: a crown (flat table plus two sloped sides) over a
        pavilion that narrows to a point, every facet its own shade. cross adds a second plate turned 90
        degrees so the gem shows facets from every side; shine adds a white sparkle."""
        def lighter(amount):
            return tuple(int(c + (255 - c) * amount) for c in color)

        # shape, width, height, center, rotation, color. Wedges are turned so their slope faces outward.
        facets = [
            ("Table", "block", 0.6, 0.35, (0, 0.175), (0, 0, 0), lighter(0.6)),
            ("CrownL", "wedge", 0.2, 0.35, (-0.4, 0.175), (0, 90, 0), lighter(0.3)),
            ("CrownR", "wedge", 0.2, 0.35, (0.4, 0.175), (0, -90, 0), lighter(0.15)),
            ("PavL", "wedge", 0.5, 0.6, (-0.25, -0.3), (0, 90, 180), color),
            ("PavR", "wedge", 0.5, 0.6, (0.25, -0.3), (0, -90, 180), tuple(int(c * 0.78) for c in color)),
        ]
        base = CF(pos) * cf(rx=tilt, ry=yaw)
        result = []
        for turn, scale in ((0, 1.0), (90, 0.96)) if cross else ((0, 1.0),):
            thickness = 0.45
            for suffix, shape, width, height, (x, y), (rx, ry, rz), facet_color in facets:
                dims = (width, height, thickness) if shape == "block" else (thickness, height, width)
                frame = base * cf(ry=turn) * CF((x * size * scale, y * size * scale, 0)) * cf(rx=rx, ry=ry, rz=rz)
                result.append(placed(f"{name}{suffix}{'B' if turn else ''}", shape,
                                     tuple(d * size * scale for d in dims), frame, facet_color, bone))
        if shine:
            result.append(placed(f"{name}Shine", "ball", (0.16 * size,) * 3,
                                 base * CF((-0.15 * size, 0.3 * size, -0.3 * size)), WHITE, bone))
        return result

    # The back slab of the shell is the Lid bone itself; everything else on the lid is welded to it.
    shell = arch("LidShell", 0, 2.5, 0.16, 0.08, body)
    shell[0] = ("Lid", *shell[0][1:5], None)

    parts = [
        part("HumanoidRootPart", "block", (1, 1, 1), (0, 0.7, 0), WHITE, None),
        part("Base", "block", (2.6, H, 2.0), (0, H / 2, 0), body, None),
        part("Interior", "block", (2.3, 0.06, 1.7), (0, H, 0), WOOD_DARK, "Base"),
        part("Loot", "ellipsoid", (2.2, 0.9, 1.7), (0, H, 0.05), GOLD, "Base"),
        *[p for i, (x, y, z, yaw) in enumerate(LOOT_GEMS[:config["gems"]])
          for p in gem(f"LootGem{i + 1}", (x, H + y, z), 0.55, GEM_COLORS[i], "Base", yaw, tilt=20)],
        *[part(f"Coin{i + 1}", "cylinder", (0.05, 0.3, 0.3), (x, H + y, z), COIN, "Base", (0, 0, a))
          for i, (x, y, z, a) in enumerate(LOOT_COINS)],
        # Gold frame (corner posts, top rim, bottom strips) and side bands in the trim color.
        *[part(f"Post{i + 1}", "block", (0.3, H + 0.02, 0.3), (x, H / 2, z), metal, "Base")
          for i, (x, z) in enumerate(((-1.19, -0.89), (1.19, -0.89), (-1.19, 0.89), (1.19, 0.89)))],
        *[part(f"RimFB{i + 1}", "block", (2.68, 0.18, 0.1), (0, H - 0.09, z), metal, "Base")
          for i, z in enumerate((-1.03, 1.03))],
        *mirrored("RimSide", "block", (0.1, 0.18, 2.08), (1.33, H - 0.09, 0), metal, "Base"),
        *[part(f"Foot{i + 1}", "block", (2.68, 0.18, 0.1), (0, 0.09, z), metal, "Base")
          for i, z in enumerate((-1.03, 1.03))],
        *mirrored("Band", "block", (0.24, H + 0.02, 2.06), (1.0, H / 2, 0), trim, "Base"),
        part("Lock", "block", (0.62, 0.6, 0.12), (0, 0.7, -1.03), metal, "Base"),
        part("LockTop", "ellipsoid", (0.62, 0.5, 0.12), (0, 0.98, -1.03), metal, "Base"),
        part("Keyhole", "ball", (0.17, 0.17, 0.17), (0, 0.84, -1.1), BLACK, "Base"),
        part("KeyholeSlot", "block", (0.08, 0.26, 0.04), (0, 0.68, -1.1), BLACK, "Base"),
        # Tongue lies flat inside the base while closed, narrow at the root (front), wide at the tip (see tongue_out).
        *[part("Tongue" if i == 0 else f"Tongue{i + 1}", "ellipsoid", (width, thickness, length), (0, H - 0.3, z),
               PINK, None if i == 0 else "Tongue")
          for i, (width, thickness, length, z) in enumerate(TONGUE_SEGMENTS)],
        part("TongueGroove", "ellipsoid", (0.07, 0.05, 1.7), (0, H - 0.21, 0), TONGUE_GROOVE, "Tongue"),
        *shell,
        *arch("LidLining", 0, 2.4, 0.04, 0.17, WOOD_DARK),
        *[p for x, side in ((-1.3, "L"), (1.3, "R"))
          for p in arch(f"Rim{side}", x, 0.16, 0.24, 0.1, trim) + end_cap(f"Cap{side}", x)],
        *[p for x, side in ((-1.0, "L"), (1.0, "R")) for p in arch(f"Hoop{side}", x, 0.24, 0.24, 0.06, trim)],
        # Face: eyes bulge out of the lid just above the seam, teeth sit on the seam (the mouth).
        *mirrored("Eye", "ball", (0.74, 0.74, 0.74), (0.42, H + 0.55, -1.08), WHITE, "Lid"),
        *mirrored("Iris", "ball", (0.56, 0.56, 0.56), (0.42, H + 0.55, -1.24), iris, "Lid"),
        *mirrored("Pupil", "ball", (0.3, 0.3, 0.3), (0.42, H + 0.55, -1.4), PUPIL, "Lid"),
        *mirrored("Brow", "block", (0.55, 0.13, 0.16), (0.42, H + 1.04, -1.02), WOOD_DARK, "Lid", (0, 0, 14)),
        part("ShineL1", "ball", (0.2, 0.2, 0.2), (-0.32, H + 0.67, -1.46), WHITE, "Lid"),
        part("ShineL2", "ball", (0.1, 0.1, 0.1), (-0.54, H + 0.45, -1.45), WHITE, "Lid"),
        part("ShineR1", "ball", (0.2, 0.2, 0.2), (0.52, H + 0.67, -1.46), WHITE, "Lid"),
        part("ShineR2", "ball", (0.1, 0.1, 0.1), (0.3, H + 0.45, -1.45), WHITE, "Lid"),
        *mirrored("TeethOuter", "block", (0.26, 0.3, 0.1), (0.75, H - 0.06, -1.03), WHITE, "Lid"),
        *mirrored("TeethInner", "block", (0.26, 0.3, 0.1), (0.28, H - 0.06, -1.03), WHITE, "Lid"),
    ]
    if config["side"] == "ring":
        for x, side in ((-1, "L"), (1, "R")):
            parts += ring(f"Ring{side}", (x * 1.4, 0.8, 0), 0.22)
            parts.append(part(f"Stud{side}", "ball", (0.18, 0.18, 0.18), (x * 1.36, 1.06, 0), metal, "Base"))
    else:
        parts += [
            *mirrored("SidePlate", "cylinder", (0.12, 0.75, 0.75), (1.36, 0.7, 0), metal, "Base"),
            *gem("SideGemL", (-1.42, 0.82, 0), 0.8, config["side"], "Base", yaw=90, tilt=0, shine=True),
            *gem("SideGemR", (1.42, 0.82, 0), 0.8, config["side"], "Base", yaw=-90, tilt=0, shine=True),
        ]
    joints = [
        ("Base", "HumanoidRootPart", (0, 0.05, 0)),
        ("Lid", "Base", (0, H, 1.0)),
        ("Tongue", "Base", (0, H - 0.3, -0.85)),
    ]

    if tier == "Epic":
        parts += [
            *gem("DiamondC", (0, TOP + 0.4, 0.1), 0.9, LAVENDER, "Lid", tilt=0, cross=True, shine=True),
            *gem("DiamondL", (-0.75, TOP + 0.28, 0.15), 0.7, PINK, "Lid", yaw=20, tilt=0, cross=True, shine=True),
            *gem("DiamondR", (0.75, TOP + 0.28, 0.15), 0.7, BLUE, "Lid", yaw=-20, tilt=0, cross=True, shine=True),
        ]
    elif tier == "Legendary":
        parts += [
            part("CrownBase", "block", (1.5, 0.3, 0.9), (0, TOP, 0.1), WHITE, "Lid"),
            *gem("DiamondC", (0, TOP + 0.61, 0.1), 0.85, PINK, "Lid", tilt=0, cross=True, shine=True),
            *gem("DiamondL", (-0.55, TOP + 0.46, 0.1), 0.6, BLUE, "Lid", yaw=20, tilt=0, cross=True, shine=True),
            *gem("DiamondR", (0.55, TOP + 0.46, 0.1), 0.6, BLUE, "Lid", yaw=-20, tilt=0, cross=True, shine=True),
        ]
    elif tier == "Mythic":
        parts += [
            *mirrored("Cloud", "ellipsoid", (1.0, 0.5, 0.9), (0.55, TOP + 0.15, 0.05), WHITE, "Lid"),
            part("CloudC", "ellipsoid", (1.1, 0.6, 1.0), (0, TOP + 0.22, 0), WHITE, "Lid"),
            *[p for i, x in enumerate((-1.05, -0.63, -0.21, 0.21, 0.63, 1.05))
              for p in gem(f"Gem{i + 1}", (x, TOP + 0.55, 0.05), 0.5, RAINBOW[i], "Lid", tilt=10, shine=True)],
        ]
        # Wings fan out in the X-Y plane so they face the player; the first feather is the WingL / WingR bone.
        root_x, root_y, root_z = 1.45, H + 0.7, 0.5
        for i, (angle, length) in enumerate(FEATHERS):
            dx, dy = math.sin(math.radians(angle)), math.cos(math.radians(angle))
            feather, bone = ("Wing", None) if i == 0 else (f"Feather{i + 1}", "Wing{}")
            parts += [
                *mirrored(feather, "ellipsoid", (0.7, length, 0.14),
                          (root_x + dx * length / 2, root_y + dy * length / 2, root_z), WHITE, bone, (0, 0, -angle)),
                *mirrored(f"{feather}Pink", "ellipsoid", (0.4, length * 0.6, 0.18),
                          (root_x + dx * length * 0.4, root_y + dy * length * 0.4, root_z), PINK, "Wing{}", (0, 0, -angle)),
            ]
        joints += [("WingL", "Base", (-root_x, root_y, root_z)), ("WingR", "Base", (root_x, root_y, root_z))]

    joints = [(name, parent, tuple(v * k for v in pivot)) for name, parent, pivot in joints]
    return SimpleNamespace(PARTS=parts, JOINTS=joints, ANIMATIONS=ANIMATIONS)


def build_model(tier, data):
    parts = {}
    for name, shape, size, rest, color, _ in data.PARTS:
        part = build_part(name, shape, size, rest, color, anchored=name == "HumanoidRootPart")
        part.rest = rest
        parts[name] = part

    model = Item("Model", [
        xml_string("Name", f"TreasureChest_{tier}"),
        f'<Ref name="PrimaryPart">{parts["HumanoidRootPart"].ref}</Ref>',
        f'<token name="ModelStreamingMode">{MODEL_STREAMING_ATOMIC}</token>',
        xml_attributes({"Anim": "Idle", "Rarity": tier}),
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

    for script_name, source_path in (("ChestAnimator", HERE.parent / "PoliceGoose" / "GooseAnimator.client.luau"),
                                     ("ChestEffects", HERE / "ChestEffects.client.luau"),
                                     ("ChestSounds", HERE / "ChestSounds.client.luau")):
        model.add(Item("Script", [
            xml_string("Name", script_name),
            f'<token name="RunContext">{RUN_CONTEXT_CLIENT}</token>',
            f'<ProtectedString name="Source"><![CDATA[{source_path.read_text(encoding="utf-8")}]]></ProtectedString>',
        ]))
    return model


def main():
    for tier in TIERS:
        data = chest_data(tier)
        xml = ('<roblox xmlns:xmime="http://www.w3.org/2005/05/xmlmime" '
               'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
               'xsi:noNamespaceSchemaLocation="http://www.roblox.com/roblox.xsd" version="4">\n'
               "  <External>null</External>\n  <External>nil</External>\n"
               f"{build_model(tier, data).to_xml()}</roblox>\n")
        out = HERE / f"TreasureChest_{tier}.rbxmx"
        out.write_text(xml, encoding="utf-8")
        print(f"Wrote {out.name} ({len(data.PARTS)} parts, {len(data.JOINTS)} joints)")
        export(data, f"TreasureChest_{tier}", HERE / f"TreasureChest_{tier}.glb")


if __name__ == "__main__":
    main()
