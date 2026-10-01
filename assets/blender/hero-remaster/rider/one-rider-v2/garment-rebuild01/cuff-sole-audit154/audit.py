"""Read-only exact physical boundaries, literal cuff/ankle sewing candidates.
No GLB, weights, source geometry or fit is changed. CPU only, two threads.
"""
from pathlib import Path
import json,struct,hashlib
from collections import defaultdict,Counter
import numpy as np
from scipy.spatial import cKDTree
REPO=Path('/Users/raynos/projects/games/rockhop')
ROOT=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2')
OUT=REPO/'docs/evidence/hero-remaster/one-rider-v2/garment-rebuild01/cuff-sole-audit154';OUT.mkdir(parents=True,exist_ok=True)
SRC=ROOT/'rig-adapter01/body-bind34/rider.glb';FIT=ROOT/'garment-rebuild01/cage04/fit04.npz';raw=SRC.read_bytes();fr=FIT.read_bytes();n=struct.unpack_from('<I',raw,12)[0];doc=json.loads(raw[20:20+n]);blob=raw[28+n:]
sha=lambda b:hashlib.sha256(b).hexdigest()
def acc(i):
 a=doc['accessors'][i];v=doc['bufferViews'][a['bufferView']];assert 'byteStride' not in v and 'sparse' not in a
 d={5121:'u1',5123:'<u2',5125:'<u4',5126:'<f4'}[a['componentType']];w={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}[a['type']]
 return np.frombuffer(blob,dtype=d,count=a['count']*w,offset=v.get('byteOffset',0)+a.get('byteOffset',0)).reshape(a['count'],w).copy()
names=[doc['nodes'][i]['name'] for i in doc['skins'][0]['joints']];assert len(names)==19
pr=[]
for pi,p in enumerate(doc['meshes'][0]['primitives']):
 a=p['attributes'];P=acc(a['POSITION']);J=acc(a['JOINTS_0']);wt=acc(a['WEIGHTS_0']);W=np.zeros((len(P),19))
 for i in range(4):np.add.at(W,(np.arange(len(P)),J[:,i]),wt[:,i])
 pr.append({'P':P,'T':acc(p['indices']).reshape(-1,3),'W':W})
f=np.load(FIT);native={'P':f['positions'],'T':f['quads'],'W':f['weights']}
def physical(item):
 P,inv=np.unique(item['P'],axis=0,return_inverse=True);aliases=[[] for _ in P]
 for i,j in enumerate(inv):aliases[j].append(i)
 weights=np.array([item['W'][ids].mean(0) for ids in aliases]);return P,inv,aliases,weights

def boundary(item,mask=None):
 P,inv,aliases,W=physical(item);faces=inv[item['T'] if mask is None else item['T'][mask]]
 ed=np.sort(np.concatenate([faces[:,[i,(i+1)%faces.shape[1]]] for i in range(faces.shape[1])]),axis=1);e,c=np.unique(ed,axis=0,return_counts=True);e=e[c==1];adj=defaultdict(list)
 for a,b in e:adj[int(a)].append(int(b));adj[int(b)].append(int(a))
 todo=set(adj);rows=[]
 while todo:
  root=min(todo);stack=[root];comp=set()
  while stack:
   i=stack.pop()
   if i in comp:continue
   comp.add(i);stack.extend(adj[i])
  todo-=comp;degree2=all(len(adj[i])==2 for i in comp)
  order=[]
  if degree2:
   prev=None;cur=min(comp)
   while cur not in order:
    order.append(cur);nxt=next(j for j in sorted(adj[cur]) if j!=prev);prev,cur=cur,nxt
   assert cur==order[0] and len(order)==len(comp)
  else:order=sorted(comp)
  q=P[order];rows.append({'physicalIDs':order,'originalAliases':[aliases[i] for i in order],'positions':q.tolist(),'weights19':W[order].tolist(),'vertices':len(comp),'closedDegree2':degree2,'boundaryDegreeHistogram':dict(Counter(len(adj[i]) for i in comp)),'center':q.mean(0).tolist(),'bounds':np.c_[q.min(0),q.max(0)].tolist(),'perimeterMeters':float(np.linalg.norm(q-np.roll(q,-1,axis=0),axis=1).sum()) if degree2 else None})
 return {'physicalVertices':len(P),'boundaryEdges':len(e),'nonmanifoldEdges':int((c>2).sum()),'loops':rows},(P,inv,aliases,W)
