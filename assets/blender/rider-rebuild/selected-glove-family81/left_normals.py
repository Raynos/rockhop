"""Actual41 L320543: immutable five-face proof and explicit target corner seam.

Construction may classify the undefined source average only with exact fan
ancestry. A native target must call apply_seam before shading/export admission.
"""
import hashlib
import os
from pathlib import Path
import runpy

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
VERTEX = 320543
FACES = (518306, 518310, 561015, 561016, 561020)
WITNESS = ROOT/'assets/blender/rider-rebuild/selected-production-family31/witness.py'
WITNESS_SHA = '95c7813b503c7d5539b2d7082e14229d484060bacefae294d28160e2c30755d5'


def oriented_key(ids):
    ids = tuple(map(int, ids)); start = ids.index(min(ids))
    return ids[start:]+ids[:start]


def source_fan(a):
    triangles = a['triangles']; actual = np.flatnonzero((triangles == VERTEX).any(axis=1))
    assert tuple(actual) == FACES, 'The known original five-face fan changed'
    assert np.array_equal(a['vertexNormals'][VERTEX], np.zeros(3)), 'Source singular normal changed'
    corners = [int(a['triangleLoopIds'][face, np.flatnonzero(triangles[face] == VERTEX)[0]]) for face in FACES]
    assert np.array_equal(a['cornerNormals'][corners], np.zeros((5, 3))), 'Known zero source corners changed'
    points = a['positions'][triangles[list(FACES)]].astype(np.float64)
    cross = np.cross(points[:, 1]-points[:, 0], points[:, 2]-points[:, 0]); lengths = np.linalg.norm(cross, axis=1)
    assert np.isfinite(lengths).all() and (lengths > 0).all(), 'Source face geometry is undefined'
    normals = cross/lengths[:, None]
    return {'originalVertexId': VERTEX, 'sourceFaceIds': list(FACES), 'sourceCornerIds': corners,
            'orientedOriginalTriangles': triangles[list(FACES)].tolist(), 'geometricNormals': normals.tolist(),
            'areasM2': (lengths/2).tolist(), 'sourceVertexNormal': a['vertexNormals'][VERTEX].tolist(),
            'sourceCornerNormals': a['cornerNormals'][corners].tolist(),
            'opposingFaceGroups': [np.asarray(FACES)[(normals@normals[0]) > 0].tolist(),
                                   np.asarray(FACES)[(normals@normals[0]) <= 0].tolist()],
            'classification': 'Undefined native source average; five nonzero-area oriented faces. Never an orphan or fitted-glove pass.'}


def apply_seam(target, original_vertex_ids, a):
    """Call only on the derived L target, after full source-aware construction.

    a is the admitted raw-array dictionary plus its original groupNames list.
    No source mutation or save. Keep geometry/UV/full-field identity. Exporters
    may split the five corner normals into coincident render vertices naturally.
    """
    assert os.environ.get('ROCKHOP_GENERATION_CONTROLLER_PID'), 'Original parent guard required'
    import bpy

    assert target.type == 'MESH' and target.name != 'ActualSelectedGlove.L'
    proof = source_fan(a); mesh = target.data; ids = np.asarray(original_vertex_ids, np.int64)
    assert len(ids) == len(mesh.vertices) and ((ids >= 0) & (ids < len(a['positions']))).all()
    assert len(np.flatnonzero(ids == VERTEX)) == 1, 'Apply corner seam before any render-vertex duplication'
    mesh.calc_loop_triangles()
    assert len(mesh.loop_triangles) == len(mesh.polygons) and all(len(p.vertices) == 3 for p in mesh.polygons)
    points = np.empty((len(mesh.vertices), 3), np.float32); mesh.vertices.foreach_get('co', points.ravel())
    assert np.array_equal(points, a['positions'][ids]), 'Seam target lost exact source positions'
    faces = np.empty((len(mesh.loop_triangles), 3), np.int32); mesh.loop_triangles.foreach_get('vertices', faces.ravel())
    loop_ids = np.empty_like(faces); mesh.loop_triangles.foreach_get('loops', loop_ids.ravel())
    source_triangles = ids[faces]; incident = np.flatnonzero((source_triangles == VERTEX).any(axis=1))
    expected = {oriented_key(a['triangles'][face]): face for face in FACES}
    assert len(incident) == 5 and {oriented_key(source_triangles[face]) for face in incident} == set(expected)
    assert hashlib.sha256(WITNESS.read_bytes()).hexdigest() == WITNESS_SHA
    witness = runpy.run_path(str(WITNESS)); before = witness['source'](target)
    # Verify actual named memberships before changing any shading attribute.
    assert [group.name for group in target.vertex_groups] == a['groupNames']
    for vertex, source_id in zip(mesh.vertices, ids):
        begin, end = a['fieldOffsets'][source_id:source_id+2]
        expected_fields = list(zip(a['fieldIndices'][begin:end].tolist(), a['fieldWeights'][begin:end].tolist()))
        assert [(g.group, g.weight) for g in vertex.groups] == expected_fields
    normals = np.empty((len(mesh.corner_normals), 3), np.float32); mesh.corner_normals.foreach_get('vector', normals.ravel())
    edited, records = [], []
    for face in incident:
        source_face = expected[oriented_key(source_triangles[face])]
        p = points[faces[face]].astype(np.float64)
        normal = np.cross(p[1]-p[0], p[2]-p[0]); normal /= np.linalg.norm(normal)
        source_normal = np.asarray(proof['geometricNormals'][FACES.index(source_face)])
        assert float(normal@source_normal) >= 1-1e-12
        corner = int(loop_ids[face, np.flatnonzero(source_triangles[face] == VERTEX)[0]])
        normals[corner] = normal.astype(np.float32); edited.append(corner)
        records.append({'targetFaceId': int(face), 'sourceFaceId': source_face, 'targetCornerId': corner,
                        'geometricNormal': normal.tolist(), 'sourceGeometricNormalDot': float(normal@source_normal)})
    assert np.isfinite(normals).all() and (np.linalg.norm(normals, axis=1) > 0).all(), 'Other target zero shading normal remains'
    mesh.normals_split_custom_set(normals.tolist()); mesh.update()
    after = np.empty_like(normals); mesh.corner_normals.foreach_get('vector', after.ravel())
    assert np.isfinite(after).all() and (np.linalg.norm(after, axis=1) > 0).all(), 'Final target shading contains a zero normal'
    for record in records:
        actual = after[record['targetCornerId']].astype(np.float64); actual /= np.linalg.norm(actual)
        assert float(actual@record['geometricNormal']) >= 1-1e-6, 'Authored seam direction not stored'
    assert witness['source'](target) == before, 'Seam changed target geometry, UVs, named fields, materials or bind'
    return {'status': 'DERIVED_LEFT_FIVE_CORNER_HARD_NORMAL_SEAM_AUTHORED_UNACCEPTED',
            'acceptedArt': False, 'sourceFan': proof, 'targetCorners': records,
            'allFinalCornerNormalsNonzero': True, 'geometryUVFieldsAndBindUnchanged': True,
            'sourceMutation': False, 'limits': 'Shading singularity treatment only; source fold, wearer, bidirectional surface, bake and moving gates remain open.'}
