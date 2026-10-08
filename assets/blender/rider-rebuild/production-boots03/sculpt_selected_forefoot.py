"""Direct selected dense forefoot edit; private unaccepted source construction.

Parent CPU2 lease required. No lattice, retopology, registration, projection or
bake. Existing selected rear alignment is retained; ORIGINAL toe vertices are
edited with three ordinary proportional artist controls. Never run on players.
blender -b -t 2 --python-exit-code 1 --python THIS -- FRESH_OUTPUT
"""
import hashlib
import json
from pathlib import Path
import sys

import bpy
import numpy as np
from mathutils import Matrix, Vector

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
CONFIG_PATH = HERE / 'sculpt-controls.json'
CONFIG = json.loads(CONFIG_PATH.read_text())
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()


def pinned(name):
    spec = CONFIG['inputs'][name]
    path = ROOT / spec['path']
    assert sha(path) == spec['sha256'], ('Changed source', name)
    return path


def smooth(value):
    value = np.clip(value, 0., 1.)
    return value * value * (3. - 2. * value)


def edit_original_forefoot(original, retained_rear, side):
    """Grab distal cap medially; expand ball; raise only dorsal leather.

    Each vertex and face survives. No surface resampling or cap replacement.
    Original rounded cap remains rounded because the lift fades out vertically
    toward its welt, including the low original nose. Sole receives medial and
    width edits too, keeping original welt/outsole under the edited upper.
    """
    spec = CONFIG['sides'][side]
    sx, sy, sz = spec['scales']
    control = CONFIG['directSculpt']
    x, y, z = original.T
    progress = np.clip((control['toeDriftStartSourceX'] - x) /
                       (control['toeDriftStartSourceX'] - control['noseSourceX']), 0., 1.)
    # One smooth Grab displacement, equal across upper, welt and sole at X.
    medial_delta_m = spec['distalMedialGrabM'] * progress ** 1.3
    # Medial is +transverse R / -transverse L; source Z correspondence is
    # unchanged through the whole last. Source delta Z is positive both sides.
    result = original.copy().astype(np.float64)
    result[:, 2] += medial_delta_m / sz
    width_brush = np.exp(-((x - control['ballSourceX']) / control['ballBrushRadiusSource']) ** 2)
    result[:, 2] += (z - control['ballWidthPivotSourceZ']) * spec['ballWidthGain'] * width_brush
    # Physical, hand-authored dorsal Grab depths. These are sculpture controls,
    # not a fit to every body point. Smooth interval blending avoids a toe wall.
    knots = np.array(control['dorsalGrabSourceX'])
    lifts = np.array(spec['dorsalGrabM'])
    interval = np.clip(np.searchsorted(knots, x, side='right') - 1, 0, len(knots)-2)
    alpha = smooth((x-knots[interval]) / (knots[interval+1]-knots[interval]))
    lift_m = lifts[interval]*(1.-alpha) + lifts[interval+1]*alpha
    dorsal = smooth((y-control['unmovedWeltSourceY']) /
                    (control['fullyDorsalSourceY']-control['unmovedWeltSourceY']))
    result[:, 1] += lift_m / sy * dorsal
    # Reuse useful selected rear alignment only. The rejected flat toe is never
    # an input to the fully authored toe. Zero drift at the rear preserves its
    # lace/tongue/heel correspondence. Never blend a reflection across a mesh.
    rear = smooth((x-control['originalToeFullBeforeSourceX']) /
                  (control['retainedRearFullAfterSourceX']-control['originalToeFullBeforeSourceX']))
    result = result*(1.-rear[:, None]) + retained_rear*rear[:, None]
    held = x >= control['retainedRearFullAfterSourceX']
    assert np.array_equal(result[held], retained_rear[held])
    return result, {'originalVertexCount': len(original), 'retainedRearVertices': int(held.sum()),
                    'changedForefootVertices': int(np.sum(np.any(result != retained_rear, axis=1))),
                    'retainedRearMaximumDeltaSource': float(np.max(abs(result[held]-retained_rear[held]))),
                    'maximumMedialGrabM': float(medial_delta_m.max())}


