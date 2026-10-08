"""Freeze the final measured connected cuff-sector correction; no Blender job.

Run with the NumPy environment after parent source review. A failed orientation
check stops this bounded mechanism; no repair loop or parameter campaign.
"""
import hashlib
import heapq
import json
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        while block := stream.read(1024*1024): h.update(block)
    return h.hexdigest()


def pin(row):
    path = ROOT/row['path']; assert sha(path) == row['sha256'], ('Changed source', row); return path


def graph(points, faces):
    edges = np.unique(np.sort(np.concatenate([faces[:, [0,1]], faces[:, [1,2]], faces[:, [2,0]]]), axis=1), axis=0)
    neighbors = [[] for _ in points]
    for a, b in edges:
        length = float(np.linalg.norm(points[a]-points[b]))
        neighbors[a].append((int(b), length)); neighbors[b].append((int(a), length))
    return neighbors


def distances(neighbors, seeds):
    """Multi-source intrinsic distance and nearest source, with stable ties."""
    dist = np.full(len(neighbors), np.inf); owner = np.full(len(neighbors), -1, int)
    previous = np.full(len(neighbors), -1, int); queue = []
    for seed in sorted(set(map(int, seeds))):
        dist[seed] = 0.; owner[seed] = seed; heapq.heappush(queue, (0., seed, seed))
    while queue:
        length, seed, index = heapq.heappop(queue)
        if length != dist[index] or seed != owner[index]: continue
        for other, edge in neighbors[index]:
            proposed = length+edge
            if proposed < dist[other] or (proposed == dist[other] and seed < owner[other]):
                dist[other] = proposed; owner[other] = seed; previous[other] = index
                heapq.heappush(queue, (proposed, seed, other))
    assert np.isfinite(dist).all(), 'Selected guide must be connected'
    return dist, owner, previous


def smooth(value):
    value = np.clip(value, 0., 1.); return value*value*(3.-2.*value)


