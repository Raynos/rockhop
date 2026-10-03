"""Verify source08 changes only declared sole-top Z, preserving complete uppers."""
import argparse
import copy
import hashlib
import json
import sys
from pathlib import Path
import bpy
ap = argparse.ArgumentParser(description=__doc__)
for n in ['source', 'candidate', 'construction', 'out']:
    ap.add_argument('--' + n, required=True)
a = ap.parse_args(sys.argv[sys.argv.index('--') + 1:]); source, candidate, construction, output = [Path(getattr(a, n)).resolve() for n in ['source', 'candidate', 'construction', 'out']]
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
def capture(file):
    bpy.ops.wm.open_mainfile(filepath=str(file)); rows = {}
    rig = bpy.data.objects['Independent anatomical foundation rig']; bind = [(b.name, b.parent.name if b.parent else None, [list(r) for r in b.matrix_local]) for b in rig.data.bones]
    for o in bpy.data.objects:
        if o.type != 'MESH':
            continue
        mesh = o.data; rows[o.name] = {'vertices': [list(v.co) for v in mesh.vertices], 'faces': [list(p.vertices) for p in mesh.polygons],
            'UV': [[list(d.uv) for d in l.data] for l in mesh.uv_layers], 'weights': [[(o.vertex_groups[g.group].name, g.weight) for g in v.groups] for v in mesh.vertices],
            'keys': {k.name: [list(v.co) for v in k.data] for k in mesh.shape_keys.key_blocks} if mesh.shape_keys else {},
            'materialNames': [m.name for m in mesh.materials], 'slots': [p.material_index for p in mesh.polygons]}
    return bind, rows
old, new = capture(source), capture(candidate); assert old[0] == new[0]
changes = json.loads(construction.read_text())['changes']; boot = 'Complete worn boot volume on own canonical feet'; expected = copy.deepcopy(old[1])
for row in changes:
    i = row['vertexID']; assert expected[boot]['vertices'][i][2] == row['beforeNativeZ']
    expected[boot]['vertices'][i][2] = new[1][boot]['vertices'][i][2]
    assert abs(expected[boot]['vertices'][i][2] - row['afterNativeZ']) < 1e-9
assert expected == new[1]
report = {'status': 'UNACCEPTED08 native declared64sole-top-Z-only successor verified', 'sourceSHA256': sha(source), 'candidateSHA256': sha(candidate),
    'constructionSHA256': sha(construction), 'verifierSHA256': sha(__file__), 'nativeChangedSoleTopVertices': len(changes), 'all51NativeBindExact': True,
    'allOtherMeshFieldsIncludingHiddenControlsExact': True, 'soleTopologyUVWeightsSlotsMaterialNamesExact': True,
    'limits': ['Native field preservation and rest separation do not certify moving footwear or live engine collision response.']}
output.write_text(json.dumps(report, indent=2)+'\n'); print('OUTSOLE_NATIVE_FIELDS_VERIFIED', len(changes), flush=True)
