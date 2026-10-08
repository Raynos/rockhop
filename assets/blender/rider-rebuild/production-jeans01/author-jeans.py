"""One intended-final Blender jeans authoring pass, then controlled actual bake.
Parent admits each stage under the serial CPU2 model guard after checkpoint.
blender -b -t 2 --python-exit-code 1 --python THIS -- SPEC FRESH_OUT author|bake
Original sources never edited. No compact source UV or prior fit solver used.
"""
import hashlib
import json
import math
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parents[4]
SHA = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()

def pin(row):
    p = ROOT / row['path']
    assert p.is_file() and SHA(p) == row['sha256'], ('Changed source', str(p))
    return p

def make(name, vertices, faces):
    m = bpy.data.meshes.new(name + 'Mesh'); m.from_pydata(vertices, [], faces); m.update()
    o = bpy.data.objects.new(name, m); bpy.context.collection.objects.link(o)
    for f in m.polygons: f.use_smooth = True
    return o

def active(o):
    bpy.ops.object.select_all(action='DESELECT'); o.hide_set(False); o.select_set(True)
    bpy.context.view_layer.objects.active = o

def signature(body, rig):
    return hashlib.sha256(json.dumps({'v':[list(v.co) for v in body.data.vertices],
      'p':[list(p.vertices) for p in body.data.polygons],
      'w':[[[g.group,g.weight] for g in v.groups] for v in body.data.vertices],
      'bones':[[b.name,list(b.head_local),list(b.tail_local),[list(r) for r in b.matrix_local]] for b in rig.data.bones]},separators=(',',':')).encode()).hexdigest()

def atlas(o):
    # Waist/cuffs are open. Mark the actual leg inner seam, front/back pelvic
    # centre seam, and waist band as conventional tailoring unwrap cuts.
    if not o.data.uv_layers: o.data.uv_layers.new(name='SelectedDenimProductionAtlas')
    active(o); bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.unwrap(method='ANGLE_BASED',margin=.018); bpy.ops.object.mode_set(mode='OBJECT')
    o.data.uv_layers.active.name='SelectedDenimProductionAtlas'
    return [(d.uv.x,d.uv.y) for d in o.data.uv_layers.active.data]