def affine(body, side):
    spec = CONFIG['sides'][side]
    names = body['jointNames'].tolist()
    ankle = body['jointHeads'][names.index('DEF-foot.' + side)]
    toe = body['jointHeads'][names.index('DEF-toe.' + side)]
    toward = np.r_[toe[:2]-ankle[:2], 0.]
    toward /= np.linalg.norm(toward)
    long = -toward
    frame = np.column_stack([long, [0., 0., 1.], np.cross(long, [0., 0., 1.])])
    transform = np.eye(4)
    signed_scales = np.array(spec['scales'])
    signed_scales[2] *= spec['mirrorWidth']
    transform[:3, :3] = frame * signed_scales[None, :]
    transform[:3, 3] = np.r_[ankle[:2], 0.] + np.einsum('ij,j->i', frame, spec['offset'])
    return transform, frame, ankle


def wearer_snapshot(body, rig):
    return {'vertices': [tuple(v.co) for v in body.data.vertices],
            'polygons': [tuple(p.vertices) for p in body.data.polygons],
            'groups': [[(g.group, g.weight) for g in v.groups] for v in body.data.vertices],
            'rest75': [(b.name, tuple(b.head_local), tuple(b.tail_local),
                        tuple(tuple(r) for r in b.matrix_local)) for b in rig.data.bones],
            'visibility': (body.hide_render, body.hide_viewport)}


def material():
    mat = bpy.data.materials.new('Exact selected boot original 4096 PBR')
    mat.use_nodes = True
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    bsdf = nodes.get('Principled BSDF')
    color = nodes.new('ShaderNodeTexImage')
    color.image = bpy.data.images.load(str(pinned('albedo')), check_existing=True)
    color.image.colorspace_settings.name = 'sRGB'
    color.image.pack()
    mr = nodes.new('ShaderNodeTexImage')
    mr.image = bpy.data.images.load(str(pinned('metallicRoughness')), check_existing=True)
    mr.image.colorspace_settings.name = 'Non-Color'
    mr.image.pack()
    links.new(color.outputs['Color'], bsdf.inputs['Base Color'])
    channels = nodes.new('ShaderNodeSeparateColor')
    channels.mode = 'RGB'
    links.new(mr.outputs['Color'], channels.inputs['Color'])
    links.new(channels.outputs['Green'], bsdf.inputs['Roughness'])
    links.new(channels.outputs['Blue'], bsdf.inputs['Metallic'])
    return mat


def mesh_object(name, source_vertices, dense, body_arrays, side, mat):
    transform, frame, ankle = affine(body_arrays, side)
    vertices = np.einsum('nj,ij->ni', source_vertices, transform[:3, :3]) + transform[:3, 3]
    reverse = bool(np.linalg.det(transform[:3, :3]) < 0)
    corner_order = [0, 2, 1] if reverse else [0, 1, 2]
    faces = dense['faces'][:, corner_order]
    uv = dense['originalCornerUV'][:, corner_order].copy()
    uv[:, :, 1] = 1.-uv[:, :, 1]
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices.tolist(), [], faces.tolist())
    mesh.update()
    layer = mesh.uv_layers.new(name='Exact selected raw corner UV copied with Blender V flip')
    layer.data.foreach_set('uv', uv.ravel())
    mesh.materials.append(mat)
    # Original declares no NORMAL. Recompute geometric smooth normals after
    # actual sculpture; do not preserve invalid pre-sculpt normals.
    for p in mesh.polygons:
        p.use_smooth = True
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj['selectedDenseSource'] = CONFIG['inputs']['dense']['sha256']
    obj['accepted'] = False
    return obj, vertices, frame, ankle, reverse


