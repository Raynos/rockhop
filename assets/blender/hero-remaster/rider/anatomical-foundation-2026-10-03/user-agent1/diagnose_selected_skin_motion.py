"""Diagnose authored skin against immutable body-material motion, no skin edit.

Nearest-body field prediction is a counterfactual diagnostic, not a proposed
weight copy. Material offsets and synthetic fixtures remain limited proxies.
"""
import argparse,collections,hashlib,json,sys
from pathlib import Path
import bpy,numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ap=argparse.ArgumentParser(description=__doc__)
for k in ['source','driver','field','out']:ap.add_argument('--'+k,required=True)
a=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);source,driver_path,field_path,out=[Path(getattr(a,k)).resolve() for k in ['source','driver','field','out']]
out.mkdir(parents=True,exist_ok=True);assert not (out/'diagnosis.json').exists(),'Preserve frozen diagnosis'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();pins={str(p):sha(p) for p in [source,driver_path,field_path]}
assert pins[str(source)]=='d3f05ff00755c0fb9e4245465092333ace538098e86eb44e4ad057e4c68d8996'
bpy.ops.wm.open_mainfile(filepath=str(source));driver=json.loads(driver_path.read_text());data=np.load(field_path)
body=bpy.data.objects['Canonical anatomical body, baked adult hm08'];g=bpy.data.objects['Selected Hunyuan authored skin wearable, unaccepted'];rig=bpy.data.objects['Independent anatomical foundation rig']
names=[b.name for b in rig.data.bones];assert names==data['boneNames'].tolist()
rest=np.array([list(v.co) for v in g.data.vertices]);body_rest=np.array([list(v.co) for v in body.data.vertices]);own=data['weights'].astype(np.float64);own/=own.sum(1)[:,None]
body_weights=np.zeros((len(body_rest),51))
for vertex in body.data.vertices:
    for m in vertex.groups:
        name=body.vertex_groups[m.group].name
        if name in names and rig.data.bones[name].use_deform:body_weights[vertex.index,names.index(name)]=m.weight
assert np.min(body_weights.sum(1))>0;body_weights/=body_weights.sum(1)[:,None]
body.data.calc_loop_triangles();body_faces=[tuple(t.vertices) for t in body.data.loop_triangles];tree=BVHTree.FromPolygons([Vector(p) for p in body_rest],body_faces,all_triangles=True)
ids=[];barycentric=[];offsets=[]
for p in rest:
    q,n,tri,distance=tree.find_nearest(Vector(p));vertices=body_faces[tri];pts=body_rest[list(vertices)]
    uv=np.linalg.lstsq(np.column_stack([pts[1]-pts[0],pts[2]-pts[0]]),np.array(q)-pts[0],rcond=None)[0]
    bary=np.clip([1-sum(uv),uv[0],uv[1]],0,1);bary/=sum(bary)
    ids.append(vertices);barycentric.append(bary);offsets.append(p-bary@pts)
ids=np.array(ids);bary=np.array(barycentric);offsets=np.array(offsets)
nearest_weights=np.einsum('vi,vij->vj',bary,body_weights[ids]);l1=np.abs(own-nearest_weights).sum(1)
parents=[x.value for x in g.data.attributes['source_parent_polygon'].data];region=np.zeros(len(rest),dtype=int)
for f in g.data.polygons:
    label=0 if parents[f.index]<1204 else 1 if parents[f.index]<1224 else 2
    for i in f.vertices:region[i]=max(region[i],label)
def frame_basis(triangles):
    edge=triangles[:,1]-triangles[:,0];normal=np.cross(edge,triangles[:,2]-triangles[:,0]);norm=np.linalg.norm(normal,axis=1)
    assert np.min(norm)>1e-12,'Degenerate body-material triangle, no target guess'
    tangent=edge/np.linalg.norm(edge,axis=1)[:,None];normal/=norm[:,None];other=np.cross(normal,tangent)
    return np.stack([tangent,other,normal],axis=2)
rest_basis=frame_basis(body_rest[ids]);local_offset=np.einsum('vji,vj->vi',rest_basis,offsets)
def evaluated(o):
    e=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=e.to_mesh();m.calc_loop_triangles()
    p=np.array([list(e.matrix_world@v.co) for v in m.vertices]);f=[tuple(t.vertices) for t in m.loop_triangles];e.to_mesh_clear();return p,f
