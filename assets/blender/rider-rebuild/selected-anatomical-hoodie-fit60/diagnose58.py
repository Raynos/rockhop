"""Exact recorded58 ray; original wall reconstruction covers native BVH ties."""
import json
import runpy
import sys
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
H = runpy.run_path(str(HERE.parent/'selected-anatomical-hoodie-fit58/component.py'))
R = runpy.run_path(str(HERE.parent/'selected-sleeve-support49/check_source_pair.py'))
S = runpy.run_path(str(HERE.parent/'selected-anatomical-hoodie-fit58/sections.py'))
G = runpy.run_path(str(HERE.parent/'selected-anatomical-hoodie-fit58/geometry.py'))


def intake():
    doc, accessor = R['glb'](R['prior']['originalHoodie']); p = doc['meshes'][0]['primitives'][0]
    raw = accessor(p['attributes']['POSITION'])[:, [0, 2, 1]].astype(float); raw[:, 1] *= -1
    faces = accessor(p['indices']).reshape(-1, 3)
    frames = H['read'](R['prior']['hoodieSourceFrames'])
    xyz = raw*np.asarray(frames['sourceDisplayAffine']['scale'])+frames['sourceDisplayAffine']['translation']
    original = np.load(H['checked'](H['REFERENCE']['original47Arrays']))['points'].astype(float)
    broad = np.load(H['checked'](H['REFERENCE']['broad50Arrays']))['points'].astype(float)
    config = H['read'](H['SOURCE47']); body_pin = config['pins']['referenceSamples']; data = np.load(H['checked'](body_pin))
    body = G['Mesh'](data['RiderBody__FullAnatomyReference_basis'], data['RiderBody__FullAnatomyReference_triangles'])
    cloth = G['Mesh'](original, faces)
    return raw, xyz, faces, frames, original, broad, body, cloth, body_pin


def variants(row, cloth, broad, precision):
    point = row['points'][0]
    candidates = np.flatnonzero(np.all((cloth.low-2*precision <= point) & (point <= cloth.high+2*precision), axis=1))
    result = []
    for face in candidates:
        tri = cloth.triangles[face]; n = np.cross(tri[1]-tri[0], tri[2]-tri[0]); n /= np.linalg.norm(n)
        # Same normal-directed paired-wall ray as58, with explicit float64 CPU provenance.
        hits = [hit for hit in cloth.ray_hits(point-n*precision, -n) if hit[0] > precision]
        if not hits: continue
        hit = hits[0]; inner = np.asarray(hit[3])@cloth.triangles[hit[2]]
        inside50 = np.asarray(hit[3])@broad[cloth.faces[hit[2]]]
        result.append((np.vstack((point, inner)), np.vstack((row['points'][1], inside50)),
            {'sourceNormalFace': int(face), 'innerOriginalFace': int(hit[2]), 'innerOriginalBarycentric': hit[3]}))
    assert result
    return result


def main():
    output = Path(sys.argv[1]).resolve(); assert not output.exists()
    raw, xyz, faces, frames, original, broad, body, cloth, body_pin = intake()
    failure_path = H['ROOT']/'harness/out/rider-rebuild/selected-anatomical-hoodie-fit58/component01/construction-failure.json'
    failure = json.loads(failure_path.read_text()); c = failure['targetContext']; station = c['lastStation']
    precision = float(np.spacing(np.float32(max(abs(body.points).max(), 1.))))
    nodes, branches, record = S['underarm'](xyz, faces, c['sourceDepth'], c['side'], frames)
    rows = S['sample_path'](nodes, branches[c['role']], (original, broad), faces, 9)
    apex, end = np.asarray(c['fixedApexPair']), np.asarray(c['healthy50EndpointPair'])
    t = station['materialCurveParameter']; blend = t*t*t*(10+t*(-15+6*t))
    center, direction = np.asarray(station['center']), np.asarray(station['direction'])
    lower, upper = station['radiusIntervalM']; desired = station['desiredRetainedEaseM']
    evidence = []
    for pair, broad_pair, ancestry in variants(rows[1], cloth, broad, precision):
        offset = ((apex-apex.mean(0))*.75+(pair-pair.mean(0))*.25)*(1-blend)+(end-end.mean(0))*blend
        def gap(r): return float(body.nearest(center+r*direction+offset)[0].min())
        # These explicit samples diagnose;60's constructor uses analytic intervals instead.
        radii = np.linspace(lower, upper, 33); gaps = [gap(r) for r in radii]
        evidence.append({'ancestry': ancestry, 'sourcePairAtOneEighth': pair.tolist(), 'offsetsAtFailure': offset.tolist(),
            'midpointMinimumM': gap((lower+upper)/2), 'sampledBestRadiusM': float(radii[np.argmax(gaps)]),
            'sampledBestMinimumM': max(gaps), 'feasibleSampleExists': max(gaps) >= desired,
            'samples': [{'radiusM': float(r), 'pairedMinimumM': g} for r, g in zip(radii, gaps)]})
    result = {'acceptedArt': False, 'diagnosticOnly': True, 'sourceRecipe': H['pin'](__file__),
        'actual58Failure': H['pin'](failure_path), 'source58Input': H['pin'](HERE.parent/'selected-anatomical-hoodie-fit58/input01.json'),
        'sourcePins': {**{k: H['REFERENCE'][k] for k in ('original47Arrays', 'broad50Arrays')},
            'originalSelectedGLB': R['prior']['originalHoodie'], 'frames': R['prior']['hoodieSourceFrames'], 'fullBody': body_pin},
        'recordedStation': station, 'nativeCoordinatePrecisionM': precision, 'wallVariants': evidence,
        'limit': 'CPU float64 normal/ray reconstruction covers original adjacent normal alternatives; native58 omitted exact paired offsets.'}
    output.parent.mkdir(parents=True, exist_ok=True); output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({'output': H['pin'](output), 'variants': [{k: v[k] for k in ('ancestry', 'midpointMinimumM', 'sampledBestRadiusM', 'sampledBestMinimumM', 'feasibleSampleExists')} for v in evidence]}))


if __name__ == '__main__': main()
