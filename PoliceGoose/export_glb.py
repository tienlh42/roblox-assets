"""Exports PoliceGoose.glb (mesh + all animations) from the data in build_police_goose.py.

Run: python export_glb.py   (standard library only)
Each Roblox Motor6D becomes a glTF node whose local transform is C0 * Transform; animations are
sampled at 30 fps with the same easing the in-game animator uses.
"""

import json
import math
import struct
from pathlib import Path

import build_police_goose as goose
from build_police_goose import CF, cf

HERE = Path(__file__).parent
FPS = 30
ELLIPSOID_SEGMENTS = (24, 14)
CYLINDER_SEGMENTS = 20


def quat_from_cf(c):
    (m00, m01, m02), (m10, m11, m12), (m20, m21, m22) = c.rot
    trace = m00 + m11 + m22
    if trace > 0:
        s = math.sqrt(trace + 1) * 2
        q = ((m21 - m12) / s, (m02 - m20) / s, (m10 - m01) / s, s / 4)
    elif m00 > m11 and m00 > m22:
        s = math.sqrt(1 + m00 - m11 - m22) * 2
        q = (s / 4, (m01 + m10) / s, (m02 + m20) / s, (m21 - m12) / s)
    elif m11 > m22:
        s = math.sqrt(1 + m11 - m00 - m22) * 2
        q = ((m01 + m10) / s, s / 4, (m12 + m21) / s, (m02 - m20) / s)
    else:
        s = math.sqrt(1 + m22 - m00 - m11) * 2
        q = ((m02 + m20) / s, (m12 + m21) / s, s / 4, (m10 - m01) / s)
    return q


def cf_from_quat(pos, q):
    x, y, z, w = q
    return CF(pos, (
        (1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)),
        (2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)),
        (2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)),
    ))


def slerp(a, b, t):
    dot = sum(x * y for x, y in zip(a, b))
    if dot < 0:
        b, dot = tuple(-v for v in b), -dot
    if dot > 0.9995:
        q = tuple(x + (y - x) * t for x, y in zip(a, b))
    else:
        theta = math.acos(dot)
        wa, wb = math.sin((1 - t) * theta) / math.sin(theta), math.sin(t * theta) / math.sin(theta)
        q = tuple(wa * x + wb * y for x, y in zip(a, b))
    length = math.sqrt(sum(v * v for v in q))
    return tuple(v / length for v in q)


def lerp_cf(a, b, t):
    pos = tuple(x + (y - x) * t for x, y in zip(a.pos, b.pos))
    return cf_from_quat(pos, slerp(quat_from_cf(a), quat_from_cf(b), t))


def ease(style, t):
    if style == "Linear":
        return t
    return 4 * t ** 3 if t < 0.5 else 1 - (-2 * t + 2) ** 3 / 2


def sample(keyframes, easing, joint, t):
    for (t0, frame0), (t1, frame1) in zip(keyframes, keyframes[1:]):
        if t < t1:
            alpha = ease(easing, max(t - t0, 0) / (t1 - t0))
            return lerp_cf(frame0.get(joint, CF()), frame1.get(joint, CF()), alpha)
    return keyframes[-1][1].get(joint, CF())


def srgb_to_linear(rgb):
    def channel(c):
        c /= 255
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    return [channel(c) for c in rgb] + [1.0]


class MeshBuilder:
    def __init__(self):
        self.positions, self.normals, self.indices = [], [], []

    def vertex(self, p, n):
        self.positions.append(p)
        self.normals.append(n)
        return len(self.positions) - 1

    def triangle(self, a, b, c):
        """Flips winding so the face is counter-clockwise when seen from outside (along the normals)."""
        pa, pb, pc = self.positions[a], self.positions[b], self.positions[c]
        e1 = [pb[i] - pa[i] for i in range(3)]
        e2 = [pc[i] - pa[i] for i in range(3)]
        cross = (e1[1] * e2[2] - e1[2] * e2[1], e1[2] * e2[0] - e1[0] * e2[2], e1[0] * e2[1] - e1[1] * e2[0])
        normal = [sum(self.normals[v][i] for v in (a, b, c)) for i in range(3)]
        if sum(cross[i] * normal[i] for i in range(3)) < 0:
            b, c = c, b
        self.indices += [a, b, c]

    def quad(self, corners, normal):
        v = [self.vertex(p, normal) for p in corners]
        self.triangle(v[0], v[1], v[2])
        self.triangle(v[0], v[2], v[3])


