"""Full native broad-phase face pairs with projected strict coplanar SAT."""
from pathlib import Path
import json,time,resource,numpy as np,ipctk
B=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2');R=Path('/Users/raynos/projects/games/rockhop');E=R/'docs/evidence/hero-remaster/one-rider-v2/arm-proportion216';z=np.load(B/'arm-proportion216/construction.npz');F=z['faces'];edges=np.unique(np.sort(np.concatenate([F[:,[0,1]],F[:,[1,2]],F[:,[2,0]]]),axis=1),axis=0)
def sat2(a,b):
    ea=np.roll(a,-1,axis=1)-a;eb=np.roll(b,-1,axis=1)-b;ee=np.concatenate([ea,eb],axis=1);axes=np.stack([-ee[:,:,1],ee[:,:,0]],axis=2);axes/=np.linalg.norm(axes,axis=2)[:,:,None]
    pa=np.einsum('nkj,nij->nki',axes,a);pb=np.einsum('nkj,nij->nki',axes,b);overlap=np.minimum(pa.max(2),pb.max(2))-np.maximum(pa.min(2),pb.min(2));return (overlap>1e-12).all(1)
a=np.array([[[0.,0.],[1.,0.],[0.,1.]]]);assert sat2(a,a+np.array([.1,.1]))[0];assert not sat2(a,a+np.array([2.,0.]))[0];assert not sat2(a,np.array([[[0.,0.],[-1.,0.],[0.,-1.]]]))[0]
results=[];start=time.monotonic()
for label,key in [('source','sourcePositionsNative'),('candidate','candidatePositionsNativeFloat32')]:
    P=z[key].astype(float);grid=ipctk.HashGrid();grid.build(P,edges,F,inflation_radius=1e-12);c=grid.detect_face_face_candidates();pairs=np.array([(x.face0_id,x.face1_id) for x in c],dtype=np.int64);del c
    hits=[];nonincident=0;copcount=0
    for offset in range(0,len(pairs),50000):
        ids=pairs[offset:offset+50000];aIDs=F[ids[:,0]];bIDs=F[ids[:,1]];keep=~(aIDs[:,:,None]==bIDs[:,None,:]).any(axis=(1,2));ids=ids[keep];nonincident+=len(ids)
        a=P[F[ids[:,0]]];b=P[F[ids[:,1]]];na=np.cross(a[:,1]-a[:,0],a[:,2]-a[:,0]);nb=np.cross(b[:,1]-b[:,0],b[:,2]-b[:,0]);na/=np.linalg.norm(na,axis=1)[:,None];nb/=np.linalg.norm(nb,axis=1)[:,None]
        cop=(np.linalg.norm(np.cross(na,nb),axis=1)<1e-10)&(np.max(abs(np.einsum('nij,nj->ni',b-a[:,0,None,:],na)),axis=1)<1e-10)
        ids=ids[cop];a=a[cop];b=b[cop];na=na[cop];copcount+=len(ids)
        if not len(ids):continue
        drop=np.argmax(abs(na),axis=1);ret=np.array([[1,2],[0,2],[0,1]])[drop];a2=np.take_along_axis(a,np.repeat(ret[:,None,:],3,axis=1),axis=2);b2=np.take_along_axis(b,np.repeat(ret[:,None,:],3,axis=1),axis=2);overlap=sat2(a2,b2);hits.extend(ids[overlap].tolist())
    results.append({'label':label,'broadPhaseFacePairs':len(pairs),'nonincidentPairs':nonincident,'coplanarPairsChecked':copcount,'strictPositiveAreaCoplanarOverlaps':hits})
report={'status':'COPLANAR_PREREQUISITES_CLEAR' if not any(r['strictPositiveAreaCoplanarOverlaps'] for r in results) else 'COPLANAR_REJECTED_SAVED_CANDIDATE','algorithm':'NativeHashGrid fullfaceface candidates1e-12inflation; exclude physicalsharedvertices; normalizednormalparallel1e-10/plane-distance1e-10; strongestnormal-axisdrop; sixprojected separatingaxes strict1e-12 overlap','results':results,'syntheticOverlapSeparatedSharedPointCasesVerified':True,'elapsedSeconds':time.monotonic()-start,'peakRSSBytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'limits':['Tolerance-defined static coplanarpositivearea check, not a symbolic exact-arithmetic proof.','Sharedphysicalvertexpairs excluded, with manifoldlinks/windingchecked separately.','No movingrig or game/contact/visual acceptance.']}
(E/'coplanar-report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
