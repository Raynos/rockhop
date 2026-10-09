"""Read qualified41 only; parent CPU2 guard required. No native writes or solve.

blender -b -t 2 --python-exit-code 1 --python extract.py -- FRESH_OUT
Then independently run check.py FRESH_OUT/extraction.json outside Blender.
"""
import hashlib
import json
import os
from pathlib import Path
import runpy
import sys

ROOT = Path(__file__).resolve().parents[4]
BASE = ROOT/'harness/out/rider-rebuild/selected-glove-family81'
RECEIPT = {'path': 'harness/out/rider-rebuild/selected-glove-component41/component01/component-qualified.json',
           'sha256': '0136d429c4501386dad7e96a6113164adafb3f091d029f3e8b496803c6b1aa5b'}
DEPENDENCIES = {'path': 'assets/blender/rider-rebuild/selected-production-family31/dependencies.py',
                'sha256': '567c5993505ee6de949db805d9bc4398dbd53415ea40312d7d5038d84c08fd17'}
WITNESS = {'path': 'assets/blender/rider-rebuild/selected-production-family31/witness.py',
           'sha256': '95c7813b503c7d5539b2d7082e14229d484060bacefae294d28160e2c30755d5'}
GLOVES = ('ActualSelectedGlove.L', 'ActualSelectedGlove.R')
REFERENCE = 'RiderBody__FullAnatomyReference'
QUALIFIED = 'UNACCEPTED_SELECTED_GLOVE_COMPONENT_REOPENED_DENSE_AND_MOTION_PENDING'


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        while block := stream.read(1024*1024): digest.update(block)
    return digest.hexdigest()


def pin(path):
    path = Path(path).resolve()
    return {'path': str(path.relative_to(ROOT)), 'sha256': sha(path)}


def checked(row):
    path = (ROOT/row['path']).resolve()
    assert path.is_relative_to(ROOT) and sha(path) == row['sha256'], row
    return path


def canonical(value):
    return json.loads(json.dumps(value))


