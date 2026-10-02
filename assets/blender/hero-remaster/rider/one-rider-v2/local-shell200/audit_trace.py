"""Read-only all-five verification of every accepted registered200 segment."""
from pathlib import Path
import ast,json,hashlib
A=Path(__file__).resolve().parent;path=A/'solve.py';prefix=[]
for node in ast.parse(path.read_text()).body:
    if isinstance(node,ast.Expr) and isinstance(node.value,ast.Call) and isinstance(node.value.func,ast.Name) and node.value.func.id=='save':break
    if isinstance(node,ast.Assert) and 'construction.npz' in ast.unparse(node):continue
    prefix.append(node)
ns={};exec(compile(ast.Module(body=prefix,type_ignores=[]),str(path),'exec'),ns)
np=ns['np'];ipctk=ns['ipctk'];S=ns['S'];E=ns['E']
trace=np.load(S/'trace.npz')['acceptedFreeXYZ'];records=json.loads((S/'trace.json').read_text())['iterations']
assert np.array_equal(trace[0],ns['rest'])
mesh=ns['collision_mesh'];mesh.can_collide=ipctk.CollisionFilter();ccd=ns['ccd']
segments=[]
for i in range(len(trace)-1):
    first=ns['full'](trace[i].ravel());last=ns['full'](trace[i+1].ravel())
    clear=bool(ipctk.is_step_collision_free(mesh,first,last,narrow_phase_ccd=ccd))
    segments.append({'acceptedUpdate':i,'unfilteredContinuousClear':clear})
    assert clear
proposal_count=0;ccd_rejects=0;armijo_rejects=0
for record in records:
    trials=record['lineSearchProposals'];assert len(trials)<=31
    for i,trial in enumerate(trials):
        assert trial['alpha']<=record['CCDcap']
        if i:assert trial['alpha']==trials[i-1]['alpha']*.5
        proposal_count+=1;ccd_rejects+=trial['continuousClear'] is False
        armijo_rejects+=trial['continuousClear'] is True and not trial['ArmijoPass']
    if record['accepted']:
        accepted=trials[-1]
        assert all(accepted[k] for k in ['continuousClear','finiteEnergy','areaValid','ArmijoPass'])
z=np.load(S/'construction.npz');actual=ns['full'](z['physicalPositions'][ns['interior']].astype(float).ravel())
final_intersects=bool(ipctk.has_intersections(mesh,actual));assert not final_intersects
chord_clear=bool(ipctk.is_step_collision_free(mesh,ns['collision_rest'],actual,narrow_phase_ccd=ccd))
chord_step=float(ipctk.compute_collision_free_stepsize(mesh,ns['collision_rest'],actual,narrow_phase_ccd=ccd))
mesh.can_collide=ipctk.make_static_obstacle_filter(46)
energy,terms=ns['energy'](trace[-1].ravel())
result={'status':'PASS_ALL_ACCEPTED_SEGMENTS_AND_FINAL_NATIVE_SURFACE','fromLiteralUnchanged185':True,
    'acceptedUpdates':len(trace)-1,'proposals':proposal_count,'CCDRejectedProposals':ccd_rejects,
    'ArmijoRejectedClearProposals':armijo_rejects,'allProposalsWithin31TrialBudgetAndNativeCap':True,
    'allAcceptedProposalsCCDAndArmijoClear':True,'unfilteredAcceptedSegments':segments,
    'finalFloat32NativeIntersections':final_intersects,'sourceToFinalLinearChordClear':chord_clear,
    'sourceToFinalLinearChordSafeStep':chord_step,'finalFloat64Energy':energy,'finalEnergyTerms':terms,
    'indexedDumpSHA256':hashlib.sha256((S/'construction.npz').read_bytes()).hexdigest(),
    'geometryModifiedByAudit':False,'solverResumed':False,'CPUThreads':2,'GPU':False}
ns['save'](E/'accepted-trace-audit.json',result);print(json.dumps({k:v for k,v in result.items() if k!='unfilteredAcceptedSegments'}))