samples=[0,24,48,72,96,120,144,168,192,216,234,240,264,288,312,336,360,384,408,432,456,480,504,528]
matrices=[];targets=[];actual=[];records=[]
bh=np.column_stack([body_rest,np.ones(len(body_rest))]);gh=np.column_stack([rest,np.ones(len(rest))]);world=np.array(rig.matrix_world)
body_dom=np.argmax(body_weights,axis=1)
def stats(errors):return {'maxM':float(errors.max()),'p95M':float(np.percentile(errors,95)),'p50M':float(np.percentile(errors,50))}
for index in samples:
    row=driver['frames'][index]
    for name,trs in row['poseBasisBlender'].items():
        bone=rig.pose.bones[name];bone.rotation_mode='QUATERNION';bone.location=trs['location'];bone.rotation_quaternion=trs['quaternionWXYZ'];bone.scale=trs['scale']
    bpy.context.view_layer.update();bp,bf=evaluated(body);gp,gf=evaluated(g)
    pose=np.array([np.array(rig.pose.bones[n].matrix@rig.data.bones[n].matrix_local.inverted()) for n in names]);matrices.append(pose)
    body_manual=np.einsum('vj,jab,vb->va',body_weights,pose,bh)@world.T
    own_manual=np.einsum('vj,jab,vb->va',own,pose,gh)@world.T
    body_error=float(np.linalg.norm(body_manual[:,:3]-bp,axis=1).max());own_error=float(np.linalg.norm(own_manual[:,:3]-gp,axis=1).max())
    assert body_error<3e-6 and own_error<3e-6,(index,body_error,own_error)
    posed_tri=bp[ids];basis=frame_basis(posed_tri);target=np.einsum('vi,vij->vj',bary,posed_tri)+np.einsum('vij,vj->vi',basis,local_offset)
    prediction=(np.einsum('vj,jab,vb->va',nearest_weights,pose,gh)@world.T)[:,:3]
    targets.append(target);actual.append(gp)
    bt=BVHTree.FromPolygons([Vector(p) for p in bp],bf,all_triangles=True);gt=BVHTree.FromPolygons([Vector(p) for p in gp],gf,all_triangles=True)
    pairs=gt.overlap(bt);classes=collections.Counter()
    for a,b in pairs:
        panel='shirt' if parents[g.data.loop_triangles[a].polygon_index]<1204 else 'collar' if parents[g.data.loop_triangles[a].polygon_index]<1224 else 'hood'
        joint=names[max(collections.Counter(body_dom[list(bf[b])]),key=collections.Counter(body_dom[list(bf[b])]).get)]
        classes[panel+'/'+joint]+=1
    be=[(i,j) for i,j in bt.overlap(bt) if i<j and not set(bf[i])&set(bf[j])]
    arm=lambda tri:any(names[body_dom[i]].startswith(('upperArm.','forearm.','hand.')) for i in bf[tri])
    torso=lambda tri:any(names[body_dom[i]] in ['pelvis','spine','chest'] for i in bf[tri])
    arm_torso=sum((arm(i) and torso(j)) or (arm(j) and torso(i)) for i,j in be)
    record={'frame':index,'timeS':row['timeS'],'bodyManualParityMaxM':body_error,'garmentManualParityMaxM':own_error,
            'bodySelfPairs':len(be),'bodyArmTorsoSelfPairs':arm_torso,'garmentBodyPairsByPanelAndJoint':dict(classes),
            'regions':{label:{'authoredVsBodyMaterialOffset':stats(np.linalg.norm(gp[region==k]-target[region==k],axis=1)),
                               'nearestWeightCounterfactualVsOffset':stats(np.linalg.norm(prediction[region==k]-target[region==k],axis=1))}
                       for k,label in enumerate(['shirt','collar','hood'])}}
    records.append(record);print('SKIN_ANCESTRY_DIAGNOSED',index,body_error,own_error,record['regions']['shirt'],flush=True)
assert pins=={p:sha(p) for p in pins}
np.savez_compressed(out/'material-motion.npz',nativeRestXYZ=rest,bodyTriangleVertexIDs=ids,barycentric=bary,restOffset=offsets,
                    nativeWeights=own,nearestBodyWeights=nearest_weights,region=region,poseFrameIDs=np.array(samples),
                    poseSkinMatricesNative=np.array(matrices),bodyMaterialTargetsWorld=np.array(targets),actualGarmentWorld=np.array(actual),
                    boneNames=np.array(names),rigWorldRows=world)
report={'status':'UNACCEPTED readonly authored-field/body-material ancestry diagnosis, no new skin',
        'pins':pins,'recipeSHA256':sha(__file__),'materialMotionSHA256':sha(out/'material-motion.npz'),
        'weightL1ByRegion':{label:stats(l1[region==k]) for k,label in enumerate(['shirt','collar','hood'])},'frames':records,
        'limits':['Body material triangle vertices/barycentrics remain fixed from rest; posed triangulation IDs are never mistaken for rest ancestry.',
                  'Body-triangle frame transports original cloth offset as a diagnostic target, not an accepted cloth trajectory or complete clearance proof.',
                  'Nearest-body weight prediction is diagnostic only: failed sleeve02already proves blind copying does not qualify garments.',
                  'All source/rest/rig/weights/PBR unchanged. Root alone judges played wearing; actual engine/coverage/iOS/allM0-M5 remain open.']}
(out/'diagnosis.json').write_text(json.dumps(report,indent=2)+'\n');print('SKIN_ANCESTRY_READY',len(records),flush=True)
