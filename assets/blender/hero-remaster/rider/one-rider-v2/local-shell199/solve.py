"""Exactly one registered local shell solve; no coefficient or domain tuning."""
import os
for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','VECLIB_MAXIMUM_THREADS'):os.environ[k]='2'
from common import *
import importlib.util
import ipctk
from scipy.linalg import solve as spd_solve
ipctk.set_num_threads(2)
C,a,F,U,q,c,alias,graph,star,path,sep=source()
assert not (S/'construction.npz').exists() and not (E/'attempt.json').exists()
removed=np.array(star['removedSourceFaceIDs'],np.int64)
interior=np.array(c['freePhysicalIDs'],np.int64);boundary=star['orientedFillBoundaryPhysicalIDs'];PF=q[F]
assert len(interior)==46 and set(PF[removed].ravel())-set(boundary)==set(interior)
rows=np.flatnonzero(np.isin(q,interior));assert len(rows)==88
assert all(v['incidentRetainedSourceFaceIDs']==[] for v in alias['sourceRowAliases'].values())
lengths=np.linalg.norm(np.diff(U[path].astype(float),axis=0),axis=1)
cumulative=np.r_[0.,np.cumsum(lengths,dtype=np.float64)];stations=cumulative/cumulative[-1]
u={int(pid):float(t) for pid,t in zip(path,stations)}
u[4041]=float(np.mean([u[i] for i in [3674,3717,4279,4393]]))
target=np.array([float(U[1488,1])+u[int(pid)]*(float(U[13448,1])-float(U[1488,1])) for pid in interior])
rest=U[interior].astype(float);target_xyz=rest.copy();target_xyz[:,1]=target
prior=np.load(B/'source-star196/construction.npz')
assert np.array_equal(target.astype(np.float32),prior['physicalPositions'][interior,1])
# Exact source metric in a tangent plane with positive second coordinate.
source_tri=U[PF[removed]].astype(float)
e0=source_tri[:,1]-source_tri[:,0];e1=source_tri[:,2]-source_tri[:,0]
ell=np.linalg.norm(e0,axis=1);proj=np.einsum('ij,ij->i',e0,e1)/ell
height=np.linalg.norm(np.cross(e0,e1),axis=1)/ell
Dm=np.zeros((len(removed),2,2));Dm[:,0,0]=ell;Dm[:,0,1]=proj;Dm[:,1,1]=height
invDm=np.linalg.inv(Dm);A0=.5*ell*height;assert np.all(A0>1e-12)
# Every two-face source edge incident to the released source168 disk.
edgeowners=edges(PF);hinges=[]
for edge,owners in sorted(edgeowners.items()):
    if len(owners)!=2 or not any(fi in set(removed) for fi,_ in owners):continue
    fi,positive=owners[0];fj,_=owners[1];i,j=edge if positive else edge[::-1]
    hinges.append((i,j,fi,fj))
hinges=np.array(hinges,np.int64)
faceids=np.unique(np.r_[removed,hinges[:,2:].ravel()])
physical_ids=np.unique(PF[faceids]);local_map={int(pid):i for i,pid in enumerate(physical_ids)}
free_local=np.array([local_map[int(pid)] for pid in interior]);local_rest=U[physical_ids].astype(float)
triids=np.array([[local_map[int(pid)] for pid in PF[fi]] for fi in faceids])
face_map={int(fi):i for i,fi in enumerate(faceids)}
region_idx=np.array([face_map[int(fi)] for fi in removed])
h0=np.array([face_map[int(fi)] for fi in hinges[:,2]])
h1=np.array([face_map[int(fi)] for fi in hinges[:,3]])
he=np.array([[local_map[int(i)],local_map[int(j)]] for i,j in hinges[:,:2]])
edge_length=np.linalg.norm(local_rest[he[:,1]]-local_rest[he[:,0]],axis=1)
wrap=lambda x:(x+np.pi)%(2*np.pi)-np.pi
def geometry(x):
    pp=local_rest.copy();pp[free_local]=x.reshape(46,3)
    tt=pp[triids];vectors=np.cross(tt[:,1]-tt[:,0],tt[:,2]-tt[:,0]);lens=np.linalg.norm(vectors,axis=1)
    if not np.isfinite(pp).all() or np.any(lens*.5<=1e-12):raise ValueError('zero/nearzero local triangle area')
    normals=vectors/lens[:,None];edge=pp[he[:,1]]-pp[he[:,0]];edge/=np.linalg.norm(edge,axis=1)[:,None]
    angles=np.arctan2(np.einsum('ij,ij->i',edge,np.cross(normals[h0],normals[h1])),np.einsum('ij,ij->i',normals[h0],normals[h1]))
    return tt[region_idx],angles,lens[region_idx]*.5
