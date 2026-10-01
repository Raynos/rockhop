"""Frozen actual V5 glove/body physical seam inventory; no geometry edits."""
from pathlib import Path
from collections import defaultdict,Counter
import json,struct,hashlib,numpy as np
REPO=Path('/Users/raynos/projects/games/rockhop');ROOT=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2');RUN=ROOT/'basic-pose-seams163';OUT=REPO/'docs/evidence/hero-remaster/one-rider-v2/basic-pose-seams163';RUN.mkdir(exist_ok=True);OUT.mkdir(parents=True,exist_ok=True);SRC=ROOT/'garment-rebuild01/physical-v5-control157/rider.glb';FIX=ROOT/'basic-pose-gate158/fixture-v4-asymmetric-halfsteps.json';raw=SRC.read_bytes();fr=FIX.read_bytes();sha=lambda b:hashlib.sha256(b).hexdigest();assert sha(raw)=='2100384b8f2183e98e6e0c78d8b717718b1cc57dd8298e76fab53c1d491c77e9';assert sha(fr)=='78732965343f6eba40ae68ca99ffa949f6718910eb7b930b67d4a48d0083afab';n=struct.unpack_from('<I',raw,12)[0];doc=json.loads(raw[20:20+n]);blob=raw[28+n:]
def acc(i):
 a=doc['accessors'][i];w={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}[a['type']];d={5121:'u1',5123:'<u2',5125:'<u4',5126:'<f4'}[a['componentType']]
 def read(vi,offset,count,width,dtype):
  v=doc['bufferViews'][vi];dt=np.dtype(dtype);return np.ndarray((count,width),dtype=dt,buffer=blob,offset=v.get('byteOffset',0)+offset,strides=(v.get('byteStride',dt.itemsize*width),dt.itemsize)).copy()
 x=read(a['bufferView'],a.get('byteOffset',0),a['count'],w,d) if 'bufferView'in a else np.zeros((a['count'],w),dtype=d)
 if 'sparse'in a:
  sparse=a['sparse'];indices=sparse['indices'];values=sparse['values'];ids=read(indices['bufferView'],indices.get('byteOffset',0),sparse['count'],1,{5121:'u1',5123:'<u2',5125:'<u4'}[indices['componentType']]).reshape(-1);x[ids]=read(values['bufferView'],values.get('byteOffset',0),sparse['count'],w,d)
 return x
sk=doc['skins'][0];names=[doc['nodes'][i]['name'] for i in sk['joints']];fixture=json.loads(fr);assert names==fixture['jointNames'];rows=[]
for pi in [0,1]:
 p=doc['meshes'][0]['primitives'][pi];attrs={k:acc(i) for k,i in p['attributes'].items()};P=attrs['POSITION'];u,inv=np.unique(P,axis=0,return_inverse=True);aliases=[np.flatnonzero(inv==i).tolist() for i in range(len(u))];T=acc(p['indices']).reshape(-1,3);phys=inv[T];edges=np.sort(np.concatenate([phys[:,[0,1]],phys[:,[1,2]],phys[:,[2,0]]]),axis=1);e,c=np.unique(edges,axis=0,return_counts=True);boundary=e[c==1];weights=np.zeros((len(P),19))
 for lane in range(4):np.add.at(weights,(np.arange(len(P)),attrs['JOINTS_0'][:,lane]),attrs['WEIGHTS_0'][:,lane])
 targets=[{k:acc(i) for k,i in target.items()} for target in p.get('targets',[])];rows.append({'pi':pi,'attrs':attrs,'P':P,'U':u,'inverse':inv,'aliases':aliases,'T':T,'physT':phys,'edges':e,'counts':c,'boundary':boundary,'W':weights,'targets':targets,'targetNames':doc['meshes'][0].get('extras',{}).get('targetNames',[])})
body,glove=rows;bk={tuple(p):i for i,p in enumerate(body['U'])};gk={tuple(p):i for i,p in enumerate(glove['U'])};common=sorted(set(bk)&set(gk));assert len(common)==127;groups=[]
for group,key in enumerate(common):
 bi=body['aliases'][bk[key]];gi=glove['aliases'][gk[key]];weights=np.r_[body['W'][bi],glove['W'][gi]];morph=[np.r_[body['targets'][i]['POSITION'][bi],glove['targets'][i]['POSITION'][gi]] for i in range(len(body['targets']))];assert np.ptp(weights,axis=0).max()==0
 groups.append({'group':group,'position':[float(v) for v in key],'bodyVertexIDs':bi,'gloveVertexIDs':gi,'weights19':weights[0].tolist(),'maximumAliasWeightComponentDifference':float(np.ptp(weights,axis=0).max()),'morphPositions':{'maximumSharedDeltaComponentGap':max(float(np.ptp(x,axis=0).max()) for x in morph),'targets':[x[0].tolist() for x in morph]},'side':'L' if key[2]>0 else 'R'})
