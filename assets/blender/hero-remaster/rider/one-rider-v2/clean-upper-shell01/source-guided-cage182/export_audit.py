"""Export one frozen geometry and compact literal combined physical topology gate."""
import numpy as np,json,struct,hashlib,copy
from pathlib import Path
R=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/clean-upper-shell01/source-guided-cage182');E=Path('/Users/raynos/projects/games/rockhop/docs/evidence/hero-remaster/one-rider-v2/clean-upper-shell01/source-guided-cage182');S=Path('/Users/raynos/Documents/Codex/2026-10-01/task-3/deliverables/C19.glb')
raw=S.read_bytes();n=struct.unpack_from('<I',raw,12)[0];j=json.loads(raw[20:20+n]);b=bytearray(raw[28+n:]);original=copy.deepcopy(j);prefix=bytes(b)
def acc(i):
 a=j['accessors'][i];v=j['bufferViews'][a['bufferView']];dt={5126:'<f4',5125:'<u4',5123:'<u2',5121:'u1'}[a['componentType']];k={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}[a['type']];return np.ndarray((a['count'],k),dtype=dt,buffer=b,offset=v.get('byteOffset',0)+a.get('byteOffset',0),strides=(v.get('byteStride',np.dtype(dt).itemsize*k),np.dtype(dt).itemsize)).copy()
def add(x,kind,component):
 x=np.ascontiguousarray(x);bb=x.tobytes();b.extend(b'\0'*((-len(b))%4));offset=len(b);b.extend(bb);vi=len(j['bufferViews']);j['bufferViews'].append({'buffer':0,'byteOffset':offset,'byteLength':len(bb)});ai=len(j['accessors']);j['accessors'].append({'bufferView':vi,'componentType':component,'count':len(x),'type':kind})
 if kind=='VEC3':j['accessors'][-1].update(min=x.min(0).tolist(),max=x.max(0).tolist())
 return ai
c=np.load(R/'cage01.npz');V=c['p'];F=c['f'];l=np.load(R/'lower-cut01.npz');LP=l['p'];LF=l['f'].astype('u4');ancestry=json.loads((R/'lower-cut-ancestry.json').read_text());sourcebody=original['meshes'][0]['primitives'][0];attrs={k:acc(i) for k,i in sourcebody['attributes'].items()};body=j['meshes'][0]['primitives'][0];derived={}
for k,x in attrs.items():
 extra=[]
 for a in ancestry:
  u,v=a['sourceEdge'];t=a['edgeParameter']
  if k=='POSITION':value=LP[a['newRow']]
  elif k.startswith('JOINTS'):value=x[u] if t<.5 else x[v]
  else:value=(x[u].astype(float)*(1-t)+x[v].astype(float)*t).astype(x.dtype)
  extra.append(value)
 arr=np.concatenate([x,np.array(extra,dtype=x.dtype)]);derived[k]=arr;old=j['accessors'][sourcebody['attributes'][k]];body['attributes'][k]=add(arr,old['type'],old['componentType'])
body['indices']=add(LF.reshape(-1,1),'SCALAR',5125)
normal=np.zeros(V.shape,dtype=float);T=V[F].astype(float);cross=np.cross(T[:,1]-T[:,0],T[:,2]-T[:,0])
for a in range(3):np.add.at(normal,F[:,a],cross)
normal/=np.maximum(np.linalg.norm(normal,axis=1)[:,None],1e-20);normal=normal.astype('f4')
mat=len(j['materials']);j['materials'].append({'name':'UNBAKED plain construction cloth','pbrMetallicRoughness':{'baseColorFactor':[.48,.24,.055,1],'metallicFactor':0,'roughnessFactor':.86}})
mesh=len(j['meshes']);j['meshes'].append({'name':'UNACCEPTED_CAGE182','primitives':[{'attributes':{'POSITION':add(V,'VEC3',5126),'NORMAL':add(normal,'VEC3',5126)},'indices':add(F.reshape(-1,1),'SCALAR',5125),'material':mat}]});ni=len(j['nodes']);j['nodes'].append({'mesh':mesh,'name':'UNACCEPTED_CAGE182_UNRIGGED'});j['scenes'][j.get('scene',0)]['nodes'].append(ni)
for q in j['nodes']:q.pop('skin',None)
j.pop('skins',None);j.pop('animations',None);j['buffers'][0]['byteLength']=len(b);assert bytes(b[:len(prefix)])==prefix;assert j['meshes'][1]==original['meshes'][1];assert j['meshes'][0]['primitives'][1:]==original['meshes'][0]['primitives'][1:]
js=json.dumps(j,separators=(',',':')).encode();js+=b' '*((-len(js))%4);b+=b'\0'*((-len(b))%4);out=struct.pack('<III',0x46546c67,2,28+len(js)+len(b))+struct.pack('<II',len(js),0x4e4f534a)+js+struct.pack('<II',len(b),0x004e4942)+b;assert not (R/'neutral-assembly01.glb').exists() or (R/'neutral-assembly01.glb').read_bytes()==out;(R/'neutral-assembly01.glb').write_bytes(out)
# All body components and final node ancestry in ONE authoritative world/glTF bodydata freeze.
parts=[(LP,LF)];payload={'p0':LP,'f0':LF,'newShellP':V,'newShellF':F,'newShellN':normal,'hoodIDs':c['hoodIDs'],'hemIDs':c['hemIDs'],'cuffLIDs':c['cuffLIDs'],'cuffRIDs':c['cuffRIDs'],'authoredQuads':c['quads']}
for k,x in derived.items():payload['p0attribute_'+k]=x
for i in [1,2]:
 q=original['meshes'][0]['primitives'][i];P=acc(q['attributes']['POSITION']);f=acc(q['indices']).reshape(-1,3);payload['p'+str(i)]=P;payload['f'+str(i)]=f;parts.append((P,f))
