"""Actual BVH proximity and camera-ray cloth coverage of unchanged skin.
Read-only anatomy/coverage audit after failed 2D prerequisite; no repaired geometry.
"""
import bpy,json,math,numpy as np,hashlib,time,resource
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from pathlib import Path
R=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/autonomous-lanes/B-local-volume');O=Path('/Users/raynos/projects/games/rockhop/docs/evidence/hero-remaster/one-rider-v2/autonomous-lanes/B-local-volume/trial03');O.mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();g=R/'trial02/character.glb';before=sha(g);t=time.monotonic();bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(g));meshes=[o for o in bpy.context.scene.objects if o.type=='MESH'];body=next(o for o in meshes if 'three-contour panel' in o.name);head=next(o for o in meshes if 'male head' in o.name)
bv=[body.matrix_world@v.co for v in body.data.vertices];bf=[tuple(p.vertices) for p in body.data.polygons];tree=BVHTree.FromPolygons(bv,bf,all_triangles=True,epsilon=0)
hv=np.array([head.matrix_world@v.co for v in head.data.vertices]);htree=BVHTree.FromPolygons([Vector(x) for x in hv],[tuple(p.vertices) for p in head.data.polygons],all_triangles=True,epsilon=0);skin=np.where(hv[:,2]<1.620)[0];points=hv[skin];dist=[];normalDot=[]
for x in points:
 hit,norm,face,dd=tree.find_nearest(Vector(x));dist.append(dd);normalDot.append(float((Vector(x)-hit).dot(norm)))
dist=np.array(dist);normalDot=np.array(normalDot);views=[]
for yaw in [0,45,90,180]:
 a=math.radians(yaw);camera=Vector((4*math.sin(a),.015-4*math.cos(a),1.56));occ=[];selfhidden=[]
 for x in points:
  ray=Vector(x)-camera;length=ray.length;hit,n,face,dd=tree.ray_cast(camera,ray.normalized(),length-.0001);occ.append(hit is not None);hh,hn,hf,hd=htree.ray_cast(camera,ray.normalized(),length-.0005);selfhidden.append(hh is not None)
 occ=np.array(occ);selfhidden=np.array(selfhidden);bands=[]
 for lo,hi in [(1.44,1.48),(1.48,1.50),(1.50,1.53),(1.53,1.56),(1.56,1.62)]:
  choose=(points[:,2]>=lo)&(points[:,2]<hi);ds=dist[choose];bands.append(dict(zRange=[lo,hi],skinVertices=int(choose.sum()),potentiallyCameraVisibleWithoutCloth=int(np.sum(choose&~selfhidden)),clothCoverageOfPotentiallyVisibleSkin=float(occ[choose&~selfhidden].mean()) if np.any(choose&~selfhidden) else None,clothOccludedFraction=float(occ[choose].mean()) if choose.any() else None,nearestClothDistanceQuantiles=np.quantile(ds,[0,.5,.9,1]).tolist() if choose.any() else None))
 views.append(dict(yaw=yaw,camera=list(camera),bands=bands));np.savez(R/'trial03'/('coverage-self-filter-yaw'+str(yaw)+'.npz'),skinSourceIndices=skin,positions=points,occludedByActualCloth=occ,nearestClothDistance=dist,nearestNormalSignedDot=normalDot)
rep=dict(status='Actual unchanged GLB skin/garment BVH coverage diagnosis only; no repaired garment',inputGLB=str(g),inputSHA=before,headMesh=head.name,bodyMesh=body.name,wholeNativeSkinUntouched=True,views=views,nearClothVerticesUnder2mm=int(np.sum(dist<.002)),nearestSignedNormalDotNegativeCount=int(np.sum(normalDot<0)),nearestSignedDotIsNotSolidInsideTest=True,method='Exact Blender BVH nearest triangle and camera-to-skin ray hits; garment holes and nonplanar folds retained',limits='Self-head ray visibility excluded before reporting potentially visible skin coverage. Vertex camera-ray occlusion is measured static coverage, not deformation/triangle collision or full motion clearance',sourceSHAAfter=sha(g),elapsedSeconds=time.monotonic()-t,peakRSSBytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,recipeSHA=sha(__file__))
assert before==rep['sourceSHAAfter'];(O/'actual-3d-coverage-self-filter.json').write_text(json.dumps(rep,indent=2)+'\n');print(json.dumps(rep),flush=True)
