"""Read-only finite body crossings for saved15 at six actual bike poses.

Parent original guard only: blender -b -t 2 --python-exit-code 1 --python
posed_contact15.py -- FRESH_OUTPUT. No reconstruction, solve or native save.
"""
import ast
from collections import Counter, defaultdict
import hashlib
import json
import os
from pathlib import Path
import sys

import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parents[4]
PREFIX = 'assets/blender/rider-rebuild/selected-hoodie-joints77/'
DATA = 'harness/out/rider-rebuild/selected-hoodie-joints77/'
PINS = {
    'receiverReceipt': (DATA+'receiver15/receiver.json', 'd92c1060f855c5daf3dc199404250b63af3bd577253dfb0fb8162bf8b41b1a0a'),
    'receiverArrays': (DATA+'receiver15/receiver.npz', 'de556ac10b40fd625b922e072d49709dd40ccc99dc28c0df9274cbdb149b5305'),
    'construction': (DATA+'receiver15/connected-cap.json', '193db2d2cea4de7ccb0372f6560109177b73a75d1904d7c3b70453c7f024508b'),
    'bodyReceipt': (DATA+'body-guide01/actual-body-fields.json', '8fb18ac1722439375e3fa30a3b72b9696fb8d2459d4747892d3a454e6f2be6e3'),
    'bodyArrays': (DATA+'body-guide01/actual-body-fields.npz', 'cfb58ca2e8bd6d9e933b7a1a22a3405080dd219aacfb5acfe97a3a079dafc4f8'),
    'source47Receipt': ('harness/out/rider-rebuild/selected-sleeve-component47/intake01/intake-qualified.json', '55adfeb1c0a6ff43d640338af1062d05c2893b56695cc94fa79a46144fd532c5'),
    'game': ('harness/out/rider-rebuild/selected-authoring-motion11/gameplay-converted02/measured-gameplay-native-world.json', 'f3e0444768655bf72500a9245745a559586a7717b3f6cb6b600b6e9d1d05c153'),
    'completedInspection': (DATA+'inspect15/field-inspection.json', '8fc59001effb326fb4603bf3574b505795d09e313d73487e6a1ca2f28c119057'),
    'completedViews': (DATA+'views15/views.json', '37358f20bdc893ccd33a8de4c443efa3e917a47a6932d0994e7ff3236915dbf6'),
    'author': (PREFIX+'author.py', '9477ea7896d42a91f0c91c18aed760d2987aabb4b9bd8953ceccf95220361fb7'),
    'views15': (PREFIX+'connected_cap_views15.py', '346291ea12a0c39b3cb141400bafb4217b32947a799af869c4256c8499a7cca0'),
    'viewsBase': (PREFIX+'connected_cap_views.py', 'b34bfe8b3ba72247629238eb769f3c823879a578aac573f056212e279a2a0277'),
    'binding': (PREFIX+'connected_cap_binding15.py', 'fbbc65482ce51632ae657c0693cc6515fce8807af197bf463a936e9128f25b40'),
    'crossing': ('assets/blender/rider-rebuild/glove-over-sleeve08/author.py', '42d428f600bdbd82c37d0024f147d57a29a1301560bc9a1fa3cd86389685d3d2'),
    'guard': ('assets/blender/hero-remaster/generation-comparison-2026-10-03/user-agent2/run_bounded96.py', 'cf8acd15d8b7484480bee74d23892be815d955ffd87115d3da8ed228ffb3d916'),
}


def pin(path):
    path = Path(path).resolve()
    return {'path': str(path.relative_to(ROOT)), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}


def checked(key):
    path, digest = PINS[key]
    assert pin(ROOT/path) == {'path': path, 'sha256': digest}, key
    return ROOT/path


def frozen_function(key, name):
    # Execute exactly one function; never import authoring/main/Pillow side effects.
    path = checked(key); tree = ast.parse(path.read_text())
    nodes = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name]
    assert len(nodes) == 1
    scope = {'np': np}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(path), 'exec'), scope)
    return scope[name]


def bounds(points):
    return [points.min(0).tolist(), points.max(0).tolist()]


def components(ids, faces):
    # Connectivity is shared actual garment edges, never spatial proximity.
    owner = {}; adjacent = defaultdict(set)
    for i in ids:
        for u, v in zip(faces[i], np.roll(faces[i], -1)):
            edge = tuple(sorted((int(u), int(v))))
            if edge in owner:
                adjacent[i].add(owner[edge]); adjacent[owner[edge]].add(i)
            else: owner[edge] = i
    unseen = set(ids); result = []
    while unseen:
        seed = min(unseen); unseen.remove(seed); stack = [seed]; group = []
        while stack:
            i = stack.pop(); group.append(i)
            for j in adjacent[i] & unseen: unseen.remove(j); stack.append(j)
        result.append(sorted(group))
    return sorted(result, key=lambda group: (-len(group), group[0]))


