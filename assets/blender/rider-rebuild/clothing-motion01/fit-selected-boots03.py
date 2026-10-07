"""Intended-final selected boots: proper foot frame, real aperture, source ARAP.

Every exterior vertex/UV originates in the selected boot. The original wearer
is an obstacle only; neither its positions nor the source masters are edited.
"""
import hashlib
import json
import math
import importlib.util
import sys
from pathlib import Path
import bpy
import bmesh
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform

ROOT = Path(__file__).resolve().parents[4]
BODY = ROOT / 'docs/evidence/rider-rebuild/glove-charts01/target01/native-body.npz'
BODY_SHA = 'b34897b3c1fe810d7bd77806a1635f8132b3a43e66986986c218ab23cfad2f45'
NATIVE = ROOT / 'harness/out/rider-rebuild/selected-boot02/selected-boot-checkpoint.blend'
NATIVE_SHA = '2e836f508a9799325225affe2cbf1e6347c818ef3eaac2884c8cf48f56d435df'
SOURCE = ROOT / 'assets/blender/hero-remaster/rider/finish-2026-10-05/wardrobe/data/prep02/boots/retopology-prototype.npz'
SOURCE_SHA = 'd420da6bc7db4fa02ea095266dc174ff07cd3fb657cb0b01b91a319aa6b17853'
DENSE = SOURCE.with_name('cleaned-donor.npz')
DENSE_SHA = '9849de6444632c2dcd1e1d76fda42ac27a7cbe8c7d2c0263ab2082e24b94777f'
GEOMETRY = ROOT / 'assets/blender/rider-rebuild/glove-charts01/geometry-checks.py'
GEOMETRY_SHA = 'd9b6080dc6380b23e35eaf3978b539b930955e052c4254d869d7e7ff3b8746fa'
PADDING = .006; MINIMUM = .0035; INNER_ROOM = .001; ITERATIONS = 18
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
args = sys.argv[sys.argv.index('--') + 1:]; assert len(args) == 1
out = Path(args[0]).resolve(); out.mkdir(parents=True, exist_ok=False)
report = {'accepted': False, 'status': 'RUNNING', 'recipeSHA256': sha(__file__),
          'inputs': [{'path':str(p),'sha256':digest} for p,digest in ((BODY,BODY_SHA),(NATIVE,NATIVE_SHA),(SOURCE,SOURCE_SHA),(DENSE,DENSE_SHA),(GEOMETRY,GEOMETRY_SHA))],
          'bounds': {'outerPaddingGoalM':PADDING,'minimumOuterPaddingM':MINIMUM,'anatomicalInnerRoomM':INNER_ROOM,
                     'iterations':ITERATIONS,'maximumStepM':.008,'maximumBacktracks':13}, 'boots': []}
def save(): (out/'fit.json').write_text(json.dumps(report,indent=2)+'\n')
def arrays(mesh):
    mesh.calc_loop_triangles()
    return np.asarray([tuple(v.co) for v in mesh.vertices]), np.asarray([tuple(t.vertices) for t in mesh.loop_triangles],dtype=np.int32)
def topology(vertices, faces):
    edges=np.concatenate([faces[:,[0,1]],faces[:,[1,2]],faces[:,[2,0]]])
    unique,inverse,counts=np.unique(np.sort(edges,axis=1),axis=0,return_inverse=True,return_counts=True)
    signs=np.where(edges[:,0]<edges[:,1],1,-1); sums=np.bincount(inverse,weights=signs)
    return {'vertices':len(vertices),'triangles':len(faces),'boundaryEdges':int((counts==1).sum()),
            'nonmanifoldEdges':int((counts>2).sum()),'sameDirectionInteriorEdges':int((sums[counts==2]!=0).sum()),
            'EulerCharacteristic':len(vertices)-len(unique)+len(faces)}