report={'kind':'Read-only literal cuff/ankle interface audit; no seam acceptance','sourceSHA256':sha(raw),'fit04SHA256':sha(fr),'canonical19':names,'interfaces':{},'sourcePositionTouch':{}}
for name,item in [('body',pr[0]),('gloves',pr[1]),('hood',pr[2]),('native',native)]:
 r,ph=boundary(item);report['interfaces'][name]=r
# Raw source shoe preservation rule from fixture (game Y<.2, all corners).
shoeMask=np.all(pr[0]['P'][pr[0]['T'],1]<.2,axis=1);r,ph=boundary(pr[0],shoeMask);r['sourceTriangleIDs']=np.flatnonzero(shoeMask).tolist();report['interfaces']['shoeCutY02']=r
# Exact shared-position source aliases and full canonical weight disagreements.
bP,bi,ba,bW=physical(pr[0]);gP,gi,ga,gW=physical(pr[1]);lookup={tuple(p):i for i,p in enumerate(bP)}
for name,item in [('gloves',pr[1]),('hood',pr[2])]:
 sP,si,sa,sW=physical(item);rows=[]
 for i,p in enumerate(sP):
  j=lookup.get(tuple(p))
  if j is not None:rows.append({'bodyPhysicalID':j,'bodyVertexIDs':ba[j],'otherPhysicalID':i,'otherVertexIDs':sa[i],'position':p.tolist(),'bodyWeights19':bW[j].tolist(),'otherWeights19':sW[i].tolist(),'weightL1':float(abs(bW[j]-sW[i]).sum())})
 report['sourcePositionTouch'][name]={'count':len(rows),'rows':rows,'maximumWeightL1':max([r['weightL1'] for r in rows],default=0)}
