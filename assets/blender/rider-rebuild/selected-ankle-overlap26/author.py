"""One source-owned hem extension over the retained actual boot/ankle envelope.

Parent guarded Blender only: -- INPUT OUT. Emits a local position/corner-normal
patch and an unaccepted native preview; never replaces an integrated master.
No topology, UV, weight, body-mask, rig, boot or sole changes are permitted.
"""
import hashlib
import json
import runpy
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Matrix, Quaternion, Vector
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parents[4]
C = Matrix(((1,0,0,0),(0,0,1,0),(0,-1,0,0),(0,0,0,1)))


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        while block:=f.read(1048576): h.update(block)
    return h.hexdigest()


def pin(row):
    path=ROOT/row['path']; assert sha(path)==row['sha256'],row['path']; return path


def points(obj):
    result=np.empty((len(obj.data.vertices),3),np.float32)
    obj.data.vertices.foreach_get('co',result.ravel()); return result.astype(float)


def faces(obj):
    obj.data.calc_loop_triangles(); result=np.empty((len(obj.data.loop_triangles),3),np.int32)
    obj.data.loop_triangles.foreach_get('vertices',result.ravel()); return result


def fields(obj,names):
    lookup={g.index:names.index(g.name) for g in obj.vertex_groups if g.name in names}
    result=np.zeros((len(obj.data.vertices),len(names)))
    for v in obj.data.vertices:
        for g in v.groups:
            if g.group in lookup: result[v.index,lookup[g.group]]=g.weight
    return result


def rest(rig):
    return [(b.name,b.parent.name if b.parent else None,[list(r) for r in b.matrix_local]) for b in rig.data.bones]


def transform(p,m): return p@m[:3,:3].T+m[:3,3]


def skin(p,w,deform):
    result=np.zeros_like(p)
    for j in np.flatnonzero(np.any(w>0,axis=0)):
        selected=w[:,j]>0
        result[selected]+=transform(p[selected],deform[j])*w[selected,j,None]
    return result


def reported_pose(snapshot,rig):
    rows={r['id']:r for r in snapshot['boneLocalTRS']}; assert set(rows)==set(rig.data.bones.keys())
    worlds={}
    def world(name):
        if name not in worlds:
            r=rows[name]; q=r['rotationXYZW']
            local=Quaternion((q[3],*q[:3])).to_matrix().to_4x4()
            for c,s in enumerate(r['scale']):
                for k in range(3): local[k][c]*=s
            local.translation=Vector(r['translation']); parent=rig.data.bones[name].parent
            worlds[name]=(world(parent.name) if parent else Matrix.Identity(4))@local
        return worlds[name]
    return {b.name:np.asarray(C.inverted()@world(b.name)) for b in rig.data.bones}


def center_at(z,ankle,axis):
    return ankle[:2]+((np.asarray(z)-ankle[2])/axis[2])[...,None]*axis[:2]


def sectional_segments(p,f,theta,ankle,axis):
    """Exact triangle/axial-half-plane sections; retain native triangle IDs."""
    planar=p[:,:2]-center_at(p[:,2],ankle,axis)
    radial=planar@np.array([np.cos(theta),np.sin(theta)])
    distance=planar@np.array([-np.sin(theta),np.cos(theta)])
    d=distance[f]; selected=np.flatnonzero((d.min(1)<=0)&(d.max(1)>=0))
    segments=[]; used=[]
    for face in selected:
        ids=f[face]; values=distance[ids]
        if np.all(values==0):
            # Entire native triangle lies in the section plane: retain all its
            # edges; extrema still belong to this actual source triangle.
            for k in range(3):
                a,b=ids[k],ids[(k+1)%3]
                segments.append([[radial[a],p[a,2]],[radial[b],p[b,2]]]);used.append(face)
            continue
        endpoints={}
        for k in range(3):
            a,b=int(ids[k]),int(ids[(k+1)%3]);da,db=distance[a],distance[b]
            if da==0: endpoints[('v',a)]=[radial[a],p[a,2]]
            if da*db<0:
                t=da/(da-db)
                endpoints[('e',min(a,b),max(a,b))]=[radial[a]+t*(radial[b]-radial[a]),p[a,2]+t*(p[b,2]-p[a,2])]
        row=list(endpoints.values())
        assert len(row) in (1,2),('Ambiguous native triangle-plane ownership',int(face),row)
        if len(row)==1: row*=2  # A tangent source vertex is a valid extremum.
        segments.append(row);used.append(face)
    return np.asarray(segments).reshape(-1,2,2),np.asarray(used,np.int32)


