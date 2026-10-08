"""Pinned complete selected outfit: native reach/open/curl/release/return.

Parent serialized CPU2 lease only. No export, source fitting or bike-pose claim.
blender -b -t 2 --python-exit-code 1 --python author.py -- CONFIG FRESH_OUT
CONFIG requires accepted:false, native/baseContract/sourceReceipt path+sha256.
"""
import hashlib
import json
import math
import runpy
import sys
from pathlib import Path
import bpy
from mathutils import Matrix, Quaternion, Vector

ROOT = Path(__file__).resolve().parents[4]
ACTION = 'UnacceptedSelectedDressedReachGripRelease145'
EXPECTED = {'RiderBody', 'RiderHoodie', 'RiderJeans', 'ActualSelectedGlove.L',
            'ActualSelectedGlove.R', 'ActualSelectedBoot.L', 'ActualSelectedBoot.R'}
STATIONS = (1, 13, 37, 49, 73, 85, 109, 145)
def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as handle:
        while block := handle.read(1024*1024): h.update(block)
    return h.hexdigest()


def pin(row):
    p = ROOT/row['path']; assert sha(p) == row['sha256'], ('Changed input', row); return p


def smooth(t):
    t = max(0., min(1., t)); return t*t*(3-2*t)


def basis(forward, normal):
    x = forward.normalized(); y = (normal-x*normal.dot(x)).normalized()
    return Matrix((x, y, x.cross(y))).transposed()


