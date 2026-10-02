"""Parent literal path certificate; does not authorize sculpt/retopology."""
from pathlib import Path
import hashlib,json,sys
import numpy as np
R=Path('/Users/raynos/projects/games/rockhop');E=R/'docs/evidence/hero-remaster/one-rider-v2/armhole-design190';B=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2');sys.path.insert(0,str(R/'assets/blender/hero-remaster/rider/one-rider-v2/candidate-handoff170'))
from map_candidate import GLB
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();assert not(E/'parent-review.json').exists()
freeze=json.loads((E/'freeze.json').read_text())
for path,r in freeze['files'].items():assert sha(path)==r['sha256'] and Path(path).stat().st_size==r['bytes']
report=json.loads((E/'report.json').read_text())
for path,r in report['inputs'].items():assert sha(path)==r['sha256'] and Path(path).stat().st_size==r['bytes']
g=GLB(B/'source-preserving-garment185/operator/rider.glb');p=g.j['meshes'][0]['primitives'][0];P=g.array(p['attributes']['POSITION']);F=g.array(p['indices']).reshape(-1,3);U,q=np.unique(P,axis=0,return_inverse=True);U=U.astype(float);T=q[F]
scope=json.loads((B/'source-axilla189/positiveZ_lateral-proposed-strip.json').read_text());edges=set(tuple(sorted(map(int,e)))for t in T[scope['sourceFaceIDs']]for e in zip(t,np.roll(t,-1)))
report=json.loads((E/'report.json').read_text());proofs=[]
for b in report['fixedBoundaryPathBounds']:
 path=b['pathPhysicalIDs'];assert all(tuple(sorted((a,c)))in edges for a,c in zip(path,path[1:]));assert path[-1]in scope['boundaryPhysicalVertexIDs']
 length=float(np.linalg.norm(np.diff(U[path],axis=0),axis=1).sum());dy=b['targetY_M']-U[path[0],1];radius=(.14**2-dy**2)**.5
 horizontal=float(np.linalg.norm((U[path[-1]]-U[path[0]])[[0,2]]));span=(max(0,horizontal-radius)**2+(b['targetY_M']-U[path[-1],1])**2)**.5;ratio=span/length
 assert abs(length-b['shortestOriginalInScopePathLengthM'])<1e-14 and abs(ratio-b['necessaryMaximumEdgeRatio'])<1e-12
 proofs.append({'targetY_M':b['targetY_M'],'literalPath':path,'restLengthM':length,'minimumFixedEndpointSpanM':span,'minimumNecessaryOneEdgeRatio':ratio})
x={'status':'FIXED_BOUNDARY_ORIGINAL_CONNECTIVITY_RAISE_CERTIFICATE_VERIFIED','filesVerified':len(freeze['files']),'inputsVerified':len(report['inputs']),'source185Unchanged':True,'proofs':proofs,'limits':'Necessary ratio applies only if original path edges and fixed boundary survive while named critical vertex is raised within140mm.1.5 is a hypothetical construction quality bar, not inherited user acceptance or a proof of all possible sculpt/retopology failure. No measured moving gate or geometry candidate.','parentSetupFault':'First inspection assumed the sibling list-based freeze schema; this freeze is a path dictionary. No source edit or candidate was involved.', 'proposalCorrection':'Reject whole closed-p0 volume requirement: p0 has genuine hood/cuff boundaries and is not closed. Use separately measured sectional channel areas or explicit validated regional closure; no open-shell signed-volume acceptance.', 'next':'Left-only local cut-and-resew changes interior connectivity explicitly, with fixed literal source boundary and protected outside; stage2 field correction still required for below-scope source witness.'}
(E/'parent-review.json').write_text(json.dumps(x,indent=2)+'\n');print(json.dumps(x))
