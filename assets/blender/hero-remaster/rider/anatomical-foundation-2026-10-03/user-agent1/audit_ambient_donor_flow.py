"""Reproduce saved ambient-flow contacts and numerical inverse independently."""
import argparse, collections, hashlib, json, sys
from pathlib import Path
import bpy, numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ap=argparse.ArgumentParser(description=__doc__)
for k in ['source','field','report','recipe','out']:ap.add_argument('--'+k,required=True)
a=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);source,field,report,recipe,out=[Path(getattr(a,k)).resolve() for k in ['source','field','report','recipe','out']]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();pins={str(p):sha(p) for p in [source,field,report,recipe]};f=np.load(field);r=json.loads(report.read_text())
bpy.ops.wm.open_mainfile(filepath=str(source));g=bpy.data.objects['Actual selected donor, ambient measured-lumen flow, unaccepted'];body=bpy.data.objects['Canonical anatomical body, baked adult hm08'];g.data.calc_loop_triangles();p=np.array([v.co[:] for v in g.data.vertices]);tri=np.array([t.vertices[:] for t in g.data.loop_triangles]);assert np.array_equal(p,f['finalNativeXYZ']);assert np.array_equal(tri,f['triangles']);body.data.calc_loop_triangles();bp=np.array([v.co[:] for v in body.data.vertices]);bt=np.array([t.vertices[:] for t in body.data.loop_triangles])
gtree=BVHTree.FromPolygons([Vector(v) for v in p],tri.tolist(),all_triangles=True);btree=BVHTree.FromPolygons([Vector(v) for v in bp],bt.tolist(),all_triangles=True);sp=sorted((i,j) for i,j in gtree.overlap(gtree) if i<j and not set(tri[i])&set(tri[j]));bop=sorted(gtree.overlap(btree));assert sp==sorted(map(tuple,f['selfTrianglePairs']));assert bop==sorted(map(tuple,f['bodyTrianglePairs']))
generators=[];kernels=[]
for part,v in sorted(r['generators'].items()):generators.append((np.array(v['velocityMatrix']),np.array(v['velocityOffsetM']),None,None));kernels.append((np.array(v['kernelCenterM']),np.array(v['kernelAxis']),v['kernelAxialSigmaM'],v['kernelRadialSigmaM']))
definition=recipe.read_text();definition=definition[definition.index('def velocity('):definition.index('isolatedErrors=[]')];exec(compile(definition,str(recipe),'exec'));inverse=integrate(p,sign=-1);error=np.linalg.norm(inverse-f['previousNativeXYZ'],axis=1);assert error.max()<1e-6
boneNames=set(bpy.data.objects['Independent anatomical foundation rig'].data.bones.keys());classes=collections.Counter();witnesses=[]
for i,j in bop:
    weights=collections.Counter()
    for v in bt[j]:
        for group in body.data.vertices[int(v)].groups:
            name=body.vertex_groups[group.group].name
            if name in boneNames:weights[name]+=group.weight/3
    name=max(weights,key=weights.get) if weights else 'noDeformBoneWeights';classes[name]+=1
    witnesses.append({'garmentTriangle':i,'bodyTriangle':j,'garmentVertexIDs':tri[i].tolist(),'bodyVertexIDs':bt[j].tolist(),'dominantRawBodyBone':name,'garmentXYZ':p[tri[i]].tolist(),'bodyXYZ':bp[bt[j]].tolist(),'sourceDisplayXYZ':f['sourceDisplayXYZ'][tri[i]].tolist(),'beforeFlowXYZ':f['previousNativeXYZ'][tri[i]].tolist()})
result={'status':'UNACCEPTED saved ambient donor flow contact/inverse audit','pins':pins,'recipeSHA256':sha(__file__),'nativePositionsTrianglesContactSetsExactToArchive':True,'bodyPairs':len(bop),'selfPairs':len(sp),'bodyContactDominantRawBoneClasses':dict(classes),'allBodyWitnesses':witnesses,'maximumSavedNativeInverseClosureM':float(error.max()),'nativeInverseClosureMPercentiles':np.percentile(error,[0,50,95,100]).tolist(),'limits':['Inverse closure here uses actual saved float32 native positions; generator report forward/inverse value uses ideal float64 integration. Both are explicit, not a whole-volume injectivity proof.','46body contacts remain failed wearing prerequisites. No new fit, source mutation, capture, skin/rig/motion/collision response, body/head/51bind change, inference/worker/Library/player promotion or M0-M5/mobile acceptance.']}
assert pins=={p:sha(p) for p in pins};out.write_text(json.dumps(result,indent=2)+'\n');print('SAVED_AMBIENT_FLOW_REPRODUCED','bodyClasses',dict(classes),'nativeInverseM',float(error.max()),flush=True)
