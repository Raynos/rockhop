"""One bounded clean-native cuff transition + literal shoe bridges. CPU only.
All source glove/shoe attributes and hand/sole probe vertices remain exact.
No radius/weight sweep, source fused weights edited, Blender/rendering or promotion.
"""
from pathlib import Path
import hashlib,json,struct,argparse
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import dijkstra
REPO=Path('/Users/raynos/projects/games/rockhop');ROOT=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2');OUT=REPO/'docs/evidence/hero-remaster/one-rider-v2/garment-rebuild01/cuff-ankle-transition155';RUN=ROOT/'garment-rebuild01/cuff-ankle-transition155'
parser=argparse.ArgumentParser();parser.add_argument('--output-dir',type=Path);parser.add_argument('--evidence-dir',type=Path);args=parser.parse_args();assert (args.output_dir is None)==(args.evidence_dir is None),'Use both owned reproduction directories together'
if args.output_dir is not None:RUN=args.output_dir;OUT=args.evidence_dir
OUT.mkdir(parents=True,exist_ok=True);RUN.mkdir(parents=True,exist_ok=True)
sha=lambda b:hashlib.sha256(b).hexdigest();source=ROOT/'rig-adapter01/body-bind34/rider.glb';fit=ROOT/'garment-rebuild01/cage04/fit04.npz';sourceBytes=source.read_bytes();fitBytes=fit.read_bytes();n=struct.unpack_from('<I',sourceBytes,12)[0];doc=json.loads(sourceBytes[20:20+n]);blob=sourceBytes[28+n:]
proposalPath=REPO/'docs/evidence/hero-remaster/one-rider-v2/garment-rebuild01/cuff-sole-audit154/sewing-proposal.json';proposal=json.loads(proposalPath.read_bytes());assert proposal['sourceSHA256']==sha(sourceBytes) and proposal['fit04SHA256']==sha(fitBytes)
def acc(i):
 a=doc['accessors'][i];v=doc['bufferViews'][a['bufferView']];assert 'sparse' not in a and 'byteStride' not in v;d={5121:'u1',5123:'<u2',5125:'<u4',5126:'<f4'}[a['componentType']];w={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a['type']]
 return np.frombuffer(blob,dtype=d,count=a['count']*w,offset=v.get('byteOffset',0)+a.get('byteOffset',0)).reshape(a['count'],w).copy()
names=[doc['nodes'][i]['name'] for i in doc['skins'][0]['joints']];assert len(names)==19
pr=[]
for p in doc['meshes'][0]['primitives'][:2]:
 a=p['attributes'];r={k:acc(a[k]) for k in ['POSITION','NORMAL','TEXCOORD_0','JOINTS_0','WEIGHTS_0']};r['triangles']=acc(p['indices']).reshape(-1,3);W=np.zeros((len(r['POSITION']),19))
 for lane in range(4):np.add.at(W,(np.arange(len(W)),r['JOINTS_0'][:,lane]),r['WEIGHTS_0'][:,lane])
 r['weights19']=W;r['physical'],r['inverse']=np.unique(r['POSITION'],axis=0,return_inverse=True);r['firstAliases']=np.array([np.flatnonzero(r['inverse']==i)[0] for i in range(len(r['physical']))]);pr.append(r)
f=np.load(fit);P=f['positions'];oldW=f['weights'];W=oldW.copy();Q=f['quads'];UV=f['uvLoops'].reshape(len(Q),4,2);physical,inv=np.unique(P,axis=0,return_inverse=True);first=np.array([np.flatnonzero(inv==i)[0] for i in range(len(physical))]);assert len(physical)==len(P)
removed=np.unique(np.concatenate([s['nativeRemovedQuadIDs'] for s in proposal['seams']]));keep=np.ones(len(Q),bool);keep[removed]=False;retainedQ=Q[keep];edges=np.unique(np.sort(np.concatenate([retainedQ[:,[i,(i+1)%4]] for i in range(4)]),axis=1),axis=0);length=np.linalg.norm(P[edges[:,0]]-P[edges[:,1]],axis=1);graph=coo_matrix((np.r_[length,length],(np.r_[edges[:,0],edges[:,1]],np.r_[edges[:,1],edges[:,0]])),shape=(len(P),len(P))).tocsr();fields=[]
# One declared anatomical span, spanning lower forearm beyond the cut boundary.
SPAN=.18
for seam in proposal['seams']:
 if not seam['name'].startswith('cuff.'):continue
 side=seam['name'].split('.')[-1];ids=np.array(seam['nativeOrderedVertexIDs']);dist=dijkstra(graph,directed=False,indices=ids,min_only=True);u=np.clip(1-dist/SPAN,0,1);alpha=u*u*u*(u*(u*6-15)+10);target=np.zeros(19);target[names.index('hand.'+side)]=1
 assert np.array_equal(pr[1]['weights19'][pr[1]['firstAliases'][seam['sourceOrderedPhysicalIDs']]],np.tile(target,(len(seam['sourceOrderedPhysicalIDs']),1)))
 W=(1-alpha[:,None])*W+alpha[:,None]*target;fields.append({'side':side,'distance':dist,'alpha':alpha,'ids':np.flatnonzero(alpha>0),'boundary':ids});assert np.allclose(W[ids],target,atol=1e-14)
