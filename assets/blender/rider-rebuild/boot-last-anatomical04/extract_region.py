"""Read actual selected boots and canonical feet; no object/data mutation.

Parent owns serial CPU2 lease. No geometry, bake, render or native save.
blender -b -t 2 --python-exit-code 1 --python THIS -- FRESH_OUTPUT
Output stays in this lane's evidence directory. Source native is never saved.
"""
import hashlib
import json
from pathlib import Path
import sys

import bpy
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
CONFIG_PATH = HERE / 'inputs.json'
CONFIG = json.loads(CONFIG_PATH.read_text())


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as handle:
        while block := handle.read(1024 * 1024):
            digest.update(block)
    return digest.hexdigest()


def pin(row):
    path = ROOT / row['path']
    assert sha(path) == row['sha256'], ('Changed input', row['path'])
    return path


def arrays(obj):
    assert obj.type == 'MESH' and obj.matrix_world.is_identity
    assert all(len(p.vertices) == 3 for p in obj.data.polygons)
    vertices = np.empty(len(obj.data.vertices) * 3, dtype=np.float64)
    faces = np.empty(len(obj.data.polygons) * 3, dtype=np.int32)
    obj.data.vertices.foreach_get('co', vertices)
    obj.data.polygons.foreach_get('vertices', faces)
    return vertices.reshape((-1, 3)), faces.reshape((-1, 3))


def state(obj):
    """Byte hashes only; no giant duplicate JSON of the selected source."""
    vertices, faces = arrays(obj)
    uv = np.empty(len(obj.data.loops) * 2, dtype=np.float32)
    assert obj.data.uv_layers.active is not None
    obj.data.uv_layers.active.data.foreach_get('uv', uv)
    packed = {}
    for material in obj.data.materials:
        assert material and material.use_nodes
        for node in material.node_tree.nodes:
            if node.type == 'TEX_IMAGE' and node.image and node.image.packed_file:
                packed[node.image.name] = hashlib.sha256(node.image.packed_file.data).hexdigest()
    return {'vertices': len(vertices), 'faces': len(faces),
            'positionSHA256': hashlib.sha256(vertices.tobytes()).hexdigest(),
            'triangleSHA256': hashlib.sha256(faces.tobytes()).hexdigest(),
            'cornerUVSHA256': hashlib.sha256(uv.tobytes()).hexdigest(),
            'packedImages': packed, 'visibility': [obj.hide_render, obj.hide_viewport, obj.hide_get()],
            'vertexGroups': [g.name for g in obj.vertex_groups],
            'modifiers': [(m.name, m.type, m.object.name if m.type == 'ARMATURE' and m.object else None)
                          for m in obj.modifiers]}


def section(vertices, faces, axis, station, source_rows=None):
    """Triangle-plane intersection; retain exact source polygon ancestry.

    Quantization is ONLY graph endpoint identification at 1 micrometre. Stored
    positions are unquantized means of actual intersections; no mesh is edited.
    A loop is called closed only when every actual graph vertex has degree two.
    Branches/open curves remain explicit. Inner/outer interpretation is left to
    the parent, not inferred from aggregate nearest-normal signs.
    """
    distances = vertices[:, axis] - station
    if source_rows is None:
        source_rows = np.arange(len(faces), dtype=np.int32)
    candidates = np.where((distances[faces].min(1) <= 0.) &
                          (distances[faces].max(1) >= 0.))[0]
    face = faces[candidates]
    endpoints, triangle_rows = [], []
    for a, b in ((0, 1), (1, 2), (2, 0)):
        da, db = distances[face[:, a]], distances[face[:, b]]
        crossing = (da < 0.) != (db < 0.)
        ids = np.where(crossing)[0]
        alpha = da[ids] / (da[ids] - db[ids])
        points = vertices[face[ids, a]] + alpha[:, None] * (
            vertices[face[ids, b]] - vertices[face[ids, a]])
        endpoints.append(points)
        triangle_rows.append(source_rows[candidates[ids]])
    if not endpoints or not sum(len(p) for p in endpoints):
        return {'stationM': station, 'axis': axis, 'segments': 0, 'curves': []}
    points, ancestry = np.concatenate(endpoints), np.concatenate(triangle_rows)
    order = np.argsort(ancestry, kind='stable')
    points, ancestry = points[order], ancestry[order]
    unique_rows, row_counts = np.unique(ancestry, return_counts=True)
    assert np.all(row_counts == 2), ('Degenerate plane/triangle contact', axis, station,
                                     unique_rows[row_counts != 2].tolist())
    segments = points.reshape((-1, 2, 3))
    keep = np.linalg.norm(segments[:, 1] - segments[:, 0], axis=1) > 1e-9
    segments, unique_rows = segments[keep], unique_rows[keep]
    keys, inverse = np.unique(np.rint(segments.reshape((-1, 3)) / 1e-6).astype(np.int64),
                              axis=0, return_inverse=True)
    representatives = np.zeros((len(keys), 3), dtype=np.float64)
    np.add.at(representatives, inverse, segments.reshape((-1, 3)))
    representatives /= np.bincount(inverse)[:, None]
    edges = inverse.reshape((-1, 2))
    adjacency = [[] for _ in keys]
    for i, (a, b) in enumerate(edges):
        if a != b:
            adjacency[int(a)].append((int(b), i))
            adjacency[int(b)].append((int(a), i))
    seen, curves = set(), []
    for seed in range(len(keys)):
        if seed in seen:
            continue
        pending, component, component_edges = [seed], set(), set()
        while pending:
            node = pending.pop()
            if node in component:
                continue
            component.add(node)
            for neighbor, edge in adjacency[node]:
                component_edges.add(edge)
                if neighbor not in component:
                    pending.append(neighbor)
        seen.update(component)
        closed = len(component) >= 3 and all(len(adjacency[n]) == 2 for n in component)
        if closed:
            walk, previous, current = [], None, min(component)
            while current not in walk:
                walk.append(current)
                next_nodes = [n for n, _ in adjacency[current] if n != previous]
                previous, current = current, next_nodes[0]
            assert len(walk) == len(component)
        else:
            walk = sorted(component)
        p = representatives[walk]
        curves.append({'closed': closed, 'vertices': len(walk),
                       'degreeHistogram': {str(d): sum(len(adjacency[n]) == d for n in component)
                                           for d in sorted({len(adjacency[n]) for n in component})},
                       'localBoundsM': [p.min(0).tolist(), p.max(0).tolist()],
                       'pointsLongHeightTransverseM': p.tolist(),
                       'sourceTriangleRows': sorted(int(unique_rows[i]) for i in component_edges)})
    curves.sort(key=lambda c: c['vertices'], reverse=True)
    return {'stationM': station, 'axis': axis, 'segments': len(segments), 'curves': curves}


