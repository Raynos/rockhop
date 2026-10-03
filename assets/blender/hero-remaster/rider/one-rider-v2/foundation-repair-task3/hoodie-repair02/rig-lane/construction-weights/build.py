from pathlib import Path
import sys,json,hashlib,numpy as np
from scipy.sparse import coo_matrix,diags
from scipy.sparse.linalg import spsolve
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE));from boundary_weights import harmonic_insert,require_rest_gate
SHAPE=HERE.parents[1]/'shape-lane/volume-lane/armhole-construction'
INPUT=SHAPE/'armhole-chart-outward.npz';SHA='10a1c2094726e7ab929b453e07e5f9c072dd06b0673a8557f4f41c6c5e33c2d7'
assert hashlib.sha256(INPUT.read_bytes()).hexdigest()==SHA
require_rest_gate(SHAPE/'armhole-chart-outward.rest-gate.json')
f=np.load(INPUT);p=f['p0'];original=[f[f'W{i}'].copy() for i in range(5)];variants={n:[w.copy() for w in original]for n in ['fabric-ownership','fabric-anatomical']}
rig=json.loads((HERE.parent/'mechanical-suite/frozen-provenance.json').read_text());print('rigkeys',list(rig),flush=True)
# Named centres are loaded from the frozen exact source34-compatible rig.
sys.path.insert(0,str(HERE.parent/'mechanical-suite'));from motion import P
rows=[]
for side,upper,fore in [('L',6,7),('R',10,11)]:
 chart=f['insertChartVertices'+side];tri=chart[f['insertChartTriangles'+side]];body=f['bodyOpeningVertices'+side];arm=f['sleeveBoundaryVertices'+side]
 field,meta=harmonic_insert(p,tri,body,arm,original[0]);domain=meta['domain'];free=meta['free'];h=meta['ownership'];variants['fabric-ownership'][0][domain]=field[domain]
 # Fresh within-arm assignment: screen a signed anatomical elbow-axis target
 # on the intrinsic new-fabric graph, while keeping every actual seam row fixed.
 axis=P[fore]-P[upper];axis/=np.linalg.norm(axis);signed=np.einsum('vi,i->v',p-P[fore],axis);s=np.clip((signed+.04)/.08,0,1);target=s*s*(3-2*s)
 ed=meta['edges'];c=1/np.maximum(meta['restLengths'],1e-6);g=coo_matrix((np.r_[c,c],(np.r_[ed[:,0],ed[:,1]],np.r_[ed[:,1],ed[:,0]])),shape=(len(p),len(p))).tocsr();degree=np.asarray(g.sum(1)).ravel();L=diags(degree)-g;boundary=np.r_[body,arm]
 fraction=np.zeros(len(p));armtotal=original[0][arm][:,[upper,fore]].sum(1);fraction[arm]=original[0][arm,fore]/armtotal
 # Body boundary fraction=0 is irrelevant where arm ownership is exactly0.
 screen=.25*degree[free];fraction[free]=spsolve(L[free][:,free]+diags(screen),-L[free][:,boundary]@fraction[boundary]+screen*target[free]);fraction=np.clip(fraction,0,1)
 fresh=field.copy();fresh[free]=0;fresh[free,2]=1-h[free];fresh[free,upper]=h[free]*(1-fraction[free]);fresh[free,fore]=h[free]*fraction[free];fresh[boundary]=original[0][boundary];variants['fabric-anatomical'][0][domain]=fresh[domain]
 rows.append({'side':side,'domainVertices':len(domain),'freeVertices':len(free),'fixedBoundaryVertices':len(boundary),'activeBoneUnion':meta['activeBoneUnion'].tolist(),'anatomicalAxis':axis.tolist(),'signedElbowTargetBlendM':.08,'screeningRelativeConductance':.25,'maxForearmFractionTarget':float(target[free].max()),'maxForearmFractionSolved':float(fraction[free].max()),'exactBoundaryRows':bool(np.array_equal(fresh[boundary],original[0][boundary]))})
# Preserve alias rows across ALL primitives. Interior patches have true author IDs;
# coincident source sheets are never used to infer sewn topology.
off=f['primitiveOffsetsNew'];weld=np.concatenate([f[f'physicalWeld{i}']for i in range(5)]);joinedOriginal=np.concatenate(original)
for name,w in variants.items():
 joined=np.concatenate(w);changed=np.any(joined!=joinedOriginal,axis=1);changedIDs=np.unique(weld[changed]);
 for u in changedIDs:
  ids=np.flatnonzero(weld==u);selected=ids[changed[ids]];assert len(selected)
  row=joined[selected[0]];assert np.max(np.abs(joined[selected]-row))<1e-12;joined[ids]=row
 w=[joined[off[i]:off[i+1]].copy()for i in range(5)];variants[name]=w
 assert all(np.array_equal(w[i],original[i])for i in [1,3,4])
 assert max((x>0).sum(1).max() for x in w)<=4
 assert max(np.max(abs(x.sum(1)-1))for x in w)<1e-12
 # Only new sewn insert interior rows may change; no source margin reassignment.
 assert np.array_equal(w[2],original[2]);allowed=np.r_[np.setdiff1d(f['insertChartVerticesL'],np.r_[f['bodyOpeningVerticesL'],f['sleeveBoundaryVerticesL']]),np.setdiff1d(f['insertChartVerticesR'],np.r_[f['bodyOpeningVerticesR'],f['sleeveBoundaryVerticesR']])]
 assert not np.any(np.any(w[0]!=original[0],1)&~np.isin(np.arange(len(p)),allowed))
 out=HERE/(name+'.npz');np.savez_compressed(out,**{f'W{i}':x for i,x in enumerate(w)},sourceGeometrySHA256=SHA)
 print(name,'changed',int(np.any(w[0]!=original[0],1).sum()),'maxdelta',float(np.max(abs(w[0]-original[0]))),flush=True)
(HERE/'weights-provenance.json').write_text(json.dumps({'status':'UNACCEPTED_POSE_GATES_PENDING','geometryPath':str(INPUT),'geometrySHA256':SHA,'sameRestGeometryJointsUVsTextures':True,'protectedHeadGlovesSourceRowsExact':True,'sourceMarginWeightsUnchanged':True,'newFabricOnly':True,'physicalAliasMethod':'Author-provided physicalWeld0..4, never proximity welding detached sheets','ownershipMethod':'Positive inverse-rest-edge harmonic extension of explicit torso chest and detached sleeve boundary rows; no rejected chart scalar','freshArmMethod':'Same ownership; soft intrinsic screened elbow-axis fraction at new interior vertices; all actual source and sewn boundary rows exact','rows':rows,'variants':{n:{'path':str(HERE/(n+'.npz')),'SHA256':hashlib.sha256((HERE/(n+'.npz')).read_bytes()).hexdigest()}for n in variants}},indent=2)+'\n')
