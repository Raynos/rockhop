"""Read-only comparison of independent authored exports and current riding rig."""
from pathlib import Path
import hashlib
import json
import struct
import numpy as np

REPO = Path('/Users/raynos/projects/games/rockhop')
TASK = Path('/Users/raynos/Documents/Codex/2026-10-01/task-3')
OUT = REPO/'docs/evidence/hero-remaster/one-rider-v2/garment-rebuild01/independent-v6-audit156'
OUT.mkdir(parents=True, exist_ok=True)
sha = lambda b: hashlib.sha256(b).hexdigest()

class GLB:
    def __init__(self, path):
        self.path = path
        self.raw = path.read_bytes()
        n = struct.unpack_from('<I', self.raw, 12)[0]
        self.j = json.loads(self.raw[20:20+n])
        self.bin = self.raw[28+n:]
    def acc(self, i):
        a = self.j['accessors'][i]
        assert 'sparse' not in a, 'Base attribute comparison requires nonsparse accessors'
        v = self.j['bufferViews'][a['bufferView']]
        widths = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}
        dt = np.dtype({5121: 'u1', 5123: '<u2', 5125: '<u4', 5126: '<f4'}[a['componentType']])
        width = widths[a['type']]
        offset = v.get('byteOffset', 0)+a.get('byteOffset', 0)
        return np.ndarray((a['count'], width), dtype=dt, buffer=self.bin, offset=offset,
            strides=(v.get('byteStride', dt.itemsize*width), dt.itemsize)).copy()
    def primitives(self):
        return [p for m in self.j['meshes'] for p in m['primitives']]
    def bone_nodes(self):
        return [self.j['nodes'][i] for i in self.j['skins'][0]['joints']]
    def rest_signature(self):
        return [{k: v for k, v in n.items() if k in ['matrix', 'translation', 'rotation', 'scale', 'children']}
            for n in self.bone_nodes()]

source = GLB(TASK/'deliverables/C19.glb')
variants = [GLB(TASK/'hoodie-repair02/deliverables/rider-foundation-v5.glb'),
            GLB(TASK/'hoodie-repair02/deliverables/rider-compression-v6.glb')]
roi = json.loads((REPO/'docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/played-surfaces11/framed04/source-roi.json').read_text())
rows = []
for g in variants:
    changes = []
    for i, (before, after) in enumerate(zip(source.primitives(), g.primitives())):
        fields = {}
        for name in ['POSITION', 'NORMAL', 'TEXCOORD_0', 'JOINTS_0', 'WEIGHTS_0']:
            A, B = source.acc(before['attributes'][name]), g.acc(after['attributes'][name])
            assert A.shape == B.shape
            fields[name] = {'exact': np.array_equal(A, B),
                'changedVertices': int(np.any(A != B, axis=1).sum()),
                'maximumAbsoluteDifference': float(np.abs(B.astype(float)-A.astype(float)).max())}
        P, Q = source.acc(before['attributes']['POSITION']), g.acc(after['attributes']['POSITION'])
        changes.append({'primitive': i, 'fields': fields,
            'maximumPositionDisplacementM': float(np.linalg.norm(Q-P, axis=1).max()),
            'indicesExact': np.array_equal(source.acc(before['indices']), g.acc(after['indices'])),
            'materialExact': before.get('material') == after.get('material'),
            'morphTargets': len(after.get('targets', []))})
    contacts = []
    for kind in ['hands', 'feet']:
        for probe in roi[kind]:
            i = 1 if kind == 'hands' else 0
            ids = probe['sourceVertices']
            A = source.primitives()[i]
            B = g.primitives()[i]
            fields = {k: np.array_equal(source.acc(A['attributes'][k])[ids], g.acc(B['attributes'][k])[ids])
                for k in ['POSITION', 'NORMAL', 'TEXCOORD_0', 'JOINTS_0', 'WEIGHTS_0']}
            contacts.append({'kind': kind, 'side': probe['side'], 'count': len(ids), 'exactBaseFields': fields})
    binds_equal = np.array_equal(source.acc(source.j['skins'][0]['inverseBindMatrices']),
        g.acc(g.j['skins'][0]['inverseBindMatrices']))
    rows.append({'file': str(g.path), 'sha256': sha(g.raw), 'bytes': len(g.raw),
        'canonical19SourceNamesExact': [n['name'] for n in source.bone_nodes()] == [n['name'] for n in g.bone_nodes()],
        'restBoneTRSChildrenExact': source.rest_signature() == g.rest_signature(),
        'inverseBindsExact': binds_equal, 'primitives': changes, 'sourceContactBaseFields': contacts,
        'materialsExact': source.j['materials'] == g.j['materials'],
        'sourceTexturesExact': source.j.get('textures') == g.j.get('textures'),
        'socketNodeNames': [n.get('name') for n in g.j['nodes'] if 'Socket' in n.get('name', '')],
        'clips': [a['name'] for a in g.j.get('animations', [])],
        'exportExperiment': g.j.get('asset', {}).get('extras', {})})

