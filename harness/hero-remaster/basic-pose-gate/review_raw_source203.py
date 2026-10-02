"""Parent read-only native construction proof; never execute child writers."""
import os
os.environ['OPENBLAS_NUM_THREADS']='2'
os.environ['OMP_NUM_THREADS']='2'
from pathlib import Path
import json, hashlib, importlib.util
from collections import Counter
import numpy as np
from scipy.spatial import cKDTree
R=Path(__file__).resolve().parents[3]
E=R/'docs/evidence/hero-remaster/one-rider-v2/raw-body-reduction-audit202'
B=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1')
D=B/'one-rider-v2/raw-body-reduction-audit202'
f=json.loads((E/'freeze.json').read_text()); counts={}
for group in ['inputPins','ownedFiles','privateOutputs']:
 for path,pin in f[group].items():
  data=Path(path).read_bytes()
  assert len(data)==pin['bytes'] and hashlib.sha256(data).hexdigest()==pin['sha256'],path
 counts[group]=len(f[group])
spec=importlib.util.spec_from_file_location('safe_reader',R/'assets/blender/hero-remaster/rider/one-rider-v2/candidate-handoff170/map_candidate.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def read(path):
 g=m.GLB(path);p=g.j['meshes'][0]['primitives'][0]
 return g,g.array(p['attributes']['POSITION']),g.array(p['indices']).reshape(-1,3)
z=np.load(D/'lineage.npz');raw=np.load(B/'hunyuan21/04/raw-shape.npz')
ng,NP,NF=read(B/'hunyuan21/04/raw-shape.glb')
sg,SP,SF=read(B/'hunyuan21/04/shape.glb')
pg,PP,PF=read(B/'hunyuan21/04/model.glb')
dg,DP,DF=read(B/'hunyuan21/04/working-display2.glb')
cg,CP,CF=read(B/'one-rider-v2/source-preserving-garment185/operator/rider.glb')
bg,BP,BF=read(B/'one-rider-v2/rig-adapter01/body-bind11/guarded-correction01/rider.glb')
assert np.array_equal(NP,raw['vertices'].astype(np.float32)) and np.array_equal(NF,raw['faces'])
assert pg.bin==dg.bin and np.array_equal(CP,BP) and np.array_equal(CF,BF)
a=json.loads((R/'docs/evidence/hero-remaster/one-rider-v2/glove-cleanup/neutral-assembly/report.json').read_text())['sourceDisplayTransform']
k=a['scale']*1.015;t=np.array(a['translation']);centre=(SP.astype(float).min(0)+SP.astype(float).max(0))/2
Mp=np.array([[0,0,-k,.65-1.015*t[1]],[0,-k,0,1.015*t[2]],[-k,0,0,-1.015*t[0]],[0,0,0,1.]])
flip=np.diag([1.,-1.,-1.,1.]);flip[:3,3]=[0,2*centre[1],2*centre[2]]
M=Mp@flip
assert np.array_equal(M,z['transform'])
def apply(P):return P.astype(float)@M[:3,:3].T+M[:3,3]
# Match the documented arithmetic too, avoiding floating operation-order drift.
def exact(P):return (P.astype(float)[:,None,:]*M[None,:3,:3]).sum(2)+M[:3,3]
assert np.array_equal(exact(NP),z['nativePositions']) and np.array_equal(exact(SP),z['reducedPositions'])
recovered=PP[:,[0,2,1]]*[1,-1,1]*flip.diagonal()[:3]+flip[:3,3]
distance,ids=cKDTree(SP).query(recovered,workers=2)
assert distance.max()<1e-6
assert Counter(map(tuple,np.sort(ids[PF],axis=1)))==Counter(map(tuple,np.sort(SF,axis=1)))
assert np.array_equal(exact(recovered),z['paintPositions'])
assert np.array_equal(CP,z['currentPositions']) and np.array_equal(CF,z['currentFaces'])
report=json.loads((E/'report.json').read_text());checked={}
for name in ['native','reduced','paint','current']:
 U,inv=np.unique(z[name+'Positions'],axis=0,return_inverse=True);T=inv[z[name+'Faces']]
 G=np.load(D/f'{name}-graph.npz');assert np.array_equal(U,G['positions']) and np.array_equal(T,G['faces'])
 # Use exact edge-keyed closed contour connectivity for full contour membership.
 sections=json.loads((D/f'{name}-sections.json').read_text());waist=next(x for x in sections if x['heightY_M']==.94)
 seeds={c['label']:{v for s in c['segments'] for edge in s['keys'] for v in edge if U[v,1]<.94} for c in waist['contours']}
 all_edges=np.sort(np.concatenate([T[:,[0,1]],T[:,[1,2]],T[:,[2,0]]]),axis=1)
 incid=Counter(map(tuple,all_edges)); edges=np.array(list(incid)); eh=U[edges,1].max(1)
 # A second algorithm: ascending-edge union-find, independent of minimax Dijkstra.
 parent=np.arange(len(U));bits=np.zeros(len(U),np.uint8)
 for flag,label in [(1,'central'),(2,'positiveZ'),(4,'negativeZ')]:
  for i in seeds[label]:bits[i]|=flag
 def root(i):
  while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
  return i
 first={}
 for i in np.argsort(eh,kind='stable'):
  a,b=map(root,edges[i]);parent[b]=a;bits[a]|=bits[b]
  for bit,label in [(2,'positiveZ'),(4,'negativeZ')]:
   if label not in first and bits[a]&1 and bits[a]&bit:first[label]=float(eh[i])
  if len(first)==2:break
 for c in report['meshes'][name]['connections']:
  assert first[c['label']]==c['firstConnectionY_M']
  path=c['pathPhysicalIDs'];assert max(U[path,1])==first[c['label']]
  assert path[0] in seeds['central'] and path[-1] in seeds[c['label']]
  for a,b in zip(path,path[1:]):assert tuple(sorted((a,b))) in incid
  if name=='native':assert all(incid[tuple(sorted((a,b)))]==2 for a,b in zip(path,path[1:]))
 # Check every frozen section segment is a literal face-edge interpolation.
 for section in sections:
  for contour in section['contours']:
   for segment in contour['segments']:
    face=set(map(int,T[segment['face']]))
    for edge,point in zip(segment['keys'],segment['positions']):
     a,b=edge;assert {a,b}<=face
     expected=U[a]+(section['heightY_M']-U[a,1])/(U[b,1]-U[a,1])*(U[b]-U[a])
     assert np.allclose(expected,point,rtol=0,atol=2e-7 if U.dtype==np.float32 else 2e-14)
 checked[name]={'firstConnectionsM':first,'triangles':len(T),'physicalVertices':len(U),'sectionSegmentsVerified':sum(len(c['segments']) for s in sections for c in s['contours'])}
out={'status':'PARENT_VERIFIED_STATIC_CONSTRUCTION_ONLY','pins':counts,'nativeNPZ_GLBFacesPositionsExact':True,'source185Body11Exact':True,'documentedTransformExact':True,'paintReduced55000FaceIncidencesExact':True,'paintReducedMaxDistanceM':float(distance.max()),'independentAscendingEdgeUnionFind':checked,'limitations':['No motion, appearance, ownership, contacts or topology suitability pass.','Section seed membership uses frozen literal waist contours; every section face/interpolation checked independently.','Current Float32 section arithmetic checked within 0.2microns; Float64 within 2e-14m. Initial 1e-14 assertion rejected Float32 operation-order rounding; no source changed.','Historical modified painter code hashes and intermediate cleanup ancestry absent; implementation causality remains inference.']}
(E/'parent-review203.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
