"""Reproduce source21 native contacts and classify the failed affine envelopes."""
import argparse, collections, hashlib, json, sys
from pathlib import Path
import bpy, numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ap=argparse.ArgumentParser(description=__doc__)
for k in ['source','field','out']:ap.add_argument('--'+k,required=True)
a=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);source,field,out=[Path(getattr(a,k)).resolve() for k in ['source','field','out']]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();pins={str(p):sha(p) for p in [source,field]};data=np.load(field)
bpy.ops.wm.open_mainfile(filepath=str(source));g=bpy.data.objects['Actual selected donor, affine measured envelopes, unaccepted'];body=bpy.data.objects['Canonical anatomical body, baked adult hm08']
g.data.calc_loop_triangles();p=np.array([v.co[:] for v in g.data.vertices]);tri=np.array([t.vertices[:] for t in g.data.loop_triangles]);assert np.array_equal(p,data['finalNativeXYZ']);assert np.array_equal(tri,data['triangles']);body.data.calc_loop_triangles();bp=np.array([v.co[:] for v in body.data.vertices]);bt=np.array([t.vertices[:] for t in body.data.loop_triangles])
gtree=BVHTree.FromPolygons([Vector(v) for v in p],tri.tolist(),all_triangles=True);btree=BVHTree.FromPolygons([Vector(v) for v in bp],bt.tolist(),all_triangles=True)
sp=sorted((i,j) for i,j in gtree.overlap(gtree) if i<j and not set(tri[i])&set(tri[j]));bop=sorted(gtree.overlap(btree));assert sp==sorted(map(tuple,data['selfTrianglePairs']));assert bop==sorted(map(tuple,data['bodyTrianglePairs']))
alpha=data['armSeamWeight'];fore=data['forearmBlendWeight'];display=data['sourceDisplayXYZ'];old=data['previousNativeXYZ']
def part(i):
    ids=tri[i];a=float(alpha[ids].mean());w=float(fore[ids].mean());side='R' if display[ids,0].mean()>=0 else 'L'
    return 'torso/hood' if a<.01 else ('arm-seam.'+side if a<.99 else ('upperArm.'+side if w<.5 else 'forearm.'+side))
selfClass=collections.Counter('|'.join(sorted([part(i),part(j)])) for i,j in sp);bodyClass=collections.Counter(part(i) for i,j in bop)
rows=[]
for i,j in sp:
    ids=np.r_[tri[i],tri[j]];rows.append({'trianglePair':[i,j],'parts':[part(i),part(j)],'vertexIDs':ids.tolist(),'previousXYZ':old[ids].tolist(),'finalXYZ':p[ids].tolist(),'sourceXYZ':display[ids].tolist(),'seamWeights':alpha[ids].tolist(),'forearmWeights':fore[ids].tolist(),'registrationDeltaM':data['registrationDelta'][ids].tolist()})
heightBands=collections.Counter();bodyBoneClasses=collections.Counter();boneNames=set(bpy.data.objects['Independent anatomical foundation rig'].data.bones.keys())
for i,j in bop:
    z=float(p[tri[i],2].mean());heightBands['belowTorsoSupport' if z<1.04 else ('withinTorsoProfileHeight' if z<=1.475484 else 'aboveTorsoSupport')]+=1
    weights=collections.Counter()
    for v in bt[j]:
        for group in body.data.vertices[int(v)].groups:
            name=body.vertex_groups[group.group].name
            if name in boneNames:weights[name]+=group.weight/3
    bodyBoneClasses[max(weights,key=weights.get) if weights else 'noDeformBoneWeights']+=1
report={'bodyContactHeightBands':dict(heightBands),'bodyContactDominantRawSourceBoneClasses':dict(bodyBoneClasses),'status':'FAILED source21 affine envelope wearer prerequisite, read-only native reproduction','pins':pins,'recipeSHA256':sha(__file__),'positionsTrianglesAndContactSetsExactToField':True,'bodyPairs':len(bop),'selfPairs':len(sp),'bodyConstructionClasses':dict(bodyClass),'selfConstructionClasses':dict(selfClass),'allSelfWitnesses':rows,'limits':['Construction branch labels and profile supports are diagnostic only, not accepted anatomy or a complete injectivity proof.','459 body/79 self contacts remain failed prerequisites; no radius/iteration sweep or rig/motion/new capture. Original donor UV/PBR, all controls and body/head/51bind preserved. All art/wearing/mobile/M0-M5 remain open; parent alone judges.']}
assert pins=={p:sha(p) for p in pins};out.write_text(json.dumps(report,indent=2)+'\n');print('PROFILE_NATIVE_CONTACTS_REPRODUCED',dict(bodyClass),dict(selfClass),flush=True)
