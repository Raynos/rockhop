"""Audit real environment and explicit physical garment seam landmarks."""
import bpy,bmesh,numpy as np,json,hashlib,sys,os,time
from pathlib import Path
from mathutils import Vector
from mathutils.kdtree import KDTree
R=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2');RUN=R/'autonomous-lanes/A-manual-panel';OUT=Path('/Users/raynos/projects/games/rockhop/docs/evidence/hero-remaster/one-rider-v2/autonomous-lanes/A-manual-panel')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
bodypath=R/'glove-cleanup/glove-material/isolated-correction01/bodyPBR.blend';headpath=R/'head-cleanup/mpfb-v8-palette/african/head.blend';maskpath=R/'collar-trial1/collar-selection.npz'
if (OUT/'setup.json').exists():raise RuntimeError('Frozen setup exists')
report={'status':'read-only laneA setup and seam landmark inspection; no character accepted','startedUTC':'2026-10-01T01:32:11Z','deadlineUTC':'2026-10-01T02:17:00Z','BlenderBinary':bpy.app.binary_path,'BlenderVersion':bpy.app.version_string,'BlenderSHA256':sha(Path(bpy.app.binary_path)),'embeddedPythonExecutable':sys.executable,'embeddedPythonVersion':sys.version,'embeddedPythonPrefix':sys.prefix,'sharedInterpreter':True,'isolatedUserRoots':{k:os.environ.get(k) for k in ['BLENDER_USER_CONFIG','BLENDER_USER_SCRIPTS','BLENDER_USER_EXTENSIONS','TMPDIR']},'sysPath':sys.path,'dependencies':{'bpy':'bundled native Blender','bmesh':'bundled native Blender','mathutils':'bundled native Blender','numpyVersion':np.__version__,'numpyPath':np.__file__,'numpyInitSHA256':sha(Path(np.__file__)),'externalGeometryPackages':[]},'sources':{str(p):sha(p) for p in [bodypath,headpath,maskpath]}}
pythonbin=Path('/Applications/Blender.app/Contents/Resources/5.2/python/bin/python3.13');report['embeddedPythonBinarySHA256']=sha(pythonbin)
bpy.ops.wm.open_mainfile(filepath=str(bodypath));body=next(o for o in bpy.context.scene.objects if o.type=='MESH');bm=bmesh.new();bm.from_mesh(body.data);bm.verts.index_update();bm.faces.index_update()
data=np.load(maskpath);v=data['verticesBlender'];f=data['faces'];keep=data['retainedFaceMask'];tree=KDTree(len(f))
for i,ids in enumerate(f):tree.insert(v[ids].mean(0),i)
tree.balance();delete=[];matched=[]
for face in bm.faces:
 if len(face.verts)!=3:continue
 points=np.array([x.co for x in face.verts]);co,i,d=tree.find(points.mean(0))
 if d<2e-6 and not keep[i] and max(min(np.linalg.norm(q-p) for p in v[f[i]]) for q in points)<2e-6:delete.append(face);matched.append(i)
assert len(set(matched))==int((~keep).sum());bmesh.ops.delete(bm,geom=delete,context='FACES');loose=[x for x in bm.verts if not x.link_faces]
if loose:bmesh.ops.delete(bm,geom=loose,context='VERTS')
bm.verts.index_update();bm.verts.ensure_lookup_table();bm.faces.index_update();points=np.array([x.co for x in bm.verts]);kt=KDTree(len(points))
for i,p in enumerate(points):kt.insert(p,i)
kt.balance()
# Deliberately specified actual physical seam landmarks, ordered around collar.
# These pick source IDs once; no radius/ring or colour cut defines this panel.
landmarks=[('front throat centre',(0,-.095,1.470)),('left front quarter',(-.068,-.077,1.478)),('left below ear seam',(-.120,-.015,1.515)),('left rear quarter',(-.090,.100,1.535)),('rear nape centre',(0,.135,1.542)),('right rear quarter',(.090,.100,1.535)),('right below ear seam',(.120,-.015,1.515)),('right front quarter',(.068,-.077,1.478))]
report['landmarks']=[]
for name,target in landmarks:
 co,idx,distance=kt.find(target);vert=bm.verts[idx];report['landmarks'].append({'label':name,'physicalTargetWorldM':target,'bodySourceVertexIndexAfterFixedMask':idx,'actualWorldM':list(co),'distanceFromTargetM':distance,'incidentMaterialIndices':sorted(set(face.material_index for face in vert.link_faces))})
np.savez(RUN/'seam-probe.npz',vertices=points,edgeVertexIndices=np.array([[e.verts[0].index,e.verts[1].index] for e in bm.edges],np.int32),facesOffsets=np.array(np.cumsum([0]+[len(face.verts) for face in bm.faces]),np.int32),faceVertices=np.array([x.index for face in bm.faces for x in face.verts],np.int32))
report['bodyMaterials']=[m.name for m in body.data.materials];report['sourceDeletedHeadTriangles']=len(matched);report['actualOpenRimEdges']=sum(e.is_boundary for e in bm.edges);report['protectedAnatomy']='No source changes: landmarks inspected only, body/head files immutable';bm.free();report['sourcesAfter']={p:sha(Path(p)) for p in report['sources']};assert report['sources']==report['sourcesAfter'];(OUT/'setup.json').write_text(json.dumps(report,indent=2)+'\n');print('LANE_A_SETUP',json.dumps({'landmarks':report['landmarks'],'dependencies':report['dependencies']}),flush=True)