report['limits']=['Exact physical positions merge UV/normal aliases only; does not spatially weld nearby vertices.','Boundary loops may be structurally closed but still represent a bad planar cut.','No mesh edits, original gloves/sole contacts/head/hood and all source bytes untouched.','No cloth seam is accepted; parent must judge full moving evidence.']
assert SRC.read_bytes()==raw and FIT.read_bytes()==fr
(OUT/'boundaries.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:{'physicalVertices':v['physicalVertices'],'boundaryEdges':v['boundaryEdges'],'loops':[{'n':l['vertices'],'center':l['center'],'closed':l['closedDegree2']} for l in v['loops']]} for k,v in report['interfaces'].items()},indent=2));print({k:v['count'] for k,v in report['sourcePositionTouch'].items()})
# Topological inward quad rings are literal sewing alternatives; no nearest snapping.
P,inv,alias,W=physical(native);Q=inv[native['T']];edgeFaces=defaultdict(list)
for qi,q in enumerate(Q):
 for a,b in zip(q,np.roll(q,-1)):edgeFaces[tuple(sorted((int(a),int(b))))].append(qi)
def inward_layers(order,maxlayers=4):
 layers=[];used=set();ring=order
 for depth in range(maxlayers+1):
  p=P[ring];layers.append({'layer':depth,'physicalIDs':ring,'nativeVertexIDs':[alias[i][0] for i in ring],'center':p.mean(0).tolist(),'bounds':np.c_[p.min(0),p.max(0)].tolist(),'positions':p.tolist(),'weights19':W[ring].tolist(),'removedQuadIDs':sorted(used)})
  opposite=[];faceids=[]
  for a,b in zip(ring,ring[1:]+ring[:1]):
   candidates=[j for j in edgeFaces[tuple(sorted((a,b)))] if j not in used]
   if len(candidates)!=1:return layers
   qi=candidates[0];q=Q[qi].tolist();ia=q.index(a);ib=q.index(b);other=[j for j in q if j not in [a,b]]
   if len(other)!=2:return layers
   opposite.append(tuple(other));faceids.append(qi)
  adj=defaultdict(list)
  for a,b in opposite:adj[a].append(b);adj[b].append(a)
  if not all(len(v)==2 for v in adj.values()):return layers
  start=min(adj);cur=start;prev=None;new=[]
  while cur not in new:
   new.append(cur);nxt=next(j for j in sorted(adj[cur]) if j!=prev);prev,cur=cur,nxt
  if len(new)!=len(adj) or cur!=start:return layers
  used.update(faceids);ring=new
 return layers
layerRows=[]
for i,l in enumerate(report['interfaces']['native']['loops']):
 if (l['vertices']==20 and l['center'][1]<1) or l['vertices']==18:
  layerRows.append({'nativeBoundaryLoopIndex':i,'layers':inward_layers(l['physicalIDs'])})
(OUT/'inward-quad-rings.json').write_text(json.dumps({'kind':'Literal inward quad rings without geometry mutation','sourceFit04SHA256':sha(fr),'rows':layerRows},indent=2)+'\n')
print(json.dumps([{'loop':r['nativeBoundaryLoopIndex'],'layers':[{'depth':a['layer'],'n':len(a['physicalIDs']),'center':a['center']} for a in r['layers']]} for r in layerRows],indent=2))
def orient_boundary(ring,faces):
 directed={(int(a),int(b)) for q in faces for a,b in zip(q,np.roll(q,-1))}
 if (ring[0],ring[1]) not in directed:ring=[ring[0]]+ring[:0:-1]
 assert all((a,b) in directed for a,b in zip(ring,ring[1:]+ring[:1]))
 return ring

def zipper(A,B,PA,PB):
 # Global cyclic phase plus monotone minimum bridge-edge energy.
 n,m=len(A),len(B);best=None
 for phase in range(m):
  bs=B[phase:]+B[:phase];a=A+[A[0]];b=bs+[bs[0]]
  dist=((PA[a][:,None,:]-PB[b][None,:,:])**2).sum(2)
  cost=np.full((n+1,m+1),np.inf);cost[0,0]=dist[0,0];prev={}
  for i in range(n+1):
   for j in range(m+1):
    if i==j==0:continue
    ca=cost[i-1,j] if i else np.inf;cb=cost[i,j-1] if j else np.inf
    if ca<cb:cost[i,j]=ca+dist[i,j];prev[(i,j)]=(i-1,j)
    else:cost[i,j]=cb+dist[i,j];prev[(i,j)]=(i,j-1)
  if best is None or cost[n,m]<best[0]:best=(cost[n,m],phase,bs,prev)
 _,phase,bs,prev=best;a=A+[A[0]];b=bs+[bs[0]];i,j=n,m;steps=[]
 while i or j:
  u,v=prev[(i,j)]
  if u<i:steps.append([['native',a[i]],['native',a[u]],['source',b[j]]])
  else:steps.append([['native',a[i]],['source',b[v]],['source',b[j]]])
  i,j=u,v
 return phase,list(reversed(steps)),best[0]

nativeByLoop={r['nativeBoundaryLoopIndex']:r for r in layerRows};seams=[]
for name,ni,scope,si in [('cuff.L',5,'gloves',0),('cuff.R',6,'gloves',1),('ankle.L',2,'shoeCutY02',0),('ankle.R',1,'shoeCutY02',1)]:
 layer=nativeByLoop[ni]['layers'][3];removed=np.array(layer['removedQuadIDs']);mask=np.ones(len(Q),bool);mask[removed]=False;A=orient_boundary(layer['physicalIDs'],Q[mask]);S=pr[1] if scope=='gloves' else pr[0];SP,iv,al,SW=physical(S);faces=iv[S['T'] if scope=='gloves' else S['T'][shoeMask]];sl=report['interfaces'][scope]['loops'][si];B=orient_boundary(sl['physicalIDs'],faces);B=[B[0]]+B[:0:-1]
 phase,triangles,cost=zipper(A,B,P,SP);pts=np.array([[P[idx] if typ=='native' else SP[idx] for typ,idx in t] for t in triangles]);area=np.linalg.norm(np.cross(pts[:,1]-pts[:,0],pts[:,2]-pts[:,0]),axis=1)/2
 aliasesLiteral=[[[('fit04-native' if typ=='native' else scope),alias[idx] if typ=='native' else al[idx]] for typ,idx in t] for t in triangles]
 seams.append({'name':name,'nativeLoopIndex':ni,'nativeInwardLayer':3,'nativeRemovedQuadIDs':layer['removedQuadIDs'],'nativeOrderedPhysicalIDs':A,'nativeOrderedVertexIDs':[alias[i][0] for i in A],'sourcePrimitive':1 if scope=='gloves' else 0,'sourceScope':scope,'sourceLoopIndex':si,'sourceOrderedPhysicalIDs':B,'sourceOrderedOriginalAliases':[al[i] for i in B],'cyclicPhase':phase,'bridgeTrianglesPhysicalNamespace':triangles,'bridgeTrianglesOriginalAliases':aliasesLiteral,'bridgeTriangles':len(triangles),'minimumTriangleAreaM2':float(area.min()),'maximumTriangleAreaM2':float(area.max()),'bridgeEnergyM2':float(cost),'newPositionsAltered':False,'sourceVerticesAltered':False,'nativeVsSourceCenterDeltaMeters':(np.mean(P[A],0)-np.mean(SP[B],0)).tolist(),'centerGapMeters':float(np.linalg.norm(np.mean(P[A],0)-np.mean(SP[B],0))),'weightRule':'Endpoint aliases retain exactly their existing19weights; any new intermediate bridge ring must linearly interpolate matching edge19vectors, normalize, and use one shared physical value across UV/normal aliases. Never independently snap vertices or retain duplicate disconnected surfaces.','limits':['Literal unbuilt sewing candidate, not accepted neck/clothing asset.','Source shoe patch is deliberately jagged original-edge cut, not planar skin surgery; bake transition must cover exposed replacement bridge.','Native bottom3quad strips removed only in proposal; retained files never changed.','Normal winding verified locally; no selfintersection or moving quality acceptance.']})
roiPath=REPO/'docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/played-surfaces11/framed04/source-roi.json';roi=json.loads(roiPath.read_bytes());probes=[]
for kind in ['hands','feet']:
 for e in roi[kind]:
  item=pr[1] if kind=='hands' else pr[0];ids=e['sourceVertices'];used=set(pr[0]['T'][shoeMask].reshape(-1)) if kind=='feet' else set(range(len(item['P'])))
  probes.append({'kind':kind,'side':e['side'],'sourcePrimitive':1 if kind=='hands' else 0,'sourceVertexIDs':ids,'count':len(ids),'allRetainedInSourcePatch':all(i in used for i in ids),'bounds':np.c_[item['P'][ids].min(0),item['P'][ids].max(0)].tolist(),'positionsSHA256':sha(item['P'][ids].tobytes()),'canonical19WeightsSHA256':sha(item['W'][ids].tobytes()),'evidenceMeaning':'Read-only unchanged source pads and retained patch membership; does not certify future moving grip/sole contacts.'})
assert all(p['allRetainedInSourcePatch'] for p in probes)
(OUT/'sewing-proposal.json').write_text(json.dumps({'status':'Unbuilt literal topological sewing proposal, not nearest-vertex snap or approved appearance','sourceSHA256':sha(raw),'fit04SHA256':sha(fr),'method':'Remove exactly3native quad strips per boundary, orient both true surface boundaries, reverse second boundary, globally optimize cyclic phase then monotone zipper DP. Shared endpoints keep all original source anatomy/weights and native ring weights.','seams':seams,'protectedContactROI_SHA256':sha(roiPath.read_bytes()),'protectedSourceContactProbes':probes},indent=2)+'\n')
assert SRC.read_bytes()==raw and FIT.read_bytes()==fr
print(json.dumps([{'name':s['name'],'triangles':s['bridgeTriangles'],'centerGapMeters':s['centerGapMeters'],'minimumTriangleAreaM2':s['minimumTriangleAreaM2']} for s in seams],indent=2))
# Sewing CPU stress evidence uses the retained actual34joint transforms, not poses invented here.
manifestPath=REPO/'docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/body-bind34/candidate-cpu/pose-manifest.json';manifest=json.loads(manifestPath.read_bytes());poseRoot=ROOT/'rig-adapter01/body-bind34/candidate-cpu';poseRows=[]
for row in manifest['rows']:
 rec=row['dump'][0]['jointTransforms'];bytes_=(poseRoot/rec['file']).read_bytes();assert sha(bytes_)==rec['sha256'];M=np.frombuffer(bytes_,dtype='<f8').reshape(-1,4,4).transpose(0,2,1)
 rows=[]
 for s in seams:
  sourceItem=pr[s['sourcePrimitive']];SP,iv,al,SW=physical(sourceItem);tri=s['bridgeTrianglesPhysicalNamespace'];pos=np.array([[P[i] if t=='native' else SP[i] for t,i in tr] for tr in tri]);weight=np.array([[W[i] if t=='native' else SW[i] for t,i in tr] for tr in tri]);posed=np.einsum('tvj,jab,tvb->tva',weight,M[:,:3,:],np.concatenate([pos,np.ones((*pos.shape[:2],1))],axis=2));restedges=np.linalg.norm(pos-np.roll(pos,-1,axis=1),axis=2);posededges=np.linalg.norm(posed-np.roll(posed,-1,axis=1),axis=2);stretch=posededges/np.maximum(restedges,1e-20);restarea=np.linalg.norm(np.cross(pos[:,1]-pos[:,0],pos[:,2]-pos[:,0]),axis=1);posedarea=np.linalg.norm(np.cross(posed[:,1]-posed[:,0],posed[:,2]-posed[:,0]),axis=1);ratios=posedarea/np.maximum(restarea,1e-20)
  rows.append({'seam':s['name'],'bridgeTriangles':len(tri),'maximumEdgeStretch':float(stretch.max()),'edgeStretchP90P99':np.quantile(stretch,[.9,.99]).tolist(),'areaRatioMinimum':float(ratios.min()),'areaCollapsedBelow25Percent':int((ratios<.25).sum())})
 poseRows.append({'actualSample':row['i'],'jointTransformsSHA256':rec['sha256'],'seams':rows})
(OUT/'sewing-cpu-stress.json').write_text(json.dumps({'kind':'Unbuilt seam proposal stress using four retained actual34physics sample joint matrices','sourceSHA256':sha(raw),'fit04SHA256':sha(fr),'jointSourceManifestSHA256':sha(manifestPath.read_bytes()),'rows':poseRows,'limits':['No moving GPU appearance, normals, texture seam, selfintersection or contact acceptance.','Seam endpoint weights are current native/source fields; source glove and sole anatomy untouched.','CPU test informs sewing refinement; no reweighted mesh or complete asset created.']},indent=2)+'\n')
# Neck team owns collar/hood detail. Keep this audit to cuffs/shoes and compact literal arrays.
report['interfaces'].pop('hood');report['interfaces']['body']['loops']=[r for r in report['interfaces']['body']['loops'] if r['center'][1]<1]
report['sourcePositionTouch'].pop('hood')
for path in OUT.glob('*.json'):
 data=report if path.name=='boundaries.json' else json.loads(path.read_bytes());path.write_text(json.dumps(data,separators=(',',':'))+'\n')
print('SOURCE_BYTES_UNCHANGED',SRC.read_bytes()==raw,FIT.read_bytes()==fr)
print('SEWING_ACTUAL_STRESS',json.dumps(poseRows))
consistency=[]
for name,item in [('body',pr[0]),('gloves',pr[1]),('native',native)]:
 p,iv,al,ww=physical(item);maximum=max(float(abs(item['W'][a]-ww[i]).max()) for i,a in enumerate(al));consistency.append({'scope':name,'physicalPositionAliasesMaximumComponentWeightDifference':maximum});assert maximum<1e-7
proposal=json.loads((OUT/'sewing-proposal.json').read_bytes());proposal['aliasWeightConsistency']=consistency
for seam in proposal['seams']:
 sourceItem=pr[seam['sourcePrimitive']];SP,iv,al,SW=physical(sourceItem);an=W[seam['nativeOrderedPhysicalIDs']].mean(0);bn=SW[seam['sourceOrderedPhysicalIDs']].mean(0)
 seam['nativeRingMeanWeights19']=an.tolist();seam['sourceRingMeanWeights19']=bn.tolist();seam['meanEndpointWeightL1Difference']=float(abs(an-bn).sum())
(OUT/'sewing-proposal.json').write_text(json.dumps(proposal,separators=(',',':'))+'\n')