def normalize(v):
    length = math.sqrt(sum(c * c for c in v)) or 1
    return tuple(c / length for c in v)


def ellipsoid(mesh, size):
    sx, sy, sz = (s / 2 for s in size)
    rings, segments = ELLIPSOID_SEGMENTS[1], ELLIPSOID_SEGMENTS[0]
    grid = []
    for i in range(rings + 1):
        phi = math.pi * i / rings
        row = []
        for j in range(segments + 1):
            theta = 2 * math.pi * j / segments
            u = (math.sin(phi) * math.cos(theta), math.cos(phi), math.sin(phi) * math.sin(theta))
            p = (u[0] * sx, u[1] * sy, u[2] * sz)
            row.append(mesh.vertex(p, normalize((u[0] / sx, u[1] / sy, u[2] / sz))))
        grid.append(row)
    for i in range(rings):
        for j in range(segments):
            a, b, c, d = grid[i][j], grid[i][j + 1], grid[i + 1][j + 1], grid[i + 1][j]
            if i > 0:
                mesh.triangle(a, b, c)
            if i < rings - 1:
                mesh.triangle(a, c, d)


def box(mesh, size):
    x, y, z = (s / 2 for s in size)
    mesh.quad([(x, -y, z), (x, -y, -z), (x, y, -z), (x, y, z)], (1, 0, 0))
    mesh.quad([(-x, -y, -z), (-x, -y, z), (-x, y, z), (-x, y, -z)], (-1, 0, 0))
    mesh.quad([(-x, y, z), (x, y, z), (x, y, -z), (-x, y, -z)], (0, 1, 0))
    mesh.quad([(-x, -y, -z), (x, -y, -z), (x, -y, z), (-x, -y, z)], (0, -1, 0))
    mesh.quad([(-x, -y, z), (x, -y, z), (x, y, z), (-x, y, z)], (0, 0, 1))
    mesh.quad([(x, y, -z), (-x, y, -z), (-x, -y, -z), (x, -y, -z)], (0, 0, -1))


def wedge(mesh, size):
    """Roblox WedgePart: full height at the back (+Z), sloping down to the front bottom edge."""
    x, y, z = (s / 2 for s in size)
    slope = normalize((0, 2 * z, -2 * y))
    mesh.quad([(-x, -y, z), (x, -y, z), (x, y, z), (-x, y, z)], (0, 0, 1))
    mesh.quad([(-x, -y, -z), (x, -y, -z), (x, -y, z), (-x, -y, z)], (0, -1, 0))
    mesh.quad([(-x, -y, -z), (x, -y, -z), (x, y, z), (-x, y, z)], slope)
    for sx in (-x, x):
        a, b, c = (mesh.vertex(p, (math.copysign(1, sx), 0, 0)) for p in ((sx, -y, -z), (sx, -y, z), (sx, y, z)))
        mesh.triangle(a, b, c)


def cylinder(mesh, size):
    """Roblox cylinder: axis along local X, diameter = min(Y, Z)."""
    half, radius = size[0] / 2, min(size[1], size[2]) / 2
    ring = [(math.cos(2 * math.pi * i / CYLINDER_SEGMENTS), math.sin(2 * math.pi * i / CYLINDER_SEGMENTS))
            for i in range(CYLINDER_SEGMENTS)]
    for i, (c0, s0) in enumerate(ring):
        c1, s1 = ring[(i + 1) % CYLINDER_SEGMENTS]
        v = [mesh.vertex((x, c * radius, s * radius), (0, c, s))
             for x, c, s in ((-half, c0, s0), (half, c0, s0), (half, c1, s1), (-half, c1, s1))]
        mesh.triangle(v[0], v[1], v[2])
        mesh.triangle(v[0], v[2], v[3])
    for x in (-half, half):
        normal = (math.copysign(1, x), 0, 0)
        center = mesh.vertex((x, 0, 0), normal)
        rim = [mesh.vertex((x, c * radius, s * radius), normal) for c, s in ring]
        for i in range(CYLINDER_SEGMENTS):
            mesh.triangle(center, rim[i], rim[(i + 1) % CYLINDER_SEGMENTS])


