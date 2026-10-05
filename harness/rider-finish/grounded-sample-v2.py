"""Read-only30Hz forward/reverse analytic support pilot with evaluated bare soles."""
import argparse
import hashlib
import json
import sys
from pathlib import Path
import bpy
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
import grounded_driver_v2 as driver
p = argparse.ArgumentParser(description=__doc__)
for name in ['source', 'source-sha256', 'out']:
    p.add_argument('--'+name, required=True)
p.add_argument('--hz', type=int, default=driver.SAMPLING_HZ)
a = p.parse_args(sys.argv[sys.argv.index('--')+1:])
source, out = Path(a.source).resolve(), Path(a.out).resolve()
assert not out.exists() and a.hz == driver.SAMPLING_HZ
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert sha(source) == a.source_sha256
bpy.ops.wm.open_mainfile(filepath=str(source))
bpy.context.window.scene = bpy.data.scenes['Finish natural wearer diagnostic']
bpy.context.view_layer.update()
rig, body = bpy.data.objects['Finish rig'], bpy.data.objects['Finish body FOUR']
rig.hide_set(False); body.hide_set(False)
rig.hide_viewport = False; body.hide_viewport = False
body.animation_data_clear()
assert not body.data.shape_keys
assert len([m for m in body.modifiers if m.show_viewport]) == 1
xyz = np.array([v.co[:] for v in body.data.vertices])
world_rest = np.array([list(body.matrix_world @ v.co) for v in body.data.vertices])
names = [b.name for b in rig.data.bones]
weights = np.zeros((len(xyz), len(names)))
for v in body.data.vertices:
    for g in v.groups:
        name = body.vertex_groups[g.group].name
        if name in names:
            weights[v.index,names.index(name)] = g.weight
probes = {}
for side in ['L', 'R']:
    field = weights[:, [names.index('foot.'+side), names.index('ball.'+side)]].sum(axis=1)
    semantic = field > .95
    minimum = xyz[semantic,2].min()
    ids = np.flatnonzero(semantic & (xyz[:,2] <= minimum+.005))
    assert len(ids) >= 30
    probes[side] = ids
contract = driver.prepare(rig)
records = []
forward_pose_bytes = {}
clip_results = {}
for clip, duration in driver.CLIPS.items():
    count = round(duration*a.hz)
    assert abs(count/a.hz-duration) < 1e-12
    clip_results[clip] = {'durationS':duration, 'intervals':count, 'actualHz':a.hz, 'reversePoseBytesExact':True}
    timeline = [('forward', i) for i in range(count+1)]+[('reverse', i) for i in range(count,-1,-1)]
    previous_support = {}
    for direction,i in timeline:
        if i == count and direction == 'reverse':
            previous_support = {}
        time_s = i/a.hz
        command = driver.apply(rig,contract,clip,time_s)
        evaluated = body.evaluated_get(bpy.context.evaluated_depsgraph_get())
        mesh = evaluated.to_mesh()
        actual = np.array([list(evaluated.matrix_world @ mesh.vertices[int(j)].co) for ids in probes.values() for j in ids])
        assert np.isfinite(actual).all()
        evaluated.to_mesh_clear()
        offset = 0
        soles = {}
        for side,ids in probes.items():
            points = actual[offset:offset+len(ids)]
            offset += len(ids)
            rest = world_rest[ids]
            sole = {'minimumZWorldM':float(points[:,2].min()), 'maximumZWorldM':float(points[:,2].max()),
                           'within5mmFloorPoints':int(np.count_nonzero(np.abs(points[:,2])<=.005)),
                           'belowFloorBeyond1mmPoints':int(np.count_nonzero(points[:,2]<-.001)),
                           'maximumHorizontalDriftFromRestM':float(np.linalg.norm(points[:,:2]-rest[:,:2],axis=1).max()),
                           'xyzWorld':points.tolist()}
            phase = command['footPhases'][side]
            supported = phase in ['stance', 'double-support']
            previous = previous_support.get(side)
            sole['supportPhase'] = phase
            sole['declaredSupported'] = supported
            sole['maximumHorizontalStepDuringSupportM'] = float(np.linalg.norm(points[:,:2]-previous[:,:2],axis=1).max()) if supported and previous is not None else None
            previous_support[side] = points.copy() if supported else None
            soles[side] = sole
        pose = {b.name:{'location':list(b.location),'quaternionWXYZ':list(b.rotation_quaternion)} for b in rig.pose.bones}
        pose_values = np.array([v for n in names for key in ['location','quaternionWXYZ'] for v in pose[n][key]], dtype='<f8')
        pose_values[pose_values == 0] = 0 # Canonicalize signed-zero serialization only.
        pose_bytes = pose_values.tobytes()
        key = (clip,i)
        if direction == 'forward':
            forward_pose_bytes[key] = pose_bytes
        else:
            if pose_bytes != forward_pose_bytes[key]:
                clip_results[clip]['reversePoseBytesExact'] = False
        records.append({**command, 'direction':direction, 'sampleIdentity':i, 'soles':soles, 'poseBasis':pose})
    clip_results[clip]['closedPoseBytesExact'] = forward_pose_bytes[(clip,0)] == forward_pose_bytes[(clip,count)] if clip not in driver.LOCOMOTION else None
    clip_results[clip]['rootMotionPolicy'] = 'Forward translation in metres; reversing the exact pose sequence reverses root motion.' if clip in driver.LOCOMOTION else 'Closed stationary loop.'
    print('GROUND_CLIP',clip,len(timeline),'reverseExact',clip_results[clip]['reversePoseBytesExact'],flush=True)
assert sha(source) == a.source_sha256
out.parent.mkdir(parents=True,exist_ok=True)
report = {'status':'UNACCEPTED_ANALYTIC_GROUNDED_PILOT', 'source':str(source), 'sourceSHA256':sha(source),
          'driverSHA256':sha(driver.__file__),'readerSHA256':sha(__file__),'blender':bpy.app.version_string,
          'hz':a.hz,'clips':clip_results, 'locomotionParameters':driver.LOCOMOTION, 'unitsAxes':'Metres native+Xforward/+Zup/-Yleft; original+.65X rig world offset retained.',
          'soleProbeNativeVertexIDs':{s:ids.tolist() for s,ids in probes.items()}, 'records':records,
          'originalRestBindsUnchanged':True, 'limits':['Barefoot >.95 foot/ball semantic vertices within5mm of rest sole minimum; this is finite sampled surface support, not complete sole triangles/boots or a continuous-time certificate.',
          'Ankle residuals and actual deformed sole results are separate. Pelvis is not a centre-of-mass estimate.',
          'Native analytic pilot only: endpoint and reverse byte results are actual measured outputs, not implied. No art, natural gait, engine/GPU, bike-contact or device acceptance. No source file saved.']}
out.write_text(json.dumps(report,separators=(',',':'),allow_nan=False)+'\n')
print('GROUNDED_READY',len(records),out.stat().st_size,flush=True)
