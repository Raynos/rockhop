"""Prepare real full/LOD selected rider derivatives in new native objects.

Parent owns the bounded Blender execution and visual judgment. This file never
writes normal player paths or changes the source objects. Usage:
  blender -b -t 2 --python-exit-code 1 --python author.py -- INPUT OUT LEVEL
LEVEL is full or lod. Separate invocations keep active texture sets bounded.
"""
import hashlib
import json
import math
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT=Path(__file__).resolve().parents[4]
HERE=Path(__file__).resolve().parent


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        while block:=f.read(1048576):h.update(block)
    return h.hexdigest()


def pin(row):
    path=ROOT/row['path'];assert sha(path)==row['sha256'],row['path'];return path


def active(obj):
    bpy.ops.object.select_all(action='DESELECT');obj.hide_set(False);obj.select_set(True)
    bpy.context.view_layer.objects.active=obj


def points(obj):
    p=np.empty((len(obj.data.vertices),3),np.float32);obj.data.vertices.foreach_get('co',p.ravel())
    return p.astype(float)


def triangles(obj):
    obj.data.calc_loop_triangles();f=np.empty((len(obj.data.loop_triangles),3),np.int32)
    obj.data.loop_triangles.foreach_get('vertices',f.ravel());return f


def digest(obj):
    return hashlib.sha256(points(obj).tobytes()+triangles(obj).tobytes()).hexdigest()


def tree(p,f):return BVHTree.FromPolygons(p.tolist(),f.tolist(),all_triangles=True)


def barycentric(p,t):
    a=t[1]-t[0];b=t[2]-t[0];q=p-t[0]
    aa=a@a;ab=a@b;bb=b@b;d=aa*bb-ab*ab
    assert d>1e-24,'Degenerate source correspondence triangle'
    v=(bb*(q@a)-ab*(q@b))/d;w=(aa*(q@b)-ab*(q@a))/d
    result=np.array([1-v-w,v,w]);assert result.min()>-1e-5
    result=np.maximum(result,0);return result/result.sum()


def skin_rows(obj,names):
    indices={g.index:names.index(g.name) for g in obj.vertex_groups if g.name in names}
    result=np.zeros((len(obj.data.vertices),len(names)))
    for v in obj.data.vertices:
        for g in v.groups:
            if g.group in indices:result[v.index,indices[g.group]]=g.weight
    return result


def priority(obj,rig,controls):
    """Zero means protected in Blender's collapse implementation, not maximal."""
    p=points(obj);f=triangles(obj);weights=np.ones(len(p))
    edges={};face_normal=np.cross(p[f[:,1]]-p[f[:,0]],p[f[:,2]]-p[f[:,0]])
    face_normal/=np.maximum(np.linalg.norm(face_normal,axis=1)[:,None],1e-30)
    mats=np.array([t.material_index for t in obj.data.loop_triangles])
    for i,face in enumerate(f):
        for a,b in zip(face,np.roll(face,-1)):edges.setdefault(tuple(sorted((int(a),int(b)))),[]).append(i)
    boundary=set();material=set();curved=set();required_edges=[]
    for (a,b),rows in edges.items():
        if len(rows)!=2:boundary.update((a,b));required_edges.append((a,b))
        elif mats[rows[0]]!=mats[rows[1]]:material.update((a,b));required_edges.append((a,b))
        elif face_normal[rows[0]]@face_normal[rows[1]]<math.cos(math.radians(controls['curvatureDegrees'])):curved.update((a,b))
    if curved:weights[list(curved)]=controls['curvatureCollapseWeight']
    rig_to_local=obj.matrix_world.inverted()@rig.matrix_world
    joint=np.zeros(len(p),bool)
    for bone in rig.data.bones:
        if not bone.name.startswith('DEF-'):continue
        center=np.asarray(rig_to_local@bone.head_local)
        radius=(rig_to_local@bone.tail_local-rig_to_local@bone.head_local).length*controls['jointBandFractionOfBoneLength']
        if radius>1e-5:joint|=np.linalg.norm(p-center,axis=1)<radius
    weights[joint]=np.minimum(weights[joint],controls['jointCollapseWeight'])
    locked=boundary|material
    if locked:weights[list(locked)]=0
    g=obj.vertex_groups.new(name='ProductionCollapseAllowed')
    # Quantized values are intentional authored priorities; four batches.
    for value in np.unique(weights):g.add(np.flatnonzero(weights==value).tolist(),float(value),'REPLACE')
    return g.name,{'openOrNonmanifoldBoundaryVertices':len(boundary),'materialBoundaryVertices':len(material),
                   'jointPriorityVertices':int(joint.sum()),'curvaturePriorityVertices':len(curved),'lockedVertices':len(locked)}, sorted(locked), required_edges