assert np.allclose(W.sum(1),1,atol=1e-12)
tri=np.concatenate([retainedQ[:,[0,1,2]],retainedQ[:,[0,2,3]]]);cross=np.cross(P[tri[:,1]]-P[tri[:,0]],P[tri[:,2]]-P[tri[:,0]]);N=np.zeros_like(P)
for lane in range(3):np.add.at(N,tri[:,lane],cross)
N/=np.maximum(np.linalg.norm(N,axis=1,keepdims=True),1e-20)
# Bridge endpoints carry separate UV/normal records, shared exact physical skin.
bridgeP=[];bridgeW=[];bridgeN=[];bridgeUV=[];bridgeRef=[];bridgeT=[];bridgeRows=[]
for si,seam in enumerate(proposal['seams']):
 sourceItem=pr[seam['sourcePrimitive']];sourceOrder=seam['sourceOrderedPhysicalIDs'];phase=seam['cyclicPhase'];sourceOrder=sourceOrder[phase:]+sourceOrder[:phase];nativeOrder=seam['nativeOrderedPhysicalIDs'];nativeVertexOrder=[int(first[i]) for i in nativeOrder]
 maps=[]
 for ns,order in [(0,nativeOrder),(1,sourceOrder)]:
  pts=physical[order] if ns==0 else sourceItem['physical'][order];arc=np.r_[0,np.cumsum(np.linalg.norm(pts-np.roll(pts,1,axis=0),axis=1)[1:])];perimeter=float(np.linalg.norm(pts-np.roll(pts,-1,axis=0),axis=1).sum());umap={int(i):float(v/perimeter) for i,v in zip(order,arc)};maps.append(umap)
 begin=len(bridgeT)
 # Duplicate first endpoint at the UV seam as needed; positions/weights exact.
 for triangle in seam['bridgeTrianglesPhysicalNamespace']:
  face=[];us=[maps[0 if ns=='native' else 1][i] for ns,i in triangle];wrap=max(us)-min(us)>.5
  for (ns,i),u in zip(triangle,us):
   alias=int(first[i]) if ns=='native' else int(sourceItem['firstAliases'][i]);point=P[alias] if ns=='native' else sourceItem['POSITION'][alias];weights=W[alias] if ns=='native' else sourceItem['weights19'][alias];normal=N[alias] if ns=='native' else sourceItem['NORMAL'][alias]
   idx=len(bridgeP);face.append(idx);bridgeP.append(point);bridgeW.append(weights);bridgeN.append(normal);bridgeUV.append([u+1 if wrap and u<.5 else u,0 if ns=='native' else 1]);bridgeRef.append([0 if ns=='native' else 1+seam['sourcePrimitive'],alias,si])
  bridgeT.append(face)
 bridgeRows.append({'name':seam['name'],'triangleRange':[begin,len(bridgeT)],'triangles':len(bridgeT)-begin,'nativeBoundaryVertexIDs':nativeVertexOrder,'sourcePrimitive':seam['sourcePrimitive'],'sourceBoundaryVertexIDs':sourceItem['firstAliases'][sourceOrder].tolist(),'material':'new local transition atlas;source/native original texture records preserved independently','newGeometryPositions':'Endpoint duplicates only; no rest edge shortening, no new in-between shape.','weightRule':'native cuff endpoints100%hand; source endpoint weights untouched; broader clean sleeve geodesic quintic field upstream. Ankles keep original native/source fields.'})
