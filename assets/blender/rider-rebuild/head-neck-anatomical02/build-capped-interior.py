"""One deliberately authored neck derivative; parent CPU2 lease required. Exact secondary opening cap derivative.

Native42f supplies the coherent thorax/clavicle/trapezius anatomy and exact
shared75 rest. Selected b7f supplies genuine facial/hair geometry and maps.
New circumferential neck sections replace both failed collar regions.
No source file is edited, and new neck topology/UV/weights are not source-exact.
"""
import hashlib
import json
import math
import struct
import sys
from pathlib import Path

import bpy
import bmesh
import numpy as np
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
NATIVE = ROOT/'harness/out/rider-rebuild/native-hand-repair01/native02/anatomical-hand-rig.blend'
ARRAYS = NATIVE.with_name('native-body.npz')
DONOR = Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/rig-adapter01/body-bind11/rider.glb')
PINS = {str(NATIVE): '42fca617ea8d246a6c3e3ca68a90cd3cb5f3ce8b9bb78130e0e2bbd65f605fac',
        str(ARRAYS): 'e62e9969503b7761e99463eccc3ca7be39e0c230a2948f2f87a224db52d0f9a2',
        str(DONOR): 'b7f4f22790124c664f9907104e5b17b77775b4c5c995f715d62be640bbcc8754'}

PINS[str(ROOT/'harness/out/rider-rebuild/head-neck-anatomical02/shell-diagnostic01/report.json')]='ba860951b21c9447c5c2f08b98bae18e2812ff5f02460fabeaf23d5799b56dea'

def rest(rig):
    return [{'name':b.name, 'parent':b.parent.name if b.parent else None,
        'head':list(b.head_local), 'tail':list(b.tail_local),
        'matrix':[list(r) for r in b.matrix_local], 'connect':b.use_connect,
        'deform':b.use_deform} for b in rig.data.bones]


def field(vertex):
    return sorted((g.group,g.weight) for g in vertex.groups)


def lower_height(co):
    # Jugular notch/front upper chest -> lateral trapezius -> C7 upper back.
    # Outside the central neck the rising surface leaves canonical shoulders.
    return 1.438 + 2.0*co.x*co.x + .20*(co.y+.04)


def upper_height(co):
    # Under-chin -> jaw angle/mastoid -> occipital attachment; oblique, not collar.
    return 1.555 + .36*(co.y+.07) + .5*co.x*co.x


def cut(bm, vertices, faces, height, keep_above):
    original = {v:v.co.copy() for v in vertices}
    all_before = set(bm.verts)
    edges = {e for f in faces for e in f.edges}
    for v in vertices: v.co.z -= height(v.co)
    bmesh.ops.bisect_plane(bm, geom=list(vertices)+list(edges)+list(faces),
        plane_co=(0,0,0), plane_no=(0,0,1), dist=1e-7,
        clear_inner=keep_above, clear_outer=not keep_above)
    for v in list(bm.verts):
        if v in original:
            v.co = original[v]
        elif v not in all_before:
            v.co.z += height(v.co)
    return {v for v in original if v.is_valid}


def boundaries(bm, belongs):
    edges={e for e in bm.edges if e.is_boundary and any(belongs(f) for f in e.link_faces)}
    adjacency={}
    for e in edges:
        for v in e.verts:adjacency.setdefault(v,[]).append(e)
    assert all(len(es)==2 for es in adjacency.values()), 'Non-circular domain boundary'
    rings=[]
    while edges:
        e=next(iter(edges)); start=e.verts[0]; v=start; ring=[]
        while True:
            ring.append(v); e=next(e for e in adjacency[v] if e in edges)
            edges.remove(e); v=e.other_vert(v)
            if v==start:break
        rings.append(ring)
    return rings


def area(ring):
    return sum(a.co.x*b.co.y-b.co.x*a.co.y for a,b in zip(ring,ring[1:]+ring[:1]))/2


def ordered(ring):
    if area(ring)<0:ring=list(reversed(ring))
    # Geometric angle about the spine column; starts at anterior median.
    k=min(range(len(ring)), key=lambda i:math.atan2(ring[i].co.x,-ring[i].co.y)%(2*math.pi))
    return ring[k:]+ring[:k]


