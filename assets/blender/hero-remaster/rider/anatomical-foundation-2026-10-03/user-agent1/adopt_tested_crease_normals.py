"""Checkpoint only the parent's tested source24 crease-normal choice."""
import argparse
import collections
import hashlib
import json
import sys
from pathlib import Path

import bpy
import numpy as np

parser = argparse.ArgumentParser(description=__doc__)
for name in ["source", "display-review", "display-field", "out"]:
    parser.add_argument("--" + name, required=True)
args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:])
source, display_review, display_field, out = [
    Path(getattr(args, name.replace("-", "_"))).resolve()
    for name in ["source", "display-review", "display-field", "out"]
]
sha = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
review = json.loads(display_review.read_text())
assert sha(source) == review["nativeCandidateSHA256"]
assert sha(display_field) == review["normalDisplayFieldSHA256"]
field = np.load(display_field)
extended = Path(__file__).with_name("verify_extended_protected_data.py")
definitions = extended.read_text()
helpers = dict(bpy=bpy, np=np, hashlib=hashlib, json=json)
exec(compile(definitions[definitions.index("def value("):definitions.index("before=snapshot(original)")], str(extended), "exec"), helpers)
pins = {str(p): sha(p) for p in [source, display_review, display_field, extended]}
out.mkdir(parents=True, exist_ok=True)
native = out / "crease-normal-candidate.blend"
assert not native.exists() and not (out / "report.json").exists()
names = [
    "Canonical anatomical body, baked adult hm08",
    "Canonical body with hidden head interface",
    "Full native diagnostic body",
    "Protected textured head above hidden neck interface",
    "Protected coherent cheek patch",
    "Protected mustard hood on own rig",
    "Opaque boxer fitting garment",
]
rig_name = "Independent anatomical foundation rig"
object_name = "Actual selected donor, compact interior flow, unaccepted"
def protected():
    objects = {}
    for name in names:
        obj = bpy.data.objects[name]
        objects[name] = {
            "object": helpers["object_state"](obj),
            "mesh": helpers["mesh_extra"](obj.data),
            "positions": helpers["array_digest"](obj.data.vertices, "co", 3),
            "polygons": [list(p.vertices) for p in obj.data.polygons],
            "materials": [m.name if m else None for m in obj.data.materials],
        }
    rig = bpy.data.objects[rig_name]
    return {
        "objects": objects, "rigObject": helpers["object_state"](rig),
        "rigData": helpers["properties"](rig.data),
        "poseBones": {
            b.name: {
                "matrix": helpers["value"](b.matrix),
                "basis": helpers["value"](b.matrix_basis),
                "properties": helpers["properties"](b),
                "constraints": [helpers["properties"](c) for c in b.constraints],
            } for b in rig.pose.bones
        },
    }
def buffers(mesh):
    mesh.calc_loop_triangles()
    return {
        "nativePositions": np.array([v.co[:] for v in mesh.vertices]),
        "triangles": np.array([t.vertices[:] for t in mesh.loop_triangles]),
        "UVs": np.array([uv.uv[:] for uv in mesh.uv_layers.active.data]),
        "normals": np.array([n.vector[:] for n in mesh.corner_normals]),
    }
def assert_buffers(mesh, treatment):
    measured = buffers(mesh)
    for key in ["nativePositions", "triangles", "UVs"]:
        assert np.array_equal(measured[key], field[key]), key
    assert np.array_equal(measured["normals"], field[treatment]), treatment
    return measured

bpy.ops.wm.open_mainfile(filepath=str(source))
before = protected()
assert len(before["poseBones"]) == 51
obj = bpy.data.objects[object_name]
mesh = obj.data
assert not mesh.has_custom_normals
assert sum(p.use_smooth for p in mesh.polygons) == 0
assert_buffers(mesh, "flatCornerNormals")
cycles = [list(p.vertices) for p in mesh.polygons]
materials = tuple(mesh.materials)
object_state = helpers["object_state"](obj)
adjacency = collections.defaultdict(list)
for polygon in mesh.polygons:
    vertices = list(polygon.vertices)
    for i in range(len(vertices)):
        edge = tuple(sorted((vertices[i], vertices[(i + 1) % len(vertices)])))
        adjacency[edge].append(polygon.index)
