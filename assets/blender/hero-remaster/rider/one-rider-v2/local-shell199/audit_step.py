"""Read-only reconstruction of the stopped proposal; never accepts an update."""
import ast,json,hashlib
from pathlib import Path
A=Path(__file__).resolve().parent
path=A/'solve.py';tree=ast.parse(path.read_text());prefix=[]
for node in tree.body:
    if isinstance(node,ast.Expr) and isinstance(node.value,ast.Call) and isinstance(node.value.func,ast.Name) and node.value.func.id=='save':break
    if isinstance(node,ast.Assert) and 'construction.npz' in ast.unparse(node):continue
    prefix.append(node)
ns={};exec(compile(ast.Module(body=prefix,type_ignores=[]),str(path),'exec'),ns)
np=ns['np'];ipctk=ns['ipctk'];dump=ns['S']/'construction.npz';z=np.load(dump)
x=z['finalFreeXYZFloat64'].ravel()
value,terms,r,cg,ch=ns['energy'](x,True);J=ns['jacobian'](x)
gradient=J.T@r+cg;H=J.T@J+ch+1e-8*np.eye(138)
direction=ns['spd_solve'](H,-gradient,assume_a='pos')
current=ns['full'](x);proposed=ns['full'](x+direction)
mesh=ns['collision_mesh'];ccd=ns['ccd']
cap=ipctk.compute_collision_free_stepsize(mesh,current,proposed,narrow_phase_ccd=ccd)
queries=[]
for ratio in [1.,.5,.25,.125]:
    trial=current+cap*ratio*(proposed-current)
    queries.append({'capRatio':ratio,'clear':ipctk.is_step_collision_free(mesh,current,trial,narrow_phase_ccd=ccd),
        'endIntersects':ipctk.has_intersections(mesh,trial),
        'reportedStepWithinCappedSegment':ipctk.compute_collision_free_stepsize(mesh,current,trial,narrow_phase_ccd=ccd)})
mesh.can_collide=ipctk.CollisionFilter()
fullcap=ipctk.compute_collision_free_stepsize(mesh,current,proposed,narrow_phase_ccd=ccd)
fullclear=ipctk.is_step_collision_free(mesh,current,current+cap*(proposed-current),narrow_phase_ccd=ccd)
float32final=ns['full'](z['physicalPositions'][ns['interior']].astype(float).ravel())
actual_final={'unfilteredHasIntersections':ipctk.has_intersections(mesh,float32final),
    'unfilteredSourceToFinalStep':ipctk.compute_collision_free_stepsize(mesh,ns['collision_rest'],float32final,narrow_phase_ccd=ccd),
    'unfilteredSourceToFinalClear':ipctk.is_step_collision_free(mesh,ns['collision_rest'],float32final,narrow_phase_ccd=ccd)}
mesh.can_collide=ipctk.make_static_obstacle_filter(46)
candidates=ipctk.Candidates();candidates.build(mesh,current,current+cap*(proposed-current));events=[]
p0_ids={tuple(position.astype(float)):i for i,position in enumerate(ns['U'])}
for kind,values in [('fv',candidates.fv_candidates),('ee',candidates.ee_candidates)]:
    for candidate in values:
        hit,toi=candidate.ccd(candidate.dof(current,ns['CE'],ns['CF']),candidate.dof(current+cap*(proposed-current),ns['CE'],ns['CF']),narrow_phase_ccd=ccd)
        if hit:
            ids=[int(v) for v in candidate.vertex_ids(ns['CE'],ns['CF']) if v>=0]
            events.append({'kind':kind,'vertices':ids,
                'sourceP0PhysicalIDs':[p0_ids.get(tuple(ns['collision_rest'][v])) for v in ids],
                'literalSourceXYZ':ns['collision_rest'][ids].tolist(),
                'acceptedStartXYZ':current[ids].tolist(),
                'cappedQueryXYZ':(current+cap*(proposed-current))[ids].tolist(),
                'reportedTOI':float(toi),'sourceDistanceSquared':float(candidate.compute_distance(current,ns['CE'],ns['CF']))})
report={'status':'READ_ONLY_DIAGNOSTIC_NO_SOLVER_RESUME',
    'finalAcceptedFloat64SourceIntersects':ipctk.has_intersections(mesh,current),
    'nextDirectionNorm':float(np.linalg.norm(direction)),'nextEnergy':value,'terms':terms,
    'gradientNorm':float(np.linalg.norm(gradient)),'slope':float(gradient@direction),
    'reportedFilteredCap':float(cap),'reportedUnfilteredCap':float(fullcap),
    'unfilteredCappedSegmentClear':fullclear,'halvedCappedSegmentQueries':queries,
    'cappedSegmentCandidateEvents':events,'actualFloat32Final':actual_final,
    'candidateDumpUnmodified':hashlib.sha256(dump.read_bytes()).hexdigest(),
    'solverResumed':False,'newCandidate':False}
ns['save'](ns['E']/'ccd-stop-diagnostic.json',report)
print(json.dumps(report))