def build_shape(shape, size):
    mesh = MeshBuilder()
    if shape in ("ellipsoid", "ball"):
        ellipsoid(mesh, size if shape == "ellipsoid" else (min(size),) * 3)
    elif shape == "cylinder":
        cylinder(mesh, size)
    elif shape == "wedge":
        wedge(mesh, size)
    else:
        box(mesh, size)
    return mesh


class GlbWriter:
    def __init__(self):
        self.bin = bytearray()
        self.gltf = {"asset": {"version": "2.0", "generator": "PoliceGoose export_glb.py"},
                     "scene": 0, "scenes": [{"nodes": [0]}], "nodes": [], "meshes": [], "materials": [],
                     "accessors": [], "bufferViews": [], "animations": []}
        self.material_ids = {}

    def view(self, data, target=None):
        while len(self.bin) % 4:
            self.bin.append(0)
        view = {"buffer": 0, "byteOffset": len(self.bin), "byteLength": len(data)}
        if target:
            view["target"] = target
        self.bin += data
        self.gltf["bufferViews"].append(view)
        return len(self.gltf["bufferViews"]) - 1

    def accessor(self, values, kind, component=5126, target=None, minmax=False):
        width = {"SCALAR": 1, "VEC3": 3, "VEC4": 4}[kind]
        flat = [c for v in values for c in (v if width > 1 else (v,))]
        fmt = "<%d%s" % (len(flat), "f" if component == 5126 else "H")
        accessor = {"bufferView": self.view(struct.pack(fmt, *flat), target), "componentType": component,
                    "count": len(values), "type": kind}
        if minmax:
            columns = list(zip(*values)) if width > 1 else [values]
            accessor["min"] = [min(c) for c in columns]
            accessor["max"] = [max(c) for c in columns]
        self.gltf["accessors"].append(accessor)
        return len(self.gltf["accessors"]) - 1

    def material(self, color):
        if color not in self.material_ids:
            metal = color in (goose.SILVER, goose.GOLD)
            pbr = {"baseColorFactor": srgb_to_linear(color), "metallicFactor": 0.6 if metal else 0.0,
                   "roughnessFactor": 0.35 if metal else 0.7}
            self.gltf["materials"].append({"pbrMetallicRoughness": pbr})
            self.material_ids[color] = len(self.gltf["materials"]) - 1
        return self.material_ids[color]

    def primitive(self, mesh, material):
        attributes = {"POSITION": self.accessor(mesh.positions, "VEC3", target=34962, minmax=True),
                      "NORMAL": self.accessor(mesh.normals, "VEC3", target=34962)}
        return {"attributes": attributes,
                "indices": self.accessor(mesh.indices, "SCALAR", component=5123, target=34963),
                "material": material}

    def add_mesh(self, name, primitives):
        self.gltf["meshes"].append({"name": name, "primitives": primitives})
        return len(self.gltf["meshes"]) - 1

    def add_node(self, name, transform=None, mesh=None, parent=None):
        node = {"name": name}
        if transform is not None:
            node["translation"] = list(transform.pos)
            node["rotation"] = list(quat_from_cf(transform))
        if mesh is not None:
            node["mesh"] = mesh
        self.gltf["nodes"].append(node)
        index = len(self.gltf["nodes"]) - 1
        if parent is not None:
            self.gltf["nodes"][parent].setdefault("children", []).append(index)
        return index

    def write(self, path):
        while len(self.bin) % 4:
            self.bin.append(0)
        self.gltf["buffers"] = [{"byteLength": len(self.bin)}]
        js = json.dumps(self.gltf, separators=(",", ":")).encode()
        js += b" " * (-len(js) % 4)
        total = 12 + 8 + len(js) + 8 + len(self.bin)
        data = struct.pack("<III", 0x46546C67, 2, total)
        data += struct.pack("<II", len(js), 0x4E4F534A) + js
        data += struct.pack("<II", len(self.bin), 0x004E4942) + bytes(self.bin)
        path.write_bytes(data)