theta0=geometry(rest.ravel())[1]
slices={};cursor=0
for name,n in [('target',46),('XZ',92),('membrane',672),('bending',len(hinges))]:slices[name]=slice(cursor,cursor+n);cursor+=n
def residual(x):
    xyz=x.reshape(46,3);tt,theta,_=geometry(x)
    Ds=np.stack([tt[:,1]-tt[:,0],tt[:,2]-tt[:,0]],axis=2);deformation=Ds@invDm
    metric=np.swapaxes(deformation,1,2)@deformation-np.eye(2)
    return np.r_[(xyz[:,1]-target)/np.sqrt(46),
        (np.sqrt(.01/46)*(xyz[:,[0,2]]-rest[:,[0,2]])).ravel(),
        (np.sqrt(.01*A0)[:,None,None]*metric).ravel(),
        np.sqrt(.0001*edge_length)*wrap(theta-theta0)]
def jacobian(x):
    jac=np.empty((cursor,138));epsilon=1e-6
    for k in range(138):
        delta=np.zeros(138);delta[k]=epsilon
        jac[:,k]=(residual(x+delta)-residual(x-delta))/(2*epsilon)
    return jac
# All-five immutable collision mesh, active-first exact XYZ physical aliases.
reader=R/'assets/blender/hero-remaster/rider/one-rider-v2/candidate-handoff170/map_candidate.py';pin(reader)
spec=importlib.util.spec_from_file_location('reader',reader);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
glb=module.GLB(SOURCE);world=module.worlds(glb.j);allpos=[];allfaces=[];offset=0
for mi,meshj in enumerate(glb.j['meshes']):
    nodes=[i for i,n in enumerate(glb.j['nodes']) if n.get('mesh')==mi];assert len(nodes)==1
    # Frozen admission independently proved this exact world mapping.
    assert np.array_equal(world[nodes[0]],np.eye(4))
    for pi,p in enumerate(meshj['primitives']):
        pos=glb.array(p['attributes']['POSITION']);ff=glb.array(p['indices']).reshape(-1,3).astype(np.int64)
        allpos.append(pos.astype(float));allfaces.append(ff+offset);offset+=len(pos)
raw=np.concatenate(allpos);collision_rest,row=np.unique(raw,axis=0,return_inverse=True)
lookup={tuple(p):i for i,p in enumerate(collision_rest)}
free_global=np.array([lookup[tuple(U[pid].astype(float))] for pid in interior]);assert len(set(free_global))==46
order=np.r_[free_global,np.array([i for i in range(len(collision_rest)) if i not in set(free_global)])]
inverse=np.empty(len(order),np.int64);inverse[order]=np.arange(len(order));collision_rest=collision_rest[order]
CF=inverse[row[np.concatenate(allfaces)]].astype(np.int32)
CE=np.unique(np.sort(np.concatenate([CF[:,[0,1]],CF[:,[1,2]],CF[:,[2,0]]]),axis=1),axis=0).astype(np.int32)
collision_mesh=ipctk.CollisionMesh(collision_rest,CE,CF)
assert not ipctk.has_intersections(collision_mesh,collision_rest)
collision_mesh.can_collide=ipctk.make_static_obstacle_filter(46)
ccd=ipctk.TightInclusionCCD(tolerance=1e-8,max_iterations=1000000,conservative_rescaling=.8)
barrier=ipctk.BarrierPotential(.001,1e9)
def full(x):
    result=collision_rest.copy();result[:46]=x.reshape(46,3);return result
