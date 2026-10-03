"""Test a connected donor-guided sewn deformation with a qualified seed audit.

Texture/UV lineage stays frozen. This static construction test is not a skin or
collision-response solver; all source artifacts and failed controls are kept.
"""
import argparse,hashlib,json,sys,math
from pathlib import Path
import bpy,bmesh,numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ap=argparse.ArgumentParser(description=__doc__)
for name in ['source','seed-builder','out','evidence']:ap.add_argument('--'+name,required=True)
a=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);source,seed_builder,out,evidence=[Path(getattr(a,n.replace('-','_'))).resolve() for n in ['source','seed-builder','out','evidence']]
out.mkdir(parents=True,exist_ok=True);evidence.mkdir(parents=True,exist_ok=True);assert not (out/'connected.blend').exists()
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();pins={str(p):sha(p) for p in [source,seed_builder]}
assert pins[str(source)]=='83f53ae355d78195698308f2fe5a466c264ac358f00f6a48bacd4cfb646a3a74'
bpy.ops.wm.open_mainfile(filepath=str(source));body=bpy.data.objects['Canonical anatomical body, baked adult hm08'];pattern=bpy.data.objects['Separate fitted sweatshirt control, hood not constructed']
old=bpy.data.objects['Selected Hunyuan sewn wearable, unrigged construction']
code=seed_builder.read_text();code=code[code.index('vertices=[list'):code.index('lineage=[];unmapped=[];maximum_fit_adjustment=0')]
assert code.count('-.03+.10*math.cos(theta)')==1
assert code.count('q[0]-=.025*math.sin(math.pi*t)')==1
# Keep the generated donor-sized back/side silhouette, but stop the seed's
# front fold from bending into the body before donor deformation starts.
code=code.replace('-.03+.10*math.cos(theta)','-.01+.12*math.cos(theta)')
code=code.replace('q[0]-=.025*math.sin(math.pi*t)','q[0]-=.025*max(0.,-math.cos(theta))*math.sin(math.pi*t)')
seed_namespace={'bpy':bpy,'bmesh':bmesh,'np':np,'math':math,'body':body,'pattern':pattern}
exec(compile(code,str(seed_builder),'exec'),seed_namespace)
seed=seed_namespace['garment'];seedxyz=np.array([list(v.co) for v in seed.data.vertices],dtype=np.float64)
assert len(seedxyz)==len(old.data.vertices)==5870
assert [list(f.vertices) for f in seed.data.polygons]==[list(f.vertices) for f in old.data.polygons]
edges=np.empty(len(seed.data.edges)*2,dtype=np.int32);seed.data.edges.foreach_get('vertices',edges);edges=edges.reshape(-1,2)
def tree(p,faces):return BVHTree.FromPolygons([Vector(x) for x in p],faces,all_triangles=True)
body.data.calc_loop_triangles();bf=[tuple(t.vertices) for t in body.data.loop_triangles];bp=np.array([list(v.co) for v in body.data.vertices]);bt=tree(bp,bf)
def audit(o):
 o.data.calc_loop_triangles();p=np.array([list(v.co) for v in o.data.vertices]);f=[tuple(t.vertices) for t in o.data.loop_triangles];t=tree(p,f)
 return {'vertices':len(p),'triangles':len(f),'bodyTrianglePairs':len(t.overlap(bt)),
  'nonAdjacentSelfTrianglePairs':sum(i<j and not set(f[i])&set(f[j]) for i,j in t.overlap(t)),
  'minimumVertexLocalSignedNormalGapM':min(float((Vector(x)-q).dot(n)) for x in p for q,n,tri,d in [bt.find_nearest(Vector(x))])}
seed_audit=audit(seed)
target=np.array([list(v.co) for v in old.data.vertices],dtype=np.float64)-seedxyz
degree=np.bincount(edges.ravel(),minlength=len(seedxyz)).astype(np.float64)
displacement=np.zeros_like(target)
for step in range(40):
 neighbor=np.zeros_like(displacement)
 np.add.at(neighbor,edges[:,0],displacement[edges[:,1]]);np.add.at(neighbor,edges[:,1],displacement[edges[:,0]])
 displacement=(target+8*neighbor)/(1+8*degree[:,None])
candidate=old.copy();candidate.data=old.data.copy();bpy.context.collection.objects.link(candidate)
candidate.name='Selected Hunyuan connected sewn wearable, unrigged'
constraint=[]
for i,(v,p) in enumerate(zip(candidate.data.vertices,seedxyz+displacement)):
 q,n,tri,d=bt.find_nearest(Vector(p));signed=float((Vector(p)-q).dot(n))
 adjustment=max(0.,.008-signed)
 if adjustment>.012:constraint.append({'vertex':i,'neededM':adjustment,'appliedM':.012,'unresolved':True})
 elif adjustment>0:constraint.append({'vertex':i,'neededM':adjustment,'appliedM':adjustment,'unresolved':False})
 v.co=Vector(p)+n*min(adjustment,.012)
candidate.data.update();candidate_audit=audit(candidate)
bpy.data.objects.remove(seed,do_unlink=True);old.hide_render=True;candidate.hide_render=False
candidate['accepted']=False;candidate['constructionStage']='Connected source deformation construction; static fit/self/coverage and independent rig/game/art pending'
bpy.ops.wm.save_as_mainfile(filepath=str(out/'connected.blend'),compress=True)
assert pins=={p:sha(p) for p in pins}
np.savez_compressed(out/'connected-field.npz',seedXYZ=seedxyz,targetDisplacement=target,connectedDisplacement=displacement,
 finalXYZ=np.array([list(v.co) for v in candidate.data.vertices]),edges=edges)
report={'status':'UNACCEPTED connected source construction control; rest audit determines failures',
 'pins':pins,'recipeSHA256':sha(__file__),'candidateSHA256':sha(out/'connected.blend'),'fieldSHA256':sha(out/'connected-field.npz'),
 'seed':seed_audit,'candidate':candidate_audit,'targetSource':'Exact source05 selected-donor geometry/PBR correspondence; old plain-shirt material never used',
 'connectedField':{'iterations':40,'edgeRegularization':8,'initialDisplacement':'zero','maximumDisplacementM':float(np.linalg.norm(displacement,axis=1).max()),
  'maximumGuideResidualM':float(np.linalg.norm(displacement-target,axis=1).max()),'RMSGuideResidualM':float(np.sqrt(np.mean(np.sum((displacement-target)**2,axis=1))))},
 'bodyFacingStaticConstraint':{'gapM':.008,'maximumAppliedM':.012,'vertices':constraint,'unresolvedVertices':sum(r['unresolved'] for r in constraint)},
 'hoodSeedChange':'Mouth front+.11m/back−.13m and backward bulge only on rear half; native20-column/12-ring shared neckline unchanged',
 'limits':['Connected Laplacian construction is static sculpting, not cloth physics/skinning/livecollision response.',
 'Guide residuals and bounded unresolved body constraints remain explicit; source05atlas/PBR lineage frozen, no new plain-shirt appearance.',
 'Seed and candidate must qualify body/self/coverage and moving shape before independent rig/game/mobile/art acceptance. No player promotion.']}
(evidence/'construction.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'seed':seed_audit,'candidate':candidate_audit,'unresolved':report['bodyFacingStaticConstraint']['unresolvedVertices']}),flush=True)
