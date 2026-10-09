"""One explicit broad proximal hoodie rest fit; parent guarded Blender only.

Exact original selected topology, source indices, UV/PBR and named fields are
preserved. Only rest positions and transported source corner normals change.
Raw native saves before postconstruction fingerprint/strain qualification.
"""
import gc
import hashlib
import importlib.util
import json
import runpy
import struct
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
c47 = runpy.run_path(str(HERE.parent/'selected-sleeve-component47/component.py'))
ROOT, checked, pin, write = (c47[k] for k in ('ROOT', 'checked', 'pin', 'write'))
OUT = ROOT/'harness/out/rider-rebuild/selected-proximal-hoodie-fit50'
SOURCE47 = {'path': 'assets/blender/rider-rebuild/selected-sleeve-component47/input01.json',
            'sha256': '7426ed1631f88fd4f6dc6c951ce10fb09d257c739add94f553243a8a3e2e6599'}
WRAPPER47 = {'path': 'assets/blender/rider-rebuild/selected-sleeve-component47/sleeve47.py',
             'sha256': 'a90e56476dffc95b1089a6d2af6df75e75fd3bfe10df173a9135d55014ea3b84'}
PENDING = 'UNACCEPTED_PROXIMAL50_SAVED_REOPEN_PENDING'
QUALIFIED = 'UNACCEPTED_PROXIMAL50_REOPENED_DISTAL_AND_MOTION_PENDING'


def read(row): return json.loads(checked(row).read_text())


def module(row, name):
    spec = importlib.util.spec_from_file_location(name, checked(row))
    value = importlib.util.module_from_spec(spec); spec.loader.exec_module(value)
    return value


def freeze(output):
    output = Path(output).resolve(); assert output.is_relative_to(HERE) and not output.exists()
    frozen = read(SOURCE47)
    for row in frozen['pins'].values(): checked(row)
    config = {**frozen, 'sourceInput47': SOURCE47,
        'operation': 'ONE_EXPLICIT_BROAD_PROXIMAL_SELECTED_HOODIE_REST_REGISTRATION',
        'retired45mmRepairGateClaimed': False, 'pins': {**frozen['pins'],
            'component50': pin(__file__), 'registration50': pin(HERE/'registration.py'),
            'wrapper47': WRAPPER47}}
    write(output, config); print(json.dumps({'input': pin(output), 'nativeRunExecuted': False}))


def source_gate(config):
    assert config['sourceInput47'] == SOURCE47 and config['acceptedArt'] is False
    assert config['retired45mmRepairGateClaimed'] is False
    original = read(SOURCE47)
    assert config['field'] == original['field']
    assert all(config['pins'][k] == v for k, v in original['pins'].items())
    assert config['pins']['component50'] == pin(__file__)
    assert config['pins']['registration50'] == pin(HERE/'registration.py')
    assert config['pins']['wrapper47'] == WRAPPER47
    for row in config['pins'].values(): checked(row)
    receipt = read(config['pins']['gloveReceipt']); c47['intake_gate'](receipt)
    return receipt


def transformed_source():
    wrapper = runpy.run_path(str(checked(WRAPPER47)))
    source = wrapper['transformed_source']()
    marker = '    surgery = B.Surgery(hoodie, source)\n'
    assert source.count(marker) == 1
    source = source[:source.index(marker)]+'    build({**globals(), **locals()})\n'
    old = "ROOT/'harness/out/rider-rebuild/selected-sleeve-component47'"
    assert source.count(old) == 1
    return wrapper, source.replace(old, "ROOT/'harness/out/rider-rebuild/selected-proximal-hoodie-fit50'")


