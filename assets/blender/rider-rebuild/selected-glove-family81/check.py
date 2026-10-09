"""Independent CPU reconstruction of raw41 identity; never imports Blender."""
import hashlib
import json
from pathlib import Path
import struct
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]


def digest(value):
    return hashlib.sha256(value).hexdigest()


def main(file):
    file = Path(file).resolve()
    report = json.loads(file.read_text())
    assert report['status'] == 'ACTUAL41_BILATERAL_RAW_CACHE_UNACCEPTED_CPU_CHECK_PENDING'
    assert report['acceptedArt'] is False and report['nativeMutation'] is False
    assert report['sourceWitnessUnchanged'] and report['dependencyWitnessUnchanged']
    for row in [report['recipe'], report['sourceReceipt'], *report['helperPins']]:
        assert digest((ROOT/row['path']).read_bytes()) == row['sha256'], row
    receipt = json.loads((ROOT/report['sourceReceipt']['path']).read_text())
    assert report['native'] == receipt['native'] and report['rest'] == receipt['protectedBefore']['rest']
    assert len(report['sourceWitness']['rig']['bones']) == 75
    assert set(report['objects']) == {'ActualSelectedGlove.L', 'ActualSelectedGlove.R'}
    results = {}
    for name, row in report['objects'].items():
        raw = ROOT/row['arrays']['path']
        assert digest(raw.read_bytes()) == row['arrays']['sha256']
        source = report['sourceWitness']['sources'][name]
        assert row['groupNames'] == [g[1] for g in source['groups']] == receipt['objects'][name]['vertexGroupNamesUnchanged']
        with np.load(raw, allow_pickle=False) as a:
            assert set(a.files) == set(row['layout'])
            for key, layout in row['layout'].items():
                assert a[key].dtype.str == layout['dtype'] and list(a[key].shape) == layout['shape']
                assert digest(a[key].tobytes()) == layout['sha256']
                assert np.isfinite(a[key]).all(), key
            for key, witness in [('positions', 'positionSHA256'), ('edges', 'edgeSHA256'),
                                 ('loopVertices', 'loopVertexSHA256'), ('polygonStarts', 'polygonStartSHA256'),
                                 ('polygonSizes', 'polygonSizeSHA256'), ('faceMaterialIds', 'materialIndexSHA256')]:
                assert digest(a[key].tobytes()) == source[witness], (name, key)
            xyz, triangles, corners = a['positions'], a['triangles'], a['triangleLoopIds']
            offsets, indices, weights = a['fieldOffsets'], a['fieldIndices'], a['fieldWeights']
            assert xyz.shape == (source['vertices'], 3) and triangles.shape == (source['polygons'], 3)
            assert len(offsets) == len(xyz)+1 and offsets[0] == 0 and offsets[-1] == len(indices) == len(weights)
            assert (np.diff(offsets) >= 0).all() and ((indices >= 0) & (indices < len(row['groupNames']))).all()
            assert (weights >= 0).all() and (weights <= 1).all()
            assert ((triangles >= 0) & (triangles < len(xyz))).all()
            assert ((corners >= 0) & (corners < len(a['loopVertices']))).all()
            assert np.array_equal(a['loopVertices'][corners], triangles)
            assert np.array_equal(a['trianglePolygonIds'], np.arange(len(triangles)))
            assert np.array_equal(a['polygonStarts'], np.arange(len(triangles))*3) and (a['polygonSizes'] == 3).all()
            assert np.array_equal(corners, a['polygonStarts'][:, None]+np.arange(3))
            geometry, fields = hashlib.sha256(), hashlib.sha256()
            geometry.update(name.encode())
            for v, point in enumerate(xyz):
                begin, end = offsets[v:v+2]
                assert len(set(indices[begin:end].tolist())) == end-begin
                geometry.update(point.tobytes())
                fields.update(struct.pack('<II', v, end-begin))
                for group, weight in zip(indices[begin:end], weights[begin:end]):
                    packed = struct.pack('<If', group, weight)
                    geometry.update(packed); fields.update(packed)
            assert fields.hexdigest() == source['weightSHA256']
            for material, face in zip(a['faceMaterialIds'], triangles):
                geometry.update(struct.pack('<II', material, 3)); geometry.update(face.astype('<u4').tobytes())
            for i, uv_name in enumerate(row['uvLayerNames']):
                uv = a['uvLayer'+str(i)]
                assert uv.shape == (len(a['loopVertices']), 2)
                assert digest(uv.tobytes()) == source['uv'][uv_name]['sha256']
                geometry.update(uv_name.encode()); geometry.update(uv.tobytes())
            for i, key_name in enumerate(row['shapeKeyNames']):
                assert digest(a['shapeKey'+str(i)].tobytes()) == source['shapeKeys'][key_name]
            for material in row['geometryPBR']:
                geometry.update(material['material'].encode())
                for image_hash in material['imageHashes']: geometry.update(bytes.fromhex(image_hash))
            assert geometry.hexdigest() == row['geometry'] == receipt['expectedConstructedGeometry'][name]
            # Zero orphan normals are reported, not normalized or silently deleted.
            results[name] = {'vertices': len(xyz), 'triangles': len(triangles), 'namedFields': len(row['groupNames']),
                'memberships': len(weights), 'maximumMemberships': int(np.diff(offsets).max()),
                'zeroVertexNormals': int((np.linalg.norm(a['vertexNormals'], axis=1) == 0).sum()),
                'cornerNormals': len(a['cornerNormals']), 'fullQualifiedGeometryReconstructed': True,
                'sourceWitnessArrayAndNamedFieldBytesExact': True}
    result = {'status': 'INDEPENDENT_CPU_ACTUAL41_CACHE_IDENTITY_PASSED_UNACCEPTED', 'acceptedArt': False,
              'extraction': {'path': str(file.relative_to(ROOT)), 'sha256': digest(file.read_bytes())},
              'checker': {'path': str(Path(__file__).resolve().relative_to(ROOT)), 'sha256': digest(Path(__file__).read_bytes())},
              'objects': results, 'candidateAttempts': 0}
    output = file.with_name('cpu-check.json')
    with output.open('x') as stream: json.dump(result, stream, indent=2); stream.write('\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    assert len(sys.argv) == 2
    main(sys.argv[1])
