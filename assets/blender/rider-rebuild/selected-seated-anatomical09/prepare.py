"""Read-only engine05 topology selection; no fitting, weight edits, or Blender.

Freeze native IDs once for a bounded native Smooth-weight brush intervention.
Re-run with python3 prepare.py; the manifest remains explicitly unaccepted.
"""
import hashlib
import heapq
import json
import math
import struct
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
PINS = {
    'native': ('harness/out/rider-rebuild/selected-complete-engine01/engine05/rider-private-masked.blend',
               '95a4f14e06fb52cc055df6d1446a035d8cd3d35180d565ad52f3a70b3b05664b'),
    'glb': ('harness/out/rider-rebuild/selected-complete-engine01/engine05/rider.glb',
            '72b90e8790f8490743a75f8b70791aa21edfee6234cec609093e9b62e08d4bfd'),
    'contract': ('harness/out/rider-rebuild/selected-complete-engine01/engine05/rider-contract.json',
                 '2aa39bc8c15738b4ecbd2aac08fd61375e0aa8fd45a0ee2ac3046f577b019728'),
    'patches': ('assets/blender/rider-rebuild/selected-posterior-support03/patches.json',
                'd76f4baadd7f447ecb72ffb01d660bbbc780142268f9e6b9c5d0ead81eba3e2f'),
    'lineage': ('harness/out/rider-rebuild/selected-seated-garage01/pelvis-rear-lineage01.json',
                '7b55fdadb0bb92491d6e7aca9a82d9c8982ad143c440d4eeab16f06a47de08e0'),
}


def sha(path):
    with Path(path).open('rb') as f:
        digest = hashlib.sha256()
        while block := f.read(1024*1024): digest.update(block)
    return digest.hexdigest()


class GLB:
    def __init__(self, path):
        self.file = Path(path).open('rb')
        self.file.seek(12); count = struct.unpack('<I', self.file.read(4))[0]
        self.file.seek(20); self.doc = json.loads(self.file.read(count)); self.base = 28+count

    def accessor(self, index):
        a = self.doc['accessors'][index]; v = self.doc['bufferViews'][a['bufferView']]
        assert not a.get('sparse') and v.get('buffer', 0) == 0
        width = {'SCALAR': 1, 'VEC3': 3, 'VEC4': 4}[a['type']]
        fmt = {5121: 'B', 5123: 'H', 5125: 'I', 5126: 'f'}[a['componentType']]
        record = struct.Struct('<'+fmt*width); stride = v.get('byteStride', record.size)
        self.file.seek(self.base+v.get('byteOffset', 0)+a.get('byteOffset', 0))
        raw = self.file.read((a['count']-1)*stride+record.size)
        return [record.unpack_from(raw, i*stride) for i in range(a['count'])]

    def mesh(self, name):
        node = next(n for n in self.doc['nodes'] if n.get('name') == name)
        positions, faces = {}, []
        for p in self.doc['meshes'][node['mesh']]['primitives']:
            ids = [int(v[0]) for v in self.accessor(p['attributes']['_NATIVE_ID'])]
            for identity, (x, y, z) in zip(ids, self.accessor(p['attributes']['POSITION'])):
                point = (x, -z, y)
                assert identity not in positions or positions[identity] == point
                positions[identity] = point
            indices = [int(v[0]) for v in self.accessor(p['indices'])]
            faces.extend(tuple(ids[i] for i in indices[k:k+3]) for k in range(0, len(indices), 3))
        return positions, faces


def graph(faces):
    result = defaultdict(set)
    for face in faces:
        for a, b in zip(face, face[1:]+face[:1]): result[a].add(b); result[b].add(a)
    return result


def distances(adjacency, positions, seeds):
    result = {i: 0. for i in seeds}; queue = [(0., i) for i in seeds]; heapq.heapify(queue)
    while queue:
        cost, i = heapq.heappop(queue)
        if cost != result[i]: continue
        for j in adjacency[i]:
            new = cost+math.dist(positions[i], positions[j])
            if new < result.get(j, math.inf): result[j] = new; heapq.heappush(queue, (new, j))
    return result


def rings(adjacency, seeds, count):
    chosen = set(seeds)
    for _ in range(count): chosen |= {j for i in chosen for j in adjacency[i]}
    return chosen


def connected(adjacency, selected):
    pending = set(selected); sizes = []
    while pending:
        component = {pending.pop()}; stack = list(component)
        while stack:
            neighbors = adjacency[stack.pop()] & pending
            pending -= neighbors; component |= neighbors; stack.extend(neighbors)
        sizes.append(len(component))
    return sorted(sizes, reverse=True)