def main():
    args = sys.argv[sys.argv.index('--')+1:]; assert len(args) == 2
    config_path, out = (Path(p).resolve() for p in args)
    config = json.loads(config_path.read_text()); assert config['accepted'] is False
    assert not out.exists() and out.is_relative_to(ROOT/'harness/out/rider-rebuild/selected-dressed-motion01')
    native, contract_path, receipt_path = [pin(config[k]) for k in ('native', 'baseContract', 'sourceReceipt')]
    contract = json.loads(contract_path.read_text()); receipt = json.loads(receipt_path.read_text())
    assert receipt['native'] == config['native'] and receipt['accepted'] is False
    assert receipt['status'] == 'PRIVATE_SELECTED_MASKED_ENGINE_EXPORT_REVIEW_PENDING'
    assert set(receipt['objects']) == EXPECTED and receipt['rigAndContractExactNative75'] is True
    helper = ROOT/'assets/blender/rider-rebuild/head-neck-anatomical02/author-clothed-neck-motion.py'
    assert sha(helper) == '86cd010c88ad10cf3d5c925a133cdaafab760ac72a30a1e487d782a562fc71b2'
    helpers = runpy.run_path(str(helper)); geometry, rest_rows = helpers['geometry'], helpers['rest']
    bpy.ops.wm.open_mainfile(filepath=str(native)); scene = bpy.context.scene
    rig = bpy.data.objects['RiderSkeleton']; assert rig.matrix_world.is_identity
    assert len(rig.data.bones) == 75 and rig.animation_data is None
    assert not rig.constraints and all(not b.constraints and b.matrix_basis.is_identity for b in rig.pose.bones)
    assert {o.name for o in scene.objects if o.type == 'MESH' and not o.hide_render} == EXPECTED
    assert all(layer.material_override is None for layer in scene.view_layers)
    rows = [{'name': b.name, 'parent': b.parent.name if b.parent else None,
             'head': list(b.head_local), 'tail': list(b.tail_local),
             'matrix': [list(r) for r in b.matrix_local],
             'useConnect': b.use_connect, 'useDeform': b.use_deform} for b in rig.data.bones]
    assert rows == contract['nativeRest']['bones'], 'Exact corrected75 native rest required'
    names = [b.name for b in rig.data.bones]; meshes = [bpy.data.objects[n] for n in sorted(EXPECTED)]
    full_reference = bpy.data.objects['RiderBody__FullAnatomyReference']; assert full_reference.hide_render
    for obj in meshes:
        arm = [m for m in obj.modifiers if m.type == 'ARMATURE']
        assert len(arm) == 1 and arm[0].object == rig
    before = {o.name: geometry(o) for o in meshes+[full_reference]}; before_rest = rest_rows(rig)
    object_state = [(o.name, o.hide_render, [list(r) for r in o.matrix_world]) for o in scene.objects]
    rest = {b.name: b.matrix_local.copy() for b in rig.data.bones}
    heads = {b.name: b.head_local.copy() for b in rig.data.bones}
    lengths, palms = {}, {}
    for side, suffix in [('left', 'L'), ('right', 'R')]:
        hand = contract['specification']['hands'][side]; wrist = hand['wristJointId']
        forward = (heads[hand['forwardJointId']]-heads[wrist]).normalized()
        radial = heads[hand['radialJointId']]-heads[hand['ulnarJointId']]
        normal = forward.cross(radial).normalized()*hand['normalSign']
        alignment = basis(Vector((0, -1, -.15)), Vector((0, 0, -1))) @ basis(forward, normal).inverted()
        palms[side] = alignment.to_quaternion() @ rest[wrist].to_quaternion()
        upper, lower = 'DEF-upper_arm.'+suffix, 'DEF-forearm.'+suffix
        lengths[side] = [(heads[lower]-heads[upper]).length, (heads[wrist]-heads[lower]).length]

    def world_rotation(name, rotation):
        bone = rig.pose.bones[name]; matrix = rotation.to_matrix().to_4x4()
        matrix.translation = bone.matrix.translation.copy(); bone.matrix = matrix; bone.scale = (1, 1, 1)
        bpy.context.view_layer.update()

    def aim(group, end, direction):
        swing = (heads[end]-heads[group[0]]).normalized().rotation_difference(direction.normalized())
        for name in group: world_rotation(name, swing @ rest[name].to_quaternion())

    assert bpy.data.actions.get(ACTION) is None
    action = bpy.data.actions.new(ACTION); rig.animation_data_create(); rig.animation_data.action = action
    scene.render.fps = 24; scene.render.fps_base = 1; scene.frame_start = 1; scene.frame_end = 145
    observations = []; maximum_wrist_error = 0.
    for frame in range(1, 146):
        scene.frame_set(frame)
        for bone in rig.pose.bones:
            bone.rotation_mode = 'QUATERNION'; bone.location = (0, 0, 0)
            bone.rotation_quaternion = (1, 0, 0, 0); bone.scale = (1, 1, 1)
        bpy.context.view_layer.update()
        reach = smooth((frame-13)/24) if frame <= 109 else 1-smooth((frame-109)/36)
        grip = smooth((frame-49)/24) if frame <= 85 else 1-smooth((frame-85)/24)
        sample = {'frame': frame, 'reach': reach, 'curl': grip, 'arms': {}}
        if reach or grip:
            for side, suffix, sign in [('left', 'L', 1), ('right', 'R', -1)]:
                upper, lower, wrist = ['DEF-'+stem+'.'+suffix for stem in ('upper_arm', 'forearm', 'hand')]
                start = rig.pose.bones[upper].matrix.translation.copy()
                target = heads[wrist].lerp(Vector((sign*.22, -.49, 1.40)), reach)
                pole_point = heads[lower].lerp(Vector((sign*.36, -.20, 1.17)), reach)
                ray = target-start; distance = ray.length; ray.normalize()
                pole = pole_point-start; pole = (pole-ray*pole.dot(ray)).normalized()
                a, b = lengths[side]; assert abs(a-b) < distance < a+b, (frame, side, distance, a+b)
                along = (a*a+distance*distance-b*b)/(2*distance)
                elbow = start+ray*along+pole*math.sqrt(max(0., a*a-along*along))
                aim([upper, upper+'.001'], lower, elbow-start)
                aim([lower, lower+'.001'], wrist, target-elbow)
                world_rotation(wrist, rest[wrist].to_quaternion().slerp(palms[side], reach))
                for name, flex in contract['driver']['digitFlex'][side].items():
                    rig.pose.bones[name].rotation_quaternion = Quaternion(Vector(flex['axisLocal']), grip*flex['maxRadians'])
                points = [rig.pose.bones[n].matrix.translation.copy() for n in (upper, lower, wrist)]
                actual = [(points[1]-points[0]).length, (points[2]-points[1]).length]
                assert max(abs(x-y) for x, y in zip(actual, lengths[side])) < .0001
                error = (points[2]-target).length; maximum_wrist_error = max(maximum_wrist_error, error)
                assert error < .0001, ('Actual wrist misses solved target', frame, side, error)
                sample['arms'][side] = {'wrist': list(points[2]), 'target': list(target), 'segmentLengthsM': actual}
        bpy.context.view_layer.update()
        for bone in rig.pose.bones:
            assert all(math.isfinite(x) for r in bone.matrix_basis for x in r)
            for prop in ('location', 'rotation_quaternion', 'scale'):
                bone.keyframe_insert(data_path=prop, frame=frame, group=bone.name)
        if frame in STATIONS: observations.append(sample)
    assert len(action.slots) == 1
    for layer in action.layers:
        for strip in layer.strips:
            bag = strip.channelbag(action.slots[0])
            if bag:
                for curve in bag.fcurves:
                    for key in curve.keyframe_points: key.interpolation = 'LINEAR'
    # Exact keyed basis return proves identical deformation inputs without
    # allocating duplicate evaluated high-resolution outfit arrays.
    endpoints = []
    for frame in (1, 145):
        scene.frame_set(frame); bpy.context.view_layer.update()
        endpoints.append([[list(r) for r in b.matrix_basis] for b in rig.pose.bones])
        assert all(b.matrix_basis.is_identity for b in rig.pose.bones)
    assert endpoints[0] == endpoints[1] and before_rest == rest_rows(rig)
    assert before == {o.name: geometry(o) for o in meshes+[full_reference]}
    assert object_state == [(o.name, o.hide_render, [list(r) for r in o.matrix_world]) for o in scene.objects]
    scene.frame_set(1); out.mkdir(parents=True); candidate = out/'selected-dressed-generic145.blend'
    bpy.ops.wm.save_as_mainfile(filepath=str(candidate), compress=True)
    report = {'accepted': False, 'candidate': {'path': str(candidate.relative_to(ROOT)), 'sha256': sha(candidate)},
              'sourceNative': config['native'], 'baseContract': config['baseContract'], 'sourceReceipt': config['sourceReceipt'],
              'recipeSHA256': sha(__file__), 'configSHA256': sha(config_path), 'fingerprintHelperSHA256': sha(helper),
              'action': ACTION, 'actionSlot': action.slots[0].identifier, 'fps': 24, 'frameRange': [1, 145],
              'visibleMeshes': sorted(EXPECTED), 'exact75TRSKeyedEveryFrame': True, 'restAndOutfitFingerprintsUnchanged': before,
              'neutralBasisReturnExact': True, 'maximumWristTargetErrorM': maximum_wrist_error, 'observations': observations,
              'limits': ['Unaccepted actual selected dressed native generic review; parent judges played film.',
                         'Curl uses measured corrected75 local digit axes; no finite handlebar/contact claim.',
                         'No native crouch or bike pose invented: actual Garage/ride runtime provides contact/extremes.',
                         'No export, normal player promotion, source stock edits, or R0-R5 acceptance.']}
    (out/'motion.json').write_text(json.dumps(report, indent=2)+'\n')
    assert sha(native) == config['native']['sha256']
    print(json.dumps({'candidate': report['candidate'], 'action': ACTION, 'frames': 145}), flush=True)


if __name__ == '__main__': main()
