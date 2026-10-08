"""Read-only saved-corner diagnostic; run only under parent's CPU2 guard.

One pinned native + genuine raw donor; writes JSON only. Tiny scratch mesh
references are never linked, rendered or saved. No candidate normal rewrite.
"""
import hashlib
import json
from pathlib import Path
import struct
import sys

import bpy
import numpy as np
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[4]
NATIVE = ROOT / 'harness/out/rider-rebuild/production-face01/native01/selected-face-native75.blend'
NATIVE_SHA = '6c80f6e8acc9b50c1d3cc30c92ca70e65148d84be6315e2100584b6f573953e4'
DONOR = Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/rig-adapter01/body-bind11/rider.glb')
DONOR_SHA = 'b7f4f22790124c664f9907104e5b17b77775b4c5c995f715d62be640bbcc8754'
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()


def unit(vector):
    vector = np.asarray(vector, dtype=float)
    return vector / np.linalg.norm(vector)


def main():
    args = sys.argv[sys.argv.index('--') + 1:]
    assert len(args) == 1
    out = Path(args[0]).resolve()
    assert out == ROOT / 'harness/out/rider-rebuild/production-face01/normal-diagnostic01'
    assert not out.exists() and sha(NATIVE) == NATIVE_SHA and sha(DONOR) == DONOR_SHA
    out.mkdir(parents=True)
    raw = DONOR.read_bytes(); size = struct.unpack_from('<I', raw, 12)[0]
    doc = json.loads(raw[20:20 + size]); binary = raw[28 + size:]

    def accessor(index):
        a = doc['accessors'][index]; view = doc['bufferViews'][a['bufferView']]
        dtype = {5126: '<f4', 5125: '<u4', 5123: '<u2', 5121: 'u1'}[a['componentType']]
        columns = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}[a['type']]
        width = np.dtype(dtype).itemsize
        return np.ndarray((a['count'], columns), dtype=dtype, buffer=binary,
                          offset=view.get('byteOffset', 0) + a.get('byteOffset', 0),
                          strides=(view.get('byteStride', width * columns), width))

    node = next(n for n in doc['nodes'] if n.get('name') == 'textured')
    primitives = doc['meshes'][node['mesh']]['primitives']
    bpy.ops.wm.open_mainfile(filepath=str(NATIVE))
    mesh = bpy.data.objects['RiderBody'].data
    retained = mesh.attributes['RetainedSourceNormal']
    assert retained.domain == 'CORNER' and retained.data_type == 'FLOAT_VECTOR'
    stored = np.array([list(row.vector) for row in retained.data])
    actual = np.array([list(row.vector) for row in mesh.corner_normals])
    ids = [row.value for row in mesh.attributes['_SOURCE_VERTEX_ID'].data]
    source_faces = [row.value for row in mesh.attributes['SelectedSourceFace'].data]
    polygons = {identity: p for identity, p in zip(source_faces, mesh.polygons) if identity >= 0}
    loop_face = {}; vertex_loops = [[] for _ in mesh.vertices]; edge_faces = [[] for _ in mesh.edges]
    for p in mesh.polygons:
        for loop in p.loop_indices:
            loop_face[loop] = p.index; vertex_loops[mesh.loops[loop].vertex_index].append(loop)
            edge_faces[mesh.loops[loop].edge_index].append(p.index)
    sharp = [e.use_edge_sharp for e in mesh.edges]
    expected_by_loop = {}; origin_by_loop = {}; coordinate_sources = {}
    for part, primitive in enumerate(primitives):
        points = accessor(primitive['attributes']['POSITION'])
        normals = accessor(primitive['attributes']['NORMAL'])
        for index, point in enumerate(points):
            if point[1] > 1.56:
                coordinate_sources.setdefault(tuple(float(x) for x in point), []).append(
                    {'part': part, 'rawVertex': index, 'rawNormal': list(map(float, normals[index]))})
        for index, triangle in enumerate(accessor(primitive['indices']).reshape(-1, 3)):
            if not all(points[int(i)][1] > 1.56 + 1e-5 for i in triangle):
                continue
            if len({tuple(points[int(i)]) for i in triangle}) < 3:
                continue
            p = polygons[part * 1000000 + index]
            for loop, original in zip(p.loop_indices, triangle):
                original = int(original); n = normals[original]
                expected_by_loop[loop] = np.array(Vector((-n[2], -n[0], n[1])).normalized())
                origin_by_loop[loop] = {'part': part, 'rawFace': index, 'rawVertex': original,
                                        'rawPosition': list(map(float, points[original]))}
    loops = np.array(list(expected_by_loop), dtype=int)
    expected = np.array([expected_by_loop[int(loop)] for loop in loops])
    errors = np.linalg.norm(actual[loops] - expected, axis=1)
    worst = loops[np.argsort(errors)[-12:][::-1]].tolist()

    def fan(target):
        vertex = mesh.loops[target].vertex_index
        by_face = {loop_face[loop]: loop for loop in vertex_loops[vertex]}
        neighbors = {loop: set() for loop in by_face.values()}
        for edge in mesh.edges:
            if vertex not in edge.vertices or sharp[edge.index]:
                continue
            faces = edge_faces[edge.index]
            if len(faces) != 2 or not all(mesh.polygons[f].use_smooth for f in faces):
                continue
            a, b = [by_face[f] for f in faces]
            neighbors[a].add(b); neighbors[b].add(a)
        seen = {target}; pending = [target]
        while pending:
            for other in neighbors[pending.pop()] - seen:
                seen.add(other); pending.append(other)
        return sorted(seen)

    def corner(loop):
        p = mesh.polygons[loop_face[loop]]; vertex = mesh.loops[loop].vertex_index
        return {'loop': loop, 'polygon': p.index, 'selectedSourceFace': source_faces[p.index],
                'sourceVertexID': ids[vertex], 'position': list(mesh.vertices[vertex].co),
                'source': origin_by_loop.get(loop), 'faceSmooth': p.use_smooth,
                'storedRetainedNormal': stored[loop].tolist(), 'actualCornerNormal': actual[loop].tolist(),
                'expectedRawNormal': expected_by_loop[loop].tolist() if loop in expected_by_loop else None,
                'actualVsStoredVectorError': float(np.linalg.norm(actual[loop] - stored[loop]))}

    worst_records = []
    for loop in worst:
        vertex = mesh.loops[loop].vertex_index; fan_loops = fan(loop)
        average = unit(stored[fan_loops].mean(axis=0))
        record = corner(loop)
        record['smoothFanLoops'] = [corner(i) for i in fan_loops]
        record['normalizedFanMeanStoredNormal'] = average.tolist()
        record['actualVsFanMeanError'] = float(np.linalg.norm(actual[loop] - average))
        record['expectedVsFanMeanError'] = float(np.linalg.norm(expected_by_loop[loop] - average))
        record['allIncidentCorners'] = [corner(i) for i in vertex_loops[vertex]]
        record['incidentEdges'] = [{'edge': e.index, 'vertices': list(e.vertices), 'sharp': sharp[e.index],
                                    'neighborPolygons': edge_faces[e.index]}
                                   for e in mesh.edges if vertex in e.vertices]
        record['allRawVerticesAtCoordinate'] = coordinate_sources[tuple(origin_by_loop[loop]['rawPosition'])]
        worst_records.append(record)

    # At most three tiny references, at the single worst vertex. Their geometry
    # is the exact one-ring triangles. Changes are confined to unlinked scratch
    # meshes to isolate smooth-fan averaging from single-corner codec error.
    target = worst[0]; target_vertex = mesh.loops[target].vertex_index
    selected_faces = sorted({loop_face[i] for i in vertex_loops[target_vertex]})
    assert len(selected_faces) <= 128
    original_loops = [i for f in selected_faces for i in mesh.polygons[f].loop_indices]
    target_offset = original_loops.index(target)
    references = []
    for mode in ('same-one-ring-shared-edges', 'same-one-ring-all-sharp', 'same-triangles-disconnected-corners'):
        reference = bpy.data.meshes.new('READONLY_NORMAL_REFERENCE_' + mode)
        if mode == 'same-triangles-disconnected-corners':
            positions = [tuple(mesh.vertices[mesh.loops[i].vertex_index].co) for i in original_loops]
            faces = []; offset = 0
            for f in selected_faces:
                count = len(mesh.polygons[f].vertices); faces.append(tuple(range(offset, offset + count))); offset += count
        else:
            vertices = sorted({v for f in selected_faces for v in mesh.polygons[f].vertices})
            mapping = {v: i for i, v in enumerate(vertices)}
            positions = [tuple(mesh.vertices[v].co) for v in vertices]
            faces = [tuple(mapping[v] for v in mesh.polygons[f].vertices) for f in selected_faces]
        reference.from_pydata(positions, [], faces); reference.update()
        for p, original_face in zip(reference.polygons, selected_faces):
            p.use_smooth = mesh.polygons[original_face].use_smooth
        if mode != 'same-triangles-disconnected-corners':
            edge_lookup = {tuple(sorted(e.vertices)): sharp[e.index] for e in mesh.edges}
            for edge in reference.edges:
                original_edge = tuple(sorted(vertices[v] for v in edge.vertices))
                edge.use_edge_sharp = mode == 'same-one-ring-all-sharp' or edge_lookup[original_edge]
        requested = stored[original_loops].copy()
        reference.normals_split_custom_set(requested.tolist())
        decoded = np.array([list(n.vector) for n in reference.corner_normals])
        references.append({'mode': mode, 'vertices': len(reference.vertices), 'faces': len(reference.polygons),
                           'targetLoopOffset': target_offset, 'targetDecodedNormal': decoded[target_offset].tolist(),
                           'targetRequestedNormal': requested[target_offset].tolist(),
                           'targetVectorError': float(np.linalg.norm(decoded[target_offset] - requested[target_offset])),
                           'allCornerMaximumVectorError': float(np.linalg.norm(decoded - requested, axis=1).max()),
                           'customNormalAttributeInventory': [{'name': a.name, 'domain': a.domain, 'type': a.data_type}
                                                             for a in reference.attributes if 'normal' in a.name]})
        bpy.data.meshes.remove(reference)
    assert np.array_equal(stored, np.array([list(row.vector) for row in mesh.attributes['RetainedSourceNormal'].data]))
    assert np.array_equal(actual, np.array([list(row.vector) for row in mesh.corner_normals]))
    assert sharp == [e.use_edge_sharp for e in mesh.edges]
    assert sha(NATIVE) == NATIVE_SHA and sha(DONOR) == DONOR_SHA
    result = {'accepted': False, 'status': 'READ_ONLY_NORMAL_CAUSE_DIAGNOSTIC',
              'candidate': {'path': str(NATIVE.relative_to(ROOT)), 'sha256': NATIVE_SHA},
              'donorSHA256': DONOR_SHA, 'recipeSHA256': sha(__file__),
              'blenderVersion': bpy.app.version_string, 'blenderBuildHash': bpy.app.build_hash.decode(),
              'attributes': [{'name': a.name, 'domain': a.domain, 'type': a.data_type} for a in mesh.attributes],
              'protectedTriangles': len(loops) // 3, 'protectedCorners': len(loops),
              'storedVsRawMaximumVectorError': float(np.linalg.norm(stored[loops] - expected, axis=1).max()),
              'actualVsRawMaximumVectorError': float(errors.max()),
              'actualErrorPercentiles': dict(zip(['50', '90', '99', '100'], np.percentile(errors, [50, 90, 99, 100]).tolist())),
              'actualCornersExceeding2eMinus6': int((errors > 2e-6).sum()),
              'worstCorners': worst_records, 'tinyReferencesAtWorstVertex': references,
              'nativeFileAndMeshNormalAttributesUnchanged': True,
              'limits': ['No candidate rewrite, save, render or art judgment.',
                         'Scratch one-ring boundaries can change geometric fan bases; shared-vs-sharp-vs-disconnected results must be interpreted with fan records.',
                         'Official source mechanism is a hypothesis until these actual diagnostic measurements run.']}
    (out / 'normal-diagnostic.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k not in ('worstCorners', 'attributes')}))


if __name__ == '__main__':
    main()