def boundary_loop_count(edges):
    neighbors={}
    for edge in edges:
        for a,b in ((edge.verts[0],edge.verts[1]),(edge.verts[1],edge.verts[0])): neighbors.setdefault(a,[]).append(b)
    assert all(len(rows)==2 for rows in neighbors.values()),'Non-simple production aperture'
    unseen=set(neighbors); loops=0
    while unseen:
        loops+=1;stack=[unseen.pop()]
        while stack:
            for vertex in neighbors[stack.pop()]:
                if vertex in unseen:unseen.remove(vertex);stack.append(vertex)
    return loops

def executed_uv_lineage(obj, prototype, dense, side):
    # Reconstruct the exact old helper's executed query, compare it with native
    # UV bytes, and retain witnesses. This mapping is explicitly rejected as a
    # final atlas; a coherent unwrap/dense bake follows accepted geometry.
    xyz=[Vector(row) for row in dense['vertices']]; tri=dense['faces'].tolist()
    tree=BVHTree.FromPolygons(xyz,tri,all_triangles=True)
    rows=[]; barys=[]; reconstructed=[]
    for face in prototype['faces']:
        center=sum((Vector(prototype['vertices'][i]) for i in face),Vector())/3
        rr=[];bb=[];uu=[]
        for vertex in face:
            point=Vector(prototype['vertices'][vertex]);hit,_,row,_=tree.find_nearest(point.lerp(center,1e-4))
            original=tri[row];bary=barycentric_transform(hit,*(xyz[i] for i in original),Vector((1,0,0)),Vector((0,1,0)),Vector((0,0,1)))
            uv=barycentric_transform(hit,*(xyz[i] for i in original),*(Vector((float(p[0]),float(p[1]),0)) for p in dense['originalCornerUV'][row]))
            rr.append(row);bb.append(tuple(bary));uu.append((uv.x,uv.y))
        rows.append(rr);barys.append(bb);reconstructed.append(uu)
    rows=np.asarray(rows);barys=np.asarray(barys);reconstructed=np.asarray(reconstructed)
    if side=='L':rows=rows[:,::-1];barys=barys[:,::-1];reconstructed=reconstructed[:,::-1]
    actual=np.asarray([[tuple(obj.data.uv_layers.active.data[i].uv) for i in f.loop_indices] for f in obj.data.polygons])
    error=float(np.max(np.abs(actual-reconstructed)));assert error<2e-7,'Executed source UV query differs from reconstruction'
    return {'actualCornerUV':actual,'cornerDenseTriangleRows':rows,'cornerDenseOriginalFaces':dense['faces'][rows],
            'cornerDenseBarycentrics':barys,'cornerDenseOriginalUV':dense['originalCornerUV'][rows]},error

def body_snapshot(body):
    names = {g.index:g.name for g in body.vertex_groups}
    return [(tuple(v.co), sorted((names[g.group],g.weight) for g in v.groups if g.weight>0)) for v in body.data.vertices]
def normalize(v): return v/np.linalg.norm(v)
def orientation_path(before, after, faces):
    e1=before[faces[:,1]]-before[faces[:,0]]; e2=before[faces[:,2]]-before[faces[:,0]]
    delta=after-before; d1=delta[faces[:,1]]-delta[faces[:,0]]; d2=delta[faces[:,2]]-delta[faces[:,0]]
    normal=np.cross(e1,e2); c=(normal*normal).sum(1)
    a=(np.cross(d1,d2)*normal).sum(1); b=((np.cross(d1,e2)+np.cross(e1,d2))*normal).sum(1)
    minimum=np.minimum(c,a+b+c); t=np.divide(-b,2*a,out=np.zeros_like(a),where=a>0)
    mask=(a>0)&(t>0)&(t<1); minimum[mask]=np.minimum(minimum[mask],(a*t*t+b*t+c)[mask])
    return bool(np.all(minimum>1e-26))
