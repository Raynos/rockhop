"""Read-only, CPU-two-thread native/head seam reconnaissance; no candidate."""
import os
os.environ.setdefault('OPENBLAS_NUM_THREADS','2');os.environ.setdefault('OMP_NUM_THREADS','2')
import importlib.util,json,hashlib
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path('/Users/raynos/projects/games/rockhop');B=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2');E=ROOT/'docs/evidence/hero-remaster/one-rider-v2/head-join211';R=B/'head-join211'
spec=importlib.util.spec_from_file_location('reader',ROOT/'assets/blender/hero-remaster/rider/one-rider-v2/candidate-handoff170/map_candidate.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
paths=[B/'finite-native208/native-display.glb',B/'source-preserving-garment185/operator/rider.glb'];Gs=[mod.GLB(p) for p in paths];report={'inputs':{str(p):sha(p) for p in paths},'status':'READ_ONLY_JOIN_PROBE_NO_CANDIDATE','meshes':[]}
arrays={}
for si,g in enumerate(Gs):
 for mi,mesh in enumerate(g.j['meshes']):
  for pi,p in enumerate(mesh['primitives']):
   v=g.array(p['attributes']['POSITION']);f=g.array(p['indices']).reshape(-1,3);u,inv=np.unique(v,axis=0,return_inverse=True);q=inv[f];e=np.sort(np.concatenate([q[:,[0,1]],q[:,[1,2]],q[:,[2,0]]]),axis=1);ue,c=np.unique(e,axis=0,return_counts=True);rim=ue[c==1];label=f's{si}m{mi}p{pi}';arrays[label+'_v']=v;arrays[label+'_f']=f
   row={'label':label,'rows':len(v),'faces':len(f),'bounds':[v.min(0).tolist(),v.max(0).tolist()],'material':p.get('material'),'attributes':p['attributes'],'openEdges':len(rim),'nonmanifoldEdges':int(sum(c>2)),'boundaryBounds':None if not len(rim) else [u[rim].reshape(-1,3).min(0).tolist(),u[rim].reshape(-1,3).max(0).tolist()]};report['meshes'].append(row)
report['sourceNodes']=[g.j['nodes'] for g in Gs];report['headMaterials']=Gs[1].j['materials'];report['headSkin']=Gs[1].j['skins'];np.savez(R/'arrays.npz',**arrays)
# Native conventional front/profile, donor canonical front/profile. Points only diagnostic.
img=Image.new('RGB',(1600,900),'#eee');draw=ImageDraw.Draw(img)
for k,(label,axes) in enumerate([('s0m0p0',(0,1)),('s0m0p0',(2,1)),('s1m1p0',(2,1)),('s1m1p0',(0,1))]):
 v=arrays[label+'_v'];m=v[:,1]>(.25 if k<2 else 1.40);v=v[m];a=v[:,axes];lo=a.min(0);hi=a.max(0);scale=min(380/(hi[0]-lo[0]),800/(hi[1]-lo[1]));pixels=(a-lo)*scale;pixels[:,1]=800-pixels[:,1];pixels[:,0]+=k*400+10
 for x,y in pixels[::max(1,len(v)//50000)]:draw.point((int(x),int(y)+50),fill='#333')
 draw.text((k*400+10,12),label+str(axes),fill='black');draw.text((k*400+10,28),str(np.round(lo,3))+'..'+str(np.round(hi,3)),fill='black')
img.save(E/'geometry-projection.png');(E/'probe.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report['meshes'],indent=2))
