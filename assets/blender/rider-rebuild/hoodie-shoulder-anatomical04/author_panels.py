"""ONE actual bilateral cloth-panel authoring pass in the private outfit.

SOURCE ONLY until parent checkpoint and global serial CPU2 lease.
blender -b -t 2 --python-exit-code 1 --python author_panels.py -- panel-controls.json FRESH_OUT
No body edit, fitting/projection modifier, sweep, normal displacement or bake.
"""
import hashlib
import json
import runpy
import sys
from pathlib import Path

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

ROOT=Path(__file__).resolve().parents[4]


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as handle:
        while block:=handle.read(1024*1024):h.update(block)
    return h.hexdigest()


def pin(row):
    p=ROOT/row['path'];assert sha(p)==row['sha256'],('Changed input',row['path'])
    return p


def smooth(a,b,x):
    t=max(0.,min(1.,(x-a)/(b-a)));return t*t*(3.-2.*t)


def sculpt(point,side,ease,influence,sag_fraction,spec):
    """Authored XYZ cloth cage. Body normals/nearest points are never inputs.

    The panel opens at its front/back seams and folds DOWN through the axillary
    air space, instead of stretching a flat source patch through the upper arm.
    Adjacent seam strips participate; historical derivative points are editable.
    """
    p=point.copy();sign=1. if side=='L' else -1.
    p.x+=sign*ease*influence
    depth=(1. if p.y>=0 else -1.)*smooth(0.,spec['frontRearTransitionM'],abs(p.y))
    p.y+=spec['frontRearEaseM']*depth*influence
    fold=1.-smooth(.045,spec['sagDepthSpanM'],abs(point.y))
    p.z-=spec['underarmFoldDropM']*fold*sag_fraction*influence
    return p


def interpolate(boundary,width,height):
    keys=([(0,j)for j in range(width+1)]+[(i,width)for i in range(1,height+1)]
          +[(height,j)for j in range(width-1,-1,-1)]+[(i,0)for i in range(height-1,0,-1)])
    grid=dict(zip(keys,boundary));assert len(grid)==len(boundary)
    top=[grid[0,j]for j in range(width+1)];bottom=[grid[height,j]for j in range(width+1)]
    left=[grid[i,0]for i in range(height+1)];right=[grid[i,width]for i in range(height+1)]
    for i in range(1,height):
        t=i/height
        for j in range(1,width):
            u=j/width
            bilinear=(1-t)*(1-u)*top[0]+(1-t)*u*top[-1]+t*(1-u)*bottom[0]+t*u*bottom[-1]
            grid[i,j]=(1-t)*top[j]+t*bottom[j]+(1-u)*left[i]+u*right[i]-bilinear
    return grid


def normalize(row):
    row=np.maximum(np.asarray(row,dtype=float),0.)
    total=row.sum();assert total>1e-8
    return row/total


def maps(obj):
    result={}
    for material in obj.data.materials:
        assert material and material.use_nodes
        for node in material.node_tree.nodes:
            if node.type=='TEX_IMAGE' and node.image:
                image=node.image;assert image.packed_file
                result[image.name]={'size':list(image.size),'sha256':hashlib.sha256(image.packed_file.data).hexdigest()}
    assert result
    return result