def clip_radial(segments,face_ids,lower,upper):
    d=segments[:,1]-segments[:,0]; lo=np.zeros(len(d));hi=np.ones(len(d))
    fixed=d[:,0]==0; valid=~fixed|((segments[:,0,0]>=lower)&(segments[:,0,0]<=upper))
    changing=~fixed
    a=(lower-segments[changing,0,0])/d[changing,0];b=(upper-segments[changing,0,0])/d[changing,0]
    lo[changing]=np.maximum(lo[changing],np.minimum(a,b));hi[changing]=np.minimum(hi[changing],np.maximum(a,b))
    valid&=lo<=hi
    return np.stack((segments[valid,0]+lo[valid,None]*d[valid],segments[valid,0]+hi[valid,None]*d[valid]),axis=1),face_ids[valid]


def polygon_hash(obj):
    indices=np.empty(len(obj.data.loops),np.int32);obj.data.loops.foreach_get('vertex_index',indices)
    starts=np.empty(len(obj.data.polygons),np.int32);obj.data.polygons.foreach_get('loop_start',starts)
    return hashlib.sha256(indices.tobytes()+starts.tobytes()).hexdigest()


def broad_ids(points,triangles,lower,upper):
    p=points[triangles]
    return np.flatnonzero(np.all((p.max(1)>=lower)&(p.min(1)<=upper),axis=1))


def immutable(obj):
    h=hashlib.sha256(polygon_hash(obj).encode())
    for uv in obj.data.uv_layers:
        q=np.empty(len(uv.data)*2,np.float32);uv.data.foreach_get('uv',q);h.update(uv.name.encode());h.update(q.tobytes())
    h.update(np.asarray([p.material_index for p in obj.data.polygons],np.int32).tobytes())
    return dict(topologyUVMaterial=h.hexdigest(),materials=[m.as_pointer() for m in obj.data.materials],
                world=[list(r) for r in obj.matrix_world],parentInverse=[list(r) for r in obj.matrix_parent_inverse],
                parent=obj.parent.name if obj.parent else None,modifiers=[(m.name,m.type,getattr(m,'object',None).name if getattr(m,'object',None) else None) for m in obj.modifiers])


