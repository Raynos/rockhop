"""Locate both actual native-probe rim circuits in immutable selected source."""
import ast
import hashlib
import json
import runpy
from collections import defaultdict
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[4]
E=ROOT/'docs/evidence/rider-rebuild/selected-cuff-topology10'
D=ROOT/'assets/blender/hero-remaster/rider/finish-2026-10-05/wardrobe/data/prep02/gloves/cleaned-donor.npz'
report=json.loads((E/'native-identity-probe02.json').read_text())
assert all(h['returnTopologyCompleted'] for h in report['hands'].values())
assert hashlib.sha256(D.read_bytes()).hexdigest()==report['sourceGlove']['sha256']
donor=np.load(D);p=donor['vertices'].astype(float);f=donor['faces']
n=np.zeros_like(p);fn=np.cross(p[f[:,1]]-p[f[:,0]],p[f[:,2]]-p[f[:,0]])
for k in range(3):np.add.at(n,f[:,k],fn)
n/=np.maximum(np.linalg.norm(n,axis=1)[:,None],1e-30)
volume=ROOT/'assets/blender/rider-rebuild/glove-over-sleeve08/volume.py'
a=ast.parse(volume.read_text());a.body=[node for node in a.body if isinstance(node,ast.FunctionDef) and node.name in ('polygon_center','source_cuff')]
env={'np':np};exec(compile(a,str(volume),'exec'),env)
g=np.load(ROOT/'harness/out/rider-rebuild/glove-cuff-construction07/inspection01/guide-L.npz')
placement=json.loads((ROOT/'assets/blender/rider-rebuild/glove-anatomical04/controls-orientation02.json').read_text())
_,x,z=env['source_cuff'](p,g,placement['sourceRest']['wrist'],1.,None,None)
r=np.column_stack((x,np.zeros(len(p)),z));r/=np.maximum(np.linalg.norm(r,axis=1)[:,None],1e-30)
signed=-np.sum(n*r,axis=1)
if signed[106803]<0:signed*=-1
owned=report['hands']['L']['returnOwnership'];ids=owned['rimClippedSourceFaceIds']
edges={};links=[];source_faces=defaultdict(list)
for face_id in ids:
 face=f[face_id];cross=[]
 for va,vb in zip(face,np.roll(face,-1)):
  if signed[va]*signed[vb]<0:
   key=tuple(sorted((int(va),int(vb))))
   if key not in edges:
    t=signed[va]/(signed[va]-signed[vb]);edges[key]=len(edges)
   cross.append(key);source_faces[key].append(face_id)
 assert len(cross)==2,(face_id,cross)
 links.append(tuple(cross))
graph=defaultdict(set)
for a,b in links:graph[a].add(b);graph[b].add(a)
assert all(len(v)==2 for v in graph.values())
unseen=set(graph);rings=[]
while unseen:
 first=min(unseen);found={first};todo=[first]
 while todo:
  for other in graph[todo.pop()]-found:found.add(other);todo.append(other)
 unseen-=found
 xyz=[]
 for a,b in sorted(found):
  t=signed[a]/(signed[a]-signed[b]);xyz.append((1-t)*p[a]+t*p[b])
 xyz=np.asarray(xyz);source_ids=sorted({i for key in found for i in source_faces[key]})
 rings.append({'vertices':len(found),'boundsSource': [xyz.min(axis=0).tolist(),xyz.max(axis=0).tolist()],
               'centroidSource':xyz.mean(axis=0).tolist(),'sourceTriangleIds':source_ids,
               'sourceEdgeVertexIds':[list(v) for v in sorted(found)],
               'meaning':'Authored zero contour of the cavity-rooted inward component, not an original anatomical opening.'})
assert sorted(r['vertices'] for r in rings)==[71,1688]
out={'acceptedArt':False,'nativeProbeSHA256':hashlib.sha256((E/'native-identity-probe02.json').read_bytes()).hexdigest(),
     'sourceSHA256':report['sourceGlove']['sha256'],'allClippedNativeSourceFacesReproduced':len(ids),
     'rings':sorted(rings,key=lambda r:-r['vertices']),
     'limits':'Coordinates locate the exact native-owned contour source edges using original adjacent normals. Source-only exact clip replay; no native save, fit or native geometry mutation. Both contour circuits must be paired to corresponding lining edges; no aperture anatomy or sewing pass is inferred.'}
helper=runpy.run_path(str(Path(__file__).with_name('probe_plane_identity02.py')))
original=donor['vertices'];chosen=np.flatnonzero(np.any(original[f,1]<=-.64,axis=1))
s=helper['surgery'](original,donor,chosen)
xyz=np.asarray(s.source,dtype=float);tri=np.asarray(s.faces)
keep=np.flatnonzero(np.all(xyz[tri,1]<=-.65+1e-7,axis=1))
for name in ('faces','face_sources','face_roles','corner_sources','uv','material','smooth'):
 values=getattr(s,name);setattr(s,name,[values[i] for i in keep])
def euler(faces):
 faces=np.asarray(faces);vertices=len(np.unique(faces))
 edges=np.sort(np.concatenate([faces[:,[0,1]],faces[:,[1,2]],faces[:,[2,0]]]),axis=1)
 unique,counts=np.unique(edges,axis=0,return_counts=True)
 return {'V':vertices,'E':len(unique),'F':len(faces),'chi':vertices-len(unique)+len(faces),'boundaryEdges':int((counts==1).sum()),'nonmanifoldEdges':int((counts>2).sum())}
pre=euler(s.faces)
cut_values=list(signed)
for parents,coeff in zip(s.parents[len(p):],s.coefficients[len(p):]):
 cut_values.append(sum(signed[a]*b for a,b in zip(parents,coeff) if a>=0))
removed=set(owned['removedSourceFaceIds'])|set(owned['rimClippedSourceFaceIds'])
s.cut(np.asarray(cut_values),np.array([i in removed for i in s.face_sources]))
post=euler(s.faces)
out['cuffBandTopologyBeforeReturnRemoval']=pre
out['retainedExteriorTopologyAfterReturnRemoval']=post
out['genusInterpretation']='Actual connected source cuff has two floor boundaries; chi=-2 means one inherited handle. Retained connected exterior has the proximal floor and both authored rim circuits; chi=-1 means genus zero with three boundaries. The 71-edge contour participates in opening that inherited cuff handle, not an additional wrist aperture.'
assert pre['chi']==-2 and post['chi']==-1,(pre,post)
(E/'rim-ownership03.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({**out,'rings':[{k:v for k,v in r.items() if k not in ('sourceTriangleIds','sourceEdgeVertexIds')} for r in out['rings']]},indent=2))