def contact(X,derivatives=False):
    collisions=ipctk.NormalCollisions();collisions.build(collision_mesh,X,.001)
    energy=float(barrier(collisions,collision_mesh,X))
    if not derivatives:return energy
    grad=barrier.gradient(collisions,collision_mesh,X)[:138]
    H=barrier.hessian(collisions,collision_mesh,X)[:138,:138].toarray();H=(H+H.T)/2
    eigen,V=np.linalg.eigh(H);H=(V*np.maximum(eigen,0))@V.T
    return energy,grad,H
def energy(x,derivatives=False):
    r=residual(x);X=full(x)
    terms={name:.5*float(r[sl]@r[sl]) for name,sl in slices.items()}
    if derivatives:
        terms['contact'],cg,ch=contact(X,True);return float(sum(terms.values())),terms,r,cg,ch
    terms['contact']=contact(X);return float(sum(terms.values())),terms
# Residual/analytic-contact consistency before the one solve is registered.
x=rest.ravel().copy();r=residual(x);J=jacobian(x)
direction=np.sin(np.arange(138)+.25);direction/=np.linalg.norm(direction);eps=1e-6
fd=(residual(x+eps*direction)-residual(x-eps*direction))/(2*eps)
jerror=float(np.linalg.norm(fd-J@direction)/max(np.linalg.norm(fd),1e-30))
target_gradient=(J.T@r).reshape(46,3);expected=np.zeros((46,3));expected[:,1]=(rest[:,1]-target)/46
analytic_error=float(np.max(abs(target_gradient-expected)))
assert jerror<1e-5 and analytic_error<1e-8
assert np.max(abs(r[slices['membrane']]))<1e-12 and np.max(abs(r[slices['bending']]))==0
# Nonzero actual triangle barrier fixture validates flattened free-gradient layout.
fixture=np.array([[0.,0.,0.],[1.,0.,0.],[.5,1.,0.],[.1,.1,.0005],[.9,.1,.0005],[.5,.9,.0005]])
fm=ipctk.CollisionMesh(fixture,np.array([[0,1],[1,2],[0,2],[3,4],[4,5],[3,5]],np.int32),np.array([[0,1,2],[3,4,5]],np.int32))
fc=ipctk.NormalCollisions();fc.build(fm,fixture,.001);fg=barrier.gradient(fc,fm,fixture)
fdir=np.zeros_like(fixture);fdir[3:,2]=1;feps=1e-8
ffd=(float(barrier(fc,fm,fixture+feps*fdir))-float(barrier(fc,fm,fixture-feps*fdir)))/(2*feps)
fanalytic=float(fg@fdir.ravel());ferror=abs(ffd-fanalytic)/abs(ffd)
assert ferror<1e-5 and np.isfinite(fg).all()
static_step=ipctk.compute_collision_free_stepsize(collision_mesh,full(x),full(x),narrow_phase_ccd=ccd);assert static_step==1
check();save(E/'preflight.json',{'status':'PASS_BEFORE_ONE_SOLVE','residualRows':cursor,'hinges':len(hinges),'sourceFaces':168,'freeXYZ':138,'sourceAreaMinimumM2':float(A0.min()),'jacobianDirectionalRelativeError':jerror,'targetAnalyticGradientMaximumError':analytic_error,'nonzeroTriangleBarrierGradientRelativeError':ferror,'sourceStaticCCDStep':static_step,'fullSourceIntersectionFree':True,'CPUThreads':2,'GPU':False,'inputPins':pins})
save(E/'attempt.json',{'status':'RUNNING_REGISTERED_ONE199_SOLVE','attemptCount':1,'sourceSHA256':SHA,'contractSHA256':pins[str(CONTRACT)]['sha256'],'geometryGenerated':False,'coefficientsRetuned':False})
trace=[];iterates=[x.reshape(46,3).copy()];stop='maximum_iterations';stalls=0
def metrics(x):
    tt,_,ar=geometry(x);edge=np.stack([tt[:,1]-tt[:,0],tt[:,2]-tt[:,1],tt[:,0]-tt[:,2]],axis=1)
    sourceedge=np.stack([source_tri[:,1]-source_tri[:,0],source_tri[:,2]-source_tri[:,1],source_tri[:,0]-source_tri[:,2]],axis=1)
    strain=np.linalg.norm(edge,axis=2)/np.linalg.norm(sourceedge,axis=2)
    return {'minimumAreaM2':float(ar.min()),'edgeRatioRange':[float(strain.min()),float(strain.max())],'maximumTargetErrorM':float(np.max(abs(x.reshape(46,3)[:,1]-target)))}