def topology(vertices, faces):
    """Report actual disconnected features and open rims without naming them."""
    edges = np.concatenate((faces[:, [0, 1]], faces[:, [1, 2]], faces[:, [2, 0]]))
    edges.sort(axis=1)
    unique, counts = np.unique(edges, axis=0, return_counts=True)
    parent = np.arange(len(vertices), dtype=np.int32)

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = int(parent[a])
        return a

    for a, b in unique:
        a, b = find(int(a)), find(int(b))
        if a != b:
            parent[max(a, b)] = min(a, b)
    labels = np.array([find(i) for i in range(len(vertices))], dtype=np.int32)
    keys, sizes = np.unique(labels, return_counts=True)
    components = []
    for index in np.argsort(sizes)[::-1][:30]:
        rows = np.where(labels == keys[index])[0]
        points = vertices[rows]
        components.append({'vertices': len(rows), 'minimumSourceVertexRow': int(rows.min()),
                           'localBoundsM': [points.min(0).tolist(), points.max(0).tolist()]})
    boundary = unique[counts == 1]
    return {'connectedComponents': len(keys), 'largestComponents': components,
            'boundaryEdges': len(boundary), 'nonManifoldEdgesAboveTwoFaces': int(np.sum(counts > 2)),
            'boundaryVertexRows': np.unique(boundary).tolist()}


def rest(rig):
    return [(b.name, tuple(b.head_local), tuple(b.tail_local),
             tuple(tuple(row) for row in b.matrix_local)) for b in rig.data.bones]