def invariant(obj, faces, author, np):
    mesh = obj.data
    weights = hashlib.sha256()
    for vertex in mesh.vertices:
        weights.update(struct.pack('<I', len(vertex.groups)))
        for group in vertex.groups: weights.update(struct.pack('<If', group.group, group.weight))
    uv = {}
    for layer in mesh.uv_layers:
        values = np.empty((len(mesh.loops), 2), np.float32); layer.data.foreach_get('uv', values.ravel())
        uv[layer.name] = hashlib.sha256(values.tobytes()).hexdigest()
    attrs = {}
    for a in mesh.attributes:
        if not a.name.startswith('_'): continue
        assert a.data_type in {'INT', 'FLOAT', 'FLOAT_VECTOR'}, ('Unclassified source identity field', a.name, a.data_type)
        width = 3 if a.data_type == 'FLOAT_VECTOR' else 1
        values = np.empty((len(a.data), width), np.int32 if a.data_type == 'INT' else np.float32)
        a.data.foreach_get('vector' if width == 3 else 'value', values.ravel())
        attrs[a.name] = {'domain': a.domain, 'type': a.data_type,
                        'sha256': hashlib.sha256(values.tobytes()).hexdigest()}
    material = np.empty(len(mesh.polygons), np.int32); mesh.polygons.foreach_get('material_index', material)
    smooth = np.empty(len(mesh.polygons), bool); mesh.polygons.foreach_get('use_smooth', smooth)
    return {'vertices': len(mesh.vertices), 'triangles': len(faces),
        'topology': hashlib.sha256(faces.tobytes()).hexdigest(), 'weights': weights.hexdigest(),
        'uv': uv, 'identityAttributes': attrs,
        'materialIndices': hashlib.sha256(material.tobytes()).hexdigest(),
        'smoothFlags': hashlib.sha256(smooth.tobytes()).hexdigest(),
        'metadata': c47['canonical'](c47['metadata'](obj, author['packed_maps']))}


def corner_normals(obj, np):
    values = np.empty((len(obj.data.corner_normals), 3), np.float32)
    obj.data.corner_normals.foreach_get('vector', values.ravel())
    return values