BP=np.array(bridgeP);BW=np.array(bridgeW);BN=np.array(bridgeN);BUV=np.array(bridgeUV);BT=np.array(bridgeT);BR=np.array(bridgeRef);changed=np.flatnonzero(np.any(W!=oldW,axis=1));arrays={'native_positions':P,'native_weights19_before':oldW,'native_weights19':W,'native_normals':N,'native_original_quads':Q,'native_retained_quads':retainedQ,'native_retained_quad_ids':np.flatnonzero(keep),'native_removed_quad_ids':removed,'native_uvLoops':UV,'native_retained_uvLoops':UV[keep],'native_modified_weight_vertex_ids':changed,'bridge_positions':BP,'bridge_weights19':BW,'bridge_normals':BN,'bridge_uv':BUV,'bridge_triangles':BT,'bridge_endpoint_reference':BR,'canonical19':np.array(names)}
for i,r in enumerate(pr):
 for key in ['POSITION','NORMAL','TEXCOORD_0','JOINTS_0','WEIGHTS_0','triangles','weights19']:arrays[f'source{i}_{key}']=r[key]
shoeMask=np.all(pr[0]['POSITION'][pr[0]['triangles'],1]<.2,axis=1);arrays['source0_shoe_patch_triangle_ids']=np.flatnonzero(shoeMask)
for field in fields:arrays['native_cuff_'+field['side']+'_geodesic_distance']=field['distance'];arrays['native_cuff_'+field['side']+'_blend_alpha']=field['alpha']
path=RUN/'transition155.npz';assert not path.exists(),'Retain this single frozen attempt; do not sweep/overwrite';np.savez_compressed(path,**arrays)
def unit(a):return a/np.maximum(np.linalg.norm(a,axis=-1,keepdims=True),1e-20)
def measure(pos,weight,faces,M,normals=None):
 q=pos[faces];posed=np.einsum('vj,jab,vb->va',weight,M[:,:3,:],np.c_[pos,np.ones(len(pos))]);p=posed[faces];re=np.linalg.norm(q-np.roll(q,-1,axis=1),axis=2);pe=np.linalg.norm(p-np.roll(p,-1,axis=1),axis=2);stretch=pe/np.maximum(re,1e-20);rc=np.cross(q[:,1]-q[:,0],q[:,2]-q[:,0]);pc=np.cross(p[:,1]-p[:,0],p[:,2]-p[:,0]);area=np.linalg.norm(pc,axis=1)/np.maximum(np.linalg.norm(rc,axis=1),1e-20);result={'triangles':len(faces),'maximumEdgeStretch':float(stretch.max()),'edgeStretchP90P99':np.quantile(stretch,[.9,.99]).tolist(),'areaRatioMinimum':float(area.min()),'areaCollapsedBelow25Percent':int((area<.25).sum())}
 if normals is not None:
  skinned=unit(np.einsum('vj,jab,vb->va',weight,M[:,:3,:3],normals));restDots=np.einsum('ti,ti->t',unit(rc),unit(normals[faces].mean(1)));posedDots=np.einsum('ti,ti->t',unit(pc),unit(skinned[faces].mean(1)));result['normalOppositionFlags']=int(((restDots>.2)&(posedDots<-.2)).sum())
 return result
manifestPath=REPO/'docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/body-bind34/candidate-cpu/pose-manifest.json';manifest=json.loads(manifestPath.read_bytes());samples=[];roiPath=REPO/'docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/played-surfaces11/framed04/source-roi.json';roi=json.loads(roiPath.read_bytes());contactCopies=[]
for kind in ['hands','feet']:
 for e in roi[kind]:
  si=1 if kind=='hands' else 0;ids=np.array(e['sourceVertices']);s=pr[si];keys=['POSITION','NORMAL','TEXCOORD_0','JOINTS_0','WEIGHTS_0'];assert all(np.array_equal(arrays[f'source{si}_{k}'][ids],s[k][ids]) for k in keys)
  contactCopies.append({'kind':kind,'side':e['side'],'sourcePrimitive':si,'sourceVertexIDs':ids.tolist(),'count':len(ids),'allFiveRawAttributesExact':True,'fields':{k:sha(s[k][ids].tobytes()) for k in keys}})
