"""Read-only contract inspection of explicitly unrigged draft178; no binding."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
sys.dont_write_bytecode=True
R=Path('/Users/raynos/projects/games/rockhop/assets/blender/hero-remaster/rider/one-rider-v2/foundation-repair-task3');sys.path.insert(0,str(R/'scripts'));from glb import GLB
source=R/'deliverables/C19.glb';candidate=Path(sys.argv[1]);out=Path(sys.argv[2]);assert not out.exists();g=GLB(source);h=GLB(candidate)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def access(doc,a):
 ac=doc.j['accessors'][a];meta={k:v for k,v in ac.items() if k not in ['bufferView','byteOffset','min','max','sparse']};parts=[]
 if'bufferView'in ac:parts.append(doc.array(a).tobytes())
 if'sparse'in ac:
  sp=ac['sparse'];parts.append(json.dumps({k:v for k,v in sp.items()if k not in ['indices','values']},sort_keys=True).encode())
  for kind in ['indices','values']:
   node=sp[kind];bv=doc.j['bufferViews'][node['bufferView']];parts.append(bytes(doc.bin[bv.get('byteOffset',0):bv.get('byteOffset',0)+bv['byteLength']]));parts.append(json.dumps({k:v for k,v in node.items()if k!='bufferView'},sort_keys=True).encode())
 return meta,hashlib.sha256(b''.join(parts)).hexdigest()
def embedded_image(doc,i):
 im=doc.j['images'][i];v=doc.j['bufferViews'][im['bufferView']];return hashlib.sha256(bytes(doc.bin[v.get('byteOffset',0):v.get('byteOffset',0)+v['byteLength']])).hexdigest()
protected=[]
for mi,pi,label in [(0,1,'gloves'),(1,0,'main head'),(1,1,'cheek'),(0,2,'source hood donor; component semantics remain explicit')]:
 p,q=g.j['meshes'][mi]['primitives'][pi],h.j['meshes'][mi]['primitives'][pi];samekeys=set(p['attributes'])==set(q['attributes']);attrs={k:access(g,p['attributes'][k])==access(h,q['attributes'][k])for k in p['attributes']};ix=access(g,p['indices'])==access(h,q['indices']);morph=len(p.get('targets',[]))==len(q.get('targets',[]))and all(set(a)==set(b)and all(access(g,a[k])==access(h,b[k])for k in a)for a,b in zip(p.get('targets',[]),q.get('targets',[])));protected.append({'mesh':mi,'primitive':pi,'label':label,'attributeKeysExact':samekeys,'attributeStoredBytesAndFlagsExact':attrs,'indexEncodingAndBytesExact':ix,'morphAccessorAndSparseBytesExact':morph,'materialJSONExact':g.j['materials'][p['material']]==h.j['materials'][q['material']]})
images=all(embedded_image(g,i)==embedded_image(h,i)for i in range(len(g.j.get('images',[]))));tables={k:g.j.get(k,[])==h.j.get(k,[])[:len(g.j.get(k,[]))]for k in ['textures','samplers']}
report={'status':'READONLY INVALID-REST NEUTRAL DRAFT EXPORT INSPECTION; NO RIGGING OR RUNTIME ACCEPTANCE','sourcePath':str(source),'sourceSHA256':sha(source),'candidateOwnedCopy':str(candidate),'candidateSHA256':sha(candidate),'sourceBINPrefixExact':bytes(h.bin[:len(g.bin)])==bytes(g.bin),'protected':protected,'allSourceEmbeddedImageBytesExact':images,'originalTextureAndSamplerTablesExact':tables,'currentNeutralDifferences':{'skinsPresent':bool(h.j.get('skins')),'meshNodeSkinBindings':sum('skin'in n for n in h.j['nodes']),'animationsPresent':bool(h.j.get('animations')),'primitive0IndicesChanged':access(g,g.j['meshes'][0]['primitives'][0]['indices'])!=access(h,h.j['meshes'][0]['primitives'][0]['indices']),'additionalMeshes':len(h.j['meshes'])-len(g.j['meshes'])},'futureContract':'After valid rest and selection ONLY: explicit19 C19/socket anatomy contract, actual<=4 weight influences without truncation, seam-alias P/W/N consistency, original170 protected/PBR guard, actual ancestor-scoped conditioned flag, full stockThree P/N parity for postbone driver and continuous geometry/contact/Garage gates. Additional shell namespace currently requires reviewed mapping rather than pretending170 five-primitive compatibility.','limits':'Unrigged neutral inspection cannot show pose quality. Old donor hood/cuffs are reference until real sewn joins qualified. Invalid13nonmanifold prototype is withheld from bind/runtime tests.'}
out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items()if k not in ['protected','futureContract']},indent=2))
