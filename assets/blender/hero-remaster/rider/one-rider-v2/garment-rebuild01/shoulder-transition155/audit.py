"""Actual480 riding-state strain and strict triangle intersection audit; no repair."""
from pathlib import Path
import hashlib,json,time
import numpy as np
from scipy.spatial import cKDTree
ROOT=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2')
REPO=Path('/Users/raynos/projects/games/rockhop');OUT=REPO/'docs/evidence/hero-remaster/one-rider-v2/garment-rebuild01/shoulder-transition155';RUN=ROOT/'garment-rebuild01/shoulder-transition155'
f=np.load(RUN/'transition.npz');P=f['positions'];T=f['triangles'];W=f['weights'];N=f['normals'];scope=f['triangleScope'];HP=f['protectedHoodPositions'];HT=f['protectedHoodTriangles'];HW=f['protectedHoodWeights'];ring=f['protectedRingIDs'];sourceIDs=f['protectedHoodVertexIDs'][ring]
def unit(a):return a/np.maximum(np.linalg.norm(a,axis=-1,keepdims=True),1e-20)
rest=P[T];cross=np.cross(rest[:,1]-rest[:,0],rest[:,2]-rest[:,0]);edge=np.linalg.norm(rest-np.roll(rest,-1,axis=1),axis=2);normal=unit(cross);sourceDot=np.einsum('ti,ti->t',normal,unit(N[T].mean(1)))
manifest=json.loads((OUT.parent/'full-motion155/report.json').read_text());rec=manifest['outputs'][0];raw=(ROOT/'garment-rebuild01/full-motion155'/rec['file']).read_bytes();assert hashlib.sha256(raw).hexdigest()==rec['sha256'];M=np.frombuffer(raw,dtype='<f8').reshape(480,19,4,4).transpose(0,1,3,2)
# Strict noncoplanar crossings. Adjacencies are excluded using exact rest-position
# identities, including protected hood material aliases.
combined=np.concatenate([P,HP]);combinedT=np.concatenate([T,HT+len(P)]);_,inv=np.unique(combined,axis=0,return_inverse=True);ids=inv[combinedT];transitionIDs=np.where(scope==1)[0]
def segment_triangle(S,E,Q):
 normal=np.cross(Q[:,1]-Q[:,0],Q[:,2]-Q[:,0]);direction=E-S;den=np.einsum('ij,ij->i',normal,direction);valid=abs(den)>1e-14
 alpha=np.divide(np.einsum('ij,ij->i',normal,Q[:,0]-S),den,out=np.full(len(S),np.nan),where=valid);point=S+alpha[:,None]*direction
 v0=Q[:,1]-Q[:,0];v1=Q[:,2]-Q[:,0];v2=point-Q[:,0];d00=np.einsum('ij,ij->i',v0,v0);d01=np.einsum('ij,ij->i',v0,v1);d11=np.einsum('ij,ij->i',v1,v1);d20=np.einsum('ij,ij->i',v2,v0);d21=np.einsum('ij,ij->i',v2,v1);det=d00*d11-d01*d01
 u=np.divide(d11*d20-d01*d21,det,out=np.full(len(S),np.nan),where=abs(det)>1e-25);v=np.divide(d00*d21-d01*d20,det,out=np.full(len(S),np.nan),where=abs(det)>1e-25)
 return valid&(alpha>1e-7)&(alpha<1-1e-7)&(u>-1e-7)&(v>-1e-7)&(u+v<1+1e-7)
def intersections(points):
 tri=points[combinedT];centers=tri.mean(1);radius=np.linalg.norm(tri-centers[:,None,:],axis=2).max(1);tree=cKDTree(centers);lo=tri.min(1);hi=tri.max(1);pairs=[]
 for i in transitionIDs:
  candidates=np.array(tree.query_ball_point(centers[i],radius[i]+radius.max()),dtype=int)
  candidates=candidates[candidates!=i];candidates=candidates[(candidates<transitionIDs[0])|(candidates>i)]
  overlap=(lo[candidates]<=hi[i]+1e-10).all(1)&(hi[candidates]>=lo[i]-1e-10).all(1)
  candidates=candidates[overlap];share=(ids[candidates,:,None]==ids[i,None,:]).any(axis=(1,2));candidates=candidates[~share]
  pairs.extend((int(i),int(j)) for j in candidates)
 pairs=np.array(pairs,dtype=int).reshape(-1,2);hits=[]
 for start in range(0,len(pairs),30000):
  batch=pairs[start:start+30000];A=tri[batch[:,0]];B=tri[batch[:,1]];hit=np.zeros(len(batch),bool)
  for k in range(3):hit|=segment_triangle(A[:,k],A[:,(k+1)%3],B)|segment_triangle(B[:,k],B[:,(k+1)%3],A)
  hits.extend(batch[hit].tolist())
 return {'broadPhasePairs':len(pairs),'strictNoncoplanarCrossings':len(hits),'transitionVsHood':sum(j>=len(T) for i,j in hits),'transitionVsNativeOrTransition':sum(j<len(T) for i,j in hits),'literalTrianglePairs':hits}