def simplify(source,rig,spec,level,config):
    obj=source.copy();obj.data=source.data.copy();obj.name='Production.'+level+'.'+source.name
    bpy.context.scene.collection.objects.link(obj);obj.hide_render=False
    # Capture source keys first; their deltas are transferred after topology.
    if obj.data.shape_keys:obj.shape_key_clear()
    for mod in list(obj.modifiers):obj.modifiers.remove(mod)
    group,receipt,locked,required_edges=priority(obj,rig,config['protection']);before=len(triangles(obj))
    original_points=points(obj)
    ancestry=obj.data.attributes.new('ProductionOriginalVertex','INT','POINT')
    ancestry.data.foreach_set('value',np.arange(len(obj.data.vertices),dtype=np.int32))
    active(obj);mod=obj.modifiers.new('Protected selected-source reduction','DECIMATE')
    mod.decimate_type='COLLAPSE';mod.ratio=min(1.,spec[level]/before)
    mod.vertex_group=group;mod.vertex_group_factor=config['protection']['vertexGroupFactor']
    mod.use_collapse_triangulate=True;mod.use_symmetry=False
    bpy.ops.object.modifier_apply(modifier=mod.name)
    obj.data.normals_split_custom_set([(0.,0.,0.)]*len(obj.data.loops))
    obj.data.update()
    actual_ids=np.empty(len(obj.data.vertices),np.int32)
    obj.data.attributes['ProductionOriginalVertex'].data.foreach_get('value',actual_ids)
    actual_points=points(obj);mapping={};missing=[]
    for v in locked:
        candidates=np.flatnonzero(actual_ids==v)
        matches=[int(i) for i in candidates if np.array_equal(actual_points[i],original_points[v])]
        if len(matches)==1:mapping[v]=matches[0]
        else:missing.append(v)
    actual_edges={tuple(sorted(e.vertices)) for e in obj.data.edges}
    missing_edges=[(a,b) for a,b in required_edges if a not in mapping or b not in mapping or tuple(sorted((mapping[a],mapping[b]))) not in actual_edges]
    receipt['actualBoundaryIdentity']={'requiredVertices':len(locked),'exactRetainedVertices':len(mapping),
                                       'requiredEdges':len(required_edges),'missingVertices':missing[:16],
                                       'missingEdges':missing_edges[:16],'passed':not missing and not missing_edges}
    assert receipt['actualBoundaryIdentity']['passed'],('Actual protected boundary changed',source.name,receipt['actualBoundaryIdentity'])
    actual=len(triangles(obj));receipt.update(sourceTriangles=before,targetTriangles=actual,targetBudget=spec[level])
    assert actual<=spec[level],('Protected topology exceeds allocation; do not remove protection',source.name,receipt)
    obj['selectedProductionRole']=source.name;obj['selectedProductionLevel']=level
    return obj,receipt