def cg(a,b,weights,diagonal,rhs,start):
    count=len(diagonal)
    def apply(x):
        diff=(x[a]-x[b])*weights[:,None]; value=x*diagonal[:,None]
        for axis in range(3): value[:,axis]+=np.bincount(a,diff[:,axis],minlength=count)-np.bincount(b,diff[:,axis],minlength=count)
        return value
    degree=diagonal+np.bincount(np.r_[a,b],np.r_[weights,weights],minlength=count)
    x=start.copy(); residual=rhs-apply(x); z=residual/degree[:,None]; direction=z.copy(); rz=float((residual*z).sum())
    for _ in range(120):
        product=apply(direction); alpha=rz/max(float((direction*product).sum()),1e-30)
        x+=alpha*direction; residual-=alpha*product
        if np.linalg.norm(residual)<1e-7:break
        z=residual/degree[:,None]; updated=float((residual*z).sum()); direction=z+(updated/max(rz,1e-30))*direction; rz=updated
    return x,float(np.linalg.norm(residual))
def obstacle(points,tree):
    signed=[]; targets=[]
    for row in points:
        p=Vector(row); hit,normal,index,distance=tree.find_nearest(p)
        assert hit is not None and normal.length>.99
        signed.append(float(distance if (p-hit).dot(normal)>=0 else -distance))
        targets.append(tuple(hit+normal*PADDING))
    return np.asarray(signed),np.asarray(targets)
def directed_boundary(faces):
    edges=np.concatenate([faces[:,[0,1]],faces[:,[1,2]],faces[:,[2,0]]]);_,inv,count=np.unique(np.sort(edges,axis=1),axis=0,return_inverse=True,return_counts=True)
    boundary=edges[count[inv]==1];successor=dict(boundary.tolist())
    assert len(successor)==len(boundary)>=3 and len(set(successor.values()))==len(boundary),'Non-simple cuff'
    loop=[];cursor=int(boundary[0,0])
    while cursor not in loop:
        loop.append(cursor);cursor=successor[cursor]
    assert cursor==loop[0] and len(loop)==len(boundary),'More than one cuff loop'
    return np.asarray(loop,dtype=int)
def make_anatomical_cavity(foot_vertices,foot_faces,cuff):
    # Only the inward cavity follows actual anatomical skin. The selected source
    # exterior, including decorative handle topology, is never duplicated here.
    data=bpy.data.meshes.new('Temporary actual anatomical foot volume');data.from_pydata(foot_vertices,[],foot_faces)
    bm=bmesh.new();bm.from_mesh(data);bm.normal_update()
    for vertex in bm.verts:vertex.co+=vertex.normal*INNER_ROOM
    bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),plane_co=(0,0,cuff),plane_no=(0,0,1),clear_outer=True,dist=1e-7)
    bmesh.ops.triangulate(bm,faces=list(bm.faces));bm.verts.index_update()
    vertices=np.asarray([tuple(v.co) for v in bm.verts]);faces=np.asarray([[v.index for v in f.verts] for f in bm.faces],dtype=np.int32)
    bm.free();bpy.data.meshes.remove(data);loop=directed_boundary(faces)
    assert np.max(abs(vertices[loop,2]-cuff))<2e-6
    return vertices,faces,loop

