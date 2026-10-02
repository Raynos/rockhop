"""Read-only literal source/export identity and physical boundary verification."""
from pathlib import Path
import importlib.util, json, hashlib
import numpy as np
from collections import Counter
R=Path('/Users/raynos/projects/games/rockhop')
spec=importlib.util.spec_from_file_location('hood185_operator',R/'assets/blender/hero-remaster/rider/one-rider-v2/source-preserving-garment185/operator.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
C=m.GLB(m.SOURCE,m.SOURCE_SHA);E=m.GLB(m.S/'rider.glb');sha=m.sha
def quotient_data(G):
 parts=[G.primitive(0,k)for k in range(3)];P=np.concatenate([a['POSITION']for a,f in parts]);U,q=np.unique(P,axis=0,return_inverse=True);phys=[];off=0
 for a,f in parts:phys.append(q[f+off]);off+=len(a['POSITION'])
 return parts,U,phys
def boundaries(f):return sorted(k for k,v in m.edges(f).items()if len(v)==1)
cp,cu,cf=quotient_data(C);ep,eu,ef=quotient_data(E);assert np.array_equal(cu,eu)
hoodc=boundaries(cf[2]);hoode=boundaries(ef[2]);assert hoodc==hoode and len(hoodc)==544
bodye=m.edges(cf[0]);pairedbodyhood=[e for e in hoodc if e in bodye];opening=[e for e in hoodc if e not in bodye];assert len(pairedbodyhood)==307 and len(opening)==237
sourcebodyglove=[e for e in boundaries(cf[1])if e in bodye];finalbodye=m.edges(ef[0]);finalbodyglove=[e for e in boundaries(ef[1])if e in finalbodye];assert sourcebodyglove==finalbodyglove and len(sourcebodyglove)==127
pf=np.concatenate(ef);parent=np.arange(len(eu))
def root(x):
 while parent[x]!=x:parent[x]=parent[parent[x]];x=int(parent[x])
 return x
for a,b,c in pf:
 for x,y in [(a,b),(b,c)]:parent[root(int(x))]=root(int(y))
components=sorted(Counter(root(int(i))for i in np.unique(pf)).values(),reverse=True);assert components==[22600]
arrays=[];images=[]
for mi,mesh in enumerate(C.d['meshes']):
 for pi,p in enumerate(mesh['primitives']):
  q=E.d['meshes'][mi]['primitives'][pi]
  for key,ai in p['attributes'].items():
   a,b=C.acc(ai),E.acc(q['attributes'][key]);assert np.array_equal(a,b);arrays.append({'mesh':mi,'primitive':pi,'field':key,'rows':len(a),'sha256':sha(a.tobytes()),'exact':True})
  for ti,t in enumerate(p.get('targets',[])):
   for key,ai in t.items():
    a,b=C.acc(ai),E.acc(q['targets'][ti][key]);assert np.array_equal(a,b);arrays.append({'mesh':mi,'primitive':pi,'target':ti,'field':key,'rows':len(a),'sha256':sha(a.tobytes()),'exact':True})
for i,img in enumerate(C.d.get('images',[])):
 if 'bufferView'in img:
  v=C.d['bufferViews'][img['bufferView']];off=v.get('byteOffset',0);b=C.bin[off:off+v['byteLength']];assert b==E.bin[off:off+v['byteLength']];images.append({'image':i,'bytes':len(b),'sha256':sha(b),'exact':True})
assert C.d.get('materials')==E.d.get('materials')and C.d.get('textures')==E.d.get('textures')and C.d.get('skins')==E.d.get('skins')and C.d.get('nodes')==E.d.get('nodes')
report={'status':'READ_ONLY_FROZEN_SOURCE_IDENTITY_VERIFIED','sourceSHA256':m.SOURCE_SHA,'outputSHA256':sha(E.raw),'sourceBINBytes':len(C.bin),'sourceBINPrefixSha256':sha(C.bin),'sourceBINPrefixExact':E.bin[:len(C.bin)]==C.bin,'facesByPrimitive':[len(f)for a,f in ep],'physicalReferencedComponents':components,'hoodBoundaryEdges':544,'paired307HoodBodyEdgesExact':True,'upper237OpeningEdgesExact':True,'source127BodyGloveCuffEdgesExact':True,'cuffSplit':{'positiveZ':sum(float(cu[list(e),2].mean())>0 for e in sourcebodyglove),'negativeZ':sum(float(cu[list(e),2].mean())<0 for e in sourcebodyglove)},'actualArrays':arrays,'embeddedImages':images,'materialsTexturesSkinNodesExact':True,'recipeSha256':sha(Path(__file__).read_bytes()),'limits':['This preserves vertex-normal arrays while changed triangles alter local interpolation.','No animation or perceived silhouette judgment.']}
m.save(m.O/'identity-boundary-report.json',report);print(json.dumps({k:v for k,v in report.items()if k not in ['actualArrays','embeddedImages','limits']}))
