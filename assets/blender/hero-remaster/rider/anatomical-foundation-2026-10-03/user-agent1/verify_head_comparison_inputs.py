"""Verify identical target, stored pose and contact convention for rest94."""
import argparse
import hashlib
import json
import sys
from pathlib import Path

import bpy
import numpy as np

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--contacts", required=True)
parser.add_argument("--out", required=True)
args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:])
contacts = Path(args.contacts).resolve()
out = Path(args.out).resolve()
assert not out.exists()
sha = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
record = json.loads(contacts.read_text())
paths = {key: Path(path) for key, path in zip(["flat", "smooth", "four"], record["pins"])}
assert all(sha(path) == record["pins"][str(path)] for path in paths.values())
helper_path = Path(__file__).with_name("verify_extended_protected_data.py")
code = helper_path.read_text()
helpers = dict(bpy=bpy, np=np, hashlib=hashlib, json=json)
exec(compile(code[code.index("def value("):code.index("before=snapshot(original)")], str(helper_path), "exec"), helpers)
states = []
arrays = []
for key, path in paths.items():
    bpy.ops.wm.open_mainfile(filepath=str(path))
    head = bpy.data.objects["Protected textured head above hidden neck interface"]
    rig = bpy.data.objects["Independent anatomical foundation rig"]
    head.hide_set(False)
    rig.hide_set(False)
    bpy.context.view_layer.update()
    state = {
        "headObject": helpers["object_state"](head),
        "headMesh": helpers["mesh_extra"](head.data),
        "headPositions": helpers["array_digest"](head.data.vertices, "co", 3),
        "headPolygons": [list(p.vertices) for p in head.data.polygons],
        "headWeights": [[[head.vertex_groups[g.group].name, float(g.weight)] for g in v.groups] for v in head.data.vertices],
        "rigObject": helpers["object_state"](rig), "rigData": helpers["properties"](rig.data),
        "storedPose": {b.name: {"matrix": helpers["value"](b.matrix), "basis": helpers["value"](b.matrix_basis),
                               "properties": helpers["properties"](b), "constraints": [helpers["properties"](c) for c in b.constraints]}
                       for b in rig.pose.bones},
    }
    evaluated = head.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = evaluated.to_mesh()
    mesh.calc_loop_triangles()
    xyz = np.array([evaluated.matrix_world @ v.co for v in mesh.vertices])
    tri = np.array([t.vertices[:] for t in mesh.loop_triangles])
    evaluated.to_mesh_clear()
    states.append(state)
    arrays.append((xyz, tri))
assert states[0] == states[1] == states[2]
assert len(states[0]["storedPose"]) == 51
assert all(np.array_equal(arrays[0][i], values[i]) for values in arrays[1:] for i in range(2))
pairs = [
    {(w["garmentTriangle"], w["headTriangle"]) for w in record["variants"][key]["allPairs"]}
    for key in paths
]
result = {
    "status": "UNACCEPTED rest94 comparison has identical protected target and stored51pose",
    "pins": {str(path): sha(path) for path in paths.values()},
    "contactsSHA256": sha(contacts), "recipeSHA256": sha(__file__), "helperSHA256": sha(helper_path),
    "rawHeadMeshWeightsModifiersTransformsExact": True,
    "storedRigAnd51PoseExact": True, "evaluatedHeadWorldPositionsTrianglesExact": True,
    "targetVertices": len(arrays[0][0]), "targetTriangles": len(arrays[0][1]),
    "protectedSnapshotSHA256": hashlib.sha256(json.dumps(states[0], sort_keys=True).encode()).hexdigest(),
    "evaluatedHeadWorldPositionsSHA256": hashlib.sha256(arrays[0][0].tobytes()).hexdigest(),
    "evaluatedHeadTrianglesSHA256": hashlib.sha256(arrays[0][1].tobytes()).hexdigest(),
    "flatVsSmoothExactContactPairSet": pairs[0] == pairs[1],
    "flatVsFourExactContactPairSet": pairs[0] == pairs[2],
    "poseConvention": "Same original stored51pose and rig for allthree native files; no driver applied and no pose/rig edits.",
    "unitsAndAxes": "Native metres,+Xforward/+Zup/-Yleft,file-frameX0.6499999761581421; intersections evaluated in shared actual world frame, translation removed exactly once for native witness coordinates.",
    "contactConvention": "Same BVHTree.overlap on actual evaluated Float32 geometry with calc_loop_triangles; every pair additionally tested via six Float64 finite edge/triangle segment tests. No face mask,alpha/culling filtering,target substitution or contact waiver.",
    "limits": [
        "Input equality and garment-contact scope only; no body/seam QA or visible-breakthrough verdict. Parentplayed93reported no gross panel holes while motion/contact qualification remains failed.",
        "No source save,newcapture,geometry/head/body/weight/rig edit,retry,engine admission,Libraryupload/promotion/publication.",
    ],
}
assert result["pins"] == {p: sha(p) for p in result["pins"]}
out.write_text(json.dumps(result, indent=2) + "\n")
print("HEAD_COMPARISON_INPUTS_EXACT", result["targetVertices"], result["targetTriangles"], pairs[0] == pairs[2], flush=True)
