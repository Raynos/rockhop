"""Minimal connected selected sleeve shell envelope under the actual native poses.

Every glove byte and every native field stays protected. The source's real
exterior sheet defines constraints; retained inner folds and caps follow
one connected deformation instead of being forced outside the glove. A discrete Dirichlet obstacle solve avoids independent bumps.
"""
import bpy, json, sys, time, hashlib, runpy
from pathlib import Path
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

HERE=Path(__file__).resolve().parent
D=runpy.run_path(str(HERE/'diagnose.py')); read,skin=D['read'],D['skin']
load_canonical=runpy.run_path(str(HERE/'canonical_cuff.py'))['load_canonical']

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def tree(p,f): return BVHTree.FromPolygons(p.tolist(),f.tolist(),all_triangles=True)
def hits(bvh,origin,direction,bound,epsilon):
    result=[]; traveled=0.; origin=np.asarray(origin,float); direction=np.asarray(direction,float)
    for _ in range(128):
        q,n,face,distance=bvh.ray_cast(Vector(origin+direction*traveled),Vector(direction),float(bound-traveled))
        if face is None: return result
        t=traveled+distance; result.append((t,float(np.asarray(n)@direction),int(face)))
        traveled=t+epsilon
        if traveled>=bound:return result
    raise AssertionError('Unresolved repeated shell intersections')

def barycentric(q,triangle):
    a,b,c=triangle;v0=b-a;v1=c-a;v2=q-a
    den=(v0@v0)*(v1@v1)-(v0@v1)**2
    if abs(den)<1e-20:return np.array([1.,0.,0.])
    v=((v1@v1)*(v2@v0)-(v0@v1)*(v2@v1))/den
    w=((v0@v0)*(v2@v1)-(v0@v1)*(v2@v0))/den
    weights=np.maximum([1-v-w,v,w],0.);return weights/weights.sum()

def load(root):
    receipt=json.loads((root/'intake.json').read_text()); comps={}
    for c in receipt['components']:
        a={k:read(root,c,k) for k in ['POSITION','JOINTS_0','WEIGHTS_0','indices','inverseBindMatrices']}
        a['indices']=a['indices'].reshape(-1,3); a['ib']=a.pop('inverseBindMatrices').reshape(-1,4,4).transpose(0,2,1).astype(float)
        a['names']=c['nativeJointNames']; comps[c['name']]=a
    return receipt,comps

