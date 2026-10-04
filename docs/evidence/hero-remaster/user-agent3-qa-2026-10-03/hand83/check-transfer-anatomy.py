"""Read-only nearest-donor ancestry and one declared anatomical section."""
import bpy,numpy as np,json,hashlib
from pathlib import Path
from mathutils.bvhtree import BVHTree
from mathutils import Vector
out=Path(__file__).resolve().parent;qa=out.parent;root=Path.cwd();ev=root/'docs/evidence/hero-remaster/anatomical-foundation-2026-10-03/user-agent1';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();prep=json.loads((qa/'hand82/preparation.json').read_text());n=np.load(ev/'hand-grip104/source-fields.npz');f=np.load(ev/'hand-grip106/candidate-fields.npz');scope=json.loads((ev/'hand-grip104/scope.json').read_text());names=n['boneNames'].tolist();P=n['gloveXYZ'].astype(float);T=n['gloveTriangles'];body=n['bodyXYZ'].astype(float);BT=n['bodyTriangles'];BW=n['bodyWeights'].astype(float);old=n['gloveWeights'];allowed=[names.index(s) for s in scope['scope']['weightBoneNames']];outside=np.setdiff1d(np.arange(51),allowed);a=f['bodyTriangleAncestry'];b=f['bodyBarycentrics'];sample=np.array([b[i]@BW[BT[a[i]]] for i in range(len(P))]);pred=old.astype(float).copy();fallback=[]
for i in range(len(P)):
 row=b[i]@BW[BT[a[i]]][:,allowed];mass=float(old[i,allowed].sum())
 if row.sum()>0:pred[i,allowed]=row/row.sum()*mass
 else:fallback.append(i)
pred=pred.astype(np.float32);assert np.array_equal(pred,f['fullWeights']);four=pred.copy();removed=[]
for i,row in enumerate(pred):
 fixed=int((row[outside]>0).sum());slots=4-fixed;ids=sorted((j for j in allowed if row[j]>0),key=lambda j:(-row[j],j));keep=ids[:slots];drop=ids[slots:];removed.append(float(row[drop].sum()));four[i,allowed]=0
 if keep:four[i,keep]=row[keep]*(float(row[allowed].sum())/float(row[keep].sum()))
assert np.array_equal(four,f['fourWeights']) and np.array_equal(np.array(removed),f['removedMass']);assert np.array_equal(pred[:,outside],old[:,outside]);tree=BVHTree.FromPolygons(body.tolist(),BT.tolist(),all_triangles=True,epsilon=0.);gTree=BVHTree.FromPolygons(P.tolist(),T.tolist(),all_triangles=True,epsilon=0.);sameTI=0;nearestGap=0.;distanceGap=0.;ties=[]
for i,p in enumerate(P):
 q,no,ti,dist=tree.find_nearest(Vector(p));sameTI+=int(ti==a[i]);archq=b[i]@body[BT[a[i]]];nearestGap=max(nearestGap,float(np.linalg.norm(np.array(q)-archq)));distanceGap=max(distanceGap,abs(float(dist)-f['bodyDistanceM'][i]))
 if ti!=a[i]:ties.append({'gloveNativeID':i,'archivedBodyTriangleID':int(a[i]),'independentBodyTriangleID':int(ti),'archivedVsIndependentNearestPointM':float(np.linalg.norm(archq-np.array(q)))})
assert nearestGap<2e-6 and distanceGap<2e-6
unit=lambda v:v/np.linalg.norm(v);distal=[];arrays={};adj=[set() for _ in P]
for tri in T:
 for i,j in [(tri[0],tri[1]),(tri[1],tri[2]),(tri[2],tri[0])]:adj[int(i)].add(int(j));adj[int(j)].add(int(i))
# Exact coincident-coordinate aliases are read-only graph nodes, not a weld.
unique,alias=np.unique(n['gloveXYZ'],axis=0,return_inverse=True);aliasAdj=[set() for _ in unique]
for tri in alias[T]:
 for i,j in [(tri[0],tri[1]),(tri[1],tri[2]),(tri[2],tri[0])]:aliasAdj[int(i)].add(int(j));aliasAdj[int(j)].add(int(i))