def main():
    for filename, digest in PINS.values(): assert sha(ROOT/filename) == digest, filename
    glb = GLB(ROOT/PINS['glb'][0]); p, faces = glb.mesh('RiderJeans'); g = graph(faces)
    patches = json.loads((ROOT/PINS['patches'][0]).read_text())
    lineage = json.loads((ROOT/PINS['lineage'][0]).read_text())
    definitions = {}
    for side in ('left', 'right'):
        polygons = set(patches[side]['contextPolygonIds'])
        definitions['posterior_context_'+side] = {i for f in lineage['nativeTriangles']
            if f['originalPolygonID'] in polygons for i in f['nativeVertexIDs']}
    # Anatomical seed IDs were inspected on the actual selected rest mesh. Mirror
    # through the exact source surface, never through weight or a height classifier.
    seed_labels = {'pelvis_anchor_left': 10506, 'thigh_anchor_left': 3337,
                   'medial_fold_left': 3478, 'crotch_context': 8552}
    for name, seed in list(seed_labels.items()):
        if name.endswith('_left'):
            point = p[seed]; target = (-point[0], point[1], point[2])
            opposite = min(p, key=lambda i: math.dist(p[i], target))
            assert math.dist(p[opposite], target) < 1e-6
            seed_labels[name.replace('_left', '_right')] = opposite
    for name, seed in seed_labels.items(): definitions[name] = rings(g, {seed}, 2)
    seeds = set().union(*(v for k, v in definitions.items() if 'context' in k or 'medial_fold' in k))
    distance = distances(g, p, seeds)
    # A brush footprint on connected surface edges, not a global body-height band.
    domain = {i for i, d in distance.items() if d < .14}
    fixed = set().union(*(v for k, v in definitions.items() if '_anchor_' in k))
    outer = {i for i in domain if g[i]-domain}
    boundary_distance = distances(g, p, outer | fixed)
    influence = {i: min(1., boundary_distance[i]/.035) for i in domain-fixed-outer}
    influence = {i: x*x*(3-2*x) for i, x in influence.items() if x > 0}
    definitions['transition'] = set(influence)
    definitions['fixed_outer_ring'] = outer
    assert {8574, 8575, 10452, 10453} <= set(influence)
    assert connected(g, domain) == [len(domain)]
    body_p, body_faces = glb.mesh('RiderBody'); body_g = graph(body_faces)
    bad = {3255, 3256, 3257, 3258, 3277, 3278, 6977, 6978, 6979, 6980, 6999, 7000}
    incident = {i for f in body_faces if bad.intersection(f) for i in f}
    body_context = rings(body_g, incident, 2)
    result = {'accepted': False, 'status': 'SOURCE_ONLY_PARENT_NATIVE_RUN_PENDING',
        'sourcePins': {k: {'path': v[0], 'sha256': v[1]} for k, v in PINS.items()},
        'recipeSHA256': sha(__file__),
        'selectionMethod': 'Frozen actual native IDs; anatomical anchor seeds, connected surface-edge brush footprint, smooth falloff to fixed boundary and anchors. Source extraction used decoded triangle adjacency; native execution uses original polygon edges.',
        'seedPositionsBlender': {k: {'id': v, 'position': p[v]} for k, v in seed_labels.items()},
        'jeans': {'groups': {k: sorted(v) for k, v in definitions.items()},
                  'influence': [[i, x] for i, x in sorted(influence.items())],
                  'domain': sorted(domain), 'witnessEdges': [[8574, 8575], [10452, 10453]],
                  'smooth': {'factor': .5, 'repeat': 8},
                  'finalCutoff': .0001, 'maximumInfluences': 4},
        'body': {'crossingWitnessNativeIDs': sorted(bad), 'incidentFaceVertices': sorted(incident),
                 'transitionContext': sorted(body_context),
                 'policy': 'Selection for subsequent coupled sculpt only. Native execution closes over WHOLE incident polygons. No body weight/position edit is justified by corrective02-only crossings.'},
        'limitations': ['Source only. Brush strength is an authored single intervention, not an optimized value or anatomical acceptance.',
            'Anchors preserve existing source fields; the residual posed volume must be authored after this result is judged.',
            'No old corrective06 delta import. No GLB/GPU, crossing, contact, moving art, or phone pass.']}
    (HERE/'selection.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({'accepted': False, 'domain': len(domain), 'transition': len(influence),
        'groups': {k: len(v) for k, v in definitions.items()}, 'bodyIncident': len(incident),
        'bodyContext': len(body_context), 'seedPositions': result['seedPositionsBlender']}))


if __name__ == '__main__': main()