def source_chart(data,component,basis):
    # Intake vertices are ALREADY wearer-frame. Only raw identity attributes
    # receive selectedToWearerRows here; no geometry is transformed a second time.
    raw=np.asarray(data['attribute_0'],dtype=float)
    points=[basis@Vector(p)for p in raw]
    corners=data['cornerVertexIds'];starts=data['polygonStarts'];counts=data['polygonCounts']
    uv=data['cornerUV_0'];triangles=[];records=[]
    for fi in component['selectedSourceCandidateFaces']:
        start,count=int(starts[fi]),int(counts[fi]);loopids=list(range(start,start+count))
        for j in range(1,count-1):
            lids=[loopids[0],loopids[j],loopids[j+1]];ids=[int(corners[k])for k in lids]
            if any(points[k].length<1e-8 for k in ids):continue
            if (points[ids[1]]-points[ids[0]]).cross(points[ids[2]]-points[ids[0]]).length_squared<1e-16:continue
            triangles.append(ids);records.append({'face':fi,'sourceCornerIds':lids,'uv':uv[lids]})
    tree=BVHTree.FromPolygons(points,triangles,all_triangles=True)

    def lookup(raw_point):
        target=basis@Vector(raw_point)
        point,normal,index,distance=tree.find_nearest(target);assert point is not None
        ids=triangles[index];a,b,c=(points[k]for k in ids)
        ab,ac,ap=b-a,c-a,point-a
        d00,d01,d11=ab.dot(ab),ab.dot(ac),ac.dot(ac)
        denominator=d00*d11-d01*d01;assert abs(denominator)>1e-20
        v=(d11*ap.dot(ab)-d01*ap.dot(ac))/denominator
        w=(d00*ap.dot(ac)-d01*ap.dot(ab))/denominator
        bary=np.array([1-v-w,v,w]);bary=np.maximum(bary,0.);bary/=bary.sum()
        record=records[index]
        return bary@record['uv'],record['face'],bary,record['sourceCornerIds'],float(distance)

    return lookup


