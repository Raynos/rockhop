import os
os.environ['OPENBLAS_NUM_THREADS']='2';os.environ['OMP_NUM_THREADS']='2'
import sys,importlib.util,json,hashlib
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
R=Path('/Users/raynos/projects/games/rockhop');B=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1');O=R/'docs/evidence/hero-remaster/one-rider-v2/raw-body-reduction-audit202'
s=importlib.util.spec_from_file_location('reader',R/'assets/blender/hero-remaster/rider/one-rider-v2/candidate-handoff170/map_candidate.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
paths=[B/'hunyuan21/04'/p for p in ['raw-shape.npz','raw-shape.glb','shape.glb','model.glb','working-display2.glb','generation.json']]+[B/'one-rider-v2/source-preserving-garment185/operator/rider.glb',B/'one-rider-v2/rig-adapter01/body-bind11/guarded-correction01/rider.glb']
report={'files':{str(p):{'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size} for p in paths},'meshes':{}}
raw=np.load(paths[0]);print('NPZ',[(k,raw[k].shape,raw[k].dtype) for k in raw.files])
coords={};faces={}
for p in paths[1:5]+paths[6:]:
 g=m.GLB(p);rows=[];world=m.worlds(g.j)
 for ni,n in enumerate(g.j['nodes']):
  if 'mesh' not in n:continue
  for pi,pr in enumerate(g.j['meshes'][n['mesh']]['primitives']):
   P=g.array(pr['attributes']['POSITION']);F=g.array(pr['indices']).reshape(-1,3);M=world[ni];W=(P.astype(float)[:,None,:]*M[None,:3,:3]).sum(2)+M[:3,3];key=f'{p.name}:{p.parent.name}:p{pi}'
   if p.parent.name in ['operator','guarded-correction01']:key=f'{p.parent.name}:m{n["mesh"]}p{pi}'
   coords[key]=W;faces[key]=F
   rows.append({'key':key,'positions':P.shape,'triangles':len(F),'world':M.tolist(),'localBounds':[P.min(0).tolist(),P.max(0).tolist()],'worldBounds':[W.min(0).tolist(),W.max(0).tolist()]})
 report['meshes'][str(p)]=rows
report['nativeGLBExactNPZ']={'positions':np.array_equal(m.GLB(paths[1]).array(0),raw['vertices'].astype(np.float32))}
print(json.dumps(report,indent=2));(O/'probe.json').write_text(json.dumps(report,indent=2)+'\n')
np.savez(B/'one-rider-v2/raw-body-reduction-audit202/probe.npz',**{'P_'+k.replace(':','_'):v for k,v in coords.items()},**{'F_'+k.replace(':','_'):v for k,v in faces.items()})
