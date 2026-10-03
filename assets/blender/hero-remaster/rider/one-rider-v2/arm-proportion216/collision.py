"""Full native static source/output plus linear source-to-output CCD diagnostic."""
from pathlib import Path
import json,time,resource,numpy as np,ipctk
B=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2');R=Path('/Users/raynos/projects/games/rockhop');E=R/'docs/evidence/hero-remaster/one-rider-v2/arm-proportion216';z=np.load(B/'arm-proportion216/construction.npz');P=z['sourcePositionsNative'].astype(float);Q=z['candidatePositionsNativeFloat32'].astype(float);F=z['faces'];edges=np.unique(np.sort(np.concatenate([F[:,[0,1]],F[:,[1,2]],F[:,[2,0]]]),axis=1),axis=0);mesh=ipctk.CollisionMesh(P,edges,F)
start=time.monotonic();source=bool(ipctk.has_intersections(mesh,P));candidate=bool(ipctk.has_intersections(mesh,Q));ccd=None;exception=None
if not source and not candidate:
    try:ccd=bool(ipctk.is_step_collision_free(mesh,P,Q,narrow_phase_ccd=ipctk.TightInclusionCCD(tolerance=1e-8,max_iterations=1000000,conservative_rescaling=.8)))
    except Exception as e:exception=repr(e)
report={'status':'NATIVE_COLLISION_PREREQUISITES_CLEAR' if not source and not candidate and ccd else 'COLLISION_CHECK_REJECTED_OR_UNQUALIFIED','sourceIntersections':source,'candidateIntersections':candidate,'straightSourceToExportedFloat32CollisionFree':ccd,'exception':exception,'vertices':len(P),'edges':len(edges),'faces':len(F),'nativeCCD':'TightInclusionCCD tolerance1e-8 max_iterations1e6 conservative_rescaling.8','elapsedSeconds':time.monotonic()-start,'peakRSSBytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'limits':['Native fullmesh query, not semantic hand/body clearance or visual acceptance.','CCD is straight sourcevertex-to-exportedvertex motion, not actual bending/rigging/physics.','Coplanar projected alltriangle overlap verification remains separate.']}
(E/'collision-report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