def main():
    assert not (HERE/'controls.json').exists(), 'One frozen source only; do not overwrite or tune'
    control = json.loads((HERE/'input.json').read_text())
    for key in ('master','fullGloves','sourceGLB','placement','guideHelpers','fingerprintHelper',
                'restHelper','sourceGuide','localControls','diagnosis','parentReceipt'):
        pin(control[key])
    diagnosis = json.loads(pin(control['diagnosis']).read_text())
    assert diagnosis['sourceSHA256'] == control['sourceGLB']['sha256']
    placement = json.loads(pin(control['placement']).read_text())
    native = np.load(pin(placement['pins']['nativeArrays'])); names = native['jointNames'].tolist()
    original_selected = np.load(pin(control['sourceGuide']))['vertices']
    hands = {}
    for side in ('L','R'):
        incoming = control['hands'][side]
        previous = np.load(pin(incoming['priorCuffOffsets']))
        local = np.load(pin(incoming['previousLocalOffsets']))
        points = previous['corrected'].astype(np.float32).astype(float); faces = previous['faces']
        linear = np.asarray(placement['hands'][side]['initialPlacement']['linear'])
        translation = np.asarray(placement['hands'][side]['initialPlacement']['translation'])
        world = points@linear.T+translation
        wrist = native['jointHeads'][names.index('DEF-hand.'+side)]
        axis = native['jointHeads'][names.index('DEF-forearm.'+side)]-wrist; axis /= np.linalg.norm(axis)
        radial = world-wrist-((world-wrist)@axis)[:,None]*axis
        neighbors = graph(world, faces)
        rows = diagnosis['hands'][side]['proposedGuideControls']
        measured = {int(row['guideVertex']): row for row in rows}
        order = control['sectorControls']; assert set(measured) == set(order)
        fractions = np.full(len(points), np.nan); centerline = []
        for start, end in zip(order, order[1:]):
            d, _, preceding = distances(neighbors, [start]); path = [end]
            while path[-1] != start:
                path.append(int(preceding[path[-1]])); assert path[-1] >= 0
            path.reverse(); centerline.extend(path)
            blend = smooth(d[path]/d[end])
            a = measured[start]['linearizedRadialContractionFraction']
            b = measured[end]['linearizedRadialContractionFraction']
            fractions[path] = a*(1.-blend)+b*blend
        # Controls define one connected radial contraction field, rather than
        # independent overlapping bumps. Intrinsic distance feathers its edge.
        centerline = sorted(set(centerline))
        for index in order: fractions[index] = measured[index]['linearizedRadialContractionFraction']
        distance, owner, _ = distances(neighbors, centerline)
        protected = (np.linalg.norm(local['offsets'], axis=1)>0) | (original_selected[:,1]>=-.52)
        protected[control['oldLipAnchors']] = True
        assert not protected[order].any(), 'A measured control touches protected anatomy'
        protect_distance, _, _ = distances(neighbors, np.flatnonzero(protected))
        full_distance = float(protect_distance[order].min()); assert full_distance > 0
        brush = smooth(1.-distance/control['falloffMeters'])*smooth(protect_distance/full_distance)
        assert np.array_equal(brush[order], np.ones(len(order)))
        scale = fractions[owner]*brush
        offsets = (-radial*scale[:,None])@np.linalg.inv(linear).T
        for index, row in measured.items():
            assert row['priorAnatomical04OffsetExactlyZero'] is True
            assert np.linalg.norm(world[index]-row['currentNativeXYZ']) < 2e-8
            exact = np.asarray(row['linearizedSourceOffsetFor1p5mmInside'])
            assert np.linalg.norm(linear@(offsets[index]-exact)) < 2e-8
            offsets[index] = exact
        offsets[protected] = 0.
        corrected = (points+offsets).astype(np.float32)
        assert np.array_equal(corrected[protected], points[protected].astype(np.float32))
        before = points[faces]; after = corrected[faces].astype(float)
        normals_before = np.cross(before[:,1]-before[:,0],before[:,2]-before[:,0])
        normals_after = np.cross(after[:,1]-after[:,0],after[:,2]-after[:,0])
        dots = (normals_before*normals_after).sum(1)/(np.linalg.norm(normals_before,axis=1)*np.linalg.norm(normals_after,axis=1))
        assert np.isfinite(dots).all() and np.all(dots>0), ('Final cuff-sector guide has an orientation reversal; stop mechanism',side,int(np.sum(dots<=0)))
        assert np.min(np.linalg.norm(normals_after,axis=1)) > np.finfo(np.float32).eps
        path = HERE/f'cuff-sector-offsets-{side}.npz'
        np.savez_compressed(path, original=points.astype(np.float32), corrected=corrected,
                            offsets=corrected.astype(float)-points, faces=faces,
                            protectedGuideIds=np.flatnonzero(protected), centerlineIds=centerline)
        hands[side] = {**incoming, 'offsets':{'path':str(path.relative_to(ROOT)),'sha256':sha(path)},
            'measuredControls': rows, 'connectedCenterlineIds': centerline,
            'protectedDistanceFullStrengthM':full_distance, 'priorAnatomicalEditsAndLipAnchorsExact':True,
            'minimumFloat32NormalDot':float(dots.min()),
            'changedGuideVertices':int(np.sum(np.any(corrected != points.astype(np.float32),axis=1))),
            'maximumWorldOffsetM':float(np.linalg.norm((corrected-points)@linear.T,axis=1).max())}
    control.update(hands=hands, freezeRecipeSHA256=sha(__file__), ready=True)
    (HERE/'controls.json').write_text(json.dumps(control,indent=2)+'\n')
    print(json.dumps({side:{key:row[key] for key in ('changedGuideVertices','maximumWorldOffsetM','minimumFloat32NormalDot','protectedDistanceFullStrengthM')} for side,row in hands.items()},indent=2))


if __name__ == '__main__': main()