def main():
    args=sys.argv[sys.argv.index('--')+1:];assert len(args)==2
    input_path=Path(args[0]).resolve();out=Path(args[1]).resolve();config=json.loads(input_path.read_text())
    assert out.is_relative_to(ROOT/'harness/out/rider-rebuild/selected-ankle-overlap26') and not out.exists()
    out.mkdir(parents=True); generic=json.loads(pin(config['genericReceipt']).read_text())
    bpy.ops.wm.open_mainfile(filepath=str(pin(generic['candidate'])),use_scripts=False)
    rig=bpy.data.objects['RiderSkeleton'];generic_rest=rest(rig);assert len(rig.data.bones)==75
    assert rig.animation_data.action.name==generic['action']
    poses=[]
    for row in generic['observations']:
        bpy.context.scene.frame_set(row['frame']);bpy.context.view_layer.update()
        poses.append(('retained-generic:'+str(row['frame']),{b.name:np.asarray(b.matrix).copy() for b in rig.pose.bones}))
    bpy.ops.wm.open_mainfile(filepath=str(pin(config['master'])),use_scripts=False)
    rig=bpy.data.objects['RiderSkeleton'];assert rest(rig)==generic_rest and rig.matrix_world.is_identity
    original_rest=rest(rig);names=[b.name for b in rig.data.bones]
    inverse=np.asarray([np.asarray(b.matrix_local.inverted()) for b in rig.data.bones])
    poses.insert(0,('rest',{b.name:np.asarray(b.matrix_local).copy() for b in rig.data.bones}))
    for source in config['playedReports']:
        report=json.loads(pin(source).read_text());assert not report['errors']
        for i,snapshot in enumerate(report['snapshots']):poses.append((source['path']+':'+str(i),reported_pose(snapshot,rig)))
    deforms=[(label,np.asarray([pose[n] for n in names])@inverse) for label,pose in poses]
    helper=runpy.run_path(str(pin(config['triangleHelper'])))
    jeans=bpy.data.objects['RiderJeans'];assert jeans.matrix_world.is_identity and not jeans.data.shape_keys
    jp=points(jeans);jf=faces(jeans);jw=fields(jeans,names);before=immutable(jeans)
    body=bpy.data.objects['RiderBody'];body_points=points(body);body_faces=faces(body);body_weights=fields(body,names)
    old_normals=np.empty((len(jeans.data.corner_normals),3),np.float32);jeans.data.corner_normals.foreach_get('vector',old_normals.ravel())
    selection=json.loads(pin(config['upperSelection']).read_text());upper=set(dict(selection['jeans']['influence']))
    result=jp.copy();changed=[];report=dict(acceptedArt=False,status='UNACCEPTED_HEM_CONSTRUCTION',inputSHA256=sha(input_path),recipeSHA256=sha(__file__),sourceMaster=config['master'],poses=[n for n,_ in poses],sides={},geometryPassed=False,movingReviewPassed=False)
    selection_arrays=dict(np.load(pin(config['hemSelection']),allow_pickle=False))
    settings=config['settings'];angles=np.arange(settings['sectionDirections'])*2*np.pi/settings['sectionDirections']
    for side,sign in [('L',1),('R',-1)]:
        ids=np.flatnonzero((jp[:,0]*sign>0)&(jp[:,2]<settings['fixedAboveZ']))
        assert np.array_equal(ids,selection_arrays['nativeIds'+side]) and np.array_equal(jp[ids].astype(np.float32),selection_arrays['beforeLocal'+side]), 'Actual native lower band differs from pinned decoded source identity'
        assert not upper.intersection(ids.tolist())
        shin=names.index('DEF-shin.'+side+'.001');assert np.array_equal(jw[ids,shin],np.ones(len(ids))) and np.array_equal(jw[ids].sum(1),np.ones(len(ids)))
        ankle=np.asarray(rig.data.bones['DEF-foot.'+side].head_local);knee=np.asarray(rig.data.bones['DEF-shin.'+side].head_local)
        axis=knee-ankle;axis/=np.linalg.norm(axis);assert axis[2]>.8
        boot=bpy.data.objects['ActualSelectedBoot.'+side];assert boot.matrix_world.is_identity
        bp=points(boot);bf=faces(boot);bw=fields(boot,names)
        local_faces=jf[np.any(np.isin(jf,ids),axis=1)]
        hem=[]
        for theta in angles:
            seg,owner=sectional_segments(jp,local_faces,theta,ankle,axis)
            seg,owner=clip_radial(seg,owner,0.,settings['maximumShaftRadiusM'])
            assert len(seg)
            low=float(seg[:,:,1].min());near=seg.reshape(-1,2);near=near[near[:,1]<=low+settings['preservedHemDetailHeightM']]
            radius=float(near[:,0].min());assert radius>.015 and low<settings['fullThroughZ']
            hem.append((low,radius))
        hem=np.asarray(hem);drop=0.;witness=None;envelope=[]
        report['sides'][side]=dict(vertices=ids.tolist(),originalHemSections=hem.tolist(),stage='measure actual collar envelope')
        for label,deform in deforms:
            posed=skin(bp,bw,deform);shin_frame=np.linalg.inv(deform[shin]);p=transform(posed,shin_frame)
            # Conservative face selection by vertical span; no face/vertex edits.
            use=np.flatnonzero((p[bf,2].max(1)>.035)&(p[bf,2].min(1)<settings['fixedAboveZ']))
            f=bf[use];tops=[]
            for i,theta in enumerate(angles):
                seg,owner=sectional_segments(p,f,theta,ankle,axis);seg,owner=clip_radial(seg,owner,0.,hem[i,1])
                assert len(seg),('Boot collar has no actual section',side,label,i)
                at=np.unravel_index(np.argmax(seg[:,:,1]),seg[:,:,1].shape);top=float(seg[at][1]);tops.append(top)
                need=hem[i,0]-top+settings['requiredAxialOverlapM']
                if need>drop:drop=need;witness=dict(pose=label,angleIndex=i,bootNativeTriangle=int(use[owner[at[0]]]),actualSectionPointRadiusZ=seg[at].tolist(),oldHemZ=float(hem[i,0]))
            envelope.append((label,deform,p,f,np.asarray(tops)))
        report['sides'][side].update(extensionM=drop,collarWitness=witness)
        (out/'construction-partial.json').write_text(json.dumps(report,indent=2)+'\n')
        assert 0<=drop<=settings['maximumExtensionM'],('Selected hem extension exceeds authored bound',side,drop,witness)
        t=np.clip((settings['fixedAboveZ']-jp[ids,2])/(settings['fixedAboveZ']-settings['fullThroughZ']),0,1);t=t*t*(3-2*t)
        q=jp[ids]-drop*t[:,None]*(axis/axis[2]);center=center_at(q[:,2],ankle,axis)
        radial=q[:,:2]-center;radius=np.linalg.norm(radial,axis=1);direction=radial/radius[:,None]
        widen=0.;radial_witness=None
        for label,deform,p,f,tops in envelope:
            tree=BVHTree.FromPolygons(p.tolist(),f.tolist(),all_triangles=True)
            for i,point in enumerate(q):
                d=np.r_[direction[i],0.];origin=np.r_[center[i],point[2]]+d*settings['maximumShaftRadiusM']
                hit=tree.ray_cast(Vector(origin),Vector(-d),settings['maximumShaftRadiusM'])
                if hit[0] is None:continue
                actual_radius=settings['maximumShaftRadiusM']-float(hit[3]);need=(actual_radius+settings['clothBootGapM']-radius[i])/t[i]
                if need>widen:widen=need;radial_witness=dict(pose=label,jeansNativeVertex=int(ids[i]),bootNativeVertexIds=f[int(hit[2])].tolist(),bootRadiusM=actual_radius)
        report['sides'][side].update(radialTailoringM=widen,radialWitness=radial_witness)
        (out/'construction-partial.json').write_text(json.dumps(report,indent=2)+'\n')
        assert 0<=widen<=settings['maximumRadialTailoringM'],('Selected lower leg would inflate beyond authored bound',side,widen,radial_witness)
        q[:,:2]+=direction*(widen*t)[:,None];result[ids]=q.astype(np.float32);changed.extend(ids.tolist())
        row=dict(vertices=ids.tolist(),extensionM=drop,radialTailoringM=widen,collarWitness=witness,radialWitness=radial_witness,
                 originalHemSections=hem.tolist(),preservedWeights='Exactly1 matching shin.001 for every edited vertex',checks={})
        report['sides'][side]=row
        (out/'construction-partial.json').write_text(json.dumps(report,indent=2)+'\n')
        jeans.data.vertices.foreach_set('co',result.astype(np.float32).ravel());jeans.data.update()
        actual_faces=faces(jeans);actual_local_ids=np.flatnonzero(np.any(np.isin(actual_faces,ids),axis=1));actual_local_faces=actual_faces[actual_local_ids]
        # Complete triangles, every retained pose. Retained sample envelope is
        # explicit; no interpolation/midpoint or full motion qualification claim.
        for label,deform,p,f,tops in envelope:
            final_pose=skin(result,jw,deform);local=transform(final_pose,np.linalg.inv(deform[shin]))
            body_local=transform(skin(body_points,body_weights,deform),np.linalg.inv(deform[shin]))
            region=local[np.unique(actual_local_faces)];lower,upper=region.min(0),region.max(0)
            jeans_ids=broad_ids(local,actual_faces,lower,upper);boot_ids=broad_ids(p,bf,lower,upper);body_ids=broad_ids(body_local,body_faces,lower,upper)
            empty=dict(passed=True,proof='No complete obstacle triangle AABB overlaps the changed garment region',testedBroadphasePairs=0)
            checks=dict(jeansSelf=helper['intersections'](local,actual_faces[jeans_ids],face_ids_a=jeans_ids),
                        jeansBoot=helper['intersections'](local,actual_local_faces,p,bf[boot_ids],face_ids_a=actual_local_ids,face_ids_b=boot_ids) if len(boot_ids) else dict(empty),
                        jeansVisibleBody=helper['intersections'](local,actual_local_faces,body_local,body_faces[body_ids],face_ids_a=actual_local_ids,face_ids_b=body_ids) if len(body_ids) else dict(empty))
            actual_hem=[]
            for theta in angles:
                seg,owners=sectional_segments(local,actual_local_faces,theta,ankle,axis);seg,owners=clip_radial(seg,owners,0.,settings['maximumShaftRadiusM'])
                assert len(seg);actual_hem.append(float(seg[:,:,1].min()))
            overlap=np.asarray(actual_hem)-tops
            checks['sectionOverlap']=dict(passed=bool(np.all(overlap<=-settings['requiredAxialOverlapM']+1e-7)),minimumOverlapM=float((-overlap).min()),actualStoredPosedHemZ=actual_hem,actualBootTopZ=tops.tolist(),numericAllowanceM=1e-7)
            row['checks'][label]=checks;(out/'construction-partial.json').write_text(json.dumps(report,indent=2)+'\n')
    changed=np.asarray(sorted(set(changed)),np.int32);result=result.astype(np.float32)
    assert np.array_equal(result[np.setdiff1d(np.arange(len(jp)),changed)],jp[np.setdiff1d(np.arange(len(jp)),changed)].astype(np.float32))
    jeans.data.vertices.foreach_set('co',result.ravel());jeans.data.normals_split_custom_set([(0.,0.,0.)]*len(jeans.data.loops));jeans.data.update()
    normals=np.empty_like(old_normals);jeans.data.corner_normals.foreach_get('vector',normals.ravel())
    changed_set=set(changed.tolist())
    affected_polygons=[p for p in jeans.data.polygons if changed_set.intersection(p.vertices)]
    corners=np.asarray([i for p in affected_polygons for i in p.loop_indices],np.int32)
    untouched=np.setdiff1d(np.arange(len(normals)),corners);normals[untouched]=old_normals[untouched]
    jeans.data.normals_split_custom_set(normals.tolist())
    assert immutable(jeans)==before and np.array_equal(fields(jeans,names),jw) and rest(rig)==original_rest
    patch=out/'selected-jeans-lower-hem-patch.npz'
    np.savez_compressed(patch,nativeVertexIds=changed,beforeLocal=jp[changed].astype(np.float32),afterLocal=result[changed],
                        polygonTopologySHA256=np.asarray(polygon_hash(jeans)),sourceLoopTriangleSHA256=np.asarray(hashlib.sha256(jf.tobytes()).hexdigest()),cornerIds=corners,beforeNormals=old_normals[corners],afterNormals=normals[corners])
    report.update(patch=dict(path=str(patch.relative_to(ROOT)),sha256=sha(patch)),outsideBandPositionsExact=True,allSkinWeightsExact=True,
                  topologyUVMaterialsExact=True,rigRestExact=True,upperWeightSelectionDisjoint=True,
                  integration='Apply only nativeVertexIds after exact beforeLocal/topology checks. Require every existing corrective delta at those IDs to be zero; shift Basis and all keys equally. Keep integrated rig/actions/weights and unrelated meshes. Recompute only incident normals.',
                  limits='One bounded authored warp; complete retained-pose triangle checks do not qualify intervening motion, overlap around all angles, selected cuff detail or final art. Actual moving review and the newer native control envelope remain required.')
    report['retainedPoseGeometryPassed']=all(check['passed'] for side in report['sides'].values() for checks in side['checks'].values() for check in checks.values())
    report['status']='UNACCEPTED_PLAYED_REVIEW_PENDING' if report['retainedPoseGeometryPassed'] else 'REJECTED_RETAINED_POSE_GEOMETRY'
    native=out/'UNACCEPTED-selected-hem-overlap.blend';bpy.ops.wm.save_as_mainfile(filepath=str(native),compress=True)
    report['native']=dict(path=str(native.relative_to(ROOT)),sha256=sha(native))
    (out/'construction.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(native=report['native'],status=report['status'])),flush=True)


if __name__=='__main__':main()
