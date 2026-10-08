"""Parent-only native intake of constructor37; unchanged frozen25 qualifiers.

Usage: blender -b -t2 --python author.py -- CONSTRUCTOR_JSON NEW_OUT
The native is saved explicitly unaccepted before qualification, including when
allocation fails. Original selected donors/appearance/rest fields stay exact.
"""
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
ENGINE_SHA = 'bc9e03aa6d99eba0d4b5037ceff49424c34ddcde99f0f2aae0f84a5090cbc483'
INPUT_SHA = '49702808cf80ec8ad7104f2681c02b758e97d19f11a386e9b27ca53f8c0f6449'
WITNESS_SHA = '95c7813b503c7d5539b2d7082e14229d484060bacefae294d28160e2c30755d5'
NATIVE_SHA = 'a155d13f9b4df422bf851f847c7d392fbd3451c5d20c675093e8913bd05138ad'


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        while block := stream.read(1048576): h.update(block)
    return h.hexdigest()


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def arrays(pin):
    file = ROOT/pin['path']; assert sha(file) == pin['sha256']
    raw = file.read_bytes(); result = {}
    for name, row in pin['layout'].items():
        dtype = np.dtype(row['dtype'])
        assert dtype in [np.dtype('<f4'), np.dtype('<i4'), np.dtype('<u4')]
        count = row.get('count', int(np.prod(row.get('shape', []))))
        assert row['byteLength'] == dtype.itemsize*count
        assert 0 <= row['byteOffset'] <= len(raw)-row['byteLength']
        result[name] = np.frombuffer(raw, dtype=dtype, count=count, offset=row['byteOffset'])
    return result


def surface_checks(engine, source, target, limit, normal_limit, out, write):
    """Fresh geometric normals and finite samples; never supplied attribute normals."""
    sp = engine.points(source); sf = engine.triangles(source)
    tp = engine.points(target); tf = engine.triangles(target)
    def normal(p, f):
        cross = np.cross(p[f[:, 1]]-p[f[:, 0]], p[f[:, 2]]-p[f[:, 0]])
        length = np.linalg.norm(cross, axis=1); assert np.all(length > 0), 'Degenerate geometric face'
        return cross/length[:, None]
    sn = normal(sp, sf); tn = normal(tp, tf)
    source_tree = engine.tree(sp, sf); target_tree = engine.tree(tp, tf)
    edges = np.unique(np.sort(np.concatenate([tf[:, [0, 1]], tf[:, [1, 2]], tf[:, [2, 0]]]), axis=1), axis=0)
    stages = [('target-face-centroids', tp[tf].mean(axis=1), source_tree, tn, sn),
              ('target-edge-midpoints', tp[edges].mean(axis=1), source_tree, None, None),
              ('source-face-centroids', sp[sf].mean(axis=1), target_tree, None, None)]
    report = {}
    for label, query, tree, qn, rn in stages:
        distances = np.full(len(query), np.nan, np.float32)
        dots = np.full(len(query), np.nan, np.float32); face_ids = np.full(len(query), -1, np.int32)
        for i, point in enumerate(query):
            near = tree.find_nearest(Vector(point))
            if near[0] is not None:
                distances[i] = near[3]; face_ids[i] = near[2]
                if qn is not None: dots[i] = qn[i] @ rn[near[2]]
        path = out/(label+'.npz')
        np.savez(path, distanceM=distances, normalDot=dots, sourceFaceId=face_ids)
        report[label] = {'samples': len(query), 'missingBearings': int(np.count_nonzero(face_ids < 0)),
            'over1mmCount': int(np.count_nonzero(distances > limit)),
            'normalBelowPoint25Count': int(np.count_nonzero(dots < normal_limit)),
            'maximumDistanceM': float(np.nanmax(distances)),
            'minimumNormalDot': float(np.nanmin(dots)) if qn is not None else None,
            'arrays': {'path': str(path.relative_to(ROOT)), 'sha256': sha(path)}}
        write(report)
        row = report[label]
        assert not row['missingBearings'] and not row['over1mmCount'] and not row['normalBelowPoint25Count'], ('Original source surface/orientation bound failed', label, row)
    return report