def build(context):
    c = context; np = c['np']; bpy = c['bpy']; config = c['config']
    intake = source_gate(config); registration = module(config['pins']['registration50'], 'proximal50_math')
    hoodie = c['hoodie']; mesh = hoodie.data
    original = c['B'].A['points'](hoodie)[1]; faces = c['B'].A['faces'](hoodie)
    assert len(original) == len(c['source']) and all(len(p.vertices) == 3 for p in mesh.polygons)
    author = runpy.run_path(str(checked(c['prior']['restHelper'])))
    before = invariant(hoodie, faces, author, np)
    normals = corner_normals(hoodie, np)
    loop_vertices = np.empty(len(mesh.loops), np.int32); mesh.loops.foreach_get('vertex_index', loop_vertices)
    groups = {g.index: g.name for g in hoodie.vertex_groups}
    arm = {i for i, name in groups.items() if name.startswith(('DEF-shoulder.', 'DEF-upper_arm.', 'DEF-forearm.', 'DEF-hand.'))}
    seeds = np.array([sum(g.weight for g in v.groups if g.group in arm) > .5 for v in mesh.vertices])
    assert seeds.sum() > 20000
    # Exact frozen28 scheduled distal-removal predicates, independently source
    # pinned. No body/garment face is deleted by this proximal operation.
    retained = np.ones(len(faces), bool); removed = {}
    for side in ('L', 'R'):
        xyz, _, _, _, _, scalar, _ = c['B'].source_sleeve_frame(c['source'], c['controls'], side)
        owned = c['ownership']['hands'][side]; data = np.load(checked(owned['arrays']))
        own_side = xyz[:, 0] > 0 if side == 'L' else xyz[:, 0] < 0
        terminal = np.all(own_side[faces], axis=1) & (scalar[faces].max(1) > owned['upperSourceAxialM'])
        inward = np.isin(np.arange(len(faces)), data['innerSourceFaceIds'])
        inward &= (scalar[faces].min(1) > owned['lowerSourceAxialM']) & (scalar[faces].max(1) < owned['upperSourceAxialM'])
        retained &= ~(terminal | inward)
        removed[side] = {'terminalCutFaces': int(terminal.sum()), 'replacedInwardFaces': int(inward.sum())}
    c['progress']('BROAD PROXIMAL50 original paired cloth and actual full anatomy')
    moved, differential, changed, maps, report = registration.register(c['field_helper'], original,
        faces[retained], seeds, c['actual_nearest'](c['bp'], c['bf']), config['field'], c['progress'])
    out = c['out']; out.mkdir(parents=True)
    arrays = {'changedOriginalNativeIds': changed, 'mapCount': np.array(len(maps), dtype=np.int32)}
    for i, field in enumerate(maps):
        for name in ('origin', 'shape', 'values', 'active'): arrays[str(i)+'_'+name] = getattr(field, name)
        arrays[str(i)+'_spacing'] = np.array(field.spacing)
    np.savez_compressed(out/'registration-maps.npz', **arrays)
    # One source differential carries every original corner normal, preserving
    # selected normal detail under the same deformation as its source vertex.
    transformed = np.empty_like(normals)
    for start in range(0, len(normals), 16384):
        end = start+16384
        inverse = np.linalg.inv(differential[loop_vertices[start:end]])
        vector = np.einsum('nji,nj->ni', inverse, normals[start:end].astype(float))
        length = np.linalg.norm(vector, axis=1)
        vector = np.divide(vector, length[:, None], out=np.zeros_like(vector), where=length[:, None] > 0)
        transformed[start:end] = vector
    mesh.vertices.foreach_set('co', moved.astype(np.float32).ravel()); mesh.update()
    mesh.normals_split_custom_set(transformed.tolist()); mesh.update()
    assert c47['canonical'](author['rest'](c['rig'])) == c47['canonical'](c['rest_before'])
    # Raw save precedes postconstruction full geometry/field/strain scans.
    del transformed, normals, arrays, maps, inverse, vector
    gc.collect(); c['progress']('SAVE actual broad proximal50 native before qualification')
    native = c47['save_native'](out, 'UNACCEPTED-selected-proximal-hoodie-fit50.blend', bpy)
    result = {'acceptedArt': False, 'status': PENDING, 'sourceRecipe': pin(__file__),
        'registrationRecipe': config['pins']['registration50'], 'input': pin(c['config_path']),
        'sourceInput47': SOURCE47, 'sourceIntake47': config['pins']['gloveReceipt'],
        'sourceComponentReceipt41': config['pins']['componentReceipt41'],
        'originalSourceGLB': c['prior']['originalHoodie'], 'native': native,
        'sourceVertexCount': len(original), 'sourceTriangleCount': len(faces),
        'scope': sorted(c47['OBJECTS']), 'broadRegistration': report,
        'registrationMaps': pin(out/'registration-maps.npz'),
        'scheduledDistalRemovalExcludedFromConstraints': removed,
        'protectedValidationPassed': False, 'sourceInvariantExact': False,
        'topologyAndSourceVertexOrderUnchanged': False, 'exact75RestUnchanged': False,
        'fullReferenceUnchanged': False, 'geometryGatesPassed': False, 'movingReviewPassed': False,
        'nativeStorage': {'compressed': False, 'reopenVerified': False},
        'limits': ['Original45mm small-repair constructor retired; this is explicit broad rest tailoring.',
            'No topology changes or inward-only deletion occur in proximal50.',
            'Full triangle relations and generic/actual-bike moving appearance remain unaccepted.']}
    write(out/'component-raw.json', result)
    assert invariant(hoodie, faces, author, np) == before
    witness = {'protectedGeometry': c['before'], 'rest': c['rest_before'], 'sourceInvariant': before,
        'rebuiltHoodieGeometry': c['geometry'](hoodie),
        'rebuiltCornerNormals': hashlib.sha256(corner_normals(hoodie, np).tobytes()).hexdigest()}
    write(out/'expected-witness.json', witness)
    singular = np.linalg.svd(differential, compute_uv=False)
    determinant = np.linalg.det(differential)
    assert float(determinant.min()) > 0
    result['actualSourcePointDifferential'] = {'minimumDeterminant': float(determinant.min()),
        'minimumSingularValue': float(singular.min()), 'maximumSingularValue': float(singular.max()),
        'singularValuePercentiles': np.percentile(singular, [0, 1, 50, 99, 100]).tolist()}
    result['expectedWitness'] = pin(out/'expected-witness.json')
    result['expectedRebuiltHoodieGeometry'] = witness['rebuiltHoodieGeometry']
    write(out/'component-pending.json', result)
    print(json.dumps({'native': native, 'status': PENDING,
        'contactSamplesPassed': report['constructionContactSamplesPassed']}), flush=True)