def polar(ring):
    angles=[math.atan2(v.co.x,-v.co.y)%(2*math.pi) for v in ring]
    # Actual selected boundary has small scanned angular reversals. Arc ordering
    # is retained; continuous parameter is cumulative contour length.
    d=[0.]
    for a,b in zip(ring,ring[1:]+ring[:1]):d.append(d[-1]+(a.co-b.co).length)
    return [x/d[-1] for x in d]


def sample(ring, arcs, u):
    i=next((i for i in range(len(ring)) if arcs[i+1]>=u),len(ring)-1)
    t=(u-arcs[i])/(arcs[i+1]-arcs[i]);a,b=ring[i],ring[(i+1)%len(ring)]
    return a.co.lerp(b.co,t)


def cubic(rows, t):
    # Catmull derivatives through the explicitly authored anatomical stations:
    # continuous longitudinal tangent, not a separate eased linear frustum.
    ts=[r[0] for r in rows]
    k=next((i for i in range(len(ts)-1) if ts[i+1]>=t),len(ts)-2)
    a,b=rows[k],rows[k+1];dt=b[0]-a[0];u=(t-a[0])/dt
    before=rows[max(0,k-1)];after=rows[min(len(rows)-1,k+2)]
    ma=(b[1]-before[1])/(b[0]-before[0])
    mb=(after[1]-a[1])/(after[0]-a[0])
    return ((2*u**3-3*u*u+1)*a[1]+(u**3-2*u*u+u)*dt*ma+
            (-2*u**3+3*u*u)*b[1]+(u**3-u*u)*dt*mb)


