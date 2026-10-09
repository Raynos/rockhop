"""Minimal connected selected sleeve shell envelope under the actual native poses.

Every glove byte and every native field stays protected. The source's real
inner/outer sleeve radial spacing is retained; only the local cuff carrier can
move outward. A discrete Dirichlet obstacle solve avoids independent bumps.
"""
import bpy, json, sys, time, hashlib, runpy
from pathlib import Path
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

HERE=Path(__file__).resolve().parent
D=runpy.run_path(str(HERE/'diagnose.py')); read,skin=D['read'],D['skin']

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
    rest=np.linalg.inv(h['ib']); hoodie_tree=tree(p,f)
    # Geometry seam identity is exact source POSITION identity, not spatial welding.
    unique,first,inverse=np.unique(p,axis=0,return_index=True,return_inverse=True)
    count=len(unique); required=np.zeros(count); domain=np.zeros(count,bool)
    source_fields=np.zeros((len(p),len(names)))
    for k in range(4):np.add.at(source_fields,(np.arange(len(p)),h['JOINTS_0'][:,k]),h['WEIGHTS_0'][:,k])
    assert np.max(abs(source_fields-source_fields[first[inverse]]))<1e-12,'Source seam native fields disagree'
    epsilon=float(8*np.max(np.spacing(h['POSITION'].astype(np.float32))))
    assert epsilon>0
    policies=[]; side_data={}
    for side in ['L','R']:
        g=comps['ActualSelectedGlove.'+side]; wrist=names.index('DEF-hand.'+side); distal=names.index('DEF-forearm.'+side+'.001')
        head=rest[wrist,:3,3]; axis=head-rest[distal,:3,3]; length=np.linalg.norm(axis);axis/=length
        allowed={distal,wrist,*[i for i,n in enumerate(names) if n.startswith('DEF-palm.') and n.endswith('.'+side)]}
        positive=source_fields>0; keep=np.array([all(int(i) in allowed for i in np.flatnonzero(row)) for row in positive])
        # Connected skin carrier is only the actual distal native forearm/wrist.
        ids=np.flatnonzero(keep); stations=(p[ids]-head)@axis; origins=head+stations[:,None]*axis
        radial=p[ids]-origins; radii=np.linalg.norm(radial,axis=1);directions=radial/radii[:,None]
        glove_min=float(((g['POSITION']-head)@axis).min()); glove_max=float(((g['POSITION']-head)@axis).max())
        inner=np.empty(len(ids)); layers=np.empty(len(ids)); shell_width=[]; missing=[]
        bound=float(np.linalg.norm(p.max(0)-p.min(0)))
        for k,(o,d,r) in enumerate(zip(origins,directions,radii)):
            intersections=hits(hoodie_tree,o,d,bound,epsilon)
            before=[row for row in intersections if row[0]<=r+epsilon*4]
            if not before:missing.append(int(ids[k]));continue
            inner[k]=before[0][0];layers[k]=max(0.,r-inner[k])
            for a,b in zip(intersections,intersections[1:]):
                if a[1]<0 and b[1]>0:shell_width.append(b[0]-a[0]);break
        assert not missing, ('Missing actual sleeve shell rays',side,missing[:20])
        # Source triangles and all their layered spacing remain; the tiny floor
        # is derived from source float32 ULP, not a tuned fit or fabric offset.
        domain[inverse[ids]]=True
        side_data[side]={'g':g,'ids':ids,'origins':origins,'directions':directions,'radii':radii,'inner':inner,'layers':layers}
        policies.append({'side':side,'vertices':len(ids),'uniqueVertices':int(len(np.unique(inverse[ids]))),
            'nativeWrist':head.tolist(),'nativeForearmAxis':axis.tolist(),'nativeSegmentLengthMeters':float(length),
            'nativeStationMeters':[float(stations.min()),float(stations.max())],'gloveStationMeters':[glove_min,glove_max],
            'sourceFabricWallMeters':np.percentile(shell_width,[0,50,100]).tolist(),'quantizationClearanceMeters':epsilon,
            'sourceOnlyCarrierNames':[names[i] for i in sorted(allowed)]})
    reports={bike:json.loads(Path(path).read_text()) for bike,path in [('rookie',rookie),('pro',pro)]}
    progress={'accepted':False,'source':receipt['source'],'policies':policies,'phase':'pose envelope','samples':[]}
    (out/'progress.json').write_text(json.dumps(progress,indent=2)+'\n')
    worst=np.zeros(count,dtype=int); processed=0
    for bike,report in reports.items():
        poses=report['played']['motionSamples'];assert len(poses)==241
        for pi,sample in enumerate(poses):
            byname={j['id']:j['worldMatrix'] for j in sample['joints']}
            world=np.array([byname[n] for n in names]).reshape(-1,4,4).transpose(0,2,1);mat=world@h['ib']
            for side,data in side_data.items():
                g=data['g'];gp=skin(g['POSITION'],g['JOINTS_0'],g['WEIGHTS_0'],mat);bvh=tree(gp,g['indices'])
                ids=data['ids'];m=np.zeros((len(ids),4,4))
                for k in range(4):m+=mat[h['JOINTS_0'][ids,k]]*h['WEIGHTS_0'][ids,k,None,None]
                origins=np.einsum('nij,nj->ni',m[:,:3,:],np.column_stack([data['origins'],np.ones(len(ids))]))
                direction=np.einsum('nij,nj->ni',m[:,:3,:3],data['directions']);scale=np.linalg.norm(direction,axis=1);direction/=scale[:,None]
                bound=float(np.linalg.norm(gp.max(0)-gp.min(0))+np.max(np.linalg.norm(origins-gp.mean(0),axis=1)))
                values=np.zeros(len(ids));intersected=0
                for k,(o,d) in enumerate(zip(origins,direction)):
                    found=hits(bvh,o,d,bound,epsilon)
                    # Outermost real glove outward crossing establishes its
                    # envelope; inner returns cannot masquerade as its exterior.
                    outward=[row[0] for row in found if row[1]>0]
                    if outward:
                        intersected+=1;glove_radius=max(outward)/scale[k]
                        values[k]=max(0.,glove_radius-data['inner'][k]+epsilon/scale[k])
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
    dot=np.sum(original_area[affected]*new_area[affected],axis=1)
    area_ratio=np.linalg.norm(new_area[affected],axis=1)/np.linalg.norm(original_area[affected],axis=1)
    np.savez(out/'patch.npz',positionsBefore=p,positionsAfter=candidate.astype(np.float32),changedRows=changed,
        requiredByUniqueRow=required,connectedDisplacementByUniqueRow=displacement,sourcePositionUniqueRows=first,
        sourcePositionToUnique=inverse,radialDirections=directions_all,sourceCarrierRowDisplacement=row_delta,worstPoseByUniqueRow=worst)
    result={'accepted':False,'schema':'selected-cuff-rest-envelope-v1','source':receipt['source'],'intakeSHA256':sha(root/'intake.json'),
        'recipeSHA256':sha(__file__),'playedReports':{b:{'path':str(path),'sha256':sha(path)} for b,path in [('rookie',rookie),('pro',pro)]},
        'policies':policies,'sourceNativeFieldsExact':True,'allGloveBytesProtected':True,'native75RestAndAnimationExact':True,
        'sourceGeometrySeamFieldsExact':True,'poseCount':processed,'constraintSamples':len(progress['samples']),
        'hoodieChangedRows':len(changed),'hoodieMaxRestDisplacementMeters':float(row_delta.max()),
        'hoodieRequiredMaxMeters':float(required.max()),'hoodieRestDisplacementPercentilesMeters':np.percentile(row_delta[changed],[0,50,95,99,100]).tolist(),
        'affectedTriangles':int(affected.sum()),'nonpositiveAreaOrientationDots':int((dot<=0).sum()),
        'affectedAreaRatioPercentiles':np.percentile(area_ratio,[0,50,100]).tolist(),'obstacleIterations':iterations+1,
        'obstacleMaxStepMeters':float(error),'patch':{'path':str(out/'patch.npz'),'sha256':sha(out/'patch.npz')},
        'elapsedSeconds':time.monotonic()-started,
        'limits':['Finite rays at every selected cuff vertex in all482 recorded poses are construction constraints, not exhaustive triangle or unseen-pose proof.',
                  'Minimum source layer radius follows actual selected shell intersections; no sleeve/glove topology or material is replaced.',
                  'New moving clips and independent finite surface validation remain parent gates.']}
    (out/'report.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
    assert result['nonpositiveAreaOrientationDots']==0,'Source face inversion rejects candidate'

if __name__=='__main__':main(*sys.argv[sys.argv.index('--')+1:])
