"""Check frozen admission results against every strict44 triangle pair."""
import os
for key in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','VECLIB_MAXIMUM_THREADS'): os.environ[key]='2'
from pathlib import Path
import importlib.util, json, hashlib
import numpy as np
import ipctk
R=Path('/Users/raynos/projects/games/rockhop')
B=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2')
E=R/'docs/evidence/hero-remaster/one-rider-v2/ipc-admission197'
settings=json.loads((E/'inputs-and-settings.json').read_text())
report=json.loads((E/'report.json').read_text())
events=json.loads((E/'actual-trajectory.json').read_text())['collisionEvents']
pairs=json.loads((E/'frozen44-comparison.json').read_text())
source=B/'source-preserving-garment185/operator/rider.glb';dump=B/'source-star196/construction.npz'
for path in (source,dump): assert hashlib.sha256(path.read_bytes()).hexdigest()==report['pins'][str(path)]['sha256']
reader=R/'assets/blender/hero-remaster/rider/one-rider-v2/candidate-handoff170/map_candidate.py'
spec=importlib.util.spec_from_file_location('reader',reader);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
g=module.GLB(source);z=np.load(dump);world=module.worlds(g.j)
ps=[];ys=[];fs=[];offset=0
for mi,m in enumerate(g.j['meshes']):
    node=next(i for i,n in enumerate(g.j['nodes']) if n.get('mesh')==mi)
    for pi,p in enumerate(m['primitives']):
        a=g.array(p['attributes']['POSITION']);f=g.array(p['indices']).reshape(-1,3).astype(np.int64);n=a
        if (mi,pi)==(0,0):
            _,q=np.unique(a,axis=0,return_inverse=True);n=z['physicalPositions'][q]
        ps.append((np.c_[a,np.ones(len(a))]@world[node].T)[:,:3]);ys.append((np.c_[n,np.ones(len(n))]@world[node].T)[:,:3]);fs.append(f+offset);offset+=len(a)
raw=np.concatenate(ps);end=np.concatenate(ys)
X,first,row=np.unique(raw,axis=0,return_index=True,return_inverse=True);Y=end[first]
assert np.array_equal(Y[row],end)
order=np.array(settings['collisionVertexToCanonicalXYZAliasID']);inverse=np.empty(len(order),np.int64);inverse[order]=np.arange(len(order))
X=X[order];Y=Y[order];F=inverse[row[np.concatenate(fs)]].astype(np.int32)
Ed=np.unique(np.sort(np.concatenate([F[:,[0,1]],F[:,[1,2]],F[:,[2,0]]]),axis=1),axis=0).astype(np.int32)
for pair in pairs['pairs']:
    i,j=pair['globalFaces'];a=set(map(int,F[i]));b=set(map(int,F[j]));coverage=[]
    for n,e in enumerate(events):
        if e['kind']=='fv':
            face=e['faceID'];vertex=e['vertexIDs'][0]
            hit=(face==i and vertex in b) or (face==j and vertex in a)
        elif e['kind']=='ee':
            u,v=[set(map(int,Ed[k])) for k in e['edgeIDs']]
            hit=(u<=a and v<=b) or (u<=b and v<=a)
        else: hit=False
        if hit: coverage.append(n)
    pair['nativeCCDHitEventIndices']=coverage
covered=sum(bool(p['nativeCCDHitEventIndices']) for p in pairs['pairs'])
assert covered==44, ('uncovered strict triangle pairs',covered)
ipctk.set_num_threads(2);mesh=ipctk.CollisionMesh(X,Ed,F)
ccd=ipctk.TightInclusionCCD(tolerance=1e-8,max_iterations=1000000,conservative_rescaling=.8)
step=report['localReportedSafeStep'];prefix=X+step*(Y-X)
checks={'all44HaveNativeCCDHit':True,'all44EndpointStrict':pairs['all44EndpointStrict'],
    'strict44SourceCrossings':pairs['sourceStrictInFrozen44'],
    'fullDefaultStaticStep':ipctk.compute_collision_free_stepsize(mesh,X,X,narrow_phase_ccd=ccd),
    'fullDefaultSourceTo196SafeStep':ipctk.compute_collision_free_stepsize(mesh,X,Y,narrow_phase_ccd=ccd),
    'fullDefaultReportedPrefixCollisionFree':ipctk.is_step_collision_free(mesh,X,prefix,narrow_phase_ccd=ccd),
    'fullDefaultEndpointStepCollisionFree':ipctk.is_step_collision_free(mesh,X,Y,narrow_phase_ccd=ccd),
    'all168ExactlyIncidentToReleased46':np.array_equal(np.flatnonzero(np.any(F[:len(z['sourceIndices'])]<46,axis=1)),z['changedSourceFaceIDs'])}
assert checks['fullDefaultStaticStep']==1 and checks['fullDefaultReportedPrefixCollisionFree'] and not checks['fullDefaultEndpointStepCollisionFree']
assert checks['all168ExactlyIncidentToReleased46']
assert checks['fullDefaultSourceTo196SafeStep']==step
# Admission of actual-source local barrier derivatives, without deformation.
mesh.can_collide=ipctk.make_static_obstacle_filter(46)
collisions=ipctk.NormalCollisions();collisions.build(mesh,X,1e-4)
barrier=ipctk.BarrierPotential(1e-4,1000.)
energy=float(barrier(collisions,mesh,X));gradient=barrier.gradient(collisions,mesh,X)
checks['actualSourceLocalBarrierEnergy']=energy
checks['actualSourceLocalBarrierGradientNorm']=float(np.linalg.norm(gradient))
checks['actualSourceLocalBarrierFinite']=bool(np.isfinite(energy) and np.isfinite(gradient).all())
assert checks['actualSourceLocalBarrierFinite']
pairs['checks']=checks
(E/'all44-native-coverage.json').write_text(json.dumps(pairs,indent=2)+'\n')
report['status']='CPU_IPC_CAPABILITY_ADMITTED_NO_SOLVER_OR_CANDIDATE'
report['verification']=checks
(E/'report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(checks))