# Four requested original34 witness keys plus rest intersections. Full480 strain
# is evaluated; intersection queries are explicitly bounded to these five states.
start=time.monotonic();rows=[];collisionRows=[{'sample':'rest',**intersections(combined)}];posedSamples={}
for frame,m in enumerate(M):
 posed=np.einsum('vj,jab,vb->va',W,m[:,:3,:],np.c_[P,np.ones(len(P))]);hood=np.einsum('vj,jab,vb->va',HW,m[:,:3,:],np.c_[HP,np.ones(len(HP))]);skinN=unit(np.einsum('vj,jab,vb->va',W,m[:,:3,:3],N));q=posed[T];cr=np.cross(q[:,1]-q[:,0],q[:,2]-q[:,0]);dot=np.einsum('ti,ti->t',unit(cr),unit(skinN[T].mean(1)));stretch=(np.linalg.norm(q-np.roll(q,-1,axis=1),axis=2)/np.maximum(edge,1e-20)).max(1);ar=np.linalg.norm(cr,axis=1)/np.maximum(np.linalg.norm(cross,axis=1),1e-20)
 row={'frame':frame,'seamPositionMaxDeltaM':float(abs(posed[ring]-hood[sourceIDs]).max()),'scopes':{}}
 for name,mask in [('native',scope==0),('transition',scope==1)]:row['scopes'][name]={'normalOppositionFlags':int((mask&(sourceDot>.2)&(dot<-.2)).sum()),'maximumEdgeStretch':float(stretch[mask].max()),'areaCollapsedBelow25Percent':int((mask&(ar<.25)).sum())}
 rows.append(row)
 if frame in [114,186,304,426]:
  collisionRows.append({'sample':frame,**intersections(np.concatenate([posed,hood]))});posedSamples[f'frame{frame}Positions']=posed;posedSamples[f'frame{frame}HoodPositions']=hood
np.savez_compressed(RUN/'four-actual-poses.npz',**posedSamples)
summary={name:{'worstNormalOppositionFlags':max(r['scopes'][name]['normalOppositionFlags'] for r in rows),'worstMaximumEdgeStretch':max(r['scopes'][name]['maximumEdgeStretch'] for r in rows),'worstAreaCollapsedBelow25Percent':max(r['scopes'][name]['areaCollapsedBelow25Percent'] for r in rows)} for name in ['native','transition']}
report={'status':'Single shoulder155 candidate CPU evidence; no static or moving appearance acceptance','matrixSHA256':rec['sha256'],'actualRidingFrames':480,'maximumSeamPositionDeltaM':max(r['seamPositionMaxDeltaM'] for r in rows),'restNormalOpposition':int((sourceDot<0).sum()),'summary':summary,'rows':rows,'intersectionRows':collisionRows,'seconds':time.monotonic()-start,'limits':['No visual appearance/rig/contact/physics approval from strain alone.','Intersection audit covers transition-vs-nonadjacent triangles at rest and four witness poses, not all480.','Strict noncoplanar edge/face crossings only; coplanar overlap and pairs sharing an exact rest vertex are excluded.','Head geometry remains source-only, not included in transition collision audit.','Native wrist/shoe interfaces remain unstitched.']}
(OUT/'audit-report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'summary':summary,'restNormalOpposition':report['restNormalOpposition'],'seam':report['maximumSeamPositionDeltaM'],'intersections':[{k:v for k,v in r.items() if k!='literalTrianglePairs'} for r in collisionRows],'seconds':report['seconds']},indent=2))