try:
    for iteration in range(200):
        check();value,terms,r,cg,ch=energy(x,True);J=jacobian(x);gradient=J.T@r+cg
        gn=float(np.linalg.norm(gradient));current=full(x)
        assert np.isfinite(value) and np.isfinite(gradient).all()
        if ipctk.has_intersections(collision_mesh,current):stop='invalid_start_intersection';break
        if metrics(x)['maximumTargetErrorM']<=.002 and gn<=1e-6:stop='target_proxy_and_gradient';break
        H=J.T@J+ch+1e-8*np.eye(138);p=spd_solve(H,-gradient,assume_a='pos')
        slope=float(gradient@p);fallback=False
        if not np.isfinite(p).all() or slope>=0:p=-gradient;slope=-gn*gn;fallback=True
        proposed=full(x+p)
        cap=ipctk.compute_collision_free_stepsize(collision_mesh,current,proposed,narrow_phase_ccd=ccd)
        alpha=float(cap);accepted=False;halvings=0
        for halvings in range(31):
            trial=x+alpha*p
            if alpha<=0:break
            # Each Armijo trial remains inside the CCD-capped segment, and is
            # independently checked as a continuous source-to-trial step.
            if not ipctk.is_step_collision_free(collision_mesh,current,full(trial),narrow_phase_ccd=ccd):raise ValueError('CCD capped trial is not clear')
            try:newvalue,newterms=energy(trial)
            except ValueError:newvalue=float('inf');newterms={}
            if np.isfinite(newvalue) and newvalue<=value+1e-4*alpha*slope:accepted=True;break
            alpha*=.5
        record={'iteration':iteration,'energyBefore':value,'termsBefore':terms,'gradientNorm':gn,'CCDcap':float(cap),'alpha':alpha,'halvings':halvings,'accepted':accepted,'gradientFallback':fallback,'elapsedSeconds':time.monotonic()-start,'anonymousGB':mem[-1]}
        if not accepted:trace.append(record);stop='failed_line_search';break
        reduction=(value-newvalue)/max(abs(value),1e-30);stalls=stalls+1 if reduction<1e-8 else 0
        x=trial;iterates.append(x.reshape(46,3).copy());record.update(energyAfter=newvalue,termsAfter=newterms,relativeReduction=reduction,**metrics(x));trace.append(record)
        if iteration%10==0:print(json.dumps({'iteration':iteration,'energy':newvalue,'targetErrorM':record['maximumTargetErrorM'],'CCDcap':cap,'alpha':alpha,'seconds':record['elapsedSeconds']}),flush=True)
        if stalls>=5:stop='five_relative_reductions_below1e8';break
except (ValueError,AssertionError,np.linalg.LinAlgError) as error:
    stop='bounded_stop:'+str(error)
# Exactly one final Float32 result, no retry after the construction.
physical=U.copy();physical[interior]=x.reshape(46,3).astype(np.float32)
np.savez_compressed(S/'trace.npz',freePhysicalIDs=interior,acceptedFreeXYZ=np.array(iterates),targetY=target)
save(S/'trace.json',{'stop':stop,'iterations':trace,'acceptedIterates':len(iterates),'finalFloat64Metrics':metrics(x),'elapsedSeconds':time.monotonic()-start,'anonymousGBSamples':mem})
attrs={s:np.concatenate([v,v[rows].copy()]) for s,v in a.items()};attrs['POSITION'][len(a['POSITION']):]=physical[q[rows]]
clones={int(row):int(len(a['POSITION'])+i) for i,row in enumerate(rows)};indices=F.astype(np.int64).copy();cornerRecords=[]
for fi in removed:
    for lane,row in enumerate(F[fi]):
        if int(row) in clones:
            indices[fi,lane]=clones[int(row)];cornerRecords.append({'sourceFace':int(fi),'lane':lane,'sourceRow':int(row),'newRow':clones[int(row)],'physicalID':int(q[row])})
