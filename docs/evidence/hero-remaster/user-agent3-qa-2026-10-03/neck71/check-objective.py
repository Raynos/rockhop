"""Recompute archived source fit objectives and their ancestry; no solve."""
import hashlib,heapq,json
from pathlib import Path
import numpy as np
out=Path(__file__).resolve().parent;qa=out.parent;root=out.parents[4];ev=root/'docs/evidence/hero-remaster/anatomical-foundation-2026-10-03/user-agent1';asset=root/'assets/blender/hero-remaster/rider/anatomical-foundation-2026-10-03/user-agent1';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();prep=json.loads((qa/'neck70/preparation.json').read_text())
for p,h in prep['pins'].items():assert sha(root/p)==h['sha256'],p
n=dict(np.load(qa/'body52/native-fields.npz'));f=dict(np.load(asset/'neck-interface27/triangulated-neck-fields.npz'));w=dict(np.load(ev/'neck-interface102/solve-witnesses.npz'));reg=dict(np.load(ev/'neck-interface96/ordered-boundaries.npz'));constraints=json.loads((qa/'neck68/source-assessment.json').read_text());scope=json.loads((qa/'body59/proposal.json').read_text())['preciseInitialAuthoringMargin'];NB=len(f['bodyRestXYZ']);hp=n['protectedHeadXYZ'].astype(float);alias=reg['headPositionAlias'];ht=n['protectedHeadTriangles'];canonical=n['originalFullXYZ'].astype(float);ct=n['originalFullTriangles'];cp=canonical[ct];names=n['boneNames'].tolist();neck=n['rigRest'][names.index('neck'),:3,3].astype(float);head=n['rigRest'][names.index('head'),:3,3].astype(float);expected=np.vstack([f['bodyRestXYZ'],f['headRestXYZ']]).astype(float)
def periodic(u,knots,points):
 knots=np.r_[knots,1.];points=np.vstack([points,points[0]]);return np.column_stack([np.interp(np.asarray(u),knots,points[:,j]) for j in range(3)])
bodyfree=np.r_[scope['bodyExistingRenderedNativeVertices'],np.arange(9037,NB)];sources=f['bodyAttributeEdgeSources'][bodyfree];a=sources[:,0].astype(int);b=sources[:,1].astype(int);u=sources[:,2,None];expected[bodyfree]=(1-u)*n['renderedBodyXYZ'][a]+u*n['renderedBodyXYZ'][b]
# Independent shortest-path ownership in the original head position quotient.
vt=alias[ht];edges=np.unique(np.sort(np.vstack([vt[:,[0,1]],vt[:,[1,2]],vt[:,[2,0]]]),axis=1),axis=0);representatives=reg['headAliasRepresentative'];adj=[[] for _ in representatives]
for a,b in edges:
 length=float(np.linalg.norm(hp[representatives[a]]-hp[representatives[b]]));adj[a].append((int(b),length));adj[b].append((int(a),length))
def shortest(seeds):
 distance=np.full(len(adj),np.inf);owners=np.full(len(adj),-1,dtype=int);queue=[]
 for i,v in enumerate(seeds):distance[v]=0.;owners[v]=i;heapq.heappush(queue,(0.,int(v),i))
 while queue:
  cost,v,owner=heapq.heappop(queue)
  if cost!=distance[v] or owners[v]!=owner:continue
  for z,weight in adj[v]:
   d=cost+weight
   if d<distance[z]:distance[z]=d;owners[z]=owner;heapq.heappush(queue,(d,z,owner))
 return distance,owners
