"""Measure every actual native53pose-driver sample with authored garment skin.

The frozen driver has529continuous48Hz FK samples; these are synthetic
native fixtures, never claimed as actual supported bike poses or live collision.
"""
import argparse,hashlib,json,sys,time
from pathlib import Path
import bpy,numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ap=argparse.ArgumentParser(description=__doc__)
for k in ['source','driver','out']:ap.add_argument('--'+k,required=True)
a=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);source,driver_path,out=[Path(getattr(a,k)).resolve() for k in ['source','driver','out']]
out.mkdir(parents=True,exist_ok=True);assert not (out/'motion.json').exists(),'Preserve frozen motion measurement'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();pins={str(p):sha(p) for p in [source,driver_path]}
assert pins[str(source)]=='d3f05ff00755c0fb9e4245465092333ace538098e86eb44e4ad057e4c68d8996'
assert pins[str(driver_path)]=='8c40c42af362a8d3d8ae44d27a0b07570f600b26adc66d325239413f66c7625b'
bpy.ops.wm.open_mainfile(filepath=str(source));d=json.loads(driver_path.read_text());rig=bpy.data.objects['Independent anatomical foundation rig']
body=bpy.data.objects['Canonical anatomical body, baked adult hm08'];g=bpy.data.objects['Selected Hunyuan authored skin wearable, unaccepted']
assert len(d['frames'])==529 and set(d['jointOrderNative'])==set(rig.data.bones.keys())
def surface(o):
    e=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=e.to_mesh();m.calc_loop_triangles()
    p=np.array([list(e.matrix_world@v.co) for v in m.vertices]);f=[tuple(t.vertices) for t in m.loop_triangles];e.to_mesh_clear()
    return p,f,BVHTree.FromPolygons([Vector(x) for x in p],f,all_triangles=True)
records=[];start=time.monotonic();body_peaks=[];self_peaks=[]
for frame in d['frames']:
    for name,trs in frame['poseBasisBlender'].items():
        bone=rig.pose.bones[name];bone.rotation_mode='QUATERNION';bone.location=trs['location'];bone.rotation_quaternion=trs['quaternionWXYZ'];bone.scale=trs['scale']
    bpy.context.view_layer.update();bp,bf,bt=surface(body);gp,gf,gt=surface(g)
    assert np.isfinite(bp).all() and np.isfinite(gp).all()
    pairs=gt.overlap(bt);selfpairs=[(i,j) for i,j in gt.overlap(gt) if i<j and not set(gf[i])&set(gf[j])]
    record={'frame':frame['index'],'timeS':frame['timeS'],'endpoint':frame['endpoint'],'segment':frame['segment'],
            'bodyTrianglePairs':len(pairs),'nonAdjacentSelfTrianglePairs':len(selfpairs),'firstBodyWitnesses':pairs[:8],'firstSelfWitnesses':selfpairs[:8]}
    records.append(record);body_peaks.append(len(pairs));self_peaks.append(len(selfpairs))
    if frame['index']%48==0:print('NATIVE_SELECTED_MOTION',frame['index'],len(pairs),len(selfpairs),flush=True)
    assert time.monotonic()-start<300,'Own bounded native measurement cap; no foreign job affected'
report={'status':'UNACCEPTED authored garment native continuous pose measurement; root judges wearing',
        'pins':pins,'recipeSHA256':sha(__file__),'frames':records,'measuredFrames':len(records),'sampleRateHz':48,'elapsedS':time.monotonic()-start,
        'maximumBodyTrianglePairs':max(body_peaks),'maximumSelfTrianglePairs':max(self_peaks),
        'bodyContactFrames':sum(x>0 for x in body_peaks),'selfContactFrames':sum(x>0 for x in self_peaks),
        'worstBodyFrame':body_peaks.index(max(body_peaks)),'worstSelfFrame':self_peaks.index(max(self_peaks)),
        'playedDriverFrameIndices':list(range(0,len(records),4)),
        'limits':['Actual evaluated Blender Armature skin and original body at every52948Hz FK sample; no cloth/collision correction or source editing.',
                  'Triangle pairs are contact witnesses, not penetration depth or complete between-sample continuous collision proof.',
                  'Native synthetic fixtures are not actual bike controller/support poses; exported rig/weights/engine mapping independently verified byAgent3.',
                  'Selected-source PBR/rest/body/head/51bind remain immutable; root alone judges played likeness/wearing, allM0-M5/mobile open.']}
assert pins=={p:sha(p) for p in pins};(out/'motion.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:report[k] for k in ['maximumBodyTrianglePairs','maximumSelfTrianglePairs','bodyContactFrames','selfContactFrames','elapsedS']}),flush=True)