for row in manifest['rows']:
 rec=row['dump'][0]['jointTransforms'];mr=(ROOT/'rig-adapter01/body-bind34/candidate-cpu'/rec['file']).read_bytes();assert sha(mr)==rec['sha256'];M=np.frombuffer(mr,dtype='<f8').reshape(-1,4,4).transpose(0,2,1);seamResults=[];nativeResults=[]
 for br in bridgeRows:
  start,end=br['triangleRange'];seamResults.append({'seam':br['name'],'before':measure(BP,np.array([oldW[i] if ns==0 else pr[ns-1]['weights19'][i] for ns,i,_ in BR]),BT[start:end],M,BN),'after':measure(BP,BW,BT[start:end],M,BN)})
 for field in fields:
  mask=(field['alpha'][tri]>0).any(1);nativeResults.append({'scope':'native upstream sleeve.'+field['side'],'trianglesLiteral':tri[mask].tolist(),'before':measure(P,oldW,tri[mask],M,N),'after':measure(P,W,tri[mask],M,N)})
 contacts=[]
 for probe in contactCopies:
  si=probe['sourcePrimitive'];ids=probe['sourceVertexIDs'];s=pr[si];before=np.einsum('vj,jab,vb->va',s['weights19'][ids],M[:,:3,:],np.c_[s['POSITION'][ids],np.ones(len(ids))]);after=np.einsum('vj,jab,vb->va',arrays[f'source{si}_weights19'][ids],M[:,:3,:],np.c_[arrays[f'source{si}_POSITION'][ids],np.ones(len(ids))]);assert np.array_equal(before,after);contacts.append({'kind':probe['kind'],'side':probe['side'],'maximumCPUPositionChangeMeters':float(np.linalg.norm(after-before,axis=1).max())})
 samples.append({'actualSample':row['i'],'jointTransformsSHA256':rec['sha256'],'seams':seamResults,'nativeSleeves':nativeResults,'protectedContactPositionChange':contacts})
report={'status':'One built cuff/ankle candidate; unaccepted CPU feasibility, parent judges actual full motion','sourceGLBSHA256':sha(sourceBytes),'sourceFit04SHA256':sha(fitBytes),'sourceSewingProposalSHA256':sha(proposalPath.read_bytes()),'artifact':str(path),'artifactSHA256':sha(path.read_bytes()),'canonical19':names,'nativePositionsExact':True,'nativeOriginalSourceWeightsStillArchived':True,'nativeChangedWeightVertexIDs':changed.tolist(),'nativeRemovedQuadIDs':removed.tolist(),'settings':{'singleAttempt':1,'transitionGeodesicSpanMeters':SPAN,'blend':'quintic smootherstep t^3(6t^2-15t+10), t=clip(1-distance/.18,0,1)','scope':'retained clean native topology only; geodesic distance from cut ring3, no source fused weights or contact geometry changed','cuffBoundary':'100%canonical side hand, matching protected source glove cuff exactly','ankles':'native source field untouched;source shoe patch untouched','sourceNormals':'all original attributes preserved; bridge endpoint normals copy selected exact alias, native endpoint normals recomputed from retained garment','UV':'new seam-local UV cylinder atlas, explicit source UV records unchanged; bake still required','geometry':'source and native positions exact; removed exactly3native quad strips per seam; old literal zipper and cyclic phase retained; no rest edge shortening'},'bridgeRows':bridgeRows,'sourceArrays':{f'source{i}_{k}':{'sha256':sha(arrays[f'source{i}_{k}'].tobytes()),'shape':list(arrays[f'source{i}_{k}'].shape),'dtype':str(arrays[f'source{i}_{k}'].dtype)} for i in range(2) for k in ['POSITION','NORMAL','TEXCOORD_0','JOINTS_0','WEIGHTS_0','triangles']},'protectedSourceContactROI_SHA256':sha(roiPath.read_bytes()),'protectedSourceContactCopies':contactCopies,'actualPoseManifestSHA256':sha(manifestPath.read_bytes()),'rows':samples,'limits':['No GPU or rendered appearance, normal continuity, intersections, Garage/seating/maximumlean or contact acceptance.','Source gloves/shoe triangles are exact; source0 full original body attrs included for source provenance but only explicit shoe_patch_triangle_ids may be retained in assembly.','Separate UV endpoints require compatible bake; raw source material/atlas still owned by originalGLB.','Endpoint aliases carry identical weights; a complete sewn mesh must weld physical boundaries across UV/normal aliases, not leave overlapping surfaces.']}
assert source.read_bytes()==sourceBytes and fit.read_bytes()==fitBytes
(OUT/'construction-report.json').write_text(json.dumps(report,separators=(',',':'))+'\n')
print(json.dumps([{'sample':s['actualSample'],'seams':[{'name':a['seam'],'before':a['before']['areaCollapsedBelow25Percent'],'after':a['after']['areaCollapsedBelow25Percent'],'stretch':a['after']['maximumEdgeStretch']} for a in s['seams']],'sleeves':[{'scope':a['scope'],'beforeCollapse':a['before']['areaCollapsedBelow25Percent'],'afterCollapse':a['after']['areaCollapsedBelow25Percent'],'beforeFlags':a['before']['normalOppositionFlags'],'afterFlags':a['after']['normalOppositionFlags'],'beforeStretch':a['before']['maximumEdgeStretch'],'afterStretch':a['after']['maximumEdgeStretch']} for a in s['nativeSleeves']]} for s in samples],indent=2))