def cuff_annulus(outer,outer_faces,inner,inner_faces):
    outer_loop=directed_boundary(outer_faces);inner_loop=directed_boundary(inner_faces);center=inner[inner_loop,:2].mean(0)
    def parameter(points,loop):
        angle=np.arctan2(points[loop,1]-center[1],points[loop,0]-center[0]);turn=(np.roll(angle,-1)-angle+np.pi)%(2*np.pi)-np.pi
        assert np.all(turn>1e-7) or np.all(turn< -1e-7),'Cuff is not a qualified radial loop'
        return float(np.sign(turn.sum()))
    direction=parameter(outer,outer_loop);assert parameter(inner,inner_loop)==direction,'Anatomical/source cuff winding mismatch'
    # Preserve boundary winding; choose a shared angular origin, then zipper the
    # two real loops. New bridge faces use opposite exterior boundary direction.
    def ordered(points,loop):
        angle=(direction*np.arctan2(points[loop,1]-center[1],points[loop,0]-center[0]))%(2*np.pi)
        start=int(np.argmin(angle));loop=np.roll(loop,-start);angle=np.roll(angle,-start)
        assert np.all(np.diff(angle)>0);return loop,np.r_[angle,angle[0]+2*np.pi]
    ol,oa=ordered(outer,outer_loop);il,ia=ordered(inner,inner_loop)
    # Every inner cuff point must lie strictly inside the selected outer cuff.
    poly=outer[ol,:2]
    for point in inner[il,:2]:
        delta=poly-point;angle=np.arctan2(delta[:,1],delta[:,0]);w=((np.roll(angle,-1)-angle+np.pi)%(2*np.pi)-np.pi).sum()
        assert abs(w)>np.pi,'Actual inner cuff is outside selected outer cuff'
    offset=len(outer);bridge=[];i=j=0
    while i<len(ol) or j<len(il):
        a=int(ol[i%len(ol)]);b=int(il[j%len(il)])+offset
        if j==len(il) or (i<len(ol) and oa[i+1]<=ia[j+1]):
            an=int(ol[(i+1)%len(ol)]);bridge.append([an,a,b]);i+=1
        else:
            bn=int(il[(j+1)%len(il)])+offset;bridge.append([a,b,bn]);j+=1
    return np.asarray(bridge,dtype=np.int32),len(ol),len(il)

def target_foot(body,side,cuff):
    bm=bmesh.new(); bm.from_mesh(body.data)
    bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),plane_co=(0,0,cuff),plane_no=(0,0,1),clear_outer=True,dist=1e-7)
    sign=1 if side=='L' else -1
    bmesh.ops.delete(bm,geom=[v for v in bm.verts if v.co.x*sign<0],context='VERTS')
    boundary=[e for e in bm.edges if e.is_boundary]
    assert boundary and all(abs(v.co.z-cuff)<2e-6 for e in boundary for v in e.verts)
    bmesh.ops.holes_fill(bm,edges=boundary,sides=0); bmesh.ops.triangulate(bm,faces=list(bm.faces))
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    if bm.calc_volume(signed=True)<0:bmesh.ops.reverse_faces(bm,faces=list(bm.faces))
    assert all(e.is_manifold for e in bm.edges)
    bm.verts.index_update(); vertices=np.asarray([tuple(v.co) for v in bm.verts]); faces=np.asarray([[v.index for v in f.verts] for f in bm.faces],dtype=np.int32)
    bm.free(); return vertices,faces