def transfer(source,target,rig,spec,level,config,out):
    sp=points(source);sf=triangles(source);tp=points(target);tf=triangles(target)
    names=[g.name for g in source.vertex_groups if g.name in rig.data.bones]
    sw=skin_rows(source,names);tw=skin_rows(target,names);bvh=tree(sp,sf)
    normals=np.cross(sp[sf[:,1]]-sp[sf[:,0]],sp[sf[:,2]]-sp[sf[:,0]])
    normals/=np.maximum(np.linalg.norm(normals,axis=1)[:,None],1e-30)
    limit=spec['maximumSurfaceErrorM']*config['levels'][level]['surfaceErrorMultiplier']
    ids=[];coefficients=[];distances=[];normal_dots=[];weight_errors=[]
    for i,p in enumerate(tp):
        near=bvh.find_nearest(Vector(p),limit)
        assert near[0] is not None,('Target vertex escapes selected source',source.name,i,limit)
        tri=int(near[2]);coeff=barycentric(np.asarray(near[0]),sp[sf[tri]])
        weights=coeff@sw[sf[tri]];difference=float(np.abs(weights-tw[i]).sum())
        dot=float(normals[tri]@np.asarray(target.data.vertices[i].normal))
        assert dot>=config['transfer']['minimumNormalDot'],('Wrong-facing source correspondence',source.name,i,dot)
        assert difference<=config['transfer']['maximumSkinWeightL1'],('Anatomical field correspondence escaped its source',source.name,i,difference)
        ids.append(tri);coefficients.append(coeff);distances.append(float(near[3]));normal_dots.append(dot);weight_errors.append(difference)
    ids=np.asarray(ids,np.int32);coefficients=np.asarray(coefficients)
    # Every source vertex and every target triangle centroid is also checked.
    target_bvh=tree(tp,tf);reverse_max=0.
    for i in np.unique(sf):
        p=sp[i]
        near=target_bvh.find_nearest(Vector(p),limit)
        assert near[0] is not None,('Selected source detail exceeds geometry bound',source.name,i,limit)
        reverse_max=max(reverse_max,float(near[3]))
    for i,p in enumerate(tp[tf].mean(axis=1)):
        near=bvh.find_nearest(Vector(p),limit)
        assert near[0] is not None,('Target face chord leaves selected source',source.name,i,limit)
    full=np.einsum('ij,ijk->ik',coefficients,sw[sf[ids]])
    full/=full.sum(axis=1)[:,None]
    chosen=np.argsort(-full,axis=1,kind='stable')[:,:config['transfer']['maximumInfluences']]
    retained=np.take_along_axis(full,chosen,axis=1).sum(axis=1)
    removed=np.maximum(0.,1-retained);four=np.zeros_like(full)
    np.put_along_axis(four,chosen,np.take_along_axis(full,chosen,axis=1)/retained[:,None],axis=1)
    edges=np.unique(np.sort(np.concatenate([tf[:,[0,1]],tf[:,[1,2]],tf[:,[2,0]]]),axis=1),axis=0)
    full_edge_l1=np.abs(full[edges[:,0]]-full[edges[:,1]]).sum(axis=1)
    four_edge_l1=np.abs(four[edges[:,0]]-four[edges[:,1]]).sum(axis=1)
    additional=np.maximum(0.,four_edge_l1-full_edge_l1)
    support=four>config['transfer']['supportEpsilon']
    full_support=full>config['transfer']['supportEpsilon']
    edge_support_changes=np.count_nonzero(support[edges[:,0]]!=support[edges[:,1]],axis=1)
    full_edge_support_changes=np.count_nonzero(full_support[edges[:,0]]!=full_support[edges[:,1]],axis=1)
    diagnostics={'maximumRemovedMass':float(removed.max()),'removedMassP95':float(np.percentile(removed,95)),
                 'maximumAdditionalAdjacentWeightL1':float(additional.max()),
                 'maximumAdjacentSupportSymmetricDifference':int(edge_support_changes.max()),
                 'maximumAdditionalAdjacentSupportChanges':int(np.maximum(0,edge_support_changes-full_edge_support_changes).max()),
                 'removedMassTolerance':config['transfer']['maximumRemovedMass'],
                 'additionalAdjacentWeightL1Tolerance':config['transfer']['maximumAdditionalAdjacentWeightL1'],
                 'overRemovedMassVertices':np.flatnonzero(removed>config['transfer']['maximumRemovedMass'])[:16].tolist(),
                 'overAdjacentL1Edges':edges[additional>config['transfer']['maximumAdditionalAdjacentWeightL1']][:16].tolist()}
    field_path=out/(target.name+'-four-field-diagnostics.npz')
    np.savez_compressed(field_path,fullInterpolatedFields=full.astype(np.float32),finalFourFields=four.astype(np.float32),
                        removedMass=removed.astype(np.float32),edgeVertexIds=edges,
                        fullEdgeWeightL1=full_edge_l1.astype(np.float32),fourEdgeWeightL1=four_edge_l1.astype(np.float32),
                        adjacentSupportChanges=edge_support_changes,fullAdjacentSupportChanges=full_edge_support_changes,
                        groupNames=np.asarray(names))
    diagnostics['arrays']={'path':str(field_path.relative_to(ROOT)),'sha256':sha(field_path)}
    (out/(target.name+'-four-field-diagnostics.json')).write_text(json.dumps(diagnostics,indent=2)+'\n')
    assert not diagnostics['overRemovedMassVertices'] and not diagnostics['overAdjacentL1Edges'],('FOUR projection changes source support beyond declared bounds',source.name,diagnostics)
    target.vertex_groups.clear();groups=[target.vertex_groups.new(name=n) for n in names]
    for i,row in enumerate(four):
        for g in np.flatnonzero(row):groups[int(g)].add([i],float(row[g]),'REPLACE')
    copied=[]
    if source.data.shape_keys:
        keys=source.data.shape_keys.key_blocks
        unknown=[k.name for k in list(keys)[1:] if k.name not in config['authorizedCorrectiveShapeNames']]
        assert not unknown,('Unreviewed source shape keys cannot transfer',unknown)
        target.shape_key_add(name='Basis')
        basis=np.empty_like(sp);keys[0].data.foreach_get('co',basis.ravel())
        for source_key in list(keys)[1:]:
            assert source_key.name not in config['forbiddenSourceShapes']
            q=np.empty_like(sp);source_key.data.foreach_get('co',q.ravel());delta=q-basis
            result=tp+np.einsum('ij,ijk->ik',coefficients,delta[sf[ids]])
            key=target.shape_key_add(name=source_key.name);key.data.foreach_set('co',result.astype(np.float32).ravel())
            key.value=0;copied.append(source_key.name)
    arm=target.modifiers.new('Selected exact75 rig','ARMATURE');arm.object=rig
    arm.use_deform_preserve_volume=False
    target.parent=source.parent;target.matrix_parent_inverse=source.matrix_parent_inverse.copy()
    target.matrix_world=source.matrix_world.copy()
    file=out/(target.name+'-source-transfer.npz')
    np.savez_compressed(file,sourceFaceIds=ids,sourceVertexIds=sf[ids],sourceCoefficients=coefficients.astype(np.float32),
                        sourceReferenceTrianglesLocal=sp[sf[ids]].astype(np.float32),
                        sourceTopologySHA256=np.asarray(hashlib.sha256(sf.tobytes()).hexdigest()),
                        targetRestLocal=tp.astype(np.float32),sourceNormalDot=np.asarray(normal_dots,np.float32))
    return {'sourceTransfer':{'path':str(file.relative_to(ROOT)),'sha256':sha(file)},'copiedShapeKeys':copied,'fourFieldDiagnostics':diagnostics,
            'maximumTargetVertexDistanceM':max(distances),'maximumSourceVertexDistanceM':reverse_max,
            'minimumSourceNormalDot':min(normal_dots),'maximumSourceSkinL1':max(weight_errors),
            'sourceSurfaceBoundM':limit,'strongestInfluences':config['transfer']['maximumInfluences'],
            'limits':'Rest correspondence only. Full posed surface/skin parity and complete moving review remain required.'}


