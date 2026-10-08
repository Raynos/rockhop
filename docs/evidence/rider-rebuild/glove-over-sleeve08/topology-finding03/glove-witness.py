"""Readonly witness reconstruction; run only after the parent's dense-load lease."""
import argparse
import ast
import hashlib
import json
import runpy
from pathlib import Path
import numpy as np

ROOT = Path('/Users/raynos/projects/games/rockhop')
REPORT = ROOT/'harness/out/rider-rebuild/glove-over-sleeve08/authored03/construction.json'
INPUT = ROOT/'assets/blender/rider-rebuild/glove-over-sleeve08/input.json'
VOLUME = ROOT/'assets/blender/rider-rebuild/glove-over-sleeve08/volume.py'
AUTHOR = ROOT/'assets/blender/rider-rebuild/glove-over-sleeve08/author.py'
MASK_ROOT = ROOT/'harness/out/rider-rebuild/selected-complete-engine01/engine05'


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        while block := stream.read(1024*1024):
            h.update(block)
    return h.hexdigest()


def pin(row):
    path = ROOT/row['path']
    assert sha(path) == row['sha256'], ('Changed evidence', row['path'])
    return path


def read_json(path):
    return json.loads(path.read_text())


def take(data, native_ids, field='worldXYZ'):
    ids = data['nativeVertexIds']
    mapping = {int(identity): index for index, identity in enumerate(ids)}
    assert all(int(i) in mapping for i in native_ids), ('Witness outside exact recorded crop', native_ids)
    return data[field][[mapping[int(i)] for i in native_ids]]


def roundtrip(world, matrix, V):
    return V['apply'](V['apply'](world, np.linalg.inv(matrix)).astype(np.float32), matrix)


def radial_hits(origin, direction, vertices, faces):
    t = vertices[faces]
    e1, e2 = t[:, 1]-t[:, 0], t[:, 2]-t[:, 0]
    p = np.cross(direction, e2)
    det = np.sum(e1*p, axis=1)
    valid = np.abs(det) > 1e-15
    inv = 1/np.where(valid, det, 1)
    s = origin-t[:, 0]
    u = np.sum(s*p, axis=1)*inv
    q = np.cross(s, e1)
    v = np.sum(direction*q, axis=1)*inv
    distance = np.sum(e2*q, axis=1)*inv
    hits = np.flatnonzero(valid & (u >= -1e-10) & (v >= -1e-10)
                         & (u+v <= 1+1e-10) & (distance > 0))
    hits = hits[np.argsort(distance[hits])]
    return [{'sourceTriangleId': int(i), 'distanceSourceUnits': float(distance[i]),
             'nativeVertexIds': faces[i].tolist()} for i in hits]