def main(intake,rookie,pro,out):
    started=time.monotonic(); root=Path(intake); out=Path(out);assert not out.exists();out.mkdir(parents=True)
    receipt,comps=load(root); h=comps['RiderHoodie']; p=h['POSITION'].astype(float); f=h['indices']; names=h['names']
    h['JOINTS_0']=h['JOINTS_0'].copy()
    rest=np.linalg.inv(h['ib']); hoodie_tree=tree(p,f)
    classify,canonical=load_canonical(Path.cwd(),names)
    # Geometry seam identity is exact source POSITION identity, not spatial welding.
    unique,first,inverse=np.unique(p,axis=0,return_index=True,return_inverse=True)
    count=len(unique); required=np.zeros(count); domain=np.zeros(count,bool)
    source_fields=np.zeros((len(p),len(names)))
    for k in range(4):np.add.at(source_fields,(np.arange(len(p)),h['JOINTS_0'][:,k]),h['WEIGHTS_0'][:,k])
    seam_field_difference=float(np.max(abs(source_fields-source_fields[first[inverse]])))
    epsilon=float(8*np.max(np.spacing(h['POSITION'].astype(np.float32))))
    assert epsilon>0
    policies=[]; side_data={}
    for side in ['L','R']:
        g=comps['ActualSelectedGlove.'+side]; wrist=names.index('DEF-hand.'+side); distal=names.index('DEF-forearm.'+side+'.001')
        head=rest[wrist,:3,3]; axis=head-rest[distal,:3,3]; length=np.linalg.norm(axis);axis/=length
        allowed={names.index('DEF-forearm.'+side),distal,wrist,*[i for i,n in enumerate(names) if n.startswith('DEF-palm.') and n.endswith('.'+side)]}
        positive=source_fields>0; keep=np.array([all(int(i) in allowed for i in np.flatnonzero(row)) for row in positive])
        # Connected skin carrier is only the actual distal native forearm/wrist.
        keep &= (p-head)@axis >= -length
        ids=np.flatnonzero(np.isin(inverse,inverse[np.flatnonzero(keep)]))
        stations=(p[ids]-head)@axis; origins=head+stations[:,None]*axis
        radial=p[ids]-origins; radii=np.linalg.norm(radial,axis=1);directions=radial/radii[:,None]
        glove_min=float(((g['POSITION']-head)@axis).min()); glove_max=float(((g['POSITION']-head)@axis).max())
        ownership,body_face,body_distance,body_signed=classify(g['POSITION'],side)
        cuff_faces=np.flatnonzero(np.any(ownership[g['indices']],axis=1))
        cuff_rows=np.unique(g['indices'][cuff_faces]);gt=tree(g['POSITION'],g['indices'][cuff_faces])
        witnesses=[167304] if side=='L' else [74724,81481]
        assert all(i in cuff_faces for i in witnesses),'Actual observed cuff surface omitted'
        domain[inverse[ids]]=True
        local_faces=np.flatnonzero(np.all(np.isin(f,ids),axis=1));local=tree(p,f[local_faces])
        area=np.cross(p[f[:,1]]-p[f[:,0]],p[f[:,2]]-p[f[:,0]])
        normal=np.zeros_like(p)
        for corner in range(3):np.add.at(normal,f[:,corner],area)
        normal/=np.maximum(np.linalg.norm(normal,axis=1)[:,None],1e-30)
        _,_,_,hoodie_body_signed=classify(p[ids],side)
        exterior=np.zeros(len(ids),bool);outer_radius=np.zeros(len(ids));missing=[]
        bound=float(np.linalg.norm(p[ids].max(0)-p[ids].min(0)))
        for k,(o,d,r) in enumerate(zip(origins,directions,radii)):
            intersections=hits(local,o,d,bound,epsilon)
            outward=[row[0] for row in intersections if row[1]>0]
            if normal[ids[k]]@d>0:outward.append(r)
            if not outward:missing.append(int(ids[k]));continue
            outer_radius[k]=max(outward);exterior[k]=abs(r-outer_radius[k])<=epsilon*8 and hoodie_body_signed[k]>=0
        # A shared nearest rest cuff correspondence conditions only the selected
        # sleeve carrier. Actual glove fields and every native driver stay exact.
        transfer_faces=[];discarded=[]
        for row in ids:
            q,n,face,d=gt.find_nearest(Vector(p[row]));gf=g['indices'][cuff_faces[face]]
            bary=barycentric(np.asarray(q),g['POSITION'][gf].astype(float));field=np.zeros(len(names))
            for corner in range(3):
                for k in range(4):field[g['JOINTS_0'][gf[corner],k]]+=bary[corner]*g['WEIGHTS_0'][gf[corner],k]
            discarded.append(float(sum(field[i] for i in range(len(names)) if i not in allowed)))
            field[[i for i in range(len(names)) if i not in allowed]]=0
            assert field.sum()>0;field/=field.sum()
            top=np.argsort(-field,kind='stable')[:4];values=field[top];values/=values.sum()
            exact=values*65535;quantized=np.floor(exact).astype(np.uint16)
            for qid in np.argsort(-(exact-quantized),kind='stable')[:65535-int(quantized.sum())]:quantized[qid]+=1
            h['JOINTS_0'][row]=top;h['WEIGHTS_0'][row]=quantized.astype(float)/65535
            transfer_faces.append(int(cuff_faces[face]))
        side_data[side]={'g':g,'cuffFaces':cuff_faces,'ids':ids,'origins':origins,'directions':directions,'radii':radii,'exterior':exterior}
        policies.append({'side':side,'vertices':len(ids),'uniqueVertices':int(len(np.unique(inverse[ids]))),
            'nativeWrist':head.tolist(),'nativeForearmAxis':axis.tolist(),'nativeSegmentLengthMeters':float(length),
            'nativeStationMeters':[float(stations.min()),float(stations.max())],'gloveStationMeters':[glove_min,glove_max],
            'sourceExteriorRows':int(exterior.sum()),'retainedInternalRows':int((~exterior).sum()),
            'sourceWearerEmbeddedRows':int(np.sum(hoodie_body_signed<0)),
            'sourceExteriorRowIDs':ids[exterior].tolist(),'noOutwardSourceHitRows':missing,'quantizationClearanceMeters':epsilon,
            'hoodieCarrierCorrespondenceFaceIDsSHA256':hashlib.sha256(np.array(transfer_faces,dtype='<u4').tobytes()).hexdigest(),
            'discardedDigitFieldMassPercentiles':np.percentile(discarded,[0,50,100]).tolist(),
            'sourceOnlyCarrierNames':[names[i] for i in sorted(allowed)],
            'canonicalCuffFaces':len(cuff_faces),'canonicalCuffVertices':len(cuff_rows),
            'canonicalCuffFaceIDsSHA256':hashlib.sha256(cuff_faces.astype('<u4').tobytes()).hexdigest(),
            'canonicalCuffStationMeters':np.percentile((g['POSITION'][cuff_rows]-head)@axis,[0,50,100]).tolist(),
            'observedWitnessFacesIncluded':witnesses})
    reports={bike:json.loads(Path(path).read_text()) for bike,path in [('rookie',rookie),('pro',pro)]}
    progress={'accepted':False,'source':receipt['source'],'policies':policies,'canonical':canonical,'phase':'pose envelope','samples':[]}
    (out/'progress.json').write_text(json.dumps(progress,indent=2)+'\n')
    worst=np.zeros(count,dtype=int); processed=0
    for bike,report in reports.items():
        poses=report['played']['motionSamples'];assert len(poses)==241
        for pi,sample in enumerate(poses):
            byname={j['id']:j['worldMatrix'] for j in sample['joints']}
            world=np.array([byname[n] for n in names]).reshape(-1,4,4).transpose(0,2,1);mat=world@h['ib']
            for side,data in side_data.items():
                g=data['g'];gp=skin(g['POSITION'],g['JOINTS_0'],g['WEIGHTS_0'],mat);bvh=tree(gp,g['indices'][data['cuffFaces']])
                ids=data['ids'];m=np.zeros((len(ids),4,4))
                for k in range(4):m+=mat[h['JOINTS_0'][ids,k]]*h['WEIGHTS_0'][ids,k,None,None]
                origins=np.einsum('nij,nj->ni',m[:,:3,:],np.column_stack([data['origins'],np.ones(len(ids))]))
                direction=np.einsum('nij,nj->ni',m[:,:3,:3],data['directions']);scale=np.linalg.norm(direction,axis=1);direction/=scale[:,None]
                bound=float(np.linalg.norm(gp.max(0)-gp.min(0))+np.max(np.linalg.norm(origins-gp.mean(0),axis=1)))
                values=np.zeros(len(ids));intersected=0
                for k,(o,d) in enumerate(zip(origins,direction)):
                    if not data['exterior'][k]:continue
                    found=hits(bvh,o,d,bound,epsilon)
                    # Source-rest anatomical cuff face identity is transported
                    # unchanged, excluding unrelated posed fingers and palm.
                    outward=[row[0] for row in found]
                    if outward:
                        intersected+=1;glove_radius=max(outward)/scale[k]
                        values[k]=max(0.,glove_radius-data['radii'][k]+epsilon/scale[k])
                uid=inverse[ids];better=values>required[uid]
                worst[uid[better]]=processed
                np.maximum.at(required,uid,values)
                del bvh,gp
                progress['samples'].append({'bike':bike,'tick':sample['tick'],'side':side,'vertices':len(ids),
                    'gloveRayHits':intersected,'maxRequiredRestDisplacementMeters':float(values.max())})
            processed+=1
            if pi%20==0:
                progress.update(processedPoses=processed,elapsedSeconds=time.monotonic()-started)
                (out/'progress.json').write_text(json.dumps(progress,indent=2)+'\n')
                print(json.dumps({'bike':bike,'tick':sample['tick'],'processed':processed,'maxRequiredMeters':float(required.max())}),flush=True)
    # Positive edge weights yield a maximum principle. Solve the Dirichlet
    # obstacle problem: minimum edge-strain envelope over the connected cuff,
    # bounded below by every measured pose constraint; exterior is fixed zero.
    edges=np.concatenate([inverse[f[:,[0,1]]],inverse[f[:,[1,2]]],inverse[f[:,[2,0]]]])
    edges=np.sort(edges,axis=1);edges=np.unique(edges[edges[:,0]!=edges[:,1]],axis=0)
    distance=np.linalg.norm(unique[edges[:,1]]-unique[edges[:,0]],axis=1);weight=1/distance
    src=np.r_[edges[:,0],edges[:,1]];dst=np.r_[edges[:,1],edges[:,0]];ww=np.r_[weight,weight]
    degree=np.bincount(src,weights=ww,minlength=count);displacement=required.copy();iterations=0
    for iterations in range(20000):
        average=np.bincount(src,weights=ww*displacement[dst],minlength=count)/np.maximum(degree,1e-30)
        updated=np.where(domain,np.maximum(required,average),0.)
        error=np.max(abs(updated-displacement));displacement=updated
        if error<=epsilon/16:break
    else:raise AssertionError('Connected obstacle solve did not converge')
    assert np.all(displacement>=required) and np.all(displacement[~domain]==0)
    candidate=p.copy();row_delta=np.zeros(len(p));directions_all=np.zeros_like(p)
    for side,data in side_data.items():
        ids=data['ids'];row_delta[ids]=displacement[inverse[ids]];directions_all[ids]=data['directions']
        candidate[ids]+=row_delta[ids,None]*data['directions']
    original_area=np.cross(p[f[:,1]]-p[f[:,0]],p[f[:,2]]-p[f[:,0]])
    new_area=np.cross(candidate[f[:,1]]-candidate[f[:,0]],candidate[f[:,2]]-candidate[f[:,0]])
    changed=np.flatnonzero(np.any(candidate!=p,axis=1));affected=np.any(row_delta[f]>0,axis=1)
    original_lengths=np.linalg.norm(original_area,axis=1);new_lengths=np.linalg.norm(new_area,axis=1)
    nondegenerate=affected & (original_lengths>1e-20)
    dot=np.sum(original_area[nondegenerate]*new_area[nondegenerate],axis=1)
    area_ratio=new_lengths[nondegenerate]/original_lengths[nondegenerate]
    new_degenerate=int(np.sum(new_lengths[nondegenerate]<=1e-20))
    h['JOINTS_0'].astype('u1').tofile(out/'jointsAfter.bin')
    np.rint(h['WEIGHTS_0']*65535).astype('<u2').tofile(out/'weightsAfter.bin')
    np.savez(out/'patch.npz',positionsBefore=p,positionsAfter=candidate.astype(np.float32),changedRows=changed,
        requiredByUniqueRow=required,connectedDisplacementByUniqueRow=displacement,sourcePositionUniqueRows=first,
        sourcePositionToUnique=inverse,radialDirections=directions_all,sourceCarrierRowDisplacement=row_delta,worstPoseByUniqueRow=worst,jointsAfter=h['JOINTS_0'],weightsAfter=h['WEIGHTS_0'])
    result={'accepted':False,'schema':'selected-cuff-rest-envelope-v1','source':receipt['source'],'intakeSHA256':sha(root/'intake.json'),
        'recipeSHA256':sha(__file__),'playedReports':{b:{'path':str(path),'sha256':sha(path)} for b,path in [('rookie',rookie),('pro',pro)]},
        'policies':policies,'canonical':canonical,'sourceNativeFieldsExact':False,'gloveNativeFieldsExact':True,'hoodieCarrierConditioned':True,'allGloveBytesProtected':True,'native75RestAndAnimationExact':True,
        'sourceGeometrySeamFieldsUnchanged':False,'sourcePositionSeamCarrierMaxDifference':seam_field_difference,'poseCount':processed,'constraintSamples':len(progress['samples']),
        'hoodieChangedRows':len(changed),'hoodieMaxRestDisplacementMeters':float(row_delta.max()),
        'hoodieRequiredMaxMeters':float(required.max()),'hoodieRestDisplacementPercentilesMeters':np.percentile(row_delta[changed],[0,50,95,99,100]).tolist(),
        'affectedTriangles':int(affected.sum()),'nonpositiveAreaOrientationDots':int((dot<=0).sum()),
        'affectedInheritedZeroAreaTriangles':int(np.sum(affected & (original_lengths<=1e-20))),
        'newlyDegenerateTriangles':new_degenerate,
        'affectedAreaRatioPercentiles':np.percentile(area_ratio,[0,50,100]).tolist(),'obstacleIterations':iterations+1,
        'obstacleMaxStepMeters':float(error),'patch':{'path':str(out/'patch.npz'),'sha256':sha(out/'patch.npz')},
        'elapsedSeconds':time.monotonic()-started,
        'limits':['Finite rays at every selected cuff vertex in all482 recorded poses are construction constraints, not exhaustive triangle or unseen-pose proof.',
                  'Only the source outer radial sheet receives enclosure constraints. Retained internal cap/fold topology follows the connected displacement; no open-cloth topology or full remaster claim.',
                  'New moving clips and independent finite surface validation remain parent gates.']}
    (out/'report.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
    assert new_degenerate==0,'New degenerate source face rejects candidate'
    assert result['nonpositiveAreaOrientationDots']==0,'Source face inversion rejects candidate'

if __name__=='__main__':main(*sys.argv[sys.argv.index('--')+1:])