parts.append((V,F));np.savez(R/'bodydata01.npz',**payload)
PP=[];FF=[];offset=0
for P,f in parts:PP.append(P);FF.append(f+offset);offset+=len(P)
PP=np.concatenate(PP);FF=np.concatenate(FF);U,inv=np.unique(PP,axis=0,return_inverse=True);physical=inv[FF];edges={};orient={}
for ti,t in enumerate(physical):
 for a,z in zip(t,np.roll(t,-1)):
  e=tuple(sorted((int(a),int(z))));edges.setdefault(e,[]).append(ti);orient.setdefault(e,[]).append(a<z)
area=np.linalg.norm(np.cross(PP[FF][:,1].astype(float)-PP[FF][:,0],PP[FF][:,2].astype(float)-PP[FF][:,0]),axis=1)/2
shellarea=np.linalg.norm(cross,axis=1)/2
# Seam edges must appear exactly twice with opposite winding in final physical body topology.
def coverage(ids):
 group={tuple(p):int(i) for i,p in enumerate(U)};pos=V[ids];counts=[];bad=[]
 for a,z in zip(pos,np.roll(pos,-1,axis=0)):
  e=tuple(sorted((group[tuple(a)],group[tuple(z)])));n=len(edges.get(e,[]));ok=n==2 and orient[e][0]!=orient[e][1];counts.append(ok)
  if not ok:bad.append({'edgePositions':[a.tolist(),z.tolist()],'incidence':n})
 return {'edges':len(ids),'pairedOpposite':sum(counts),'failed':len(ids)-sum(counts),'firstWitnesses':bad[:3]}
seams={k:coverage(c[k]) for k in ['hoodIDs','hemIDs','cuffLIDs','cuffRIDs']};audit={'status':'FROZEN_COMBINED_FLOAT32_GATE','sourceBINPrefixExact':True,'protectedHeadMeshesExact':True,'protectedHoodGlovePrimitivesExact':True,'originalPBRImageDefinitionsPrefixExact':True,'source0DerivedClipAttributes':'Original rows retained;319cutrows explicitly interpolated on sourceedge; joints nearestendpoint diagnosticonly; all skin/animations removed.','assemblySHA256':hashlib.sha256(out).hexdigest(),'bodydataSHA256':hashlib.sha256((R/'bodydata01.npz').read_bytes()).hexdigest(),'shellDegenerateBelow1e12':int((shellarea<1e-12).sum()),'combinedDegenerateBelow1e12':int((area<1e-12).sum()),'combinedNonmanifoldEdges':sum(len(x)>2 for x in edges.values()),'combinedWrongWindingEdges':sum(len(ids)==2 and orient[e][0]==orient[e][1] for e,ids in edges.items()),'combinedBoundaryEdges':sum(len(ids)==1 for ids in edges.values()),'seamCoverage':seams,'lowerCutPlane':'Y=.940+.20*(X-.640), explicitnewwardrobedesigncut; not semantic sourcehem','ghostSleeveComponentsRemoved':True,'crossings':'NOT_RUN_YET: conservative source+shell triangle audit required; no BVH selfzero claim.','limits':'Physical topology failure stopsrender. No appearance/pose/rig/weight/game-ready acceptance.'}
audit['gatePass']=audit['shellDegenerateBelow1e12']==0 and audit['combinedDegenerateBelow1e12']==0 and audit['combinedNonmanifoldEdges']==0 and audit['combinedWrongWindingEdges']==0 and all(v['failed']==0 for v in seams.values());(E/'export-audit.json').write_text(json.dumps(audit,indent=2,default=lambda x:x.item()));print(json.dumps(audit,default=lambda x:x.item()))