arrays['nativeCoordinateAlias']=alias;sections={}
for side in ['L','R']:
 idx=lambda s:names.index(s+'.'+side);wrist=n['heads'][idx('hand')];middle=n['heads'][idx('middle_01')];width=unit(n['heads'][idx('pinky_01')]-n['heads'][idx('index_01')]);long=unit(middle-wrist-width*np.dot(width,middle-wrist));nonthumb=['index','middle','ring','pinky'];mcps=np.array([n['heads'][idx(z+'_01')] for z in nonthumb]);pips=np.array([n['heads'][idx(z+'_02')] for z in nonthumb]);plane=float(((mcps-wrist)@long).max()+.5*((pips-mcps)@long).min());station=(P-wrist)@long;sideMask=P[:,1]<0 if side=='L' else P[:,1]>0;cut=np.flatnonzero(sideMask&(station>plane));remaining=set(map(int,cut));components=[]
 while remaining:
  seed=min(remaining);todo=[seed];remaining.remove(seed);component=[]
  while todo:
   i=todo.pop();component.append(i)
   for j in adj[i]:
    if j in remaining:remaining.remove(j);todo.append(j)
  component.sort();components.append(component)
 components.sort(key=lambda z:len(z),reverse=True);witness=[]
 for ci,ids in enumerate(components):
  tip=int(ids[int(np.argmax(station[ids]))]);witness.append({'component':ci,'vertices':len(ids),'farthestStationNativeID':tip,'stationM':float(station[tip]),'tipXYZNativeM':P[tip].tolist(),'minimumDistanceToSemanticTerminalTailM':{z:float(np.linalg.norm(P[ids]-n['tails'][idx(z+'_03')],axis=1).min()) for z in nonthumb}});arrays[side+'DistalSectionComponent'+str(ci)+'NativeIDs']=np.array(ids,int)
 remainingAlias=set(map(int,alias[cut]));aliasComponents=[]
 while remainingAlias:
  seed=min(remainingAlias);todo=[seed];remainingAlias.remove(seed);component=[]
  while todo:
   v=todo.pop();component.append(v)
   for j in aliasAdj[v]:
    if j in remainingAlias:remainingAlias.remove(j);todo.append(j)
  aliasComponents.append(sorted(component))
 aliasComponents.sort(key=lambda z:len(z),reverse=True);aliasWitness=[]
 for ci,comp in enumerate(aliasComponents):
  nativeIDs=cut[np.isin(alias[cut],comp)];tip=int(nativeIDs[np.argmax(station[nativeIDs])]);aliasWitness.append({'component':ci,'uniqueExactCoordinateNodes':len(comp),'nativeVertices':len(nativeIDs),'farthestStationNativeID':tip,'stationM':float(station[tip]),'nativeIDArchiveKey':side+'ExactAliasSection'+str(ci)+'NativeIDs'});arrays[side+'ExactAliasSection'+str(ci)+'NativeIDs']=nativeIDs
 sections[side]={'definition':'ONE plane: maximum nonthumb MCP longitudinal station + half minimum MCP-to-PIP projected length; no section/angle/threshold sweep. Raw graph and exact-coordinate alias graph connectivity after this single plane, independent of weights; no proximity weld. Thumb can lie proximal to this plane.','wristNativeXYZ':wrist.tolist(),'widthUnitNative':width.tolist(),'longitudinalUnitNative':long.tolist(),'planeStationM':plane,'rawNativeGraphComponents':witness,'exactCoordinateAliasGraphComponents':aliasWitness,'limits':'Section components alone do not prove five complete fingers or inability to reshape existing topology; labels are nearest semantic-tail diagnostic, not geometric segmentation certification.'}
 for finger in ['index','middle','ring','pinky','thumb']:
  j=idx(finger+'_03');donor=np.flatnonzero(BW[:,j]>0);triWith=np.flatnonzero((BW[BT,j]>0).any(1));covered=np.flatnonzero(sample[:,j]>0);strong=np.flatnonzero(BW[:,j]>.5);tip=n['tails'][j];q,norm,ti,dist=gTree.find_nearest(Vector(tip));gt=T[ti];dv=P[gt];uv=np.linalg.lstsq(np.column_stack([dv[1]-dv[0],dv[2]-dv[0]]),np.array(q)-dv[0],rcond=None)[0];gb=np.array([1-uv.sum(),uv[0],uv[1]]);donorDistances=[]
  for vi in strong:
   qq,nn,tID,dd=gTree.find_nearest(Vector(body[vi]));donorDistances.append((float(dd),int(vi),int(tID),list(qq)))
  best=min(donorDistances);worst=max(donorDistances);nearestBody=int(donor[np.argmin(np.linalg.norm(body[donor]-tip,axis=1))]);nearestGlove=int(np.argmin(np.linalg.norm(P-tip,axis=1)));transferTI=int(a[nearestGlove]);transferVertices=BT[transferTI];donorRow={'bone':names[j],'donorPositiveVertices':len(donor),'donorPositiveTriangles':len(triWith),'donorMaximumWeight':float(BW[:,j].max()),'sourceGlovePositiveVertices':int((old[:,j]>0).sum()),'candidateFullPositiveVertices':int((pred[:,j]>0).sum()),'candidateFourPositiveVertices':int((four[:,j]>0).sum()),'gloveSamplesTouchingAnyPositiveDonorTriangleVertices':int(np.isin(a,triWith).sum()),'gloveSamplesWithPositiveInterpolatedDistalMass':len(covered),'maximumSampledDistalMass':float(sample[:,j].max()),'terminalTailNativeM':tip.tolist(),'nearestGeometricGloveSurface':{'triangleID':int(ti),'polygonID':int(n['gloveTrianglePolygonIDs'][ti]),'nativeVertexIDs':gt.tolist(),'barycentric':gb.tolist(),'pointNativeM':list(q),'tailDistanceMm':float(dist*1000),'notAssumedSemanticFinger':True},'nearestGloveVertexToTail':{'nativeID':nearestGlove,'XYZNativeM':P[nearestGlove].tolist(),'tailDistanceMm':float(np.linalg.norm(P[nearestGlove]-tip)*1000),'sampledBodyTriangleID':transferTI,'sampledBodyPolygonID':int(n['bodyTrianglePolygonIDs'][transferTI]),'sampledBodyNativeVertexIDs':transferVertices.tolist(),'archivedBarycentric':b[nearestGlove].tolist(),'positiveDonorWeightsByCorner':BW[transferVertices,j].tolist(),'sampledAllHandFingerWeights':{names[k]:float(sample[nearestGlove,k]) for k in allowed if sample[nearestGlove,k]>0}},'nearestDonorVertexToTail':{'nativeID':nearestBody,'weight':float(BW[nearestBody,j]),'XYZNativeM':body[nearestBody].tolist(),'tailDistanceMm':float(np.linalg.norm(body[nearestBody]-tip)*1000)},'strongDonorRegionToActualGloveSurface':{'vertices':len(strong),'nearestGapMm':best[0]*1000,'nearestDonorVertex':best[1],'nearestGloveTriangle':best[2],'farthestGapMm':worst[0]*1000,'farthestDonorVertex':worst[1]},'coverageCause': 'No positive donor-region sample; nearest geometric projection cannot create absent sampled distal mass.' if not len(covered) else 'Positive donor-region samples exist.'};distal.append(donorRow)
  arrays[names[j]+'PositiveDonorNativeIDs']=donor;arrays[names[j]+'PositiveDonorTriangleIDs']=triWith;arrays[names[j]+'SampledPositiveGloveNativeIDs']=covered
