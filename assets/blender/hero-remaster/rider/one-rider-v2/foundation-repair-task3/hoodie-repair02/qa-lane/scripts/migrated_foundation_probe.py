from pathlib import Path
import json,hashlib,sys
import numpy as np
MAIN=Path('/Users/raynos/projects/games/rockhop/assets/blender/hero-remaster/rider/one-rider-v2/foundation-repair-task3')
Q=MAIN/'hoodie-repair02/qa-lane'; OUT=Q/'screenshot01';OUT.mkdir(exist_ok=True)
B=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/rig-adapter01/body-bind34/candidate-cpu')
R=Path('/Users/raynos/projects/games/rockhop/docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/body-bind34')
j=json.loads((R/'candidate-cpu/pose-manifest.json').read_text());r=next(r for r in j['rows']if r['i']==304)
sys.path.insert(0,str(MAIN/'scripts'));from glb import GLB
g=GLB(j['source']);prim=[p for m in g.j['meshes']for p in m['primitives']];data={};raw=[]
for mi,sourcepi in [(0,0),(1,2)]:
 for key,receipt in [('positions',r['dump'][mi]['positions']),('normals',r['dump'][mi]['gpuRuleSkinnedNormals']),('joint_transforms',r['dump'][mi]['jointTransforms']),('rest',j['primitives'][mi]['attributes']['position']),('triangles',j['primitives'][mi]['index'])]:
  f=B/receipt['file'];h=hashlib.sha256(f.read_bytes()).hexdigest();assert h==receipt['sha256'];a=np.fromfile(f,dtype='<f8');data[f'{key}{sourcepi}']=a.reshape(-1,4,4).transpose(0,2,1)if key=='joint_transforms'else a.reshape(-1,3);raw.append({'path':str(f),'sha256':h,'key':f'{key}{sourcepi}'})
np.savez_compressed(OUT/'body34-reference-sample304.npz',**data)
report=json.loads((R/'played/candidate/side/textured/report.json').read_text());sample=report['samples'][304]
meta={'status':'REFERENCE CAMERA/TIME MATCH, EXACT SCREENSHOT MESH UNCONFIRMED','source_glb':j['source'],'source_sha256':j['sourceSHA256'],'sample':304,'tick':sample['tick'],'camera':sample['camera'],'orbit':sample['orbit'],'anchor':sample['anchor'],'state_hash':sample['hash'],'materials':[{'name':m.get('name'),'doubleSided':m.get('doubleSided',False),'alphaMode':m.get('alphaMode','OPAQUE')}for m in g.j['materials']],'frame_space':'bike-frame coordinates. joint_transforms are complete runtime prefix * boneWorld * inverseBind * bindMatrix, column-major dump decoded to row-major NumPy. Not skeleton rotation quaternions to copy across rigs.','raw_receipts':raw,'limits':['Source screenshot is JPEG and differs visibly at underarm from body34 recorded original; matching camera/time does not identify its mesh.','No actual GPU/PBR certification. Normals follow Three shader arithmetic as CPU reconstruction.','Do not transfer these D matrices directly to a different rest/bind skeleton.']}
(OUT/'body34-reference-sample304.json').write_text(json.dumps(meta,indent=2))
V=MAIN/'hoodie-repair02/shape-lane/volume-lane';OLD=Path('/Users/raynos/Documents/Codex/2026-10-01/task-3/hoodie-repair02');rows=[]
for name in ['rounded-elbow-1.npz','rounded-single-elbow-90.npz']:
 rows.append({'variant':'v7','probe':name.removesuffix('.npz'),'fraction':1,'path':str(V/name)})
for name in ['rounded-forward-0.5.npz','rounded-forward-1.npz','skin-single-elbow-90.npz','skin-elbow-1.npz']:
 rows.append({'variant':'v7','probe':name.removesuffix('.npz'),'fraction':1,'path':str(OLD/'shape-lane/volume-lane'/name)})
rows.append({'variant':'v7','probe':'T-control','fraction':1,'path':str(OLD/'qa-lane/poses/v5-horizontal-1.npz')})
for r in rows:assert Path(r['path']).exists(),r
(Q/'rounded-bounded-manifest.json').write_text(json.dumps({'topology_path':str(MAIN/'hoodie-repair02/v7-bind.npz'),'rows':rows,'limits':'Read-only frozen candidate arrays. Independent bounded probe diagnostics, no full foundation acceptance.'},indent=2))
print(json.dumps({'snapshot':str(OUT),'probes':len(rows)}))