def segment_hits(a, b):
    result = []
    for label, first, second in [('gloveEdge', a, b), ('otherEdge', b, a)]:
        for i in range(3):
            edge = first[(i+1) % 3]-first[i]
            mat = np.column_stack((edge, -(second[1]-second[0]), -(second[2]-second[0])))
            if abs(np.linalg.det(mat)) < 1e-20:
                continue
            t, u, v = np.linalg.solve(mat, second[0]-first[i])
            if 0 <= t <= 1 and u >= 0 and v >= 0 and u+v <= 1:
                result.append({'edgeOwner': label, 'edgeIndex': i,
                               'edgeFraction': float(t), 'otherBarycentricUV': [float(u), float(v)],
                               'worldXYZ': (first[i]+t*edge).tolist()})
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', action='store_true', required=True)
    args = parser.parse_args()
    report = read_json(REPORT)
    assert sha(INPUT) == report['inputSHA256']
    assert sha(VOLUME) == report['volumeRecipeSHA256']
    config = read_json(INPUT)
    V = runpy.run_path(str(VOLUME))
    # Read only the existing pure triangle predicate, never import bpy/author.py.
    tree = ast.parse(AUTHOR.read_text())
    fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'strict_cross')
    scope = {'np': np}
    exec(compile(ast.Module(body=[fn], type_ignores=[]), str(AUTHOR), 'exec'), scope)
    placement = read_json(pin(config['placement']))
    inspection = read_json(pin(config['currentInspection']))
    with np.load(pin(config['originalGloveDense'])) as donor:
        original, source_faces = donor['vertices'], donor['faces']
    with np.load(pin(config['originalGloveGuide'])) as donor:
        original_guide = donor['vertices']
    with np.load(pin(report['actualHoodieWristArrays'])) as data:
        sleeve = {key: data[key] for key in ('nativeVertexIds', 'worldXYZ', 'changedMask')}
    mask = read_json(MASK_ROOT/'body-mask-receipt.json')
    manifest = read_json(MASK_ROOT/'body-mask-manifest.json')
    kept_triangles = set(mask['keptSourceTriangleIds'])
    assert mask['allOriginalVertexRowsWeightsUVMaterialsPreserved'] and mask['originalFullBodyAnd75RestUnchanged']
    result = {'acceptedArt': False, 'reportSHA256': sha(REPORT), 'witnessesOnly': True,
              'maskReceiptSHA256': sha(MASK_ROOT/'body-mask-receipt.json'),
              'maskManifestSHA256': sha(MASK_ROOT/'body-mask-manifest.json'), 'hands': {}}
    for side in ('L', 'R'):
        hand = report['hands'][side]
        rows = inspection['hands'][side]['localSurfaces']
        dense_row = next(row for row in rows if row['role'] == 'dense-cuff')
        wearer_row = next(row for row in rows if row['role'] == 'wearer')
        with np.load(pin(dense_row)) as data:
            dense = {key: data[key] for key in ('nativeVertexIds', 'worldXYZ', 'matrixWorld')}
        with np.load(pin(wearer_row)) as data:
            wearer = {key: data[key] for key in ('nativeVertexIds', 'worldXYZ', 'nativeTriangleIds', 'faces')}
        with np.load(pin(config['guideArrays'][side])) as data:
            guide = {key: data[key] for key in data.files}
        scale, x, z = V['cuff_frame'](guide, placement['hands'][side])
        assert scale == hand['sourceCuffScaleMPerSourceUnit']
        transverse = hand['transverseSourceVolumeAffine']
        guide_world, _ = V['construct_cuff'](original_guide, guide['currentWorldXYZ'], guide,
            placement['sourceRest']['wrist'], scale, x, z, transverse, config['authoring'])
        reconstructed_guide = roundtrip(guide_world, guide['matrixWorld'], V)
        with np.load(pin(hand['actualGuideArrays'])) as data:
            residual = float(np.max(abs(reconstructed_guide-data['worldXYZ'])))
        assert residual == 0, ('Guide reconstruction is not byte exact', side, residual)
        records = {}
        for gate in ('gloveSleeveIntersection', 'cuffWearerIntersection'):
            witness = hand[gate]
            ids = witness['firstTriangleVertexIds']
            source = original[ids]
            before = take(dense, ids)
            glove_world, alpha = V['construct_cuff'](source, before, guide,
                placement['sourceRest']['wrist'], scale, x, z, transverse, config['authoring'])
            actual = roundtrip(glove_world, dense['matrixWorld'], V)
            other_ids = witness['secondTriangleVertexIds']
            other = take(sleeve if gate == 'gloveSleeveIntersection' else wearer, other_ids)
            assert scope['strict_cross'](actual, other), ('Receipt crossing not reproduced', side, gate)
            centroid = source.mean(axis=0)
            _, rx, rz = V['source_cuff'](centroid[None], guide, placement['sourceRest']['wrist'], scale, x, z)
            center = centroid.copy(); center[[0, 2]] -= np.array([rx[0], rz[0]])/scale
            direction = centroid-center; radius = np.linalg.norm(direction); direction /= radius
            normal = np.cross(source[1]-source[0], source[2]-source[0]); normal /= np.linalg.norm(normal)
            hits = radial_hits(center, direction, original, source_faces)
            witness_hits = [i for i, h in enumerate(hits) if set(h['nativeVertexIds']) == set(ids)]
            assert witness_hits, ('Witness source face absent from radial ray', ids)
            axial = (actual-guide['wristWorld'])@guide['forearmAxisWorld']
            record = {'gloveNativeVertexIds': ids, 'otherNativeVertexIds': other_ids,
                'nativeTriangleIds': witness['firstStrictCrossingTriangles'], 'sourceXYZ': source.tolist(),
                'sourceYRange': [float(source[:, 1].min()), float(source[:, 1].max())],
                'constructionAlpha': alpha.tolist(),
                'changedVertices': (alpha > 0).tolist(),
                'fullSourceConstructionVertices': (alpha == 1).tolist(),
                'unchangedJoinVertices': (alpha == 0).tolist(),
                'gloveWorldXYZ': actual.tolist(), 'otherWorldXYZ': other.tolist(),
                'gloveNativeAxialM': axial.tolist(), 'sourceUnitNormal': normal.tolist(),
                'sourceAxialNormalMagnitude': float(abs(normal[1])),
                'sourceRadialNormalDot': float(normal@direction),
                'sourceRayOrigin': center.tolist(), 'sourceRayDirection': direction.tolist(),
                'witnessSourceRadius': float(radius), 'sourceRadialHits': hits,
                'witnessSourceRadialHitRanksZeroBased': witness_hits,
                'strictCrossingReproduced': True, 'crossingSegmentHits': segment_hits(actual, other)}
            if gate == 'cuffWearerIntersection':
                triangle_id = witness['firstStrictCrossingTriangles'][1]
                crop_index = np.flatnonzero(wearer['nativeTriangleIds'] == triangle_id)
                assert len(crop_index) == 1
                assert np.array_equal(wearer['nativeVertexIds'][wearer['faces'][crop_index[0]]], other_ids)
                record['fullAnatomyTrianglePresentInVisibleBody'] = triangle_id in kept_triangles
                record['coveringEquippedGarments'] = [g for g in mask['equipped']
                    if triangle_id in manifest['garmentTriangleIds'][g]]
            else:
                mapping = {int(i): j for j, i in enumerate(sleeve['nativeVertexIds'])}
                record['otherSleeveChangedVertices'] = [bool(sleeve['changedMask'][mapping[i]]) for i in other_ids]
            records[gate] = record
        result['hands'][side] = {'guideReconstructionMaximumResidual': residual, 'witnesses': records}
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
