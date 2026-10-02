"""Parent integration check: frozen inputs, skin ownership and motion proof."""
from pathlib import Path
import hashlib,json
import numpy as np
R=Path('/Users/raynos/projects/games/rockhop');O=R/'docs/evidence/hero-remaster/one-rider-v2/rig-foundation167';B=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/rig-foundation167')
f=json.loads((O/'freeze.json').read_text());verified=0
for cat in ['sourceFiles','recipeAndInspectedDependencies','evidenceFiles','privateInputs']:
 for row in f[cat]:
  p=Path(row['path']);expected=row.get('sha256',row.get('SHA256'));assert hashlib.sha256(p.read_bytes()).hexdigest()==expected;verified+=1
fixture=Path(f['fixture']['path']);assert hashlib.sha256(fixture.read_bytes()).hexdigest()==f['fixture']['SHA256'];verified+=1
x=json.loads((O/'raw-foundation.json').read_text());actual=json.loads((O/'actual-three-foundation.json').read_text());frames=json.loads(fixture.read_text())['frames'];c=np.load(B/'raw-core.npz')
assert all(x['bindingComparisons'].values());assert len(actual['bindings'])==5 and len(actual['rows'])==5404
assert len(c['positions'])==1423 and actual['loaderWeights']['allPredictionLanesExact']
P=np.c_[c['positions'].astype(float),np.ones(1423)];W=np.zeros((1423,19))
for k in range(4):np.add.at(W,(np.arange(1423),c['joints'][:,k]),c['weights'][:,k])
rest=c['rest'];ib=c['inverseBind'];D=np.array([r['deformationWorldColumnMajor'] for r in frames]).reshape(5404,19,4,4).transpose(0,1,3,2);M=D@rest@ib
baseline=np.einsum('vj,jab,vb->va',W,M[0,:,:3,:],P,optimize=True);maxdiff=0;unilateral=0;unilateralRoundoff=0
coreJoints=np.flatnonzero(W.sum(0)>0)
for start in range(0,5404,32):
 positions=np.einsum('vj,fjab,vb->fva',W,M[start:start+32,:,:3,:],P,optimize=True);motion=np.linalg.norm(positions-baseline,axis=2).max(1)
 for k,value in enumerate(motion):
  i=start+k;maxdiff=max(maxdiff,abs(float(value)-actual['rows'][i]['maximumCoreMotionVsNeutralM']))
  if '.' in frames[i]['family']:
   # The exact contributing matrices and actual Three surface stay unchanged.
   # NumPy's scalar/batched contractions can round their identical sums differently.
   assert np.array_equal(M[i,coreJoints],M[0,coreJoints])
   assert actual['rows'][i]['maximumCoreMotionVsNeutralM']==0
   unilateralRoundoff=max(unilateralRoundoff,float(value));unilateral+=1
assert unilateral==16*193 and maxdiff<1e-12
result={'kind':'Parent independent frozen rig diagnostic verification; no anatomy acceptance','verifiedHashes':verified,'coreVertices':1423,'frames':5404,'unilateralFramesExactContributingMatricesAndActualZeroMotion':unilateral,'independentPerFrameMotionDeltaM':maxdiff,'numpyScalarVsBatchedNeutralRoundoffM':unilateralRoundoff,'setupFinding':'First assertion requiring identical scalar/batched BLAS rounding failed. Exact contributing matrix equality and actualThree0motion remain mandatory; no physical threshold changed.','allBindingComparisonsExact':True,'limits':'Central frozen ROI only. Does not exclude outer chest/axilla arm influence or validate pivots from nearby cloth. Actual game contacts, moving neck/shoulder anatomy and Garage/device appearance remain open.'}
(O/'parent-verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