def construct():
    wrapper, source = transformed_source()
    namespace = {'__name__': 'proximal50_selected_intake', '__file__': str(checked(wrapper['ORIGINAL'])),
        'helper47': wrapper['helper47'], 'ORIGINAL': wrapper['ORIGINAL'], 'WRAPPER': __file__,
        'gc': gc, 'build': build}
    exec(compile(source, namespace['__file__'], 'exec'), namespace)
    namespace['main']()


def qualify(path, bpy):
    import numpy as np
    path = Path(path).resolve(); assert path.is_relative_to(OUT)
    report = json.loads(path.read_text()); assert report['status'] == PENDING
    config = read(report['input']); source_gate(config)
    assert report['sourceRecipe'] == pin(__file__) and report['registrationRecipe'] == config['pins']['registration50']
    expected = read(report['expectedWitness']); prior = read(config['pins']['priorInputs'])
    author, geometry = c47['helpers'](prior)
    assert bpy.ops.wm.open_mainfile(filepath=str(checked(report['native'])), use_scripts=False) == {'FINISHED'}
    rig = c47['scoped'](bpy); hoodie = bpy.data.objects['RiderHoodie']
    assert hoodie.matrix_world.is_identity and not hoodie.data.shape_keys
    assert c47['canonical'](author['rest'](rig)) == expected['rest']
    assert set(expected['protectedGeometry']) == c47['PROTECTED']
    for name, value in expected['protectedGeometry'].items(): assert geometry(bpy.data.objects[name]) == value
    assert geometry(hoodie) == expected['rebuiltHoodieGeometry'] == report['expectedRebuiltHoodieGeometry']
    assert hashlib.sha256(corner_normals(hoodie, np).tobytes()).hexdigest() == expected['rebuiltCornerNormals']
    hoodie.data.calc_loop_triangles()
    faces = np.empty((len(hoodie.data.loop_triangles), 3), np.int32)
    hoodie.data.loop_triangles.foreach_get('vertices', faces.ravel())
    assert invariant(hoodie, faces, author, np) == expected['sourceInvariant']
    assert len(hoodie.data.vertices) == report['sourceVertexCount'] and len(faces) == report['sourceTriangleCount']
    checked(report['registrationMaps'])
    report.update(status=QUALIFIED, protectedValidationPassed=True, sourceInvariantExact=True,
        topologyAndSourceVertexOrderUnchanged=True, exact75RestUnchanged=True, fullReferenceUnchanged=True,
        protectedGeometryUnchanged=expected['protectedGeometry'],
        protectedValidationStage='SEPARATE_REOPENED_COMPONENT_NATIVE', pendingReceipt=pin(path))
    report['nativeStorage']['reopenVerified'] = True
    write(path.parent/'component-qualified.json', report)


if __name__ == '__main__':
    args = sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else sys.argv[1:]
    if args[0] == 'freeze':
        assert len(args) == 2; freeze(args[1])
    elif args[0] == 'qualify':
        assert len(args) == 2
        import bpy
        qualify(args[1], bpy)
    else:
        assert len(args) == 2
        construct()
