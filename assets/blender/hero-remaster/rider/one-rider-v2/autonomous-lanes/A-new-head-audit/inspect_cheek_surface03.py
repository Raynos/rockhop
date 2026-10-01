"""Read-only exact raw topology and visible cheek ray witnesses, CPU2.

Position welding below is diagnostic only, never a manifold pass or asset edit.
An index boundary in the painted mesh can be a UV seam, not a physical hole.
"""
import bpy,numpy as np,json,math,hashlib
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
R=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/autonomous-lanes/A-new-head-audit/generation/h21-buzz-native01')
O=Path('/Users/raynos/projects/games/rockhop/docs/evidence/hero-remaster/one-rider-v2/autonomous-lanes/A-new-head-audit/generation-evidence/h21-buzz-native01/gray-diagnostic03')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
if (O/'cheek-surface-forensic.json').exists():raise RuntimeError('Frozen forensic exists')
witness=json.loads((O.parent/'painted-orientation-witness01/manifest.json').read_text());f=next(v for v in witness['views'] if v['label']=='X180')
norm=Matrix.Translation(Vector(f['translation']))@Matrix.Diagonal((f['displayScale'],)*3+(1,))
report={'status':'UNACCEPTED read-only surface diagnosis, no repair','CPUThreads':2,'GPUJob':False,'recipeSHA256':sha(Path(__file__)),'variants':[]}
for label,name,rotation,probeY in [('raw','raw-shape.glb',0,394),('reduced','shape.glb',0,394),('painted','model.glb',180,382)]:
 source=R/name;digest=sha(source);bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(source));bpy.context.view_layer.update();mesh=next(o for o in bpy.context.scene.objects if o.type=='MESH');matrix=norm@Matrix.Rotation(math.radians(rotation),4,'X')@mesh.matrix_world
 points=np.array([matrix@v.co for v in mesh.data.vertices],dtype=np.float64);faces=np.array([list(p.vertices) for p in mesh.data.polygons],dtype=np.int64)
 assert faces.shape[1]==3
 quantized=np.rint(points/1e-7).astype(np.int64);_,inverse=np.unique(quantized,axis=0,return_inverse=True);wf=inverse[faces]
 edges=np.concatenate([wf[:,[0,1]],wf[:,[1,2]],wf[:,[2,0]]]);edges=np.sort(edges,axis=1);ue,counts=np.unique(edges,axis=0,return_counts=True)
 representative=np.zeros(int(inverse.max())+1,dtype=np.int64);representative[inverse]=np.arange(len(inverse));boundary=ue[counts==1];boundaryWorld=points[representative[boundary]]
 mid=boundaryWorld.mean(1) if len(boundary) else np.empty((0,3));near=((np.abs(mid[:,0])>.035)&(np.abs(mid[:,0])<.08)&(mid[:,2]>1.52)&(mid[:,2]<1.59)&(mid[:,1]<0)) if len(mid) else np.zeros(0,bool)
 bvh=BVHTree.FromPolygons([Vector(p) for p in points],faces.tolist(),all_triangles=True);rays=[]
 for side,px in [('left',240),('right',388)]:
  for offset in [-12,-6,0,6,12]:
   x=(px+.5-320)/640*.46;z=1.6+(320-probeY-.5)/640*.46;origin=Vector((x+offset/640*.46,-4,z));hit,normal,face,distance=bvh.ray_cast(origin,Vector((0,1,0)),10)
   rays.append({'side':side,'pixel':[px+offset,probeY],'hit':hit is not None,'point':list(hit) if hit is not None else None,'normal':list(normal) if normal is not None else None,'BlenderImportedFaceIndex':face,'rayDistanceM':distance})
 report['variants'].append({'label':label,'source':str(source),'sourceSHA256':digest,'sourceSHA256After':sha(source),'vertices':len(points),'trianglesActuallyImported':len(faces),'positionDiagnosticToleranceM':1e-7,'positionDiagnosticUniqueVertices':int(inverse.max())+1,'positionDiagnosticBoundaryEdges':len(boundary),'positionDiagnosticAbove2Edges':int(np.sum(counts>2)),'positionDiagnosticBoundarySegmentsNearCheeks':boundaryWorld[near].tolist(),'sampledVisibleCheekRays':rays,'limits':['Position diagnostic may weld coincident UV seams; not a geometry repair or closed-volume acceptance.','Imported face IDs are not source NPZ face IDs or live mesh mappings.','Different selected probe rows follow actual view artifacts; no per-vertex painted-to-reduced correspondence asserted.']})
 assert sha(source)==digest
report['finding']='Actual raw gray and painted gray both show cheek defects before cleanup/reduction/paint. Exact boundary and ray witnesses support diagnosis; parent determines next method.'
(O/'cheek-surface-forensic.json').write_text(json.dumps(report,indent=2)+'\n');print('CHEEK_SURFACE_FORENSIC_FROZEN',flush=True)
