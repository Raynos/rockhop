"""Read frozen neck ancestry/relative attachment. No source writes or capture."""
import gzip,hashlib,json,struct
from collections import defaultdict
from pathlib import Path
import numpy as np
out=Path(__file__).resolve().parent;qa=out.parent;prepared=json.loads((qa/'body58/preparation.json').read_text())
def sha(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
 return h.hexdigest()
for path,pin in prepared['pins'].items():assert sha(path)==pin['sha256'],path
n=np.load(qa/'body52/native-fields.npz');e=np.load(qa/'body52/export-fields.npz');names=n['boneNames'].tolist();norm=lambda s:s.replace('.','').replace('_','');order=[list(map(norm,names)).index(norm(s)) for s in e['jointNames']];joint_names=e['jointNames'].tolist();C=np.array([[1.,0,0,0],[0,0,1,0],[0,-1,0,0],[0,0,0,1]]);native_to_gltf=C[:3,:3];B=n['renderedBodyXYZ'];H=n['protectedHeadXYZ'];BT=n['renderedBodyTriangles'];HT=n['protectedHeadTriangles'];source_ids=n['renderedBodySourceIDs'].astype(int)
def stats(values):
 v=np.asarray(values);return {'minimum':float(v.min()),'median':float(np.median(v)),'p95':float(np.quantile(v,.95)),'maximum':float(v.max())}
def bounds(points):return [points.min(0).tolist(),points.max(0).tolist()]
def cyclic(tri):
 a,b,c=map(int,tri);return min((a,b,c),(b,c,a),(c,a,b))
def boundary(tris):
 edges=np.sort(np.concatenate([tris[:,[0,1]],tris[:,[1,2]],tris[:,[2,0]]]),axis=1);uniq,count=np.unique(edges,axis=0,return_counts=True);return uniq[count==1],uniq[count>2]
def loops(edges):
 adj=defaultdict(list)
 for a,b in edges:adj[int(a)].append(int(b));adj[int(b)].append(int(a))
 assert all(len(v)==2 for v in adj.values());seen=set();result=[]
 for seed in sorted(adj):
  if seed in seen:continue
  cycle=[seed];previous=-1;current=seed
  while True:
   nxt=next(v for v in sorted(adj[current]) if v!=previous)
   if nxt==seed:break
   assert nxt not in cycle;cycle.append(nxt);previous,current=current,nxt
  seen.update(cycle);result.append(np.array(cycle,dtype=int))
 assert len(seen)==len(adj);return result
be,bnon=boundary(BT);bloops=loops(be);assert len(be)==56 and len(bloops)==1 and not len(bnon);bid=bloops[0]
HP,alias=np.unique(H,axis=0,return_inverse=True);he,hnon=boundary(alias[HT]);hloops=loops(he);assert len(he)==524 and len(hloops)==6 and not len(hnon);low_loops=[x for x in hloops if HP[x,2].max()<1.54];assert len(low_loops)==2;hid=[np.array([np.flatnonzero(alias==v)[0] for v in cycle]) for cycle in low_loops];assert [len(x) for x in low_loops]==[183,190]
# Original donor ancestry is derived directly from frozen attributes/indices.
donor=Path(next(k for k,v in prepared['pins'].items() if v['sha256']=='b7f4f22790124c664f9907104e5b17b77775b4c5c995f715d62be640bbcc8754'));raw=donor.read_bytes();length=struct.unpack_from('<I',raw,12)[0];g=json.loads(raw[20:20+length]);binary=raw[28+length:]
def acc(index):
 a=g['accessors'][index];v=g['bufferViews'][a['bufferView']];size={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}[a['type']];dtype=np.dtype({5126:'<f4',5125:'<u4',5123:'<u2',5121:'<u1'}[a['componentType']]);assert 'sparse' not in a;return np.ndarray((a['count'],size),dtype=dtype,buffer=binary,offset=v.get('byteOffset',0)+a.get('byteOffset',0),strides=(v.get('byteStride',size*dtype.itemsize),dtype.itemsize)).copy()
p=g['meshes'][1]['primitives'][0];dp=acc(p['attributes']['POSITION']).astype(float);donor_native=dp@C[:3,:3];donor_native[:,0]-=.65;dt=acc(p['indices']).reshape(-1,3).astype(int);selected=np.flatnonzero(np.all(donor_native[dt,2]>=1.525,axis=1));used=np.unique(dt[selected]);inv=np.full(len(dp),-1);inv[used]=np.arange(len(used));assert np.array_equal(inv[dt[selected]],HT);assert np.array_equal(donor_native[used].astype('<f4').astype(float),H)
assembly=json.loads(Path(next(k for k in prepared['pins'] if k.endswith('appearance01/assembly.json'))).read_text());head_part=next(x for x in assembly['parts'] if x['name'].startswith('Protected textured head'));assert hashlib.sha256(used.astype('<u4').tobytes()).hexdigest()==head_part['sourceVertexIDsSHA256']
donor_joints=[g['nodes'][i]['name'] for i in g['skins'][0]['joints']];dj=acc(p['attributes']['JOINTS_0']).astype(int);dw=acc(p['attributes']['WEIGHTS_0']);dweights=np.zeros_like(n['protectedHeadWeights'])
for slot in range(4):
 for joint in np.unique(dj[used,slot]):
  own=list(map(norm,names)).index(norm(donor_joints[joint]));mask=dj[used,slot]==joint;dweights[mask,own]=dw[used[mask],slot]
assert np.array_equal(dweights,n['protectedHeadWeights'])
full=n['canonicalFourXYZ'];ft=n['canonicalFourTriangles'];body_faces=np.flatnonzero(np.all(full[ft,2]<=1.54,axis=1));assert np.array_equal(B,full[source_ids]);body_triangle_set={cyclic(x) for x in source_ids[BT]};candidate_set={cyclic(x) for x in ft[body_faces]};assert body_triangle_set.issubset(candidate_set);extra_omitted=np.array([i for i in body_faces if cyclic(ft[i]) not in body_triangle_set]);assert len(extra_omitted)==4;assert set(source_ids)==set(np.flatnonzero(full[:,2]<=1.54))
# Point/triangle closest point uses face projection plus each bounded edge.
def closest(point,triangles):
 a,b,c=triangles[:,0],triangles[:,1],triangles[:,2];ab=b-a;ac=c-a;ap=point-a;aa=np.einsum('ij,ij->i',ab,ab);bb=np.einsum('ij,ij->i',ab,ac);cc=np.einsum('ij,ij->i',ac,ac);dd=np.einsum('ij,ij->i',ap,ab);ee=np.einsum('ij,ij->i',ap,ac);den=aa*cc-bb*bb;valid=den>1e-24;u=np.divide(cc*dd-bb*ee,den,out=np.zeros_like(den),where=valid);v=np.divide(aa*ee-bb*dd,den,out=np.zeros_like(den),where=valid);inside=valid&(u>=0)&(v>=0)&(u+v<=1);q=a+u[:,None]*ab+v[:,None]*ac;dist=np.where(inside,np.einsum('ij,ij->i',q-point,q-point),np.inf);bary=np.column_stack([1-u-v,u,v])
 for i,j in [(0,1),(1,2),(2,0)]:
  start=triangles[:,i];edge=triangles[:,j]-start;l2=np.einsum('ij,ij->i',edge,edge);t=np.divide(np.einsum('ij,ij->i',point-start,edge),l2,out=np.zeros_like(l2),where=l2>0).clip(0,1);qedge=start+t[:,None]*edge;d=np.einsum('ij,ij->i',qedge-point,qedge-point);mask=d<dist;dist[mask]=d[mask];q[mask]=qedge[mask];bary[mask]=0;bary[mask,i]=1-t[mask];bary[mask,j]=t[mask]
 index=int(np.argmin(dist));return index,bary[index],q[index],float(np.sqrt(dist[index]))
rest={};weights={}
for label in ['renderedBody','protectedHead','canonicalFour','originalFull','cheek']:
 xyz=n[label+'XYZ'];rest[label]=np.column_stack([xyz,np.ones(len(xyz))])@(C@n[label+'World']).T;w=n[label+'Weights'][:,order].copy();w/=w.sum(1)[:,None];weights[label]=w
body_rest=rest['renderedBody'][:,:3];head_rest=rest['protectedHead'][:,:3];correspondences=[]
for b in bid:
 h,bc,point,distance=closest(body_rest[b],head_rest[HT]);correspondences.append({'bodyNativeVertex':int(b),'fullBodySourceVertex':int(source_ids[b]),'headNativeTriangle':h,'headNativeVertices':HT[h].tolist(),'headBarycentric':bc.tolist(),'bodyRestGLTFXYZ':body_rest[b].tolist(),'headRestClosestGLTFXYZ':point.tolist(),'restDistanceM':distance})
hpairs=np.array([x['headNativeTriangle'] for x in correspondences]);hbary=np.array([x['headBarycentric'] for x in correspondences]);hp=np.einsum('vi,vij->vj',hbary,head_rest[HT[hpairs]]);hweights=np.einsum('vi,vij->vj',hbary,weights['protectedHead'][HT[hpairs]]);bweights=weights['renderedBody'][bid];gap0=body_rest[bid]-hp
body_moment=bweights[:,:,None]*rest['renderedBody'][bid,None,:];head_moment=np.einsum('vi,vij,vik->vjk',hbary,weights['protectedHead'][HT[hpairs]],rest['protectedHead'][HT[hpairs]]);moments=body_moment-head_moment;neck=joint_names.index('neck');head=joint_names.index('head')
base=Path(next(k for k in prepared['pins'] if k.endswith('diagnostic02/driver.json'))).parent;driver=json.loads((base/'driver.json').read_text());stream={d:np.memmap(base/('body-native-'+d+'.f64'),dtype='<f8',mode='r',shape=(529,13380,3)) for d in ['full','four']}
with gzip.open(qa/'garment47/first.weights.ndjson.gz','rt') as f:actual=[json.loads(line) for line in f]
def skin(label,K):return np.einsum('vj,jab,vb->va',weights[label],K,rest[label],optimize=True)[:,:3]
def fields(domain,index,weight):
 if domain=='native':
  W=np.array([np.array(driver['frames'][index]['jointWorldColumnMajor'][names[j]]).reshape(4,4).T for j in order]);K=W@e['inverseBinds'];body=stream[weight][index][source_ids]
 else:
  K=np.array(actual[index-1]['matrices']).reshape(51,4,4).transpose(0,2,1);body=skin('originalFull' if weight=='full' else 'canonicalFour',K)[source_ids]
 return body,skin('protectedHead',K),K
# Canonical rest is not riding tick0. Only already archived sample identities.
samples=[];witness_npz={};targets={'native':[0,72,96,144,192,216,240,242,264,528],'actual47':[4,478,512,514,591,668,669,703]}
for domain,indices in targets.items():
 for index in indices:
  fields_by_weight={d:fields(domain,index,d) for d in ['full','four']};body,headpos,K=fields_by_weight['four'];pairs=np.einsum('vi,vij->vj',hbary,headpos[HT[hpairs]]);gap=body[bid]-pairs;reference=gap0@K[neck,:3,:3].T;drift=gap-reference;contribution=np.einsum('jab,vjb->vja',K-K[neck],moments)[:,:,:3];assert np.abs(contribution.sum(1)-drift).max()<2e-6
  full_body=fields_by_weight['full'][0];delta=np.linalg.norm(full_body[bid]-body[bid],axis=1);worst=int(np.argmax(np.linalg.norm(drift,axis=1)));sample={'domain':domain,'sourceIndex':index,'sourceTimeS':driver['frames'][index]['timeS'] if domain=='native' else index/120,'fixedRestBodyToHeadTriangleGapM':stats(np.linalg.norm(gap,axis=1)),'attachmentDriftFromRigidNeckReferenceM':stats(np.linalg.norm(drift,axis=1)),'fullFourBodyCutLoopLossM':stats(delta),'worstFixedPair':{'correspondence':correspondences[worst],'gapGLTFXYZM':gap[worst].tolist(),'driftGLTFXYZM':drift[worst].tolist(),'jointContributionGLTFXYZM':{joint_names[j]:contribution[worst,j].tolist() for j in range(51) if np.linalg.norm(contribution[worst,j])>1e-8}},'headRelativeNeckK':(np.linalg.inv(K[neck])@K[head]).tolist(),'neckReferenceLinearSingularValues':np.linalg.svd(K[neck,:3,:3],compute_uv=False).tolist(),'attachmentDecompositionMaxAbsResidualM':float(np.abs(contribution.sum(1)-drift).max()),'fourBodyManualStreamParityM':float(np.linalg.norm(skin('renderedBody',K)[bid]-body[bid],axis=1).max())};assert sample['fourBodyManualStreamParityM']<2e-6;samples.append(sample);witness_npz[domain+str(index)+'BodyLoopGLTFXYZ']=body[bid];witness_npz[domain+str(index)+'HeadClosestRestCorrespondenceGLTFXYZ']=pairs
# Spatially correlate the distinct garment/head witnesses without causal merging.
contacts=json.loads(Path(next(k for k in prepared['pins'] if k.endswith('rest-head94/contacts.json'))).read_text());flat=contacts['variants']['flat'];garment_rows=flat['allPairs'];garment_triangles=sorted({row['headTriangle'] for row in garment_rows});garment_error=max(float(np.abs(H[HT[row['headTriangle']]]-np.array(row['headTriangleNativeXYZ'])).max()) for row in garment_rows);assert garment_error<2e-7
# Express existing low rims in the same neck reference; no new skin field.
loop_frame_rows=[]
for domain,indices in targets.items():
 for index in indices:
  body,headpos,K=fields(domain,index,'four');Ki=np.linalg.inv(K[neck]);parts=[]
  for number,ids in enumerate(hid):
   in_neck=(np.column_stack([headpos[ids],np.ones(len(ids))])@Ki.T)[:,:3];difference=in_neck-head_rest[ids];native_neck=in_neck@C[:3,:3];parts.append({'loop':number,'vertices':len(ids),'displacementInNeckRestFrameM':stats(np.linalg.norm(difference,axis=1)),'restNativeHeightRangeM':[float(H[ids,2].min()),float(H[ids,2].max())],'posedInNeckRestFrameNativeHeightRangeM':[float(native_neck[:,2].min()),float(native_neck[:,2].max())],'worstNativeVertex':int(ids[np.argmax(np.linalg.norm(difference,axis=1))]),'worstWeightByJoint':{joint_names[j]:float(weights['protectedHead'][ids[np.argmax(np.linalg.norm(difference,axis=1))],j]) for j in range(51) if weights['protectedHead'][ids[np.argmax(np.linalg.norm(difference,axis=1))],j]>0}})
  loop_frame_rows.append({'domain':domain,'sourceIndex':index,'headLowerLoopIntrinsicRelativeAttachment':parts})
# Original donor bone node hierarchy versus the own canonical rest frames.
parents={child:i for i,node in enumerate(g['nodes']) for child in node.get('children',[])};worlds={}
def node_world(i):
 if i in worlds:return worlds[i]
 node=g['nodes'][i]
 if 'matrix' in node:m=np.array(node['matrix']).reshape(4,4).T
 else:
  x,y,z,w=node.get('rotation',[0,0,0,1]);r=np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],[2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],[2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]]);m=np.eye(4);m[:3,:3]=r@np.diag(node.get('scale',[1,1,1]));m[:3,3]=node.get('translation',[0,0,0])
 worlds[i]=(node_world(parents[i]) if i in parents else np.eye(4))@m;return worlds[i]
