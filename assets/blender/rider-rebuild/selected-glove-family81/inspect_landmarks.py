"""Small CPU-only inventory of the frozen selector against both admitted caches.

No candidate, native read, simplifier, source mutation or parameter sweep.
"""
import hashlib
import json
from pathlib import Path
import sys
import time

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]


def unit(v):
    v = np.asarray(v, np.float64); return v/np.linalg.norm(v)


def inspect(a, rest, side, names):
    p = a['positions'].astype(np.float64); used = np.zeros(len(p), bool); used[a['triangles'].ravel()] = True
    bones = {r[0]: r for r in rest}; bone = lambda stem: bones[stem+'.'+side]
    offsets = a['fieldOffsets']; fields = np.zeros((len(p), len(names)), np.float32)
    fields[np.repeat(np.arange(len(p)), np.diff(offsets)), a['fieldIndices']] = a['fieldWeights']
    weight = lambda stems: fields[:, [names.index(s+'.'+side) for s in stems]].sum(axis=1)
    rows = []

    def ring(label, center, axis, preferred, mask, band):
        axis = unit(axis); x = unit(preferred-np.dot(preferred, axis)*axis); z = np.cross(axis, x)
        relative = p-center; axial, rx, rz = relative@axis, relative@x, relative@z
        radius2 = rx*rx+rz*rz
        spatial = used & (np.abs(axial) <= band) & (radius2 > 0)
        sectors = np.floor((np.arctan2(rz, rx)+np.pi)*(8/(2*np.pi))).astype(np.int32) % 8
        counts = np.bincount(sectors[spatial & mask], minlength=8)
        all_counts = np.bincount(sectors[spatial], minlength=8)
        signed = axial[a['triangles']]
        crossing = (signed.min(axis=1) < 0) & (signed.max(axis=1) > 0)
        zero_vertex = (signed == 0).any(axis=1)
        rows.append({'landmark': label, 'filteredSectorCounts': counts.tolist(), 'unfilteredSectorCounts': all_counts.tolist(),
                     'missingFilteredSectors': np.flatnonzero(counts == 0).tolist(),
                     'missingUnfilteredSectors': np.flatnonzero(all_counts == 0).tolist(),
                     'exactPlaneCrossingTriangles': int(crossing.sum()), 'exactPlaneTouchTriangles': int(zero_vertex.sum()),
                     'oldBandM': float(band), 'oldSemanticVerticesInBand': int((spatial & mask).sum())})

    for digit in ('thumb', 'f_index', 'f_middle', 'f_ring', 'f_pinky'):
        stems = [f'DEF-{digit}.{i:02}' for i in (1, 2, 3)]; support = weight(stems) >= .2
        for i, stem in enumerate(stems, 1):
            b = bone(stem); head, tail = np.asarray(b[2]), np.asarray(b[3]); axis = tail-head
            ring(f'{digit}-joint{i}', head, axis, np.asarray(b[4])[:3, 0], support, np.linalg.norm(axis)*.35)
        b = bone(stems[-1]); head, tail = np.asarray(b[2]), np.asarray(b[3]); axis = tail-head
        ring(digit+'-tip-rim', tail, axis, np.asarray(b[4])[:3, 0], weight([stems[-1]]) >= .2,
             max(.002, np.linalg.norm(axis)*.6))
    hand = bone('DEF-hand'); wrist, palm_end = np.asarray(hand[2]), np.asarray(hand[3])
    across = unit(np.asarray(bone('DEF-f_pinky.01')[2])-bone('DEF-f_index.01')[2])
    normal = unit(np.cross(unit(palm_end-wrist), across))
    for first, second in [('thumb', 'f_index'), ('f_index', 'f_middle'), ('f_middle', 'f_ring'), ('f_ring', 'f_pinky')]:
        a1, b = bone('DEF-'+first+'.01'), bone('DEF-'+second+'.01')
        center = (np.asarray(a1[3] if first == 'thumb' else a1[2])+b[2])/2
        mask = used & (weight(['DEF-'+first+'.01', 'DEF-'+second+'.01']) >= .2)
        relative = p-center; dorsal, transverse = relative@normal, relative@across
        counts = [int((mask & (dorsal*d >= 0) & (transverse*t >= 0)).sum()) for d in (-1, 1) for t in (-1, 1)]
        rows.append({'landmark': first+'-'+second+'-web', 'filteredQuadrantCounts': counts,
                     'missingFilteredQuadrants': [i for i, count in enumerate(counts) if count == 0]})
    forearm = bones['DEF-forearm.'+side+'.001']; axis = unit(np.asarray(forearm[3])-forearm[2])
    mask = used & (fields[:, [names.index(n) for n in ['DEF-hand.'+side, 'DEF-forearm.'+side, 'DEF-forearm.'+side+'.001']]].sum(axis=1) >= .2)
    band = max(.003, np.linalg.norm(np.asarray(forearm[3])-forearm[2])*.1)
    ring('wrist-cuff-junction', wrist, axis, np.asarray(forearm[4])[:3, 0], mask, band)
    proximal = ((p[mask]-wrist)@axis).min()
    ring('proximal-cuff-lip', wrist+proximal*axis, axis, np.asarray(forearm[4])[:3, 0], mask, band)
    return rows


if __name__ == '__main__':
    started = time.monotonic(); assert len(sys.argv) == 3
    extraction = json.loads(Path(sys.argv[1]).read_text()); target = Path(sys.argv[2]); assert not target.exists()
    results = {}
    for side in ('L', 'R'):
        row = extraction['objects']['ActualSelectedGlove.'+side]; file = ROOT/row['arrays']['path']
        assert hashlib.sha256(file.read_bytes()).hexdigest() == row['arrays']['sha256']
        with np.load(file, allow_pickle=False) as dump:
            arrays = {key: dump[key] for key in ('positions', 'triangles', 'fieldOffsets', 'fieldIndices', 'fieldWeights')}
        results[side] = inspect(arrays, extraction['rest'], side, row['groupNames'])
    result = {'status': 'ACTUAL41_BILATERAL_FROZEN_LANDMARK_SOURCE_INVENTORY', 'acceptedArt': False,
              'recipeSHA256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'extractionSHA256': hashlib.sha256(Path(sys.argv[1]).read_bytes()).hexdigest(),
              'sides': results, 'elapsedSeconds': time.monotonic()-started, 'candidateAttempts': 0,
              'limits': 'Read-only source inventory, no reduction or geometry/fit acceptance.'}
    target.parent.mkdir(parents=True, exist_ok=True); target.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({'elapsedSeconds': result['elapsedSeconds'], 'missing': {side: [r for r in rows if r.get('missingFilteredSectors') or r.get('missingFilteredQuadrants')] for side, rows in results.items()}}, indent=2))