outer=f['headOriginalFrontOrderedIDs'];inner=reg['innerHeadOrderedNativeRepresentatives'][::-1];inner=np.roll(inner,-int(np.argmax(hp[inner,0])));od,_=shortest(alias[outer]);idist,iowner=shortest(alias[inner]);lengths=np.linalg.norm((np.roll(hp[inner],-1,axis=0)-hp[inner])[:,:2],axis=1);iu=np.r_[0.,np.cumsum(lengths[:-1])]/lengths.sum();rows=[];inner_count=0
cross2=lambda a,b:a[...,0]*b[...,1]-a[...,1]*b[...,0]
for v in constraints['actualEditableHeadIDsAfterAliasProtection']:
 p=hp[v];z=p[2];axis=(neck+(head-neck)*((z-neck[2])/(head[2]-neck[2])))[:2];direction=p[:2]-axis;direction/=np.linalg.norm(direction);ids=np.flatnonzero((cp[:,:,2].min(1)<z)&(cp[:,:,2].max(1)>=z));segments=[];barys=[]
 for face in cp[ids]:
  ss=[];bb=[]
  for a,b in [(0,1),(1,2),(2,0)]:
   if (face[a,2]<z)!=(face[b,2]<z):
    t=(z-face[a,2])/(face[b,2]-face[a,2]);weights=np.zeros(3);weights[a]=1-t;weights[b]=t;ss.append(weights@face);bb.append(weights)
  assert len(ss)==2;segments.append(ss);barys.append(bb)
 segments=np.array(segments);barys=np.array(barys);a=segments[:,0,:2];edge=segments[:,1,:2]-a;den=cross2(direction,edge);ok=np.abs(den)>1e-14;distance=np.full(len(den),np.nan);fraction=distance.copy();distance[ok]=cross2(a[ok]-axis,edge[ok])/den[ok];fraction[ok]=cross2(a[ok]-axis,direction)/den[ok];hits=np.flatnonzero(ok&(distance>0)&(fraction>=-1e-9)&(fraction<=1+1e-9));assert len(np.unique(np.round(distance[hits],10)))==1;j=int(hits[np.argmin(distance[hits])]);bary=(1-fraction[j])*barys[j,0]+fraction[j]*barys[j,1];reference=bary@canonical[ct[ids[j]]];offset=np.zeros(3);inside=idist[alias[v]]<od[alias[v]]
 if inside:
  phase=iu[iowner[alias[v]]];offset=periodic([phase],iu,hp[inner])[0]-periodic([phase],f['headOriginalKnots'],hp[outer])[0];inner_count+=1
 expected[NB+v]=reference+offset;rows.append({'originalHeadVertex':int(v),'canonicalTriangleID':int(ids[j]),'canonicalTriangleVertexIDs':ct[ids[j]].tolist(),'canonicalBarycentric':bary.tolist(),'canonicalReferenceNativeM':reference.tolist(),'innerGeodesicReference':bool(inside),'retainedInnerMinusOuterOffsetM':offset.tolist()})
shared=periodic(f['commonU'],f['bodyOriginalKnots'],n['renderedBodyXYZ'][f['bodyOriginalFrontOrderedIDs']])
for part,offset in [('body',0),('head',NB)]:
 sid=f[part+'SeamPhysicalIDs'];ids=np.flatnonzero(sid>=0);expected[offset+ids]=shared[sid[ids]]
cap=np.flatnonzero(f['headAttributeEdgeSources'][:,0]<0);assert len(cap)==1;expected[NB+cap[0]]=expected[NB+inner].mean(0)
mapping=w['physicalRawToNode'];nodes,first=np.unique(mapping,return_index=True);assert np.array_equal(nodes,np.arange(len(w['referenceXYZ'])));reference=expected[first];fixed=w['fixedPhysicalNodes'];reference[fixed]=w['referenceXYZ'][fixed];delta=np.linalg.norm(reference-w['anatomicalReferenceXYZ'],axis=1);assert delta.max()<1e-9
report={'status':'UNACCEPTED_ARCHIVED_FIT_OBJECTIVE_SOURCE_ANCESTRY_REPRODUCED','recipeSHA256':sha(__file__),'all30InputPinsUnchanged':True,'originalEditableHeadRayReferences':len(rows),'innerReferenceRows':inner_count,'bodyReferenceRows':len(bodyfree),'sharedSourceCurveKnots':len(shared),'capSourceIdentity':None,'capReferenceDerivedFromDistinctInner190Loop':True,'fixedQEqualsReferenceP':bool(np.array_equal(reference[fixed],w['referenceXYZ'][fixed])),'maximumObjectiveReferenceResidualM':float(delta.max()),'headRayWitnesses':rows,'limits':['Canonical fit objectives only on free physical nodes; fixed Q is unchanged source P. No claimed exact-source identity for authored geometry.','Interior classification is original source shortest-path ownership and retained shell offset, not collision avoidance or shell containment.','Q recomputation and archived stationarity verification only; no solve/new candidate/source write/capture.']}
for p,h in prep['pins'].items():assert sha(root/p)==h['sha256'],p
(out/'objective-ancestry.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='headRayWitnesses'},indent=2))