def main():
    args = sys.argv[sys.argv.index('--')+1:]; assert len(args) == 2
    receipt_path = Path(args[0]).resolve(); out = Path(args[1]).resolve()
    base = ROOT/'harness/out/rider-rebuild/selected-production-constructor37'
    assert receipt_path.is_relative_to(base) and out.is_relative_to(base) and not out.exists()
    receipt = json.loads(receipt_path.read_text())
    assert receipt['status'] in ['UNACCEPTED_CANDIDATE_AWAITING_NATIVE_QUALIFICATION', 'REJECTED_ALLOCATION_ABOVE_8000']
    assert receipt['candidateAttempts'] == 1 and receipt['acceptedArt'] is False
    assert receipt['recipeSHA256'] == sha(HERE/'construct.mjs')
    pins = receipt['censusSourcePins']
    assert pins['productionAuthor']['sha256'] == ENGINE_SHA and pins['productionInput']['sha256'] == INPUT_SHA
    assert pins['rejectedNative']['sha256'] == NATIVE_SHA
    engine_path = ROOT/pins['productionAuthor']['path']; assert sha(engine_path) == ENGINE_SHA
    engine = load(engine_path, 'constructor37_frozen25')
    for row in pins.values(): engine.pin(row)
    engine.pin(receipt['census'])
    witness_path = ROOT/'assets/blender/rider-rebuild/selected-production-family31/witness.py'
    assert sha(witness_path) == WITNESS_SHA
    witness = load(witness_path, 'constructor37_witness31')
    config = json.loads(engine.pin(pins['productionInput']).read_text())
    name = 'ActualSelectedBoot.L'; spec = config['objects'][name]
    assert spec['full'] == 8000 and spec['maximumSurfaceErrorM'] == 0.001
    assert config['transfer'] == {'minimumNormalDot': 0.25, 'maximumSkinWeightL1': 0.3,
        'maximumInfluences': 4, 'maximumRemovedMass': 0.001,
        'maximumAdditionalAdjacentWeightL1': 0.002, 'supportEpsilon': 1e-05}
    bpy.ops.wm.open_mainfile(filepath=str(engine.pin(pins['rejectedNative'])))
    rig = bpy.data.objects[config['rig']]; assert len(rig.data.bones) == 75
    sources = {n: bpy.data.objects[n] for n, row in config['objects'].items() if row['family'] == 'boots'}
    before = witness.retained(sources, rig); source = sources[name]
    dense = arrays(receipt['sourceArrayPackage']); candidate = arrays(receipt['candidate'])
    p = candidate['positions'].reshape(-1, 3); f = candidate['triangles'].reshape(-1, 3)
    original = candidate['originalVertexIds']; names = receipt['groupNames']
    sp = engine.points(source).astype(np.float32); sf = engine.triangles(source)
    sw = engine.skin_rows(source, names).astype(np.float32)
    assert names == [g.name for g in source.vertex_groups if g.name in rig.data.bones]
    assert np.array_equal(sp.ravel(), dense['positions']) and np.array_equal(sf.ravel(), dense['triangles'])
    assert np.array_equal(sw.ravel(), dense['namedWeights'])
    assert len(original) == len(p) and np.all(original < len(sp)) and len(np.unique(original)) == len(original)
    assert np.array_equal(p, sp[original]), 'Candidate moved original positions'
    fields = candidate['namedWeights'].reshape(len(p), len(names))
    assert np.array_equal(fields, sw[original]), 'Candidate changed inherited named fields'
    assert len(f) == receipt['targetTriangles'] and len(p) == receipt['targetVertices']
    # Retire only the old rejected derivative in this new diagnostic scene.
    old = bpy.data.objects.get('Production.full.'+name)
    if old: bpy.data.objects.remove(old, do_unlink=True)
    mesh = bpy.data.meshes.new('Constructor37.original-position-topology')
    mesh.from_pydata(p.tolist(), [], f.tolist()); mesh.update()
    target = source.copy(); target.data = mesh; target.name = 'Production.full.'+name
    bpy.context.scene.collection.objects.link(target)
    for mod in list(target.modifiers): target.modifiers.remove(mod)
    target.vertex_groups.clear()
    for j, group_name in enumerate(names):
        group = target.vertex_groups.new(name=group_name)
        for i in np.flatnonzero(fields[:, j]): group.add([int(i)], float(fields[i, j]), 'REPLACE')
    for material in source.data.materials: mesh.materials.append(material)
    assert np.all(candidate['faceMaterialIds'] < len(mesh.materials))
    mesh.polygons.foreach_set('material_index', candidate['faceMaterialIds'].astype(np.int32))
    for polygon in mesh.polygons: polygon.use_smooth = True
    ancestry = mesh.attributes.new('ProductionOriginalVertex', 'INT', 'POINT')
    ancestry.data.foreach_set('value', original.astype(np.int32))
    target['selectedProductionRole'] = name; target['selectedProductionLevel'] = 'full'
    target['qualificationState'] = 'UNACCEPTED_CONSTRUCTOR37_BEFORE_QUALIFICATION'
    target.hide_render = False; target.hide_set(False); bpy.context.view_layer.update()
    assert np.array_equal(engine.points(target).astype(np.float32), p)
    assert np.array_equal(engine.skin_rows(target, names).astype(np.float32), fields)
    inverse = {int(v): i for i, v in enumerate(original)}
    for v in candidate['lockedOriginalVertexIds']: assert int(v) in inverse
    actual_edges = {tuple(sorted(edge.vertices)) for edge in mesh.edges}
    for a, b in candidate['requiredEdgesOriginal'].reshape(-1, 2):
        assert tuple(sorted([inverse[int(a)], inverse[int(b)]])) in actual_edges
    assert before == witness.retained(sources, rig), 'Selected source changed during construction'
    out.mkdir(parents=True)
    report = {'status': 'UNACCEPTED_BEFORE_TRANSFER', 'acceptedArt': False, 'level': 'full',
        'authoredFamilies': ['boots'], 'authoredSourceObjects': [name],
        'constructor': {'path': str(receipt_path.relative_to(ROOT)), 'sha256': sha(receipt_path)},
        'sourceMaster': pins['rejectedNative'], 'sourceWitness': before,
        'recipeSHA256': sha(__file__), 'objects': {}, 'totalTriangles': len(f),
        'sourceIdentityAfterProduction': True, 'sourceInputBytesUnchanged': True,
        'bakeCompleted': False, 'movingReviewPassed': False, 'denseGeometryPassed': False, 'devicePassed': False,
        'bakeEligibility': 'LEFT_BOOT_ONLY_NOT_A_BILATERAL_FAMILY32_INPUT',
        'limits': 'Left boot only; no new right boot or complete selected rider. Exact source ancestry and original named fields precede unchanged frozen25 correspondence. Selected donor maps persist; target appearance awaits its fresh atlas and cage bake.'}
    def write(): (out/'production.json').write_text(json.dumps(report, indent=2)+'\n')
    write()
    native = out/'UNACCEPTED-constructor37-before-transfer.blend'
    bpy.ops.wm.save_as_mainfile(filepath=str(native), compress=False)
    report['native'] = {'path': str(native.relative_to(ROOT)), 'sha256': sha(native)}; write()
    try:
        assert len(f) <= spec['full'], 'Allocation exceeds8000; candidate retained unaccepted, no forced reduction'
        report['objects'][name] = {'sourceTriangles': len(sf), 'targetTriangles': len(f),
            'targetBudget': spec['full'], 'constructor': 'meshoptimizer1.1.1 index-only attributes',
            'originalPositionsAndFieldsExact': True}
        # Frozen transfer enforces original vertex orientation/skin, reverse
        # source vertices, target chord and FOUR/removed-mass/adjacency limits.
        report['objects'][name]['transfer'] = engine.transfer(source, target, rig, spec, 'full', config, out); write()
        def save_surface(value): report['sourceSurfaceSamples'] = value; write()
        surface_checks(engine, source, target, spec['maximumSurfaceErrorM'], config['transfer']['minimumNormalDot'], out, save_surface)
        engine.unwrap_family([target])
        assert before == witness.retained(sources, rig), 'Original selected geometry/fields/UV/maps/binds changed'
        target['qualificationState'] = 'UNACCEPTED_GEOMETRY_PASSED_BAKE_AND_MOTION_PENDING'
        source.hide_render = True; source.hide_set(True)
        native = out/'UNACCEPTED-selected-production-full.blend'
        bpy.ops.wm.save_as_mainfile(filepath=str(native), compress=False)
        report['native'] = {'path': str(native.relative_to(ROOT)), 'sha256': sha(native)}
        report['status'] = 'UNACCEPTED_LEFT_BOOT_GEOMETRY_AND_ATLAS_PREPARED'
        report['restGeometryPassed'] = True; write()
    except Exception as error:
        report['status'] = 'REJECTED_NATIVE_CONSTRUCTOR37_UNACCEPTED'; report['failure'] = repr(error); write(); raise


if __name__ == '__main__': main()