def main():
    args=sys.argv[sys.argv.index('--')+1:];assert len(args)==1
    out=Path(args[0]).resolve();assert out==ROOT/'harness/out/rider-rebuild/head-neck-anatomical02/native02' and not out.exists()
    for p,d in PINS.items():assert sha(p)==d,('Source changed',p)
    out.mkdir(parents=True)
    bpy.ops.wm.open_mainfile(filepath=str(NATIVE))
    body,rig=bpy.data.objects['RiderBody'],bpy.data.objects['RiderSkeleton']
    assert len(body.data.vertices)==10582 and len(rig.data.bones)==75
    before_rest=rest(rig);data=np.load(ARRAYS);ids=body.data.attributes['_SOURCE_VERTEX_ID'].data
    original={int(ids[v.index].value):(tuple(v.co),field(v)) for v in body.data.vertices}
    assert len(original)==10582
    groups={g.name:g.index for g in body.vertex_groups}
    body_materials=list(body.data.materials)
    bm=bmesh.new();bm.from_mesh(body.data)
    source_id=bm.verts.layers.int.get('_SOURCE_VERTEX_ID')
    assert source_id
    deform=bm.verts.layers.deform.verify();uv=bm.loops.layers.uv.verify()
    source_face=bm.faces.layers.int.new('SelectedSourceFace')
    ancestry=bm.faces.layers.int.new('AuthoredNeckDomain')
    raw_normal=bm.loops.layers.float_vector.new('GenuineSelectedCornerNormal')
    for f in bm.faces:f[source_face]=-1;f[ancestry]=0
    old_vertices=set(bm.verts);cut(bm,old_vertices,list(bm.faces),lower_height,False)
    for v in bm.verts:
        if v not in old_vertices:v[source_id]=-1
    lower_rings=boundaries(bm,lambda f:f[source_face]<0)
    assert len(lower_rings)==1,('Canonical neck boundary must be one loop',len(lower_rings))
    lower=ordered(lower_rings[0]);lower_arc=polar(lower)
    raw=DONOR.read_bytes();length=struct.unpack_from('<I',raw,12)[0];doc=json.loads(raw[20:20+length]);binary=memoryview(raw)[28+length:]
    def accessor(i):
        a=doc['accessors'][i];v=doc['bufferViews'][a['bufferView']]
        dtype={5126:'<f4',5125:'<u4',5123:'<u2',5121:'u1'}[a['componentType']]
        n={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a['type']];w=np.dtype(dtype).itemsize
        return np.ndarray((a['count'],n),dtype=dtype,buffer=binary,offset=v.get('byteOffset',0)+a.get('byteOffset',0),strides=(v.get('byteStride',n*w),w)).copy()
    head_node=next(n for n in doc['nodes'] if n.get('name')=='textured');primitives=doc['meshes'][head_node['mesh']]['primitives']
    before=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(DONOR),merge_vertices=False)
    imported=set(bpy.data.objects)-before
    donor_object=next(o for o in imported if o.type=='MESH' and len(o.data.vertices)==61393)
    donor_materials=list(donor_object.data.materials)
    for o in imported:bpy.data.objects.remove(o,do_unlink=True)
    material_offset=len(body_materials)
    for m in donor_materials:body.data.materials.append(m)
    scale=1.78/1.8225715160369873
    donor_vertices=[];donor_faces=[];lookup={};projection_positions=[];projection_triangles=[];projection_uv=[];projection_material=[]
    for part,primitive in enumerate(primitives):
        points=accessor(primitive['attributes']['POSITION']);tex=accessor(primitive['attributes']['TEXCOORD_0']);norm=accessor(primitive['attributes']['NORMAL']);faces=accessor(primitive['indices']).reshape(-1,3)
        converted=np.c_[-points[:,2],-(points[:,0]-.65),points[:,1]]*scale
        offset=len(projection_positions);projection_positions.extend(converted.tolist())
        mapping=[]
        for index,(row,co) in enumerate(zip(points,converted)):
            key=tuple(row)
            if key not in lookup:
                v=bm.verts.new(co);v[source_id]=1000000+part*100000+index
                v[deform][groups['DEF-spine.006']]=1.;lookup[key]=v;donor_vertices.append(v)
            mapping.append(lookup[key])
        for index,triangle in enumerate(faces):
            vs=[mapping[int(i)] for i in triangle]
            if len(set(vs))<3:continue
            try:f=bm.faces.new(vs)
            except ValueError:continue
            f[source_face]=part*1000000+index;f[ancestry]=0;f.material_index=material_offset+part;f.smooth=True
            for loop,i in zip(f.loops,triangle):
                loop[uv].uv=(float(tex[i][0]),1-float(tex[i][1]))
                loop[raw_normal]=Vector((-norm[i][2],-norm[i][0],norm[i][1])).normalized()
            donor_faces.append(f)
            if all(1.475<converted[int(i)][2]<1.615 for i in triangle):
                projection_triangles.append([offset+int(i) for i in triangle]);projection_uv.append([(float(tex[i][0]),1-float(tex[i][1])) for i in triangle]);projection_material.append(part)
    before_cut=set(bm.verts)
    cut(bm,set(donor_vertices),donor_faces,upper_height,True)
    for v in bm.verts:
        if v not in before_cut:v[source_id]=-1
    upper_rings=boundaries(bm,lambda f:f[source_face]>=0)
    upper_rings.sort(key=lambda r:abs(area(r)),reverse=True)
    assert len(upper_rings) in (1,2),('Unexpected selected submental openings',len(upper_rings))
    upper=ordered(upper_rings[0]);upper_arc=polar(upper)
    # The actual raw diagnostic found zero exact triangle-UV pairs. No inferred
    # inner-layer or ear faces are deleted. Close only the measured inner cut
    # opening, retaining the existing connected inner-head surface honestly.
    inner_removed=0;inner_cap_faces=0;inner_cap_records=[]
    def inside_outer(point):
        x,y=point.x,point.y;inside=False
        for a,b in zip(upper,upper[1:]+upper[:1]):
            if (a.co.y>y)!=(b.co.y>y):
                crossing=(b.co.x-a.co.x)*(y-a.co.y)/(b.co.y-a.co.y)+a.co.x
                if x<crossing:inside=not inside
        return inside
    for ring in upper_rings[1:]:
        enclosed=sum(inside_outer(v.co) for v in ring)
        assert enclosed==len(ring),('Secondary rim is not strictly interior',enclosed,len(ring))
        edges=[]
        for a,b in zip(ring,ring[1:]+ring[:1]):
            edge=bm.edges.get((a,b));assert edge is not None and edge.is_boundary
            edges.append(edge)
        filled=bmesh.ops.holes_fill(bm,edges=edges,sides=0)['faces']
        assert len(filled)==1,'One internal opening must produce one explicit cap'
        triangles=bmesh.ops.triangulate(bm,faces=filled)['faces']
        for f in triangles:
            f[source_face]=-1;f[ancestry]=2;f.material_index=material_offset;f.smooth=False
            for loop in f.loops:
                # Internal cap only: independent planar UV, no outer albedo edit.
                loop[uv].uv=(.5+loop.vert.co.x*2,.5+loop.vert.co.y*2)
        inner_cap_faces+=len(triangles)
        inner_cap_records.append({'rimVertices':len(ring),'enclosedByActualOuterRim':enclosed,
            'triangles':len(triangles),'bounds':[[min(v.co[k] for v in ring) for k in range(3)],
                                            [max(v.co[k] for v in ring) for k in range(3)]]})
    # Explicit broad anatomic sections: width, anterior throat, posterior nape.
    # These are authored control stations in metres, not a registration fit.
    sections=[(.00,None),(.20,(.082,-.069,.081)),(.40,(.058,-.063,.064)),
              (.60,(.052,-.065,.055)),(.80,(.055,-.074,.055)),(1.,None)]
    count=144;rings=[lower];params=[0.];new_positions=[];landmarks=[]
    def coordinates(u,t):
        lo=sample(lower,lower_arc,u);hi=sample(upper,upper_arc,u)
        # The canonical contour parameter and upper contour parameter run
        # anterior->right->posterior->left; angle gives the named surface masses.
        angle=2*math.pi*u;sin=math.sin(angle);cos=math.cos(angle)
        stations=[(0.,lo)]
        for a,profile in sections[1:-1]:
            width,front,back=profile
            y=(front+back)/2-(back-front)/2*cos
            x=width*sin
            # Paired SCM runs obliquely down from mastoid to medial clavicle.
            scm_angle=.38+1.0*a
            scm=math.exp(-((abs(((angle+math.pi)%(2*math.pi))-math.pi)-scm_angle)/.21)**2)
            # Low relief, not a separate tendon cylinder.
            x += .0025*scm*sin*math.sin(math.pi*a)
            y -= .0035*scm*max(cos,0)*math.sin(math.pi*a)
            # Descending posterior nuchal slope and under-chin throat rise.
            z=lo.z+(hi.z-lo.z)*a
            stations.append((a,Vector((x,y,z))))
        stations.append((1.,hi))
        return cubic(stations,t)
    # 19 broad authored circumferential sections; dense donor edge is retained.
    for row in range(1,20):
        t=row/20;ring=[]
        for i in range(count):
            u=i/count;co=coordinates(u,t);v=bm.verts.new(co);v[source_id]=-1
            # Blend original clavicular/upper-chest influence into the neck chain.
            nearest=min(lower,key=lambda q:(q.co-sample(lower,lower_arc,u)).length_squared)
            w=dict(nearest[deform]);blend=min(1,t/.40);blend=blend*blend*(3-2*blend)
            z=co.z;head=max(0,min(1,(z-1.49)/.105));mid=max(0,1-abs((z-1.525)/.055))
            neck={groups['DEF-spine.004']:max(0,1-head-mid*.5),groups['DEF-spine.005']:mid*.5,groups['DEF-spine.006']:head}
            total=sum(neck.values());neck={k:x/total for k,x in neck.items()}
            combined={k:x*(1-blend) for k,x in w.items()}
            for k,x in neck.items():combined[k]=combined.get(k,0)+x*blend
            four=sorted(combined.items(),key=lambda a:-a[1])[:4];total=sum(x for _,x in four)
            for k,x in four:
                if x>0:v[deform][k]=x/total
            ring.append(v);new_positions.append(tuple(co))
        rings.append(ring);params.append(t)
    rings.append(upper);params.append(1.)
    for a,b,ta,tb in zip(rings,rings[1:],params,params[1:]):
        aa,bb=polar(a),polar(b);i=j=0
        while i<len(a) or j<len(b):
            if j==len(b) or (i<len(a) and aa[i+1]<=bb[j+1]):
                vs=[a[i%len(a)],a[(i+1)%len(a)],b[j%len(b)]]
                uvrows=[(aa[i],ta),(aa[i+1],ta),(bb[j],tb)];i+=1
            else:
                vs=[a[i%len(a)],b[(j+1)%len(b)],b[j%len(b)]]
                uvrows=[(aa[i],ta),(bb[j+1],tb),(bb[j],tb)];j+=1
            f=bm.faces.new(vs);f[source_face]=-1;f[ancestry]=1;f.material_index=len(body.data.materials);f.smooth=True
            for loop,tex in zip(f.loops,uvrows):loop[uv].uv=tex
    # Derivative UV chart obtains new samples over its area from the genuine
    # donor neck triangles. It is not one upper UV extruded down the surface.
    tree=BVHTree.FromPolygons(projection_positions,projection_triangles,all_triangles=True)
    source_pixels=[]
    for mat in donor_materials:
        texnode=next(n for n in mat.node_tree.nodes if n.type=='TEX_IMAGE' and n.image)
        image=texnode.image;source_pixels.append((np.array(image.pixels[:],dtype=np.float32).reshape(image.size[1],image.size[0],4),image.size[:]))
    base=body_materials[0].node_tree.nodes.get('Principled BSDF')
    base_color=np.array(base.inputs['Base Color'].default_value[:3] if base else [.55,.31,.22])
    def source_color(co):
        # New upper chest is outside the photographed neck; restrict projection
        # to clean neck reference, and extrapolate its low-frequency colour.
        query=Vector((co.x,co.y,max(1.496,co.z)))
        location,normal,index,distance=tree.find_nearest(query)
        tri=np.array([projection_positions[k] for k in projection_triangles[index]])
        p=np.array(location);a,b,c=tri;v0=b-a;v1=c-a;v2=p-a
        d00=v0@v0;d01=v0@v1;d11=v1@v1;den=d00*d11-d01*d01
        beta=(d11*(v2@v0)-d01*(v2@v1))/den;gamma=(d00*(v2@v1)-d01*(v2@v0))/den
        tex=np.array(projection_uv[index]);st=tex[0]*(1-beta-gamma)+tex[1]*beta+tex[2]*gamma
        pixels,size=source_pixels[projection_material[index]];x=st[0]*(size[0]-1);y=st[1]*(size[1]-1)
        x0=int(np.clip(x,0,size[0]-2));y0=int(np.clip(y,0,size[1]-2));fx=x-x0;fy=y-y0
        col=pixels[y0,x0,:3]*(1-fx)*(1-fy)+pixels[y0,x0+1,:3]*fx*(1-fy)+pixels[y0+1,x0,:3]*(1-fx)*fy+pixels[y0+1,x0+1,:3]*fx*fy
        # Selected PNG byte channels are encoded sRGB; the new packed atlas is
        # explicit linear Non-Color data, matching Principled boundary values.
        return np.where(col<=.04045,col/12.92,((col+.055)/1.055)**2.4)
    size=256;pixels=np.ones((size,size,4),np.float32)
    for j in range(size):
        t=j/(size-1)
        for i in range(size):
            u=i/(size-1);co=coordinates(u,t);col=source_color(co)
            # Match the actual lower material only within the lower chest edge;
            # geometric shape is fully present and independently reviewable.
            edge=min(1,t/.24);edge=edge*edge*(3-2*edge)
            pixels[j,i,:3]=base_color*(1-edge)+col*edge
    atlas=bpy.data.images.new('SelectedSkin_NewAnatomicalNeckUV',width=size,height=size,alpha=True)
    atlas.colorspace_settings.name='Non-Color';atlas.pixels.foreach_set(pixels.ravel());atlas.pack()
    mat=bpy.data.materials.new('Selected skin - authored anatomical neck');mat.use_nodes=True
    tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=atlas;tex.interpolation='Linear'
    principled=mat.node_tree.nodes.get('Principled BSDF');principled.inputs['Roughness'].default_value=.62
    mat.node_tree.links.new(tex.outputs['Color'],principled.inputs['Base Color']);body.data.materials.append(mat)
    bm.normal_update()
    for f in bm.faces:
        f.smooth=f[ancestry]!=2
    # Correct orientation by the coherent connected exterior, no second skin.
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    topology_metrics={'boundaryEdges':sum(e.is_boundary for e in bm.edges),
        'nonmanifoldEdges':sum(not e.is_manifold for e in bm.edges),
        'looseVertices':sum(not v.link_faces for v in bm.verts),
        'authoredNeckTriangles':sum(f[ancestry]==1 for f in bm.faces),
        'internalCapTriangles':sum(f[ancestry]==2 for f in bm.faces)}
    bm.to_mesh(body.data);bm.free();body.data.update()
    sf=body.data.attributes['SelectedSourceFace'];domain=body.data.attributes['AuthoredNeckDomain'];rn=body.data.attributes['GenuineSelectedCornerNormal']
    custom=[];edited_corner=0;retained_corner=0
    for loop in body.data.loops:
        custom.append(tuple(body.data.vertices[loop.vertex_index].normal))
    # Keep actual selected corner seams above a deliberate 25mm shading blend
    # strip; the new strip's normals are honestly derivative.
    for p in body.data.polygons:
        if sf.data[p.index].value>=0:
            for li in p.loop_indices:
                co=body.data.vertices[body.data.loops[li].vertex_index].co
                a=max(0,min(1,(co.z-upper_height(co))/.025));a=a*a*(3-2*a)
                raw=Vector(rn.data[li].vector);normal=Vector(custom[li])
                if raw.length>0:
                    custom[li]=tuple(normal.lerp(raw,a).normalized())
                if a==1:retained_corner+=1
                else:edited_corner+=1
    body.data.normals_split_custom_set(custom)
    after_ids=body.data.attributes['_SOURCE_VERTEX_ID'].data
    retained={int(after_ids[v.index].value):(tuple(v.co),field(v)) for v in body.data.vertices if after_ids[v.index].value>=0 and after_ids[v.index].value<1000000}
    for identity,row in retained.items():assert row==original[identity],('Canonical retained row changed',identity)
    hands=set(map(int,data['nativeSourceVertexIds'][data['newFieldBlendAlpha']>0]))
    assert hands<=retained.keys() and all(retained[i]==original[i] for i in hands)
    assert rest(rig)==before_rest
    rig.animation_data_clear()
    for b in rig.pose.bones:b.matrix_basis=Matrix.Identity(4)
    for image in bpy.data.images:
        if image.source=='FILE' and not image.packed_file:image.pack()
    bpy.ops.wm.save_as_mainfile(filepath=str(out/'selected-head-anatomical-neck.blend'))
    for p,d in PINS.items():assert sha(p)==d
    new_ids=[v.index for v in body.data.vertices if after_ids[v.index].value<0]
    np.savez_compressed(out/'authored-domain.npz',newVertexIndices=np.array(new_ids),vertices=np.array([tuple(v.co) for v in body.data.vertices]),canonicalRetainedSourceIds=np.array(sorted(retained)),restJSON=np.array(json.dumps(before_rest)))
    report={'accepted':False,'status':'UNACCEPTED_AUTHORED_SHAPE_NATIVE_SAVED',
        'candidate':{'path':str((out/'selected-head-anatomical-neck.blend').relative_to(ROOT)),'sha256':sha(out/'selected-head-anatomical-neck.blend')},
        'sourcePins':PINS,'recipeSHA256':sha(__file__),'all75RestRecordsUnchanged':True,
        'canonicalRetainedPositionFieldRows':len(retained),'handRowsUnchanged':len(hands),
        'vertices':len(body.data.vertices),'polygons':len(body.data.polygons),
        'lowerBoundaryVertices':len(lower),'upperBoundaryVertices':len(upper),'removedSecondaryInternalScanVertices':inner_removed,
        'explicitInteriorCapTriangles':inner_cap_faces,'internalCapRecords':inner_cap_records,'actualTopology':topology_metrics,
        'interiorPolicy':'Zero exact source UVpairs observed; no inferred inner-head/ear layer deleted. Only enclosed secondary oblique cut opening capped, ancestry2. Existing connected inner-head surface retained.',
        'authoredNeckNewVertices':len(new_ids),'circumferentialSections':19,'sectionSamples':144,
        'selectedRawCornerNormalsRetained':retained_corner,'selectedCornerNormalsInDerivativeBlendStrip':edited_corner,
        'upperCut':'z=1.555+.36*(y+.07)+.5*x*x','lowerCut':'z=1.438+2*x*x+.20*(y+.04)',
        'authoredSections':sections,'texture':'New cylindrical UV chart, source-triangle barycentric sampling of genuine donor neck; newly exposed low chest uses extrapolated source neck with lower boundary blend to canonical material; 256x256 packed derivative albedo. No donor bust geometry.',
        'limits':['Parent alone judges shape; no moving-art acceptance from stills.','No finished outfit, bike motion, exported/GPU transport or player promotion.','New throat UV/PBR is derivative; original source maps and native files unchanged.','This construction has not passed an independent saved-native readback.','Existing connected inner-head shell retained; no whole-head interior cleanup claim.']}
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'candidate':report['candidate'],'vertices':len(body.data.vertices),'newVertices':len(new_ids)}))


if __name__=='__main__':main()