def main():
    args = sys.argv[sys.argv.index('--') + 1:]
    assert len(args) == 1
    out = Path(args[0]).resolve()
    assert out.is_relative_to(ROOT / CONFIG['outputRoot']) and not out.exists()
    paths = {name: pin(row) for name, row in CONFIG['inputs'].items()}
    working = pin(CONFIG['workingOutfit'])
    # Open the exact assembled context, not a duplicate source or author fixture.
    bpy.ops.wm.open_mainfile(filepath=str(working))
    body, rig = (bpy.data.objects[CONFIG['objects'][name]] for name in ('body', 'rig'))
    assert len(rig.data.bones) == 75 and rig.animation_data is None
    assert all(b.matrix_basis.is_identity for b in rig.pose.bones)
    before_rest = rest(rig)
    body_positions = np.array([tuple(v.co) for v in body.data.vertices], dtype=np.float64)
    body_weights = [[(g.group, g.weight) for g in v.groups] for v in body.data.vertices]
    foot_source = dict(np.load(paths['native-body.npz']))
    source_ids = body.data.attributes['_SOURCE_VERTEX_ID']
    displayed_by_source_id = {int(row.value): np.array(v.co) for row, v in
                              zip(source_ids.data, body.data.vertices) if row.value >= 0}
    assert len(displayed_by_source_id) == sum(row.value >= 0 for row in source_ids.data)
    outline = json.loads(paths['target-foot-outline.json'].read_text())
    report = {'accepted': False, 'stage': 'READ_ONLY_ACTUAL_REGION_EXTRACTION',
              'recipeSHA256': sha(__file__), 'inputs': CONFIG['inputs'],
              'workingOutfit': CONFIG['workingOutfit'], 'sides': {},
              'sectionRationale': CONFIG['sectionRationale'], 'limits': CONFIG['limits']}
    out.mkdir()
    for side, name in CONFIG['objects']['boots'].items():
        obj = bpy.data.objects[name]
        before = state(obj)
        expected_maps = {CONFIG['inputs'][key]['sha256'] for key in
                         ('baseColorTexture.png', 'metallicRoughnessTexture.png')}
        assert expected_maps <= set(before['packedImages'].values())
        vertices, faces = arrays(obj)
        spec = outline['sides'][side]
        frame = np.array(spec['footFrame'])
        origin = np.array(spec['footReferenceOrigin'])
        assert np.linalg.det(frame) > .999999
        ankle = rig.data.bones['DEF-foot.' + side].head_local
        toe = rig.data.bones['DEF-toe.' + side].head_local
        assert np.linalg.norm(np.array(ankle) - spec['ankleHead']) < 1e-7
        assert np.linalg.norm(np.array(toe) - spec['toeJointHead']) < 1e-7
        local = (vertices - origin) @ frame
        feet = (foot_source['vertices'] - origin) @ frame
        # Broad own-foot domain; never a changed/hidden body. All canonical
        # triangles crossing this domain stay intact, including lower shin.
        foot_vertex_mask = ((feet[:, 0] > -.25) & (feet[:, 0] < .10) &
                            (feet[:, 1] < .17) & (feet[:, 1] > -.01) &
                            (np.abs(feet[:, 2]) < .10))
        foot_face_rows = np.where(np.all(foot_vertex_mask[foot_source['faces']], axis=1))[0]
        foot_faces = foot_source['faces'][foot_face_rows]
        # The selected-head integration reindexes the body. Match the actual
        # retained native source IDs, never assume current rows equal old rows.
        canonical_rows = np.where(foot_vertex_mask)[0]
        displayed = np.array([displayed_by_source_id[int(foot_source['nativeSourceVertexIds'][i])]
                              for i in canonical_rows])
        canonical_difference = float(np.max(np.abs(displayed - foot_source['vertices'][canonical_rows])))
        assert canonical_difference < 1e-7, ('Actual displayed foot differs', side, canonical_difference)
        result = {'object': name, 'sourceState': before,
                  'actualDisplayedCanonicalFootMaximumDeltaM': canonical_difference,
                  'footFrame': spec['footFrame'], 'footOrigin': spec['footReferenceOrigin'],
                  'medialTransverseSign': 1 if side == 'R' else -1,
                  'localBoundsM': [local.min(0).tolist(), local.max(0).tolist()],
                  'topology': topology(local, faces), 'longitudinal': [], 'height': []}
        for axis, stations, key in ((0, CONFIG['longitudinalSectionsM'], 'longitudinal'),
                                    (1, CONFIG['heightSectionsM'], 'height')):
            for station in stations:
                result[key].append({'boot': section(local, faces, axis, station),
                                    'canonicalFoot': section(feet, foot_faces, axis, station, foot_face_rows)})
        assert state(obj) == before
        path = out / (side + '-sections.json')
        path.write_text(json.dumps(result, separators=(',', ':')) + '\n')
        report['sides'][side] = {'path': str(path.relative_to(ROOT)), 'sha256': sha(path),
                                'sourceState': before, 'localBoundsM': result['localBoundsM'],
                                'topologySummary': {k: v for k, v in result['topology'].items()
                                                    if k != 'boundaryVertexRows'},
                                'sectionLoopSummary': {key: [
                                    {'stationM': s['boot']['stationM'],
                                     'bootCurveSizesClosed': [[c['vertices'], c['closed']] for c in s['boot']['curves']],
                                     'footCurveSizesClosed': [[c['vertices'], c['closed']] for c in s['canonicalFoot']['curves']]}
                                    for s in result[key]] for key in ('longitudinal', 'height')}}
    assert np.array_equal(np.array([tuple(v.co) for v in body.data.vertices]), body_positions)
    assert [[(g.group, g.weight) for g in v.groups] for v in body.data.vertices] == body_weights
    assert rest(rig) == before_rest and not body.hide_render
    assert all(sha(ROOT / row['path']) == row['sha256'] for row in CONFIG['inputs'].values())
    assert sha(working) == CONFIG['workingOutfit']['sha256']
    report['sourceNativeBodyWeightsRestAndBootDataUnchanged'] = True
    (out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'accepted': False, 'report': str((out / 'report.json').relative_to(ROOT)),
                      'actualSectionsSaved': True, 'noModelBakeRenderOrSave': True}))


if __name__ == '__main__':
    main()