commonID={key:i for i,key in enumerate(common)};be={tuple(sorted((tuple(body['U'][a]),tuple(body['U'][b])))):int(c) for (a,b),c in zip(body['edges'],body['counts'])};ge={tuple(sorted((tuple(glove['U'][a]),tuple(glove['U'][b])))):int(c) for (a,b),c in zip(glove['edges'],glove['counts'])};matched=[];unmatched=[]
for a,b in glove['boundary']:
 key=tuple(sorted((tuple(glove['U'][a]),tuple(glove['U'][b]))));row={'endpointGroups':[commonID[key[0]],commonID[key[1]]],'bodyIncidentFaces':be.get(key,0),'gloveIncidentFaces':ge[key],'restEdgeMeters':float(np.linalg.norm(np.array(key[0])-np.array(key[1])))}
 (matched if be.get(key)==1 and ge[key]==1 else unmatched).append(row)
assert len(matched)==127 and not unmatched;adj=defaultdict(list)
for e in matched:a,b=e['endpointGroups'];adj[a].append(b);adj[b].append(a)
assert all(len(a)==2 for a in adj.values());todo=set(adj);loops=[]
while todo:
 start=min(todo);prev=None;cur=start;loop=[]
 while cur not in loop:
  loop.append(cur);nxt=next(v for v in sorted(adj[cur]) if v!=prev);prev,cur=cur,nxt
 assert cur==start;todo-=set(loop);loops.append({'groupIDs':loop,'vertices':len(loop),'side':groups[loop[0]]['side']})
scopes=[]
for r in rows:
 physSeam={bk[k] if r['pi']==0 else gk[k] for k in common};near=np.isin(r['physT'],list(physSeam)).any(1);regionIDs=set(r['physT'][near].reshape(-1));region=np.isin(r['physT'],list(regionIDs)).any(1);faceIDs=np.flatnonzero(region);vertexIDs=np.unique(r['T'][faceIDs]);scopes.append({'primitive':r['pi'],'vertices':vertexIDs.tolist(),'triangles':r['T'][faceIDs].tolist(),'sourceTriangleIDs':faceIDs.tolist(),'scope':'two topological face rings incident to exact seam; no capsule/distance heuristic'})
payload={'source':str(SRC),'sourceSHA256':sha(raw),'fixture':str(FIX),'fixtureSHA256':sha(fr),'jointNames':names,'inverseBindsColumnMajor':acc(sk['inverseBindMatrices']).tolist(),'groups':groups,'matchedBoundaryEdges':matched,'loops':loops,'scopes':scopes,'meshes':[{'primitive':r['pi'],'name':'Protected_body_NEW_hood_joined_garment'+('_1' if r['pi']==1 else ''),'attrs':{k:v.tolist() for k,v in r['attrs'].items()},'targets':[{k:v.tolist() for k,v in t.items()} for t in r['targets']],'targetNames':r['targetNames']} for r in rows]};(RUN/'raw-seam-input.json').write_text(json.dumps(payload,separators=(',',':'))+'\n')
for p,b in [(RUN/'rider-source.glb',raw),(RUN/'fixture-v4.json',fr)]:
 if p.exists():assert p.read_bytes()==b
 else:p.write_bytes(b)
report={k:payload[k] for k in ['source','sourceSHA256','fixture','fixtureSHA256','jointNames','groups','matchedBoundaryEdges','loops','scopes']};report['rawInputSHA256']=sha((RUN/'raw-seam-input.json').read_bytes());report['topologyMeaning']='Both loops are matching open physical boundaries, each edge has1cloth+1glove triangle. Material primitives/UV-normal aliases stay separate but share exact restpos/19weights; this is sewn-surface-equivalent boundary coverage, not merely disjoint overlapping closed shells.';report['limits']=['No solid/thickness/manifoldwholecharacter or intersection clearance claim.','Near-seam triangles test two topological rings only; other sleeve/body/finger defects are out of this regional scope.','Normal/UV continuity and actual posed endpoint gaps are evaluated separately; topology equality is not visible contact acceptance.'];assert SRC.read_bytes()==raw and FIX.read_bytes()==fr;(OUT/'raw-topology.json').write_text(json.dumps(report,separators=(',',':'))+'\n');print(json.dumps({'loops':loops,'scopes':[(x['primitive'],len(x['vertices']),len(x['triangles'])) for x in scopes],'matchedEdges':len(matched)}))
