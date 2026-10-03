"""One guarded derived normal preview; native geometry remains immutable."""
import argparse, hashlib, json, os, subprocess
from pathlib import Path
import numpy as np
import trimesh
from audit_native import audit
from orient_derived_preview import orient_derived_preview

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
p=argparse.ArgumentParser()
for n in ['native','native-sha256','orbit','orbit-sha256','out']: p.add_argument('--'+n,required=True)
a=p.parse_args()
assert os.environ.get('ROCKHOP_GENERATION_CONTROLLER_PID')==str(os.getppid())
assert sha(a.native)==a.native_sha256 and sha(a.orbit)==a.orbit_sha256
out=Path(a.out); assert not out.exists(); out.mkdir(parents=True)
previous=json.loads(Path(a.orbit).read_text())
with np.load(a.native,allow_pickle=False) as d: v=d['vertices'].copy(); f=d['faces'].copy()
original=trimesh.Trimesh(vertices=v.copy(),faces=f.copy(),process=False)
ff, adapter=orient_derived_preview(v,f)
cross=np.cross(v[ff[:,1]].astype(float)-v[ff[:,0]],v[ff[:,2]].astype(float)-v[ff[:,0]])
normals=np.zeros(v.shape,dtype=np.float64)
for column in range(3): np.add.at(normals,ff[:,column],cross)
length=np.linalg.norm(normals,axis=1); normals/=np.maximum(length[:,None],1e-20)
np.savez_compressed(out/'derived-normals.npz',faces=ff,normals=normals.astype(np.float32))
matrix=np.array(previous['previewRawToBlenderMatrixRows']); cuts={}; cutstats=[]
for fraction in [.2,.4,.6,.8]:
    z=float(v[:,2].min()+fraction*np.ptp(v[:,2]))
    lines=trimesh.intersections.mesh_plane(original,[0,0,1],[0,0,z])
    world=lines@matrix[:3,:3].T+matrix[:3,3]; name='cut'+str(int(fraction*100))
    cuts[name]=world; cutstats.append({'name':name,'worldZ':float(matrix[2,2]*z+matrix[2,3]),'segments':len(lines)})
np.savez_compressed(out/'cross-sections.npz',**cuts)
r={'accepted':False,'nativeSHA256':sha(a.native),'previousOrbitSHA256':sha(a.orbit),'recipeSHA256':sha(__file__),
   'verticesUnchanged':True,'samePerRowTriangleVertexSets':True,'flippedFaceRows':int(np.count_nonzero(np.any(ff!=f,axis=1))),
   'normalMethod':'owned derived orientation adapter plus explicit area-weighted smooth vertex normals','adapter':adapter,
   'zeroUsedVertexNormals':int(np.count_nonzero(length[np.unique(ff)]<1e-20)),
   'derivedAudit':audit(v,ff),'derivedArchiveSHA256':sha(out/'derived-normals.npz'),
   'sectionsArchiveSHA256':sha(out/'cross-sections.npz'),'sectionPlanes':cutstats,
   'previewRawToBlenderMatrixRows':previous['previewRawToBlenderMatrixRows'],'camera':previous['camera'],
   'limits':['No vertex movement, smoothing, remesh, added/deleted triangles or native mutation',
             'Residual orientation/topology conflicts are measured, not assumed solved','No neural inference, art/fit/rig or texture-generator judgment']}
(out/'preparation.json').write_text(json.dumps(r,indent=2)+'\n')
base=Path(__file__).resolve().parent
subprocess.run(['/Applications/Blender.app/Contents/MacOS/Blender','--background','--factory-startup','--threads','4','--python-exit-code','1','--python',str(base/'normal_orbit.py'),'--','--native',a.native,'--native-sha256',a.native_sha256,'--preparation',str(out/'preparation.json'),'--preparation-sha256',sha(out/'preparation.json'),'--out',str(out/'orbit')],check=True)
assert sha(a.native)==a.native_sha256
print(json.dumps({'preparation':r,'nativeUnchanged':True}))
