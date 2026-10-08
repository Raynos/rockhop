"""Freeze anatomical face brush selections; NumPy only, no Blender/model job.

Selections are artist planes/strips in each actual hand's local frame. Runtime
modeling consumes explicit face IDs and never classifies a tip branch or casts
surface rays. Input fields do not decide which anatomical faces exist.
"""
import hashlib
import json
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
unit = lambda p: p / np.linalg.norm(p)
records = json.loads((HERE / 'inputs.json').read_text())
body = np.load(ROOT / records['nativeArrays']['path'])
names = body['jointNames'].tolist()
result = {'construction': 'EXPLICIT_CONNECTED_ANATOMICAL_FACE_REGIONS', 'sides': {}}
for side in ('R', 'L'):
    hand = np.load(ROOT / records['hand' + side]['path'])
    vertices, faces = hand['vertices'], hand['faces']
    centers = vertices[faces].mean(1)
    normals = np.cross(vertices[faces[:, 1]] - vertices[faces[:, 0]], vertices[faces[:, 2]] - vertices[faces[:, 0]])
    normals /= np.linalg.norm(normals, axis=1)[:, None]
    head = lambda name: body['jointHeads'][names.index(name + '.' + side)]
    tail = lambda name: body['jointTails'][names.index(name + '.' + side)]
    wrist = head('DEF-hand')
    forward = unit(head('DEF-f_middle.01') - wrist)
    radial = head('DEF-f_index.01') - head('DEF-f_pinky.01')
    radial = unit(radial - forward * np.dot(radial, forward))
    dorsal = unit(np.cross(radial, forward)) * (1 if side == 'R' else -1)
    local = (centers - wrist) @ np.array([radial, forward, dorsal]).T
    x, y, z = local.T
    dorsal_dot = normals @ dorsal
    edges = {}
    for fi, face in enumerate(faces):
        for a, b in zip(face, np.roll(face, -1)):
            edges.setdefault(tuple(sorted((int(a), int(b)))), []).append(fi)
    neighbors = [set() for _ in faces]
    for owners in edges.values():
        for fi in owners:
            neighbors[fi].update(set(owners) - {fi})
    regions = []
    def region(name, mask, height, inset=.0007, subdivision=2, rib_count=0, axis=None, anchor=None):
        ids = set(map(int, np.flatnonzero(mask)))
        components = []
        while ids:
            seen = {min(ids)}; frontier = list(seen)
            while frontier:
                fi = frontier.pop()
                for other in neighbors[fi] & ids - seen:
                    seen.add(other); frontier.append(other)
            ids -= seen; components.append(sorted(seen))
        assert components, (side, name, 'empty anatomical brush')
        if anchor is not None:
            chosen = next(c for c in components if anchor in c)
        else:
            chosen = max(components, key=len)
        assert len(chosen) >= 1, (side, name, len(chosen))
        regions.append({'name': name, 'faceIds': chosen, 'heightMeters': height,
                        'insetMeters': inset, 'subdivision': subdivision,
                        'ribCount': rib_count, 'ribAxisWorld': None if axis is None else axis.tolist(),
                        'brushComponents': [len(c) for c in components],
                        'discardedDisconnectedFaceIds': [fi for c in components if c != chosen for fi in c]})
    region('selected-knuckle-leather-pad', (y > .050) & (y < .079) & (x > -.040) & (x < .026) & (dorsal_dot > .45), .0021)
    region('selected-back-textile-panel', (y > .016) & (y < .046) & (abs(x) < .027) & (dorsal_dot > .48), .00055)
    region('selected-palm-grip-pad', (y > .025) & (y < .070) & (x > -.032) & (x < .018) & (dorsal_dot < -.42), .001)
    # Thumb-root panel deliberately owns proximal thenar/web faces omitted by
    # historical tip seeds. R279 is a real dorsal thenar face, explicitly owned.
    region('selected-thumb-thenar-web-panel', (x > .023) & (y > .023) & (y < .078) & (dorsal_dot > .20), .00115, anchor=279)
    region('selected-thumb-palm-thenar-pad', (x > .019) & (y > .023) & (y < .071) & (dorsal_dot < -.22), .001)
    for digit in ('pinky', 'ring', 'middle', 'index', 'thumb'):
        stem = 'DEF-thumb' if digit == 'thumb' else 'DEF-f_' + digit
        hs = np.array([head(stem + '.' + str(i).zfill(2)) for i in (1, 2, 3)])
        ts = np.array([tail(stem + '.' + str(i).zfill(2)) for i in (1, 2, 3)])
        lengths = np.linalg.norm(ts - hs, axis=1)
        starts = np.r_[0, np.cumsum(lengths)]
        segments = ts - hs
        t = np.clip(np.sum((centers[:, None] - hs[None]) * segments[None], axis=2) / lengths[None] ** 2, 0, 1)
        projection = hs[None] + t[:, :, None] * segments[None]
        squared = np.sum((centers[:, None] - projection) ** 2, axis=2)
        own = squared.argmin(1)
        s = starts[own] + t[np.arange(len(faces)), own] * lengths[own]
        corner_s = starts[own, None] + np.sum((vertices[faces] - hs[own, None]) * (segments[own] / lengths[own, None])[:, None], axis=2)
        radius = np.sqrt(squared[np.arange(len(faces)), own])
        axes = segments[own] / lengths[own, None]
        across = radial[None] - axes * np.sum(axes * radial, axis=1)[:, None]
        across /= np.linalg.norm(across, axis=1)[:, None]
        offset = np.sum((centers - projection[np.arange(len(faces)), own]) * across, axis=1)
        start = .049 if digit != 'index' else .043
        if digit == 'middle': start = .047
        # Thumb proximal panel is thenar/web above; distal patches start after
        # that structural surface rather than pretending a tip pool owns it.
        if digit == 'thumb': start = .051
        available = starts[-1] - start
        support = (radius < .016) & (abs(offset) < .009) & (dorsal_dot > .32)
        for index, (lo, hi) in enumerate(((0, .28), (.44, .65), (.77, 1.02)), 1):
            region(f'{digit}-leather-panel{index}', support & (s > start + available * lo) & (s < start + available * hi), .00065)
        for index, (lo, hi) in enumerate(((.28, .44), (.65, .77)), 1):
            region(f'{digit}-joint-rib-band{index}', support & (corner_s.max(1) >= start + available * lo) & (corner_s.min(1) <= start + available * hi), .00075, inset=.00025, subdivision=3, rib_count=3, axis=unit(segments[1 if index == 1 else 2]))
    region('selected-cuff-closure-strap', (y > -.017) & (y < -.004) & (abs(x) < .025) & (dorsal_dot > .35), .0018, inset=.0006)
    result['sides'][side] = {'inputPin': records['hand' + side], 'regions': regions,
                             'thumbRootIncludesFace279': 279 in next(r['faceIds'] for r in regions if r['name'] == 'selected-thumb-thenar-web-panel')}
path = HERE / 'face-regions.json'
path.write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({'faceRegionsSHA256': hashlib.sha256(path.read_bytes()).hexdigest(),
                  'counts': {s: {r['name']: len(r['faceIds']) for r in d['regions']} for s, d in result['sides'].items()}}, indent=2))