def unwrap_family(objects):
    for slot,obj in enumerate(objects):
        active(obj)
        while obj.data.uv_layers:obj.data.uv_layers.remove(obj.data.uv_layers[0])
        obj.data.uv_layers.new(name='SelectedProductionAtlas')
        bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.uv.smart_project(angle_limit=math.radians(66),island_margin=.012,correct_aspect=True,scale_to_bounds=True)
        bpy.ops.object.mode_set(mode='OBJECT')
        uv=obj.data.uv_layers.active.data
        if len(objects)>1:
            for corner in uv:corner.uv.x=(corner.uv.x+slot)/len(objects)


def main():
    args=sys.argv[sys.argv.index('--')+1:];assert len(args) in (3,4)
    input_path=Path(args[0]).resolve();out=Path(args[1]).resolve();level=args[2]
    config=json.loads(input_path.read_text());assert level in config['levels']
    families_requested=set(args[3].split(',')) if len(args)==4 else {r['family'] for r in config['objects'].values()}
    assert families_requested and families_requested<={r['family'] for r in config['objects'].values()}
    config['objects']={n:r for n,r in config['objects'].items() if r['family'] in families_requested}
    assert out.is_relative_to(ROOT/'harness/out/rider-rebuild/selected-rider-production25') and not out.exists()
    bpy.ops.wm.open_mainfile(filepath=str(pin(config['sourceMaster'])))
    rig=bpy.data.objects[config['rig']];assert len(rig.data.bones)==75
    rig.animation_data_clear()
    for b in rig.pose.bones:b.matrix_basis.identity()
    sources={name:bpy.data.objects[name] for name in config['objects']}
    before={name:digest(obj) for name,obj in sources.items()}
    for obj in sources.values():
        if obj.data.shape_keys:
            for key in obj.data.shape_keys.key_blocks:key.value=0
        obj.hide_set(False)
    bpy.context.view_layer.update();out.mkdir(parents=True)
    report={'acceptedArt':False,'status':'UNACCEPTED_PRODUCTION_GEOMETRY','sourceMaster':config['sourceMaster'],
            'recipeSHA256':sha(__file__),'inputSHA256':sha(input_path),'level':level,'authoredFamilies':sorted(families_requested),'objects':{},'bakeCompleted':False,
            'movingReviewPassed':False,'denseGeometryPassed':False,'devicePassed':False}
    targets={};families={}
    for name,spec in config['objects'].items():
        print('COMPACT '+level+' '+name,flush=True)
        target,row=simplify(sources[name],rig,spec,level,config);targets[name]=target
        row['transfer']=transfer(sources[name],target,rig,spec,level,config,out)
        report['objects'][name]=row;families.setdefault(spec['family'],[]).append(target)
        (out/'production.json').write_text(json.dumps(report,indent=2)+'\n')
    for objects in families.values():unwrap_family(objects)
    assert before=={name:digest(obj) for name,obj in sources.items()},'Source geometry changed'
    count=sum(len(triangles(obj)) for obj in targets.values());assert count<=config['levels'][level]['triangleBudget']
    for source in sources.values():source.hide_render=True;source.hide_set(True)
    report.update(totalTriangles=count,sourceGeometryUnchanged=before,realIndependentLOD=level=='lod',
                  limits='Production geometry saved for original selected-source cage baking next; source native remains immutable. This is neither final art nor runtime/device qualification.')
    native=out/('UNACCEPTED-selected-production-'+level+'.blend')
    bpy.ops.wm.save_as_mainfile(filepath=str(native),compress=True)
    report['native']={'path':str(native.relative_to(ROOT)),'sha256':sha(native)}
    (out/'production.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'native':report['native'],'triangles':count,'bakeCompleted':False}),flush=True)


if __name__=='__main__':main()