try:
    assert all(sha(p)==digest for p,digest in ((BODY,BODY_SHA),(NATIVE,NATIVE_SHA),(SOURCE,SOURCE_SHA),(DENSE,DENSE_SHA),(GEOMETRY,GEOMETRY_SHA)))
    target=dict(np.load(BODY)); source=dict(np.load(SOURCE)); dense=dict(np.load(DENSE)); names=target['jointNames'].tolist()
    spec=importlib.util.spec_from_file_location('boot_geometry',GEOMETRY);geometry=importlib.util.module_from_spec(spec);spec.loader.exec_module(geometry)
    report['geometryHelperSHA256']=sha(GEOMETRY);report['sourceClosedTopologyAudit']=topology(source['vertices'],source['faces'])
    assert report['sourceClosedTopologyAudit']['boundaryEdges']==0 and report['sourceClosedTopologyAudit']['nonmanifoldEdges']==0
    bpy.ops.wm.open_mainfile(filepath=str(NATIVE)); body=bpy.data.objects['RiderBody']; rig=bpy.data.objects['RiderSkeleton']
    original_body=body_snapshot(body); original_rest=[(b.name,tuple(b.head_local),tuple(b.tail_local),tuple(tuple(row) for row in b.matrix_local)) for b in rig.data.bones]
    assert np.array_equal(target['vertices'],np.asarray([tuple(v.co) for v in body.data.vertices]))
    for side in ('R','L'):
        obj=bpy.data.objects['ActualSelectedBoot.'+side]; donor=source['vertices'].astype(np.float64).copy()
        lineage,uv_error=executed_uv_lineage(obj,source,dense,side)
        np.savez_compressed(out/('executed-input-uv-lineage-'+side+'.npz'),**lineage,compactVertices=source['vertices'],compactFaces=source['faces'] if side=='R' else source['faces'][:,::-1],
                            prototypeOriginalTriangleRows=source['originalTriangleRows'],prototypeBarycentric=source['barycentric'])
        if side=='L':donor[:,2]*=-1
        ankle=target['jointHeads'][names.index('DEF-foot.'+side)]; toe=target['jointHeads'][names.index('DEF-toe.'+side)]
        forward=normalize(np.r_[toe[:2]-ankle[:2],0]); up=np.array([0.,0.,1.]); lateral=np.cross(-forward,up)
        frame=np.column_stack([-forward,up,lateral]); assert np.linalg.det(frame)>1-1e-12
        cuff=ankle[2]+.125
        foot_v,foot_f=target_foot(body,side,cuff+.025)
        field_ids=[names.index('DEF-foot.'+side),names.index('DEF-toe.'+side)]
        footprint=target['vertices'][(target['nativeCoefficients'][:,field_ids].sum(1)>.25)&(target['vertices'][:,2]<ankle[2]+.025)]
        local=footprint@frame; low,high=local.min(0),local.max(0); source_low,source_high=donor.min(0),donor.max(0)
        low[0]-=.016;high[0]+=.016;low[2]-=.014;high[2]+=.014
        low[1]=float(footprint[:,2].min())-.007;high[1]=cuff+.010
        scales=(high-low)/(source_high-source_low)
        calibrated=((donor-source_low)*scales+low)@frame.T
        source_to_native=np.eye(4);mirror=np.diag([1.,1.,-1. if side=='L' else 1.])
        source_to_native[:3,:3]=frame@np.diag(scales)@mirror;source_to_native[:3,3]=frame@(low-source_low*scales)
        assert np.allclose(source['vertices']@source_to_native[:3,:3].T+source_to_native[:3,3],calibrated,atol=1e-12)
        assert len(obj.data.vertices)==len(calibrated)
        for v,p in zip(obj.data.vertices,calibrated):v.co=p
        # Closed voxel caps are not garment ports. Cut a source-derived aperture;
        # untouched exterior faces/UVs and their original point IDs survive.
        bm=bmesh.new();bm.from_mesh(obj.data);vi=bm.verts.layers.int.new('_SOURCE_VERTEX_ID');fi=bm.faces.layers.int.new('_SOURCE_FACE_ID')
        bm.verts.index_update();bm.faces.index_update()
        for v in bm.verts:v[vi]=v.index
        for f in bm.faces:f[fi]=f.index
        before_vertices=set(bm.verts);before_faces=len(bm.faces)
        bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),plane_co=(0,0,cuff),plane_no=(0,0,1),clear_outer=True,dist=1e-7)
        cut=[v for v in bm.verts if v not in before_vertices]
        for v in cut:v[vi]=-1
        boundary=[e for e in bm.edges if e.is_boundary]
        assert boundary_loop_count(boundary)==1,'Production boot requires exactly one real ankle aperture'
        assert boundary and all(abs(v.co.z-cuff)<2e-6 for e in boundary for v in e.verts)
        bm.to_mesh(obj.data);bm.free();obj.data.update();points,faces=arrays(obj.data)
        record={'side':side,'properFootFrame':frame.tolist(),'toeOutRadians':float(math.atan2(abs(forward[0]),-forward[1])),
                'inheritedUVMappingAccepted':False,'executedInputUVReconstructionMaximumError':uv_error,
                'UVFinish':'Pending coherent compact unwrap + dense original map bake; inherited mapping is evidence only',
                'sourceToNativeAffine':source_to_native.tolist(),'sourceObjectMatrixWorld':np.asarray(obj.matrix_world).tolist(),
                'initialScales':scales.tolist(),'sourceApertureCutNativeZ':float(cuff),'originalClosedBoundaryEdges':report['sourceClosedTopologyAudit']['boundaryEdges'],
                'derivedCutVertices':len(cut),'sourceFaceCountBeforeCut':before_faces,'sourceFaceCountAfterCut':len(obj.data.polygons),
                'apertureBoundaryEdges':len(boundary),'mathematicalBodyCuffZ':float(cuff+.025),'iterations':[]}
        report['boots'].append(record);save()
        reference=points.copy();edges=np.unique(np.sort(np.concatenate([faces[:,[0,1]],faces[:,[1,2]],faces[:,[2,0]]]),axis=1),axis=0)
        a,b=edges.T;original_edges=reference[a]-reference[b];length=np.linalg.norm(original_edges,axis=1)
        assert length.min()>1e-9;weights=np.median(length)/length
        obstacle_tree=BVHTree.FromPolygons([Vector(p) for p in foot_v],foot_f.tolist(),all_triangles=True)
        current=reference.copy()
        for iteration in range(ITERATIONS):
            e=current[a]-current[b];covariance=np.zeros((len(current),3,3));products=np.einsum('ni,nj->nij',e,original_edges)*weights[:,None,None]
            np.add.at(covariance,a,products);np.add.at(covariance,b,products);u,_,vh=np.linalg.svd(covariance)
            correction=np.ones((len(current),3));correction[:,2]=np.linalg.det(u@vh);rotation=(u*correction[:,None,:])@vh
            desired=np.einsum('nij,nj->ni',(rotation[a]+rotation[b])*.5,original_edges)*weights[:,None]
            rhs=np.zeros_like(current)
            for axis in range(3):rhs[:,axis]=np.bincount(a,desired[:,axis],minlength=len(current))-np.bincount(b,desired[:,axis],minlength=len(current))
            signed,targets=obstacle(current,obstacle_tree);active=signed<PADDING;contacts=active.astype(float)*120
            candidate,residual=cg(a,b,weights,contacts+.25,rhs+contacts[:,None]*targets+.25*reference,current)
            assert np.isfinite(candidate).all() and residual<1e-4,'Unconverged ARAP linear solve';maximum=float(np.linalg.norm(candidate-current,axis=1).max());step=min(1.,.008/max(maximum,1e-12))
            for backtrack in range(13):
                proposed=current+step*(candidate-current)
                if orientation_path(current,proposed,faces):break
                step*=.5
            else:raise AssertionError('No orientation-preserving selected source step')
            current=proposed;record['iterations'].append({'iteration':iteration,'contacts':int(active.sum()),'minimumVertexSignedM':float(signed.min()),'CGResidual':residual,'step':step,'backtracks':backtrack})
        for v,p in zip(obj.data.vertices,current):v.co=p
        obj.data.update();signed,_=obstacle(current,obstacle_tree);centroids=current[faces].mean(1);center_signed,_=obstacle(centroids,obstacle_tree)
        deformation=geometry.deformation_metrics(current,reference,faces)
        record['minimumPrincipalStretch']=float(deformation['principalStretches'].min());record['maximumPrincipalStretch']=float(deformation['principalStretches'].max())
        record['maximumSourceDisplacementM']=float(np.linalg.norm(current-reference,axis=1).max())
        corner_uv=np.asarray([[tuple(obj.data.uv_layers.active.data[i].uv) for i in t.loops] for t in obj.data.loop_triangles])
        source_face_ids=np.asarray([obj.data.attributes['_SOURCE_FACE_ID'].data[t.polygon_index].value for t in obj.data.loop_triangles])
        source_vertex_ids=np.asarray([v.value for v in obj.data.attributes['_SOURCE_VERTEX_ID'].data]);valid=source_vertex_ids>=0
        full_fitted=np.full((len(source['vertices']),3),np.nan);full_fitted[source_vertex_ids[valid]]=current[valid]
        valid_original=np.isfinite(full_fitted).all(1)
        record['appearanceSupportPolicy']='Postcut source-coordinate triangles paired with fitted triangles; removed original cap points are invalid/NaN and masked. New anatomical cavity/rim needs separate atlas support.'
        np.savez_compressed(out/('fitted-outer-'+side+'.npz'),vertices=current,referenceVertices=reference,faces=faces,
                            sourceVertexIDs=source_vertex_ids,sourceFaceIDs=source_face_ids,
                            originalCompactFittedVerticesNative=full_fitted,originalCompactFittedValid=valid_original,
                            removedOriginalCompactVertexIDs=np.flatnonzero(~valid_original),
                            sourceCompactVertices=source['vertices'],sourceCompactFaces=source['faces'],
                            nativeOriginalCompactFaces=source['faces'] if side=='R' else source['faces'][:,::-1],
                            initialOriginalCompactVerticesNative=calibrated,sourceToNativeAffine=source_to_native,
                            cutReferenceVerticesSource=(reference-source_to_native[:3,3])@np.linalg.inv(source_to_native[:3,:3]).T,
                            nativeObjectMatrixWorld=np.asarray(obj.matrix_world),
                            actualCornerUV=corner_uv,vertexClearance=signed,triangleCentroidClearance=center_signed,**deformation)
        assert record['minimumPrincipalStretch']>.15 and record['maximumPrincipalStretch']<3,'Catastrophic selected source chart deformation'
        record['minimumOuterVertexClearanceM']=float(signed.min());record['minimumOuterCentroidClearanceM']=float(center_signed.min());save()
        assert min(signed.min(),center_signed.min())>=MINIMUM,'Selected outer remains through actual foot; reject before cavity/native output'
        # Anatomical skin defines only a coherent inner cavity with real cuff;
        # selected lace/handle surface is never copied inward as thin geometry.
        inner_points,inner_faces,inner_loop=make_anatomical_cavity(foot_v,foot_f,cuff)
        bridge,outer_cuff_count,inner_cuff_count=cuff_annulus(current,faces,inner_points,inner_faces)
        all_points=np.vstack([current,inner_points]);all_faces=np.vstack([faces,inner_faces[:,::-1]+len(current),bridge])
        shell_topology=topology(all_points,all_faces);record['shellTopology']=shell_topology
        assert shell_topology['boundaryEdges']==shell_topology['nonmanifoldEdges']==shell_topology['sameDirectionInteriorEdges']==0,'Cavity/cuff shell is not oriented closed manifold'
        new_data=bpy.data.meshes.new('Actual selected boot outer and anatomical cavity '+side);new_data.from_pydata(all_points,[],all_faces);new_data.update()
        for material in obj.data.materials:new_data.materials.append(material)
        uv=new_data.uv_layers.new(name='UVMap');identity=new_data.attributes.new('_SOURCE_VERTEX_ID','INT','POINT');face_identity=new_data.attributes.new('_SOURCE_FACE_ID','INT','FACE');role=new_data.attributes.new('_SOURCE_OUTER_FACE','INT','FACE')
        for i,value in enumerate(np.r_[source_vertex_ids,np.full(len(inner_points),-1)]):identity.data[i].value=int(value)
        for face in new_data.polygons:
            is_outer=face.index<len(faces);role.data[face.index].value=int(is_outer);face_identity.data[face.index].value=int(source_face_ids[face.index]) if is_outer else -1;face.use_smooth=True
            if is_outer:
                for loop,value in zip(face.loop_indices,corner_uv[face.index]):uv.data[loop].uv=value
        obj.data=new_data;native_points,native_faces=arrays(obj.data)
        assert np.array_equal(native_points[:len(current)],np.asarray(current,dtype=np.float32).astype(np.float64)),'Source exterior moved during cavity construction'
        inner_signed,_=obstacle(inner_points,obstacle_tree);record['minimumAnatomicalCavityVertexClearanceM']=float(inner_signed.min());record['outerCuffVertices']=outer_cuff_count;record['innerCuffVertices']=inner_cuff_count
        record['cavityReference']='Complete actual foot/calf mathematical volume, outward1mm room, true calf cuff; source decorative genus remains outer only'
        np.savez_compressed(out/('anatomical-cavity-'+side+'.npz'),vertices=inner_points,faces=inner_faces,cuffLoop=inner_loop,bridgeFaces=bridge)
        save();assert inner_signed.min()>=.0005,'Anatomical inner cavity intersects actual foot'
        # New fields derive from actual anatomical source triangles only.
        body.data.calc_loop_triangles();body_triangles=[list(t.vertices) for t in body.data.loop_triangles if all(body.data.vertices[i].co.x*(1 if side=='L' else -1)>0 and body.data.vertices[i].co.z<cuff+.07 for i in t.vertices)]
        body_xyz=[v.co.copy() for v in body.data.vertices];field_tree=BVHTree.FromPolygons(body_xyz,body_triangles,all_triangles=True)
        obj.vertex_groups.clear();groups={}
        for v in obj.data.vertices:
            hit,_,row,_=field_tree.find_nearest(v.co);triangle=body_triangles[row]
            bary=barycentric_transform(hit,*(body_xyz[i] for i in triangle),Vector((1,0,0)),Vector((0,1,0)),Vector((0,0,1)))
            field=sum(target['nativeCoefficients'][i]*max(0,w) for i,w in zip(triangle,bary));slots=np.argsort(field)[::-1][:4];total=float(field[slots].sum());assert total>0
            for slot in slots:
                if field[slot]<=0:continue
                name=names[int(slot)]
                if name not in groups:groups[name]=obj.vertex_groups.new(name=name)
                groups[name].add([v.index],float(field[slot]/total),'REPLACE')
        record['nativeShellVertices']=len(obj.data.vertices);record['nativeShellTriangles']=len(native_faces)
        record['sourcePackedMapsPreserved']=all(n.image.packed_file for m in obj.data.materials for n in m.node_tree.nodes if n.type=='TEX_IMAGE' and n.image)
    assert original_body==body_snapshot(body)
    assert original_rest==[(b.name,tuple(b.head_local),tuple(b.tail_local),tuple(tuple(row) for row in b.matrix_local)) for b in rig.data.bones]
    assert all(sha(p)==digest for p,digest in ((BODY,BODY_SHA),(NATIVE,NATIVE_SHA),(SOURCE,SOURCE_SHA),(DENSE,DENSE_SHA),(GEOMETRY,GEOMETRY_SHA)))
    bpy.ops.wm.save_as_mainfile(filepath=str(out/'selected-boots03.blend'))
    report.update(status='SOURCE_FIT_CANDIDATE_UNACCEPTED_REQUIRES_FULL_SURFACE_AND_PLAYED_REVIEW',bodyAnd75RestUntouched=True,
                  native={'path':str(out/'selected-boots03.blend'),'sha256':sha(out/'selected-boots03.blend')},
                  limits=['Vertex/centroid clearance is measured; complete surface intersections and actual foot enclosure require independent qualification.',
                          'Selected detailed source outer remains with explicit aperture and anatomical inner cavity. Inherited compact UV is unaccepted and requires coherent unwrap plus dense original map bake; parent judges actual front/side played evidence.',
                          'SoleSocket and complete-source driver calibration must derive from accepted actual final soles; no old floor is inherited as acceptance.'])
except Exception as error:
    report['status']='REJECTED_BEFORE_NATIVE_CANDIDATE';report['error']=type(error).__name__+': '+str(error);raise
finally:
    save();print(json.dumps({key:report[key] for key in ('status','error','native') if key in report}))