pivots={}
for role in ['chest','neck','head']:
 di=list(map(norm,donor_joints)).index(norm(role));old=node_world(g['skins'][0]['joints'][di]);own=e['jointRestWorld'][joint_names.index(role)];pivots[role]={'donorRestGLTFWorldRows':old.tolist(),'ownRestGLTFWorldRows':own.tolist(),'originDifferenceM':float(np.linalg.norm(old[:3,3]-own[:3,3])),'ownFromDonorRestRows':(own@np.linalg.inv(old)).tolist()}
head_low_weights={str(i):{'meanWeights':{joint_names[j]:float(weights['protectedHead'][ids,j].mean()) for j in range(51) if weights['protectedHead'][ids,j].max()>0},'weightRanges':{joint_names[j]:[float(weights['protectedHead'][ids,j].min()),float(weights['protectedHead'][ids,j].max())] for j in range(51) if weights['protectedHead'][ids,j].max()>0}} for i,ids in enumerate(hid)}
margin_htri=np.flatnonzero(np.max(H[HT,2],axis=1)<=1.60);margin_hids=np.unique(HT[margin_htri]);aliases_low=[np.flatnonzero(np.isin(alias,cycle)) for cycle in low_loops]
# Two indexed rings around the body cut are a proposal margin, not an edit.
body_margin=set(map(int,bid))
for _ in range(2):
 incident=np.any(np.isin(BT,list(body_margin)),axis=1);body_margin.update(map(int,BT[incident].ravel()))