def weight_boot(obj, vertices, frame, ankle, side, rig):
    groups = {n: obj.vertex_groups.new(name=n) for n in
              ('DEF-foot.'+side, 'DEF-toe.'+side, 'DEF-shin.'+side+'.001')}
    origin = np.r_[ankle[:2], 0.]
    longitudinal = np.einsum('ni,i->n', vertices-origin, frame[:, 0])
    toe = .08*smooth((-longitudinal-.105)/.060)
    shin = .12*smooth((vertices[:, 2]-.080)/.060)
    toe[vertices[:, 2] < .026] = 0.
    shin[vertices[:, 2] < .026] = 0.
    for i in range(len(vertices)):
        for name, weight in [('DEF-foot.'+side, 1.-toe[i]-shin[i]),
                             ('DEF-toe.'+side, toe[i]), ('DEF-shin.'+side+'.001', shin[i])]:
            if weight:
                groups[name].add([i], float(weight), 'REPLACE')
    modifier = obj.modifiers.new('Actual unchanged native75 shared wearer', 'ARMATURE')
    modifier.object = rig
    obj.parent = rig
    obj.matrix_parent_inverse = rig.matrix_world.inverted()


def render_comparison(scene, out, original, sculpted, body, frame, ankle):
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = 8
    scene.cycles.use_denoising = True
    scene.render.threads_mode, scene.render.threads = 'FIXED', 2
    scene.render.resolution_x, scene.render.resolution_y = 800, 640
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.view_settings.view_transform = 'Standard'
    world = bpy.data.worlds.new('Selected boot comparison studio')
    world.use_nodes = True
    world.node_tree.nodes['Background'].inputs[0].default_value = (.25, .27, .31, 1.)
    world.node_tree.nodes['Background'].inputs[1].default_value = .6
    scene.world = world
    focus = np.r_[ankle[:2], 0.] + np.einsum('ij,j->i', frame, [-.105, .045, 0.])
    for i, offset in enumerate([[-.45, .60, -.40], [.35, .45, .30]]):
        data = bpy.data.lights.new('Sculpt comparison light '+str(i), 'AREA')
        data.energy, data.size = 45, 1.3
        lamp = bpy.data.objects.new(data.name, data)
        bpy.context.collection.objects.link(lamp)
        lamp.location = focus+np.einsum('ij,j->i', frame, offset)
        lamp.rotation_euler = (Vector(focus)-lamp.location).to_track_quat('-Z', 'Y').to_euler()
    data = bpy.data.cameras.new('Unchanged full-foot selected source comparison')
    data.type, data.ortho_scale = 'ORTHO', .38
    camera = bpy.data.objects.new(data.name, data)
    bpy.context.collection.objects.link(camera)
    scene.camera = camera
    for view, offset in [('lateral', [0., .12, -.65]), ('toe-threequarter', [-.50, .34, -.32])]:
        camera.location = focus+np.einsum('ij,j->i', frame, offset)
        camera.rotation_euler = (Vector(focus)-camera.location).to_track_quat('-Z', 'Y').to_euler()
        for role, chosen in [('original-selected', [original]), ('sculpted-selected', sculpted)]:
            allowed = {body.name, *(o.name for o in chosen)}
            for o in scene.objects:
                if o.type in {'MESH', 'CURVE', 'SURFACE', 'FONT', 'META'}:
                    o.hide_render = o.name not in allowed
            body.hide_render = False
            scene.render.filepath = str(out/(role+'-'+view+'.png'))
            bpy.ops.render.render(write_still=True)
    # Save with actual edited pair visible and original parked as hidden ref.
    original.hide_render = True
    original.hide_set(True)
    for o in sculpted:
        o.hide_render = False
        o.hide_set(False)