def export(data, model_name, out):
    """data needs PARTS, JOINTS and ANIMATIONS in the same format as build_police_goose."""
    glb = GlbWriter()
    parts = {p[0]: p for p in data.PARTS}
    joints = {j[0]: j for j in data.JOINTS}
    children = {}
    for part1, part0, _ in data.JOINTS:
        children.setdefault(part0, []).append(part1)
    decor = {}
    for name, *_, bone in data.PARTS:
        if bone:
            decor.setdefault(bone, []).append(name)

    # Roblox faces -Z, glTF convention is +Z forward.
    root = glb.add_node(model_name, cf(ry=180))
    joint_nodes = {}
    c0s = {}

    def part_mesh(name):
        _, shape, size, _, color, _ = parts[name]
        return glb.add_mesh(name, [glb.primitive(build_shape(shape, size), glb.material(color))])

    def add_decor(name, rest, parent_node):
        """Parts welded to name, and parts welded to those (a hub with a ring of blocks, for example)."""
        for child in decor.get(name, []):
            node = glb.add_node(child, rest.inverse() * parts[child][3], mesh=part_mesh(child), parent=parent_node)
            add_decor(child, parts[child][3], node)

    def add_bone(name, parent_node):
        _, _, _, rest, _, _ = parts[name]
        if name == "HumanoidRootPart":
            bone_node = glb.add_node(name, rest, parent=parent_node)
        else:
            _, part0, pivot = joints[name]
            c0 = parts[part0][3].inverse() * CF(pivot)
            c0s[name] = c0
            joint_nodes[name] = glb.add_node(name + "Joint", c0, parent=parent_node)
            c1 = rest.inverse() * CF(pivot)
            bone_node = glb.add_node(name, c1.inverse(), mesh=part_mesh(name), parent=joint_nodes[name])
        add_decor(name, rest, bone_node)
        for child in children.get(name, []):
            add_bone(child, bone_node)

    add_bone("HumanoidRootPart", root)

    for anim_name, (looped, _, easing, keyframes) in data.ANIMATIONS.items():
        length = keyframes[-1][0]
        times = [min(i / FPS, length) for i in range(math.ceil(length * FPS) + 1)]
        time_accessor = glb.accessor(times, "SCALAR", minmax=True)
        samplers, channels = [], []
        for joint, node in joint_nodes.items():
            local = [c0s[joint] * sample(keyframes, easing, joint, t) for t in times]
            rotations = [quat_from_cf(local[0])]
            for c in local[1:]:
                q = quat_from_cf(c)
                # Keep consecutive quaternions in the same hemisphere so viewers don't spin the long way.
                if sum(a * b for a, b in zip(q, rotations[-1])) < 0:
                    q = tuple(-v for v in q)
                rotations.append(q)
            for path, values, kind in (("translation", [c.pos for c in local], "VEC3"),
                                       ("rotation", rotations, "VEC4")):
                samplers.append({"input": time_accessor, "output": glb.accessor(values, kind), "interpolation": "LINEAR"})
                channels.append({"sampler": len(samplers) - 1, "target": {"node": node, "path": path}})
        glb.gltf["animations"].append({"name": anim_name, "samplers": samplers, "channels": channels})

    glb.write(out)
    print(f"Wrote {out} ({len(glb.gltf['animations'])} animations, {len(glb.bin) // 1024} KB binary)")


if __name__ == "__main__":
    export(goose, "PoliceGoose", HERE / "PoliceGoose.glb")