# Area-weighted normals preserve each source normal crease chart separately.
tri=attrs['POSITION'][indices].astype(float);vectors=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);groups=defaultdict(list)
for row in rows:groups[(int(q[row]),tuple(a['NORMAL'][row].view(np.uint32).tolist()))].append(int(row))
normalReceipts=[];normalFailures=[];normalTurns=[]
for (pid,bits),sr in sorted(groups.items()):
    fs=sorted({int(fi) for fi in removed for row in F[fi] if int(q[row])==pid and tuple(a['NORMAL'][row].view(np.uint32).tolist())==bits})
    total=np.zeros(3)
    for fi in fs:total+=vectors[fi]
    norm=float(np.linalg.norm(total));n=np.zeros(3,np.float32) if norm==0 else (total/norm).astype(np.float32)
    dot=float(n.astype(float)@a['NORMAL'][sr[0]].astype(float))
    if norm==0:normalFailures.append({'type':'zero_group_area_normal','physicalID':pid})
    if dot<=0:normalTurns.append({'physicalID':pid,'sourceRows':sr,'newDotOriginal':dot})
    for row in sr:attrs['NORMAL'][clones[row]]=n
    normalReceipts.append({'physicalID':pid,'originalNormalBits':bits,'originalRows':sr,'newRows':[clones[row] for row in sr],'sourceFaceIDs':fs,'sumAreaVector':total.tolist(),'sumLength':norm,'newNormal':n.tolist(),'newDotOriginal':dot})
morphs=[]
for targetj in C.d['meshes'][0]['primitives'][0].get('targets',[]):morphs.append({s:np.concatenate([C.acc(ai),C.acc(ai)[rows]]) for s,ai in targetj.items()})
dump={'positions':attrs['POSITION'],'indices':indices,'sourceIndices':F,'sourcePhysicalPositions':U,'physicalPositions':physical,'attributeRowPhysicalIDs':np.r_[q,q[rows]],'clonedSourceRows':rows,'clonedNewRows':np.arange(len(a['POSITION']),len(attrs['POSITION'])),'changedSourceFaceIDs':removed,'pathPhysicalIDs':np.array(path),'pathLengthsFloat64':lengths,'pathCumulativeFloat64':cumulative,'pathStationsFloat64':stations,'interiorPhysicalIDs':interior,'interiorStationsFloat64':np.array([u[int(i)] for i in interior]),'boundaryPhysicalIDs':np.array(boundary),'targetYFloat64':target,'finalFreeXYZFloat64':x.reshape(46,3)}
for s,v in attrs.items():dump['attribute_'+s]=v
for i,targetj in enumerate(morphs):
    for s,v in targetj.items():dump['morph_'+str(i)+'_'+s]=v
np.savez_compressed(S/'construction.npz',**dump)
save(S/'construction-provenance.json',{'sourceSHA256':SHA,'contractSHA256':pins[str(CONTRACT)]['sha256'],'recipeSHA256':sha(Path(__file__).read_bytes()),'cornerProvenance':cornerRecords,'cloneRows':[{'sourceRow':row,'newRow':clones[row],'physicalID':int(q[row])} for row in rows.tolist()],'normalGroups':normalReceipts,'constructionFailures':normalFailures,'sourceNormalTurnsNotInversionCertificate':normalTurns,'boundaryNormals':'Literal original rows','inputs':pins})
summary={'status':'ONE199_FINAL_DUMP_PENDING_STATIC','attemptCount':1,'stop':stop,'acceptedUpdates':len(iterates)-1,'geometryGenerated':True,'GLBExported':False,'sourceSHA256':SHA,'dumpSHA256':sha((S/'construction.npz').read_bytes()),'traceSHA256':sha((S/'trace.npz').read_bytes()),'traceJSONSHA256':sha((S/'trace.json').read_bytes()),'finalFloat64Metrics':metrics(x),'normalZeroFailures':len(normalFailures),'normalTurnGroups':len(normalTurns),'elapsedSeconds':time.monotonic()-start,'anonymousGBRange':[min(mem),max(mem)],'CPUThreads':2,'GPU':False,'inputPins':pins}
save(E/'build-report.json',summary);save(E/'attempt.json',summary);print(json.dumps(summary),flush=True)
