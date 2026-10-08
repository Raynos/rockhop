"""Cheap immutable-array authoring of lower correspondence controls; no Blender.
Original evaluated source only. This never loads rejected fitted positions.
"""
import hashlib
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[5]
LEAF = Path(__file__).resolve().parent
EVIDENCE = ROOT / 'docs/evidence/rider-rebuild/production-jeans02/whole-correspondence02'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    lineage = ROOT / 'harness/out/rider-rebuild/production-jeans02/dense-fit01/authored01/dense-fit-lineage.npz'
    dense = ROOT / 'assets/blender/hero-remaster/rider/finish-2026-10-05/wardrobe/data/prep02/jeans/cleaned-donor.npz'
    gusset = ROOT / 'harness/out/rider-rebuild/production-jeans02/authored01/local-gusset-delta.npz'
    assert sha(lineage) == '1c644d3993648b4f25d88e86303cfb4643a76f8b6ac1e50b19b7fcf172605478'
    assert sha(dense) == 'c38413a36d564d97f106ebde13bb240d4c7075078ce463f30234a97c0f3d2237'
    assert sha(gusset) == '3af3c3d7d7e73abbe4b9b4ffb71bdbd0b41c1f0bb11804a751928dacb2be21f2'
    with np.load(lineage) as data: points = data['originalEvaluatedPositions'].copy()
    with np.load(dense) as data: faces = data['faces'].copy()
    with np.load(gusset) as data: original = data['newCage'].copy()
    proxy, cage = original.copy(), original.copy()
    # Exact existing native control vertex lineage, including welded root arc.
    ids, shared, counter = {}, {}, 0
    for side in ('L', 'R'):
        ids[side] = []
        for level in range(14):
            row = []
            for k in range(48):
                if level == 13 and 18 <= k <= 30:
                    if k in shared: row.append(shared[k]); continue
                    shared[k] = counter
                row.append(counter); counter += 1
            ids[side].append(row)
    # Original X0 triangle intersections, retained as line segments.
    triangles = points[faces]
    triangles = triangles[(triangles[:, :, 0].min(1) <= 0) & (triangles[:, :, 0].max(1) >= 0)]
    segments = []
    for triangle in triangles:
        intersections = []
        for i, j in ((0, 1), (1, 2), (2, 0)):
            a, b = triangle[i], triangle[j]
            if a[0] * b[0] <= 0 and abs(float(a[0] - b[0])) > 1e-10:
                intersections.append(a + (-a[0] / (b[0] - a[0])) * (b - a))
        if len(intersections) == 2: segments.append(intersections)
    segments = np.asarray(segments)
    root_y = np.linspace(-.163, .140, 13)
    roots = []
    for y in root_y:
        a, b = segments[:, 0], segments[:, 1]
        valid = ((a[:, 1] - y) * (b[:, 1] - y) <= 0) & (np.abs(a[:, 1] - b[:, 1]) > 1e-9)
        aa, bb = a[valid], b[valid]; t = (y - aa[:, 1]) / (bb[:, 1] - aa[:, 1])
        z = float(np.min(aa[:, 2] + t * (bb[:, 2] - aa[:, 2])))
        roots.append([0, float(y), z + .003])
    rows = []; strips = []
    source_heights = [None, None, .24, .31, .41, .49, .52, .55, .58, .62, .70, .77, .83, .91]
    for side, sign in (('L', 1), ('R', -1)):
        own = points.copy(); own[:, 0] *= sign; own = own[own[:, 0] > 0]
        hem_section = own[np.abs(own[:, 2] - .175) <= .008]
        hem_centre = (hem_section[:, :2].min(0) + hem_section[:, :2].max(0)) / 2
        hem_radius = (hem_section[:, :2].max(0) - hem_section[:, :2].min(0)) / 2
        hem_candidates = own[own[:, 2] < .22]
        hem_theta = np.arctan2(-(hem_candidates[:, 1] - hem_centre[1]) / hem_radius[1],
                               (hem_candidates[:, 0] - hem_centre[0]) / hem_radius[0])
        hem_z = []
        for anchor in range(8):
            angle = anchor * np.pi / 4
            delta = np.abs((hem_theta - angle + np.pi) % (2 * np.pi) - np.pi)
            sample = hem_candidates[delta <= np.deg2rad(3)]
            assert len(sample)
            hem_z.append(float(sample[:, 2].min()) + .008)
        for level in range(14):
            heights = np.asarray(hem_z) + (0 if level == 0 else .05) if level <= 1 else np.full(8, source_heights[level])
            section = own[np.abs(own[:, 2] - heights.mean()) <= .01]
            assert len(section)
            centre = (section[:, :2].min(0) + section[:, :2].max(0)) / 2
            radius = (section[:, :2].max(0) - section[:, :2].min(0)) / 2
            angular = np.arctan2(-(own[:, 1] - centre[1]) / radius[1], (own[:, 0] - centre[0]) / radius[0])
            radial = np.sqrt(((own[:, 0] - centre[0]) / radius[0]) ** 2 + ((own[:, 1] - centre[1]) / radius[1]) ** 2)
            p8, c8, envelopes = [], [], []
            for anchor, z in enumerate(heights):
                if level == 13 and anchor in (3, 4, 5):
                    # Above the fork there is one pelvis, not two radial leg
                    # cylinders. These anchors use the measured underside seam.
                    root = roots[(anchor - 3) * 6]
                    p8.append(root); c8.append([0, root[1], root[2] - .015])
                    envelopes.append({'anchor': anchor * 45, 'authority': 'exact original source sagittal underside'})
                    continue
                angle = anchor * np.pi / 4
                delta = np.abs((angular - angle + np.pi) % (2 * np.pi) - np.pi)
                selected = np.flatnonzero((delta <= np.pi / 8) & (np.abs(own[:, 2] - z) <= .008))
                assert len(selected), (side, level, anchor, z)
                maximum = float(radial[selected].max()); median = float(np.median(radial[selected]))
                basis = np.asarray([radius[0] * np.cos(angle), -radius[1] * np.sin(angle)])
                q = centre + median * basis
                c = centre + maximum / np.cos(np.pi / 8) * basis + .008 * basis / np.linalg.norm(basis)
                q[0] = max(float(q[0]), .002); c[0] = max(float(c[0]), .001)
                p8.append([sign * q[0], q[1], float(z)]); c8.append([sign * c[0], c[1], float(z)])
                witness = int(selected[np.argmax(radial[selected])])
                envelopes.append({'anchor': anchor * 45, 'samples': len(selected), 'maximumRadius': maximum,
                                  'medianRadius': median, 'ownSourceWitness': own[witness].tolist()})
            for k, vertex in enumerate(ids[side][level]):
                a = k / 6; lo = int(a) % 8; hi = (lo + 1) % 8; t = a - int(a)
                proxy[vertex] = np.asarray(p8[lo]) * (1 - t) + np.asarray(p8[hi]) * t
                cage[vertex] = np.asarray(c8[lo]) * (1 - t) + np.asarray(c8[hi]) * t
            rows.append({'side': side, 'level': level, 'sourceMeanZ': float(heights.mean()),
                         'ownCentreXY': centre.tolist(), 'ownBasisRadiusXY': radius.tolist(),
                         'proxyAnchors': p8, 'cageAnchors': c8, 'envelopes': envelopes})
        # Direct underside seam and own-sided support strips follow actual source.
        for k, root in zip(range(18, 31), roots):
            vertex = ids[side][13][k]; proxy[vertex] = root; cage[vertex] = [0, root[1], root[2] - .015]
            old_root = original[vertex]
            for level in (11, 12):
                support = ids[side][level][k]; desired = np.asarray(root) + (original[support] - old_root)
                candidates = np.flatnonzero((np.abs(own[:, 1] - desired[1]) <= .01) & (np.abs(own[:, 2] - desired[2]) <= .01))
                assert len(candidates), (side, level, k, desired.tolist())
                witness = own[int(candidates[np.argmin(own[candidates, 0])])].copy()
                proxy[support] = [sign * (witness[0] + .002), witness[1], witness[2]]
                cage[support] = [sign * max(witness[0] - .008, .001), witness[1], witness[2]]
                strips.append({'side': side, 'level': level, 'k': k, 'vertex': support,
                               'sourceInnerBoundaryWitness': witness.tolist(), 'proxy': proxy[support].tolist(),
                               'cage': cage[support].tolist()})
    assert original.shape == proxy.shape == cage.shape == (1691, 3)
    controls_path = LEAF / 'lower-controls.npz'
    np.savez_compressed(controls_path, originalNativeControlPositions=original,
                        authoredProjectionControlPositions=proxy, authoredCaptureControlPositions=cage)
    receipt = {'accepted': False, 'originalEvaluatedArraySHA256': hashlib.sha256(points.tobytes()).hexdigest(),
        'inputs': {key: {'path': str(p.relative_to(ROOT)), 'sha256': sha(p)} for key, p in
                   [('originalSourceLineage', lineage), ('originalDense', dense), ('nativeGussetLineage', gusset)]},
        'controlArray': {'path': str(controls_path.relative_to(ROOT)), 'sha256': sha(controls_path)},
        'generatorSHA256': sha(__file__), 'nativeControlVertices': 1691,
        'rows': rows, 'sourceSagittalSeamProxy': roots, 'sourceSagittalCageZOffset': -.015,
        'ownSidedSupportStrips': strips, 'limits': ['Original evaluated source only; fitted arrays never read.',
            'Measured anchors do not prove whole interpolation capture. Actual native save and direct capture gate precede any map.',
            'Only lower correspondence derivatives use these controls; working pelvis/wearing geometry/UV/fields unchanged.']}
    (EVIDENCE / 'source-envelope.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps({'controlsSHA256': sha(controls_path), 'sourceEnvelopeSHA256': sha(EVIDENCE / 'source-envelope.json'),
                      'rows': len(rows), 'anchors': len(rows) * 8, 'strips': len(strips), 'seam': roots}))


if __name__ == '__main__': main()