def measure(p, f, q, g, strict_cross):
    assert np.isfinite(p).all() and np.isfinite(q).all()
    normals = [np.cross(x[t[:, 1]]-x[t[:, 0]], x[t[:, 2]]-x[t[:, 0]]) for x, t in ((p, f), (q, g))]
    magnitudes = [np.linalg.norm(n, axis=1) for n in normals]
    valid = [np.flatnonzero(length > 1e-14) for length in magnitudes]
    invalid = [np.flatnonzero(length <= 1e-14) for length in magnitudes]
    trees = [BVHTree.FromPolygons([Vector(v) for v in x], t[ok].tolist(), all_triangles=True) if len(ok) else None
             for x, t, ok in zip((p, q), (f, g), valid)]
    candidates = sorted(trees[0].overlap(trees[1])) if all(tree is not None for tree in trees) else []
    pairs = []; signed_body = []; signed_garment = []
    for ia, ib in candidates:
        i, j = int(valid[0][ia]), int(valid[1][ib]); a, b = p[f[i]], q[g[j]]
        if strict_cross(a, b):
            pairs.append((i, j))
            signed_body.append((a-b[0]) @ (normals[1][j]/magnitudes[1][j]))
            signed_garment.append((b-a[0]) @ (normals[0][i]/magnitudes[0][i]))
    return (np.asarray(pairs, dtype=np.int32).reshape(-1, 2),
            np.asarray(signed_body, dtype=np.float64).reshape(-1, 3),
            np.asarray(signed_garment, dtype=np.float64).reshape(-1, 3), invalid, magnitudes, len(candidates))