def main():
    args=sys.argv[sys.argv.index('--')+1:];assert len(args)==2
    cp,out=(Path(x).resolve()for x in args);c=json.loads(cp.read_text())
    assert not out.exists() and out.is_relative_to(ROOT/c['outputRoot'])
    rows=[v for v in c.values()if isinstance(v,dict)and 'path'in v and 'sha256'in v]
    for row in rows:pin(row)
    source=np.load(pin(c['selectedIntake']));intake=np.load(pin(c['compactIntake']))
    original_receipt=json.loads(pin(c['originalAuthorReceipt']).read_text())
    working_receipt=json.loads(pin(c['workingReceipt']).read_text())
    bpy.ops.wm.open_mainfile(filepath=str(pin(c['workingContext'])))
    obj,body,rig=(bpy.data.objects[c[key]]for key in ('targetObject','bodyObject','rigObject'))
    assert len(rig.data.bones)==75
    helpers=runpy.run_path(str(pin(c['baseAuthorHelpers'])))
    assert helpers['hoodie_geometry'](obj)==original_receipt['targetGeometrySHA256']
    before_body=helpers['signature'](body,rig)
    assert before_body==working_receipt['bodyAnd75RigSignature']
    assert np.array_equal(np.asarray([v.co[:]for v in obj.data.vertices]),intake['vertices'])
    original_maps=maps(obj)
    reference_maps=maps(bpy.data.objects[c['denseContextObject']])
    assert {v['sha256']for v in original_maps.values()}=={v['sha256']for v in reference_maps.values()}
    assert all(v['size']==[4096,4096]for v in original_maps.values())
    group_count=len(obj.vertex_groups)
    bm=bmesh.new();bm.from_mesh(obj.data)
    bm.verts.ensure_lookup_table();bm.faces.ensure_lookup_table()
    original_id=bm.verts.layers.int.new('_panel04_original_vertex_id')
    original_face=bm.faces.layers.int.new('_panel04_original_face_id')
    panel=bm.faces.layers.int.new('_panel04_side')
    source_face=bm.loops.layers.int.new('_panel04_selected_face_id')
    bary_layer=bm.loops.layers.float_vector.new('_panel04_selected_barycentric')
    source_corner_layers=[bm.loops.layers.int.new('_panel04_selected_corner_'+str(i))for i in range(3)]
    raw_layer=bm.verts.layers.float_vector['actual_donor_display_xyz']
    deform=bm.verts.layers.deform.active;assert deform is not None
    uv_layer=bm.loops.layers.uv.active;assert uv_layer is not None
    patch_layer=bm.faces.layers.int['_HOODIE_PATCH']
    for vertex in bm.verts:vertex[original_id]=vertex.index
    for face in bm.faces:
        face[original_face]=face.index
        for loop in face.loops:loop[source_face]=-1
    old_positions={v.index:v.co.copy()for v in bm.verts}
    old_rows={v.index:np.array([v[deform].get(i,0.)for i in range(group_count)])for v in bm.verts}
    components=[];removed=set();adjacent={}
    for component in c['components']:
        ids=component['removedFaces'];assert all(bm.faces[i][patch_layer]==component['patchValue']for i in ids)
        removed.update(ids)
        boundary=[bm.verts[i]for i in component['boundaryVertexIds']]
        components.append((component,boundary))
        for vertex in boundary:adjacent[vertex.index]=(1.,component)
        for influence,faces in zip(c['panelSculpt']['adjacentRingInfluences'],component['adjacentFaces']):
            for fi in faces:
                for vertex in bm.faces[fi].verts:
                    if vertex.index not in adjacent or influence>adjacent[vertex.index][0]:adjacent[vertex.index]=(influence,component)
    removed_vertices={v.index for fi in removed for v in bm.faces[fi].verts}
    boundary_ids={v.index for _,boundary in components for v in boundary}
    bmesh.ops.delete(bm,geom=[bm.faces[i]for i in sorted(removed)],context='FACES')
    moved=[]
    for vertex in bm.verts:
        index=vertex[original_id]
        if index in adjacent:
            influence,component=adjacent[index]
            vertex.co=sculpt(old_positions[index],component['side'],component['lateralEaseM'],influence,
                             c['panelSculpt']['boundarySagFraction'],c['panelSculpt'])
            moved.append({'originalVertex':index,'before':list(old_positions[index]),'after':list(vertex.co),
                          'influence':influence,'component':component['label']})
    basis=Matrix(c['selectedToWearerRows']);correspondence=[];component_records=[];identity_repairs=[]
    simplified=bm.faces.layers.int.get('simplified_donor_polygon')
    source22=bm.faces.layers.int.get('source22_polygon_id')
    for component,boundary in components:
        width,height=component['width'],component['height']
        raw=[np.asarray(v[raw_layer][:],dtype=float)for v in boundary]
        base=[np.asarray(old_positions[v[original_id]][:],dtype=float)for v in boundary]
        fields=[old_rows[v[original_id]]for v in boundary]
        valid=[i for i,p in enumerate(raw)if np.linalg.norm(p)>1e-8]
        assert len(valid)>=4, 'No adequate actual source identity anchors on this seam'
        # Generated old seam points have zero raw identity. Fill only that
        # missing material correspondence ALONG the known seam; never interpret
        # zero as a source location or infer a new body/garment surface from it.
        for i in range(len(raw)):
            if i in valid:continue
            before=next((i-j)%len(raw)for j in range(1,len(raw))if (i-j)%len(raw)in valid)
            after=next((i+j)%len(raw)for j in range(1,len(raw))if (i+j)%len(raw)in valid)
            path=[before];current=before
            while current!=after:current=(current+1)%len(raw);path.append(current)
            lengths=[np.linalg.norm(base[b]-base[a])for a,b in zip(path,path[1:])]
            total=sum(lengths);assert total>1e-8
            fraction=sum(lengths[:path.index(i)])/total
            raw[i]=raw[before]*(1-fraction)+raw[after]*fraction
            identity_repairs.append({'component':component['label'],'originalVertex':boundary[i][original_id],
                                     'beforeAnchor':boundary[before][original_id],'afterAnchor':boundary[after][original_id],
                                     'seamArcFraction':float(fraction),'kind':'MISSING_IDENTITY_INTERPOLATED_FOR_UV_ONLY'})
        seam_identity=dict(zip(boundary,raw))
        centers=[np.mean(values,axis=0)for values in (base,raw,fields)]
        lookup=source_chart(source,component,basis)
        new_faces=[];all_new=[]

        def vertex(point,identity,row,sag):
            v=bm.verts.new(sculpt(Vector(point),component['side'],component['lateralEaseM'],1.,sag,c['panelSculpt']))
            v[original_id]=-1;v[raw_layer]=Vector(identity)
            for i,weight in enumerate(normalize(row)):
                if weight>1e-8:v[deform][i]=float(weight)
            all_new.append(v);return v

        def face(vertices):
            f=bm.faces.new(vertices);f[panel]=component['patchValue'];f[patch_layer]=component['patchValue']
            f[original_face]=-1
            if simplified is not None:f[simplified]=-1
            if source22 is not None:f[source22]=-1
            f.material_index=0;f.smooth=True
            for loop in f.loops:
                uv,fi,bary,corners,distance=lookup(seam_identity.get(loop.vert,loop.vert[raw_layer]))
                loop[uv_layer].uv=uv;loop[source_face]=fi;loop[bary_layer]=Vector(bary)
                for layer,value in zip(source_corner_layers,corners):loop[layer]=value
                correspondence.append({'component':component['label'],'selectedFace':fi,'selectedCorners':corners,
                                       'barycentric':bary.tolist(),'UV':uv.tolist(),'identityFrameDistance':distance})
            new_faces.append(f)

        previous=boundary
        inner_base=base;inner_raw=raw;inner_fields=fields
        for factor in c['supportLoopInsetFactors']:
            inner_base=[centers[0]*(1-factor)+p*factor for p in base]
            inner_raw=[centers[1]*(1-factor)+p*factor for p in raw]
            inner_fields=[normalize(centers[2]*(1-factor)+p*factor)for p in fields]
            sag=c['panelSculpt']['boundarySagFraction']+(1-factor)*(1-c['panelSculpt']['boundarySagFraction'])
            ring=[vertex(p,r,w,sag)for p,r,w in zip(inner_base,inner_raw,inner_fields)]
            for i in range(len(boundary)):face((previous[i],previous[(i+1)%len(boundary)],ring[(i+1)%len(boundary)],ring[i]))
            previous=ring
        pgrid=interpolate(inner_base,width,height);rgrid=interpolate(inner_raw,width,height);wgrid=interpolate(inner_fields,width,height)
        perimeter=([(0,j)for j in range(width+1)]+[(i,width)for i in range(1,height+1)]
                   +[(height,j)for j in range(width-1,-1,-1)]+[(i,0)for i in range(height-1,0,-1)])
        grid=dict(zip(perimeter,previous))
        for i in range(1,height):
            for j in range(1,width):
                fullness=4*(i/height)*(1-i/height)*4*(j/width)*(1-j/width)
                sag=.55+.45*fullness
                grid[i,j]=vertex(pgrid[i,j],rgrid[i,j],wgrid[i,j],sag)
        for i in range(height):
            for j in range(width):face((grid[i,j],grid[i,j+1],grid[i+1,j+1],grid[i+1,j]))
        assert all(len(f.verts)==4 for f in new_faces)
        component_records.append({'component':component['label'],'side':component['side'],'layerRole':component['layerRole'],
                                  'actualRetainedSeamVertices':component['boundaryVertexIds'],
                                  'removedFaces':len(component['removedFaces']),'newQuads':len(new_faces),
                                  'newVertices':len(all_new),'newSupportLoops':2,
                                  'selectedChartSeedFaces':component['selectedSourceFaceSeeds']})
    bm.normal_update();bm.verts.index_update();bm.faces.index_update()
    new_panel_faces=[f for f in bm.faces if f[panel]in(1,2)]
    local_edges={e for f in new_panel_faces for e in f.edges}
    assert all(len(e.link_faces)==2 for e in local_edges), 'Authored panel has a local open/nonmanifold edge'
    bm.to_mesh(obj.data);bm.free();obj.data.update()
    assert maps(obj)==original_maps
    assert helpers['signature'](body,rig)==before_body
    assert not body.hide_render and not body.hide_get()
    dense=bpy.data.objects[c['denseContextObject']]
    dense.hide_render=True;dense.hide_set(True)
    obj.hide_render=False;obj.hide_viewport=False;obj.hide_set(False)
    obj['acceptedArt']=False;obj['contextStatus']='ONE_AUTHORED_CONCAVE_AXILLARY_PANEL_UNREVIEWED_ORIGINAL_SELECTED_PBR'
    obj['panel04RecipeSHA256']=sha(__file__);obj['panel04ControlsSHA256']=sha(cp)
    obj['panel04OriginalSelectedNativeSHA256']=c['selectedNative']['sha256']
    obj['changedTopologyNeedsDenseBake']=True
    visible=sorted(o.name for o in bpy.context.scene.objects if o.type=='MESH'and not o.hide_render)
    assert len(visible)==7 and obj.name in visible and body.name in visible and dense.name not in visible
    out.mkdir(parents=True)
    native=out/'selected-panel-outfit.blend'
    bpy.ops.wm.save_as_mainfile(filepath=str(native),compress=True)
    # Actual native is saved BEFORE any later output or review operation.
    (out/'selected-source-corner-correspondence.json').write_text(json.dumps(correspondence,separators=(',',':'))+'\n')
    (out/'moved-adjacent-cloth.json').write_text(json.dumps(moved,indent=2)+'\n')
    (out/'missing-source-identity-interpolation.json').write_text(json.dumps(identity_repairs,indent=2)+'\n')
    fields=np.zeros((len(obj.data.vertices),len(rig.data.bones)))
    names=[b.name for b in rig.data.bones];groups={g.index:g.name for g in obj.vertex_groups}
    for v in obj.data.vertices:
        for group in v.groups:
            if groups[group.group]in names:fields[v.index,names.index(groups[group.group])]=group.weight
    np.savez_compressed(out/'panel-native-fields.npz',vertices=np.asarray([v.co[:]for v in obj.data.vertices]),fields=fields,jointNames=np.asarray(names))
    result={'accepted':False,'stage':'ACTUAL_BILATERAL_PANEL_GEOMETRY_AND_SELECTED_UV_SAVED_IN_WORKING_OUTFIT',
            'native':{'path':str(native.relative_to(ROOT)),'sha256':sha(native)},'recipeSHA256':sha(__file__),
            'controlsSHA256':sha(cp),'targetObject':obj.name,'visibleMeshes':visible,
            'components':component_records,'movedRetainedClothVertices':len(moved),
            'vertices':len(obj.data.vertices),'polygons':len(obj.data.polygons),
            'newUVCornerCorrespondences':len(correspondence),'originalPackedMapsUnchanged':original_maps,
            'missingBoundaryIdentitiesInterpolatedAlongSeamForUVOnly':identity_repairs,
            'bodyAnd75RigUnchanged':True,'bodyAnd75RigSignature':before_body,
            'maximumNonzeroFieldCount':int(np.count_nonzero(fields>1e-8,axis=1).max()),
            'fullBoundaryInterpolationNoFourConditioning':True,'localPanelEdgesTwoIncidentFaces':True,
            'shapeControls':c['panelSculpt'],'limits':c['limits']+[
                'Local manifold edges and construction controls do not certify ease, clearance, body enclosure or selected form; parent judges actual clothed views.',
                'Explicit initial source UV correspondence is unreviewed; original dense panel alignment/bake and moving wearing review remain pending.']}
    (out/'author.json').write_text(json.dumps(result,indent=2)+'\n')
    for row in rows:pin(row)
    print('ACTUAL_SELECTED_PANEL_OUTFIT_SAVED',str(native),flush=True)


if __name__=='__main__':main()