missing=[z['bone'] for z in distal if z['candidateFullPositiveVertices']==0];assert set(missing)=={'index_03.L','pinky_03.L','thumb_03.L','pinky_03.R','ring_03.R'}
for p,h in prep['pins'].items():assert sha(root/p)==h['sha256'],p
np.savez_compressed(out/'anatomy-witness-ids.npz',**arrays);r={'status':'EXACT_TRANSFER_REPRODUCED_DONOR_SUPPORT_UNSAMPLED_FOR_FIVE_FIELDS','recipeSHA256':sha(__file__),'nativeSourceAndCandidatePositionsTopologyByteExact':True,'fullAndFourWeightsAndRemovedMassReproducedByteExact':True,'transferFallbackVertices':fallback,'independentNearestDonorTriangleIDsExact':sameTI==len(P),'independentNearestDonorTrianglesMatched':sameTI,'gloveVertices':len(P),'maximumNearestPointGapM':nearestGap,'maximumDistanceReceiptGapM':distanceGap,'nearestTriangleTies':ties,'distalFields':distal,'oneAnatomicalSection':sections,'archiveSHA256':sha(out/'anatomy-witness-ids.npz'),'pinsUnchangedAfter':True,'limits':['Nearest geometric projection samples a single body triangle per glove vertex with no per-finger constraint or endpoint-coverage guarantee. It can preserve empty influence fields despite a complete donor.','Physical lobe/terminal proximity and one-section connectivity witnesses are independent of semantic influence labels; they do not certify a full five-finger surface, closed wrap or a constrained repair feasible in the frozen scope.','Only existing field metrology, no source changes, candidate, geometry/weight/pose solve, parameter sweep, render/capture or admission.']};(out/'transfer-anatomy.json').write_text(json.dumps(r,indent=2)+'\n');print('FULL_FOUR_TRANSFER_EXACT',missing,'NEAREST_MATCHES',sameTI,'SECTION_COMPONENTS',{s:[z['vertices'] for z in d['rawNativeGraphComponents']] for s,d in sections.items()},flush=True)