def main(output):
    controller = int(os.environ['ROCKHOP_GENERATION_CONTROLLER_PID'])
    assert controller == os.getppid(); os.kill(controller, 0)
    assert os.environ['OPENBLAS_NUM_THREADS'] == os.environ['OMP_NUM_THREADS'] == '2'
    assert sys.version_info[:2] == (3, 13) and np.__version__ == '2.3.4'
    output = Path(output).resolve()
    assert output.is_relative_to(ROOT/DATA) and not output.exists()
    self_pin = pin(__file__)
    for key in PINS: checked(key)
    read = lambda key: json.loads(checked(key).read_text())
    receipt, body, views, inspection, game = [read(k) for k in ('receiverReceipt', 'bodyReceipt', 'completedViews', 'completedInspection', 'game')]
    pinfo = lambda key: {'path': PINS[key][0], 'sha256': PINS[key][1]}
    assert receipt['receiver'] == pinfo('receiverArrays') and body['arrays'] == pinfo('bodyArrays')
    assert receipt['connectedCapBinding']['bodyGuide'] == pinfo('bodyReceipt')
    assert receipt['construction'] == pinfo('construction')
    assert receipt['source47Receipt'] == body['sourceReceipt'] == pinfo('source47Receipt')
    for prior in (views, inspection):
        assert prior['receiverReceipt'] == pinfo('receiverReceipt') and prior['bindingVerifier'] == pinfo('binding')
        assert prior['gameplayMatrices'] == pinfo('game')
    assert inspection['keys'] == 482 and views['recipe'] == pinfo('views15')
    a, b = np.load(checked('receiverArrays')), np.load(checked('bodyArrays'))
    f, _, polygon_ids = frozen_function('author', 'triangulate')(a); g = b['triangles']
    assert len(f) == 32084 and len(g) == 77974
    pose = frozen_function('viewsBase', 'pose'); strict_cross = frozen_function('crossing', 'strict_cross')
    names = game['boneNames']; rest = {row['name']: row for row in game['nativeRest']['bones']}
    assert len(names) == len(set(names)) == len(rest) == len(body['rest']) == 75
    assert all(row[4] == rest[row[0]]['matrix'] and row[1] == rest[row[0]]['parent'] for row in body['rest'])
    assert len(a['groupNames']) == len(b['groupNames']) == 71
    inverse = np.linalg.inv(np.asarray([rest[name]['matrix'] for name in names]))
    output.mkdir(parents=True); rows = []
    for action in game['actions']:
        for frame in (121, 129, 193):
            matrices = np.asarray(action['nativeWorldMatrices'][frame-1]) @ inverse
            p = pose(a['positions'], a['namedFields'], a['groupNames'], names, matrices)
            q = pose(b['positions'], b['normalizedNamedFields'], b['groupNames'], names, matrices)
            pairs, sb, sg, invalid, magnitudes, tested = measure(p, f, q, g, strict_cross)
            patches = []
            for ids in components(np.unique(pairs[:, 0]).tolist(), f):
                pair_ids = np.flatnonzero(np.isin(pairs[:, 0], ids)); body_ids = np.unique(pairs[pair_ids, 1])
                vertices = np.unique(f[ids]); polygons = polygon_ids[ids]; first = int(pair_ids[0]); i, j = pairs[first]
                patches.append({'garmentTriangleIds': ids, 'crossingPairCount': len(pair_ids),
                    'bodyTriangleIds': body_ids.tolist(), 'restBoundsM': bounds(a['positions'][vertices]),
                    'posedBoundsM': bounds(p[vertices]), 'bodyPosedBoundsM': bounds(q[np.unique(g[body_ids])]),
                    'garmentFaceRoles': dict(Counter(a['faceRoles'][polygons].tolist())),
                    'garmentWallKeys': dict(Counter(a['faceWallKey'][polygons].tolist())),
                    'garmentVertexRoles': dict(Counter(a['vertexRoles'][vertices].tolist())),
                    'firstWitness': {'pairRow': first, 'triangleIds': [int(i), int(j)], 'garmentVertexIds': f[i].tolist(),
                        'bodyVertexIds': g[j].tolist(), 'bodyNativeIds': b['nativeIds'][g[j]].tolist(),
                        'bodyRegionIds': b['regionIds'][g[j]].tolist(), 'garmentWorldXYZ': p[f[i]].tolist(),
                        'bodyWorldXYZ': q[g[j]].tolist(), 'garmentSignedBodyPlaneM': sb[first].tolist(),
                        'bodySignedGarmentPlaneM': sg[first].tolist()}})
            artifact = output/f'{action["bike"]}-{frame}-contacts.npz'
            np.savez_compressed(artifact, garmentPosed=p, bodyPosed=q, garmentTriangles=f, bodyTriangles=g,
                garmentPolygonIds=polygon_ids, crossingTrianglePairs=pairs, garmentSignedBodyPlaneM=sb,
                bodySignedGarmentPlaneM=sg, garmentDegenerateTriangleIds=invalid[0], bodyDegenerateTriangleIds=invalid[1])
            row = {'bike': action['bike'], 'action': action['name'], 'frame': frame, 'arrays': pin(artifact),
                   'strictCrossingPairs': len(pairs), 'testedBroadphasePairs': tested, 'allBroadphasePairsInspected': True,
                   'crossingPatches': patches, 'degenerates': [
                       {'surface': label, 'triangleIds': ids.tolist(), 'triangleAreasM2': (length[ids]/2).tolist()}
                       for label, ids, length in zip(('garment', 'body'), invalid, magnitudes)]}
            rows.append(row)
            print(json.dumps({k: row[k] for k in ('bike', 'frame', 'strictCrossingPairs', 'testedBroadphasePairs')}), flush=True)
    assert len(rows) == 6 and {r['bike'] for r in rows} == {'rookie', 'pro'}
    for key in PINS: checked(key)
    assert pin(__file__) == self_pin
    report = {'status': 'SAVED15_SIX_POSE_FINITE_TRIANGLE_CROSSINGS_MEASURED_UNACCEPTED', 'recipe': self_pin,
        'inputs': {key: pinfo(key) for key in PINS}, 'inputsAndSourceUnchanged': True, 'rows': rows,
        'runtime': {'blender': bpy.app.version_string, 'python': sys.version, 'numpy': np.__version__, 'numpyOrigin': np.__file__},
        'acceptedArt': False, 'nativeParityPassed': False, 'enclosurePassed': False, 'productionFourPassed': False,
        'fullGarmentTriangles': len(f), 'fullBodyTriangles': len(g), 'coordinateConvention':
        'Exact frozen endpoint pose function: full 71 named fields, nativeWorld @ inverse(nativeRest), all75 native bone names. Source triangle winding unchanged.',
        'signedMeasurement': 'Distances to the oriented plane of each actually intersecting finite triangle. These are local plane distances, not global signed-solid distance or penetration depth.',
        'locality': 'Shared-edge components of actual crossing garment triangles; all pair IDs and both posed complete surfaces retained. No nearest body query, crop or mask.',
        'allDegeneratesRemainFailures': True, 'crossMagnitudeThresholdM2': 1e-14,
        'limits': 'A strict finite crossing establishes real intersection independent of painter order. Zero strict crossings does not establish enclosure, clearance, silhouette, native/GPU parity or played art. No reconstruction, solve, candidate, native save, field edit, mask or bake.'}
    (output/'posed-contact.json').write_text(json.dumps(report, indent=2)+'\n')


if __name__ == '__main__':
    args = sys.argv[sys.argv.index('--')+1:]; assert len(args) == 1
    main(args[0])
