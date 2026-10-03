"""Verify original rig/pattern/corrective data carried into appearance assembly."""
import argparse
import hashlib
import json
import sys
from pathlib import Path
import bpy

ap = argparse.ArgumentParser(description=__doc__)
for n in ['source', 'candidate', 'out']:
    ap.add_argument('--' + n, required=True)
a = ap.parse_args(sys.argv[sys.argv.index('--') + 1:])
source, candidate, out = [Path(getattr(a, n)).resolve() for n in ['source', 'candidate', 'out']]
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
def capture(file):
    bpy.ops.wm.open_mainfile(filepath=str(file))
    rig = bpy.data.objects['Independent anatomical foundation rig']
    bind = [{'name': b.name, 'parent': b.parent.name if b.parent else None,
        'matrix': [list(r) for r in b.matrix_local], 'deform': b.use_deform} for b in rig.data.bones]
    rows = {}
    for name in ['Canonical anatomical body, baked adult hm08', 'Separate fitted sweatshirt control, hood not constructed', 'Separate fitted native trousers control']:
        o = bpy.data.objects[name]
        rows[name] = {'vertices': [list(v.co) for v in o.data.vertices], 'polygons': [list(p.vertices) for p in o.data.polygons],
            'uv': [[list(d.uv) for d in l.data] for l in o.data.uv_layers],
            'weights': [[(o.vertex_groups[g.group].name, g.weight) for g in v.groups] for v in o.data.vertices],
            'shapes': {k.name: [list(v.co) for v in k.data] for k in o.data.shape_keys.key_blocks} if o.data.shape_keys else None}
    return bind, rows
before = capture(source); after = capture(candidate)
assert before == after
report = {'status': 'Original native rig, body and garment basis/UV/weights/topology/local morphs unchanged in assembled master',
    'sourceSHA256': sha(source), 'candidateSHA256': sha(candidate), 'recipeSHA256': sha(__file__),
    'boneCount': len(before[0]), 'deformCount': sum(b['deform'] for b in before[0]),
    'preservedMeshes': {k: {'vertices': len(v['vertices']), 'polygons': len(v['polygons']),
        'shapeNames': list(v['shapes'] or {}), 'dataSHA256': hashlib.sha256(json.dumps(v).encode()).hexdigest()} for k, v in before[1].items()},
    'limits': ['Visible body head-interface derivative and new head/hood/accessory objects are explicit additions, not original-body preservation claims.',
        'Export parity, whole-rider fit, moving appearance and engine/device acceptance remain pending.']}
out.write_text(json.dumps(report, indent=2) + '\n'); print('APPEARANCE_SOURCE_PRESERVED', report['boneCount'], flush=True)
