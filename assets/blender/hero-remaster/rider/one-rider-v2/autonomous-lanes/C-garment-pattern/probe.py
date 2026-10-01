"""Read-only local cloth-pattern preflight. CPU two threads, no addons."""
import bpy,bmesh,numpy as np,json,sys,os,hashlib,platform
from pathlib import Path
R=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2')
O=Path('/Users/raynos/projects/games/rockhop/docs/evidence/hero-remaster/one-rider-v2/autonomous-lanes/C-garment-pattern')
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
body=R/'glove-cleanup/glove-material/isolated-correction01/bodyPBR.blend'
head=R/'head-cleanup/mpfb-v8-palette/african/head.blend'
env={'executable':bpy.app.binary_path,'binarySHA256':sha(bpy.app.binary_path),'Blender':bpy.app.version_string,'Python':sys.version,'PythonExecutable':sys.executable,'numpy':np.__version__,'platform':platform.platform(),'isolatedEnvironment':{k:os.environ.get(k) for k in ['BLENDER_USER_CONFIG','BLENDER_USER_SCRIPTS','BLENDER_USER_EXTENSIONS','TMPDIR']},'threadCap':2,'sharedInstalledBinary':True,'loadedAddons':list(bpy.context.preferences.addons.keys()),'inputs':{str(p):sha(p) for p in [body,head]}}
(O/'environment.json').write_text(json.dumps(env,indent=2)+'\n')
bpy.ops.wm.open_mainfile(filepath=str(body));obj=next(o for o in bpy.context.scene.objects if o.type=='MESH')
rows=[]
for z in [1.40,1.425,1.45,1.475]:
 b=bmesh.new();b.from_mesh(obj.data)
 remove=[f for f in b.faces if min(v.co.z for v in f.verts)>z]
 bmesh.ops.delete(b,geom=remove,context='FACES');edges=[e for e in b.edges if e.is_boundary];vs=set(v for e in edges for v in e.verts)
 rows.append({'z':z,'removed':len(remove),'boundaryEdges':len(edges),'branchedVertices':sum(sum(e.is_boundary for e in v.link_edges)!=2 for v in vs),'boundaryBounds':[[min(v.co[i] for v in vs) for i in range(3)],[max(v.co[i] for v in vs) for i in range(3)]]})
 b.free()
(O/'preflight.json').write_text(json.dumps(rows,indent=2)+'\n');print('PREFLIGHT',json.dumps(rows),flush=True)