face_normals = np.array([p.normal[:] for p in mesh.polygons])
sharp = {
    edge for edge, adjacent in adjacency.items()
    if len(adjacent) == 2 and
    np.degrees(np.arccos(np.clip(face_normals[adjacent[0]] @ face_normals[adjacent[1]], -1, 1))) > 30
}
assert len(sharp) == 2671
mesh.polygons.foreach_set("use_smooth", np.ones(len(mesh.polygons), dtype=np.bool_))
for edge in mesh.edges:
    edge.use_edge_sharp = tuple(sorted(edge.vertices)) in sharp
mesh.update()
assert_buffers(mesh, "smooth30CornerNormals")
assert [list(p.vertices) for p in mesh.polygons] == cycles
assert tuple(mesh.materials) == materials
assert helpers["object_state"](obj) == object_state
assert protected() == before
bpy.ops.wm.save_as_mainfile(filepath=str(native))
candidate_sha = sha(native)
# Reopen the actual saved native candidate; no display-copy substitute.
bpy.ops.wm.open_mainfile(filepath=str(native))
obj = bpy.data.objects[object_name]
mesh = obj.data
assert_buffers(mesh, "smooth30CornerNormals")
assert [list(p.vertices) for p in mesh.polygons] == cycles
assert [m.name for m in mesh.materials] == [m.name for m in materials]
assert helpers["object_state"](obj) == object_state
assert protected() == before
assert not mesh.has_custom_normals
assert sum(p.use_smooth for p in mesh.polygons) == 19878
assert sum(e.use_edge_sharp for e in mesh.edges) == 2671
assert pins == {path: sha(path) for path in pins}
protected_sha = hashlib.sha256(json.dumps(before, sort_keys=True).encode()).hexdigest()
report = {
    "status": "UNACCEPTED native candidate with parent-selected tested30-degree normals",
    "pins": pins, "recipeSHA256": sha(__file__),
    "candidate": str(native), "candidateSHA256": candidate_sha,
    "actualObject": object_name, "vertices": len(mesh.vertices),
    "triangles": len(mesh.loop_triangles), "smoothFaces": 19878, "sharpEdges": 2671,
    "hasCustomNormals": False, "cornerNormalsExactToTested88Buffer": True,
    "positionsTrianglesPolygonCyclesUVExactToSource24": True,
    "materialIdentityBeforeSaveAndNamesAfterReopenExact": True,
    "actualObjectTransformsAndModifiersExact": True,
    "protectedMeshesExact": 7, "protectedPoseBonesExact": 51,
    "protectedSnapshotSHA256": protected_sha, "savedNativeReopenVerified": True,
    "authorization": "Root selected TESTED30-degree crease-preserving treatment for THISsource24 after playing normals88; bridge01a1054f-988a-710f-b72e-417ac96ba032 relayed decision. Shading choice only, not art/fit/M0-M5.",
    "limits": [
        "Source24 and flat controls retained byte-exact; no geometry/UV/PBR shrink/smoothing/recolor. Body89 flat review remains existing evidence, not recaptured.",
        "Native smooth/sharp flags produce the exact tested corner-normal buffer. Actual glTF export and engine consumption of those normals remain unverified until qualified handoff.",
        "Native weights/rig/motion unchanged and not qualified. All24 historical coverage misses, inflated silhouette/wearing ease, appearance andM0-M5/mobile remain open; parent body89 review pending.",
        "No broad construction/new body/inference/worker/Library upload/player promotion/publication. Native master stays in ignored owned asset namespace.",
    ],
}
(out / "report.json").write_text(json.dumps(report, indent=2) + "\n")
print("TESTED_CREASE_NORMALS_NATIVE_PASS", candidate_sha, len(mesh.corner_normals), flush=True)
