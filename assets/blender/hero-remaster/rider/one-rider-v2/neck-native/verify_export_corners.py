"""Read-only geometry-matched corner UV/material audit, CPU at most4 workers."""
import numpy as np,json,hashlib,itertools
from pathlib import Path
from scipy.spatial import cKDTree
R=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/neck-native/trial01');O=Path('/Users/raynos/projects/games/rockhop/docs/evidence/hero-remaster/one-rider-v2/neck-native/trial01')
if (O/'corner-precision-audit.json').exists():raise RuntimeError('Frozen independent audit exists')
p=R/'export-corners.npz';d=np.load(p);before=d['beforePoints'];after=d['afterPoints'];aUV=d['beforeUV'];bUV=d['afterUV'];aM=d['beforeMaterials'];bM=d['afterMaterials']
# Select the closest original triangle by all3 physical corners; sorting is not
# used as a surrogate for actual UV agreement. Four nearest centres tolerate
# genuinely coincident geometry; ties remain visible in the result.
tree=cKDTree(before.mean(1));dist,candidates=tree.query(after.mean(1),k=4,workers=4)
best=np.full(len(after),np.inf);selected=np.full(len(after),-1,np.int32);order=np.empty((len(after),3),np.int32)
for k in range(4):
 ids=candidates[:,k]
 for permutation in itertools.permutations(range(3)):
  points=before[ids][:,permutation,:];error=np.linalg.norm(points-after,axis=2).max(1);take=error<best
  best[take]=error[take];selected[take]=ids[take];order[take]=permutation
row=np.arange(len(after))[:,None];uv=aUV[selected[:,None],order];uvError=np.abs(uv-bUV).max(axis=(1,2));materialMatch=aM[selected]==bM
report={'status':'UNACCEPTED first-trial roundtrip precision audit; intended face material assignment still failed','arraysSHA256':hashlib.sha256(p.read_bytes()).hexdigest(),'recipeSHA256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'trianglesBefore':len(before),'trianglesAfter':len(after),'uniqueSourceTrianglesMatched':len(np.unique(selected)),'maxWorldCornerPositionErrorM':float(best.max()),'worldCornerErrorAbove2eMinus6M':int((best>2e-6).sum()),'maximumFaceCornerUVError':float(uvError.max()),'UVErrorAbove1eMinus6':int((uvError>1e-6).sum()),'UVErrorEquivalentAt2kPixels':float(uvError.max()*2048),'actualPrePostMaterialNameMismatchTriangles':int((~materialMatch).sum()),'CPUWorkers':4,'actualFaceAssignmentAccepted':False,'explanation':'Pre-export body already collapsed to material0. Roundtrip agreement cannot establish intended head/glove/lining assignment. Native source UV and outside-band source invariants are separate build checks; this audit only establishes actual pre/post export preservation.'}
(O/'corner-precision-audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