def main(output):
    assert os.environ.get('ROCKHOP_GENERATION_CONTROLLER_PID'), 'Original parent guard required'
    import bpy
    import numpy as np

    output = Path(output).resolve()
    assert output.is_relative_to(BASE) and output != BASE and not output.exists()
    receipt = json.loads(checked(RECEIPT).read_text())
    assert receipt['status'] == QUALIFIED and receipt['acceptedArt'] is False
    assert receipt['protectedValidationPassed'] and receipt['nativeStorage']['reopenVerified']
    assert receipt['exact75RestUnchanged'] and receipt['constructedGloveGeometryAndNamedFieldsExactAfterReopen']
    component = runpy.run_path(str(checked(receipt['sourceRecipe'])))
    assert component['GLOVES'] == GLOVES and component['QUALIFIED'] == QUALIFIED
    source = json.loads(checked(receipt['priorInput']).read_text())
    author = runpy.run_path(str(checked(source['restHelper'])))
    geometry = runpy.run_path(str(checked(source['geometryHelper'])))['geometry']
    witness = runpy.run_path(str(checked(WITNESS)))
    dependencies = runpy.run_path(str(checked(DEPENDENCIES)))
    assert bpy.ops.wm.open_mainfile(filepath=str(checked(receipt['native'])), use_scripts=False) == {'FINISHED'}
    assert {obj.name for obj in bpy.data.objects} == set(component['REQUESTED'])
    rig = bpy.data.objects['RiderSkeleton']
    sources = {name: bpy.data.objects[name] for name in GLOVES}
    assert len(rig.data.bones) == 75 and all(b.matrix_basis.is_identity for b in rig.pose.bones)
    assert canonical(author['rest'](rig)) == receipt['protectedBefore']['rest']
    assert geometry(bpy.data.objects[REFERENCE]) == receipt['protectedBefore']['fullReference']

    def dependency_graph():
        graph = dependencies['dependencies'](bpy.data.user_map())
        kept = dependencies['closure']([*sources.values(), rig, bpy.data.objects[REFERENCE]], graph)
        label = lambda item: item.bl_rna.identifier+':'+item.name_full
        return {label(item): sorted(label(child) for child in graph.get(item, ())) for item in kept}

    def read(collection, attribute, width, dtype):
        result = np.empty((len(collection), width), dtype)
        collection.foreach_get(attribute, result.ravel())
        return result if width > 1 else result[:, 0]

    before = canonical(witness['retained'](sources, rig))
    graph = dependency_graph()
    output.mkdir(parents=True)
    report = {'status': 'RAW_EXTRACTION_PENDING_UNACCEPTED', 'acceptedArt': False,
              'recipe': pin(__file__), 'sourceReceipt': RECEIPT, 'native': receipt['native'],
              'helperPins': [receipt['sourceRecipe'], source['restHelper'], source['geometryHelper'], WITNESS, DEPENDENCIES],
              'sourceWitness': before, 'rest': receipt['protectedBefore']['rest'],
              'fullReferenceGeometry': receipt['protectedBefore']['fullReference'],
              'dependencyWitness': graph, 'objects': {}, 'nativeMutation': False,
              'fieldPolicy': 'Every actual41 stored named weight in original membership order; no normalization or pruning.',
              'limits': 'Source cache only. No candidate, geometry qualification, palette reduction, bake, moving or device acceptance.'}
    write = lambda: (output/'extraction.json').write_text(json.dumps(report, indent=2)+'\n')
    write()
    for name, obj in sources.items():
        print('GLOVE81_EXTRACT '+name, flush=True)
        expected = receipt['objects'][name]
        checked(expected['ancestry'])
        assert geometry(obj) == receipt['expectedConstructedGeometry'][name]
        assert canonical(component['metadata'](obj, author['packed_maps'])) == receipt['protectedBefore']['gloves'][name]
        mesh = obj.data
        assert len(mesh.vertices) == expected['vertices'] and len(mesh.polygons) == expected['triangles']
        mesh.calc_loop_triangles()
        assert len(mesh.loop_triangles) == len(mesh.polygons) and all(len(p.vertices) == 3 for p in mesh.polygons)
        arrays = {'positions': read(mesh.vertices, 'co', 3, np.float32),
                  'edges': read(mesh.edges, 'vertices', 2, np.int32),
                  'triangles': read(mesh.loop_triangles, 'vertices', 3, np.int32),
                  'triangleLoopIds': read(mesh.loop_triangles, 'loops', 3, np.int32),
                  'trianglePolygonIds': read(mesh.loop_triangles, 'polygon_index', 1, np.int32),
                  'loopVertices': read(mesh.loops, 'vertex_index', 1, np.int32),
                  'polygonStarts': read(mesh.polygons, 'loop_start', 1, np.int32),
                  'polygonSizes': read(mesh.polygons, 'loop_total', 1, np.int32),
                  'faceMaterialIds': read(mesh.polygons, 'material_index', 1, np.int32),
                  'vertexNormals': read(mesh.vertices, 'normal', 3, np.float32),
                  'cornerNormals': read(mesh.corner_normals, 'vector', 3, np.float32),
                  'faceNormals': read(mesh.polygons, 'normal', 3, np.float32)}
        offsets, indices, weights = [0], [], []
        for vertex in mesh.vertices:
            for group in vertex.groups:
                indices.append(group.group); weights.append(group.weight)
            offsets.append(len(indices))
        arrays.update(fieldOffsets=np.asarray(offsets, np.int64), fieldIndices=np.asarray(indices, np.int32),
                      fieldWeights=np.asarray(weights, np.float32))
        del offsets, indices, weights
        uv_names = [layer.name for layer in mesh.uv_layers]
        for index, layer in enumerate(mesh.uv_layers): arrays['uvLayer'+str(index)] = read(layer.data, 'uv', 2, np.float32)
        for index, key in enumerate(mesh.shape_keys.key_blocks if mesh.shape_keys else ()):
            arrays['shapeKey'+str(index)] = read(key.data, 'co', 3, np.float32)
        # Preserve ordered PBR inputs to the existing qualified41 geometry digest.
        pbr = [{'material': material.name, 'imageHashes': [hashlib.sha256(node.image.packed_file.data).hexdigest()
                for node in material.node_tree.nodes if node.type == 'TEX_IMAGE' and node.image]}
               for material in mesh.materials if material and material.use_nodes]
        target = output/(name+'.npz')
        with target.open('xb') as stream: np.savez(stream, **arrays)
        report['objects'][name] = {'arrays': pin(target), 'geometry': receipt['expectedConstructedGeometry'][name],
            'ancestry': expected['ancestry'], 'groupNames': [group.name for group in obj.vertex_groups],
            'uvLayerNames': uv_names, 'geometryPBR': pbr,
            'shapeKeyNames': [key.name for key in mesh.shape_keys.key_blocks] if mesh.shape_keys else [],
            'layout': {key: {'dtype': value.dtype.str, 'shape': list(value.shape),
                            'sha256': hashlib.sha256(value.tobytes()).hexdigest()} for key, value in arrays.items()}}
        write()
        del arrays
    assert canonical(witness['retained'](sources, rig)) == before
    assert dependency_graph() == graph
    assert canonical(author['rest'](rig)) == report['rest']
    report.update(status='ACTUAL41_BILATERAL_RAW_CACHE_UNACCEPTED_CPU_CHECK_PENDING',
                  sourceWitnessUnchanged=True, dependencyWitnessUnchanged=True)
    write()
    print(report['status'], flush=True)


if __name__ == '__main__':
    args = sys.argv[sys.argv.index('--')+1:]
    assert len(args) == 1
    main(args[0])
