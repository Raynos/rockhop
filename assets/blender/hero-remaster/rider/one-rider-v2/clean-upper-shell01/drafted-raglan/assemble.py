"""Preserve original donor bytes while assembling one failed neutral shell."""
import json, struct, hashlib, copy
from pathlib import Path
R=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/clean-upper-shell01/drafted-raglan')
E=Path('/Users/raynos/projects/games/rockhop/docs/evidence/hero-remaster/one-rider-v2/clean-upper-shell01/drafted-raglan')
S=Path('/Users/raynos/Documents/Codex/2026-10-01/task-3/deliverables/C19.glb')
def read(p):
 raw=p.read_bytes();n=struct.unpack_from('<I',raw,12)[0]
 return json.loads(raw[20:20+n]),bytearray(raw[28+n:]),raw
j,b,original=read(S);k,c,_=read(R/'shell01.glb');sourcej=copy.deepcopy(j);sourcebin=bytes(b)
def array(doc,bin,i):
 a=doc['accessors'][i];v=doc['bufferViews'][a['bufferView']];fmt={5126:'f',5125:'I',5123:'H',5121:'B'}[a['componentType']];n={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}[a['type']];stride=v.get('byteStride',struct.calcsize(fmt)*n);off=v.get('byteOffset',0)+a.get('byteOffset',0)
 return [struct.unpack_from('<'+fmt*n,bin,off+t*stride) for t in range(a['count'])]
def append_indices(indices):
 while len(b)%4:b.append(0)
 off=len(b);b.extend(struct.pack('<'+'I'*len(indices),*indices));vi=len(j['bufferViews']);j['bufferViews'].append({'buffer':0,'byteOffset':off,'byteLength':len(indices)*4,'target':34963});ai=len(j['accessors']);j['accessors'].append({'bufferView':vi,'componentType':5125,'count':len(indices),'type':'SCALAR'})
 return ai
q=j['meshes'][0]['primitives'][0];p=array(j,b,q['attributes']['POSITION']);ix=[x[0] for x in array(j,b,q['indices'])];kept=[];keptids=[]
for t in range(0,len(ix),3):
 tri=ix[t:t+3];ps=[p[a] for a in tri]
 # glTF coordinate semantics: X forward, Y height, Z lateral.
 lower=max(x[1] for x in ps)<=.965
 cuff=max(x[1] for x in ps)<=.955 and min(abs(x[2]) for x in ps)>=.28
 if lower or cuff:kept+=tri;keptids.append(t//3)
q['indices']=append_indices(kept)
while len(b)%4:b.append(0)
base=len(b);b.extend(c);av=len(j['bufferViews']);aa=len(j['accessors']);am=len(j['materials'])
for v in k['bufferViews']:
 v=copy.deepcopy(v);v['byteOffset']=base+v.get('byteOffset',0);v['buffer']=0;j['bufferViews'].append(v)
for a in k['accessors']:
 a=copy.deepcopy(a);a['bufferView']+=av;j['accessors'].append(a)
j['materials']+=k['materials'];mesh=copy.deepcopy(k['meshes'][0])
for q in mesh['primitives']:
 q['indices']+=aa;q['attributes']={a:i+aa for a,i in q['attributes'].items()};q['material']+=am
mi=len(j['meshes']);j['meshes'].append(mesh);ni=len(j['nodes']);j['nodes'].append({'mesh':mi,'name':'UNACCEPTED_UNRIGGED_NEW_RAGLAN_SHELL01'});j['scenes'][j.get('scene',0)]['nodes'].append(ni)
for n in j['nodes']:n.pop('skin',None)
j.pop('animations',None);j.pop('skins',None);j['buffers'][0]['byteLength']=len(b)
j.setdefault('extras',{})['status']='FAILED_NEUTRAL_TOPOLOGY_ONLY_UNRIGGED_UNBAKED_NO_GAME_PROMOTION'
jb=json.dumps(j,separators=(',',':')).encode();jb+=b' '*((-len(jb))%4);b+=b'\0'*((-len(b))%4)
raw=struct.pack('<III',0x46546c67,2,28+len(jb)+len(b))+struct.pack('<II',len(jb),0x4e4f534a)+jb+struct.pack('<II',len(b),0x004e4942)+b;(R/'neutral-assembly01.glb').write_bytes(raw)
assert bytes(b[:len(sourcebin)])==sourcebin
assert j['meshes'][1]==sourcej['meshes'][1]
for key in ['materials','images','textures','samplers']:
 assert j.get(key,[])[:len(sourcej.get(key,[]))]==sourcej.get(key,[])
rep={'status':'FAILED_NEUTRAL_PROTOTYPE_NOT_RIGGED','sourceSHA256':hashlib.sha256(original).hexdigest(),'assemblySHA256':hashlib.sha256(raw).hexdigest(),'sourceBINPrefixExact':True,'protectedHeadAllMeshAttributesMorphsPrimitiveIndicesExact':True,'protectedHeadOriginalPBRMaterialsImagesTexturesSamplersExact':True,'sourceHoodAndGlovesPrimitiveExact':True,'sourcePrimitive0OriginalAttributesRetainedExact':'Indices only filtered; unused vertex rows retained.','semanticMask':'primitive0 all triangle vertices glTFY<=.965 (lower) or maxY<=.955 and minabsZ>=.28 (cuff); primitive1 gloves entire; primitive2 hood entire.','sourcePrimitive0RetainedTriangles':len(keptids),'sourcePrimitive0DeletedTriangles':len(ix)//3-len(keptids),'sourcePrimitive0RetainedTriangleIDs':keptids,'skinAndAnimationExportDifference':'All mesh skin bindings and authored animations removed for explicitly neutral/unrigged assembly; original protected geometry/PBR byte exact in assembled GLB. Render import may transform data.','seams':'Separate protected identity references, no donor-shell physical welding; measurements pending.','limits':'Not accepted; shell nonmanifold defects frozen, no pose or appearance score.'}
(E/'assembly.json').write_text(json.dumps(rep,indent=2));print(json.dumps({k:v for k,v in rep.items() if k!='sourcePrimitive0RetainedTriangleIDs'}))
