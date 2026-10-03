"""Freeze literal ownership before the one admitted216 anatomy edit."""
from pathlib import Path
import json,hashlib,numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
B=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2');R=Path('/Users/raynos/projects/games/rockhop');E=R/'docs/evidence/hero-remaster/one-rider-v2/arm-proportion216';D=B/'arm-proportion216'
def pin(p):return {'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size}
src=B/'finite-cleanup210/ancestry.npz';assert pin(src)['sha256']=='2e27039502c33d580127d141a8460429a3daaa321c5de101ce8231227ac979ee'
z=np.load(src);old=np.load(B/'finite-native208/ancestry.npz');cut=np.load(B/'head-join211/literal-cut211.npz');c=json.loads((R/'docs/evidence/hero-remaster/one-rider-v2/head-join211/join-contract.json').read_text());spec=json.loads((R/'docs/evidence/hero-remaster/one-rider-v2/tpose-rig-adapter212/proposal.json').read_text());admission=json.loads((R/'docs/evidence/hero-remaster/one-rider-v2/tpose-rig-adapter212/parent-admission212.json').read_text());assert admission['status']=='PARENT_ADMITTED_ONE_PROTECTED_ARM_PROPORTION_TRIAL_NO_BIND'
M=np.array(c['explicitBodyTransform']['matrixNativeToCanonical']);P=z['positions'].astype(float)@M[:3,:3].T+M[:3,3];F=z['faces'];n=len(P)
def mappedRows(faceids):return np.unique(z['sourceRowToOutput'][np.unique(old['faces'][faceids])])
hood=mappedRows(cut['nativeProtectedHoodFaceIDs']);head=mappedRows(cut['nativeHeadRemovedFaceIDs']);central=np.flatnonzero((abs(P[:,2])<=.18)|(P[:,1]<=1.30));tiny=z['sourceRowToOutput'][[98491,98492,98493,98495,98508,100201]]
protected=np.unique(np.r_[hood,head,central,tiny]);owned=[];rigid=[];rows=[];failures=[]
for s in spec['armTrial']:
    sign=1 if s['side']=='L' else -1;r=sign*P[:,2];arm=(r>.18)&(P[:,1]>1.30);hand=(r>=.50)&(P[:,1]>1.20);mask=arm|hand;ids=np.flatnonzero(mask);hands=np.flatnonzero(hand);owned.append(ids);rigid.append(hands)
    conflicts=np.intersect1d(ids,protected);switch=np.flatnonzero((r[F].min(1)<.50)&(r[F].max(1)>=.50)&(P[F,1].min(1)<1.34)&(P[F,1].max(1)>1.20))
    inside=F[np.all(mask[F],axis=1)];edges=np.unique(np.sort(np.concatenate([inside[:,[0,1]],inside[:,[1,2]],inside[:,[2,0]]]),axis=1),axis=0);reverse=np.full(n,-1,int);reverse[ids]=np.arange(len(ids));a=reverse[edges];nc,labels=connected_components(coo_matrix((np.ones(2*len(a)),(np.r_[a[:,0],a[:,1]],np.r_[a[:,1],a[:,0]])),shape=(len(ids),len(ids))).tocsr())
    rec={'side':s['side'],'ownedVertices':len(ids),'rigidHandVertices':len(hands),'ownedComponents':np.bincount(labels).tolist(),'ownedBoundsCanonicalM':[P[ids].min(0).tolist(),P[ids].max(0).tolist()],'protectedConflictIDs':conflicts.tolist(),'distalGateSwitchFacesBelowFullYGate':switch.tolist(),'minimumYNearDistalSwitch':float(P[F[(r[F].min(1)<.50)&(r[F].max(1)>=.50)],1].min()),'sourceKnots':s['sourceLateralKnotsM'],'outwardDisplacementKnots':s['outwardDisplacementAtKnotsM']};rows.append(rec)
    if len(conflicts):failures.append(s['side']+' protected ownership conflict')
    if len(switch):failures.append(s['side']+' distal override discontinuity on source surface')
    if nc!=1:failures.append(s['side']+' arm ownership not one component')
np.savez_compressed(D/'ownership.npz',leftOwned=owned[0],rightOwned=owned[1],leftRigidHand=rigid[0],rightRigidHand=rigid[1],protected=protected,protectedHood=hood,protectedGeneratedHead=head,protectedCentralChestPantsShoes=central,protectedTiny=tiny,matrixNativeToCanonical=M)
report={'status':'OWNERSHIP_ADMITTED_LITERAL_PREREQUISITES_ONLY' if not failures else 'REJECTED_BEFORE_GEOMETRY','failures':failures,'geometryAttempts':0,'protectedHoodRows':len(hood),'protectedGeneratedHeadRows':len(head),'protectedCentralRows':len(central),'protectedTotalRows':len(protected),'sides':rows,'limits':['Source graph branches are declared sleeve ownership; parent visual judgment remains required.','Continuous source-surface field: sourcefaces intersecting r=.50 all lie aboveY1.34, where proximalYgate=1 equalsrigidhand override.','r=.18 andY1.30 support boundaries havezeroC2 field. No mask widening or protected-coordinate clamp.','No field is applied at this stage; invalid ownership stops before a candidate.']}
(E/'preflight.json').write_text(json.dumps(report,indent=2)+'\n')
inputs=[src,B/'finite-cleanup210/clean-native.glb',B/'finite-native208/ancestry.npz',B/'head-join211/literal-cut211.npz',R/'docs/evidence/hero-remaster/one-rider-v2/head-join211/join-contract.json',R/'docs/evidence/hero-remaster/one-rider-v2/tpose-rig-adapter212/proposal.json',R/'docs/evidence/hero-remaster/one-rider-v2/tpose-rig-adapter212/parent-admission212.json',R/'assets/blender/hero-remaster/rider/one-rider-v2/arm-proportion216/preflight.py']
freeze={'status':report['status'],'inputPins':{str(p):pin(p) for p in inputs},'ownershipPin':pin(D/'ownership.npz'),'preflightPin':pin(E/'preflight.json'),'geometryAttempts':0}
(E/'preflight-freeze.json').write_text(json.dumps(freeze,indent=2)+'\n');print(json.dumps(report,indent=2))
