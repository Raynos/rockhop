"""Bounded CPU reproduction of55's first nonexistent endpoint interval.

The old native exception omitted side/depth/role. This reconstructs the exact
ordered source intake and covers both possible adjacent-triangle ray normals.
It does not pretend that an unlogged Blender BVH tie winner was observed.
"""
import json
import runpy
import sys
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
h = runpy.run_path(str(HERE.parent/'selected-anatomical-hoodie-fit55/component.py'))
r = runpy.run_path(str(HERE.parent/'selected-sleeve-support49/check_source_pair.py'))
S = runpy.run_path(str(HERE.parent/'selected-anatomical-hoodie-fit55/sections.py'))
Mesh = runpy.run_path(str(HERE/'geometry.py'))['Mesh']


def main():
    output = Path(sys.argv[1]).resolve(); assert not output.exists()
    doc, accessor = r['glb'](r['prior']['originalHoodie']); primitive = doc['meshes'][0]['primitives'][0]
    raw = accessor(primitive['attributes']['POSITION'])[:, [0, 2, 1]].astype(float); raw[:, 1] *= -1
    faces = accessor(primitive['indices']).reshape(-1, 3)
    frames = h['read'](r['prior']['hoodieSourceFrames'])
    xyz = raw*np.asarray(frames['sourceDisplayAffine']['scale'])+frames['sourceDisplayAffine']['translation']
    original = np.load(h['checked'](h['REFERENCE']['original47Arrays']))['points'].astype(float)
    broad = np.load(h['checked'](h['REFERENCE']['broad50Arrays']))['points'].astype(float)
    config = h['read'](h['SOURCE47']); body_pin = config['pins']['referenceSamples']; data = np.load(h['checked'](body_pin))
    body = Mesh(data['RiderBody__FullAnatomyReference_basis'], data['RiderBody__FullAnatomyReference_triangles'])
    cloth = Mesh(original, faces); precision = float(np.spacing(np.float32(max(abs(body.points).max(), 1.))))
    target = config['field']['clothClearanceM']+config['field']['contactSolveMarginM']
    examined = []; located = None
    for side, sign in (('L', 1), ('R', -1)):
        front = frames['landmarks']['frontArmhole.'+side]['source'][1]
        rear = frames['landmarks']['rearArmhole.'+side]['source'][1]
        for depth in np.linspace(front, rear, 13):
            try: nodes, branches, _ = S['underarm'](xyz, faces, float(depth), side, frames)
            except AssertionError: continue
            for role, path in branches.items():
                row = S['sample_path'](nodes, path, (original, broad), faces, 9)[-1]
                point, end = row['points']; candidates = np.flatnonzero(np.all(
                    (cloth.low-2*precision <= point) & (point <= cloth.high+2*precision), axis=1))
                variants = []
                for face in candidates:
                    tri = cloth.triangles[face]; normal = np.cross(tri[1]-tri[0], tri[2]-tri[0]); normal /= np.linalg.norm(normal)
                    hits = [hit for hit in cloth.ray_hits(point-normal*precision, -normal) if hit[0] > precision]
                    assert hits
                    hit = hits[0]; inside = np.asarray(hit[3])@broad[faces[hit[2]]]
                    pair = np.vstack((end, inside)); center = pair.mean(0)
                    ray = body.x_hits(center[1], center[2], sign)
                    gaps = [(a[0], b[0]) for a, b in zip(ray[:-1], ray[1:]) if a[1] > 0 and b[1] < 0 and b[0]-a[0] > precision]
                    mid_min = None
                    if gaps:
                        middle = np.array([sign*np.mean(gaps[0]), center[1], center[2]])
                        mid_min = float(body.nearest(middle+pair-center)[0].min())
                    variants.append({'sourceNormalFace': int(face), 'pairedInnerFace': hit[2],
                        'pairedInnerBarycentric': hit[3], 'endpointPair': pair.tolist(),
                        'actualEndpointMinimumM': float(body.nearest(pair)[0].min()),
                        'bodyXLineHits': [{'xFromCenter': x, 'outward': n > 0, 'face': f} for x, n, f in ray],
                        'hasInterbodyInterval': bool(gaps), 'oldIntervalMidpointMinimumM': mid_min,
                        'oldIntervalCanStart': bool(gaps and mid_min >= target)})
                record = {'side': side, 'sourceDepth': float(depth), 'role': role,
                    'outerOriginalEndpoint': point.tolist(), 'outerBroad50Endpoint': end.tolist(),
                    'outerBroad50ActualClearanceM': float(body.nearest(end[None])[0][0]),
                    'originalEndpointAncestry': row['parents'], 'adjacentNormalVariants': variants}
                examined.append(record)
                if all(not v['oldIntervalCanStart'] for v in variants): located = record; break
                assert all(v['oldIntervalCanStart'] for v in variants), 'BVH normal tie changes classification; native diagnostic needed'
            if located: break
        if located: break
    assert located and all(v['actualEndpointMinimumM'] >= target for v in located['adjacentNormalVariants'])
    failure = h['ROOT']/'harness/out/rider-rebuild/selected-anatomical-hoodie-fit55/component01/construction-failure.json'
    result = {'acceptedArt': False, 'diagnosticOnly': True, 'recipe': h['pin'](__file__),
        'geometryHelper': h['pin'](HERE/'geometry.py'), 'actual55Failure': h['pin'](failure),
        'sources': {'original47': h['REFERENCE']['original47Arrays'], 'broad50': h['REFERENCE']['broad50Arrays'],
            'originalSelectedGLB': r['prior']['originalHoodie'], 'sourceFrames': r['prior']['hoodieSourceFrames'], 'fullReference': body_pin},
        'contactMinimumM': target, 'orderedEndpointsExamined': examined,
        'firstNonexistentInterval': {'side': located['side'], 'depth': located['sourceDepth'], 'role': located['role']},
        'finding': 'Healthy rear sleeve paired endpoint lies in open exterior.55 incorrectly required it to have an opposing arm/torso hit on a horizontal X-line.',
        'limit': 'Actual55 log omitted endpoint context. CPU reconstruction establishes first failing predicate and covers adjacent normal alternatives; it does not claim the exact unlogged native BVH tie winner.'}
    output.parent.mkdir(parents=True, exist_ok=True); output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({'output': h['pin'](output), 'firstNonexistentInterval': result['firstNonexistentInterval']}))


if __name__ == '__main__': main()