played_file = REPO/'docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/body-bind34/played/candidate/side/textured/report.json'
played = json.loads(played_file.read_text())
errors = []
for s in played['samples']:
    q = np.array(s['bones']['neck']['quaternion'])
    r = np.array(s['bones']['head']['quaternion'])
    errors.append(float(min(np.max(abs(q-r)), np.max(abs(q+r)))))
assert len(errors) == 480 and max(errors) < 1e-10
gate_file = TASK/'hoodie-repair02/qa-lane/results/v6-export-motion-manifest-gate.json'
gate = json.loads(gate_file.read_text())
from collections import Counter
scopes = {}
for scope in ['shoulder_underarm', 'hip', 'cuff_elbow']:
    values = [r['regions'][scope] for r in gate['rows']]
    scopes[scope] = {'samples': len(values), 'gates': dict(Counter(v['gate'] for v in values)),
        'maximumStrictCrossings': max(v['strict_transverse_crossings'] for v in values),
        'maximumEdgeRatioExcludingEdgesUnder2mm': max(v['edge_ge_2mm_max'] for v in values),
        'maximumFacesBelowQuarterArea': max(v['area_below_quarter'] for v in values)}
for g in [source]+variants:
    assert g.path.read_bytes() == g.raw
report = {'kind': 'Independent authored export comparison, no replacement or runtime adoption',
    'source': str(source.path), 'sourceSHA256': sha(source.raw), 'variants': rows,
    'actual34PlayedReportSHA256': sha(played_file.read_bytes()),
    'existingRuntimeNeckHeadWorldQuaternionMaximumDifference': max(errors),
    'existingRuntimeNeckHeadMatchedFrames': len(errors), 'finiteV6ExportGateSHA256': sha(gate_file.read_bytes()),
    'finiteV6ExportGates': scopes,
    'finding': 'V6 contains49 compression morph targets driven by a2second authored clip. It is not an arbitrary physics pose driver. Current actual34 already aims neck and head together; the independent authored posture fix does not prove a runtime bug.',
    'next': 'Evaluate v5 static shape/weights with explicit19bone/socket mapping in the existing physics driver. Keep v6 authored compression evidence separate until an explicit pose-feature morph driver and holdouts are validated.',
    'limits': ['No new in-engine render or quality pass for v5/v6.',
        'Authored sitting comparisons are not the full480 actual riding/landing/contact gate.',
        'Base-attribute equality does not prove animated or morphed contact equality.']}
(OUT/'report.json').write_text(json.dumps(report, indent=2)+'\n')
print(json.dumps({'variants': [(Path(r['file']).name, r['inverseBindsExact'], r['restBoneTRSChildrenExact']) for r in rows],
    'neckHeadActualDifference': max(errors), 'finiteGates': scopes}, indent=2))