def production_surface(spec):
    v=[]; faces=[]; rings={}; seam_pairs=set(); count=48; quarter=count//4
    # Deliberately arranged rings; no source-face survival contract. Each pair
    # of upper inner arcs shares the saddle seam, forming one pelvis/crotch.
    shared={}
    for side,sign in [('L',1),('R',-1)]:
        rows=[]
        for level,(z,cx,cy,rx,ry) in enumerate(spec['legRings']):
            ids=[]
            for k in range(count):
                theta=2*math.pi*k/count
                x=sign*(cx+rx*math.cos(theta)); y=cy-ry*math.sin(theta); zz=z
                if level<=1:
                    yaw=sign*math.radians(spec['cuff']['footYawDegrees'])
                    dx,dy=x-sign*cx,y-cy
                    x=sign*cx+dx*math.cos(yaw)-dy*math.sin(yaw)
                    y=cy+dx*math.sin(yaw)+dy*math.cos(yaw)
                if level==0:
                    # Directional cuff overlap around actual short shoe profile.
                    zz=spec['cuff']['backZ']+(spec['cuff']['frontZ']-spec['cuff']['backZ'])*(.5+.5*math.sin(theta))
                if level==len(spec['legRings'])-1 and quarter+quarter//2 <= k <= count-quarter-quarter//2:
                    # Inner arc is the authored inseam saddle, not a figure-eight
                    # pinched single point. Front/back endpoints end at pelvis.
                    x=0; zz=z-.085*max(0,-math.cos(theta))**2
                    key=k
                    if key in shared: ids.append(shared[key]); continue
                    shared[key]=len(v)
                ids.append(len(v)); v.append((x,y,zz))
            if rows:
                for k in range(count): faces.append((rows[-1][k],rows[-1][(k+1)%count],ids[(k+1)%count],ids[k]))
            if rows: seam_pairs.add(tuple(sorted((rows[-1][count//2],ids[count//2]))))
            rows.append(ids)
        rings[side]=rows
    lo=quarter+quarter//2; hi=count-quarter-quarter//2
    # Exterior arcs together create a single 60-edge pelvis perimeter.
    outer=list(range(hi,count))+list(range(0,lo+1))
    perimeter=[rings['L'][-1][k] for k in outer]
    right=[rings['R'][-1][k] for k in reversed(outer)]
    perimeter+=right[1:-1]
    for z,rx,front,back in spec['pelvisRings']:
        ids=[]
        for old in perimeter:
            p=np.array(v[old]); angle=math.atan2(-(p[1]+.017),p[0])
            ids.append(len(v)); v.append((rx*math.cos(angle),-.017-(front if math.sin(angle)>0 else back)*math.sin(angle),z))
        for k in range(len(ids)): faces.append((perimeter[k],perimeter[(k+1)%len(ids)],ids[(k+1)%len(ids)],ids[k]))
        for k in (0,len(ids)//2): seam_pairs.add(tuple(sorted((perimeter[k],ids[k]))))
        if abs(z-1.021)<.0001:
            for k in range(len(ids)): seam_pairs.add(tuple(sorted((ids[k],ids[(k+1)%len(ids)]))))
        perimeter=ids
    o=make('RiderJeans',v,faces)
    # Deterministic winding correction by Blender, with open real apertures.
    import bmesh
    bm=bmesh.new(); bm.from_mesh(o.data); bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces)); bm.to_mesh(o.data); bm.free()
    for edge in o.data.edges: edge.use_seam=tuple(sorted(edge.vertices)) in seam_pairs
    return o

def author(spec,out):
    native=pin(spec['native']); densepath=pin(spec['dense']); bodypath=pin(spec['body'])
    bpy.ops.wm.open_mainfile(filepath=str(native))
    body=bpy.data.objects['RiderBody']; rig=bpy.data.objects['RiderSkeleton']; before=signature(body,rig)
    dense=dict(np.load(densepath)); points=dense['vertices'].astype(float)
    # Source is Y up/+Z forward. One fixed ordinary affine sets its modelling
    # space; an explicit 5x3x11 artist lattice supplies subsequent large edits.
    aff=np.array(spec['sourceAffine']); points=np.einsum('ni,ji->nj',points,aff[:3,:3])+aff[:3,3]
    reference=make('AlignedSelectedDenseJeans',points.tolist(),dense['faces'].tolist())
    normals=np.einsum('ni,ij->nj',dense['donorCornerNormals'].reshape(-1,3).astype(float),np.linalg.inv(aff[:3,:3]))
    normals/=np.linalg.norm(normals,axis=1)[:,None]
    reference.data.normals_split_custom_set(normals.tolist())
    uv=reference.data.uv_layers.new(name='OriginalSelectedDenseCornerUV')
    for p,values in zip(reference.data.polygons,dense['originalCornerUV']):
        # Immutable saved UVs are raw glTF TEXCOORD_0; Blender needs V flipped.
        for loop,value in zip(p.loop_indices,values): uv.data[loop].uv=(float(value[0]),1.0-float(value[1]))
    mat=bpy.data.materials.new('ActualSelectedDenseDenim'); mat.use_nodes=True
    n=mat.node_tree.nodes; l=mat.node_tree.links; bs=n.get('Principled BSDF')
    tex=n.new('ShaderNodeTexImage'); tex.image=bpy.data.images.load(str(pin(spec['maps']['albedo']))); tex.image.pack(); l.new(tex.outputs['Color'],bs.inputs['Base Color'])
    mr=n.new('ShaderNodeTexImage'); mr.image=bpy.data.images.load(str(pin(spec['maps']['metallicRoughness']))); mr.image.colorspace_settings.name='Non-Color'; mr.image.pack()
    split=n.new('ShaderNodeSeparateColor'); l.new(mr.outputs['Color'],split.inputs[0]); l.new(split.outputs['Green'],bs.inputs['Roughness']); l.new(split.outputs['Blue'],bs.inputs['Metallic']); reference.data.materials.append(mat)
    lattice=bpy.data.lattices.new('AuthoredJeansLargeFormCage'); lattice.points_u=5; lattice.points_v=3; lattice.points_w=11
    lattice.interpolation_type_u='KEY_BSPLINE'; lattice.interpolation_type_v='KEY_LINEAR'; lattice.interpolation_type_w='KEY_LINEAR'
    cage=bpy.data.objects.new('EditableSelectedJeansLattice',lattice); bpy.context.collection.objects.link(cage)
    cage.location=(0,-.015,.581); cage.scale=(.56,.38,.97)
    for k,p in enumerate(lattice.points):
        z=k//15; x=k%5; y=(k//5)%3
        delta=spec['latticeRows'][z]
        depth=delta['frontDelta']*(1-y/2)+delta['backDelta']*(y/2)
        p.co_deform=p.co+Vector(((x-2)*delta['spread']/.56,(delta['forwardShift']+depth)/.38,0))
    mod=reference.modifiers.new('Authored selected large-form fit','LATTICE'); mod.object=cage
    target=production_surface(spec); atlas(target)
    target['selectedAppearanceAuthority']=spec['dense']['sha256']; target['unaccepted']=True
    # Two subdiv levels supply deformation loops and actual geometric folds.
    subdiv=target.modifiers.new('Production joint and fold tessellation','SUBSURF'); subdiv.levels=2
    active(target); bpy.ops.object.modifier_apply(modifier=subdiv.name)
    sw=target.modifiers.new('Selected sculpt major folds','SHRINKWRAP'); sw.target=reference; sw.wrap_method='NEAREST_SURFACEPOINT'; sw.offset=.0015
    # Selected sculpt projection is bounded by the authored fitted form;
    # neither source projection nor body-derived shell becomes appearance alone.
    # Blender validates this setter against existing groups: create first.
    group=target.vertex_groups.new(name='SelectedSculptProjection')
    assert group.name=='SelectedSculptProjection', 'Projection group name changed'
    sw.vertex_group=group.name
    assert sw.vertex_group==group.name=='SelectedSculptProjection', 'Projection group binding absent'
    for vertex in target.data.vertices:
        z=vertex.co.z
        # Keep waist/crotch/cuffs authored. Source projection owns selected folds
        # on broad exterior thigh/knee/shin panels where those forms are real.
        ease=max(0,min(1,(z-.145)/.05,(.96-z)/.09))
        inside=abs(vertex.co.x)<.065 and z>.72
        group.add([vertex.index],0 if inside else .78*ease,'REPLACE')
    active(target); bpy.ops.object.modifier_apply(modifier=sw.name)
    # Modifier application can replace RNA data: reacquire, never skip absence.
    projected_group=target.vertex_groups.get('SelectedSculptProjection')
    assert projected_group is not None, 'Applied projection lost its named group'
    target.vertex_groups.remove(projected_group)
    # Restricted body-nearest initialization, then deliberate hip/knee field
    # transitions. Opposite-side leg and upper-body groups cannot leak across.
    source=np.load(bodypath); bv=source['vertices']; bf=source['faces']; coeff=source['nativeCoefficients']; names=source['jointNames'].tolist()
    pelvis={n for n in names if n in ('DEF-spine','DEF-pelvis.L','DEF-pelvis.R','DEF-spine.001')}
    trees={}
    for side,sign in [('L',1),('R',-1),('pelvis',0)]:
        chain={stem+'.'+side+suffix for stem in ('DEF-thigh','DEF-shin') for suffix in ('','.001')} if side in ('L','R') else set()
        allowed=pelvis|(set(names)&chain)
        cols=[names.index(n) for n in allowed]
        mask=(coeff[:,cols].sum(1)>.25)&(bv[:,2]>.10)&(bv[:,2]<1.13)
        if sign: mask&=bv[:,0]*sign>=-.008
        rows=np.flatnonzero(mask[bf].all(1)); trees[side]=(BVHTree.FromPolygons([Vector(p) for p in bv],bf[rows].tolist(),all_triangles=True),rows,allowed)
    groups={n:target.vertex_groups.new(name=n) for n in sorted(pelvis|{n for n in names if n.startswith(('DEF-thigh','DEF-shin'))})}
    for vertex in target.data.vertices:
        p=vertex.co; side='pelvis' if p.z>.95 else ('L' if p.x>=0 else 'R'); tree,rows,allowed=trees[side]
        hit,normal,local,distance=tree.find_nearest(p); tri=bv[bf[rows[local]]]
        a,b,c=tri; q=np.array(hit); u=b-a; v=c-a; d=q-a
        uu=float(np.sum(u*u)); vv=float(np.sum(v*v)); uv=float(np.sum(u*v)); du=float(np.sum(d*u)); dv=float(np.sum(d*v))
        den=uu*vv-uv*uv
        wb=(vv*du-uv*dv)/den; wc=(uu*dv-uv*du)/den
        weights=np.maximum([1-wb-wc,wb,wc],0); weights/=weights.sum(); field=np.einsum('i,ij->j',weights,coeff[bf[rows[local]]])
        row={n:float(field[i]) for i,n in enumerate(names) if n in allowed and field[i]>.0001}
        # Authored saddle/waist stays pelvis; broad leg fields remain initialized
        # from actual skin and receive a smooth hip bridge over 80 mm.
        if .87<p.z<.95:
            t=(p.z-.87)/.08; mass=sum(row.values()); row={n:w*(1-t) for n,w in row.items()}; row['DEF-spine']=row.get('DEF-spine',0)+mass*t
        total=sum(row.values()); assert total>0
        for n,w in row.items(): groups[n].add([vertex.index],w/total,'REPLACE')
    target.parent=rig; target.matrix_parent_inverse=Matrix.Identity(4)
    arm=target.modifiers.new('Shared75 selected jeans deformation','ARMATURE'); arm.object=rig; arm.use_deform_preserve_volume=False
    reference.hide_render=True; reference.hide_set(True); cage.hide_render=True; cage.hide_set(True)
    assert signature(body,rig)==before
    out.mkdir(parents=True); bpy.ops.wm.save_as_mainfile(filepath=str(out/'production-jeans.blend'))
    report={'accepted':False,'stage':'editable authored source; bake still required','bodyAnd75RestUntouched':True,'nativeSha256':SHA(native),'denseSha256':SHA(densepath),'vertices':len(target.data.vertices),'faces':len(target.data.polygons),'triangles':sum(len(p.vertices)-2 for p in target.data.polygons),'uvLayer':target.data.uv_layers.active.name,'sourceBlendSha256':SHA(out/'production-jeans.blend'),'controls':spec['cuff'],'structuralPolicy':'One authored pass; at most one targeted repair. No body hiding.'}
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')

def bake(spec,out):
    authored=Path(spec['authoredInput']).resolve(); assert authored.is_file()
    assert SHA(authored)==spec['authoredInputSha256'], 'Parent must pin actual authored result before bake'
    bpy.ops.wm.open_mainfile(filepath=str(authored))
    target=bpy.data.objects['RiderJeans']; source=bpy.data.objects['AlignedSelectedDenseJeans']
    rig=bpy.data.objects['RiderSkeleton']; body=bpy.data.objects['RiderBody']; before=signature(body,rig)
    scene=bpy.context.scene; scene.render.engine='CYCLES'; scene.cycles.device='CPU'; scene.cycles.samples=1
    scene.render.bake.use_selected_to_active=True; scene.render.bake.use_cage=True; scene.render.bake.cage_extrusion=.018; scene.render.bake.max_ray_distance=.045; scene.render.bake.margin=16
    out.mkdir(parents=True); dg=bpy.context.evaluated_depsgraph_get(); sm=bpy.data.meshes.new_from_object(source.evaluated_get(dg)); source.data=sm
    for m in list(source.modifiers): source.modifiers.remove(m)
    # Shared atlas, explicitly isolated upper/left/right source rays.
    regions=[('pelvis',lambda p:p.z>.84),('left',lambda p:p.z<=.84 and p.x>=0),('right',lambda p:p.z<=.84 and p.x<0)]
    baked={}; source_mat=source.data.materials[0]; sn=source_mat.node_tree.nodes; sl=source_mat.node_tree.links
    output=sn.get('Material Output'); bs=sn.get('Principled BSDF'); emission=sn.new('ShaderNodeEmission')
    original_albedo=next(n for n in sn if n.type=='TEX_IMAGE' and n.image.colorspace_settings.name=='sRGB')
    original_mr=next(n for n in sn if n.type=='TEX_IMAGE' and n!=original_albedo)
    destination=bpy.data.materials.new('ActualSelectedBakedDenimPBR'); destination.use_nodes=True
    dn=destination.node_tree.nodes; dl=destination.node_tree.links; image_node=dn.new('ShaderNodeTexImage'); target.data.materials.clear(); target.data.materials.append(destination)
    for label,kind,original in [('albedo','EMIT',original_albedo),('metallicRoughness','EMIT',original_mr),('normal','NORMAL',None)]:
        image=bpy.data.images.new('SelectedDenim_'+label,width=4096,height=4096,alpha=False); image.colorspace_settings.name='sRGB' if label=='albedo' else 'Non-Color'; image_node.image=image; dn.active=image_node
        if original: sl.new(original.outputs['Color'],emission.inputs['Color']); sl.new(emission.outputs[0],output.inputs['Surface'])
        else: sl.new(bs.outputs[0],output.inputs['Surface'])
        first=True
        for label_region,belongs in regions:
            # Temporary regional copies retain target corner UV and normals;
            # delete unrelated faces to prevent rays across neighbouring legs.
            import bmesh
            src=source.copy(); src.data=source.data.copy(); bpy.context.collection.objects.link(src); src.hide_render=False
            dst=target.copy(); dst.data=target.data.copy(); bpy.context.collection.objects.link(dst); dst.hide_render=False
            for o,is_source in [(src,True),(dst,False)]:
                for m in list(o.modifiers): o.modifiers.remove(m)
                original_normals=[tuple(v.normal) for v in o.data.vertices]
                bm=bmesh.new(); bm.from_mesh(o.data); original_id=bm.verts.layers.int.new('BakeOriginalIndex')
                for v in bm.verts: v[original_id]=v.index
                remove=[]
                for f in bm.faces:
                    p=f.calc_center_median()
                    keep=belongs(p)
                    if is_source:
                        keep=(p.z>.80 if label_region=='pelvis' else (p.z<.89 and (p.x>=-.004 if label_region=='left' else p.x<=.004)))
                    if not keep: remove.append(f)
                bmesh.ops.delete(bm,geom=remove,context='FACES'); bm.verts.ensure_lookup_table()
                kept_normals=[original_normals[v[original_id]] for v in bm.verts]
                bm.to_mesh(o.data); bm.free()
                o.data.normals_split_custom_set_from_vertices(kept_normals)
            active(dst); src.hide_set(False); src.select_set(True); scene.render.bake.use_clear=first; first=False
            bpy.ops.object.bake(type=kind); bpy.data.objects.remove(src,do_unlink=True); bpy.data.objects.remove(dst,do_unlink=True)
        image.filepath_raw=str(out/(label+'.png')); image.file_format='PNG'; image.save(); image.pack(); baked[label]=image
    bs=dn.get('Principled BSDF'); image_node.image=baked['albedo']; dl.new(image_node.outputs['Color'],bs.inputs['Base Color'])
    mr=dn.new('ShaderNodeTexImage'); mr.image=baked['metallicRoughness']; split=dn.new('ShaderNodeSeparateColor'); dl.new(mr.outputs[0],split.inputs[0]); dl.new(split.outputs['Green'],bs.inputs['Roughness']); dl.new(split.outputs['Blue'],bs.inputs['Metallic'])
    normal=dn.new('ShaderNodeTexImage'); normal.image=baked['normal']; convert=dn.new('ShaderNodeNormalMap'); dl.new(normal.outputs[0],convert.inputs['Color']); dl.new(convert.outputs[0],bs.inputs['Normal'])
    assert signature(body,rig)==before
    bpy.ops.wm.save_as_mainfile(filepath=str(out/'production-jeans-textured.blend'))
    (out/'report.json').write_text(json.dumps({'accepted':False,'bodyAnd75RestUntouched':True,'maps':{k:{'sha256':SHA(out/(k+'.png')),'size':4096} for k in baked},'sourceBlendSha256':SHA(authored),'resultSha256':SHA(out/'production-jeans-textured.blend'),'review':'Actual selected material inspection and complete played outfit required'},indent=2)+'\n')

if __name__=='__main__':
    args=sys.argv[sys.argv.index('--')+1:]; assert len(args)==3
    spec=json.loads(Path(args[0]).read_text()); out=Path(args[1]).resolve(); stage=args[2]
    assert not out.exists() and out.is_relative_to(ROOT/'harness/out/rider-rebuild/production-jeans01')
    assert spec['accepted'] is False and stage in ('author','bake')
    (author if stage=='author' else bake)(spec,out)
