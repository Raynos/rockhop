"""Cheap source/mesh-edit preflight; does not import Blender or execute a bake."""
import ast
import hashlib
import json
from pathlib import Path
import numpy as np
from region_geometry import duplicate_inset_extrude, seam_edge_geometry, boundary_edges

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
EVIDENCE = ROOT / 'docs/evidence/rider-rebuild/production-gloves02'
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
records = json.loads((HERE / 'inputs.json').read_text())
for key, record in records.items():
    assert sha(ROOT / record['path']) == record['sha256'], ('Changed pin', key)
for path in HERE.glob('*.py'): ast.parse(path.read_text(), filename=str(path))
regions = json.loads((HERE / 'face-regions.json').read_text())
body = np.load(ROOT / records['nativeArrays']['path'])
names = body['jointNames'].tolist()
receipts = {}
for side in ('R', 'L'):
    hand = np.load(ROOT / records['hand' + side]['path'])
    v, f = hand['vertices'], hand['faces']
    head = lambda name: body['jointHeads'][names.index(name + '.' + side)]
    wrist = head('DEF-hand'); forward = head('DEF-f_middle.01') - wrist; forward /= np.linalg.norm(forward)
    radial = head('DEF-f_index.01') - head('DEF-f_pinky.01'); radial -= forward * np.dot(radial, forward); radial /= np.linalg.norm(radial)
    dorsal = np.cross(radial, forward) * (1 if side == 'R' else -1)
    n = np.zeros_like(v); area = np.cross(v[f[:, 1]] - v[f[:, 0]], v[f[:, 2]] - v[f[:, 0]])
    for corner in range(3): np.add.at(n, f[:, corner], area)
    n /= np.linalg.norm(n, axis=1)[:, None]
    back = np.clip(n @ dorsal, 0, 1); palm = np.clip(-n @ dorsal, 0, 1)
    ease = (.0016 + back * .0018 + palm * .0007) * (1 - .20 * np.clip(((v - wrist) @ forward - .15) / .05, 0, 1))
    scaffold = v + n * ease[:, None]
    total_vertices, total_faces = len(v), len(f)
    all_fields = [hand['fourCoefficients']]
    patch_receipts = []
    for spec in regions['sides'][side]['regions']:
        selected = f[spec['faceIds']]
        edge_owners = {}
        for fi, face in enumerate(selected):
            for a, b in zip(face, np.roll(face, -1)):
                edge_owners.setdefault(tuple(sorted((int(a), int(b)))), []).append(fi)
        adjacency = [set() for _ in selected]
        for owners in edge_owners.values():
            for fi in owners: adjacency[fi].update(set(owners) - {fi})
        visited = {0}; queue = [0]
        while queue:
            fi = queue.pop()
            for other in adjacency[fi] - visited: visited.add(other); queue.append(other)
        assert len(visited) == len(selected), (side, spec['name'], 'Disconnected patch')
        vv, ff, four, full, seams, receipt = duplicate_inset_extrude(scaffold, n, hand['fourCoefficients'], hand['fullCoefficients'], f, spec)
        assert np.isfinite(vv).all()
        assert np.max(abs(np.asarray(four).sum(1) - 1)) < 1e-10
        assert np.max(abs(np.asarray(full).sum(1) - 1)) < 1e-10
        assert np.min(np.asarray(four)) >= 0 and np.min(np.asarray(full)) >= 0
        # Triangle/quad geometry must be real and finite, including sidewalls.
        positions = np.asarray(vv)
        min_area = min(float(np.linalg.norm(np.cross(positions[face[1]] - positions[face[0]], positions[face[2]] - positions[face[0]]))) for face in ff)
        assert min_area > 1e-14, (side, spec['name'], 'Collapsed face', min_area)
        all_fields.append(np.asarray(four))
        count_v, count_f = len(vv), len(ff)
        if not spec['ribCount']:
            sv, sf, sw, sfull = seam_edge_geometry(seams, .00023, dorsal)
            assert np.isfinite(sv).all()
            all_fields.append(np.asarray(sw))
            count_v += len(sv); count_f += len(sf)
        total_vertices += count_v; total_faces += count_f
        patch_receipts.append({'name': spec['name'], 'connectedActualSourceFaces': len(selected),
                               'generatedVertices': count_v, 'generatedPolygons': count_f,
                               'minimumDoubleFaceAreaMeters2': min_area})
    cuff = [(scaffold[a], scaffold[b], hand['fourCoefficients'][a], hand['fourCoefficients'][b], hand['fullCoefficients'][a], hand['fullCoefficients'][b]) for a, b in hand['cuffBoundaryEdges']]
    cv, cf, cw, _ = seam_edge_geometry(cuff, .00115, dorsal)
    all_fields.append(np.asarray(cw))
    inherited = np.vstack(all_fields)
    order = np.argsort(-inherited, axis=1, kind='stable')[:, :4]
    conditioned = np.zeros_like(inherited)
    np.put_along_axis(conditioned, order, np.take_along_axis(inherited, order, axis=1), axis=1)
    removed = 1 - conditioned.sum(1)
    conditioned /= conditioned.sum(1)[:, None]
    opposite = [i for i, name in enumerate(names) if name.endswith('.' + ('L' if side == 'R' else 'R'))]
    assert not np.any(conditioned[:, opposite])
    cuff_ids = np.unique(hand['cuffBoundaryEdges'])
    distal_forearm = names.index('DEF-forearm.' + side + '.001')
    assert hand['fourCoefficients'][cuff_ids, distal_forearm].min() > .94
    for digit in ('pinky', 'ring', 'middle', 'index', 'thumb'):
        stem = 'thumb' if digit == 'thumb' else 'f_' + digit
        for number in (1, 2, 3):
            assert conditioned[:, names.index(f'DEF-{stem}.{number:02d}.{side}')].sum() > 1
    total_vertices += len(cv); total_faces += len(cf)
    thumb = next(r for r in regions['sides'][side]['regions'] if r['name'] == 'selected-thumb-thenar-web-panel')
    assert 279 in thumb['faceIds'] and len(thumb['faceIds']) > 1
    receipts[side] = {'actualTargetSHA256': records['hand' + side]['sha256'],
                       'thumbWebFaceCount': len(thumb['faceIds']), 'thumbIncludesActualFace279': True,
                       'predictedVertices': total_vertices, 'predictedPolygons': total_faces,
                       'oppositeHandInfluenceMass': float(conditioned[:, opposite].sum()),
                       'cuffDistalForearmMinimumWeight': float(hand['fourCoefficients'][cuff_ids, distal_forearm].min()),
                       'interpolatedFourMaximumRemovedMass': float(removed.max()),
                       'interpolatedFourMaximumCoefficientChange': float(np.max(abs(conditioned - inherited))),
                       'digitJointsWithUsefulInfluence': 15,
                       'regions': patch_receipts}
report = {'status': 'SOURCE_ONLY_ARRAY_EDITS_EXECUTED_NO_BLENDER_JOB', 'acceptedArt': False,
          'pythonASTPassed': True, 'immutableInputPinsPassed': len(records), 'hands': receipts,
          'sourceFiles': {str(p.relative_to(ROOT)): sha(p) for p in sorted(HERE.iterdir()) if p.is_file()},
          'limits': ['Array edits are not native Blender construction, material bake, animation, or played art qualification.',
                     'Native geometry, full fields, UV/action checkpoints and textured comparison remain unexecuted.',
                     'Predicted geometry needs measured complete-outfit performance/LOD review.']}
EVIDENCE.mkdir(parents=True, exist_ok=True)
(EVIDENCE / 'source-checkpoint.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({k: report[k] for k in ('status', 'pythonASTPassed', 'immutableInputPinsPassed')}))
print(json.dumps({s: {k: value for k, value in receipt.items() if k != 'regions'} for s, receipt in receipts.items()}, indent=2))
