"""Intended-final actual boot semantic classifier; no fitted/exported asset.

The source is thick closed material surrounding a real shaft aperture. Identify
its actual inner surface by visibility from certified empty cavity seeds. Every
source vertex/triangle stays intact; dense appearance provenance is recorded.
No global maximum-height cut or body-offset exterior is permitted.
"""
import hashlib
import json
from pathlib import Path
import sys
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parents[4]
PREP = ROOT / 'assets/blender/hero-remaster/rider/finish-2026-10-05/wardrobe/data/prep02/boots'
SOURCE = PREP / 'retopology-prototype.npz'
DENSE = PREP / 'cleaned-donor.npz'
SOURCE_SHA = 'd420da6bc7db4fa02ea095266dc174ff07cd3fb657cb0b01b91a319aa6b17853'
DENSE_SHA = '9849de6444632c2dcd1e1d76fda42ac27a7cbe8c7d2c0263ab2082e24b94777f'
SHA = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
args = sys.argv[sys.argv.index('--') + 1:]
assert len(args) == 1
out = Path(args[0]).resolve()
assert out.is_relative_to(ROOT / 'harness/out/rider-rebuild')
out.mkdir(parents=True, exist_ok=False)
report = {'accepted': False, 'status': 'RUNNING_SOURCE_CLASSIFICATION',
          'recipeSHA256': SHA(__file__), 'inputs': [
              {'path': str(SOURCE), 'sha256': SOURCE_SHA},
              {'path': str(DENSE), 'sha256': DENSE_SHA}],
          'limits': ['Source semantic construction only; no fit or art acceptance.',
                     'Visibility masks are witnesses, not automatically removable faces.',
                     'Actual selected source and all source vertices remain unchanged.']}

def save():
    (out / 'classification.json').write_text(json.dumps(report, indent=2) + '\n')

def winding(points, vertices, faces):
    values = []
    for point in points:
        a, b, c = (vertices[faces[:, i]] - point for i in range(3))
        la, lb, lc = (np.linalg.norm(row, axis=1) for row in (a, b, c))
        numerator = np.einsum('ij,ij->i', a, np.cross(b, c))
        denominator = la * lb * lc + np.einsum('ij,ij->i', a, b) * lc
        denominator += np.einsum('ij,ij->i', b, c) * la
        denominator += np.einsum('ij,ij->i', c, a) * lb
        values.append(float(np.arctan2(numerator, denominator).sum() / (2 * np.pi)))
    return np.asarray(values)

def boundary_cycles(faces):
    edges = np.concatenate((faces[:, [0, 1]], faces[:, [1, 2]], faces[:, [2, 0]]))
    unique, counts = np.unique(np.sort(edges, axis=1), axis=0, return_counts=True)
    boundary = unique[counts == 1]
    neighbors = {}
    for a, b in boundary:
        neighbors.setdefault(int(a), []).append(int(b))
        neighbors.setdefault(int(b), []).append(int(a))
    degrees = {str(degree): sum(len(v) == degree for v in neighbors.values())
               for degree in sorted(set(map(len, neighbors.values())))}
    return {'boundaryEdges': len(boundary), 'boundaryVertexDegrees': degrees,
            'simpleCyclesPossible': bool(neighbors) and all(len(v) == 2 for v in neighbors.values())}

try:
    assert SHA(SOURCE) == SOURCE_SHA and SHA(DENSE) == DENSE_SHA
    source = dict(np.load(SOURCE))
    vertices, faces = source['vertices'], source['faces']
    tree = BVHTree.FromPolygons([Vector(row) for row in vertices], faces.tolist(), all_triangles=True)
    triangles = vertices[faces]
    centers = triangles.mean(1)
    normals = np.cross(triangles[:, 1] - triangles[:, 0], triangles[:, 2] - triangles[:, 0])
    normals /= np.linalg.norm(normals, axis=1)[:, None]
    # Seeds occupy the actually rendered shaft void, along its ingress path.
    # Solid-angle containment certifies emptiness; upward escape certifies that
    # this void is the actual wearer port rather than a decorative closed pocket.
    seeds = np.asarray([[.45, .15, -.07], [.45, 0., -.07], [.45, -.20, -.07]])
    seed_winding = winding(seeds, vertices, faces)
    assert np.max(np.abs(seed_winding)) < 1e-8, 'Source seed is inside boot material'
    escapes = [tree.ray_cast(Vector(row), Vector((0, 1, 0)))[0] is None for row in seeds]
    assert all(escapes), 'Source cavity seed does not escape through actual shaft'
    visible = np.zeros((len(seeds), len(faces)), dtype=bool)
    inward = np.zeros_like(visible)
    for seed_id, seed in enumerate(seeds):
        delta = centers - seed
        distance = np.linalg.norm(delta, axis=1)
        direction = delta / distance[:, None]
        facing = np.einsum('ij,ij->i', normals, -direction) > .0001
        for face_id in np.flatnonzero(facing):
            hit, normal, hit_id, hit_distance = tree.ray_cast(Vector(seed), Vector(direction[face_id]))
            if hit is not None and hit_id == face_id and abs(hit_distance - distance[face_id]) < 2e-6:
                visible[seed_id, face_id] = True
        inward[seed_id] = facing
    inner_visible = visible.any(0)
    lower_visible = inner_visible & (triangles[:, :, 1].max(1) < .18001)
    report['seedCertificates'] = [{'sourcePosition': seed.tolist(), 'materialWinding': float(value),
                                   'upwardEscapeThroughShaft': bool(escape)}
                                  for seed, value, escape in zip(seeds, seed_winding, escapes)]
    report['sourceSurfaceWitness'] = {'triangles': len(faces),
                                    'innerVisibleTriangles': int(inner_visible.sum()),
                                    'innerVisibleBelowMeasuredRimTriangles': int(lower_visible.sum()),
                                    'lowerVisibilityBoundary': boundary_cycles(faces[lower_visible]),
                                    'lowerVisibilityBounds': [vertices[np.unique(faces[lower_visible])].min(0).tolist(),
                                                             vertices[np.unique(faces[lower_visible])].max(0).tolist()]}
    # Empty/solid probes establish whether the source provides a usable forefoot
    # cavity. They never expand seeds or relax the winding certificate.
    probes = np.asarray([[x, y, -.04] for x in (-.7, -.4, -.1, .2, .45)
                         for y in (-.4, -.3, -.2, -.1, 0.)])
    report['footVolumeProbes'] = [{'sourcePosition': point.tolist(), 'materialWinding': float(value)}
                                 for point, value in zip(probes, winding(probes, vertices, faces))]
    np.savez_compressed(out / 'source-semantic-witness.npz', sourceVertices=vertices,
                        sourceFaces=faces, sourceFaceCenters=centers, sourceFaceNormals=normals,
                        cavitySeeds=seeds, cavitySeedWinding=seed_winding,
                        cavityVisibilityBySeed=visible, cavityInwardFacingBySeed=inward,
                        sourceInnerVisibleMask=inner_visible, sourceInnerVisibleBelowRimMask=lower_visible)
    assert SHA(SOURCE) == SOURCE_SHA and SHA(DENSE) == DENSE_SHA
    report['originalSourceFilesBytePreserved'] = True
    report['status'] = 'SOURCE_CLASSIFIED_UNACCEPTED'
except BaseException as error:
    report['status'] = 'REJECTED_SOURCE_CLASSIFICATION'
    report['error'] = type(error).__name__ + ': ' + str(error)
    raise
finally:
    save()
    print(json.dumps({key: report[key] for key in ('status', 'error') if key in report}))