def main():
    arguments = sys.argv[sys.argv.index('--')+1:]
    assert len(arguments) == 1
    out = Path(arguments[0]).resolve()
    assert not out.exists() and out.is_relative_to(ROOT/'harness/out/rider-rebuild/production-boots03')
    paths = {k: pinned(k) for k in CONFIG['inputs']}
    dense = dict(np.load(paths['dense']))
    body_arrays = dict(np.load(paths['bodyArrays']))
    retained = dict(np.load(paths['retainedRear']))
    assert np.array_equal(retained['sourceOriginalDenseVertexRows'], np.arange(len(dense['vertices'])))
    assert np.array_equal(retained['originalDenseFaceRows'], np.arange(len(dense['faces'])))
    out.mkdir(parents=True)
    report = {'accepted': False, 'status': 'DIRECT_ORIGINAL_DENSE_SCULPT_IN_PROGRESS',
              'controlSHA256': sha(CONFIG_PATH), 'recipeSHA256': sha(__file__),
              'inputs': CONFIG['inputs'], 'sides': {}}
    save_report = lambda: (out/'report.json').write_text(json.dumps(report, indent=2)+'\n')
    save_report()
    bpy.ops.wm.open_mainfile(filepath=str(paths['wearer']))
    body, rig = bpy.data.objects['RiderBody'], bpy.data.objects['RiderSkeleton']
    before = wearer_snapshot(body, rig)
    assert len(rig.data.bones) == 75 and len(body.data.vertices) == 10582
    assert not body.hide_render and not body.hide_viewport
    mat = material()
    sculpted = []
    for side in ['R', 'L']:
        edited, receipt = edit_original_forefoot(dense['vertices'], retained['sourceAuthoredVertices'], side)
        obj, vertices, frame, ankle, reverse = mesh_object('SculptedSelectedDenseBoot.'+side,
                                                        edited, dense, body_arrays, side, mat)
        weight_boot(obj, vertices, frame, ankle, side, rig)
        receipt.update({'faces': len(dense['faces']), 'reflectedFaceAndUVCornerOrderTogether': reverse,
                        'nativeBounds': [vertices.min(0).tolist(), vertices.max(0).tolist()],
                        'medialBigToeTransverseSign': 1 if side == 'R' else -1,
                        'material': 'byte-exact selected 4096 albedo + metallicRoughness; no bake'})
        report['sides'][side] = receipt
        np.savez_compressed(out/('direct-sculpt-source-'+side+'.npz'),
                            editedOriginalDenseVertices=edited,
                            originalDenseVertexRows=np.arange(len(edited)),
                            originalDenseTriangleRows=np.arange(len(dense['faces'])))
        sculpted.append(obj)
        save_report()
    original, _, frame, ankle, _ = mesh_object('UnchangedOriginalSelectedBoot.R',
                                               dense['vertices'], dense, body_arrays, 'R', mat)
    assert wearer_snapshot(body, rig) == before
    report['bodyAndRest75Unchanged'] = True
    report['denseTopologyPreserved'] = True
    report['uvPolicy'] = 'Raw corner UV unchanged; copied V=1-V; negative determinant L face/UV corners both reversed'
    report['sourceNormals'] = 'Selected original GLB has no NORMAL; geometric smooth normals recomputed after sculpt'
    report['status'] = 'UNACCEPTED_DENSE_SOURCE_SCULPT_REST_REVIEW_PENDING'
    save_report()
    native = out/'direct-selected-source-sculpt.blend'
    original.hide_render = True
    original.hide_set(True)
    bpy.ops.wm.save_as_mainfile(filepath=str(native))
    render_comparison(bpy.context.scene, out, original, sculpted, body, frame, ankle)
    assert wearer_snapshot(body, rig) == before
    bpy.ops.wm.save_as_mainfile(filepath=str(native))
    assert all(sha(paths[k]) == CONFIG['inputs'][k]['sha256'] for k in paths)
    report['native'] = {'path': str(native.relative_to(ROOT)), 'sha256': sha(native)}
    report['views'] = [p.name for p in sorted(out.glob('*.png'))]
    save_report()
    print(json.dumps({'status': report['status'], 'native': report['native'], 'views': report['views']}))


if __name__ == '__main__':
    main()