body_margin=np.array(sorted(body_margin));body_margin_faces=np.flatnonzero(np.any(np.isin(BT,body_margin),axis=1));restore_band=np.flatnonzero((full[:,2]>1.54)&(full[:,2]<=1.60));restoration_faces=np.flatnonzero(np.any(np.isin(ft,restore_band),axis=1));head_seed=np.unique(np.concatenate(aliases_low));head_patch=set(map(int,head_seed))
for _ in range(2):
 incident=np.any(np.isin(HT,list(head_patch)),axis=1);head_patch.update(map(int,HT[incident].ravel()))
head_patch=np.array(sorted(head_patch));head_patch_faces=np.flatnonzero(np.any(np.isin(HT,head_patch),axis=1));oriented=np.concatenate([alias[HT][:,[0,1]],alias[HT][:,[1,2]],alias[HT][:,[2,0]]]);edge_to_direction={tuple(sorted(map(int,x))):tuple(map(int,x)) for x in oriented};head_cut_orientation=[]
for cycle in low_loops:
 points=HP[cycle];vector=.5*np.cross(points,np.roll(points,-1,axis=0)).sum(0);first=(int(cycle[0]),int(cycle[1]));vector*=1 if edge_to_direction[tuple(sorted(first))]==first else -1;head_cut_orientation.append(vector.tolist())
