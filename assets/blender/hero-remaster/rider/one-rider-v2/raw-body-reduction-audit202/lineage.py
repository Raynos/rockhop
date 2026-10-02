import os
os.environ['OPENBLAS_NUM_THREADS']='2';os.environ['OMP_NUM_THREADS']='2'
import json,hashlib,importlib.util
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
R=Path('/Users/raynos/projects/games/rockhop');B=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1');O=R/'docs/evidence/hero-remaster/one-rider-v2/raw-body-reduction-audit202';D=B/'one-rider-v2/raw-body-reduction-audit202'
s=importlib.util.spec_from_file_location('reader',R/'assets/blender/hero-remaster/rider/one-rider-v2/candidate-handoff170/map_candidate.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
def get(path,mi=0,pi=0):
 g=m.GLB(path);p=g.j['meshes'][mi]['primitives'][pi];return g,g.array(p['attributes']['POSITION']),g.array(p['indices']).reshape(-1,3)
native=np.load(B/'hunyuan21/04/raw-shape.npz');ng,NP,NF=get(B/'hunyuan21/04/raw-shape.glb');sg,SP,SF=get(B/'hunyuan21/04/shape.glb');mg,MP,MF=get(B/'hunyuan21/04/model.glb');dg,DP,DF=get(B/'hunyuan21/04/working-display2.glb');bg,BP,BF=get(B/'one-rider-v2/rig-adapter01/body-bind11/guarded-correction01/rider.glb');cg,CP,CF=get(B/'one-rider-v2/source-preserving-garment185/operator/rider.glb')
assert np.array_equal(NP,native['vertices'].astype(np.float32)) and np.array_equal(NF,native['faces']);assert mg.bin==dg.bin and np.array_equal(MP,DP) and np.array_equal(MF,DF)
# Transform is literal from neutral assembly report, proper axis and 1.015 declared in bind04 recipe; not fitted.
assembly=json.loads((R/'docs/evidence/hero-remaster/one-rider-v2/glove-cleanup/neutral-assembly/report.json').read_text());s0=assembly['sourceDisplayTransform']['scale'];t=np.array(assembly['sourceDisplayTransform']['translation']);s1=1.015
Mpaint=np.array([[0,0,-s0*s1,.65-s1*t[1]],[0,-s0*s1,0,s1*t[2]],[-s0*s1,0,0,-s1*t[0]],[0,0,0,1]])
centre=(SP.astype(float).min(0)+SP.astype(float).max(0))*.5
paintFlip=np.diag([1.,-1.,-1.,1.]);paintFlip[:3,3]=[0,2*centre[1],2*centre[2]]
M=Mpaint@paintFlip
def transform(P):return (P.astype(float)[:,None,:]*M[None,:3,:3]).sum(2)+M[:3,3]
NR=transform(NP);SR=transform(SP)
# Painted vertices are native(x,z,-y), rounded 6 decimals; undo only that documented export axis.
paintNative=MP[:,[0,2,1]]*[1,-1,1]
recoveredNative=(paintNative*paintFlip.diagonal()[:3])+paintFlip[:3,3]
MR=transform(recoveredNative);DR=MR.copy()
assert np.array_equal(BP,CP) and np.array_equal(BF,CF)
q,ids=cKDTree(DR).query(CP,workers=2);selected=(CP[:,1]>=1.05)&(CP[:,1]<=1.38)&(abs(CP[:,2])>.12)&(abs(CP[:,2])<.35)
print('selectedmatching',selected.sum(),np.quantile(q[selected],[0,.5,.95,1]),'overall',np.quantile(q,[0,.5,.95,1]))
qq,ii=cKDTree(SP).query(recoveredNative,workers=2)
print('paintreduced',np.quantile(qq,[0,.5,.95,1]))
from collections import Counter
faceSame=Counter(map(tuple,np.sort(ii[MF],axis=1)))==Counter(map(tuple,np.sort(SF,axis=1)))
assert qq.max()<1e-6 and faceSame
assert (q[selected&(CP[:,1]<1.35)]<2e-6).all()
rep={'status':'READ_ONLY_DOCUMENTED_LINEAGE_NO_ARBITRARY_FIT','nativeGLBPositionFloat32Exact':True,'nativeGLBIndicesExact':True,'nativeCounts':{'vertices':len(NP),'triangles':len(NF)},'reducedCounts':{'vertices':len(SP),'triangles':len(SF)},'paintCounts':{'vertices':len(MP),'triangles':len(MF)},'paintDisplayBINExact':True,'source185Body11PositionIndexExact':True,'nativeToCurrentRestMatrix':M.tolist(),'paintToCurrentRestMatrix':Mpaint.tolist(),'paintFlipAboutReducedCentre':paintFlip.tolist(),'reducedBoundingCentre':centre.tolist(),'lineage':['raw-shape.npz native vertices/triangles equal raw-shape.glb after required Float32 encoding','shape.glb reduced in same native axes','Observed painted geometry is X180 about reduced bbox centre within rounding. Mechanism inferred from current pinned CPU get_mesh in-place NumPy views and two inpaint calls; generation did not record historical source-file hashes','paint mesh local coordinates (paintOBJ X,paintOBJ Z,-paintOBJ Y), six-decimal OBJ rounding; paintOBJ already has bbox-centred X180','working-display2 only node X+90→X−90; BIN unchanged','Blender imported working-display point(paintOBJ X,paintOBJ Z,-paintOBJ Y)','neutral assembly canonical = sourceDisplayTransform.scale*import point+translation','bind04 proper Blender Z+90 followed by scale1.015 and X+.65, export Blender(X,Z,-Y)','C19/source185 body attributes exactly body11; use source185 identity-world rest positions, do not reapply body11 outer rig transform'],'paintReducedSpatialDistanceM':{'quantiles':[0,.5,.95,1],'values':np.quantile(qq,[0,.5,.95,1]).tolist(),'indexMapRecoveredAfterExactSourceDerivedFlip':True,'all55000IndexedFaceIncidencesMatchByRecoveredPositionMap':bool(faceSame),'preservedNativeRawIDsVsReduced':'No raw→reduced index map saved'},'sourceRestUnderarmDocumentedTransformMatch':{'selection':'1.05<=Y<=1.38 and .12<absZ<.35; purely geometric underarm neighbourhood, not a torso ownership mask','rows':int(selected.sum()),'nearestPaintVertexDistanceQuantilesM':np.quantile(q[selected],[0,.5,.95,1]).tolist(),'matchingToleranceM':2e-6,'allWithinTolerance':bool((q[selected]<2e-6).all()),'mismatchedRows':np.flatnonzero(selected&(q>=2e-6)).tolist(),'mismatchExplanation':'75 rows in Y1.355..1.374 and absZ<=.193 are collar boundary edits; low underarm rows belowY1.35 all match within2microns','spatialCorrespondenceUsedOnlyAfterLiteralRecipeTransform':True},'limits':['No nearest-vertex contact/surface or skin quality claim','Native/deleted fragments and remesh face ancestry differ; exact native→reduced face map not saved','Only preservation/numeric transform verification; parent visual motion judgment remains required']}
(O/'lineage.json').write_text(json.dumps(rep,indent=2)+'\n');np.savez(D/'lineage.npz',nativePositions=NR,nativeFaces=NF,reducedPositions=SR,reducedFaces=SF,paintPositions=DR,paintFaces=DF,currentPositions=CP,currentFaces=CF,transform=M,currentToPaintVertex=ids,currentToPaintDistance=q)
print(json.dumps(rep,indent=2))