report={'status':'UNACCEPTED_READ_ONLY_NECK_INTERFACE_ANCESTRY_AND_ATTACHMENT_DIAGNOSIS','creationDate':'2026-10-04','preparationSHA256':sha(qa/'body58/preparation.json'),'recipeSHA256':sha(__file__),'headAncestry':{'currentNative43707Vertices71826TrianglesExactDonorSlice':True,'sourceDonorSHA256':sha(donor),'donorMesh':1,'donorPrimitive':0,'selectedOriginalVertexIDsSHA256':hashlib.sha256(used.astype('<u4').tobytes()).hexdigest(),'nativeOriginalWeightsExactSemanticRebind':True,'nativeGeometryFloat32Exact':True,'nativeOrientedTrianglesExact':True,'exportOrientedHeadAncestryStillUnproven':True,'sourceGeometryChoice':'Original file-world donor head/bust fragment; not registered to canonical hm08 rest geometry. No shared body/head vertex ancestry.'},'bodyAncestry':{'full13380BodyHeadRetainedAsControl':True,'current9037VerticesExactHeightVertexCut':True,'current18016TrianglesExactOrientedSourceSubset':True,'extraOmittedTriangleIDsBeyondTriangleHeightPredicate':extra_omitted.tolist(),'extraOmittedTriangleVertexIDs':ft[extra_omitted].tolist(),'extraOmittedInterpretation':'All current triangles belong to the original. Whole-polygon vertex deletion can additionally remove4retained triangle ears from crossing quads; original polygon ancestry not reconstructed here.','removedSourceVertices':int(len(full)-len(B)),'cutNativeHeightM':1.54,'boundarySourceIDs':source_ids[bid].tolist(),'boundaryLocalNativeIDs':bid.tolist(),'boundaryNativeBounds':bounds(B[bid]),'boundaryWidthM':float(np.ptp(B[bid,1])),'boundaryEdges':56},'headBoundary':{'rawIndexBoundaryEdges':len(boundary(HT)[0]),'virtualExactPositionBoundaryEdges':524,'virtualBoundaryCycles':6,'physicalWeldingOrCommonSewnInterfaceNotInferred':True,'lowerCutOrientedAreaVectorsNativeM2':head_cut_orientation,'lowerCutLoops':[{'virtualVertices':len(cycle),'nativeVertexAliases':aliases_low[i].tolist(),'representativeNativeVertexIDs':hid[i].tolist(),'boundsNative':bounds(HP[cycle]),'widthM':float(np.ptp(HP[cycle,1]))} for i,cycle in enumerate(low_loops)]},'restPairCorrespondence':{'method':'Each actual body cut-loop vertex to closest point on ALL current head triangles, fixed at canonical rest. Bidirectional seam sewing is absent; this nearest relation is a numeric reference, not material or anatomical correspondence.','restDistanceM':stats([x['restDistanceM'] for x in correspondences]),'bodyVsHeadInterpolatedWeightL1':stats(np.abs(bweights-hweights).sum(1)),'bodyCutLoopMeanJointWeights':{joint_names[j]:float(bweights[:,j].mean()) for j in range(51) if bweights[:,j].max()>0},'matchedHeadMeanJointWeights':{joint_names[j]:float(hweights[:,j].mean()) for j in range(51) if hweights[:,j].max()>0},'correspondences':correspondences},'samples':samples,'headLowerLoopRelativeAttachment':loop_frame_rows,'headLowerLoopWeights':head_low_weights,'donorVsOwnRestBoneFrames':pivots,'commonCurrentObjectFrame':{'bodyWorldRows':n['renderedBodyWorld'].tolist(),'headWorldRows':n['protectedHeadWorld'].tolist(),'maximumObjectWorldComponentDifference':float(np.abs(n['renderedBodyWorld']-n['protectedHeadWorld']).max()),'bothUseSameOwn51InverseBindMatrices':True,'noAddedSourceX0_65AppliedTwice':True},'relativeAttachmentMethod':'Existing paired fields minus rigid neck rotation of the rest difference. Drift=sum_j (K_j-K_neck)*(body weighted homogeneous moment - fixed head barycentric weighted moment). This decomposes existing skinning, creates no replacement weights/pose/geometry. Individual contributions can cancel; magnitudes must not be summed as penetration.','garmentHeadCorrelation':{'rest94ContactsSHA256':sha(Path(next(k for k in prepared['pins'] if k.endswith('rest-head94/contacts.json')))),'distinctMethodAndCause':True,'headTriangles':garment_triangles,'headTriangleCoordinateMaxResidualToCurrentNativeM':garment_error,'allContactHeadTrianglesInsideProposedLowHeadProxy':set(garment_triangles).issubset(set(margin_htri)),'intersectionPointBoundsNative':flat['intersectionPointNativeXYZBounds'],'interpretation':'Preexisting rear-neck/lower-head garment contact is spatially in the lower-head proxy. It does not establish that the visible flange shares the same surface pixels or cause. No alpha/culling/depth/contact waiver.'},'proposedMargin':{'headNativeTrianglesAllCornersAtOrBelow1_60M':margin_htri.tolist(),'headNativeVertices':margin_hids.tolist(),'bodyRenderedNativeVerticesWithinTwoGraphRings':body_margin.tolist(),'bodyFullSourceVertices':source_ids[body_margin].tolist(),'originalCanonicalNeckRestoreBandSourceVertices1_54To1_60M':restore_band.tolist(),'originalCanonicalTrianglesIncidentToRestoreBand':restoration_faces.tolist(),'headBoundaryLedTwoRingNativeVertices':head_patch.tolist(),'headBoundaryLedTwoRingNativeTriangles':head_patch_faces.tolist(),'bodyRenderedTrianglesIncidentToMargin':body_margin_faces.tolist(),'unmodifiedFaceAndCheekProtected':'All head/cheek outside the explicitly admitted lower-neck transition; no head-face/UV/image deletion or global transform/bind/weight change. Proxy1.60m needs anatomical/parent review, not automatic permission.'},'limits':['All source bytes,body/head/original51bind/weights and body56/PDF53 controls remain unchanged. QA proposed scope only, no capture/repair/new controller/inference/installation/publication/delivery.','Only listed existing native and actual47 field samples; actual50 never synchronized. No complete repaired-motion/device/player acceptance.','Nearest rest correspondence and virtual exact-position aliasing do not prove a sewn surface, physical head watertightness or signed penetration.','Root severe visual verdict is authoritative; separate pixel-ownership.json traces existing played witnesses without a new render. Parent decides repair/acceptance; all M0-M5 open.']}
np.savez_compressed(out/'neck-witnesses.npz',bodyLoopNativeIDs=bid,bodyLoopFullSourceIDs=source_ids[bid],headTriangleIDs=hpairs,headBarycentric=hbary,bodyRestGLTFXYZ=body_rest[bid],headRestClosestGLTFXYZ=hp,bodyJointWeights=bweights,headInterpolatedJointWeights=hweights,headOriginalDonorVertexIDs=used,headOriginalDonorTriangleIDs=selected,**witness_npz);report['witnessNPZ_SHA256']=sha(out/'neck-witnesses.npz')
for path,pin in prepared['pins'].items():assert sha(path)==pin['sha256'],path
(out/'assessment.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'headAncestry':report['headAncestry'],'bodyCutBounds':report['bodyAncestry']['boundaryNativeBounds'],'restPairDistance':report['restPairCorrespondence']['restDistanceM'],'selectedSamples':[{k:s[k] for k in ['domain','sourceIndex','attachmentDriftFromRigidNeckReferenceM','fullFourBodyCutLoopLossM']} for s in samples],'headBoundaryLoops':[(len(x),bounds(HP[x])) for x in low_loops],'garmentHeadCoordinateResidual':garment_error},indent=2))
